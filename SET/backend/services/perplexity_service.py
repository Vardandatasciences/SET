import httpx
import json
import re
from typing import Dict, Any, Literal, Optional
import os
from .data_sources import (
    EXECUTIVE_ROLES,
    STANDARD_DATA_SOURCES,
    ORGANIZATION_SEARCH_POINTS,
    DATA_QUALITY_REQUIREMENTS,
    format_sources_for_prompt,
    format_search_points_for_prompt
)


class LinkedInDataService:
    """
    Service to fetch LinkedIn profile data using Proxycurl API
    Sign up at https://proxycurl.com to get an API key
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("PROXYCURL_API_KEY")
        self.base_url = "https://nubela.co/proxycurl/api/v2/linkedin"
    
    async def get_profile(self, linkedin_url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch LinkedIn profile data from Proxycurl
        Returns None if API key not configured or request fails
        """
        if not self.api_key:
            print("⚠️  PROXYCURL_API_KEY not configured - LinkedIn data fetch skipped")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.base_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={"url": linkedin_url}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"⚠️  Proxycurl API error: {response.status_code}")
                    return None
        except Exception as e:
            print(f"⚠️  Proxycurl request failed: {e}")
            return None


class PerplexityService:
    def __init__(self, api_key: str, proxycurl_api_key: str = None):
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY is required. Please set it in your .env file.")
        # Clean the API key (remove whitespace, quotes, etc.)
        self.api_key = api_key.strip().strip('"').strip("'")
        if not self.api_key.startswith("pplx-"):
            print(f"WARNING: API key doesn't start with 'pplx-'. Current format: {self.api_key[:10]}...")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Initialize LinkedIn data service
        self.linkedin_service = LinkedInDataService(proxycurl_api_key)
    
    async def fetch_research_data(
        self, 
        query: str, 
        research_type: Literal["individual", "organization"],
        sources: list = None,
        # NEW: Optional pre-verified profile data from user
        verified_profile: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive research data from Perplexity API
        
        Args:
            query: The search query (individual name or organization name)
            research_type: Type of research ("individual" or "organization")
            sources: List of source dictionaries with 'name' and 'link' keys
            verified_profile: Optional pre-verified profile data with keys:
                - company: Current company name
                - title: Current job title
                - location: Location
                - education: Education details
        
        Returns:
            Dictionary containing raw_response, sources, query, and research_type
        """
        print("\n" + "="*80)
        print("🔍 STARTING RESEARCH REQUEST")
        print("="*80)
        print(f"📋 Query: {query}")
        print(f"📊 Research Type: {research_type}")
        print(f"📎 Sources Provided: {len(sources) if sources else 0}")
        
        # For individual research, try to get LinkedIn data first
        linkedin_data = None
        if research_type == "individual" and sources:
            for source in sources:
                link = source.get('link', '').lower()
                if 'linkedin.com/in/' in link:
                    print("\n" + "="*80)
                    print("🔗 LINKEDIN URL DETECTED - ATTEMPTING TO FETCH PROFILE DATA")
                    print("="*80)
                    print(f"📎 LinkedIn URL: {source.get('link', '')}")
                    
                    # Try to fetch from Proxycurl
                    linkedin_data = await self.linkedin_service.get_profile(source.get('link', ''))
                    
                    if linkedin_data:
                        print("✅ LinkedIn profile data fetched successfully!")
                        print(f"   👤 Name: {linkedin_data.get('full_name', 'N/A')}")
                        print(f"   🏢 Company: {linkedin_data.get('experiences', [{}])[0].get('company', 'N/A') if linkedin_data.get('experiences') else 'N/A'}")
                        print(f"   💼 Title: {linkedin_data.get('experiences', [{}])[0].get('title', 'N/A') if linkedin_data.get('experiences') else 'N/A'}")
                        print(f"   📍 Location: {linkedin_data.get('city', 'N/A')}, {linkedin_data.get('country', 'N/A')}")
                    else:
                        print("⚠️  Could not fetch LinkedIn data - will use search-based approach")
                        print("💡 TIP: For accurate results, consider:")
                        print("   1. Setting up PROXYCURL_API_KEY in .env")
                        print("   2. OR providing verified profile details manually")
                    
                    print("="*80)
                    break
        
        # Use verified_profile if provided (takes priority)
        if verified_profile:
            print("\n✅ USING USER-PROVIDED VERIFIED PROFILE DATA:")
            print(f"   🏢 Company: {verified_profile.get('company', 'N/A')}")
            print(f"   💼 Title: {verified_profile.get('title', 'N/A')}")
            print(f"   📍 Location: {verified_profile.get('location', 'N/A')}")
        
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
            prompt = self._build_individual_prompt(
                query, 
                sources, 
                linkedin_data=linkedin_data,
                verified_profile=verified_profile
            )
        else:
            print("🔨 Building ORGANIZATION research prompt...")
            prompt = self._build_organization_prompt(query, sources)
        
        print(f"📝 Prompt length: {len(prompt)} characters")
        print("-"*80)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Try different model names - Perplexity model names
            models_to_try = [
                "sonar",
                "sonar-pro",
                "sonar-online",
                "pplx-7b-online",
                "pplx-70b-online",
                "llama-3.1-sonar-large-128k-online",
                "llama-3.1-sonar-huge-128k-online"
            ]
            
            print("\n🤖 ATTEMPTING API CALLS WITH DIFFERENT MODELS:")
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
                            "max_tokens": 4000
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
                        
                        # Extract citations from response
                        citations = result.get("citations", [])
                        if not citations:
                            citation_pattern = r'\[(\d+)\]'
                            citations = list(set(re.findall(citation_pattern, message_content)))
                        
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
                            "sources": citations if isinstance(citations, list) else [],
                            "query": query,
                            "research_type": research_type,
                            "linkedin_data": linkedin_data,  # Include fetched LinkedIn data
                            "verified_profile": verified_profile  # Include verified profile
                        }
                    elif response.status_code == 401:
                        print(f"❌ AUTHENTICATION ERROR (401) with model '{model}'")
                        response_text = response.text
                        if "<html>" in response_text.lower() or "cloudflare" in response_text.lower():
                            print("⚠️  Detected HTML/Cloudflare response")
                            error_msg = "Perplexity API returned HTML (likely Cloudflare protection). "
                            error_msg += "Please verify your API key."
                        else:
                            error_msg = f"Perplexity API authentication failed (401). Response: {response_text[:300]}"
                        print(f"💥 {error_msg}")
                        raise Exception(error_msg)
                    elif response.status_code == 400:
                        last_error = f"Model '{model}' not found (400). Trying alternatives..."
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
            raise Exception(f"All model attempts failed. Last error: {last_error}")
    
    def _get_system_prompt(self, research_type: str) -> str:
        """
        Get the appropriate system prompt based on research type
        """
        if research_type == "individual":
            return """You are a comprehensive research assistant specializing in individual/person research.

CRITICAL INSTRUCTIONS:

1. WHEN VERIFIED PROFILE DATA IS PROVIDED:
   - The user has provided VERIFIED information about the person (company, title, location)
   - This information is CORRECT and AUTHORITATIVE
   - Use this information as the ANCHOR for all searches
   - Do NOT search for or report information about other people with the same name
   - ALL search queries must include the verified company name or job title

2. SEARCH STRATEGY:
   - ALWAYS use: "Person Name" + "Verified Company Name" in ALL searches
   - NEVER search by name alone
   - Cross-verify all found information matches the verified company/role
   - If you find conflicting information, DISCARD it - trust the verified data

3. VERIFICATION:
   - Before including ANY information, verify it matches the verified profile
   - If information doesn't match the verified company/role, DO NOT include it
   - It's better to say "Not found" than include wrong person's data

4. CITATION:
   - Include specific URLs for every piece of information
   - If information is not found, explicitly state "Not found"

Remember: The verified profile data is TRUTH. Only find additional information about THAT specific person."""
        else:
            return """You are a comprehensive research assistant for organization research. Extract exact information from websites and cite all sources."""

    def _build_individual_prompt(
        self, 
        query: str, 
        sources: list = None,
        linkedin_data: Dict[str, Any] = None,
        verified_profile: Dict[str, Any] = None
    ) -> str:
        """
        Build comprehensive prompt for individual research
        
        Now supports:
        1. linkedin_data: Data fetched from Proxycurl/LinkedIn API
        2. verified_profile: User-provided verified profile data
        3. sources: LinkedIn URLs (with warning about limitations)
        """
        individual_name = query.strip()
        
        print(f"\n📝 Building Individual Prompt for: {individual_name}")
        
        # Determine which verified data to use
        verified_company = None
        verified_title = None
        verified_location = None
        verified_education = None
        verified_headline = None
        linkedin_url = None
        
        # Priority 1: User-provided verified profile
        if verified_profile:
            verified_company = verified_profile.get('company')
            verified_title = verified_profile.get('title')
            verified_location = verified_profile.get('location')
            verified_education = verified_profile.get('education')
            print(f"   ✅ Using USER-PROVIDED verified profile data")
        
        # Priority 2: LinkedIn API data (Proxycurl)
        elif linkedin_data:
            if linkedin_data.get('experiences') and len(linkedin_data['experiences']) > 0:
                current_exp = linkedin_data['experiences'][0]
                verified_company = current_exp.get('company')
                verified_title = current_exp.get('title')
            verified_location = f"{linkedin_data.get('city', '')}, {linkedin_data.get('country', '')}".strip(', ')
            verified_headline = linkedin_data.get('headline')
            if linkedin_data.get('education') and len(linkedin_data['education']) > 0:
                verified_education = linkedin_data['education'][0].get('school')
            print(f"   ✅ Using LINKEDIN API data (Proxycurl)")
        
        # Extract LinkedIn URL from sources
        if sources:
            for source in sources:
                link = source.get('link', '').lower()
                if 'linkedin.com/in/' in link:
                    linkedin_url = source.get('link', '')
                    print(f"   🔗 LinkedIn URL: {linkedin_url}")
                    break
        
        # Build the prompt based on available data
        if verified_company and verified_title:
            # WE HAVE VERIFIED DATA - Build a precise search prompt
            prompt = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  INDIVIDUAL RESEARCH REQUEST - VERIFIED PROFILE DATA PROVIDED               ║
╚══════════════════════════════════════════════════════════════════════════════╝

🎯 PERSON TO RESEARCH: {individual_name}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ VERIFIED PROFILE DATA (THIS IS AUTHORITATIVE - DO NOT QUESTION THIS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The following information has been VERIFIED and is CORRECT:

┌─────────────────────────────────────────────────────────────────────────────┐
│ ✅ VERIFIED COMPANY: {verified_company}
│ ✅ VERIFIED JOB TITLE: {verified_title}
│ ✅ VERIFIED LOCATION: {verified_location or 'Not provided'}
│ ✅ VERIFIED EDUCATION: {verified_education or 'Not provided'}
│ ✅ LINKEDIN HEADLINE: {verified_headline or 'Not provided'}
│ ✅ LINKEDIN URL: {linkedin_url or 'Not provided'}
└─────────────────────────────────────────────────────────────────────────────┘

⚠️ CRITICAL INSTRUCTION:
This person is "{individual_name}" who works as "{verified_title}" at "{verified_company}".
There may be MANY people named "{individual_name}" in the world.
You must ONLY find information about the person at "{verified_company}".
Do NOT include information about any other "{individual_name}".

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 SEARCH STRATEGY (USE VERIFIED COMPANY IN ALL SEARCHES)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALL searches must include "{verified_company}" to find the correct person:

A. COMPANY WEBSITE SEARCH:
   - Visit {verified_company} official website
   - Go to /team, /about-us, /leadership, /people pages
   - Search for "{individual_name}" on the company website
   - Find their bio, photo, and role description

B. GOOGLE SEARCHES (ALWAYS include company name):
   - "{individual_name}" "{verified_company}"
   - "{individual_name}" "{verified_title}" "{verified_company}"
   - "{individual_name}" "{verified_company}" news
   - "{individual_name}" "{verified_company}" speaker conference
   - "{individual_name}" "{verified_company}" interview podcast
   - "{individual_name}" "{verified_company}" award

C. SOCIAL MEDIA (with company qualifier):
   - "{individual_name}" "{verified_company}" site:twitter.com
   - "{individual_name}" "{verified_company}" site:github.com
   - "{individual_name}" "{verified_company}" site:medium.com

D. NEWS AND PRESS:
   - "{individual_name}" "{verified_company}" announcement
   - "{individual_name}" "{verified_company}" promotion

⛔ DO NOT SEARCH FOR:
   - "{individual_name}" alone (will find wrong people)
   - "{individual_name}" at other companies
   - Other people named "{individual_name}"

"""
        elif linkedin_url and not verified_company:
            # LinkedIn URL provided but no verified data - WARN about limitations
            prompt = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️ WARNING: LINKEDIN URL PROVIDED BUT CANNOT BE DIRECTLY ACCESSED          ║
╚══════════════════════════════════════════════════════════════════════════════╝

🎯 PERSON TO RESEARCH: {individual_name}
🔗 PROVIDED LINKEDIN URL: {linkedin_url}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ CRITICAL LIMITATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LinkedIn blocks direct profile access. The provided URL ({linkedin_url}) 
CANNOT be scraped directly. Searching for "{individual_name}" may return 
information about DIFFERENT people with the same name.

⚠️ THERE ARE LIKELY MULTIPLE PEOPLE NAMED "{individual_name}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 SEARCH APPROACH - FIND AND LIST ALL MATCHES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Since we cannot verify which "{individual_name}" this is, please:

1. SEARCH for "{individual_name}" across multiple sources
2. LIST ALL distinct people found with this name
3. For each person found, note:
   - Company they work at
   - Job title
   - Location
   - LinkedIn username (if visible)

FORMAT YOUR RESPONSE AS:

┌─────────────────────────────────────────────────────────────────────────────┐
│ ⚠️ MULTIPLE PEOPLE FOUND - VERIFICATION REQUIRED                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Found multiple people named "{individual_name}":                            │
│                                                                             │
│ PERSON 1:                                                                   │
│ - Name: {individual_name}                                                   │
│ - Company: [Company Name]                                                   │
│ - Title: [Job Title]                                                        │
│ - Location: [City, Country]                                                 │
│ - LinkedIn: [URL if found]                                                  │
│                                                                             │
│ PERSON 2:                                                                   │
│ - Name: {individual_name}                                                   │
│ - Company: [Different Company]                                              │
│ - Title: [Different Title]                                                  │
│ - Location: [Different Location]                                            │
│ - LinkedIn: [URL if found]                                                  │
│                                                                             │
│ ... (list all found)                                                        │
│                                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ TO GET ACCURATE RESULTS, please provide:                                    │
│ - The person's current COMPANY NAME, or                                     │
│ - The person's current JOB TITLE, or                                        │
│ - The person's LOCATION                                                     │
│                                                                             │
│ This will help identify the correct person.                                 │
└─────────────────────────────────────────────────────────────────────────────┘

If only ONE person is found, provide full research on that person.
If MULTIPLE people are found, list them and request clarification.
"""
        else:
            # No sources, no verified data - broad search with disambiguation
            prompt = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  INDIVIDUAL RESEARCH REQUEST - NO VERIFIED DATA                             ║
║  ⚠️ DISAMBIGUATION MAY BE REQUIRED                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

🎯 PERSON TO RESEARCH: {individual_name}

⚠️ WARNING: No verified profile data provided.
   "{individual_name}" is a common name - there may be multiple people.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 SEARCH AND IDENTIFY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Search for "{individual_name}" on LinkedIn and Google
2. Identify ALL distinct people with this name
3. If multiple people found, list them with their companies/roles
4. If only one prominent person found, provide full research

FORMAT IF MULTIPLE PEOPLE FOUND:

"Found multiple people named {individual_name}:

1. {individual_name} - [Title] at [Company], [Location]
2. {individual_name} - [Title] at [Company], [Location]
3. {individual_name} - [Title] at [Company], [Location]

Please specify which person by providing their company name or job title."
"""

        # Add common output format section
        prompt += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRED OUTPUT FORMAT (If single person identified)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────────────────┐
│ SECTION 0: PERSON IDENTIFICATION                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ Full Name: [Name]                                                           │
│ Current Company: [Company] [Source URL]                                     │
│ Current Role/Title: [Title] [Source URL]                                    │
│ Location: [City, Country] [Source URL]                                      │
│ LinkedIn URL: [URL]                                                         │
│                                                                             │
│ ✅ IDENTITY CONFIRMATION:                                                   │
│ "[Name] is [Title] at [Company] based in [Location]"                        │
└─────────────────────────────────────────────────────────────────────────────┘

1. **Professional Background**
   - Current position: [Title] [Source URL]
   - Current company: [Company] [Source URL]
   - Previous positions: [List with dates]
   - Years of experience: [Number]
   - Industry expertise: [Areas]
   - LinkedIn profile: [URL]

2. **Education & Certifications**
   - Universities: [Names with URLs]
   - Degrees: [Full degree names]
   - Graduation years: [Years]
   - Certifications: [List]

3. **Current Company Information**
   - Company name: [Full name] [URL]
   - Company size: [Employees]
   - Industry: [Sector]
   - Headquarters: [Location]
   - Person's bio on company site: [If found]

4. **Public Presence & Online Activity**
   - LinkedIn summary: [Key points]
   - Recent posts: [With dates]
   - Articles/publications: [With URLs]
   - Speaking engagements: [List]
   - Social profiles: [Twitter, GitHub, etc.]

5. **Professional Network**
   - Associations/memberships: [List]
   - Board positions: [If any]
   - Advisory roles: [If any]

6. **Recent Activity**
   - Latest activity: [Date and description]
   - Current focus areas: [Topics]
   - Recent career changes: [If any]

7. **Contact Information**
   - LinkedIn: [URL]
   - Company email format: [Pattern]
   - Other profiles: [URLs]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ CRITICAL RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DO:
   - {"Use verified company '" + verified_company + "' in ALL searches" if verified_company else "List all people found if multiple matches"}
   - Include source URLs for every fact
   - Say "Not found" if information unavailable

❌ DO NOT:
   - {"Search for other '" + individual_name + "' at different companies" if verified_company else "Assume which person without verification"}
   - Mix up different people with same name
   - Make up information
"""
        
        return prompt
    
    def _build_organization_prompt(self, query: str, sources: list = None) -> str:
        """
        Build comprehensive prompt for organization research
        """
        # Format standard data sources
        standard_sources = format_sources_for_prompt()
        standard_search_points = format_search_points_for_prompt()
        
        # Extract company name for website search
        company_name = query.strip()
        
        print(f"\n📝 Building Organization Prompt for: {company_name}")
        if sources:
            print(f"   📎 Including {len(sources)} user-provided reference sources")
        else:
            print(f"   ℹ️  No reference sources - will search broadly")
        print(f"   📋 Standard data sources configured: Yes")
        print(f"   🔍 Standard search points configured: Yes")
        
        sources_section = f"""
        
        ⚠️ CRITICAL PRIORITY - VISIT ACTUAL COMPANY WEBSITE FIRST:
        
        1. **FIND AND VISIT THE OFFICIAL COMPANY WEBSITE** for {company_name}
           - Search for: "{company_name}" official website, {company_name}.com, {company_name}.in, {company_name}.co
           - Visit these specific pages on the website:
             * /about or /about-us (company background, history, mission)
             * /team or /leadership or /about-us (leadership team with names, photos, titles)
             * /contact or /contact-us (office locations, contact information)
             * /services or /products (what they offer)
             * /careers or /jobs (company size, culture, job openings)
             * /news or /blog or /press (recent company announcements)
             * /investors or /financials (financial information if available)
        
        2. **EXTRACT REAL, CURRENT INFORMATION FROM WEBSITE**:
           - Exact names of leadership team members (CEO, CTO, CFO, Directors, Board Members)
           - Their specific titles and roles as shown on website
           - Company foundation year, founders' names
           - Exact number of employees if mentioned
           - Real office locations and addresses
           - Actual services/products listed
           - Recent news and announcements from their website
           - Contact information (email, phone)
        
        3. **DO NOT MAKE UP OR GENERALIZE** - Only report what you actually find on their website
           - If website doesn't have certain information, explicitly state "Not found on website"
           - Use exact names and titles as they appear on the website
           - Include the specific URL where you found each piece of information
        """
        
        if sources and len(sources) > 0:
            sources_list = "\n".join([f"           - {source.get('name', 'Unknown')}: {source.get('link', '')}" for source in sources])
            sources_section += f"""
        
        4. **USER-PROVIDED REFERENCE SOURCES** (Optional - Use as starting points/hints):
        {sources_list}
        
        SEARCH STRATEGY: Cast a wide net - search across the internet comprehensively.
        ALWAYS cite the actual source where you found each piece of information.
        """
        
        # Add standard data sources requirement
        data_sources_section = f"""
        
        STANDARD DATA SOURCES (REQUIRED - Search these sources):
        {standard_sources}
        
        CRITICAL SEARCH POINTS (REQUIRED):
        {standard_search_points}
        
        DATA QUALITY REQUIREMENTS:
        - PARAPHRASE all information for clarity
        - NO REPETITION
        - CITE SOURCE in brackets after each fact
        - Present in CLEAR, CONCISE language
        - Maintain BALANCED view
        """
        
        return f"""
        Conduct comprehensive research on the following organization: {query}
        {sources_section}
        {data_sources_section}
        
        Please provide detailed information organized in these sections:
        
        1. **Company Background** - Name, industry, headquarters, founded, employees, mission, products/services
        2. **Leadership Intelligence** - Real names and titles from company website, executive communications
        3. **Financial Information** - Revenue, funding, financial health
        4. **News Intelligence** - Positive, negative, and neutral news (last 7-10 years)
        5. **Challenges & Risks** - External, internal, controversies
        6. **Strategic Priorities** - Current initiatives, digital transformation, growth plans
        7. **Recent Activity** - Latest news, partnerships, product updates
        
        CITE ALL SOURCES with URLs.
        """