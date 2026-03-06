"""
Ollama Service for Free Local AI Intelligence
Handles information extraction using Ollama (free, local, open-source)
No API costs - runs completely on your local machine
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


class OllamaService:
    """
    Service to fetch and analyze web data using Ollama (FREE, LOCAL)
    
    Ollama runs AI models locally on your machine - completely free!
    No API keys needed, no costs, full privacy.
    
    Supported models:
    - deepseek-r1 (Latest DeepSeek model - DEFAULT)
    - llama3.1 (Meta's Llama)
    - mistral (Fast and efficient)
    - qwen2.5 (Alibaba's model)
    And many more!
    """
    
    def __init__(self, base_url: str = None, model: str = None):
        """
        Initialize Ollama service
        
        Args:
            base_url: Ollama API URL (default: http://13.205.15.232:11434)
            model: Model name to use (default: deepseek-r1:8b)
        """
        # Ollama cloud instance
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://13.205.15.232:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
        self.api_url = f"{self.base_url}/api/chat"
        
        print(f"🤖 Ollama Service initialized")
        print(f"   📍 URL: {self.base_url}")
        print(f"   🧠 Model: {self.model}")
    
    async def check_ollama_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            print(f"⚠️  Ollama not reachable: {e}")
            return False
    
    async def check_model_available(self) -> bool:
        """Check if the specified model is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get('name', '') for m in data.get('models', [])]
                    # Check if model exists (with or without tag)
                    model_base = self.model.split(':')[0]
                    return any(model_base in m for m in models)
        except Exception:
            pass
        return False
    
    async def fetch_research_data(
        self, 
        query: str, 
        research_type: Literal["individual", "organization"],
        sources: list = None,
        verified_profile: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive research data using Ollama (FREE)
        
        Args:
            query: The search query (individual name or organization name)
            research_type: Type of research ("individual" or "organization")
            sources: List of source dictionaries with 'name' and 'link' keys
            verified_profile: Optional pre-verified profile data
        
        Returns:
            Dictionary containing raw_response, sources, query, and research_type
        """
        print("\n" + "="*80)
        print("🤖 OLLAMA (FREE LOCAL AI) - STARTING RESEARCH REQUEST")
        print("="*80)
        print(f"📋 Query: {query}")
        print(f"📊 Research Type: {research_type}")
        print(f"📎 Sources Provided: {len(sources) if sources else 0}")
        print(f"🧠 Model: {self.model}")
        
        # Check if Ollama is running
        if not await self.check_ollama_available():
            error_msg = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ⚠️  OLLAMA IS NOT RUNNING                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 TO START OLLAMA:

   Windows:
      1. Press Windows key and search for "Ollama"
      2. Click to open Ollama application
      3. Wait for it to start (check system tray in bottom-right)
      4. You should see Ollama icon in system tray when running

   Mac:
      1. Open Finder → Applications
      2. Find and open "Ollama"
      3. Wait for it to start (check menu bar)

   Linux:
      1. Run: systemctl start ollama
      2. Or run: ollama serve
      3. Check status: systemctl status ollama

   Download Ollama:
      Visit: https://ollama.ai/download

💡 After starting Ollama:
   1. Wait 5-10 seconds for it to fully start
   2. Verify it's running: ollama list
   3. Restart this server (python main.py)
   4. Try your request again

🔍 Troubleshooting:
   - Check if Ollama is in system tray (Windows) or menu bar (Mac)
   - Try: curl http://localhost:11434/api/tags
   - If that works, Ollama is running but server needs restart
"""
            raise Exception(error_msg)
        
        # Check if model is available
        if not await self.check_model_available():
            print(f"\n⚠️  Model '{self.model}' not found!")
            print(f"💡 Downloading model... (this may take a few minutes)")
            print(f"   Run: ollama pull {self.model}")
            raise Exception(
                f"Model '{self.model}' not available. Please run:\n"
                f"  ollama pull {self.model}\n"
                f"Or choose a different model (llama3.1, mistral, etc.)"
            )
        
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
        
        # Call Ollama API
        print(f"\n🔄 Sending request to Ollama (model: {self.model})...")
        
        async with httpx.AsyncClient(timeout=900.0) as client:  # Extended timeout for large models (15 minutes)
            try:
                # First, verify the model exists
                print(f"🔍 Verifying model '{self.model}' is available...")
                model_check = await client.get(f"{self.base_url}/api/tags")
                if model_check.status_code == 200:
                    models_data = model_check.json()
                    available_models = [m.get('name', '') for m in models_data.get('models', [])]
                    model_base = self.model.split(':')[0]
                    if not any(model_base in m for m in available_models):
                        error_msg = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ⚠️  MODEL NOT FOUND                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Model '{self.model}' is not available.

Available models:
{chr(10).join(f'   • {m}' for m in available_models) if available_models else '   (none)'}

💡 TO FIX:
   1. Download the model:
      ollama pull {self.model}
   
   2. OR use an available model by updating .env:
      OLLAMA_MODEL={available_models[0] if available_models else 'llama3.1:8b'}

⏱️  Download time: 5-15 minutes (one-time only)
"""
                        print(error_msg)
                        raise Exception(f"Model '{self.model}' not found. Available: {', '.join(available_models) if available_models else 'none'}")
                    print(f"✅ Model '{self.model}' is available")
                
                # Make the API call
                print(f"📤 Sending request to Ollama...")
                response = await client.post(
                    self.api_url,
                    json={
                        "model": self.model,
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
                        "stream": False,
                        "options": {
                            "temperature": 0.2,
                            "num_predict": 4000
                        }
                    }
                )
                
                if response.status_code == 200:
                    print(f"✅ SUCCESS with Ollama!")
                    print("-"*80)
                    
                    result = response.json()
                    message_content = result.get("message", {}).get("content", "")
                    
                    if not message_content:
                        # Check if there's an error in the response
                        error_info = result.get("error", "")
                        if error_info:
                            raise Exception(f"Ollama returned error: {error_info}")
                        raise Exception("Ollama returned empty response. Check model is working: ollama run " + self.model)
                    
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
                    print("✅ RESEARCH COMPLETED SUCCESSFULLY (FREE - NO API COSTS!)")
                    print("="*80 + "\n")
                    
                    return {
                        "raw_response": message_content,
                        "sources": citations,
                        "query": query,
                        "research_type": research_type,
                        "verified_profile": verified_profile
                    }
                else:
                    error_text = response.text[:500] if response.text else "No error details"
                    error_msg = f"Ollama API error {response.status_code}: {error_text}"
                    print(f"❌ {error_msg}")
                    print(f"   Full response: {response.text}")
                    raise Exception(error_msg)
                    
            except httpx.TimeoutException:
                error_msg = f"Ollama request timed out after 300 seconds. The model might be too slow or your system needs more resources."
                print(f"❌ {error_msg}")
                print("💡 Try a smaller/faster model: ollama pull llama3.1:8b")
                raise Exception(error_msg)
            except httpx.ConnectError:
                error_msg = "Cannot connect to Ollama. Make sure Ollama is running."
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            except Exception as e:
                error_details = str(e) if str(e) else f"Unknown error: {type(e).__name__}"
                print(f"❌ Error calling Ollama: {error_details}")
                print(f"   Error type: {type(e).__name__}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()}")
                raise Exception(f"Ollama request failed: {error_details}")
    
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
        
        # Check if we have company name for disambiguation
        company_name = verified_profile.get('company', '') if verified_profile else ''
        
        if company_name:
            # Company name provided - focus on this specific person
            prompt = f"""
Research the following individual: {individual_name} who works at {company_name}

⚠️ CRITICAL: There may be multiple people named "{individual_name}". You MUST search for and include information ONLY about the person who works at {company_name}.

DISAMBIGUATION INSTRUCTIONS:
1. Search for "{individual_name}" AND "{company_name}" together
2. Look for company website team pages, LinkedIn profiles mentioning {company_name}
3. Verify that all information you provide is specifically about the person at {company_name}
4. If you find information about other people with the same name, IGNORE IT
5. If you cannot find information about {individual_name} at {company_name}, state "Not found at {company_name}"

Please provide comprehensive information in these sections:

1. **Professional Background**
   - Current position at {company_name} (VERIFY this is the correct company)
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
   - Role and responsibilities at {company_name}
   - Company website: Check {company_name}'s team/about page
   - Department or team
   - Direct reports or team size (if available)

4. **Public Presence & Online Activity**
   - Professional social media profiles (verify they mention {company_name})
   - Recent posts or articles
   - Publications or research papers
   - Speaking engagements or conferences
   - Media mentions

5. **Professional Network**
   - Professional associations or memberships
   - Board positions
   - Advisory roles

6. **Recent Activity**
   - Latest career developments at {company_name}
   - Recent projects or initiatives
   - Public statements or interviews

CRITICAL REQUIREMENTS:
- Include source URLs for every fact [Source: URL]
- ONLY include information about {individual_name} at {company_name}
- If information is not available, state "Not found"
- Focus on publicly available professional information only
"""
        else:
            # No company name - general search with warning
            prompt = f"""
Research the following individual: {individual_name}

⚠️ WARNING: No company name provided for disambiguation. There may be multiple people with this name.
If you find multiple people named "{individual_name}", provide a brief summary and suggest that the user provide a company name for accurate results.

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
- If you find multiple people with this name, mention it
- If information is not available, state "Not found"
- Focus on publicly available professional information only
"""
        
        if sources:
            # Check if sources have scraped content
            sources_with_content = [s for s in sources if s.get('content')]
            sources_without_content = [s for s in sources if not s.get('content')]
            
            if sources_with_content:
                prompt += f"""

SCRAPED WEB CONTENT (REAL DATA FROM WEBSITES):
"""
                for idx, source in enumerate(sources_with_content, 1):
                    content = source.get('content', '')
                    # Truncate very long content
                    if len(content) > 3000:
                        content = content[:3000] + "... [truncated]"
                    
                    prompt += f"""
[Source {idx}] {source.get('name', 'Unknown')}
URL: {source.get('link', 'N/A')}
Content:
{content}

"""
            
            if sources_without_content:
                sources_list = "\n".join([f"   - {source.get('name', 'Unknown')}: {source.get('link', '')}" for source in sources_without_content])
                prompt += f"""

ADDITIONAL REFERENCE SOURCES (URLs only):
{sources_list}
"""
            
            if sources_with_content:
                prompt += """
IMPORTANT: Use the scraped content above as your PRIMARY source of information. 
This is real, current data extracted from websites. Analyze this content thoroughly.
"""
        
        if verified_profile:
            title = verified_profile.get('title', '')
            location = verified_profile.get('location', '')
            if title or location:
                prompt += f"""

ADDITIONAL VERIFIED INFORMATION:
"""
                if title:
                    prompt += f"- Job Title: {title}\n"
                if location:
                    prompt += f"- Location: {location}\n"
                
                prompt += f"\nUse this information to verify you have the correct person."
        
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
            # Check if sources have scraped content
            sources_with_content = [s for s in sources if s.get('content')]
            sources_without_content = [s for s in sources if not s.get('content')]
            
            if sources_with_content:
                prompt += f"""

SCRAPED WEB CONTENT (REAL DATA FROM WEBSITES):
"""
                for idx, source in enumerate(sources_with_content, 1):
                    content = source.get('content', '')
                    # Truncate very long content
                    if len(content) > 3000:
                        content = content[:3000] + "... [truncated]"
                    
                    prompt += f"""
[Source {idx}] {source.get('name', 'Unknown')}
URL: {source.get('link', 'N/A')}
Content:
{content}

"""
            
            if sources_without_content:
                sources_list = "\n".join([f"   - {source.get('name', 'Unknown')}: {source.get('link', '')}" for source in sources_without_content])
                prompt += f"""

ADDITIONAL REFERENCE SOURCES (URLs only):
{sources_list}
"""
            
            if sources_with_content:
                prompt += """
IMPORTANT: Use the scraped content above as your PRIMARY source of information. 
This is real, current data extracted from websites. Analyze this content thoroughly and cite the URLs.
"""
        
        return prompt
