import httpx
import json
import re
from typing import Dict, Any, Literal, Optional
import os
import asyncio

# Handle imports for both module and direct execution
try:
    from .data_sources import (
        format_sources_for_prompt,
        format_search_points_for_prompt
    )
except ImportError:
    def format_sources_for_prompt():
        return "Company website, LinkedIn, News sources, SEC/SEBI filings, Crunchbase"
    
    def format_search_points_for_prompt():
        return "Company background, Leadership, Financials, News, Products"


class PerplexityService:
    """
    Perplexity Research Service - REQUIRES COMPANY NAME for Individual Research
    
    WHY: Perplexity cannot access LinkedIn profiles directly. Searching by name
    returns random/famous people with similar names. The ONLY way to ensure
    accurate results is to require the user to provide the company name.
    
    USAGE:
        service = PerplexityService(api_key)
        result = await service.fetch_research_data(
            query="Sanjay Jindal",
            research_type="individual",
            sources=[...],
            company_name="Bunge"  # REQUIRED for accuracy!
        )
    """
    
    def __init__(self, api_key: str = None):
        if not api_key:
            api_key = os.getenv("PERPLEXITY_API_KEY")
        
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY is required.")
        
        self.api_key = api_key.strip().strip('"').strip("'")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        print(f"✅ PerplexityService initialized")
    
    async def fetch_research_data(
        self, 
        query: str, 
        research_type: Literal["individual", "organization"],
        sources: list = None,
        # REQUIRED FIELDS FOR INDIVIDUAL RESEARCH
        company_name: str = None,    # REQUIRED - Person's current company
        job_title: str = None,       # OPTIONAL - Person's job title
        location: str = None         # OPTIONAL - Person's location
    ) -> Dict[str, Any]:
        """
        Fetch research data from Perplexity API
        
        For INDIVIDUAL research, company_name is REQUIRED for accurate results.
        Without it, Perplexity may return information about the wrong person.
        
        Args:
            query: Person's name or organization name
            research_type: "individual" or "organization"
            sources: List of source URLs (LinkedIn, etc.)
            company_name: REQUIRED for individual - Person's current company
            job_title: Optional - Person's current job title  
            location: Optional - Person's location
        """
        print("\n" + "="*80)
        print("🔍 STARTING RESEARCH REQUEST")
        print("="*80)
        print(f"📋 Query: {query}")
        print(f"📊 Type: {research_type}")
        
        if research_type == "individual":
            # Check if company_name is provided
            if not company_name:
                print("\n" + "⚠️"*30)
                print("⚠️  WARNING: NO COMPANY NAME PROVIDED!")
                print("⚠️  LinkedIn profiles CANNOT be accessed directly.")
                print("⚠️  Results may be about the WRONG person.")
                print("⚠️  Please provide company_name for accurate results.")
                print("⚠️"*30)
                
                # Return disambiguation request
                return await self._request_disambiguation(query, sources)
            else:
                print(f"\n✅ VERIFIED COMPANY: {company_name}")
                if job_title:
                    print(f"✅ JOB TITLE: {job_title}")
                if location:
                    print(f"✅ LOCATION: {location}")
                
                return await self._research_individual_verified(
                    name=query,
                    company=company_name,
                    title=job_title,
                    location=location,
                    sources=sources
                )
        else:
            return await self._research_organization(query, sources)
    
    async def _request_disambiguation(self, name: str, sources: list = None) -> Dict[str, Any]:
        """
        When no company is provided, search and return multiple matches
        asking user to specify which person they want.
        """
        print("\n📌 SEARCHING FOR ALL PEOPLE NAMED: " + name)
        
        # Extract LinkedIn URL if provided
        linkedin_url = None
        if sources:
            for source in sources:
                if isinstance(source, dict) and 'linkedin' in source.get('link', '').lower():
                    linkedin_url = source.get('link', '')
                    break
        
        prompt = f"""Search for people named "{name}" and list ALL distinct people found.

{f"LinkedIn URL provided (but cannot be accessed directly): {linkedin_url}" if linkedin_url else ""}

For each person found, provide:
- Full Name
- Current Company
- Job Title
- Location

Format as:

## ⚠️ MULTIPLE PEOPLE FOUND - PLEASE SPECIFY

Found several people named "{name}":

### Person 1
- **Name:** {name}
- **Company:** [Company A]
- **Title:** [Job Title]
- **Location:** [City, Country]

### Person 2
- **Name:** {name}
- **Company:** [Company B]  
- **Title:** [Job Title]
- **Location:** [City, Country]

### Person 3
- **Name:** {name}
- **Company:** [Company C]
- **Title:** [Job Title]
- **Location:** [City, Country]

---

**⚠️ To get accurate results, please provide the person's COMPANY NAME.**

Without the company name, we cannot identify which "{name}" you are researching.
"""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json={
                        "model": "sonar-pro",
                        "messages": [
                            {"role": "system", "content": "List all people found with this name."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.2,
                        "max_tokens": 2000
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    return {
                        "raw_response": content,
                        "sources": [],
                        "query": name,
                        "research_type": "individual",
                        "status": "DISAMBIGUATION_REQUIRED",
                        "message": "Please provide company name for accurate results"
                    }
                else:
                    raise Exception(f"API error: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            raise

    async def _research_individual_verified(
        self,
        name: str,
        company: str,
        title: str = None,
        location: str = None,
        sources: list = None
    ) -> Dict[str, Any]:
        """
        Research individual with VERIFIED company name.
        All searches will include the company name to ensure accuracy.
        """
        print(f"\n🎯 Researching: \"{name}\" at \"{company}\"")
        
        # Extract LinkedIn URL if provided
        linkedin_url = None
        if sources:
            for source in sources:
                if isinstance(source, dict) and 'linkedin' in source.get('link', '').lower():
                    linkedin_url = source.get('link', '')
        
        # Build the prompt with verified company
        prompt = f"""
Research "{name}" who works at "{company}".

✅ VERIFIED INFORMATION:
- Name: {name}
- Company: {company}
- Title: {title or "[Find from search]"}
- Location: {location or "[Find from search]"}
- LinkedIn: {linkedin_url or "[Find from search]"}

⚠️ CRITICAL: Only include information about "{name}" who works at "{company}".
There are multiple people named "{name}" - do NOT include information about others.

🔍 SEARCH STRATEGY (ALWAYS include "{company}"):

1. COMPANY WEBSITE:
   - Visit {company} official website
   - Check /about, /team, /leadership, /our-people pages
   - Find {name}'s bio, photo, and role description
   - URL pattern: {company.lower().replace(' ', '')}.com

2. GOOGLE SEARCHES (include company in every search):
   - "{name}" "{company}"
   - "{name}" "{company}" LinkedIn
   - "{name}" "{company}" biography profile
   - "{name}" "{company}" news announcement
   - "{name}" "{company}" interview podcast
   - "{name}" "{company}" conference speaker
   - "{name}" "{company}" award recognition

3. LINKEDIN SEARCH:
   - "{name}" "{company}" site:linkedin.com
   - Find their LinkedIn profile URL

4. SOCIAL MEDIA:
   - "{name}" "{company}" site:twitter.com
   - "{name}" "{company}" site:medium.com

5. NEWS:
   - "{name}" "{company}" latest news
   - "{name}" appointed {company}
   - "{name}" joins {company}

⛔ DO NOT:
- Search for "{name}" without "{company}"
- Include information about other people named "{name}"
- Make assumptions - only report verified information

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## PERSON IDENTIFICATION
- **Full Name:** {name}
- **Company:** {company}
- **Title:** [From {company} website or LinkedIn] [Source URL]
- **Location:** [City, Country] [Source URL]
- **LinkedIn:** [Profile URL if found]

✅ **CONFIRMED:** "{name} is [Title] at {company}"

## 1. Professional Background
- **Current Role:** [Title] at {company} [Source URL]
- **Responsibilities:** [Key responsibilities from bio] [Source URL]
- **Duration at {company}:** [Time period if available] [Source URL]
- **Previous Positions:**
  - [Previous Title] at [Previous Company] ([Years]) [Source URL]
  - [Previous Title] at [Previous Company] ([Years]) [Source URL]
- **Total Experience:** [X years]
- **Key Expertise:** [Areas of expertise] [Source URL]

## 2. Education
- **University:** [Name] [Source URL]
- **Degree:** [Full degree name] [Source URL]
- **Graduation Year:** [Year] [Source URL]
- **Certifications:** [List] [Source URL]

## 3. Current Company Information ({company})
- **Company Name:** {company}
- **Website:** [URL]
- **Industry:** [Sector]
- **Size:** [Employees/Revenue if available]
- **Headquarters:** [Location]
- **{name}'s Bio on Website:** [Quote or summary if found] [Source URL]

## 4. Public Presence & Activity
- **LinkedIn Profile:** [URL]
- **LinkedIn Headline:** [Exact headline text]
- **LinkedIn Summary:** [Key points from About section]
- **Recent Posts/Articles:** [List with dates and topics]
- **Speaking Engagements:** [Events, conferences]
- **Publications:** [Articles, papers]
- **Twitter/X:** [Handle if found]
- **Other Profiles:** [Medium, GitHub, etc.]

## 5. Recent Activity & News
- **Recent News:** [News mentioning {name} at {company}]
- **Career Updates:** [Recent changes, promotions]
- **Current Focus:** [Topics they discuss/work on]

## 6. Contact Information
- **LinkedIn:** [URL]
- **Email Pattern:** [firstname.lastname@{company.lower().replace(' ', '')}.com]
- **Company Contact:** [Company contact page URL]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Include [Source URL] after EVERY piece of information.
If information is not found, write "Not found in search results."
"""

        system_prompt = f"""You are a professional research assistant.

CRITICAL INSTRUCTION: You are researching "{name}" who works at "{company}".

1. ALL searches must include "{company}"
2. ONLY include information about the person at "{company}"
3. There are MULTIPLE people named "{name}" - do NOT mix them up
4. If you find information about a different "{name}" (at a different company), IGNORE it
5. Cite sources for every fact

The person you are researching is: {name} at {company}"""

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json={
                        "model": "sonar-pro",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.2,
                        "max_tokens": 4000
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    citations = result.get("citations", [])
                    
                    print(f"\n✅ Research completed - {len(content)} chars")
                    
                    return {
                        "raw_response": content,
                        "sources": citations,
                        "query": name,
                        "research_type": "individual",
                        "verified_company": company,
                        "verified_title": title,
                        "verified_location": location,
                        "linkedin_url": linkedin_url,
                        "status": "SUCCESS"
                    }
                else:
                    raise Exception(f"API error: {response.status_code} - {response.text[:200]}")
                    
        except Exception as e:
            print(f"❌ Research error: {e}")
            raise

    async def _research_organization(self, query: str, sources: list = None) -> Dict[str, Any]:
        """Research organization/company"""
        
        company_name = query.strip()
        print(f"\n🏢 Researching Organization: {company_name}")
        
        sources_text = ""
        if sources:
            sources_text = "\n".join([f"- {s.get('name', 'Source')}: {s.get('link', '')}" 
                                      for s in sources if isinstance(s, dict)])
        
        prompt = f"""Research organization: {company_name}

1. Visit {company_name} official website
   - /about, /team, /leadership, /contact pages
   - Extract: Company info, leadership names and titles

2. Search additional sources:
   - LinkedIn company page
   - News articles
   - Crunchbase, PitchBook
   - SEC/SEBI filings
{f"3. User-provided sources:{chr(10)}{sources_text}" if sources_text else ""}

Provide comprehensive information:

## 1. Company Background
- Full legal name [Source]
- Industry/Sector
- Headquarters location
- Founded year
- Number of employees
- Revenue (if public)
- Mission/Vision statement

## 2. Leadership Team
[Extract REAL names and titles from company website]
- CEO: [Name] [Source URL]
- CFO: [Name] [Source URL]
- CTO: [Name] [Source URL]
- Other key executives with names and titles

## 3. Financial Information
- Revenue trends
- Funding/Investors
- Financial health indicators

## 4. News & Recent Activity
- Recent positive news
- Recent negative news/challenges
- Latest announcements

## 5. Products/Services
- Main offerings
- Key clients/customers

## 6. Challenges & Risks
- Known issues
- Market challenges
- Competitive pressures

CITE ALL SOURCES with URLs.
"""

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json={
                        "model": "sonar-pro",
                        "messages": [
                            {"role": "system", "content": "Professional company research assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.2,
                        "max_tokens": 4000
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    citations = result.get("citations", [])
                    
                    return {
                        "raw_response": content,
                        "sources": citations,
                        "query": query,
                        "research_type": "organization",
                        "status": "SUCCESS"
                    }
                else:
                    raise Exception(f"API error: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Organization research error: {e}")
            raise


# ============================================================================
# TEST FUNCTION
# ============================================================================

async def test_with_company():
    """Test with the CORRECT company name"""
    
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n" + "🧪"*40)
    print("     TEST: Research with VERIFIED Company Name")
    print("🧪"*40)
    
    service = PerplexityService()
    
    # TEST CASE: Sanjay Jindal at BUNGE (the correct person!)
    result = await service.fetch_research_data(
        query="Sanjay Jindal",
        research_type="individual",
        sources=[{"name": "LinkedIn", "link": "https://www.linkedin.com/in/sajindal/"}],
        company_name="Bunge",  # ✅ CORRECT COMPANY!
        job_title="Global Leader Bunge Global Business Services",  # Optional
        location="Mumbai, India"  # Optional
    )
    
    print("\n" + "="*80)
    print("📊 RESULT")
    print("="*80)
    print(f"Status: {result.get('status')}")
    print(f"Verified Company: {result.get('verified_company')}")
    print(f"\n📝 Response Preview:")
    print("-"*80)
    print(result.get('raw_response', '')[:2000])
    print("-"*80)


async def test_without_company():
    """Test WITHOUT company name - should request disambiguation"""
    
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n" + "🧪"*40)
    print("     TEST: Research WITHOUT Company Name")
    print("🧪"*40)
    
    service = PerplexityService()
    
    # TEST: No company name provided
    result = await service.fetch_research_data(
        query="Sanjay Jindal",
        research_type="individual",
        sources=[{"name": "LinkedIn", "link": "https://www.linkedin.com/in/sajindal/"}]
        # NO company_name provided!
    )
    
    print("\n" + "="*80)
    print("📊 RESULT")
    print("="*80)
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")
    print(f"\n📝 Response:")
    print("-"*80)
    print(result.get('raw_response', '')[:1500])
    print("-"*80)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SELECT TEST:")
    print("1. Test WITH company name (accurate results)")
    print("2. Test WITHOUT company name (disambiguation)")
    print("="*80)
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(test_with_company())
    else:
        asyncio.run(test_without_company())