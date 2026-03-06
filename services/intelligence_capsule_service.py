"""
Intelligence Capsule Service
Main orchestrator for the Sales Enablement Tool (SET)

This service integrates all intelligence modules to create comprehensive
sales enablement intelligence capsules.
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from .company_intelligence_service import CompanyIntelligenceService
from .financial_intelligence_service import FinancialIntelligenceService
from .news_intelligence_service import NewsIntelligenceService
from .leadership_profiling_service import LeadershipProfilingService


class IntelligenceCapsuleService:
    """
    Main Intelligence Capsule Orchestrator
    
    Integrates all intelligence modules to create comprehensive
    sales enablement capsules for organizations and individuals.
    """
    
    def __init__(self, perplexity_api_key: str):
        # Initialize all intelligence services
        self.company_intel_service = CompanyIntelligenceService(perplexity_api_key)
        self.financial_intel_service = FinancialIntelligenceService(perplexity_api_key)
        self.news_intel_service = NewsIntelligenceService(perplexity_api_key)
        self.leadership_intel_service = LeadershipProfilingService(perplexity_api_key)
    
    async def generate_organization_capsule(
        self,
        company_name: str,
        industry: Optional[str] = None,
        website: Optional[str] = None,
        is_public: Optional[bool] = None,
        ticker_symbol: Optional[str] = None,
        modules_to_include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive organization intelligence capsule
        
        Args:
            company_name: Name of the target organization
            industry: Industry sector (optional, will auto-detect)
            website: Company website (optional, will search)
            is_public: Whether company is publicly traded
            ticker_symbol: Stock ticker symbol (for public companies)
            modules_to_include: List of module IDs to include (default: all)
        
        Returns:
            Comprehensive intelligence capsule with all gathered intelligence
        """
        print("\n" + "="*80)
        print("🎯 GENERATING ORGANIZATION INTELLIGENCE CAPSULE")
        print("="*80)
        print(f"📊 Company: {company_name}")
        print(f"🏭 Industry: {industry or 'Auto-detect'}")
        print(f"🌐 Website: {website or 'Will search'}")
        print(f"📈 Public: {is_public if is_public is not None else 'Auto-detect'}")
        print(f"🎫 Ticker: {ticker_symbol or 'N/A'}")
        print("="*80 + "\n")
        
        # Determine which modules to include
        if modules_to_include is None:
            modules_to_include = [
                "company_intelligence",
                "financial_intelligence",
                "news_intelligence",
                "leadership_intelligence"
            ]
        
        capsule = {
            "capsule_type": "organization",
            "company_name": company_name,
            "industry": industry,
            "website": website,
            "is_public": is_public,
            "ticker_symbol": ticker_symbol,
            "generated_at": datetime.now().isoformat(),
            "intelligence": {}
        }
        
        # Module 1: Company Intelligence Discovery
        if "company_intelligence" in modules_to_include:
            print("🏢 Gathering Company Intelligence...")
            try:
                capsule["intelligence"]["company_intelligence"] = await self.company_intel_service.gather_comprehensive_intelligence(
                    company_name=company_name,
                    industry=industry,
                    website=website
                )
                print("✅ Company Intelligence gathered successfully\n")
            except Exception as e:
                print(f"❌ Error gathering company intelligence: {e}\n")
                capsule["intelligence"]["company_intelligence"] = {"error": str(e)}
        
        # Module 2: Financial Intelligence
        if "financial_intelligence" in modules_to_include:
            print("💰 Gathering Financial Intelligence...")
            try:
                capsule["intelligence"]["financial_intelligence"] = await self.financial_intel_service.gather_financial_intelligence(
                    company_name=company_name,
                    is_public=is_public,
                    ticker_symbol=ticker_symbol
                )
                print("✅ Financial Intelligence gathered successfully\n")
            except Exception as e:
                print(f"❌ Error gathering financial intelligence: {e}\n")
                capsule["intelligence"]["financial_intelligence"] = {"error": str(e)}
        
        # Module 3: News and Media Intelligence
        if "news_intelligence" in modules_to_include:
            print("📰 Gathering News Intelligence...")
            try:
                capsule["intelligence"]["news_intelligence"] = await self.news_intel_service.gather_news_intelligence(
                    company_name=company_name,
                    lookback_years=7
                )
                print("✅ News Intelligence gathered successfully\n")
            except Exception as e:
                print(f"❌ Error gathering news intelligence: {e}\n")
                capsule["intelligence"]["news_intelligence"] = {"error": str(e)}
        
        # Module 4: Leadership Intelligence
        if "leadership_intelligence" in modules_to_include:
            print("👔 Gathering Leadership Intelligence...")
            try:
                capsule["intelligence"]["leadership_intelligence"] = await self.leadership_intel_service.gather_leadership_intelligence(
                    company_name=company_name
                )
                print("✅ Leadership Intelligence gathered successfully\n")
            except Exception as e:
                print(f"❌ Error gathering leadership intelligence: {e}\n")
                capsule["intelligence"]["leadership_intelligence"] = {"error": str(e)}
        
        # Generate Sales Talking Points
        print("💼 Generating Sales Talking Points...")
        capsule["sales_talking_points"] = self._generate_sales_talking_points(capsule["intelligence"])
        print("✅ Sales Talking Points generated\n")
        
        # Generate Executive Summary
        print("📋 Generating Executive Summary...")
        capsule["executive_summary"] = self._generate_executive_summary(capsule["intelligence"])
        print("✅ Executive Summary generated\n")
        
        print("="*80)
        print("✅ ORGANIZATION INTELLIGENCE CAPSULE COMPLETED")
        print("="*80 + "\n")
        
        return capsule
    
    async def generate_individual_capsule(
        self,
        person_name: str,
        company_name: Optional[str] = None,
        title: Optional[str] = None,
        linkedin_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive individual intelligence capsule
        
        Args:
            person_name: Name of the individual
            company_name: Current company (if known)
            title: Current title (if known)
            linkedin_url: LinkedIn profile URL
        
        Returns:
            Comprehensive intelligence capsule for the individual
        """
        print("\n" + "="*80)
        print("🎯 GENERATING INDIVIDUAL INTELLIGENCE CAPSULE")
        print("="*80)
        print(f"👤 Person: {person_name}")
        print(f"🏢 Company: {company_name or 'Will search'}")
        print(f"💼 Title: {title or 'Will search'}")
        print(f"🔗 LinkedIn: {linkedin_url or 'Will search'}")
        print("="*80 + "\n")
        
        capsule = {
            "capsule_type": "individual",
            "person_name": person_name,
            "company_name": company_name,
            "title": title,
            "linkedin_url": linkedin_url,
            "generated_at": datetime.now().isoformat(),
            "intelligence": {}
        }
        
        # If company is known, get company context
        if company_name:
            print(f"📊 Gathering company context for {company_name}...")
            try:
                # Get lightweight company intelligence
                capsule["intelligence"]["company_context"] = await self.company_intel_service._gather_company_profile(
                    company_name=company_name
                )
                print("✅ Company context gathered\n")
            except Exception as e:
                print(f"⚠️  Could not gather company context: {e}\n")
        
        # Individual profile (using existing perplexity_service logic)
        # This would integrate with the existing individual research in perplexity_service.py
        capsule["intelligence"]["individual_profile"] = {
            "note": "Individual profiling uses existing perplexity_service.py logic",
            "person_name": person_name,
            "company_name": company_name,
            "title": title
        }
        
        print("="*80)
        print("✅ INDIVIDUAL INTELLIGENCE CAPSULE COMPLETED")
        print("="*80 + "\n")
        
        return capsule
    
    def _generate_sales_talking_points(
        self,
        intelligence: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Generate actionable sales talking points from intelligence
        
        Returns:
            Dictionary with categorized talking points
        """
        talking_points = {
            "conversation_starters": [],
            "challenges_to_address": [],
            "positive_momentum": [],
            "timing_opportunities": [],
            "caution_areas": [],
            "value_propositions": []
        }
        
        # Extract from company intelligence
        company_intel = intelligence.get("company_intelligence", {})
        if company_intel and not company_intel.get("error"):
            modules = company_intel.get("modules", {})
            
            # From regulatory intelligence
            regulatory = modules.get("regulatory_intelligence", {})
            if regulatory and regulatory.get("compliance_challenges"):
                talking_points["challenges_to_address"].append(
                    "Compliance challenges present opportunity for governance solutions"
                )
            
            # From workforce intelligence
            workforce = modules.get("workforce_intelligence", {})
            if workforce and workforce.get("layoffs"):
                talking_points["challenges_to_address"].append(
                    "Recent workforce reductions suggest need for automation and efficiency tools"
                )
            
            # From operational disruptions
            disruptions = modules.get("operational_disruptions", {})
            if disruptions and disruptions.get("cybersecurity_incidents"):
                talking_points["challenges_to_address"].append(
                    "Security incidents indicate opportunity for cybersecurity solutions"
                )
        
        # Extract from financial intelligence
        financial_intel = intelligence.get("financial_intelligence", {})
        if financial_intel and not financial_intel.get("error"):
            modules = financial_intel.get("modules", {})
            
            # From stress signals
            stress = modules.get("stress_signals", {})
            if stress:
                stress_level = stress.get("stress_level", "NONE")
                if stress_level in ["HIGH", "CRITICAL"]:
                    talking_points["caution_areas"].append(
                        "Financial stress detected - emphasize ROI and cost savings"
                    )
                    talking_points["value_propositions"].append(
                        "Focus on efficiency gains and rapid payback period"
                    )
            
            # From revenue analysis
            revenue = modules.get("revenue_analysis", {})
            if revenue and revenue.get("growth_metrics"):
                talking_points["positive_momentum"].append(
                    "Company showing revenue growth - good time to discuss growth-enabling solutions"
                )
        
        # Extract from news intelligence
        news_intel = intelligence.get("news_intelligence", {})
        if news_intel and not news_intel.get("error"):
            modules = news_intel.get("modules", {})
            
            # From positive news
            positive_news = modules.get("positive_news", {})
            if positive_news:
                if positive_news.get("partnerships"):
                    talking_points["conversation_starters"].append(
                        "Recent partnerships show openness to new vendor relationships"
                    )
                if positive_news.get("product_launches"):
                    talking_points["positive_momentum"].append(
                        "Product launches indicate innovation focus and budget availability"
                    )
            
            # From negative news
            negative_news = modules.get("negative_news", {})
            if negative_news:
                severity = negative_news.get("overall_severity", "moderate")
                if severity in ["critical", "high"]:
                    talking_points["caution_areas"].append(
                        "Recent negative news - approach with empathy and solution focus"
                    )
        
        # Extract from leadership intelligence
        leadership_intel = intelligence.get("leadership_intelligence", {})
        if leadership_intel and not leadership_intel.get("error"):
            modules = leadership_intel.get("modules", {})
            
            # From turnover
            turnover = modules.get("leadership_turnover", {})
            if turnover:
                stability = turnover.get("stability_assessment", "unknown")
                if stability == "unstable":
                    talking_points["timing_opportunities"].append(
                        "New leadership presents opportunity for vendor re-evaluation"
                    )
            
            # From executive messages
            exec_messages = modules.get("executive_messages", {})
            if exec_messages and exec_messages.get("strategic_priorities"):
                talking_points["conversation_starters"].append(
                    "Align messaging with executive strategic priorities"
                )
        
        # Default talking points if none generated
        if not any(talking_points.values()):
            talking_points["conversation_starters"] = [
                "Research company's current strategic initiatives",
                "Identify pain points related to your solution",
                "Build rapport through industry insights"
            ]
            talking_points["value_propositions"] = [
                "Emphasize ROI and business value",
                "Highlight customer success stories",
                "Focus on long-term partnership approach"
            ]
        
        return talking_points
    
    def _generate_executive_summary(
        self,
        intelligence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate executive summary of intelligence gathered
        
        Returns:
            Executive summary with key highlights
        """
        summary = {
            "company_overview": "",
            "financial_health": "",
            "recent_news_sentiment": "",
            "leadership_stability": "",
            "key_opportunities": [],
            "key_risks": [],
            "recommended_approach": ""
        }
        
        # Company overview
        company_intel = intelligence.get("company_intelligence", {})
        if company_intel and not company_intel.get("error"):
            modules = company_intel.get("modules", {})
            profile = modules.get("company_profile", {})
            if profile:
                summary["company_overview"] = "Comprehensive company intelligence gathered"
        
        # Financial health
        financial_intel = intelligence.get("financial_intelligence", {})
        if financial_intel and not financial_intel.get("error"):
            modules = financial_intel.get("modules", {})
            health = modules.get("financial_health", {})
            if health:
                summary["financial_health"] = health.get("health_classification", "Assessment in progress")
        
        # News sentiment
        news_intel = intelligence.get("news_intelligence", {})
        if news_intel and not news_intel.get("error"):
            modules = news_intel.get("modules", {})
            recent = modules.get("recent_news", {})
            if recent:
                summary["recent_news_sentiment"] = recent.get("overall_tone", "Mixed sentiment")
        
        # Leadership stability
        leadership_intel = intelligence.get("leadership_intelligence", {})
        if leadership_intel and not leadership_intel.get("error"):
            modules = leadership_intel.get("modules", {})
            turnover = modules.get("leadership_turnover", {})
            if turnover:
                summary["leadership_stability"] = turnover.get("stability_assessment", "Stable")
        
        # Key opportunities and risks
        summary["key_opportunities"] = [
            "Analyze gathered intelligence to identify specific opportunities"
        ]
        summary["key_risks"] = [
            "Review intelligence for potential engagement risks"
        ]
        
        # Recommended approach
        summary["recommended_approach"] = "Multi-threaded engagement focusing on identified pain points and strategic priorities"
        
        return summary
    
    def export_capsule_summary(
        self,
        capsule: Dict[str, Any]
    ) -> str:
        """
        Export capsule as text summary for quick review
        
        Args:
            capsule: Intelligence capsule to summarize
        
        Returns:
            Text summary of the capsule
        """
        lines = []
        lines.append("="*80)
        lines.append("SALES ENABLEMENT INTELLIGENCE CAPSULE")
        lines.append("="*80)
        lines.append("")
        
        if capsule["capsule_type"] == "organization":
            lines.append(f"Company: {capsule['company_name']}")
            lines.append(f"Industry: {capsule.get('industry', 'N/A')}")
            lines.append(f"Generated: {capsule['generated_at']}")
            lines.append("")
            
            # Executive Summary
            exec_summary = capsule.get("executive_summary", {})
            if exec_summary:
                lines.append("EXECUTIVE SUMMARY:")
                lines.append("-" * 80)
                for key, value in exec_summary.items():
                    if isinstance(value, list):
                        lines.append(f"{key.replace('_', ' ').title()}:")
                        for item in value:
                            lines.append(f"  • {item}")
                    else:
                        lines.append(f"{key.replace('_', ' ').title()}: {value}")
                lines.append("")
            
            # Sales Talking Points
            talking_points = capsule.get("sales_talking_points", {})
            if talking_points:
                lines.append("SALES TALKING POINTS:")
                lines.append("-" * 80)
                for category, points in talking_points.items():
                    if points:
                        lines.append(f"\n{category.replace('_', ' ').title()}:")
                        for point in points:
                            lines.append(f"  • {point}")
                lines.append("")
        
        lines.append("="*80)
        lines.append("For detailed intelligence, refer to the complete capsule data.")
        lines.append("="*80)
        
        return "\n".join(lines)
