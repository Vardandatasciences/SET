"""
Strategic Intelligence System
Module 5 from Sales Enablement Tool (SET)

This module provides strategic intelligence including strategic priorities,
digital transformation initiatives, growth strategies, M&A strategy,
and competitive positioning.
"""

import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime


class StrategicIntelligenceService:
    """
    Strategic Intelligence System
    Analyzes company strategy including:
    - Strategic priorities and initiatives
    - Digital transformation programs
    - Growth strategies and expansion plans
    - M&A strategy and activity
    - Innovation and R&D strategy
    - Competitive positioning strategy
    - Market positioning and go-to-market
    - Strategic partnerships approach
    """
    
    def __init__(self, perplexity_api_key: str):
        self.api_key = perplexity_api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def gather_strategic_intelligence(
        self,
        company_name: str,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main orchestrator for strategic intelligence gathering
        """
        print("\n" + "="*80)
        print("🎯 STRATEGIC INTELLIGENCE SYSTEM")
        print("="*80)
        print(f"📊 Target Company: {company_name}")
        print("="*80 + "\n")
        
        strategic_intel = {
            "company_name": company_name,
            "gathered_at": datetime.now().isoformat(),
            "modules": {}
        }
        
        # Module 5.1: Strategic Priorities
        print("🎯 Module 5.1: Identifying Strategic Priorities...")
        strategic_intel["modules"]["strategic_priorities"] = await self._identify_strategic_priorities(company_name)
        
        # Module 5.2: Digital Transformation
        print("\n💻 Module 5.2: Analyzing Digital Transformation Initiatives...")
        strategic_intel["modules"]["digital_transformation"] = await self._analyze_digital_transformation(company_name)
        
        # Module 5.3: Growth Strategy
        print("\n📈 Module 5.3: Analyzing Growth Strategy...")
        strategic_intel["modules"]["growth_strategy"] = await self._analyze_growth_strategy(company_name)
        
        # Module 5.4: Innovation Strategy
        print("\n🚀 Module 5.4: Analyzing Innovation and R&D Strategy...")
        strategic_intel["modules"]["innovation_strategy"] = await self._analyze_innovation_strategy(company_name)
        
        # Module 5.5: Competitive Positioning
        print("\n🏆 Module 5.5: Analyzing Competitive Positioning...")
        strategic_intel["modules"]["competitive_positioning"] = await self._analyze_competitive_positioning(company_name)
        
        print("\n" + "="*80)
        print("✅ STRATEGIC INTELLIGENCE GATHERING COMPLETED")
        print("="*80 + "\n")
        
        return strategic_intel
    
    async def _identify_strategic_priorities(self, company_name: str) -> Dict[str, Any]:
        """Identify company's strategic priorities"""
        prompt = f"""
Identify the strategic priorities for {company_name}.

REQUIRED INFORMATION:
1. TOP STRATEGIC PRIORITIES (from executive communications):
   - Priority 1, 2, 3, etc.
   - When announced
   - Progress indicators

2. STRATEGIC INITIATIVES:
   - Major initiatives underway
   - Investment areas
   - Focus areas

3. STRATEGIC GOALS:
   - Short-term goals (1-2 years)
   - Long-term goals (3-5 years)
   - Metrics they're tracking

Provide specific examples, quotes, and sources from earnings calls, CEO letters, press releases.
"""
        
        response = await self._query_perplexity(prompt)
        return {
            "raw_data": response.get("content", ""),
            "sources": response.get("sources", [])
        }
    
    async def _analyze_digital_transformation(self, company_name: str) -> Dict[str, Any]:
        """Analyze digital transformation initiatives"""
        prompt = f"""
Analyze digital transformation initiatives at {company_name}.

REQUIRED INFORMATION:
1. DIGITAL TRANSFORMATION PROGRAMS:
   - Announced digital transformation initiatives
   - Technology modernization efforts
   - Cloud migration status
   - Data and analytics investments
   - AI/ML adoption

2. TECHNOLOGY INVESTMENTS:
   - Areas of technology investment
   - Partnerships with tech companies
   - Technology platform choices

3. DIGITAL CAPABILITIES:
   - Digital products or services
   - E-commerce capabilities
   - Mobile strategies
   - API ecosystems

Provide specific examples, timelines, and sources.
"""
        
        response = await self._query_perplexity(prompt)
        return {
            "raw_data": response.get("content", ""),
            "sources": response.get("sources", [])
        }
    
    async def _analyze_growth_strategy(self, company_name: str) -> Dict[str, Any]:
        """Analyze growth strategy"""
        prompt = f"""
Analyze the growth strategy for {company_name}.

REQUIRED INFORMATION:
1. GROWTH VECTORS:
   - Organic growth strategies
   - Inorganic growth (M&A)
   - Geographic expansion plans
   - Market expansion
   - Product expansion

2. EXPANSION PLANS:
   - New markets entering
   - New products launching
   - Capacity expansions
   - Store/location openings

3. MARKET SHARE GOALS:
   - Market share targets
   - Competitive positioning goals

Provide specific examples, dates, and sources.
"""
        
        response = await self._query_perplexity(prompt)
        return {
            "raw_data": response.get("content", ""),
            "sources": response.get("sources", [])
        }
    
    async def _analyze_innovation_strategy(self, company_name: str) -> Dict[str, Any]:
        """Analyze innovation and R&D strategy"""
        prompt = f"""
Analyze innovation and R&D strategy for {company_name}.

REQUIRED INFORMATION:
1. R&D FOCUS AREAS:
   - Key areas of R&D investment
   - Innovation priorities
   - Technology development

2. INNOVATION APPROACH:
   - Internal R&D
   - Partnerships and collaborations
   - Acquisitions for technology
   - Innovation labs or centers

3. PATENTS AND IP:
   - Recent patents filed
   - IP strategy
   - Technology breakthroughs

Provide specific examples and sources.
"""
        
        response = await self._query_perplexity(prompt)
        return {
            "raw_data": response.get("content", ""),
            "sources": response.get("sources", [])
        }
    
    async def _analyze_competitive_positioning(self, company_name: str) -> Dict[str, Any]:
        """Analyze competitive positioning strategy"""
        prompt = f"""
Analyze competitive positioning strategy for {company_name}.

REQUIRED INFORMATION:
1. MARKET POSITIONING:
   - How does {company_name} position itself?
   - Value proposition
   - Differentiation strategy

2. COMPETITIVE ADVANTAGES:
   - Stated competitive advantages
   - Defensibility of position
   - Moats or barriers to entry

3. GO-TO-MARKET STRATEGY:
   - Sales channels
   - Marketing approach
   - Customer acquisition strategy

Provide specific examples and sources.
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
                                {"role": "system", "content": "You are a strategic intelligence analyst."},
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
