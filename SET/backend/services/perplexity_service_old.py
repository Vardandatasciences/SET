import httpx
import json
import re
from typing import Dict, Any, Literal
import os
from .data_sources import (
    EXECUTIVE_ROLES,
    STANDARD_DATA_SOURCES,
    ORGANIZATION_SEARCH_POINTS,
    DATA_QUALITY_REQUIREMENTS,
    format_sources_for_prompt,
    format_search_points_for_prompt
)


class PerplexityService:
    def __init__(self, api_key: str):
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
    
    async def fetch_research_data(
        self, 
        query: str, 
        research_type: Literal["individual", "organization"],
        sources: list = None
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive research data from Perplexity API
        
        Args:
            query: The search query (individual name or organization name)
            research_type: Type of research ("individual" or "organization")
            sources: List of source dictionaries with 'name' and 'link' keys
                    Example: [{"name": "LinkedIn", "link": "https://linkedin.com/in/..."}, ...]
        
        Returns:
            Dictionary containing raw_response, sources, query, and research_type
        """
        print("\n" + "="*80)
        print("🔍 STARTING RESEARCH REQUEST")
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
            prompt = self._build_individual_prompt(query, sources)
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
                "llama-3.1-sonar-large-128k-online",  # Keep as fallback
                "llama-3.1-sonar-huge-128k-online"   # Keep as fallback
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
                                    "content": "You are a comprehensive research assistant. When a user provides a specific LinkedIn URL or other source link, you MUST visit that EXACT URL first and extract information from that specific source. Do NOT search for other profiles or sources with similar names - use ONLY the provided URL. If multiple people share the same name, extract information ONLY from the profile/source at the provided URL. Always extract exact information as it appears on the source. Verify the information matches the provided URL. Do not generalize or make assumptions. Cite the actual source URL where you found each piece of information. Provide detailed, accurate information from the specified source with proper citations."
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
                        # Success!
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
                            for idx, citation in enumerate(citations[:10], 1):  # Show first 10
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
                            "research_type": research_type
                        }
                    elif response.status_code == 401:
                        print(f"❌ AUTHENTICATION ERROR (401) with model '{model}'")
                        # Check if it's an HTML response (Cloudflare protection)
                        response_text = response.text
                        if "<html>" in response_text.lower() or "cloudflare" in response_text.lower():
                            print("⚠️  Detected HTML/Cloudflare response")
                            error_msg = "Perplexity API returned HTML (likely Cloudflare protection). "
                            error_msg += "This usually means:\n"
                            error_msg += "1. The API endpoint might be incorrect\n"
                            error_msg += "2. Your API key format is wrong\n"
                            error_msg += "3. The API key is invalid or expired\n"
                            error_msg += "\nPlease verify:\n"
                            error_msg += "- Your API key starts with 'pplx-'\n"
                            error_msg += "- The key is active in your Perplexity dashboard\n"
                            error_msg += "- Your account has credits/balance\n"
                            error_msg += f"\nAPI Key format check: {self.api_key[:15]}... (should start with 'pplx-')"
                        else:
                            error_msg = "Perplexity API authentication failed (401). "
                            error_msg += "Please check:\n"
                            error_msg += "1. Your API key is correct in the .env file\n"
                            error_msg += "2. Your API key hasn't expired\n"
                            error_msg += "3. Your account has sufficient credits\n"
                            error_msg += "4. Your IP address is not restricted\n"
                            error_msg += f"\nAPI Response: {response_text[:300]}"
                        print(f"💥 {error_msg}")
                        raise Exception(error_msg)
                    elif response.status_code == 400:
                        # Model name might be wrong, try next one
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
                        raise  # Re-raise 401 errors immediately
                    last_error = str(e)
                    print(f"⚠️  Exception with model '{model}': {last_error}")
                    continue
            
            # If we get here, all models failed
            print("\n" + "="*80)
            print("❌ ALL MODEL ATTEMPTS FAILED")
            print("="*80)
            print(f"💥 Last error: {last_error}")
            print("="*80 + "\n")
            raise Exception(f"All model attempts failed. Last error: {last_error}")
            
            result = response.json()
            message_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Extract citations from response (Perplexity may include them in citations field or in content)
            citations = result.get("citations", [])
            if not citations:
                # Try to extract from message content if citations are embedded
                citation_pattern = r'\[(\d+)\]'
                citations = list(set(re.findall(citation_pattern, message_content)))
            
            return {
                "raw_response": message_content,
                "sources": citations if isinstance(citations, list) else [],
                "query": query,
                "research_type": research_type
            }
    
    def _build_individual_prompt(self, query: str, sources: list = None) -> str:
        """
        Build comprehensive prompt for individual research
        """
        individual_name = query.strip()
        
        print(f"\n📝 Building Individual Prompt for: {individual_name}")
        if sources:
            print(f"   📎 Including {len(sources)} user-provided reference sources")
        else:
            print(f"   ℹ️  No reference sources - will search broadly")
        
        sources_section = f"""
        
        ⚠️ CRITICAL PRIORITY - FIND REAL INFORMATION ABOUT THIS PERSON:
        
        1. **AGGRESSIVE LINKEDIN SEARCH** for {individual_name}:
           - Search LinkedIn using: "{individual_name}" site:linkedin.com/in/
           - Try variations: "{individual_name}" + location, "{individual_name}" + company
           - Search Google: "{individual_name}" LinkedIn profile
           - Search Google: "{individual_name}" site:linkedin.com
           - If exact name not found, try name variations (first name + last name combinations)
           - Extract exact current job title and company name if profile found
           - Get their complete work history with dates
           - Note education details (universities, degrees, years)
           - Look for recent posts and activity
           - Include the LinkedIn profile URL if found
        
        2. **COMPREHENSIVE GOOGLE SEARCH**:
           - Search: "{individual_name}" professional profile
           - Search: "{individual_name}" biography
           - Search: "{individual_name}" about
           - Search: "{individual_name}" + current company
           - Search: "{individual_name}" + job title
           - Check Google People Cards if available
           - Look for any professional directories or databases
        
        3. **VISIT THEIR CURRENT COMPANY'S WEBSITE** (if company is known):
           - If they work at a company, visit that company's website
           - Look for /team, /leadership, /about-us, /people pages
           - Check if they are listed on the company website
           - Extract any bio or description from the website
           - Get the exact title as shown on company website
        
        4. **SEARCH FOR PROFESSIONAL PRESENCE**:
           - Personal website or blog: search "{individual_name}" personal website
           - GitHub profile: search "{individual_name}" site:github.com
           - Twitter/X profile: search "{individual_name}" site:twitter.com OR site:x.com
           - Medium articles: search "{individual_name}" site:medium.com
           - Conference speaking engagements: search "{individual_name}" speaker OR conference
           - Published papers or articles: search "{individual_name}" published OR research
           - Patents or innovations: search "{individual_name}" patent
           - News articles: search "{individual_name}" news
        
        5. **ALTERNATIVE SEARCH STRATEGIES**:
           - If no results with exact name, try searching by:
             * Known company + "{individual_name}"
             * Known location + "{individual_name}"
             * Known profession/role + "{individual_name}"
           - Check professional databases (ZoomInfo, RocketReach, etc.) if accessible
           - Look for email addresses or contact information
        
        6. **DO NOT GIVE UP TOO EASILY**:
           - Try multiple search strategies before reporting "Not found"
           - Search with and without middle names/initials
           - Try different name spellings or variations
           - Check if person uses a different name professionally
           - Only report "Not found" after exhaustive search attempts
           - If information is not available, state "Not found after comprehensive search"
           - Use exact job titles and company names as they appear
           - Include specific URLs for all information found
        """
        
        if sources and len(sources) > 0:
            # Check if LinkedIn is among the sources
            linkedin_source = None
            other_sources = []
            for source in sources:
                if 'linkedin' in source.get('link', '').lower() or 'linkedin' in source.get('name', '').lower():
                    linkedin_source = source
                    print(f"\n🔗 LINKEDIN URL DETECTED: {source.get('link', '')}")
                    print(f"   ⚠️  This URL will be used as PRIMARY source - extracting ONLY from this profile")
                else:
                    other_sources.append(source)
            
            if linkedin_source:
                linkedin_url = linkedin_source.get('link', '')
                sources_section += f"""
        
        5. **⚠️ CRITICAL - USER-PROVIDED LINKEDIN PROFILE (MANDATORY)**:
           LinkedIn URL: {linkedin_url}
        
           ⚠️ ABSOLUTE REQUIREMENT - YOU MUST:
           - VISIT THIS EXACT LINKEDIN URL: {linkedin_url}
           - Extract information ONLY from this specific LinkedIn profile
           - DO NOT search for other profiles with the same name
           - DO NOT use information from different people with similar names
           - Verify the profile matches the name "{individual_name}"
           - Extract the EXACT job title, company, location, and all details from THIS profile
           - If this profile shows different information than other sources, USE THIS PROFILE'S INFORMATION
           - This is the PRIMARY and AUTHORITATIVE source for this person
           - All professional background, education, and current role information MUST come from this profile
        
           After extracting from this LinkedIn profile, you may supplement with:
           - Company website information (for the company shown on THIS LinkedIn profile)
           - News articles about this person (matching the company/role from THIS profile)
           - Other professional sources that match THIS profile's information
        """
            
            if other_sources:
                other_sources_list = "\n".join([f"           - {source.get('name', 'Unknown')}: {source.get('link', '')}" for source in other_sources])
                sources_section += f"""
        
        6. **OTHER USER-PROVIDED SOURCES** (Use as additional references):
        {other_sources_list}
        """
            else:
                sources_section += """
        
        6. **ADDITIONAL SOURCES TO SEARCH** (After extracting from the provided LinkedIn profile):
        """
            
            sources_section += """
        - Company website (for the company shown on the LinkedIn profile)
        - News articles and press releases (about this specific person)
        - Professional publications and industry reports
        - Education institution websites (matching the education on LinkedIn)
        - Conference and speaking engagement records
        - Social media profiles (Twitter/X, GitHub, Medium, etc.)
        - Industry directories and databases
        
        ⚠️ CRITICAL: All information must match and be consistent with the LinkedIn profile provided.
        If you find conflicting information, prioritize the LinkedIn profile information.
        """
        else:
            sources_section += """
        
        5. **ADDITIONAL SOURCES TO SEARCH**:
        - Company websites and official communications
        - News articles and press releases
        - Professional publications and industry reports
        - Social media profiles (Twitter, GitHub, etc.)
        - Public databases and registries
        - Education institution websites
        - Conference and speaking engagement records
        """
        
        return f"""
        Conduct comprehensive research on the following individual: {individual_name}
        {sources_section}
        
        Please provide detailed, REAL information about this person:
        
        1. **Professional Background** (Extract from LinkedIn and company website):
           - Current position (exact title): [From LinkedIn/company website with URL]
           - Current company (full name): [From LinkedIn/company website with URL]
           - Previous positions and companies: [List chronologically with dates from LinkedIn with URL]
           - Total years of experience: [Calculate from LinkedIn history]
           - Industry expertise and specializations: [From LinkedIn profile/posts with URL]
           - LinkedIn profile link: [Include actual URL]
        
        2. **Education** (Extract from LinkedIn or education institution websites):
           - Universities/colleges attended: [Exact names from LinkedIn with URL]
           - Degrees obtained: [e.g., "Bachelor of Technology in Computer Science"] [From LinkedIn with URL]
           - Years of graduation: [From LinkedIn with URL]
           - Notable achievements or honors: [From LinkedIn/university websites with URL]
           - Certifications: [From LinkedIn with URL]
        
        3. **Current Company Information** (Visit their company's website):
           - Current company full name: [From company website with URL]
           - Company size (employees, revenue if available): [From company website/LinkedIn with URL]
           - Industry and sector: [From company website with URL]
           - Company headquarters location: [From company website with URL]
           - Person's role in the company (from company website): [From /team or /about page with URL]
           - Company's recent news and developments: [From company website/news with URL]
        
        4. **Public Presence & Online Activity**:
           - LinkedIn profile summary: [Exact summary text from LinkedIn with URL]
           - Recent LinkedIn posts (last 3-6 months): [List with dates and URLs]
           - Articles, publications, or thought leadership: [List with URLs]
           - Speaking engagements: [List with dates and event URLs]
           - Awards or recognitions: [List with sources and URLs]
           - Blog posts or content published: [List with URLs]
           - Twitter/X profile: [Include URL if found]
           - GitHub profile: [Include URL if found]
           - Personal website: [Include URL if found]
        
        5. **Professional Network & Industry Involvement**:
           - Key connections or associations: [From LinkedIn with context]
           - Industry involvement: [Memberships, committees, boards]
           - Professional memberships: [List with sources]
           - Open source contributions: [From GitHub if applicable]
        
        6. **Recent Activity & Current Focus**:
           - Most recent LinkedIn post/update: [With exact date and content summary with URL]
           - Current projects or initiatives mentioned: [From LinkedIn/company website with URL]
           - Public statements or interviews: [With dates and URLs]
           - Recent career moves or changes: [With dates from LinkedIn]
           - Active topics they discuss: [From recent posts/articles]
        
        ⚠️ CRITICAL REQUIREMENTS:
        - Extract EXACT information as it appears on LinkedIn and websites
        - Include SPECIFIC URLs for every piece of information
        - Include DATES for all time-based information
        - If information is NOT found, explicitly state "Not found" or "Not available online"
        - DO NOT generalize or make assumptions
        - Cite the source URL in brackets after each piece of information
        
        Format the response in a structured, organized manner with clear sections and proper citations.
        """
    
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
        
        ⚠️ IMPORTANT SEARCH APPROACH:
        - The above sources are PROVIDED AS REFERENCES ONLY - not mandatory restrictions
        - USE them as helpful starting points or hints about where to look for information
        - You can TRY to visit these links if available and helpful
        - BUT you are NOT limited to only these sources
        - SEARCH BROADLY across the entire internet for comprehensive information about {company_name}
        - Use the heading/topic from these sources as guidance for what type of information to find
        - Search multiple platforms, databases, and websites to get complete information
        - Cite whatever source you actually find the information from (even if different from provided sources)
        
        Reference guide for source types (if you find similar sources):
        - ZoomInfo/similar: Revenue, employee count, financial data, key contacts
        - PitchBook/similar: Funding data, investors, valuation, financial metrics
        - Tracxn/similar: Company insights, funding rounds, competitors, market position
        - Tofler/MCA/similar: Registration details, directors, financial statements, compliance data
        - Zauba Corp/similar: Corporate data, registration info, directors, shareholding
        - LinkedIn/similar: Company page info, posts, employee insights, company updates
        
        SEARCH STRATEGY: Cast a wide net - search across the internet comprehensively.
        The user-provided sources are helpful hints, not restrictions.
        ALWAYS cite the actual source where you found each piece of information.
        Example citations: [Bloomberg], [Company Website], [SEC Filing], [News Article], [LinkedIn]
        """
        
        # Add standard data sources requirement
        data_sources_section = f"""
        
        STANDARD DATA SOURCES (REQUIRED - Search these sources):
        {standard_sources}
        
        CRITICAL SEARCH POINTS (REQUIRED):
        {standard_search_points}
        
        EXECUTIVE COMMUNICATIONS (HIGH PRIORITY):
        Search specifically for messages and communications from:
        - CEO message (shareholder letters, annual report messages, public statements)
        - CFO message (financial outlook, earnings commentary, investor communications)
        - CTO message (technology vision, innovation roadmap, technical strategy)
        - CIO message (digital transformation initiatives, IT strategy, technology adoption)
        - Audit Committee reports and findings (governance, risk management, compliance)
        - Advisory Board messages and recommendations (strategic guidance, industry insights)
        
        For each executive communication found, extract:
        - The specific message or key points
        - Date of communication
        - Context and purpose
        - Strategic implications
        - Source citation in brackets
        
        DATA QUALITY REQUIREMENTS:
        - PARAPHRASE all information for clarity and easy understanding
        - NO REPETITION or overemphasis on the same topics
        - CITE SOURCE in brackets after each piece of information (e.g., [SEC 10-K Filing 2023])
        - Present in CLEAR, CONCISE language suitable for sales professionals
        - Maintain BALANCED view with both positive and negative aspects
        
        Additional search areas:
        - Company website and official communications
        - News articles and press releases (last 7-10 years)
        - Financial filings (SEC, SEBI, annual reports, regulatory filings)
        - Industry reports and analysis
        - Public databases and registries
        - Social media and LinkedIn company page
        - Industry publications and trade journals
        - Government databases and regulatory filings
        - Market research reports
        - Wikipedia for company background and history
        - Investopedia for industry context and definitions
        
        Combine all information from user-provided sources, standard data sources, and additional internet resources.
        """
        
        return f"""
        Conduct comprehensive research on the following organization: {query}
        {sources_section}
        {data_sources_section}
        
        Please provide detailed information organized in the following sections:
        
        1. **Company Background**
           
           ⚠️ EXTRACT FROM COMPANY WEBSITE FIRST (visit /about or /about-us page):
           - Company full legal name [Exact name from website with URL]
           - Industry/sector they operate in [From website with URL]
           - Headquarters location and other offices [Exact addresses from website with URL]
           - Founded year and founders' names [From website with URL]
           - Company size: number of employees if stated [From website with URL]
           - Mission statement or company vision [Exact text from website with URL]
           - Core products/services [List exactly as shown on website with URL]
           - Key clients or customers if mentioned [From website with URL]
           
           Additional information from other sources:
           - Revenue data [Source with URL]
           - Business model details [Source with URL]
           - Market position and competitors [Source with URL]
           - Registration details (from regulatory sources like Tofler, Zauba Corp, MCA) [Source with URL]
           - Company registration number, CIN, or incorporation details [Source with URL]
           
           IMPORTANT: Report exact information as found on website. If not available, state "Not found on website". Always cite specific URLs.
        
        2. **Leadership Intelligence & Executive Communications**
           
           ⚠️ PRIORITY: Extract REAL leadership information from company website first:
           - Visit the company's /about, /team, /leadership, or /about-us page
           - Extract EXACT names and titles as shown on the website
           - Example: "John Smith - Chief Executive Officer" not "CEO position exists"
           - Include all leadership team members visible on the website with their exact titles
           - Note any photos, bios, or descriptions provided for each leader
           - Cite the specific website URL where this information was found
           
           Key executives with real names and titles from website:
           - CEO/Chief Executive Officer: [Exact name from website] [Website URL]
           - CTO/Chief Technology Officer: [Exact name from website] [Website URL]
           - CFO/Chief Financial Officer: [Exact name from website] [Website URL]
           - CIO/Chief Information Officer: [Exact name from website] [Website URL]
           - COO/Chief Operating Officer: [Exact name from website] [Website URL]
           - Board of Directors: [List all names if available on website] [Website URL]
           - Other key executives: [List all with exact titles] [Website URL]
           
           LinkedIn profiles (search after getting names from website):
           - Search LinkedIn for each executive name found on website
           - Include LinkedIn profile URLs if found
           
           Leadership backgrounds and experience from website/LinkedIn:
           - Education details [Source]
           - Previous experience [Source]
           - Years in current role [Source]
           - Recent leadership changes [Source]
           
           EXECUTIVE MESSAGES (CRITICAL):
           - CEO Message: Extract CEO's message from annual reports, website, shareholder letters, or public statements [Source with URL]
           - CFO Message: Extract CFO's financial outlook and commentary [Source with URL]
           - CTO Message: Extract CTO's technology vision and innovation roadmap [Source with URL]
           - CIO Message: Extract CIO's digital transformation initiatives [Source with URL]
           - Audit Committee Message: Extract audit committee findings and governance reports [Source with URL]
           - Advisory Board Guidance: Extract advisory board recommendations [Source with URL]
           
           LEADERSHIP TARGETS & FOCUS POINTS:
           - Specific targets set by leadership team [Source with URL]
           - Strategic focus areas announced by executives [Source with URL]
           - Priority initiatives communicated by leadership [Source with URL]
           
           - Public-facing challenges or controversies [Source with URL]
           - Leadership turnover patterns [Source with URL]
           - Recent posts or activity from leadership [Source with URL]
        
        3. **Financial Information (Last 7-10 years)**
           Search SEC filings, SEBI reports, Yahoo Finance, Bloomberg for:
           - Revenue trends (with year-over-year comparisons) [Source]
           - Funding rounds and investment history (if applicable) [Source]
           - Financial stress events and warnings [Source]
           - Funding failures or declined investments [Source]
           - Declining revenue patterns [Source]
           - Auditor warnings and concerns [Source]
           - Risk factors from SEC/SEBI filings [Source]
           - Most recent financial data from all sources [Source]
           
           IMPORTANT: Paraphrase financial data for clarity. Always cite source in brackets.
        
        4. **News Intelligence (Last 7-10 years)**
           Search Bloomberg, Yahoo Finance, NDTV, Wikipedia, general news sources for:
           
           Positive news:
           - Expansions and growth initiatives [Source with date]
           - Partnerships and strategic alliances [Source with date]
           - Product launches and innovations [Source with date]
           - Awards and recognitions [Source with date]
           
           Negative news:
           - Fines and penalties [Source with date]
           - Lawsuits and legal proceedings (check FBI, CBI databases) [Source with date]
           - Regulatory warnings and actions (SEC, SEBI) [Source with date]
           - Data breaches and security incidents [Source with date]
           - PR crises and reputation damage [Source with date]
           - Failed product launches [Source with date]
           - Major financial losses [Source with date]
           - Leadership misconduct [Source with date]
           
           Neutral industry context:
           - Market trends affecting the company [Source]
           - Industry developments and changes [Source]
           
           For each news item: Paraphrase clearly, include date, cite source in brackets, avoid repetition
        
        5. **Challenges & Risks**
           External challenges:
           - Market competition and competitive pressures [Source]
           - Regulatory pressure and compliance requirements (check CPCB for environmental) [Source]
           - Economic headwinds and market conditions [Source]
           - Geopolitical factors [Source]
           - Technology disruptions [Source]
           
           Internal challenges:
           - Leadership instability and turnover [Source]
           - Declining sales or market share [Source]
           - Operational inefficiencies [Source]
           - Culture issues or employee concerns [Source]
           - Failed initiatives or strategy misses [Source]
           
           Public controversies:
           - Lawsuits and legal battles [Source]
           - Scandals and misconduct allegations [Source]
           - Customer backlash and complaints [Source]
           - Negative PR cycles [Source]
           
           Impact assessment:
           - Severity and magnitude [Source]
           - Short-term vs long-term implications [Source]
           
           IMPORTANT: Present challenges clearly without overemphasis. Cite all sources.
        
        6. **Strategic Priorities & Leadership Vision**
           - Current strategic initiatives announced by leadership [Source]
           - Digital transformation efforts and technology roadmap [Source]
           - Market expansion plans and growth strategies [Source]
           - Cost reduction and efficiency measures [Source]
           - Compliance and regulatory focus (GRC-related content) [Source]
           - Environmental and sustainability initiatives (check CPCB standards) [Source]
           - Priorities triggered by recent challenges [Source]
           - Leadership's stated targets and focus points [Source]
           
           IMPORTANT: Paraphrase leadership communications clearly. Always cite source.
        
        7. **Recent Activity & Company News**
           - Latest news and press releases [Source with date]
           - Recent LinkedIn company posts [Source with date]
           - Social media activity and announcements [Source with date]
           - Recent partnerships or deals [Source with date]
           - Product updates and launches [Source with date]
           - Recent regulatory filings or updates [Source with date]
           - Last activity in relevant domain [Source with date]
           
           IMPORTANT: Paraphrase all news items. Include dates. Cite sources in brackets.
        
        8. **Additional Sources Information**
           - Summary of key information found in each standard source (SEC, SEBI, Bloomberg, etc.)
           - Summary of information from user-provided sources (ZoomInfo, PitchBook, Tracxn, Tofler, Zauba Corp, LinkedIn, etc.)
           - Important data points with clear source attribution
           - Links to original sources for reference
        
        CRITICAL FORMATTING REQUIREMENTS:
        - PARAPHRASE all extracted information for clarity and easy understanding
        - NO REPETITION or overemphasis on topics - present each point once clearly
        - CITE SOURCE in brackets after EVERY piece of information (e.g., [SEC 10-K 2023], [Bloomberg Jan 2024], [SEBI Filing 2023])
        - Use CLEAR, CONCISE language suitable for sales professionals
        - Provide BALANCED view with both positive and negative aspects
        - Format response in structured, organized manner with clear sections
        - Include specific URLs and links when referencing information
        """

