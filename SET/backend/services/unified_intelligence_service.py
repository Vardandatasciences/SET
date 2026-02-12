"""
Unified Intelligence Service
Routes requests to appropriate services based on source type:
- LinkedIn data -> LinkedIn Scraper
- All other sources -> Google Search API (extracts data directly from search results)
"""

import os
from typing import Dict, Any, Literal, Optional, List
import re

from .ollama_service import OllamaService
from .linkedin_scraper_service import LinkedInScraperService
from .web_search_service import WebSearchService
from .web_scraper_service import WebScraperService


class UnifiedIntelligenceService:
    """
    Unified service that intelligently routes data fetching:
    - LinkedIn URLs -> LinkedIn Scraper (direct scraping)
    - All other sources -> Google Search API (extracts data directly from search results)
    """
    
    def __init__(self, ollama_base_url: str = None, ollama_model: str = None):
        """
        Initialize the unified intelligence service
        
        Args:
            ollama_base_url: Ollama API URL (default: http://13.205.15.232:11434)
            ollama_model: Model to use (default: deepseek-r1:8b)
        """
        # Check if AI web intelligence should be disabled
        self.disable_ai_web_intelligence = os.getenv("DISABLE_AI_WEB_INTELLIGENCE", "false").lower() == "true"
        
        if self.disable_ai_web_intelligence:
            print("⚠️  AI Web Intelligence DISABLED - Using LinkedIn data only")
            print("   This provides 100% accurate, verified data")
            self.ollama_service = None
        else:
            # Initialize Ollama service (FREE, LOCAL)
            self.ollama_service = OllamaService(
                base_url=ollama_base_url or os.getenv("OLLAMA_BASE_URL"),
                model=ollama_model or os.getenv("OLLAMA_MODEL")
            )
            print("✅ Ollama service initialized (FREE - No API costs!)")
        
        # Initialize LinkedIn scraper service
        self.linkedin_service = LinkedInScraperService()
        print("✅ LinkedIn scraper service initialized")
        
        # Initialize web search service (Google Search API for data extraction)
        self.web_search_service = WebSearchService()
        
        # Web scraper service kept for potential fallback scenarios
        self.web_scraper_service = WebScraperService()
    
    async def fetch_research_data(
        self, 
        query: str, 
        research_type: Literal["individual", "organization"],
        sources: list = None,
        verified_profile: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Fetch research data using the appropriate service
        
        Args:
            query: The search query (individual name or organization name)
            research_type: Type of research ("individual" or "organization")
            sources: List of source dictionaries with 'name' and 'link' keys
            verified_profile: Optional pre-verified profile data
        
        Returns:
            Dictionary containing raw_response, sources, query, research_type, and linkedin_data if available
        """
        print("\n" + "="*80)
        print("🚀 UNIFIED INTELLIGENCE SERVICE - REQUEST RECEIVED")
        print("="*80)
        print(f"📋 Query: {query}")
        print(f"📊 Research Type: {research_type}")
        print(f"📎 Sources: {len(sources) if sources else 0}")
        print("="*80)
        
        # Step 1: Check if we have LinkedIn URLs and can scrape them
        linkedin_data = None
        linkedin_urls = self._extract_linkedin_urls(sources)
        
        if linkedin_urls:
            print("\n🔗 LINKEDIN URLs DETECTED")
            print("="*80)
            for url in linkedin_urls:
                print(f"  • {url}")
            print("="*80)
            
            if research_type == "individual":
                # Try to scrape LinkedIn profile
                profile_url = next((url for url in linkedin_urls if '/in/' in url), None)
                if profile_url:
                    print(f"\n🎯 Attempting to scrape LinkedIn profile: {profile_url}")
                    linkedin_data = await self.linkedin_service.get_person_from_url(profile_url)
                    
                    if linkedin_data:
                        print("✅ Successfully scraped LinkedIn profile!")
                    else:
                        print("⚠️  LinkedIn profile scraping failed, will use web search")
            
            elif research_type == "organization":
                # Try to scrape LinkedIn company page
                company_url = next((url for url in linkedin_urls if '/company/' in url), None)
                if company_url:
                    print(f"\n🎯 Attempting to scrape LinkedIn company: {company_url}")
                    linkedin_data = await self.linkedin_service.get_company_from_url(company_url)
                    
                    if linkedin_data:
                        print("✅ Successfully scraped LinkedIn company!")
                    else:
                        print("⚠️  LinkedIn company scraping failed, will use web search")
        
        # Step 2: Use Google Search API for all non-LinkedIn sources
        google_search_data = []
        
        # Check if we need to search (if no LinkedIn data or if there are non-LinkedIn sources)
        non_linkedin_sources = []
        if sources:
            for source in sources:
                link = source.get('link', '').strip()
                if link and not self._is_linkedin_url(link):
                    non_linkedin_sources.append(source)
        
        # Use Google Search API for data extraction
        if not linkedin_data or non_linkedin_sources:
            print("\n" + "="*80)
            print("🔍 USING GOOGLE SEARCH API FOR DATA EXTRACTION")
            print("="*80)
            
            # Build search query
            if non_linkedin_sources:
                # If specific sources provided, search for those
                search_queries = []
                for source in non_linkedin_sources:
                    source_name = source.get('name', '')
                    source_link = source.get('link', '')
                    if source_link:
                        # Extract domain or use source name
                        if source_name:
                            search_queries.append(f"{query} {source_name}")
                        else:
                            search_queries.append(f"{query} site:{source_link}")
                search_query = " OR ".join(search_queries[:3])  # Limit to 3 queries
            else:
                # General search for the query
                search_query = query
            
            # Search using Google Search API
            search_results = await self.web_search_service.search(
                query=search_query,
                num_results=10,
                research_type=research_type
            )
            
            if search_results:
                print(f"\n✅ Google Search API returned {len(search_results)} results")
                # Format Google Search results as data
                google_search_data = self._format_google_search_results(search_results)
                print(f"   Extracted data from {len(google_search_data)} sources")
            else:
                print("⚠️  Google Search API returned no results")
                # Try fallback search with just the query
                if search_query != query:
                    print("   Trying fallback search with original query...")
                    search_results = await self.web_search_service.search(
                        query=query,
                        num_results=10,
                        research_type=research_type
                    )
                    if search_results:
                        google_search_data = self._format_google_search_results(search_results)
                        print(f"   ✅ Fallback search found {len(google_search_data)} results")
        
        # Step 3: Process Google Search API data
        ai_data = None
        
        if self.disable_ai_web_intelligence:
            print("\n" + "="*80)
            print("⏭️  AI WEB INTELLIGENCE DISABLED")
            print("="*80)
            print("   Using Google Search API data only (100% accurate)")
            print("   To enable AI analysis, set DISABLE_AI_WEB_INTELLIGENCE=false")
            print("="*80)
            
            # Create response from Google Search API data only
            if google_search_data:
                combined_text = self._format_google_search_data(google_search_data)
                ai_data = {
                    "raw_response": combined_text,
                    "sources": [item['link'] for item in google_search_data],
                    "query": query,
                    "research_type": research_type
                }
            else:
                ai_data = {
                    "raw_response": "",
                    "sources": [],
                    "query": query,
                    "research_type": research_type
                }
        else:
            print("\n" + "="*80)
            print("🤖 USING OLLAMA TO ANALYZE GOOGLE SEARCH API DATA")
            print("="*80)
            
            # Prepare sources with Google Search API data for Ollama
            enhanced_sources = []
            
            # Add Google Search API results as sources
            for item in google_search_data:
                enhanced_sources.append({
                    "name": item.get('title', 'Google Search Result'),
                    "link": item.get('link', ''),
                    "content": item.get('snippet', '')  # Include snippet from Google Search
                })
            
            # Add original non-LinkedIn sources (if any)
            if sources:
                for source in sources:
                    link = source.get('link', '').strip()
                    if link and not self._is_linkedin_url(link):
                        enhanced_sources.append(source)
            
            if enhanced_sources:
                print(f"📎 Passing {len(enhanced_sources)} Google Search API results to Ollama")
            else:
                print("📎 No sources to analyze, Ollama will use general knowledge")
            
            # Fetch data using Ollama with Google Search API data
            try:
                ai_data = await self.ollama_service.fetch_research_data(
                    query=query,
                    research_type=research_type,
                    sources=enhanced_sources,
                    verified_profile=verified_profile
                )
            except Exception as e:
                print(f"❌ Error fetching AI data: {e}")
                # Fallback: Use Google Search API data directly
                if google_search_data:
                    print("   Using Google Search API data directly (without AI analysis)")
                    combined_text = self._format_google_search_data(google_search_data)
                    ai_data = {
                        "raw_response": combined_text,
                        "sources": [item['link'] for item in google_search_data],
                        "query": query,
                        "research_type": research_type
                    }
                elif linkedin_data:
                    ai_data = {
                        "raw_response": "Ollama unavailable, showing LinkedIn data only.",
                        "sources": [],
                        "query": query,
                        "research_type": research_type
                    }
                else:
                    raise
        
        # Step 3: Combine LinkedIn data with AI intelligence
        if linkedin_data and ai_data:
            print("\n" + "="*80)
            print("🔄 COMBINING LINKEDIN DATA WITH AI INTELLIGENCE")
            print("="*80)
            
            # Prepend LinkedIn data to the response
            if research_type == "individual":
                linkedin_text = self.linkedin_service.transform_person_for_set(linkedin_data)
            else:
                linkedin_text = self.linkedin_service.transform_company_for_set(linkedin_data)
            
            combined_response = f"""{linkedin_text}

{"="*80}
ADDITIONAL WEB INTELLIGENCE (from Google Search API)
{"="*80}

{ai_data.get('raw_response', '')}
"""
            
            result = {
                "raw_response": combined_response,
                "sources": ai_data.get('sources', []),
                "query": query,
                "research_type": research_type,
                "linkedin_data": linkedin_data,
                "verified_profile": verified_profile
            }
            
            print("✅ Combined LinkedIn data with web intelligence")
            
        elif linkedin_data:
            # Only LinkedIn data available
            print("\n⚠️  Only LinkedIn data available")
            linkedin_text = self.linkedin_service.transform_person_for_set(linkedin_data) if research_type == "individual" else self.linkedin_service.transform_company_for_set(linkedin_data)
            
            result = {
                "raw_response": linkedin_text,
                "sources": [linkedin_data.get('linkedin_url', '')],
                "query": query,
                "research_type": research_type,
                "linkedin_data": linkedin_data,
                "verified_profile": verified_profile
            }
            
        else:
            # Only AI data available
            result = ai_data
        
        print("\n" + "="*80)
        print("✅ UNIFIED INTELLIGENCE SERVICE - COMPLETED")
        print("="*80)
        print(f"📏 Response length: {len(result.get('raw_response', ''))} characters")
        print(f"📚 Sources: {len(result.get('sources', []))}")
        print(f"🔗 LinkedIn data: {'Yes' if linkedin_data else 'No'}")
        print("="*80 + "\n")
        
        return result
    
    def _extract_linkedin_urls(self, sources: list) -> List[str]:
        """Extract LinkedIn URLs from sources list"""
        if not sources:
            return []
        
        linkedin_urls = []
        for source in sources:
            link = source.get('link', '').strip()
            if self._is_linkedin_url(link):
                linkedin_urls.append(link)
        
        return linkedin_urls
    
    def _is_linkedin_url(self, url: str) -> bool:
        """Check if URL is a LinkedIn URL"""
        if not url:
            return False
        return 'linkedin.com/in/' in url.lower() or 'linkedin.com/company/' in url.lower()
    
    def _format_google_search_results(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format Google Search API results into structured data"""
        formatted_results = []
        
        for result in search_results:
            formatted_results.append({
                "title": result.get('title', ''),
                "link": result.get('link', ''),
                "snippet": result.get('snippet', '')
            })
        
        return formatted_results
    
    def _format_google_search_data(self, google_data: List[Dict[str, Any]]) -> str:
        """Format Google Search API data into readable text"""
        if not google_data:
            return ""
        
        formatted = []
        formatted.append("="*80)
        formatted.append("GOOGLE SEARCH API DATA")
        formatted.append("="*80)
        formatted.append("")
        
        for idx, item in enumerate(google_data, 1):
            formatted.append(f"[{idx}] {item.get('title', 'Untitled')}")
            formatted.append(f"URL: {item.get('link', 'N/A')}")
            formatted.append("-"*80)
            
            snippet = item.get('snippet', '')
            if snippet:
                formatted.append(snippet)
            else:
                formatted.append("(No snippet available)")
            
            formatted.append("")
            formatted.append("="*80)
            formatted.append("")
        
        return "\n".join(formatted)