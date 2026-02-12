"""
Web Search Service
Provides web search functionality using:
- Google Custom Search API (Primary) - Extracts data directly from search results
- DuckDuckGo (Fallback - Free) - Only used if Google API is unavailable
"""

import os
import httpx
from typing import Dict, Any, List, Optional
import asyncio


class WebSearchService:
    """
    Service for searching the web and extracting data
    Uses Google Custom Search API as primary for data extraction
    DuckDuckGo as fallback (only if Google API unavailable)
    """
    
    def __init__(self):
        """Initialize web search service"""
        # Google Custom Search API configuration
        self.google_api_key = os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
        
        # Check if Google API is configured
        self.google_available = bool(self.google_api_key and self.google_cse_id)
        
        if self.google_available:
            print("✅ Google Custom Search API configured")
            print(f"   API Key: {'*' * 20}...{self.google_api_key[-4:] if len(self.google_api_key) > 4 else '****'}")
            print(f"   Search Engine ID: {self.google_cse_id[:10]}...{self.google_cse_id[-4:] if len(self.google_cse_id) > 14 else self.google_cse_id}")
        else:
            print("⚠️  Google Custom Search API not configured")
            if not self.google_api_key:
                print("   ❌ GOOGLE_CUSTOM_SEARCH_API_KEY is missing")
            if not self.google_cse_id:
                print("   ❌ GOOGLE_CUSTOM_SEARCH_ENGINE_ID is missing")
            print("   Will use DuckDuckGo fallback only")
            print("   To enable Google Search:")
            print("   1. Get API key: https://console.cloud.google.com/")
            print("   2. Create Custom Search Engine: https://programmablesearchengine.google.com/")
            print("   3. Set GOOGLE_CUSTOM_SEARCH_API_KEY and GOOGLE_CUSTOM_SEARCH_ENGINE_ID in .env")
        
        # DuckDuckGo is always available (free, no API key needed)
        print("✅ DuckDuckGo search available (free fallback)")
    
    async def search(
        self, 
        query: str, 
        num_results: int = 10,
        research_type: str = "organization"
    ) -> List[Dict[str, Any]]:
        """
        Search the web for a query
        
        Args:
            query: Search query
            num_results: Number of results to return (max 10 for Google, unlimited for DuckDuckGo)
            research_type: Type of research ("individual" or "organization")
        
        Returns:
            List of search results with 'title', 'link', 'snippet' keys
        """
        print("\n" + "="*80)
        print("🔍 WEB SEARCH - STARTING")
        print("="*80)
        print(f"📋 Query: {query}")
        print(f"📊 Research Type: {research_type}")
        print(f"🔢 Max Results: {num_results}")
        print("="*80)
        
        # Try Google Custom Search API first
        if self.google_available:
            try:
                print("\n🌐 Attempting Google Custom Search API...")
                results = await self._search_google(query, num_results, research_type)
                if results:
                    print(f"✅ Google Search successful: {len(results)} results")
                    return results
                else:
                    print("⚠️  Google Search returned no results, trying DuckDuckGo...")
            except Exception as e:
                error_msg = str(e)
                # Only show detailed error if it's not about API access (fallback message already included)
                if "Falling back to DuckDuckGo" in error_msg:
                    print(f"⚠️  {error_msg}")
                else:
                    print(f"⚠️  Google Search failed: {error_msg}")
                    print("   Falling back to DuckDuckGo...")
        
        # Fallback to DuckDuckGo
        print("\n🦆 Using DuckDuckGo search (free fallback)...")
        try:
            results = await self._search_duckduckgo(query, num_results, research_type)
            if results:
                print(f"✅ DuckDuckGo Search successful: {len(results)} results")
                return results
            else:
                print("⚠️  DuckDuckGo Search returned no results")
                return []
        except Exception as e:
            print(f"❌ DuckDuckGo Search failed: {e}")
            return []
    
    async def _search_google(
        self, 
        query: str, 
        num_results: int,
        research_type: str
    ) -> List[Dict[str, Any]]:
        """
        Search using Google Custom Search API
        
        Args:
            query: Search query
            num_results: Number of results (max 10 per request)
            research_type: Type of research
        
        Returns:
            List of search results
        """
        # Google API limits to 10 results per request
        num_results = min(num_results, 10)
        
        # Enhance query based on research type
        if research_type == "organization":
            enhanced_query = f"{query} company official website"
        else:
            enhanced_query = f"{query} professional profile"
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.google_api_key,
            "cx": self.google_cse_id,
            "q": enhanced_query,
            "num": num_results
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get("items", []):
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })
                
                return results
            elif response.status_code == 429:
                # Rate limit exceeded
                raise Exception("Google API rate limit exceeded. Try again later.")
            else:
                error_data = response.json() if response.text else {}
                error_info = error_data.get("error", {})
                error_msg = error_info.get("message", response.text)
                error_code = error_info.get("code", response.status_code)
                error_status = error_info.get("status", "")
                
                # Debug: Print full error details
                print(f"   🔍 Error Code: {error_code}")
                print(f"   🔍 Error Status: {error_status}")
                print(f"   🔍 Error Message: {error_msg}")
                
                # Check for specific error cases
                if error_code == 403 or "access" in error_msg.lower() or "permission" in error_msg.lower():
                    # API not enabled, access denied, or billing issue
                    if "billing" in error_msg.lower() or "quota" in error_msg.lower():
                        raise Exception(
                            f"Google API billing/quota issue: {error_msg}. "
                            f"Please check billing in Google Cloud Console. "
                            f"Falling back to DuckDuckGo..."
                        )
                    else:
                        raise Exception(
                            f"Google Custom Search API access denied (403). "
                            f"Possible causes:\n"
                            f"   1. API key restrictions don't allow Custom Search API\n"
                            f"   2. API key belongs to different project\n"
                            f"   3. Billing not enabled (required even for free tier)\n"
                            f"   Fix: Check API key restrictions in Google Cloud Console → Credentials\n"
                            f"   Falling back to DuckDuckGo..."
                        )
                elif "Custom Search" in error_msg or "Custom Seaarch" in error_msg:
                    raise Exception(
                        f"Google Custom Search API issue: {error_msg}. "
                        f"Falling back to DuckDuckGo..."
                    )
                else:
                    raise Exception(f"Google API error ({error_code}): {error_msg}")
    
    async def _search_duckduckgo(
        self, 
        query: str, 
        num_results: int,
        research_type: str
    ) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo (free, no API key needed)
        Uses Playwright to scrape search results
        
        Args:
            query: Search query
            num_results: Number of results to return
            research_type: Type of research
        
        Returns:
            List of search results
        """
        try:
            # Try multiple DuckDuckGo libraries (new and old)
            try:
                # Try new ddgs library first
                try:
                    from ddgs import DDGS
                    print("   Using ddgs library (new)...")
                except ImportError:
                    # Fallback to old library
                    from duckduckgo_search import DDGS
                    print("   Using duckduckgo-search library (old)...")
                
                # Enhance query based on research type
                if research_type == "organization":
                    enhanced_query = f"{query} company"
                else:
                    enhanced_query = f"{query} profile"
                
                print(f"   Searching DuckDuckGo: {enhanced_query}")
                
                # Use synchronous library in async context
                loop = asyncio.get_event_loop()
                ddgs = await loop.run_in_executor(None, DDGS)
                
                # Search
                results_data = await loop.run_in_executor(
                    None,
                    lambda: list(ddgs.text(enhanced_query, max_results=num_results))
                )
                
                results = []
                for item in results_data:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("href", ""),
                        "snippet": item.get("body", "")
                    })
                
                if results:
                    print(f"   ✅ DuckDuckGo found {len(results)} results")
                else:
                    print(f"   ⚠️  DuckDuckGo returned no results")
                
                return results
                
            except ImportError:
                # Fallback: Use Playwright to scrape DuckDuckGo
                print("   Using Playwright to scrape DuckDuckGo...")
                return await self._search_duckduckgo_playwright(query, num_results, research_type)
                
        except Exception as e:
            print(f"   Error with DuckDuckGo library: {e}")
            # Fallback to Playwright
            return await self._search_duckduckgo_playwright(query, num_results, research_type)
    
    async def _search_duckduckgo_playwright(
        self, 
        query: str, 
        num_results: int,
        research_type: str
    ) -> List[Dict[str, Any]]:
        """
        Search DuckDuckGo using Playwright (fallback method)
        
        Args:
            query: Search query
            num_results: Number of results
            research_type: Type of research
        
        Returns:
            List of search results
        """
        import sys
        import os
        # Add linkedin_scraper to path to use BrowserManager
        linkedin_scraper_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'linkedin_scraper'
        )
        if linkedin_scraper_path not in sys.path:
            sys.path.insert(0, linkedin_scraper_path)
        
        from linkedin_scraper import BrowserManager
        
        # Enhance query
        if research_type == "organization":
            enhanced_query = f"{query} company"
        else:
            enhanced_query = f"{query} profile"
        
        search_url = f"https://html.duckduckgo.com/html/?q={enhanced_query.replace(' ', '+')}"
        
        results = []
        
        try:
            async with BrowserManager(headless=True) as browser:
                page = browser.page
                
                # Navigate to DuckDuckGo
                await page.goto(search_url, wait_until="networkidle")
                await asyncio.sleep(2)  # Wait for results to load
                
                # Extract search results
                result_elements = await page.query_selector_all(".result")
                
                for element in result_elements[:num_results]:
                    try:
                        # Extract title
                        title_elem = await element.query_selector(".result__a")
                        title = await title_elem.inner_text() if title_elem else ""
                        
                        # Extract link
                        link = await title_elem.get_attribute("href") if title_elem else ""
                        
                        # Extract snippet
                        snippet_elem = await element.query_selector(".result__snippet")
                        snippet = await snippet_elem.inner_text() if snippet_elem else ""
                        
                        if title and link:
                            results.append({
                                "title": title.strip(),
                                "link": link.strip(),
                                "snippet": snippet.strip()
                            })
                    except Exception as e:
                        print(f"   Warning: Failed to extract result: {e}")
                        continue
                
                return results
                
        except Exception as e:
            print(f"   Error scraping DuckDuckGo: {e}")
            return []
