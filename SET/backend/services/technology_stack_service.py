"""
Technology Stack Intelligence Service
Module 6 from Sales Enablement Tool (SET)

Identifies and analyzes the technology stack, tools, and platforms
used by target organizations.
"""

import httpx
from typing import Dict, Any, Optional
from datetime import datetime


class TechnologyStackService:
    """
    Technology Stack Intelligence System
    Identifies technology stack including:
    - Cloud infrastructure and platforms
    - Development tools and languages
    - Enterprise software and SaaS tools
    - Data and analytics platforms
    - Security and compliance tools
    - Marketing and sales technology
    - Collaboration and productivity tools
    """
    
    def __init__(self, perplexity_api_key: str):
        self.api_key = perplexity_api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def gather_technology_intelligence(
        self,
        company_name: str,
        website: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gather technology stack intelligence
        """
        print("\n" + "="*80)
        print("💻 TECHNOLOGY STACK INTELLIGENCE SYSTEM")
        print("="*80)
        print(f"📊 Target Company: {company_name}")
        print("="*80 + "\n")
        
        tech_intel = {
            "company_name": company_name,
            "gathered_at": datetime.now().isoformat(),
            "modules": {}
        }
        
        # Module 6.1: Infrastructure and Cloud
        print("☁️ Module 6.1: Identifying Cloud and Infrastructure...")
        tech_intel["modules"]["cloud_infrastructure"] = await self._identify_cloud_infrastructure(company_name, website)
        
        # Module 6.2: Development Stack
        print("\n👨‍💻 Module 6.2: Identifying Development Stack...")
        tech_intel["modules"]["development_stack"] = await self._identify_development_stack(company_name, website)
        
        # Module 6.3: Enterprise Applications
        print("\n🏢 Module 6.3: Identifying Enterprise Applications...")
        tech_intel["modules"]["enterprise_apps"] = await self._identify_enterprise_apps(company_name)
        
        # Module 6.4: Marketing and Sales Tech
        print("\n📱 Module 6.4: Identifying Marketing and Sales Technology...")
        tech_intel["modules"]["martech_salestech"] = await self._identify_martech_salestech(company_name)
        
        print("\n" + "="*80)
        print("✅ TECHNOLOGY STACK INTELLIGENCE COMPLETED")
        print("="*80 + "\n")
        
        return tech_intel
    
    async def _identify_cloud_infrastructure(self, company_name: str, website: Optional[str]) -> Dict[str, Any]:
        """Identify cloud infrastructure and platforms"""
        prompt = f"""
Identify cloud infrastructure and platforms used by {company_name}.

REQUIRED INFORMATION:
1. CLOUD PROVIDERS:
   - Primary cloud provider (AWS, Azure, GCP, etc.)
   - Multi-cloud strategy
   - Cloud migration status

2. INFRASTRUCTURE:
   - Hosting and infrastructure
   - CDN providers
   - Database platforms
   - Container orchestration (Kubernetes, etc.)

3. TECHNOLOGY ANNOUNCEMENTS:
   - Technology partnerships announced
   - Platform migrations
   - Infrastructure investments

Sources: Job postings, tech blog posts, conference talks, partnerships announced.
Provide specific technologies and sources.
"""
        
        response = await self._query_perplexity(prompt)
        return {
            "raw_data": response.get("content", ""),
            "sources": response.get("sources", [])
        }
    
    async def _identify_development_stack(self, company_name: str, website: Optional[str]) -> Dict[str, Any]:
        """Identify development tools and languages"""
        prompt = f"""
Identify development stack and tools used by {company_name}.

REQUIRED INFORMATION:
1. PROGRAMMING LANGUAGES:
   - Primary languages (from job postings, tech talks)
   - Frontend frameworks (React, Angular, Vue, etc.)
   - Backend frameworks

2. DEVELOPMENT TOOLS:
   - Version control (GitHub, GitLab, Bitbucket)
   - CI/CD tools
   - Development platforms
   - Testing frameworks

3. TECH BLOG INSIGHTS:
   - Technologies mentioned in engineering blog
   - Open source projects
   - Technical conference presentations

Sources: Job postings, engineering blog, GitHub presence, conference talks.
"""
        
        response = await self._query_perplexity(prompt)
        return {
            "raw_data": response.get("content", ""),
            "sources": response.get("sources", [])
        }
    
    async def _identify_enterprise_apps(self, company_name: str) -> Dict[str, Any]:
        """Identify enterprise applications and SaaS tools"""
        prompt = f"""
Identify enterprise applications and SaaS platforms used by {company_name}.

REQUIRED INFORMATION:
1. ENTERPRISE SYSTEMS:
   - ERP system (SAP, Oracle, Workday, etc.)
   - CRM system (Salesforce, HubSpot, Dynamics, etc.)
   - HRIS/HCM systems
   - Financial systems

2. COLLABORATION TOOLS:
   - Communication platforms (Slack, Teams, etc.)
   - Video conferencing
   - Project management tools
   - Document management

3. SECURITY AND COMPLIANCE:
   - Security platforms
   - Identity management
   - Compliance tools

Sources: Technology partnerships, job postings, vendor case studies, press releases.
"""
        
        response = await self._query_perplexity(prompt)
        return {
            "raw_data": response.get("content", ""),
            "sources": response.get("sources", [])
        }
    
    async def _identify_martech_salestech(self, company_name: str) -> Dict[str, Any]:
        """Identify marketing and sales technology"""
        prompt = f"""
Identify marketing and sales technology used by {company_name}.

REQUIRED INFORMATION:
1. MARKETING TECHNOLOGY:
   - Marketing automation platforms
   - Email marketing tools
   - Analytics platforms
   - Advertising technology

2. SALES TECHNOLOGY:
   - Sales engagement platforms
   - Sales intelligence tools
   - CPQ systems
   - Sales analytics

Sources: Job postings, vendor partnerships, tool mentions in content.
"""
        
        response = await self._query_perplexity(prompt)
        return {
            "raw_data": response.get("content", ""),
            "sources": response.get("sources", [])
        }
    
    async def _query_perplexity(self, prompt: str) -> Dict[str, Any]:
        """Query Perplexity API"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            models_to_try = ["sonar", "sonar-pro"]
            
            for model in models_to_try:
                try:
                    response = await client.post(
                        self.base_url,
                        headers=self.headers,
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": "You are a technology intelligence analyst."},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.2,
                            "max_tokens": 4000
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return {
                            "content": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                            "sources": result.get("citations", [])
                        }
                except Exception:
                    continue
            
            return {"content": "", "sources": []}
