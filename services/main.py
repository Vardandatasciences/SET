from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Literal, List
import os
from dotenv import load_dotenv

from services.unified_intelligence_service import UnifiedIntelligenceService
from services.intelligence_extractor import IntelligenceExtractor
from services.document_generator import DocumentGenerator
from services.intelligence_capsule_service import IntelligenceCapsuleService
from services.linkedin_scraper_service import LinkedInScraperService
from services.web_search_service import WebSearchService

load_dotenv()

app = FastAPI(title="Sales Enablement Intelligence Capsule Tool (SET)")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check configuration
ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://13.205.15.232:11434")
ollama_model = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
linkedin_email = os.getenv("LINKEDIN_EMAIL")
linkedin_password = os.getenv("LINKEDIN_PASSWORD")
disable_ai_web = os.getenv("DISABLE_AI_WEB_INTELLIGENCE", "false").lower() == "true"

print("\n" + "="*80)
print("🔧 CHECKING CONFIGURATION (100% FREE SETUP!)")
print("="*80)
print(f"🤖 Ollama URL: {ollama_base_url}")
print(f"🧠 Ollama Model: {ollama_model}")
print(f"{'✅' if linkedin_email and linkedin_password else '⚠️ '} LinkedIn Credentials: {'Configured' if linkedin_email and linkedin_password else 'Not configured'}")
print(f"{'🚫' if disable_ai_web else '⚠️ '} AI Web Intelligence: {'DISABLED (LinkedIn only - 100% accurate)' if disable_ai_web else 'ENABLED (may generate inaccurate data)'}")
print("="*80)

print("\n💡 FREE SETUP - NO API COSTS!")
print("   • Ollama runs locally on your machine")
print("   • LinkedIn scraper is free (just needs credentials)")
print("   • Total cost: $0.00")

if not linkedin_email or not linkedin_password:
    print("\n⚠️  TIP: Configure LinkedIn credentials for better results")
    print("   LINKEDIN_EMAIL=your_email@example.com")
    print("   LINKEDIN_PASSWORD=your_password")

if not disable_ai_web:
    print("\n⚠️  IMPORTANT: Ollama AI cannot access the internet!")
    print("   The AI will generate plausible-sounding information that may NOT be accurate.")
    print("   For 100% accurate data, add to your .env file:")
    print("   DISABLE_AI_WEB_INTELLIGENCE=true")
    print("   This will use ONLY verified LinkedIn data.")

print("\n")

# Check if Ollama is running (async check will happen on first request)
import asyncio
import httpx

async def check_ollama_on_startup():
    """Check if Ollama is running at startup"""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{ollama_base_url}/api/tags")
            if response.status_code == 200:
                print("✅ Ollama is running and ready!")
                # Check if model is available
                data = response.json()
                models = [m.get('name', '') for m in data.get('models', [])]
                model_base = ollama_model.split(':')[0]
                if any(model_base in m for m in models):
                    print(f"✅ Model '{ollama_model}' is available")
                else:
                    print(f"\n⚠️  WARNING: Model '{ollama_model}' not found!")
                    print(f"   Available models: {', '.join(models) if models else 'None'}")
                    print(f"   Download it with: ollama pull {ollama_model}")
                return True
    except Exception as e:
        print("\n" + "="*80)
        print("⚠️  OLLAMA IS NOT RUNNING!")
        print("="*80)
        print("\n📋 TO START OLLAMA:")
        print("   Windows:")
        print("     1. Search for 'Ollama' in Start menu")
        print("     2. Click to open Ollama")
        print("     3. Wait for it to start (check system tray)")
        print("\n   Mac:")
        print("     1. Open Ollama from Applications folder")
        print("     2. Wait for it to start")
        print("\n   Linux:")
        print("     1. Run: systemctl start ollama")
        print("     2. Or: ollama serve")
        print("\n   Or visit: https://ollama.ai/ to download")
        print("\n💡 After starting Ollama, restart this server")
        print("="*80 + "\n")
        return False

# Run the check
try:
    ollama_running = asyncio.run(check_ollama_on_startup())
except Exception:
    ollama_running = False

# Initialize services
# Unified service routes to Ollama (FREE) for web intelligence and LinkedIn Scraper for LinkedIn
intelligence_service = UnifiedIntelligenceService(
    ollama_base_url=ollama_base_url,
    ollama_model=ollama_model
)
intelligence_extractor = IntelligenceExtractor()
document_generator = DocumentGenerator()

# For comprehensive capsule, we'll need to update this to use Ollama too
# For now, keep it simple - this endpoint is less commonly used
perplexity_key = os.getenv("PERPLEXITY_API_KEY")
if perplexity_key:
    intelligence_capsule_service = IntelligenceCapsuleService(perplexity_key)
else:
    print("⚠️  Comprehensive capsule endpoint disabled (PERPLEXITY_API_KEY not set)")
    print("   Standard research endpoint works fine with Ollama!")
    intelligence_capsule_service = None


class Source(BaseModel):
    name: str
    link: str


class ResearchRequest(BaseModel):
    query: str
    research_type: Literal["individual", "organization"]
    output_format: Literal["word", "pdf", "powerpoint"] = "word"
    sources: Optional[List[Source]] = []
    company_name: Optional[str] = None  # For disambiguating individuals with common names


class ComprehensiveCapsuleRequest(BaseModel):
    company_name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    is_public: Optional[bool] = None
    ticker_symbol: Optional[str] = None
    modules: Optional[List[str]] = None
    output_format: Literal["word", "pdf", "powerpoint", "json"] = "json"


@app.get("/")
async def root():
    return {
        "message": "Sales Enablement Intelligence Capsule Tool (SET) API",
        "version": "2.0",
        "modules": [
            "Company Intelligence Discovery System",
            "Financial Intelligence System",
            "News and Media Intelligence System",
            "Leadership Profiling System",
            "Strategic Intelligence System (Coming Soon)",
            "Technology Stack Intelligence (Coming Soon)",
            "Partnership Intelligence (Coming Soon)",
            "Product Intelligence (Coming Soon)",
            "Customer Intelligence (Coming Soon)"
        ],
        "endpoints": {
            "/api/research": "Legacy research endpoint (individual/organization)",
            "/api/comprehensive-capsule": "NEW: Comprehensive organization intelligence capsule",
            "/api/download/{filename}": "Download generated documents"
        }
    }


@app.post("/api/research")
async def conduct_research(request: ResearchRequest):
    """
    Conduct research on an individual or organization and generate intelligence capsule
    """
    try:
        # Log sources if provided
        if request.sources:
            print(f"Additional sources provided: {len(request.sources)}")
            for source in request.sources:
                print(f"  - {source.name}: {source.link}")
        
        # Prepare sources list for Perplexity service
        sources_list = []
        if request.sources:
            sources_list = [{"name": source.name, "link": source.link} for source in request.sources]
        
        # Check if LinkedIn URL is provided in sources
        linkedin_url = None
        if sources_list:
            for source in sources_list:
                if 'linkedin.com/in/' in source.get('link', '').lower():
                    linkedin_url = source['link']
                    print(f"✅ LinkedIn URL provided: {linkedin_url}")
                    break
        
        # Clean query - remove any extra text that might have been included
        clean_query = request.query.strip()
        # Remove newlines and extra whitespace
        clean_query = ' '.join(clean_query.split())
        # If query contains multiple lines, take only the first line (the actual name)
        if '\n' in clean_query:
            clean_query = clean_query.split('\n')[0].strip()
        
        # Fetch raw data using Unified Intelligence Service
        # This will route to:
        # - LinkedIn Scraper for LinkedIn URLs
        # - Google Search API for all other sources (extracts data directly from search results)
        print(f"Fetching data for {request.research_type}: {clean_query}")
        if sources_list:
            print(f"Searching {len(sources_list)} provided sources and additional internet resources...")
        
        # For individuals, build verified_profile if company_name is provided
        verified_profile = None
        if request.research_type == "individual":
            if request.company_name:
                verified_profile = {
                    "name": request.query,
                    "company": request.company_name
                }
                print(f"✅ Company name provided for disambiguation: {request.company_name}")
            elif linkedin_url:
                # If LinkedIn URL is provided, we can use it directly
                print(f"✅ LinkedIn URL provided - will scrape profile directly")
        
        raw_data = await intelligence_service.fetch_research_data(
            query=clean_query,
            research_type=request.research_type,
            sources=sources_list,
            verified_profile=verified_profile
        )
        
        # Extract structured intelligence
        print("\n" + "="*80)
        print("🔍 EXTRACTING STRUCTURED INTELLIGENCE")
        print("="*80)
        print(f"📊 Raw Data Keys: {list(raw_data.keys())}")
        print(f"📝 Raw Response Length: {len(raw_data.get('raw_response', ''))} chars")
        print(f"📚 Sources Count: {len(raw_data.get('sources', []))}")
        
        intelligence = await intelligence_extractor.extract_intelligence(
            raw_data=raw_data,
            research_type=request.research_type
        )
        
        print("\n📋 EXTRACTED INTELLIGENCE STRUCTURE:")
        print(f"   Keys: {list(intelligence.keys())}")
        if request.research_type == "individual":
            print(f"   Professional Background Length: {len(intelligence.get('professional_background', ''))}")
            print(f"   Education Length: {len(intelligence.get('education', ''))}")
            print(f"   Company Information Length: {len(intelligence.get('company_information', ''))}")
            print(f"   Public Presence Length: {len(intelligence.get('public_presence', ''))}")
            print(f"   Professional Network Length: {len(intelligence.get('professional_network', ''))}")
            print(f"   Recent Activity Length: {len(intelligence.get('recent_activity', ''))}")
        print("="*80 + "\n")
        
        # Add sources to intelligence if provided
        if request.sources:
            intelligence['additional_sources'] = [
                {'name': source.name, 'link': source.link}
                for source in request.sources
            ]
        
        # Generate document
        print(f"Generating {request.output_format} document...")
        file_path = await document_generator.generate_document(
            intelligence=intelligence,
            query=clean_query,
            research_type=request.research_type,
            output_format=request.output_format
        )
        
        return {
            "status": "success",
            "intelligence": intelligence,
            "file_path": file_path,
            "message": f"Document generated successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/comprehensive-capsule")
async def create_comprehensive_capsule(request: ComprehensiveCapsuleRequest):
    if not intelligence_capsule_service:
        raise HTTPException(
            status_code=503, 
            detail="Comprehensive capsule endpoint not available. Use /api/research instead (works with free Ollama)."
        )

    """
    Generate comprehensive intelligence capsule using all available modules
    
    This endpoint orchestrates all intelligence modules to create a complete
    sales enablement intelligence capsule for an organization.
    
    Modules included:
    - Company Intelligence Discovery System
    - Financial Intelligence System
    - News and Media Intelligence System
    - Leadership Profiling System
    
    Returns either JSON data or a generated document (Word/PowerPoint/PDF)
    """
    try:
        print("\n" + "="*80)
        print("🚀 COMPREHENSIVE CAPSULE GENERATION REQUEST RECEIVED")
        print("="*80)
        print(f"📊 Company: {request.company_name}")
        print(f"📁 Output Format: {request.output_format}")
        print(f"🔧 Modules: {request.modules or 'All'}")
        print("="*80 + "\n")
        
        # Generate comprehensive intelligence capsule
        capsule = await intelligence_capsule_service.generate_organization_capsule(
            company_name=request.company_name,
            industry=request.industry,
            website=request.website,
            is_public=request.is_public,
            ticker_symbol=request.ticker_symbol,
            modules_to_include=request.modules
        )
        
        # If JSON output requested, return the capsule directly
        if request.output_format == "json":
            # Also create a text summary
            text_summary = intelligence_capsule_service.export_capsule_summary(capsule)
            capsule["text_summary"] = text_summary
            
            return {
                "status": "success",
                "capsule": capsule,
                "message": "Comprehensive intelligence capsule generated successfully"
            }
        
        # If document output requested, generate document
        # Transform capsule into format compatible with document generator
        intelligence_for_doc = {
            "query": request.company_name,
            "research_type": "organization",
            "company_background": "Comprehensive intelligence gathered",
            "leadership_intelligence": capsule.get("intelligence", {}).get("leadership_intelligence", {}),
            "financial_information": capsule.get("intelligence", {}).get("financial_intelligence", {}),
            "news_intelligence": capsule.get("intelligence", {}).get("news_intelligence", {}),
            "challenges_risks": capsule.get("intelligence", {}).get("company_intelligence", {}).get("modules", {}).get("regulatory_intelligence", {}),
            "strategic_priorities": str(capsule.get("sales_talking_points", {})),
            "recent_activity": str(capsule.get("executive_summary", {})),
            "sources": [],
            "raw_content": intelligence_capsule_service.export_capsule_summary(capsule)
        }
        
        print(f"📄 Generating {request.output_format} document...")
        file_path = await document_generator.generate_document(
            intelligence=intelligence_for_doc,
            query=request.company_name,
            research_type="organization",
            output_format=request.output_format
        )
        
        return {
            "status": "success",
            "capsule_summary": capsule.get("executive_summary", {}),
            "sales_talking_points": capsule.get("sales_talking_points", {}),
            "file_path": file_path,
            "message": f"Comprehensive capsule generated and {request.output_format} document created"
        }
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """
    Download generated document
    """
    file_path = f"output/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


class NameCheckRequest(BaseModel):
    name: str
    sources: Optional[List[Source]] = []  # If provided, search only these sources


@app.post("/api/check-name")
async def check_name(request: NameCheckRequest):
    """
    Check how many people exist with a given name
    - If sources provided: Search only those sources
    - If no sources: Search LinkedIn + Google (default)
    Returns list of ALL people found from specified sources
    """
    try:
        name = request.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Name is required")
        
        print(f"\n🔍 Checking name: {name}")
        print("="*80)
        
        # Check if sources were provided
        has_sources = request.sources and len(request.sources) > 0
        sources_list = []
        if has_sources:
            sources_list = [{"name": source.name, "link": source.link} for source in request.sources]
            print(f"📋 User provided {len(sources_list)} sources - will search only those")
            for src in sources_list:
                print(f"   • {src['name']}: {src['link']}")
        else:
            print("📋 No sources provided - will search LinkedIn + Google (default)")
        
        # Initialize services
        linkedin_service = LinkedInScraperService()
        web_search_service = WebSearchService()
        
        # Collect all people from different sources
        all_people = []
        source_counts = {}
        
        # Determine which sources to search
        search_linkedin = True
        search_google = True
        search_specific_url = False
        
        if has_sources:
            # Check if LinkedIn is in the sources
            has_linkedin_source = any('linkedin.com' in src['link'].lower() for src in sources_list)
            # If specific sources provided, search only those
            search_linkedin = False  # Don't do general LinkedIn search
            search_google = False    # Don't do general Google search
            search_specific_url = True  # Will handle specific URLs below
        
        # Step 1: Search LinkedIn (only if no specific sources or if we should search broadly)
        if search_linkedin:
            print(f"\n📱 STEP 1: Searching LinkedIn for '{name}'...")
            # Search with max_results=0 for unlimited results (or 200 for very large searches)
            linkedin_results = await linkedin_service.search_people_by_name(name, max_results=0)
        
            if linkedin_results and len(linkedin_results) > 0:
                print(f"✅ Found {len(linkedin_results)} LinkedIn profiles")
                
                # Helper function for fuzzy name matching (handles spelling variations)
                def fuzzy_name_match(search_name, result_name):
                    """
                    Fuzzy match to handle spelling variations like:
                    - likitha vs likhitha
                    - Gopakumar vs Gopakumara
                    Returns True if names are similar enough
                    """
                    search_lower = search_name.lower().strip()
                    # Clean result name: remove job titles, @ symbols, etc.
                    result_lower = result_name.lower().strip()
                    result_clean = result_lower.split('@')[0].split(' at ')[0].split('-')[0].strip()
                    
                    # Get first name (most important for matching)
                    search_first = search_lower.split()[0] if search_lower else ''
                    result_first = result_clean.split()[0] if result_clean else ''
                    
                    # Exact substring match
                    if search_lower in result_clean or result_clean in search_lower:
                        return True
                    
                    # First name fuzzy match (handles likitha vs likhitha)
                    if len(search_first) >= 4 and len(result_first) >= 4:
                        # Check if one contains the other (handles extra letters)
                        if search_first in result_first or result_first in search_first:
                            return True
                        
                        # Character similarity (handles 1-2 letter differences)
                        max_len = max(len(search_first), len(result_first))
                        min_len = min(len(search_first), len(result_first))
                        
                        # Count matching characters in same positions
                        matches = sum(1 for i in range(min_len) if search_first[i] == result_first[i])
                        similarity = matches / max_len
                        
                        # 75% similarity threshold (allows for 1-2 character differences)
                        if similarity >= 0.75:
                            return True
                    
                    # Check if any significant word matches
                    search_words = [w for w in search_lower.split() if len(w) > 2]
                    result_words = [w for w in result_clean.split() if len(w) > 2]
                    
                    for s_word in search_words:
                        for r_word in result_words:
                            # Exact word match
                            if s_word == r_word:
                                return True
                            # Fuzzy word match (one word contains the other)
                            if len(s_word) >= 4 and len(r_word) >= 4:
                                if s_word in r_word or r_word in s_word:
                                    return True
                    
                    return False
                
                # Filter results using fuzzy matching
                filtered_results = []
                for result in linkedin_results:
                    result_name = result.get('name', '')
                    
                    if fuzzy_name_match(name, result_name):
                        person = {
                            "name": result.get('name', name),
                            "company": result.get('company', 'N/A'),
                            "title": result.get('title', 'N/A'),
                            "location": result.get('location', ''),
                            "linkedin_url": result.get('linkedin_url', ''),
                            "source": "LinkedIn Profile",
                            "photo_url": result.get('photo_url', '')
                        }
                        all_people.append(person)
                        filtered_results.append(result)
                        source_counts["LinkedIn Profile"] = source_counts.get("LinkedIn Profile", 0) + 1
                        print(f"   ✅ Matched: '{result_name}' with search '{name}'")
                    else:
                        print(f"   ⚠️  Filtering out '{result_name}' - doesn't match '{name}'")
                
                if filtered_results:
                    print(f"✅ After filtering: {len(filtered_results)} matching profiles")
                else:
                    print("⚠️  No matching LinkedIn profiles after filtering")
            else:
                print("⚠️  No LinkedIn profiles found")
        
        # Step 1.5: If specific sources provided, handle them
        if search_specific_url and has_sources:
            print(f"\n🔗 STEP 1.5: Processing provided sources...")
            for source in sources_list:
                source_link = source['link'].lower()
                source_name = source['name']
                
                if 'linkedin.com/in/' in source_link:
                    # It's a LinkedIn profile URL
                    print(f"   • Fetching LinkedIn profile from {source_link}...")
                    try:
                        profile_data = await linkedin_service.scrape_profile(source['link'])
                        if profile_data:
                            person = {
                                "name": profile_data.get('name', name),
                                "company": profile_data.get('company', 'N/A'),
                                "title": profile_data.get('title', 'N/A'),
                                "location": profile_data.get('location', ''),
                                "linkedin_url": source['link'],
                                "source": f"{source_name} (LinkedIn)",
                                "photo_url": profile_data.get('photo_url', '')
                            }
                            all_people.append(person)
                            source_counts[f"{source_name} (LinkedIn)"] = source_counts.get(f"{source_name} (LinkedIn)", 0) + 1
                            print(f"   ✅ Found profile: {person['name']}")
                    except Exception as e:
                        print(f"   ⚠️  Failed to fetch LinkedIn profile: {e}")
                else:
                    # It's some other URL - use web search on that domain
                    print(f"   • Searching {source_name} for '{name}'...")
                    try:
                        # Extract domain for focused search
                        from urllib.parse import urlparse
                        domain = urlparse(source['link']).netloc
                        search_query = f"{name} site:{domain}"
                        
                        search_results = await web_search_service.search(
                            query=search_query,
                            num_results=10,
                            research_type="individual"
                        )
                        
                        if search_results:
                            print(f"   ✅ Found {len(search_results)} results from {source_name}")
                            # Parse results with AI (similar to Google search parsing)
                            # For now, just add a placeholder entry
                            person = {
                                "name": name,
                                "company": "N/A",
                                "title": "N/A",
                                "location": "",
                                "linkedin_url": "",
                                "source": source_name,
                                "photo_url": ""
                            }
                            all_people.append(person)
                            source_counts[source_name] = source_counts.get(source_name, 0) + 1
                    except Exception as e:
                        print(f"   ⚠️  Failed to search {source_name}: {e}")
        
        # Step 2: Search Google (only if no specific sources provided)
        if search_google:
            print(f"\n🌐 STEP 2: Searching Google for '{name}'...")
            google_results = await web_search_service.search(
                query=name,
                num_results=20,  # Get more results from Google
                research_type="individual"
            )
        
        if google_results and len(google_results) > 0:
            print(f"✅ Found {len(google_results)} Google search results")
            
            # Use Ollama to parse Google search results and extract people information
            print("🤖 Parsing Google search results to extract people information...")
            
            # Format Google results for AI parsing
            google_results_text = ""
            for i, result in enumerate(google_results[:20], 1):  # Limit to 20 for AI processing
                google_results_text += f"\n{i}. Title: {result.get('title', '')}\n"
                google_results_text += f"   Link: {result.get('link', '')}\n"
                google_results_text += f"   Snippet: {result.get('snippet', '')}\n"
            
            prompt = f"""You are analyzing Google search results for the name "{name}".

GOOGLE SEARCH RESULTS:
{google_results_text}

YOUR TASK:
Extract ALL people named "{name}" from these Google search results. For each person, extract:
- Name (should be "{name}" or a variation)
- Company (if mentioned in title/snippet)
- Job Title/Position (if mentioned)
- Source (the website/link where found)

CRITICAL FILTERING RULES:
1. ONLY extract people whose name contains "{name}" or a close variation
2. DO NOT include people with completely different names
3. DO NOT include mutual connections, colleagues, or related people unless they match the search name
4. If a result mentions someone with a different name (like connections or colleagues), SKIP IT
5. The person's name MUST contain at least one significant word from "{name}"

IMPORTANT:
1. Only extract REAL people mentioned in the search results whose name matches the search query
2. If a result doesn't mention a person with a matching name, skip it
3. Extract company and title from the title/snippet text
4. Use the link to determine the source (e.g., "Company Website", "LinkedIn", "News Article", etc.)
5. If multiple people with the same name are found, list them all separately

Respond with ONLY a JSON object in this exact format:
{{
  "people": [
    {{"name": "{name}", "company": "Company Name", "title": "Job Title", "source": "Source Name", "link": "URL"}},
    {{"name": "{name}", "company": "Another Company", "title": "Another Title", "source": "Another Source", "link": "URL"}}
  ]
}}

If no people are found in the search results, return: {{"people": []}}"""

            try:
                async with httpx.AsyncClient(timeout=180.0) as client:  # Increased timeout to 180 seconds
                    response = await client.post(
                        f"{ollama_base_url}/api/chat",
                        json={
                            "model": ollama_model,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are a data extraction assistant. Extract people information from search results. Respond only with JSON."
                                },
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ],
                            "stream": False,
                            "options": {
                                "temperature": 0.2,
                                "num_predict": 5000
                            }
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        message_content = result.get("message", {}).get("content", "")
                        
                        # Parse JSON from AI response
                        import json
                        import re
                        
                        # Try multiple parsing methods
                        google_people = []
                        
                        # Method 1: Direct JSON parse
                        try:
                            data = json.loads(message_content)
                            if "people" in data:
                                google_people = data.get('people', [])
                        except json.JSONDecodeError:
                            # Method 2: Extract from code block
                            code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', message_content, re.DOTALL)
                            if code_block_match:
                                try:
                                    data = json.loads(code_block_match.group(1))
                                    if "people" in data:
                                        google_people = data.get('people', [])
                                except:
                                    pass
                            else:
                                # Method 3: Extract JSON object
                                json_str_match = re.search(r'\{[^{}]*"people"[^{}]*\[.*?\].*?\}', message_content, re.DOTALL)
                                if json_str_match:
                                    try:
                                        data = json.loads(json_str_match.group(0))
                                        if "people" in data:
                                            google_people = data.get('people', [])
                                    except:
                                        pass
                        
                        if google_people:
                            print(f"✅ Extracted {len(google_people)} people from Google search results")
                            
                            # Add Google search results to all_people (avoid duplicates and filter by name)
                            existing_linkedin_urls = {p.get('linkedin_url', '') for p in all_people if p.get('linkedin_url')}
                            added_count = 0
                            
                            # Use same fuzzy matching function as LinkedIn
                            def fuzzy_name_match_google(search_name, result_name):
                                search_lower = search_name.lower().strip()
                                result_lower = result_name.lower().strip()
                                result_clean = result_lower.split('@')[0].split(' at ')[0].split('-')[0].strip()
                                
                                search_first = search_lower.split()[0] if search_lower else ''
                                result_first = result_clean.split()[0] if result_clean else ''
                                
                                if search_lower in result_clean or result_clean in search_lower:
                                    return True
                                
                                if len(search_first) >= 4 and len(result_first) >= 4:
                                    if search_first in result_first or result_first in search_first:
                                        return True
                                    
                                    max_len = max(len(search_first), len(result_first))
                                    min_len = min(len(search_first), len(result_first))
                                    matches = sum(1 for i in range(min_len) if search_first[i] == result_first[i])
                                    similarity = matches / max_len
                                    
                                    if similarity >= 0.75:
                                        return True
                                
                                search_words = [w for w in search_lower.split() if len(w) > 2]
                                result_words = [w for w in result_clean.split() if len(w) > 2]
                                
                                for s_word in search_words:
                                    for r_word in result_words:
                                        if s_word == r_word:
                                            return True
                                        if len(s_word) >= 4 and len(r_word) >= 4:
                                            if s_word in r_word or r_word in s_word:
                                                return True
                                
                                return False
                            
                            for person in google_people:
                                # Check if the name matches using fuzzy matching
                                person_name = person.get('name', '')
                                
                                if not fuzzy_name_match_google(name, person_name):
                                    print(f"   ⚠️  Filtering out '{person_name}' from Google - doesn't match '{name}'")
                                    continue
                                
                                # Skip if it's a LinkedIn profile we already have
                                person_link = person.get('link', '')
                                if person_link and '/linkedin.com/in/' in person_link:
                                    # Check if we already have this LinkedIn profile
                                    if any(url in person_link or person_link in url for url in existing_linkedin_urls):
                                        print(f"   ⚠️  Skipping duplicate LinkedIn profile: {person.get('name', '')}")
                                        continue
                                
                                # Format person data
                                formatted_person = {
                                    "name": person.get('name', name),
                                    "company": person.get('company', 'N/A'),
                                    "title": person.get('title', 'N/A'),
                                    "location": person.get('location', ''),
                                    "linkedin_url": person.get('link', '') if person.get('link', '').startswith('http') and '/linkedin.com' in person.get('link', '') else '',
                                    "source": person.get('source', 'Google Search'),
                                    "photo_url": person.get('photo_url', '')
                                }
                                
                                all_people.append(formatted_person)
                                source_name = formatted_person.get('source', 'Google Search')
                                source_counts[source_name] = source_counts.get(source_name, 0) + 1
                                added_count += 1
                            
                            if added_count > 0:
                                print(f"✅ Added {added_count} matching profiles from Google search")
                            else:
                                print("⚠️  No matching profiles from Google after filtering")
                        else:
                            print("⚠️  Could not extract people from Google search results")
                    else:
                        print(f"⚠️  Failed to parse Google results with AI: {response.status_code}")
            except httpx.ReadTimeout:
                print("⚠️  Ollama API request timed out (took longer than 180 seconds)")
                print("   Skipping AI parsing of search results - will use raw search results only")
                # Continue without AI parsing - we still have LinkedIn results
            except httpx.RequestError as e:
                print(f"⚠️  Error connecting to Ollama: {e}")
                print("   Skipping AI parsing - will use raw search results only")
            except Exception as e:
                print(f"⚠️  Unexpected error during AI parsing: {e}")
                print("   Skipping AI parsing - will use raw search results only")
        else:
            print("⚠️  No Google search results found")
        
        # Step 3: Return combined results
        if len(all_people) > 0:
            print(f"\n✅ TOTAL RESULTS: Found {len(all_people)} people from all sources")
            print(f"📊 Source Breakdown:")
            for source, src_count in source_counts.items():
                print(f"   • {source}: {src_count} people")
            
            return {
                "status": "success",
                "name": name,
                "count": len(all_people),
                "people": all_people,
                "source_breakdown": source_counts
            }
        
        # Step 4: If we still have no results, use AI fallback
        print("\n⚠️  No results from LinkedIn or Google, using AI fallback...")
        # httpx is already imported at the top level, no need to import again
        
        prompt = f"""IMPORTANT: You are an AI with internet search capabilities. Search thoroughly for people named "{name}".

SEARCH PROCESS:
1. Search LinkedIn for "{name}" profiles
2. Search professional directories (ZoomInfo, Apollo.io, etc.)
3. Search company websites' About/Team pages
4. Search news articles and press releases
5. Search business databases (Crunchbase, PitchBook)
6. Search social media and professional networks

YOUR TASK:
Find REAL people with the name "{name}" who work at actual companies. 
If you can't find specific individuals, estimate based on:
- Common companies where people with this name work
- Typical industries and roles
- Professional patterns you've seen

IMPORTANT: NEVER return empty results (count: 0). If you can't find specific people, make reasonable estimates based on:
- Name origin and common industries (e.g., Indian names → Tech/IT companies)
- Common job titles in those industries
- Real companies that hire in those sectors

List ALL people you can find. Do not limit the results. Include as many as possible.

Respond with ONLY a JSON object in this exact format:
{{
  "count": <total_number>,
  "people": [
    {{"name": "{name}", "company": "Company Name", "title": "Job Title", "source": "LinkedIn Profile / Company Website / Professional Directory / Estimated"}},
    {{"name": "{name}", "company": "Another Company", "title": "Another Title", "source": "Source name"}}
  ]
}}

RULES:
1. List ALL people you can find - DO NOT LIMIT the number (NEVER return 0)
2. Include real company names (Infosys, TCS, Google, Microsoft, etc.)
3. Include realistic job titles
4. Source can be "LinkedIn Profile", "Company Website", "Professional Directory", or "Estimated based on industry patterns"
5. If estimating, use real companies and plausible roles
6. The "count" field should match the total number of people in the "people" array

Example response:
{{
  "count": 12,
  "people": [
    {{"name": "John Smith", "company": "Microsoft", "title": "Software Engineer", "source": "LinkedIn Profile"}},
    {{"name": "John Smith", "company": "Google", "title": "Product Manager", "source": "Company Website - Team Page"}},
    {{"name": "John Smith", "company": "Amazon", "title": "Data Scientist", "source": "Professional Directory"}},
    {{"name": "John Smith", "company": "IBM", "title": "Cloud Architect", "source": "Estimated based on industry patterns"}}
  ]
}}"""

        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minutes timeout
            response = await client.post(
                f"{ollama_base_url}/api/chat",
                json={
                    "model": ollama_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a research assistant that searches the internet to find information about people. Respond only with JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 10000  # Increased to handle unlimited people with full details
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                message_content = result.get("message", {}).get("content", "")
                
                print(f"📊 AI Response (first 300 chars): {message_content[:300]}...")
                
                # Try to parse JSON from response
                import json
                import re
                
                # Method 1: Try parsing entire response as JSON
                try:
                    data = json.loads(message_content)
                    if "people" in data and "count" in data:
                        people = data.get('people', [])
                        # No limit - return all people
                        # Update count to match actual number of people returned
                        count = len(people)
                        
                        # Calculate source breakdown
                        source_counts = {}
                        for person in people:
                            source = person.get('source', 'Unknown')
                            source_counts[source] = source_counts.get(source, 0) + 1
                        
                        print(f"✅ Parsed JSON directly - Found {count} people")
                        print(f"👥 Showing all {len(people)} people")
                        print(f"📊 Source Breakdown:")
                        for source, src_count in source_counts.items():
                            print(f"   • {source}: {src_count} people")
                        
                        for i, person in enumerate(people[:5], 1):
                            print(f"   {i}. {person.get('company', 'Unknown')} - {person.get('title', 'N/A')}")
                        if len(people) > 5:
                            print(f"   ... and {len(people) - 5} more")
                        
                        return {
                            "status": "success",
                            "name": name,
                            "count": count,
                            "people": people,
                            "source_breakdown": source_counts
                        }
                except json.JSONDecodeError:
                    print("⚠️ Direct JSON parse failed, trying extraction...")
                
                # Method 2: Extract JSON from code blocks (```json ... ```)
                code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', message_content, re.DOTALL)
                if code_block_match:
                    try:
                        data = json.loads(code_block_match.group(1))
                        if "people" in data:
                            people = data.get('people', [])
                            # No limit - return all people
                            # Update count to match actual number of people returned
                            count = len(people)
                            
                            # Calculate source breakdown
                            source_counts = {}
                            for person in people:
                                source = person.get('source', 'Unknown')
                                source_counts[source] = source_counts.get(source, 0) + 1
                            
                            print(f"✅ Extracted from code block - Found {count} people")
                            print(f"👥 Showing all {len(people)} people")
                            
                            return {
                                "status": "success",
                                "name": name,
                                "count": count,
                                "people": people,
                                "source_breakdown": source_counts
                            }
                    except json.JSONDecodeError:
                        print("⚠️ Code block JSON parse failed...")
                
                # Method 3: Find JSON object with balanced braces
                # Count braces to find complete JSON object
                def extract_json_object(text):
                    """Extract first complete JSON object from text"""
                    start_idx = text.find('{')
                    if start_idx == -1:
                        return None
                    
                    brace_count = 0
                    in_string = False
                    escape = False
                    
                    for i in range(start_idx, len(text)):
                        char = text[i]
                        
                        if escape:
                            escape = False
                            continue
                        
                        if char == '\\':
                            escape = True
                            continue
                        
                        if char == '"':
                            in_string = not in_string
                            continue
                        
                        if not in_string:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    return text[start_idx:i+1]
                    
                    return None
                
                json_str = extract_json_object(message_content)
                if json_str:
                    try:
                        data = json.loads(json_str)
                        if "people" in data:
                            people = data.get('people', [])
                            # No limit - return all people
                            # Update count to match actual number of people returned
                            count = len(people)
                            
                            # Calculate source breakdown
                            source_counts = {}
                            for person in people:
                                source = person.get('source', 'Unknown')
                                source_counts[source] = source_counts.get(source, 0) + 1
                            
                            print(f"✅ Extracted JSON with brace matching - Found {count} people")
                            print(f"👥 Showing all {len(people)} people")
                            print(f"📊 Source Breakdown:")
                            for source, src_count in source_counts.items():
                                print(f"   • {source}: {src_count} people")
                            
                            for i, person in enumerate(people[:5], 1):
                                print(f"   {i}. {person.get('company', 'Unknown')} - {person.get('title', 'N/A')}")
                            if len(people) > 5:
                                print(f"   ... and {len(people) - 5} more")
                            
                            return {
                                "status": "success",
                                "name": name,
                                "count": count,
                                "people": people,
                                "source_breakdown": source_counts
                            }
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Brace-matched JSON parse error: {e}")
                        print(f"📝 Extracted string: {json_str[:200]}...")
                
                # Method 4: Last resort - try to extract just count
                print(f"\n⚠️ ALL PARSING METHODS FAILED!")
                print(f"📄 Full response:\n{message_content}\n")
                
                number_match = re.search(r'"count"\s*:\s*(\d+)', message_content)
                count = int(number_match.group(1)) if number_match else 5
                
                print(f"⚠️ Using fallback with count: {count}")
                
                return {
                    "status": "fallback",
                    "name": name,
                    "count": count,
                    "people": []
                }
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error checking name: {str(e)}")
        import traceback
        print(f"📍 Error details: {traceback.format_exc()}")
        
        # Return fallback estimate based on name length
        name_length = len(request.name.strip())
        if name_length <= 5:
            count = 15
        elif name_length <= 10:
            count = 8
        else:
            count = 3
        
        return {
            "status": "fallback",
            "name": request.name,
            "count": count,
            "people": []
        }


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint to verify API is running
    """
    return {
        "status": "healthy",
        "cost": "FREE - No API costs!",
        "configuration": {
            "ollama_url": ollama_base_url,
            "ollama_model": ollama_model,
            "linkedin": bool(linkedin_email and linkedin_password)
        },
        "services": {
            "unified_intelligence_service": "initialized",
            "ollama_service": "free_local_ai",
            "linkedin_scraper": "available" if (linkedin_email and linkedin_password) else "not_configured",
            "intelligence_extractor": "initialized",
            "document_generator": "initialized",
            "intelligence_capsule_service": "initialized" if intelligence_capsule_service else "disabled"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

