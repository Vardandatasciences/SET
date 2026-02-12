"""
DeepSeek Service for Web Scraping
Handles information extraction from non-LinkedIn websites using DeepSeek AI
"""

import httpx
import json
import re
from typing import Dict, Any, Literal, Optional, List
import os
from .data_sources import (
    STANDARD_DATA_SOURCES,
    ORGANIZATION_SEARCH_POINTS,
    DATA_QUALITY_REQUIREMENTS,
    format_sources_for_prompt,
    format_search_points_for_prompt
)


class DeepSeekService:
    """
    Service to fetch and analyze web data using DeepSeek AI
    DeepSeek is a cost-effective AI model for intelligent web scraping
    """
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is required. Please set it in your .env file.")
        
        self.api_key = api_key.strip().strip('"').strip("'")
        # DeepSeek uses OpenAI-compatible API
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def fetch_research_data(
        self, 
        query: str, 
        research_type: Literal["individual", "organization"],
        sources: list = None,
        verified_profile: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive research data using DeepSeek AI
        
        Args:
            query: The search query (individual name or organization name)
            research_type: Type of research ("individual" or "organization")
            sources: List of source dictionaries with 'name' and 'link' keys
            verified_profile: Optional pre-verified profile data
        
        Returns:
            Dictionary containing raw_response, sources, query, and research_type
        """
        print("\n" + "="*80)
        print("🤖 DEEPSEEK AI - STARTING RESEARCH REQUEST")
        print("="*80)
        print(f"📋 Query: {query}")
        print(f"📊 Research Type: {research_type}")
        print(f"📎 Sources Provided: {len(sources) if sources else 0}")
        
        # Validate and clean sources
        if sources:
            print("\n📌 VALIDATING USER-PROVIDED SOURCES:")
            validated_sources = []
            for idx, source in enumerate(sources, 1):
                if isinstance(source, dict) and source.get('link'):
                    validated_source = {
                        'name': source.get('name', 'Unknown Source'),
                        'link': source.get('link', '').strip()
                    }
                    validated_sources.append(validated_source)
                    print(f"  ✅ Source {idx}: {validated_source['name']}")
                    print(f"     🔗 Link: {validated_source['link']}")
                else:
                    print(f"  ❌ Source {idx}: Invalid format or missing link - SKIPPED")
            
            sources = validated_sources if validated_sources else None
            if sources:
                print(f"\n✓ Total Valid Sources: {len(sources)}")
            else:
                print("\n⚠️  No valid sources after validation")
        else:
            print("ℹ️  No sources provided - will search broadly across internet")
        
        print("\n" + "-"*80)
        if research_type == "individual":
            print("🔨 Building INDIVIDUAL research prompt...")
            prompt = self._build_individual_prompt(query, sources, verified_profile)
        else:
            print("🔨 Building ORGANIZATION research prompt...")
            prompt = self._build_organization_prompt(query, sources)
        
        print(f"📝 Prompt length: {len(prompt)} characters")
        print("-"*80)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            # DeepSeek models
            models_to_try = [
                "deepseek-chat",
                "deepseek-reasoner"
            ]
            
            print("\n🤖 ATTEMPTING API CALLS WITH DEEPSEEK MODELS:")
            print(f"📋 Models to try: {', '.join(models_to_try)}")
            print("-"*80)
            
            last_error = None
            for idx, model in enumerate(models_to_try, 1):
                try:
                    print(f"\n🔄 Attempt {idx}/{len(models_to_try)}: Trying model '{model}'...")
                    response = await client.post(
                        self.base_url,
                        headers=self.headers,
                        json={
                            "model": model,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": self._get_system_prompt(research_type)
                                },
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ],
                            "temperature": 0.2,
                            "max_tokens": 4000,
                            "stream": False
                        }
                    )
                    
                    if response.status_code == 200:
                        print(f"✅ SUCCESS with model '{model}'!")
                        print("-"*80)
                        
                        result = response.json()
                        message_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        
                        print(f"\n📊 RESPONSE DETAILS:")
                        print(f"   📏 Response length: {len(message_content)} characters")
                        print(f"   📝 Response preview: {message_content[:200]}...")
                        
                        # Extract citations/sources from response
                        citations = self._extract_sources_from_response(message_content)
                        
                        print(f"\n📚 SOURCES/CITATIONS FOUND:")
                        if citations:
                            print(f"   ✓ Total citations extracted: {len(citations)}")
                            for idx, citation in enumerate(citations[:10], 1):
                                print(f"   [{idx}] {citation}")
                            if len(citations) > 10:
                                print(f"   ... and {len(citations) - 10} more")
                        else:
                            print("   ⚠️  No citations found in response")
                        
                        print("\n" + "="*80)
                        print("✅ RESEARCH COMPLETED SUCCESSFULLY")
                        print("="*80 + "\n")
                        
                        return {
                            "raw_response": message_content,
                            "sources": citations,
                            "query": query,
                            "research_type": research_type,
                            "verified_profile": verified_profile
                        }
                    elif response.status_code == 401:
                        print(f"❌ AUTHENTICATION ERROR (401) with model '{model}'")
                        error_msg = f"DeepSeek API authentication failed. Please verify your API key."
                        print(f"💥 {error_msg}")
                        raise Exception(error_msg)
                    elif response.status_code == 400:
                        last_error = f"Model '{model}' request error (400). Response: {response.text[:300]}"
                        print(f"⚠️  {last_error}")
                        continue
                    else:
                        last_error = f"API error {response.status_code}: {response.text[:300]}"
                        print(f"⚠️  {last_error}")
                        continue
                        
                except Exception as e:
                    if "401" in str(e):
                        print(f"💥 Fatal authentication error - stopping all attempts")
                        raise
                    last_error = str(e)
                    print(f"⚠️  Exception with model '{model}': {last_error}")
                    continue
            
            print("\n" + "="*80)
            print("❌ ALL MODEL ATTEMPTS FAILED")
            print("="*80)
            print(f"💥 Last error: {last_error}")
            print("="*80 + "\n")
            raise Exception(f"All DeepSeek model attempts failed. Last error: {last_error}")
    
    def _extract_sources_from_response(self, content: str) -> List[str]:
        """Extract URLs and citations from response text"""
        citations = []
        
        # Extract URLs
        url_pattern = r'https?://[^\s\)\]\>]+'
        urls = re.findall(url_pattern, content)
        citations.extend(urls)
        
        # Extract [Source: ...] style citations
        source_pattern = r'\[([^\]]+)\]'
        source_refs = re.findall(source_pattern, content)
        citations.extend(source_refs)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_citations = []
        for citation in citations:
            if citation not in seen:
                seen.add(citation)
                unique_citations.append(citation)
        
        return unique_citations
    
    def _get_system_prompt(self, research_type: str) -> str:
        """Get the appropriate system prompt based on research type"""
        if research_type == "individual":
            return """You are a comprehensive research assistant specializing in individual/person research.

Your task is to find accurate, up-to-date information about individuals from publicly available sources.

CRITICAL INSTRUCTIONS:
1. Search across multiple reputable sources (company websites, news articles, professional profiles, publications)
2. Verify information across multiple sources when possible
3. Include specific URLs/sources for every piece of information
4. If information is not found or uncertain, explicitly state "Not found" or "Unverified"
5. Focus on professional, publicly available information only

CITATION FORMAT:
- Include [Source: URL] after each fact
- Prefer official company websites and reputable news sources
- Note the date of information when available"""
        else:
            return """You are a comprehensive research assistant for organization research.

Your task is to extract accurate, comprehensive information about organizations from publicly available sources.

CRITICAL INSTRUCTIONS:
1. Visit and extract information from the company's official website first
2. Search regulatory filings (SEC, SEBI), financial news, industry reports
3. Verify financial data from official sources
4. Include both positive developments and challenges/risks
5. Cite specific sources with URLs for every piece of information
6. Paraphrase all information for clarity
7. Present in clear, concise language suitable for business professionals

CITATION FORMAT:
- Include [Source: URL] after each fact
- Prioritize official sources (company website, regulatory filings, official announcements)
- Note the date of information when available"""
    
    def _build_individual_prompt(
        self, 
        query: str, 
        sources: list = None,
        verified_profile: Dict[str, Any] = None
    ) -> str:
        """Build comprehensive prompt for individual research"""
        individual_name = query.strip()
        
        prompt = f"""
Research the following individual: {individual_name}

Please provide comprehensive information in these sections:

1. **Professional Background**
   - Current position and company
   - Previous positions and career history
   - Years of experience
   - Industry expertise
   - LinkedIn or professional profile URL

2. **Education & Certifications**
   - Universities attended
   - Degrees obtained
   - Graduation years
   - Professional certifications

3. **Current Company Information**
   - Company name and website
   - Company size and industry
   - Company headquarters
   - Person's role and responsibilities

4. **Public Presence & Online Activity**
   - Professional social media profiles
   - Recent posts or articles
   - Publications or research papers
   - Speaking engagements or conferences
   - Media mentions

5. **Professional Network**
   - Professional associations or memberships
   - Board positions
   - Advisory roles

6. **Recent Activity**
   - Latest career developments
   - Recent projects or initiatives
   - Public statements or interviews

CRITICAL REQUIREMENTS:
- Include source URLs for every fact [Source: URL]
- If information is not available, state "Not found"
- Focus on publicly available professional information only
"""
        
        if sources:
            sources_list = "\n".join([f"   - {source.get('name', 'Unknown')}: {source.get('link', '')}" for source in sources])
            prompt += f"""

REFERENCE SOURCES PROVIDED:
{sources_list}

Start by checking these sources, then search broadly across the internet for additional information.
"""
        
        if verified_profile:
            company = verified_profile.get('company', '')
            title = verified_profile.get('title', '')
            prompt += f"""

VERIFIED INFORMATION (Use this to identify the correct person):
- Company: {company}
- Job Title: {title}
- Location: {verified_profile.get('location', 'Not provided')}

This information is authoritative. Only include information about the person at {company}.
"""
        
        return prompt
    
    def _build_organization_prompt(self, query: str, sources: list = None) -> str:
        """Build comprehensive prompt for organization research"""
        company_name = query.strip()
        
        # Format standard data sources
        standard_sources = format_sources_for_prompt()
        standard_search_points = format_search_points_for_prompt()
        
        prompt = f"""
Conduct comprehensive research on the following organization: {company_name}

PRIORITY 1: VISIT THE OFFICIAL COMPANY WEBSITE
1. Find and visit the official website for {company_name}
2. Extract information from these pages:
   - /about or /about-us (company background, mission, history)
   - /team or /leadership (executive team with names and titles)
   - /contact (office locations, contact information)
   - /services or /products (offerings)
   - /careers (company size, culture)
   - /news or /blog (recent announcements)
   - /investors (financial information if public company)

PRIORITY 2: SEARCH STANDARD DATA SOURCES
{standard_sources}

PRIORITY 3: KEY SEARCH POINTS
{standard_search_points}

REQUIRED INFORMATION SECTIONS:

1. **Company Background**
   - Full company name
   - Industry and sector
   - Headquarters location
   - Founded (year and founders)
   - Number of employees
   - Mission and vision
   - Products and services

2. **Leadership Intelligence**
   - CEO, CFO, CTO, CIO names and titles (from company website)
   - Board members and directors
   - Recent leadership changes
   - Executive communications or messages

3. **Financial Information**
   - Revenue and funding (if available)
   - Recent financial performance
   - Funding rounds or investments
   - Stock information (if public company)
   - Financial challenges or strengths

4. **News Intelligence (Last 7-10 years)**
   - Positive developments (partnerships, awards, expansions)
   - Negative events (controversies, lawsuits, setbacks)
   - Neutral news (general announcements, events)
   - Recent press releases

5. **Challenges & Risks**
   - External challenges (market, competition, regulatory)
   - Internal challenges (operational, organizational)
   - Public controversies or issues
   - Risk factors (from filings if public company)

6. **Strategic Priorities**
   - Current initiatives and projects
   - Digital transformation efforts
   - Market expansion plans
   - Cost reduction or efficiency measures
   - Innovation and R&D focus

7. **Recent Activity**
   - Latest news and announcements
   - Recent partnerships or collaborations
   - New product launches
   - Office openings or expansions

DATA QUALITY REQUIREMENTS:
- Paraphrase all information for clarity
- NO REPETITION of information
- CITE SOURCE [Source: URL] after each fact
- Use clear, concise language
- Maintain balanced view (both positive and challenges)
- Include dates when mentioning events or changes
"""
        
        if sources:
            sources_list = "\n".join([f"   - {source.get('name', 'Unknown')}: {source.get('link', '')}" for source in sources])
            prompt += f"""

USER-PROVIDED REFERENCE SOURCES:
{sources_list}

Use these as starting points, then search broadly for comprehensive information.
"""
        
        return prompt
