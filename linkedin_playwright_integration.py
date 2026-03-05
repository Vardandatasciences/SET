"""
Integration layer to use the async Playwright-based `linkedin_scraper` package
from synchronous code (Flask endpoints, CLI helpers, etc.).

This focuses on scraping a single LinkedIn person profile URL and returning a
plain Python dict that is easy to serialize to JSON and display in the UI.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict


def scrape_linkedin_profile(url: str) -> Dict[str, Any]:
    """
    Synchronous wrapper to scrape a LinkedIn profile using linkedin_scraper.

    Args:
        url: Direct LinkedIn profile URL (must contain `/in/`).

    Returns:
        Dictionary representation of the scraped Person profile.

    Notes:
        - Uses Playwright under the hood via linkedin_scraper.BrowserManager.
        - Expects LinkedIn credentials in the environment:
          LINKEDIN_EMAIL / LINKEDIN_USERNAME and LINKEDIN_PASSWORD
          (handled by linkedin_scraper.login_with_credentials).
    """
    if "linkedin.com/in/" not in url:
        raise ValueError("scrape_linkedin_profile expects a direct LinkedIn /in/ profile URL")

    return asyncio.run(_scrape_linkedin_profile_async(url))


async def _scrape_linkedin_profile_async(url: str) -> Dict[str, Any]:
    """Async implementation that talks to linkedin_scraper."""
    from linkedin_scraper import (  # type: ignore[import]
        BrowserManager,
        PersonScraper,
        login_with_credentials,
        SilentCallback,
    )

    async with BrowserManager(headless=True, slow_mo=0) as browser:
        # Let the library load credentials from .env if not passed explicitly.
        await login_with_credentials(browser.page)

        callback = SilentCallback()
        scraper = PersonScraper(browser.page, callback=callback)

        person = await scraper.scrape(url)
        # Person is a pydantic model; to_dict() is provided in models/person.py
        data = person.to_dict()
        # Attach original URL explicitly for clarity.
        data.setdefault("linkedin_url", url)
        return data

