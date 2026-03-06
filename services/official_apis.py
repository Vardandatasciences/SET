"""
Official API integrations for data sources that provide free APIs
This enhances the Perplexity-based approach with structured data from official sources
"""

import httpx
import json
from typing import Dict, Any, Optional, List
import re


class OfficialAPIs:
    """
    Integrate official APIs for sources that provide them
    Reduces API costs and provides structured data
    """
    
    def __init__(self):
        self.timeout = 30.0
        self.headers = {
            "User-Agent": "Sales Intelligence Tool (contact@example.com)",
            "Accept": "application/json"
        }
    
    async def get_sec_data(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Get SEC EDGAR data using official API
        SEC provides free, official API - no scraping needed!
        
        API Docs: https://www.sec.gov/edgar/sec-api-documentation
        """
        try:
            # Step 1: Search for company CIK (Central Index Key)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # SEC company tickers API
                search_url = f"https://www.sec.gov/cgi-bin/browse-edgar?company={company_name}&owner=exclude&action=getcompany"
                
                # For structured data, use SEC's company tickers JSON
                tickers_url = "https://www.sec.gov/files/company_tickers.json"
                
                response = await client.get(tickers_url, headers=self.headers)
                
                if response.status_code == 200:
                    tickers_data = response.json()
                    
                    # Find matching company
                    for entry in tickers_data.values():
                        if company_name.lower() in entry.get("title", "").lower():
                            cik = str(entry.get("cik_str", "")).zfill(10)
                            
                            # Step 2: Get company submissions (filings)
                            submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
                            submissions_response = await client.get(
                                submissions_url, 
                                headers=self.headers
                            )
                            
                            if submissions_response.status_code == 200:
                                submissions = submissions_response.json()
                                
                                # Extract recent filings
                                recent_filings = submissions.get("filings", {}).get("recent", {})
                                
                                return {
                                    "company_name": entry.get("title", ""),
                                    "cik": cik,
                                    "ticker": entry.get("ticker", ""),
                                    "recent_filings": {
                                        "10-K": self._extract_filing_urls(recent_filings, "10-K"),
                                        "10-Q": self._extract_filing_urls(recent_filings, "10-Q"),
                                        "8-K": self._extract_filing_urls(recent_filings, "8-K")
                                    },
                                    "source": "SEC EDGAR API (Official)"
                                }
        except Exception as e:
            print(f"SEC API error: {e}")
            return None
        
        return None
    
    def _extract_filing_urls(self, filings_data: Dict, form_type: str) -> List[Dict]:
        """Extract URLs for specific filing types"""
        forms = filings_data.get("form", [])
        descriptions = filings_data.get("description", [])
        dates = filings_data.get("filingDate", [])
        accession_numbers = filings_data.get("accessionNumber", [])
        
        results = []
        for i, form in enumerate(forms):
            if form == form_type:
                accession = accession_numbers[i].replace("-", "")
                filing_url = f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={filings_data.get('cik', '')}&accession_number={accession_numbers[i]}&xbrl_type=v"
                
                results.append({
                    "date": dates[i] if i < len(dates) else "Unknown",
                    "description": descriptions[i] if i < len(descriptions) else "",
                    "url": filing_url,
                    "accession_number": accession_numbers[i] if i < len(accession_numbers) else ""
                })
        
        return results[:5]  # Return 5 most recent
    
    async def get_wikipedia_data(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Get Wikipedia data using official REST API
        Wikipedia provides free API - no scraping needed!
        
        API Docs: https://www.mediawiki.org/wiki/API:Main_page
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Wikipedia REST API
                url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{company_name.replace(' ', '_')}"
                
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    return {
                        "title": data.get("title", ""),
                        "extract": data.get("extract", ""),
                        "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                        "thumbnail": data.get("thumbnail", {}).get("source", ""),
                        "source": "Wikipedia API (Official)"
                    }
        except Exception as e:
            print(f"Wikipedia API error: {e}")
            return None
        
        return None
    
    async def get_company_intelligence(
        self, 
        company_name: str
    ) -> Dict[str, Any]:
        """
        Get structured data from official APIs
        This complements Perplexity's intelligent search
        """
        results = {
            "company_name": company_name,
            "official_api_data": {}
        }
        
        # Get SEC data (if U.S. company)
        sec_data = await self.get_sec_data(company_name)
        if sec_data:
            results["official_api_data"]["sec"] = sec_data
        
        # Get Wikipedia data
        wiki_data = await self.get_wikipedia_data(company_name)
        if wiki_data:
            results["official_api_data"]["wikipedia"] = wiki_data
        
        return results
    
    def format_for_prompt(self, api_data: Dict[str, Any]) -> str:
        """
        Format official API data for inclusion in Perplexity prompt
        This helps Perplexity use structured data more effectively
        """
        formatted = []
        
        if "sec" in api_data.get("official_api_data", {}):
            sec = api_data["official_api_data"]["sec"]
            formatted.append(f"\nSEC EDGAR Data (Official API):")
            formatted.append(f"Company: {sec.get('company_name', '')}")
            formatted.append(f"CIK: {sec.get('cik', '')}")
            formatted.append(f"Ticker: {sec.get('ticker', '')}")
            
            if sec.get("recent_filings"):
                formatted.append("\nRecent Filings:")
                for filing_type, filings in sec["recent_filings"].items():
                    if filings:
                        formatted.append(f"  {filing_type}:")
                        for filing in filings[:3]:  # Top 3
                            formatted.append(f"    - {filing['date']}: {filing['description']}")
                            formatted.append(f"      URL: {filing['url']}")
        
        if "wikipedia" in api_data.get("official_api_data", {}):
            wiki = api_data["official_api_data"]["wikipedia"]
            formatted.append(f"\nWikipedia Data (Official API):")
            formatted.append(f"Title: {wiki.get('title', '')}")
            formatted.append(f"Summary: {wiki.get('extract', '')[:500]}...")
            formatted.append(f"URL: {wiki.get('url', '')}")
        
        return "\n".join(formatted) if formatted else ""


# Example usage:
"""
async def enhanced_research(company_name: str):
    # Step 1: Get structured data from official APIs
    official_apis = OfficialAPIs()
    api_data = await official_apis.get_company_intelligence(company_name)
    
    # Step 2: Format for Perplexity prompt
    structured_context = official_apis.format_for_prompt(api_data)
    
    # Step 3: Use with Perplexity (enhanced with structured data)
    # This gives Perplexity better context and reduces API costs
    perplexity_prompt = f"""
    Research {company_name} with the following structured data:
    {structured_context}
    
    Use this data and search for additional information from:
    - Bloomberg
    - Yahoo Finance
    - News sources
    - Executive communications
    ...
    """
"""

