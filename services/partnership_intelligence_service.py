"""
Partnership and Alliance Intelligence Service
Module 7 from Sales Enablement Tool (SET)

Tracks partnerships, alliances, and ecosystem relationships
for target organizations.
"""

import httpx
from typing import Dict, Any, Optional
from datetime import datetime


class PartnershipIntelligenceService:
    """
    Partnership and Alliance Intelligence System
    Tracks partnerships including:
    - Strategic partnerships and alliances
    - Technology partnerships
    - Distribution partnerships
    - Channel partnerships
    - Joint ventures
    - Ecosystem participation
    """
    
    def __init__(self, perplexity_api_key: str):
        self.api_key = perplexity_api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def gather_partnership_intelligence(
        self,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Gather partnership and alliance intelligence
        """
        print("\n" + "="*80)
        print("🤝 PARTNERSHIP INTELLIGENCE SYSTEM")
        print("="*80)
        print(f"📊 Target Company: {company_name}")
        print("="*80 + "\n")
        
        partnership_intel = {
            "company_name": company_name,
            "gathered_at": datetime.now().isoformat(),
            "modules": {}
        }
        
        # Module 7.1: Strategic Partnerships
        print("🎯 Module 7.1: Identifying Strategic Partnerships...")
        partnership_intel["modules"]["strategic_partnerships"] = await self._identify_strategic_partnerships(company_name)
        
        # Module 7.2: Technology Partnerships
        print("\n💻 Module 7.2: Identifying Technology Partnerships...")
        partnership_intel["modules"]["technology_partnerships"] = await self._identify_technology_partnerships(company_name)
        
        # Module 7.3: Channel and Distribution
        print("\n📦 Module 7.3: Identifying Channel and Distribution Partners...")
        partnership_intel["modules"]["channel_partnerships"] = await self._identify_channel_partnerships(company_name)
        
        # Module 7.4: Ecosystem Participation
        print("\n🌐 Module 7.4: Analyzing Ecosystem Participation...")
        partnership_intel["modules"]["ecosystem"] = await self._analyze_ecosystem_participation(company_name)
        
        print("\n" + "="*80)
        print("✅ PARTNERSHIP INTELLIGENCE COMPLETED")
        print("="*80 + "\n")
        
        return partnership_intel
    
    async def _identify_strategic_partnerships(self, company_name: str) -> Dict[str, Any]:
        """Identify strategic partnerships and alliances"""
        prompt = f"""
Identify strategic partnerships and alliances for {company_name}.

REQUIRED INFORMATION:
1. MAJOR STRATEGIC PARTNERSHIPS:
   - Partner companies
   - Partnership announcement date
   - Strategic rationale
   - Partnership scope and objectives
   - Joint offerings or initiatives

2. JOINT VENTURES:
   - JV partners
   - JV objectives
   - Ownership structure (if disclosed)

3. STRATEGIC ALLIANCES:
   - Industry alliances
   - Consortium memberships
   - Trade associations

Provide specific partner names, dates, and sources from press releases.
"""
        
        response = await self._query_perplexity(prompt)
        return {
            "raw_data": response.get("content", ""),
            "sources": response.get("sources", [])
        }
    
    async def _identify_technology_partnerships(self, company_name: str) -> Dict[str, Any]:
        """Identify technology partnerships"""
        prompt = f"""
Identify technology partnerships for {company_name}.

REQUIRED INFORMATION:
1. TECHNOLOGY PARTNER ECOSYSTEM:
   - Technology platform partnerships
   - Integration partnerships
   - API partnerships
   - Certified partner programs

2. CLOUD AND INFRASTRUCTURE PARTNERSHIPS:
   - Cloud provider partnerships (AWS, Azure, GCP)
   - Infrastructure technology partners
   - SaaS platform partnerships

3. INNOVATION PARTNERSHIPS:
   - Research partnerships
   - Innovation labs collaborations
   - University partnerships

Provide specific details and sources.
"""
        
        response = await self._query_perplexity(prompt)
        return {
            "raw_data": response.get("content", ""),
            "sources": response.get("sources", [])
        }
    
    async def _identify_channel_partnerships(self, company_name: str) -> Dict[str, Any]:
        """Identify channel and distribution partnerships"""
        prompt = f"""
Identify channel and distribution partnerships for {company_name}.

REQUIRED INFORMATION:
1. DISTRIBUTION PARTNERS:
   - Distribution agreements
   - Reseller partnerships
   - Value-added resellers (VARs)

2. CHANNEL PROGRAM:
   - Channel partner program details
   - Partner tiers
   - Channel incentives

3. REGIONAL PARTNERSHIPS:
   - Geographic-specific partnerships
   - International distributors

Provide specific details and sources.
"""
        
        response = await self._query_perplexity(prompt)
        return {
            "raw_data": response.get("content", ""),
            "sources": response.get("sources", [])
        }
    
    async def _analyze_ecosystem_participation(self, company_name: str) -> Dict[str, Any]:
        """Analyze ecosystem participation"""
        prompt = f"""
Analyze ecosystem participation for {company_name}.

REQUIRED INFORMATION:
1. PLATFORM ECOSYSTEMS:
   - Which platforms/ecosystems does {company_name} participate in?
   - Marketplace presence (AWS Marketplace, Azure Marketplace, etc.)
   - App store presence

2. INDUSTRY ECOSYSTEMS:
   - Industry-specific ecosystems
   - Standards bodies participation
   - Open source community involvement

3. DEVELOPER ECOSYSTEM:
   - Developer programs
   - API ecosystem
   - Developer community

Provide specific details and sources.
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
                                {"role": "system", "content": "You are a partnership intelligence analyst."},
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
