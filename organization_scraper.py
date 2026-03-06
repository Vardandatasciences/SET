from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict

import requests
from bs4 import BeautifulSoup

from google_scraper import HEADERS, SELENIUM_AVAILABLE, SeleniumScraper
from linkedin_scraper import BrowserManager, login_with_credentials
from organ import generate_organization_report

log = logging.getLogger(__name__)


def _find_linkedin_company_url_selenium(query: str) -> str:
    """
    Use the existing SeleniumScraper (from google_scraper) to resolve
    a LinkedIn company URL via Google search.
    """
    if not SELENIUM_AVAILABLE:
        return ""

    selenium_scraper = SeleniumScraper()
    try:
        urls = selenium_scraper.find_linkedin_company_urls(query, max_results=1)
        if urls:
            clean_url = urls[0]
            log.info(
                "[org_scraper] (selenium) candidate company URL via helper: %s",
                clean_url,
            )
            return clean_url
    finally:
        try:
            selenium_scraper.close()
        except Exception:
            pass

    log.info("[org_scraper] (selenium) no LinkedIn company URL found")
    return ""


def _find_linkedin_company_url_html(query: str) -> str:
    """
    Fallback: find LinkedIn company URL using a plain requests + HTML search.
    """
    search_q = f"site:linkedin.com/company {query}"
    url = f"https://www.google.com/search?q={requests.utils.quote(search_q)}&num=5"
    log.info("[org_scraper] (html) Google search for company: %r", query)
    log.info("[org_scraper] (html) search url: %s", url)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
    except Exception as exc:
        log.warning("[org_scraper] (html) Google request failed: %s", exc)
        return ""

    if resp.status_code != 200:
        log.warning(
            "[org_scraper] (html) Google returned non-200 status: %s",
            resp.status_code,
        )
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "linkedin.com/company/" not in href:
            continue

        m = re.search(
            r"(https?://(?:www\.)?linkedin\.com/company/[^\?&\"'>]+)", href
        )
        clean_url = m.group(1) if m else href
        log.info("[org_scraper] (html) candidate company URL: %s", clean_url)
        return clean_url

    log.info("[org_scraper] (html) no LinkedIn company URL found in Google HTML")
    return ""


def _find_linkedin_company_url(query: str) -> str:
    """
    Prefer Selenium-based resolution when available; otherwise fall
    back to plain HTML scraping.
    """
    url = _find_linkedin_company_url_selenium(query)
    if url:
        return url
    return _find_linkedin_company_url_html(query)


async def _scrape_company_playwright(url: str) -> Dict[str, Any]:
    """
    Use the Playwright-based `linkedin_scraper` BrowserManager to
    log in and scrape a LinkedIn company page (no Selenium).
    """
    async with BrowserManager(headless=True, slow_mo=0) as browser:
        # Let linkedin_scraper load credentials from .env / environment.
        await login_with_credentials(browser.page)

        page = browser.page

        # Be tolerant of LinkedIn's heavy pages and avoid strict
        # "networkidle" waits which often time out. First try a
        # DOMContentLoaded navigation with a higher timeout, then
        # an explicit short delay.
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as exc:
            # If navigation partially succeeded, we still try to read
            # whatever content is available instead of failing hard.
            log.warning("[org_scraper] page.goto timeout/err for %s: %s", url, exc)

        await page.wait_for_timeout(4000)

        try:
            title = await page.title()
        except Exception:
            title = ""

        try:
            body_text = await page.inner_text("body")
        except Exception:
            body_text = ""

        # Rough cleanup of text; we keep it simple and let the UI
        # show the first chunk as the "About" section.
        clean_text = re.sub(r"\s+", " ", (body_text or "")).strip()

        name = ""
        if title:
            # Typical pattern: "Company Name | LinkedIn"
            name = title.split("|", 1)[0].strip()
        if not name:
            name = url

        about = clean_text[:1500] if clean_text else ""

        return {
            "name": name,
            "headline": "",
            "location": "",
            "about": about,
            "experience": [],
            "education": [],
            "skills": [],
            "certifications": [],
            "source_url": url,
        }


def _organization_intelligence_to_profile(
    intelligence: Dict[str, Any],
    query: str,
    source_url: str,
) -> Dict[str, Any]:
    """
    Adapt the richer organization intelligence JSON into the lightweight
    profile-card structure expected by the frontend UI.
    """
    if not isinstance(intelligence, dict):
        return {
            "query": query,
            "error": "Invalid organization intelligence format.",
            "source_url": source_url,
        }

    # Prefer an explicit company name if present; otherwise fall back to query.
    name = (
        intelligence.get("company_name")
        or intelligence.get("query")
        or query
        or "Organization"
    )

    sections: list[str] = []

    company_background = intelligence.get("company_background")
    if company_background:
        sections.append(f"Company Background:\n{company_background}")

    leadership = intelligence.get("leadership_intelligence") or {}
    if isinstance(leadership, dict) and leadership.get("summary"):
        sections.append(f"Leadership Intelligence:\n{leadership['summary']}")

    financial = intelligence.get("financial_information") or {}
    if isinstance(financial, dict) and financial.get("summary"):
        sections.append(f"Financial Information:\n{financial['summary']}")

    news = intelligence.get("news_intelligence") or {}
    if isinstance(news, dict) and news.get("summary"):
        sections.append(f"News Intelligence:\n{news['summary']}")

    challenges = intelligence.get("challenges_risks") or {}
    if isinstance(challenges, dict) and challenges.get("summary"):
        sections.append(f"Challenges & Risks:\n{challenges['summary']}")

    strategic = intelligence.get("strategic_priorities")
    if strategic:
        sections.append(f"Strategic Priorities:\n{strategic}")

    recent_activity = intelligence.get("recent_activity")
    if recent_activity:
        sections.append(f"Recent Activity:\n{recent_activity}")

    about = "\n\n".join(s for s in sections if s).strip()
    if not about:
        # Fallback to raw content if we couldn't build a concise summary.
        about = intelligence.get("raw_content", "")

    return {
        "name": name,
        "headline": "",
        "location": "",
        "about": about,
        # The current UI renders these arrays but they are not
        # critical for organizations, so we leave them empty.
        "experience": [],
        "education": [],
        "skills": [],
        "certifications": [],
        "source_url": source_url,
        # Expose full intelligence payload for advanced use / debugging.
        "intelligence": intelligence,
        "query": query,
    }


def scrape_organization(query: str) -> Dict[str, Any]:
    """
    High-level helper used by the Flask UI for organization lookups.

    - If query is a direct LinkedIn company URL, use it as-is.
    - Otherwise, first try to resolve a LinkedIn company URL via Google
      (prefer Selenium when available).
    - Then pass that LinkedIn company URL into the full organization
      intelligence pipeline in `organ.generate_organization_report`,
      and adapt the result into the lightweight profile-card structure
      expected by the UI.
    """
    query = (query or "").strip()
    if not query:
        return {"error": "Empty organization query."}

    if query.startswith("http") and "linkedin.com/company/" in query:
        target = query
    else:
        target = _find_linkedin_company_url(query)
        if not target:
            return {
                "query": query,
                "error": "Could not find a LinkedIn company page for this organization.",
            }

    log.info(
        "[org_scraper] generating organization intelligence report for LinkedIn company URL: %r",
        target,
    )

    # Primary path: use the unified intelligence pipeline from organ.py,
    # which combines LinkedIn + web + AI analysis into a rich JSON report.
    try:
        intelligence = asyncio.run(generate_organization_report(target))
        return _organization_intelligence_to_profile(
            intelligence=intelligence,
            query=query,
            source_url=target,
        )
    except Exception as exc:
        log.warning(
            "[org_scraper] generate_organization_report failed, falling back to simple Playwright scrape: %s",
            exc,
        )

    # Fallback: simple DOM scrape of the LinkedIn company page so the UI
    # still gets at least basic name/about information.
    try:
        data = asyncio.run(_scrape_company_playwright(target))
    except Exception as exc:
        log.warning("[org_scraper] Playwright company scrape failed: %s", exc)
        return {
            "query": query,
            "error": "LinkedIn company scraping failed. Please try a direct company URL.",
        }

    data.setdefault("query", query)
    return data


