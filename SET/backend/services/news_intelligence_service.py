"""
News and Media Intelligence System
Module 3 from Sales Enablement Tool (SET)

This module provides comprehensive news and media monitoring, tracking positive/negative news,
press releases, media coverage, sentiment trends, and industry news affecting target companies.
"""

import httpx
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum


class NewsSentiment(Enum):
    """News sentiment classification"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class ImpactLevel(Enum):
    """Impact level of news"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NewsIntelligenceService:
    """
    News and Media Intelligence System
    Comprehensive news monitoring and analysis including:
    - Positive and negative news tracking
    - Press release monitoring
    - Media coverage analysis
    - Sentiment trend tracking
    - Crisis and controversy detection
    - Industry news contextualization
    - News-driven sales opportunities
    """
    
    def __init__(self, perplexity_api_key: str):
        self.api_key = perplexity_api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def gather_news_intelligence(
        self,
        company_name: str,
        lookback_years: int = 7
    ) -> Dict[str, Any]:
        """
        Main orchestrator for news and media intelligence gathering
        
        Returns comprehensive news intelligence covering:
        - Recent news (last 90 days)
        - Historical news trends (7-10 years)
        - Positive news and achievements
        - Negative news and crises
        - Press releases and announcements
        - Media coverage analysis
        - Industry news context
        - News-driven opportunities
        """
        print("\n" + "="*80)
        print("📰 NEWS AND MEDIA INTELLIGENCE SYSTEM")
        print("="*80)
        print(f"📊 Target Company: {company_name}")
        print(f"📅 Lookback Period: {lookback_years} years")
        print("="*80 + "\n")
        
        news_intel = {
            "company_name": company_name,
            "lookback_years": lookback_years,
            "gathered_at": datetime.now().isoformat(),
            "modules": {}
        }
        
        # Module 3.1: Recent News (Last 90 days)
        print("📱 Module 3.1: Gathering Recent News (Last 90 days)...")
        news_intel["modules"]["recent_news"] = await self._gather_recent_news(
            company_name
        )
        
        # Module 3.2: Positive News and Achievements
        print("\n✅ Module 3.2: Gathering Positive News and Achievements...")
        news_intel["modules"]["positive_news"] = await self._gather_positive_news(
            company_name, lookback_years
        )
        
        # Module 3.3: Negative News and Crises
        print("\n❌ Module 3.3: Gathering Negative News and Crises...")
        news_intel["modules"]["negative_news"] = await self._gather_negative_news(
            company_name, lookback_years
        )
        
        # Module 3.4: Press Releases and Official Announcements
        print("\n📢 Module 3.4: Monitoring Press Releases...")
        news_intel["modules"]["press_releases"] = await self._monitor_press_releases(
            company_name
        )
        
        # Module 3.5: Media Coverage Analysis
        print("\n📺 Module 3.5: Analyzing Media Coverage...")
        news_intel["modules"]["media_coverage"] = await self._analyze_media_coverage(
            company_name
        )
        
        # Module 3.6: Industry News Context
        print("\n🏭 Module 3.6: Gathering Industry News Context...")
        news_intel["modules"]["industry_news"] = await self._gather_industry_news(
            company_name
        )
        
        # Module 3.7: Sentiment Trend Analysis
        print("\n📊 Module 3.7: Analyzing Sentiment Trends...")
        news_intel["modules"]["sentiment_trends"] = await self._analyze_sentiment_trends(
            company_name, lookback_years
        )
        
        # Module 3.8: News-Driven Sales Opportunities
        print("\n💼 Module 3.8: Identifying News-Driven Sales Opportunities...")
        news_intel["modules"]["sales_opportunities"] = self._identify_sales_opportunities(
            news_intel["modules"]
        )
        
        print("\n" + "="*80)
        print("✅ NEWS AND MEDIA INTELLIGENCE GATHERING COMPLETED")
        print("="*80 + "\n")
        
        return news_intel
    
    # =========================================================================
    # Module 3.1: Recent News (Last 90 Days)
    # =========================================================================
    
    async def _gather_recent_news(
        self,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Module 3.1: Recent News (Last 90 Days)
        
        Gathers:
        - Latest news stories
        - Breaking news
        - Recent announcements
        - Current events
        - Trending topics
        """
        prompt = f"""
Gather comprehensive recent news about {company_name} from the last 90 days.

REQUIRED INFORMATION:

1. RECENT NEWS STORIES (Last 90 days):
   For each significant news story, provide:
   - Date published
   - Headline
   - News source (publication name)
   - Brief summary (2-3 sentences)
   - Sentiment (positive, negative, or neutral)
   - Impact level (critical, high, medium, low)
   - URL/link to article
   - Key takeaways for sales conversations

2. BREAKING NEWS OR MAJOR DEVELOPMENTS:
   - Any breaking news in last 7 days
   - Major announcements
   - Significant events
   - Urgent developments

3. NEWS CATEGORIES:
   Organize news into categories:
   - Product/Service Launches
   - Financial Results and Announcements
   - Leadership Changes
   - Strategic Partnerships
   - Mergers and Acquisitions
   - Legal/Regulatory News
   - Operational Updates
   - Customer Wins/Losses
   - Awards and Recognition
   - Controversies or Challenges

4. TRENDING TOPICS:
   - What topics are getting most media attention
   - Viral stories or social media trends
   - Hashtags associated with the company

5. MEDIA TONE:
   - Overall media tone (positive, neutral, negative)
   - Sentiment shift in recent weeks
   - Reasons for sentiment changes

Prioritize the most recent and most significant news. Include specific dates, sources, and URLs.
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "news_stories": self._extract_news_stories(response.get("content", "")),
            "breaking_news": self._extract_breaking_news(response.get("content", "")),
            "news_by_category": self._categorize_news(response.get("content", "")),
            "trending_topics": self._extract_trending_topics(response.get("content", "")),
            "overall_tone": self._assess_media_tone(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 3.2: Positive News and Achievements
    # =========================================================================
    
    async def _gather_positive_news(
        self,
        company_name: str,
        lookback_years: int = 7
    ) -> Dict[str, Any]:
        """
        Module 3.2: Positive News and Achievements
        
        Tracks:
        - Awards and recognition
        - Product launches
        - Partnership announcements
        - Expansion news
        - Growth milestones
        - Customer wins
        - Innovation highlights
        """
        prompt = f"""
Research positive news, achievements, and milestones for {company_name} over the last {lookback_years} years.

REQUIRED INFORMATION:

1. AWARDS AND RECOGNITION:
   - Industry awards received
   - "Best of" lists or rankings
   - Certifications achieved
   - Recognition from analysts or research firms
   - For each: Date, award name, awarding organization, significance

2. PRODUCT AND SERVICE LAUNCHES:
   - Major product launches
   - New service offerings
   - Product innovation highlights
   - Customer reception and reviews
   - Market impact

3. STRATEGIC PARTNERSHIPS:
   - Major partnership announcements
   - Strategic alliances
   - Technology partnerships
   - Distribution partnerships
   - Joint ventures

4. BUSINESS EXPANSION:
   - New market entries (geographic or vertical)
   - Office openings
   - Manufacturing facility expansions
   - Acquisition of companies (as growth indicator)
   - International expansion

5. GROWTH MILESTONES:
   - Revenue milestones (e.g., crossing $100M, $1B)
   - Customer milestones (e.g., 1 million users)
   - Valuation milestones
   - IPO or funding announcements
   - Profitability achievements

6. CUSTOMER WINS:
   - Major customer announcements
   - Enterprise customer wins
   - Contract wins and renewals
   - Customer testimonials or case studies
   - Reference customers

7. INNOVATION AND R&D:
   - Patents granted
   - Technology breakthroughs
   - R&D initiatives announced
   - Innovation labs or centers established
   - Thought leadership recognition

8. ESG AND CORPORATE CITIZENSHIP:
   - Sustainability initiatives
   - Community involvement
   - Diversity and inclusion achievements
   - Corporate social responsibility highlights
   - Environmental commitments

For each positive news item, include:
- Date
- Headline/summary
- Source
- Business impact
- Sales conversation angle

Organize chronologically within each category.
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "awards_recognition": self._extract_awards(response.get("content", "")),
            "product_launches": self._extract_product_launches(response.get("content", "")),
            "partnerships": self._extract_partnerships(response.get("content", "")),
            "expansion_news": self._extract_expansion_news(response.get("content", "")),
            "growth_milestones": self._extract_growth_milestones(response.get("content", "")),
            "customer_wins": self._extract_customer_wins(response.get("content", "")),
            "innovation": self._extract_innovation_news(response.get("content", "")),
            "esg_initiatives": self._extract_esg_news(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 3.3: Negative News and Crises
    # =========================================================================
    
    async def _gather_negative_news(
        self,
        company_name: str,
        lookback_years: int = 7
    ) -> Dict[str, Any]:
        """
        Module 3.3: Negative News and Crises
        
        Tracks:
        - Legal issues and lawsuits
        - Regulatory penalties
        - Data breaches and security incidents
        - Product recalls
        - Executive scandals
        - Financial losses
        - Layoffs and downsizing
        - Customer losses
        - Controversies and backlash
        """
        prompt = f"""
Research negative news, challenges, and crises for {company_name} over the last {lookback_years} years.

REQUIRED INFORMATION:

1. LEGAL ISSUES AND LAWSUITS:
   - Lawsuits filed (as plaintiff or defendant)
   - Legal settlements
   - Class action lawsuits
   - Intellectual property disputes
   - Contract disputes
   - For each: Date, parties involved, issue, status, financial impact

2. REGULATORY PENALTIES AND VIOLATIONS:
   - Fines imposed by regulators
   - Regulatory violations
   - Consent decrees
   - Warning letters
   - Regulatory investigations

3. CYBERSECURITY AND DATA INCIDENTS:
   - Data breaches
   - Cybersecurity incidents
   - Customer data exposure
   - Security vulnerabilities disclosed
   - Response and remediation

4. PRODUCT ISSUES AND RECALLS:
   - Product recalls
   - Safety issues
   - Quality problems
   - Performance failures
   - Customer complaints

5. FINANCIAL SETBACKS:
   - Missed earnings expectations
   - Revenue warnings or guidance reductions
   - Write-downs or impairments
   - Debt defaults or covenant violations
   - Credit rating downgrades

6. WORKFORCE ISSUES:
   - Layoffs and workforce reductions
   - Executive departures or firings
   - Labor disputes or strikes
   - Discrimination or harassment allegations
   - Toxic culture reports

7. CUSTOMER AND MARKET SETBACKS:
   - Major customer losses
   - Contract cancellations
   - Market share losses
   - Competitive losses
   - Failed product launches

8. REPUTATION CRISES:
   - PR crises
   - Social media backlash
   - Boycott campaigns
   - Executive scandals
   - Ethical controversies

9. OPERATIONAL FAILURES:
   - Production outages or failures
   - Supply chain crises
   - Service outages
   - Operational incidents

For each negative news item, include:
- Date
- Headline/summary
- Source
- Severity (critical, high, medium, low)
- Business impact
- Company's response
- Current status (ongoing, resolved, etc.)
- Lessons learned or changes made
- How to address in sales conversations (if applicable)

IMPORTANT: For sales enablement purposes, also note:
- Whether the issue creates a solution opportunity
- How to empathetically address if it comes up
- Competitive context (did others have similar issues?)
"""
        
        response = await self._query_perplexity(prompt)
        
        # Classify severity of negative news
        overall_severity = self._assess_negative_news_severity(response.get("content", ""))
        
        return {
            "raw_data": response.get("content", ""),
            "overall_severity": overall_severity,
            "legal_issues": self._extract_legal_issues(response.get("content", "")),
            "regulatory_penalties": self._extract_regulatory_penalties(response.get("content", "")),
            "cybersecurity_incidents": self._extract_cyber_incidents(response.get("content", "")),
            "product_issues": self._extract_product_issues(response.get("content", "")),
            "financial_setbacks": self._extract_financial_setbacks(response.get("content", "")),
            "workforce_issues": self._extract_workforce_issues(response.get("content", "")),
            "customer_setbacks": self._extract_customer_setbacks(response.get("content", "")),
            "reputation_crises": self._extract_reputation_crises(response.get("content", "")),
            "operational_failures": self._extract_operational_failures(response.get("content", "")),
            "sales_guidance": self._extract_negative_news_sales_guidance(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 3.4: Press Releases and Official Announcements
    # =========================================================================
    
    async def _monitor_press_releases(
        self,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Module 3.4: Press Releases and Official Announcements
        
        Monitors:
        - Company press releases
        - Earnings announcements
        - Executive statements
        - Official communications
        """
        prompt = f"""
Gather recent press releases and official announcements from {company_name}.

REQUIRED INFORMATION:

1. RECENT PRESS RELEASES (Last 6 months):
   - Date of release
   - Headline
   - Category (financial, product, partnership, leadership, etc.)
   - Key points from the release
   - Quotes from executives
   - Link to full release

2. EARNINGS ANNOUNCEMENTS:
   - Recent earnings release dates
   - Key financial highlights announced
   - Management commentary
   - Forward guidance provided
   - Analyst call highlights

3. EXECUTIVE STATEMENTS:
   - CEO statements or letters
   - CFO commentary
   - Other executive communications
   - Strategic vision statements

4. OFFICIAL COMPANY BLOG POSTS:
   - Recent company blog posts
   - Thought leadership content
   - Technical announcements
   - Company culture posts

5. INVESTOR RELATIONS COMMUNICATIONS:
   - Investor presentations
   - Shareholder letters
   - Proxy statements (if recent)
   - IR events announced

6. REGULATORY FILINGS (if public):
   - Recent 10-K, 10-Q filings
   - 8-K material events
   - Key disclosures or risk factors highlighted

Provide dates, summaries, and links for all items.
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "press_releases": self._extract_press_releases(response.get("content", "")),
            "earnings_announcements": self._extract_earnings_announcements(response.get("content", "")),
            "executive_statements": self._extract_executive_statements(response.get("content", "")),
            "company_blog": self._extract_blog_posts(response.get("content", "")),
            "investor_relations": self._extract_ir_communications(response.get("content", "")),
            "regulatory_filings": self._extract_filings(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 3.5: Media Coverage Analysis
    # =========================================================================
    
    async def _analyze_media_coverage(
        self,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Module 3.5: Media Coverage Analysis
        
        Analyzes:
        - Volume of media coverage
        - Media outlets covering the company
        - Share of voice vs. competitors
        - Media sentiment trends
        - Key journalists covering the company
        """
        prompt = f"""
Analyze media coverage patterns for {company_name}.

REQUIRED ANALYSIS:

1. MEDIA COVERAGE VOLUME:
   - Estimated number of articles/mentions (last quarter)
   - Trend in coverage volume (increasing, stable, decreasing)
   - Peak coverage periods and reasons
   - Coverage gaps or quiet periods

2. MEDIA OUTLETS:
   - Major publications frequently covering the company:
     * Tier 1 publications (WSJ, NYT, Bloomberg, etc.)
     * Industry trade publications
     * Business media (Forbes, Fortune, Fast Company, etc.)
     * Tech media (if applicable)
     * Local/regional media
   - Most frequent coverage source
   - Coverage tone by outlet

3. SHARE OF VOICE:
   - How frequently {company_name} is mentioned vs. top competitors
   - Media attention comparison to industry leaders
   - Relative visibility in media

4. MEDIA SENTIMENT BY OUTLET:
   - Which outlets provide positive coverage
   - Which outlets provide critical coverage
   - Neutral or balanced outlets
   - Sentiment trends over time

5. KEY JOURNALISTS AND REPORTERS:
   - Journalists who regularly cover the company
   - Beats they cover (financial, tech, industry-specific)
   - Recent articles by these journalists
   - Their typical angle or perspective

6. COVERAGE TRIGGERS:
   - What events generate media coverage
   - Proactive vs. reactive media coverage
   - Press release pickup rate

7. MEDIA RELATIONS EFFECTIVENESS:
   - Quality of media coverage (depth, accuracy)
   - Executive media visibility
   - Thought leadership placements

Provide specific outlet names, journalist names, article counts, and examples.
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "coverage_volume": self._extract_coverage_volume(response.get("content", "")),
            "media_outlets": self._extract_media_outlets(response.get("content", "")),
            "share_of_voice": self._extract_share_of_voice(response.get("content", "")),
            "sentiment_by_outlet": self._extract_sentiment_by_outlet(response.get("content", "")),
            "key_journalists": self._extract_key_journalists(response.get("content", "")),
            "coverage_triggers": self._extract_coverage_triggers(response.get("content", "")),
            "media_relations": self._extract_media_relations_analysis(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 3.6: Industry News Context
    # =========================================================================
    
    async def _gather_industry_news(
        self,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Module 3.6: Industry News Context
        
        Gathers:
        - Industry trends affecting the company
        - Competitor news
        - Regulatory changes
        - Technology shifts
        - Market dynamics
        """
        prompt = f"""
Gather industry news and context relevant to {company_name}.

REQUIRED INFORMATION:

1. INDUSTRY TRENDS:
   - Major trends affecting the industry
   - Technology shifts impacting the sector
   - Market dynamics and changes
   - Growth or decline in the industry
   - Emerging opportunities and threats

2. COMPETITOR NEWS:
   - Recent news about major competitors
   - Competitive announcements affecting {company_name}
   - Market share shifts
   - Competitor innovations or setbacks
   - Competitive landscape changes

3. REGULATORY AND POLICY CHANGES:
   - New regulations affecting the industry
   - Policy changes impacting operations
   - Government initiatives or programs
   - Compliance requirement changes
   - Industry-wide regulatory events

4. M&A ACTIVITY IN THE INDUSTRY:
   - Recent mergers and acquisitions
   - Industry consolidation trends
   - Valuation trends
   - Strategic rationales

5. INVESTMENT AND FUNDING TRENDS:
   - Venture capital activity in the sector
   - IPO activity
   - Valuation multiples
   - Investor sentiment

6. TECHNOLOGY AND INNOVATION:
   - Emerging technologies in the industry
   - R&D trends
   - Patents and intellectual property
   - Innovation leaders

7. MARKET DYNAMICS:
   - Supply and demand trends
   - Pricing trends
   - Customer behavior changes
   - Economic factors affecting the industry

How does each trend affect {company_name} specifically?
What opportunities or threats do these create?
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "industry_trends": self._extract_industry_trends(response.get("content", "")),
            "competitor_news": self._extract_competitor_news(response.get("content", "")),
            "regulatory_changes": self._extract_regulatory_changes(response.get("content", "")),
            "ma_activity": self._extract_industry_ma(response.get("content", "")),
            "investment_trends": self._extract_investment_trends(response.get("content", "")),
            "technology_shifts": self._extract_technology_shifts(response.get("content", "")),
            "market_dynamics": self._extract_market_dynamics(response.get("content", "")),
            "impact_on_company": self._extract_industry_impact(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 3.7: Sentiment Trend Analysis
    # =========================================================================
    
    async def _analyze_sentiment_trends(
        self,
        company_name: str,
        lookback_years: int = 7
    ) -> Dict[str, Any]:
        """
        Module 3.7: Sentiment Trend Analysis
        
        Analyzes:
        - Sentiment over time
        - Sentiment inflection points
        - Drivers of sentiment changes
        - Current sentiment trajectory
        """
        prompt = f"""
Analyze sentiment trends for {company_name} over the last {lookback_years} years.

REQUIRED ANALYSIS:

1. OVERALL SENTIMENT TRAJECTORY:
   - Current sentiment (positive, neutral, or negative)
   - Sentiment 1 year ago
   - Sentiment 3 years ago
   - Sentiment 5 years ago
   - Overall trend (improving, stable, declining)

2. SENTIMENT INFLECTION POINTS:
   - Key events that changed sentiment positively
   - Key events that changed sentiment negatively
   - Dates and descriptions of these events
   - Magnitude of sentiment impact

3. SENTIMENT DRIVERS:
   Current positive sentiment drivers:
   - What's contributing to positive perception
   
   Current negative sentiment drivers:
   - What's contributing to negative perception
   
   Neutral factors:
   - Areas where sentiment is balanced

4. SENTIMENT BY STAKEHOLDER GROUP:
   - Customer sentiment
   - Investor sentiment
   - Employee sentiment (if available)
   - Media/analyst sentiment
   - Public/community sentiment

5. SENTIMENT RECOVERY (if applicable):
   - If there was negative sentiment, has it recovered?
   - How long did recovery take?
   - What actions drove recovery?

6. SENTIMENT FORECAST:
   - Expected sentiment direction (next 6-12 months)
   - Factors that could improve sentiment
   - Risks that could hurt sentiment

Provide specific examples, dates, and data to support sentiment assessments.
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "sentiment_trajectory": self._extract_sentiment_trajectory(response.get("content", "")),
            "inflection_points": self._extract_inflection_points(response.get("content", "")),
            "sentiment_drivers": self._extract_sentiment_drivers(response.get("content", "")),
            "sentiment_by_stakeholder": self._extract_stakeholder_sentiment(response.get("content", "")),
            "sentiment_recovery": self._extract_sentiment_recovery(response.get("content", "")),
            "sentiment_forecast": self._extract_sentiment_forecast(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 3.8: News-Driven Sales Opportunities
    # =========================================================================
    
    def _identify_sales_opportunities(
        self,
        modules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Module 3.8: News-Driven Sales Opportunities
        
        Identifies:
        - Sales conversation hooks from news
        - Problem areas that solutions can address
        - Positive momentum to leverage
        - Timing opportunities
        """
        opportunities = {
            "conversation_hooks": [],
            "problem_areas": [],
            "positive_momentum": [],
            "timing_opportunities": [],
            "caution_areas": []
        }
        
        # Analyze recent news for opportunities
        recent_news = modules.get("recent_news", {})
        positive_news = modules.get("positive_news", {})
        negative_news = modules.get("negative_news", {})
        
        # Extract opportunities from positive news
        if positive_news:
            opportunities["positive_momentum"] = [
                "Company recently launched new products - good time to discuss complementary solutions",
                "Recent partnerships announced - potential for ecosystem integrations",
                "Growth milestones achieved - indicative of budget availability",
                "Awards received - acknowledge achievements to build rapport"
            ]
        
        # Extract opportunities from negative news/challenges
        if negative_news:
            opportunities["problem_areas"] = [
                "Operational challenges mentioned - position solutions for operational excellence",
                "Security incidents reported - opportunity for security solutions",
                "Cost reduction initiatives - emphasize ROI and efficiency gains",
                "Customer satisfaction issues - position customer experience solutions"
            ]
        
        # Timing opportunities
        opportunities["timing_opportunities"] = [
            "Recent executive changes - new decision makers, potential for fresh vendor evaluation",
            "Fiscal year timing - budget cycles and purchasing windows",
            "Industry events coming up - networking opportunities",
            "Earnings/reporting periods - avoid during blackout periods"
        ]
        
        # Caution areas
        opportunities["caution_areas"] = [
            "Recent layoffs - budget constraints likely, adjust messaging",
            "Ongoing legal issues - be sensitive in conversations",
            "Negative media coverage - acknowledge if raised, don't dwell on it"
        ]
        
        return opportunities
    
    # =========================================================================
    # Helper Methods: API Communication
    # =========================================================================
    
    async def _query_perplexity(self, prompt: str) -> Dict[str, Any]:
        """Query Perplexity API with the given prompt"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            models_to_try = ["sonar", "sonar-pro", "llama-3.1-sonar-large-128k-online"]
            
            for model in models_to_try:
                try:
                    response = await client.post(
                        self.base_url,
                        headers=self.headers,
                        json={
                            "model": model,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are a news and media intelligence analyst. Provide comprehensive, factual news analysis with specific dates, sources, and citations."
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
                        result = response.json()
                        return {
                            "content": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                            "sources": result.get("citations", []),
                            "model_used": model
                        }
                except Exception:
                    continue
            
            return {"content": "", "sources": [], "model_used": None}
    
    # =========================================================================
    # Helper Methods: Data Extraction (Stubs - implementations would parse content)
    # =========================================================================
    
    def _extract_news_stories(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_breaking_news(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _categorize_news(self, content: str) -> Dict[str, List[Dict[str, Any]]]:
        return {}
    
    def _extract_trending_topics(self, content: str) -> List[str]:
        return []
    
    def _assess_media_tone(self, content: str) -> str:
        content_lower = content.lower()
        positive_count = sum(content_lower.count(word) for word in ["positive", "success", "growth", "innovation"])
        negative_count = sum(content_lower.count(word) for word in ["negative", "crisis", "decline", "challenge"])
        
        if positive_count > negative_count * 1.5:
            return "predominantly_positive"
        elif negative_count > positive_count * 1.5:
            return "predominantly_negative"
        return "mixed_neutral"
    
    def _extract_awards(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_product_launches(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_partnerships(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_expansion_news(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_growth_milestones(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_customer_wins(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_innovation_news(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_esg_news(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _assess_negative_news_severity(self, content: str) -> str:
        content_lower = content.lower()
        critical_terms = ["bankruptcy", "fraud", "criminal", "class action", "data breach affecting millions"]
        high_terms = ["lawsuit", "fine", "violation", "recall", "investigation"]
        
        if any(term in content_lower for term in critical_terms):
            return "critical"
        elif any(term in content_lower for term in high_terms):
            return "high"
        return "moderate"
    
    def _extract_legal_issues(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_regulatory_penalties(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_cyber_incidents(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_product_issues(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_financial_setbacks(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_workforce_issues(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_customer_setbacks(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_reputation_crises(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_operational_failures(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_negative_news_sales_guidance(self, content: str) -> Dict[str, List[str]]:
        return {"dos": [], "donts": []}
    
    def _extract_press_releases(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_earnings_announcements(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_executive_statements(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_blog_posts(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_ir_communications(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_filings(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_coverage_volume(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_media_outlets(self, content: str) -> List[Dict[str, str]]:
        return []
    
    def _extract_share_of_voice(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_sentiment_by_outlet(self, content: str) -> Dict[str, str]:
        return {}
    
    def _extract_key_journalists(self, content: str) -> List[Dict[str, str]]:
        return []
    
    def _extract_coverage_triggers(self, content: str) -> List[str]:
        return []
    
    def _extract_media_relations_analysis(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_industry_trends(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_competitor_news(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_regulatory_changes(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_industry_ma(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_investment_trends(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_technology_shifts(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_market_dynamics(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_industry_impact(self, content: str) -> Dict[str, List[str]]:
        return {"opportunities": [], "threats": []}
    
    def _extract_sentiment_trajectory(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_inflection_points(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_sentiment_drivers(self, content: str) -> Dict[str, List[str]]:
        return {"positive": [], "negative": [], "neutral": []}
    
    def _extract_stakeholder_sentiment(self, content: str) -> Dict[str, str]:
        return {}
    
    def _extract_sentiment_recovery(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_sentiment_forecast(self, content: str) -> Dict[str, Any]:
        return {}
