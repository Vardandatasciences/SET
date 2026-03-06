"""
Simple script to generate an organization intelligence report as JSON.

Edit the COMPANY_QUERY variable below with the company name (or LinkedIn
company URL) you want to research, then run:

    python organ.py

This uses the existing services:
- UnifiedIntelligenceService  (web + LinkedIn + Ollama pipeline)
- IntelligenceExtractor       (turns raw text into structured intelligence)
- LinkedInScraperService      (under the hood for LinkedIn company data)
"""

import asyncio
import json
import os

from dotenv import load_dotenv

from services.unified_intelligence_service import UnifiedIntelligenceService
from services.intelligence_extractor import IntelligenceExtractor


# ---------------------------------------------------------------------------
# 1. EDIT THIS VALUE TO CHANGE THE COMPANY YOU WANT TO RESEARCH
# ---------------------------------------------------------------------------
COMPANY_QUERY = "https://www.linkedin.com/company/vardaan-ds/"

async def generate_organization_report(company_query: str) -> dict:
    """
    Run the full organization intelligence pipeline and return a JSON-ready dict.
    """
    # Initialize the unified service (uses Ollama + LinkedIn + web search)
    unified_service = UnifiedIntelligenceService(
        ollama_base_url=os.getenv("OLLAMA_BASE_URL"),
        ollama_model=os.getenv("OLLAMA_MODEL"),
    )

    # If the query is a direct LinkedIn company URL, pass it as a source so
    # the unified service will FIRST use the LinkedIn company scraper and then
    # enrich with web/AI intelligence.
    sources = None
    q = (company_query or "").strip()
    if q.startswith("http") and "linkedin.com/company/" in q:
        sources = [
            {
                "name": "LinkedIn Company Page",
                "link": q,
            }
        ]

    # Step 1: fetch raw research data (combined LinkedIn + web + AI text)
    raw_data = await unified_service.fetch_research_data(
        query=company_query,
        research_type="organization",
        sources=sources,
        verified_profile=None,
    )

    # Step 2: extract structured intelligence sections
    extractor = IntelligenceExtractor()
    intelligence = await extractor.extract_intelligence(
        raw_data=raw_data,
        research_type="organization",
    )

    return intelligence


async def _async_main() -> None:
    load_dotenv()

    company = COMPANY_QUERY.strip()
    if not company:
        raise SystemExit("Please set COMPANY_QUERY to a non-empty company name.")

    print(f"\n=== Generating organization intelligence report for: {company!r} ===\n")
    report = await generate_organization_report(company)

    # Pretty-print JSON report to stdout
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(_async_main())

