from flask import Flask, render_template, request, jsonify
import json
import logging
import re

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
            # Print structured profile to terminal so you can see everything fetched
            print("\n" + "=" * 60, flush=True)
            print("STRUCTURED PROFILE (Playwright)", flush=True)
            print("=" * 60, flush=True)
            print(json.dumps(profile_data, indent=2, ensure_ascii=False, default=str), flush=True)
            print("=" * 60 + "\n", flush=True)
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

