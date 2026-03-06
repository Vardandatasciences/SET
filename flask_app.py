from flask import Flask, render_template, request, jsonify
import json
import logging
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from groq import Groq

# Import existing pipeline functions and config
from google_scraper import (
    process_query,
    GROQ_API_KEY,
    HEADERS,
    SELENIUM_AVAILABLE,
    SeleniumScraper,
)
from openai_person_info import process_query_person
from gemini_model import ask_gemini_person_info
from perplexity import ask_perplexity_person_info
from organization_scraper import scrape_organization

try:
    # Optional: Playwright-based LinkedIn scraper integration
    from linkedin_playwright_integration import scrape_linkedin_profile
except Exception:  # pragma: no cover - best-effort optional import
    scrape_linkedin_profile = None  # type: ignore[assignment]

app = Flask(__name__)
groq_client = Groq(api_key=GROQ_API_KEY)
log = logging.getLogger(__name__)

# Directory where LinkedIn profile JSON files are stored
PROFILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "profiles")


def _save_profile(profile_data: dict) -> str | None:
    """
    Store profile as a JSON file under data/profiles/.
    Filename: {slug}_{timestamp}.json
    Returns the path where saved, or None on error.
    """
    if not profile_data or not isinstance(profile_data, dict):
        return None
    try:
        os.makedirs(PROFILES_DIR, exist_ok=True)
        # Slug from linkedin_url or query or name
        url = (
            profile_data.get("linkedin_url")
            or profile_data.get("source_url")
            or profile_data.get("query")
            or ""
        )
        name = (profile_data.get("name") or "").strip().replace(" ", "_")[:50]
        if "linkedin.com/in/" in url:
            slug = url.rstrip("/").split("/in/")[-1].split("?")[0] or "profile"
        else:
            slug = re.sub(r"[^\w\-]", "", name) or "profile"
        slug = (slug or "profile")[:80]
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{slug}_{ts}.json"
        filepath = os.path.join(PROFILES_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False, default=str)
        log.info("Saved profile to %s", filepath)
        return filepath
    except Exception as e:
        log.warning("Failed to save profile: %s", e)
        return None


def _print_profile(profile_data: dict, source: str = "LinkedIn scraper") -> None:
    """Print full profile to console for debugging / visibility."""
    if not profile_data:
        return
    print("\n" + "=" * 60, flush=True)
    print(f"PROFILE ({source}) – all details", flush=True)
    print("=" * 60, flush=True)
    print(json.dumps(profile_data, indent=2, ensure_ascii=False, default=str), flush=True)
    print("=" * 60 + "\n", flush=True)


def _enrich_playwright_profile_with_groq(profile_data: dict) -> dict:
    """
    Use the existing Selenium + Groq pipeline (process_query)
    to fill in missing or obviously broken fields from a Playwright profile.

    - Keeps good Playwright data (DOM-structured)
    - Uses Groq output only to fix missing / malformed pieces
    """
    if not profile_data or not isinstance(profile_data, dict):
        return profile_data

    # Import here to avoid circular issues
    try:
        from google_scraper import process_query as _process_query  # type: ignore
    except Exception as e:  # pragma: no cover - defensive
        log.warning("Groq enrichment unavailable (import failed): %s", e)
        return profile_data

    url = (
        profile_data.get("linkedin_url")
        or profile_data.get("source_url")
        or profile_data.get("query")
        or ""
    )
    if not url:
        return profile_data

    try:
        llm = _process_query(url)
    except Exception as e:
        log.warning("Groq enrichment failed: %s", e)
        return profile_data

    if not llm or llm.get("error"):
        return profile_data

    # 1) Simple scalar fields: if missing in Playwright, take them from Groq.
    for key in ("name", "location", "about"):
        if not profile_data.get(key) and llm.get(key):
            profile_data[key] = llm[key]

    if (not profile_data.get("skills")) and llm.get("skills"):
        profile_data["skills"] = llm.get("skills") or []

    # 2) Fix obviously broken education:
    #    If current educations look like mashed-up job rows, replace from Groq.
    educations = profile_data.get("educations") or []
    llm_edu = llm.get("education") or []
    if llm_edu:
        all_look_like_jobs = bool(educations) and all(
            isinstance(ed, dict)
            and isinstance(ed.get("institution_name"), str)
            and any(token in ed["institution_name"] for token in [" · ", "Present", "yr"])
            for ed in educations
        )
        if not educations or all_look_like_jobs:
            new_educations = []
            for ed in llm_edu:
                if not isinstance(ed, dict):
                    continue
                institution = ed.get("institution") or ""
                degree = ed.get("degree") or ""
                years = ed.get("years") or ""
                if not institution and not degree and not years:
                    continue
                new_educations.append(
                    {
                        "institution_name": institution,
                        "degree": degree,
                        "linkedin_url": None,
                        "from_date": None,
                        "to_date": None,
                        "description": years,
                    }
                )
            if new_educations:
                profile_data["educations"] = new_educations

    # 3) If there are no experiences at all, fill them from Groq.
    if not profile_data.get("experiences") and llm.get("experience"):
        new_exps = []
        for job in llm.get("experience", []):
            if not isinstance(job, dict):
                continue
            title = job.get("title") or ""
            company = job.get("company") or ""
            duration = job.get("duration") or job.get("years") or ""
            location = job.get("location") or ""
            desc = job.get("description") or ""
            if not title and not company and not desc:
                continue
            new_exps.append(
                {
                    "position_title": title,
                    "institution_name": company,
                    "linkedin_url": None,
                    "from_date": None,
                    "to_date": None,
                    "duration": duration,
                    "location": location,
                    "description": desc,
                }
            )
        if new_exps:
            profile_data["experiences"] = new_exps

    # 4) Light cleanup of obviously bogus accomplishments from accessibility text.
    accs = profile_data.get("accomplishments") or []
    cleaned_accs = []
    for acc in accs:
        if not isinstance(acc, dict):
            continue
        title = (acc.get("title") or "").strip()
        issuer = (acc.get("issuer") or "").strip()
        # Drop pure "About"/"Accessibility" noise.
        if title.lower() == "about" and issuer.lower() == "accessibility":
            continue
        cleaned_accs.append(acc)
    profile_data["accomplishments"] = cleaned_accs

    # 5) Deduplicate posts by (content, post_url).
    posts = profile_data.get("posts") or []
    seen_posts = set()
    unique_posts = []
    for p in posts:
        if not isinstance(p, dict):
            continue
        key = (
            (p.get("content") or "").strip(),
            p.get("post_url") or "",
        )
        if key in seen_posts:
            continue
        seen_posts.add(key)
        unique_posts.append(p)
    profile_data["posts"] = unique_posts

    # 6) Gather additional web context (news, bios, company sites) via Selenium Google search
    #    and then send everything to Groq once more to get a final, professionally
    #    organized profile JSON.
    extra_context = _gather_broad_web_info(profile_data)
    profile_data = _finalize_profile_with_ai(profile_data, extra_context)

    return profile_data


def _gather_broad_web_info(profile_data: dict) -> str:
    """
    Use a Selenium-based Google search (from linkedin_scraper.SeleniumScraper)
    to collect broader information about the person from other sources:
    news, company sites, profiles, biographies, etc.
    """
    # Build a reasonable query from name + current/primary role
    name = (profile_data.get("name") or "").strip()
    experiences = profile_data.get("experiences") or []
    primary_title = ""
    primary_company = ""
    if experiences and isinstance(experiences[0], dict):
        primary_title = (experiences[0].get("position_title") or "").strip()
        primary_company = (experiences[0].get("institution_name") or "").strip()

    base_query_parts = [name, primary_title, primary_company]
    query = " ".join(p for p in base_query_parts if p).strip()
    if not query:
        return ""

    try:
        # Import SeleniumScraper from linkedin_scraper to use its broad Google info helper
        from linkedin_scraper import SeleniumScraper as LinkedInBroadScraper  # type: ignore
    except Exception:
        return ""

    scraper = None
    try:
        scraper = LinkedInBroadScraper()
        if not getattr(scraper, "driver", None):
            return ""
        return scraper._get_broad_google_info(query)  # type: ignore[attr-defined]
    except Exception:
        return ""
    finally:
        try:
            if scraper is not None:
                scraper.close()
        except Exception:
            pass


def _finalize_profile_with_ai(profile_data: dict, extra_context: str) -> dict:
    """
    Send the merged profile JSON + extra web context to Groq one last time
    to get a polished, well-organized professional profile JSON.
    """
    if not profile_data or not isinstance(profile_data, dict):
        return profile_data

    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        return profile_data

    try:
        system_msg = (
            "You are a senior sales enablement analyst. "
            "You receive raw person profile JSON (from LinkedIn and web sources) "
            "plus extra text snippets. Your job is to produce a final, "
            "professional, well-structured JSON profile for a sales intelligence tool.\n\n"
            "CRITICAL:\n"
            "1) Preserve and clean the existing factual fields (name, location, about, experiences, educations, skills, posts, etc.).\n"
            "2) In addition, populate a 'leadership_mvp' object with these fields when possible, "
            "using ONLY information strongly supported by the inputs:\n"
            "   - full_name\n"
            "   - current_title\n"
            "   - normalized_title\n"
            "   - function\n"
            "   - seniority\n"
            "   - company\n"
            "   - location\n"
            "   - linkedin_url\n"
            "   - official_bio_url\n"
            "   - tenure_current_role\n"
            "   - joined_company_date\n"
            "   - prior_company\n"
            "   - internal_vs_external_hire\n"
            "   - top_strategic_priorities (array of strings)\n"
            "   - top_pain_points (array of strings)\n"
            "   - recent_public_quotes (array of strings)\n"
            "   - recent_trigger_events (array of strings)\n"
            "   - visibility_score (0-10)\n"
            "   - decision_maker_score (0-10)\n"
            "   - buying_committee_role\n"
            "   - sales_relevance_score (0-10)\n"
            "   - best_outreach_angle\n"
            "   - suggested_questions (array of strings)\n"
            "   - topics_to_avoid (array of strings)\n"
            "   - source_list (array of {source, url, snippet})\n"
            "   - confidence_score (0-1)\n"
            "   - last_verified_date (ISO 8601)\n"
            "If you cannot reliably infer a field, set it to null or an empty list.\n\n"
            "3) Only include information that helps: identify the right person, understand what they care about, "
            "see their pressures and timing, talk to them better, or avoid saying the wrong thing.\n"
            "4) Do NOT hallucinate facts; conservative inference only. ALWAYS return STRICT JSON (no markdown)."
        )

        user_msg = (
            "Raw profile JSON (from LinkedIn scraper + first Groq pass):\n"
            f"{json.dumps(profile_data, ensure_ascii=False)}\n\n"
            "Additional web context (Google results, knowledge panels, news snippets, bios, etc.):\n"
            f"{extra_context or '(none)'}\n\n"
            "Return ONLY the final merged and cleaned JSON profile, including a 'leadership_mvp' object as specified."
        )

        resp = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=4096,
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()

        # Strip accidental fences and parse JSON
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        return profile_data
    except Exception:
        # On any error, fall back to original merged data
        return profile_data


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    raw_data = None
    error = None

    if request.method == "POST":
        sname = request.form.get("sname", "").strip()
        description = request.form.get("description", "").strip()
        source = request.form.get("source", "")
        # Combine name + description so all backends get full context
        combined = f"{sname} {description}".strip() or sname

        if not sname or not source:
            error = "Please enter a name and choose a source."
        else:
            try:
                if source == "internet":
                    # For plain form POST we still run the full pipeline directly.
                    raw_data = process_query(combined)
                elif source == "openai":
                    # OpenAI knowledge-only person info
                    raw_data = process_query_person(combined)
                elif source == "perplexity":
                    # Perplexity Sonar (web + model)
                    raw_data = ask_perplexity_person_info(combined)
                elif source == "google":
                    # Google Gemini (knowledge-only), wired to "google" in dropdown
                    raw_data = ask_gemini_person_info(combined)
                else:
                    error = f"Unknown source: {source}"

                if raw_data is not None:
                    if isinstance(raw_data, dict) and raw_data.get("error"):
                        error = raw_data.get("error")
                    else:
                        result = raw_data
            except Exception as exc:
                error = f"Backend error: {exc}"

    return render_template("index.html", result=result, error=error)


def _search_linkedin_candidates(query: str) -> list[dict]:
    """
    Lightweight Google HTML search for site:linkedin.com/in results.
    Returns a list of candidates with (name, company guess, snippet, url).
    This is independent of the main scraping pipeline.
    """
    search_q = f"site:linkedin.com/in {query}"
    url = f"https://www.google.com/search?q={requests.utils.quote(search_q)}&num=6"
    print(f"[search_linkedin] query={query!r}", flush=True)
    print(f"[search_linkedin] url={url}", flush=True)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
    except Exception:
        return []

    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    candidates: list[dict] = []
    seen_urls: set[str] = set()

    # First pass: Google HTML page
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "linkedin.com/in/" not in href:
            continue

        m = re.search(r"(https?://(?:www\.)?linkedin\.com/in/[^\?&\"'>]+)", href)
        clean_url = m.group(1) if m else href
        if clean_url in seen_urls:
            continue
        seen_urls.add(clean_url)

        # Anchor text as initial title
        title = a.get_text(" ", strip=True)

        # Try to get some surrounding text as snippet
        snippet = ""
        parent = a.find_parent()
        if parent is not None:
            snippet = parent.get_text(" ", strip=True)
        if snippet and len(snippet) > 400:
            snippet = snippet[:400] + "…"

        # Guess name / company from title
        name = title or clean_url.split("/")[-1]
        company = ""
        for sep in [" - ", " – ", " | ", " · "]:
            if sep in title:
                parts = title.split(sep, 1)
                name = parts[0].strip() or name
                company = parts[1].strip()
                break

        candidates.append(
            {
                "name": name,
                "company": company,
                "snippet": snippet,
                "url": clean_url,
            }
        )

    print(f"[search_linkedin] found {len(candidates)} raw candidate(s) from Google", flush=True)

    # If Google HTML is blocked / empty, fall back to DuckDuckGo HTML,
    # which is usually more scraper‑friendly.
    if not candidates and SELENIUM_AVAILABLE:
        # Final fallback: reuse Selenium's Google search logic to find a profile URL,
        # same as the main scraper pipeline, and expose that as candidate list.
        try:
            print("[search_linkedin] no HTML candidates, trying Selenium _find_linkedin_url", flush=True)
            selenium_scraper = SeleniumScraper()
            selenium_urls: list[str] = []
            if selenium_scraper.driver:
                selenium_urls = selenium_scraper.find_linkedin_urls(query, max_results=5)
                selenium_scraper.close()

            for selenium_url in selenium_urls:
                print(f"[search_linkedin] Selenium found LinkedIn URL: {selenium_url}", flush=True)
                candidates.append(
                    {
                        "name": query,
                        "company": "",
                        "snippet": "Found via Selenium Google search.",
                        "url": selenium_url,
                    }
                )
        except Exception as e:
            print(f"[search_linkedin] Selenium fallback failed: {e}", flush=True)

    if not candidates:
        try:
            ddg_q = f"site:linkedin.com/in {query}"
            ddg_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(ddg_q)}"
            print(f"[search_linkedin] Google returned 0, trying DuckDuckGo", flush=True)
            print(f"[search_linkedin] ddg_url={ddg_url}", flush=True)

            ddg_resp = requests.get(ddg_url, headers=HEADERS, timeout=12)
            if ddg_resp.status_code == 200:
                ddg_soup = BeautifulSoup(ddg_resp.text, "html.parser")
                for a in ddg_soup.find_all("a", href=True):
                    href = a["href"]
                    if "linkedin.com/in/" not in href:
                        continue

                    m = re.search(r"(https?://(?:www\.)?linkedin\.com/in/[^\?&\"'>]+)", href)
                    clean_url = m.group(1) if m else href
                    if clean_url in seen_urls:
                        continue
                    seen_urls.add(clean_url)

                    title = a.get_text(" ", strip=True)
                    snippet = ""
                    parent = a.find_parent()
                    if parent is not None:
                        snippet = parent.get_text(" ", strip=True)
                    if snippet and len(snippet) > 400:
                        snippet = snippet[:400] + "…"

                    name = title or clean_url.split("/")[-1]
                    company = ""
                    for sep in [" - ", " – ", " | ", " · "]:
                        if sep in title:
                            parts = title.split(sep, 1)
                            name = parts[0].strip() or name
                            company = parts[1].strip()
                            break

                    candidates.append(
                        {
                            "name": name,
                            "company": company,
                            "snippet": snippet,
                            "url": clean_url,
                        }
                    )

            print(f"[search_linkedin] DuckDuckGo added {len(candidates)} candidate(s)", flush=True)
        except Exception as e:
            print(f"[search_linkedin] DuckDuckGo search failed: {e}", flush=True)

    print(f"[search_linkedin] total {len(candidates)} raw candidate(s)", flush=True)
    for i, c in enumerate(candidates[:5]):
        print(
            f"[search_linkedin] {i}: name={c.get('name')} "
            f"company={c.get('company')} url={c.get('url')}",
            flush=True,
        )

    return candidates


def _search_linkedin_org_candidates(query: str) -> list[dict]:
    """
    Similar to _search_linkedin_candidates but targeting LinkedIn company pages
    (site:linkedin.com/company) instead of person profiles.
    """
    search_q = f"site:linkedin.com/company {query}"
    url = f"https://www.google.com/search?q={requests.utils.quote(search_q)}&num=6"
    print(f"[search_linkedin_org] query={query!r}", flush=True)
    print(f"[search_linkedin_org] url={url}", flush=True)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
    except Exception:
        return []

    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    candidates: list[dict] = []
    seen_urls: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "linkedin.com/company/" not in href:
            continue

        m = re.search(r"(https?://(?:www\.)?linkedin\.com/company/[^\?&\"'>]+)", href)
        clean_url = m.group(1) if m else href
        if clean_url in seen_urls:
            continue
        seen_urls.add(clean_url)

        # Anchor text often looks like "Company Name – Tagline"
        title = a.get_text(" ", strip=True)

        snippet = ""
        parent = a.find_parent()
        if parent is not None:
            snippet = parent.get_text(" ", strip=True)
        if snippet and len(snippet) > 400:
            snippet = snippet[:400] + "…"

        name = title or clean_url.split("/")[-1]
        company = ""
        for sep in [" - ", " – ", " | ", " · "]:
            if sep in title:
                parts = title.split(sep, 1)
                name = parts[0].strip() or name
                company = parts[1].strip()
                break

        candidates.append(
            {
                "name": name,
                "company": company,
                "snippet": snippet,
                "url": clean_url,
            }
        )

    print(
        f"[search_linkedin_org] found {len(candidates)} raw organization candidate(s) from Google",
        flush=True,
    )

    # When Google HTML returns nothing, fall back to Selenium (same pattern as person search)
    if not candidates and SELENIUM_AVAILABLE:
        try:
            print(
                "[search_linkedin_org] no HTML candidates, trying Selenium find_linkedin_company_urls",
                flush=True,
            )
            selenium_scraper = SeleniumScraper()
            selenium_urls: list[str] = []
            if selenium_scraper.driver:
                selenium_urls = selenium_scraper.find_linkedin_company_urls(
                    query, max_results=5
                )
                selenium_scraper.close()
            for selenium_url in selenium_urls:
                print(
                    f"[search_linkedin_org] Selenium found company URL: {selenium_url}",
                    flush=True,
                )
                candidates.append(
                    {
                        "name": query,
                        "company": "",
                        "snippet": "Found via Selenium Google search.",
                        "url": selenium_url,
                    }
                )
        except Exception as e:
            print(
                f"[search_linkedin_org] Selenium fallback failed: {e}",
                flush=True,
            )

    return candidates


def _enrich_candidates_with_groq(candidates: list[dict]) -> list[dict]:
    """
    Use a very small Groq call to normalize just name + company
    from Google result titles/snippets (no LinkedIn scraping here).
    """
    if not candidates:
        print("[enrich_candidates] no candidates to enrich", flush=True)
        return candidates

    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        print("[enrich_candidates] GROQ_API_KEY missing, skipping enrichment", flush=True)
        return candidates

    # Build compact text for the model
    lines = []
    for idx, c in enumerate(candidates):
        title = f"{c.get('name','')}".strip()
        company = c.get("company", "").strip()
        snippet = c.get("snippet", "").strip()
        line = f"[{idx}] title: {title}; company_guess: {company}; snippet: {snippet}"
        lines.append(line)
    joined = "\n".join(lines)

    system_msg = (
        "You are helping disambiguate LinkedIn search results. "
        "For each line, extract a clean person name and their main company "
        "(or best guess from the text). Always return STRICT JSON."
    )
    user_msg = f"""
Given these Google search result lines, return JSON with clean name and company for each index.

Lines:
{joined}

Return ONLY JSON like:
{{
  "candidates": [
    {{"index": 0, "name": "Full Name", "company": "Company Name"}},
    ...
  ]
}}
"""
    try:
        print(f"[enrich_candidates] sending {len(candidates)} candidate(s) to Groq", flush=True)
        resp = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=512,
            temperature=0.1,
        )
        raw = resp.choices[0].message.content.strip()
    except Exception:
        return candidates

    import json

    # Strip any accidental fences and parse JSON
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        data = json.loads(cleaned)
        print("[enrich_candidates] Groq raw JSON parsed successfully", flush=True)
    except Exception:
        return candidates

    mapping = {}
    for item in data.get("candidates", []):
        try:
            idx = int(item.get("index"))
        except Exception:
            continue
        mapping[idx] = {
            "name": item.get("name") or "",
            "company": item.get("company") or "",
        }

    # Apply normalized values where available
    print(f"[enrich_candidates] got normalized data for {len(mapping)} indices", flush=True)
    for idx, c in enumerate(candidates):
        norm = mapping.get(idx)
        if not norm:
            continue
        if norm["name"]:
            c["name"] = norm["name"]
        if norm["company"]:
            c["company"] = norm["company"]

    return candidates


@app.post("/api/search")
def api_search():
    """
    POST /api/search
    JSON body: { "query": "name or LinkedIn URL" }

    Returns: { "candidates": [ { name, company, snippet, url }, ... ] }
    """
    print("[api_search] POST /api/search called", flush=True)
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    print(f"[api_search] query={query!r}", flush=True)
    if not query:
        return jsonify({"error": "Missing 'query' in request body."}), 400

    # If user already pasted a direct LinkedIn URL, no need to search
    if query.startswith("http") and "linkedin.com/in/" in query:
        print("[api_search] direct LinkedIn URL provided, returning single candidate", flush=True)
        return jsonify(
            {
                "candidates": [
                    {
                        "name": "",
                        "company": "",
                        "snippet": "Direct LinkedIn URL provided.",
                        "url": query,
                    }
                ]
            }
        )

    candidates = _search_linkedin_candidates(query)
    candidates = _enrich_candidates_with_groq(candidates)

    print(f"[api_search] returning {len(candidates)} candidate(s) to UI", flush=True)
    return jsonify({"candidates": candidates})


@app.post("/api/org/search")
def api_org_search():
    """
    POST /api/org/search
    JSON body: { "query": "organization name or LinkedIn company URL" }

    Returns: { "candidates": [ { name, company, snippet, url }, ... ] }
    """
    print("[api_org_search] POST /api/org/search called", flush=True)
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    print(f"[api_org_search] query={query!r}", flush=True)
    if not query:
        return jsonify({"error": "Missing 'query' in request body."}), 400

    if query.startswith("http") and "linkedin.com/company/" in query:
        print(
            "[api_org_search] direct LinkedIn company URL provided, returning single candidate",
            flush=True,
        )
        return jsonify(
            {
                "candidates": [
                    {
                        "name": "",
                        "company": "",
                        "snippet": "Direct LinkedIn company URL provided.",
                        "url": query,
                    }
                ]
            }
        )

    candidates = _search_linkedin_org_candidates(query)
    candidates = _enrich_candidates_with_groq(candidates)

    print(
        f"[api_org_search] returning {len(candidates)} organization candidate(s) to UI",
        flush=True,
    )
    return jsonify({"candidates": candidates})


@app.post("/api/profile")
def api_profile():
    """
    POST /api/profile
    JSON body: { "query": "name or LinkedIn URL" }

    Returns structured profile JSON produced by process_query().
    """
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Missing 'query' in request body."}), 400

    # If this is a direct LinkedIn profile URL and the Playwright-based
    # scraper is available, try it first for richer, DOM-based data.
    if (
        scrape_linkedin_profile is not None
        and query.startswith("http")
        and "linkedin.com/in/" in query
    ):
        try:
            log.info("Using linkedin_scraper (Playwright) for LinkedIn URL")
            profile_data = scrape_linkedin_profile(query)
            profile_data.setdefault("source_url", query)
            profile_data.setdefault("query", query)
            # Enrich Playwright data with Selenium + Groq (fix missing/bad fields)
            profile_data = _enrich_playwright_profile_with_groq(profile_data)
            _save_profile(profile_data)
            _print_profile(profile_data, source="Playwright + Selenium/Groq")
            return jsonify(profile_data)
        except Exception as e:
            log.warning(f"linkedin_scraper failed, falling back to Groq pipeline: {e}")

    # Fallback: use existing Selenium + Groq pipeline
    result = process_query(query)

    if not result:
        return jsonify({"error": "Unknown error during processing."}), 500

    if result.get("error"):
        # Pass through the error but keep 200 so UI can show the message
        return jsonify(result), 200

    # Store and print all details for Selenium+Groq pipeline too
    _save_profile(result)
    _print_profile(result, source="Selenium + Groq pipeline")

    return jsonify(result)


@app.post("/api/org/profile")
def api_org_profile():
    """
    POST /api/org/profile
    JSON body: { "query": "organization name or LinkedIn company URL" }

    Uses the Selenium + Groq LinkedIn pipeline to extract a structured profile.
    """
    print("[api_org_profile] POST /api/org/profile called", flush=True)
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    print(f"[api_org_profile] query={query!r}", flush=True)
    if not query:
        return jsonify({"error": "Missing 'query' in request body."}), 400

    # Use the dedicated organization scraper, which resolves a company
    # LinkedIn URL (if needed) and then reuses the Selenium + Groq pipeline.
    result = scrape_organization(query)

    if not result:
        return jsonify({"error": "No organization data found."}), 404

    if result.get("error"):
        # Pass through the error but keep 200 so UI can show the message
        return jsonify(result), 200

    print("[api_org_profile] returning organization profile to UI", flush=True)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)

