"""
Financial Intelligence System
Module 2 from Sales Enablement Tool (SET)

This module provides comprehensive financial intelligence gathering and analysis,
including revenue trends, profitability analysis, funding history, financial health indicators,
and investment patterns.
"""

import httpx
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum


class FinancialHealth(Enum):
    """Financial health classification"""
    STRONG = "strong"
    STABLE = "stable"
    CONCERNING = "concerning"
    DISTRESSED = "distressed"


class FinancialIntelligenceService:
    """
    Financial Intelligence System
    Provides deep financial analysis including:
    - Revenue and growth trends
    - Profitability analysis
    - Funding and investment history
    - Financial health indicators
    - Capital allocation patterns
    - Financial stress signals
    """
    
    def __init__(self, perplexity_api_key: str):
        self.api_key = perplexity_api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def gather_financial_intelligence(
        self,
        company_name: str,
        is_public: bool = None,
        ticker_symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main orchestrator for financial intelligence gathering
        
        Returns comprehensive financial intelligence covering:
        - Revenue trends and growth analysis
        - Profitability metrics
        - Funding history (for private companies)
        - Stock performance (for public companies)
        - Financial health indicators
        - Capital allocation patterns
        - Cash flow analysis
        - Debt and leverage metrics
        - Financial stress signals
        """
        print("\n" + "="*80)
        print("💰 FINANCIAL INTELLIGENCE SYSTEM")
        print("="*80)
        print(f"📊 Target Company: {company_name}")
        print(f"📈 Public Status: {is_public if is_public is not None else 'Auto-detect'}")
        print(f"🎫 Ticker Symbol: {ticker_symbol or 'N/A'}")
        print("="*80 + "\n")
        
        financial_intel = {
            "company_name": company_name,
            "is_public": is_public,
            "ticker_symbol": ticker_symbol,
            "gathered_at": datetime.now().isoformat(),
            "modules": {}
        }
        
        # Module 2.1: Revenue and Growth Analysis
        print("📈 Module 2.1: Analyzing Revenue and Growth Trends...")
        financial_intel["modules"]["revenue_analysis"] = await self._analyze_revenue_trends(
            company_name, ticker_symbol
        )
        
        # Module 2.2: Profitability Analysis
        print("\n💵 Module 2.2: Analyzing Profitability Metrics...")
        financial_intel["modules"]["profitability"] = await self._analyze_profitability(
            company_name, ticker_symbol
        )
        
        # Module 2.3: Funding and Investment History
        print("\n💼 Module 2.3: Gathering Funding and Investment History...")
        financial_intel["modules"]["funding_history"] = await self._gather_funding_history(
            company_name
        )
        
        # Module 2.4: Stock Performance (for public companies)
        if is_public or ticker_symbol:
            print("\n📊 Module 2.4: Analyzing Stock Performance...")
            financial_intel["modules"]["stock_performance"] = await self._analyze_stock_performance(
                company_name, ticker_symbol
            )
        
        # Module 2.5: Financial Health Assessment
        print("\n🏥 Module 2.5: Assessing Financial Health...")
        financial_intel["modules"]["financial_health"] = await self._assess_financial_health(
            company_name, ticker_symbol
        )
        
        # Module 2.6: Capital Allocation Patterns
        print("\n💎 Module 2.6: Analyzing Capital Allocation Patterns...")
        financial_intel["modules"]["capital_allocation"] = await self._analyze_capital_allocation(
            company_name
        )
        
        # Module 2.7: Financial Stress Signals
        print("\n⚠️ Module 2.7: Detecting Financial Stress Signals...")
        financial_intel["modules"]["stress_signals"] = await self._detect_stress_signals(
            company_name
        )
        
        # Module 2.8: Analyst Sentiment (for public companies)
        if is_public or ticker_symbol:
            print("\n👔 Module 2.8: Gathering Analyst Sentiment...")
            financial_intel["modules"]["analyst_sentiment"] = await self._gather_analyst_sentiment(
                company_name, ticker_symbol
            )
        
        print("\n" + "="*80)
        print("✅ FINANCIAL INTELLIGENCE GATHERING COMPLETED")
        print("="*80 + "\n")
        
        return financial_intel
    
    # =========================================================================
    # Module 2.1: Revenue and Growth Analysis
    # =========================================================================
    
    async def _analyze_revenue_trends(
        self,
        company_name: str,
        ticker_symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Module 2.1: Revenue and Growth Analysis
        
        Analyzes:
        - Historical revenue figures (last 5-10 years)
        - Quarter-over-quarter growth
        - Year-over-year growth
        - Revenue by segment/division
        - Geographic revenue breakdown
        - Revenue growth drivers
        - Revenue guidance and forecasts
        """
        ticker_info = f" (Ticker: {ticker_symbol})" if ticker_symbol else ""
        
        prompt = f"""
Conduct comprehensive revenue and growth analysis for {company_name}{ticker_info}.

REQUIRED ANALYSIS:

1. HISTORICAL REVENUE DATA (Last 10 years or since founding):
   - Annual revenue figures with specific years
   - Quarterly revenue for last 8 quarters (if public)
   - Revenue CAGR (Compound Annual Growth Rate)
   - Revenue milestones achieved

2. GROWTH TRENDS:
   - Year-over-year growth rates (percentage and absolute)
   - Quarter-over-quarter growth rates
   - Growth acceleration or deceleration
   - Periods of negative growth (if any)
   - Comparison to industry average growth rates

3. REVENUE BREAKDOWN:
   - Revenue by business segment/division
   - Revenue by product line
   - Geographic revenue distribution
   - Customer concentration (if disclosed)
   - Recurring vs. one-time revenue

4. GROWTH DRIVERS:
   - Key factors driving revenue growth
   - New products or services contributing to growth
   - Market expansion driving growth
   - Pricing changes impact
   - Mergers and acquisitions impact on revenue

5. REVENUE GUIDANCE:
   - Latest revenue guidance from management
   - Historical accuracy of guidance
   - Guidance revisions (upgrades or downgrades)
   - Management commentary on revenue outlook

6. REVENUE QUALITY:
   - Revenue recognition practices
   - Deferred revenue trends
   - Accounts receivable aging
   - Revenue concentration risks

Provide specific numbers, dates, percentages, and sources for all data.
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "historical_revenue": self._extract_historical_revenue(response.get("content", "")),
            "growth_metrics": self._extract_growth_metrics(response.get("content", "")),
            "revenue_breakdown": self._extract_revenue_breakdown(response.get("content", "")),
            "growth_drivers": self._extract_growth_drivers(response.get("content", "")),
            "guidance": self._extract_revenue_guidance(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 2.2: Profitability Analysis
    # =========================================================================
    
    async def _analyze_profitability(
        self,
        company_name: str,
        ticker_symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Module 2.2: Profitability Analysis
        
        Analyzes:
        - Gross profit margins
        - Operating margins
        - Net profit margins
        - EBITDA and adjusted EBITDA
        - Path to profitability (for unprofitable companies)
        - Profitability by segment
        """
        ticker_info = f" (Ticker: {ticker_symbol})" if ticker_symbol else ""
        
        prompt = f"""
Conduct comprehensive profitability analysis for {company_name}{ticker_info}.

REQUIRED ANALYSIS:

1. PROFIT MARGINS (Last 5 years):
   - Gross profit margins (% and trend)
   - Operating profit margins (% and trend)
   - Net profit margins (% and trend)
   - EBITDA margins
   - Adjusted EBITDA (if reported)

2. PROFITABILITY TRENDS:
   - Margin expansion or contraction
   - Factors driving margin changes
   - Cost structure evolution
   - Operating leverage
   - Economies of scale realization

3. PROFITABILITY BY SEGMENT:
   - Which business units are profitable
   - Which are loss-making
   - Segment margin trends
   - Investment vs. harvest segments

4. PATH TO PROFITABILITY (if not yet profitable):
   - Timeline to profitability stated by management
   - Key milestones on path to profitability
   - Unit economics improvement
   - Cost reduction initiatives
   - Revenue scale needed for profitability

5. COST STRUCTURE:
   - Cost of goods sold trends
   - Operating expense breakdown (R&D, S&M, G&A)
   - Operating expense as % of revenue
   - Cost optimization initiatives

6. PROFITABILITY DRIVERS:
   - Key factors improving or hurting profitability
   - Pricing power
   - Cost inflation impacts
   - Efficiency improvements

Provide specific percentages, dollar amounts, dates, and sources.
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "margin_analysis": self._extract_margin_analysis(response.get("content", "")),
            "profitability_trends": self._extract_profitability_trends(response.get("content", "")),
            "segment_profitability": self._extract_segment_profitability(response.get("content", "")),
            "path_to_profitability": self._extract_path_to_profitability(response.get("content", "")),
            "cost_structure": self._extract_cost_structure(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 2.3: Funding and Investment History
    # =========================================================================
    
    async def _gather_funding_history(
        self,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Module 2.3: Funding and Investment History
        
        Gathers:
        - All funding rounds (seed, series A, B, C, etc.)
        - Investors and lead investors
        - Valuation history
        - Total capital raised
        - IPO information (if applicable)
        - Strategic investors
        """
        prompt = f"""
Research comprehensive funding and investment history for {company_name}.

REQUIRED INFORMATION:

1. FUNDING ROUNDS (All historical rounds):
   For each round, provide:
   - Round type (Seed, Series A, B, C, etc., or IPO)
   - Date announced
   - Amount raised
   - Pre-money and post-money valuation (if disclosed)
   - Lead investor(s)
   - All participating investors
   - Use of proceeds stated

2. TOTAL CAPITAL RAISED:
   - Total equity funding raised
   - Total debt financing (if applicable)
   - Grants or government funding
   - Cumulative capital raised to date

3. INVESTOR PROFILE:
   - Notable venture capital firms invested
   - Strategic corporate investors
   - Angel investors or founders
   - Investor syndicate composition
   - Board seats held by investors

4. VALUATION HISTORY:
   - Valuation progression across rounds
   - Valuation multiples (revenue multiple, if calculable)
   - Up rounds vs. down rounds vs. flat rounds
   - Latest known valuation

5. IPO INFORMATION (if applicable):
   - IPO date
   - IPO price
   - Amount raised in IPO
   - Current market cap vs. IPO valuation
   - IPO underwriters
   - Lockup period details

6. M&A ACTIVITY:
   - Acquisitions made by the company
   - Acquisition prices (if disclosed)
   - Strategic rationale for acquisitions

7. SECONDARY MARKETS:
   - Secondary share sales (if private)
   - Tender offers
   - Employee liquidity events

Provide specific dates, amounts, investor names, and sources.
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "funding_rounds": self._extract_funding_rounds(response.get("content", "")),
            "total_capital": self._extract_total_capital(response.get("content", "")),
            "investors": self._extract_investors(response.get("content", "")),
            "valuation_history": self._extract_valuation_history(response.get("content", "")),
            "ipo_details": self._extract_ipo_details(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 2.4: Stock Performance Analysis
    # =========================================================================
    
    async def _analyze_stock_performance(
        self,
        company_name: str,
        ticker_symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Module 2.4: Stock Performance Analysis (Public Companies)
        
        Analyzes:
        - Current stock price and market cap
        - Historical price performance
        - Trading volume
        - 52-week high/low
        - Price volatility
        - Comparison to indices and peers
        """
        ticker_info = f" (Ticker: {ticker_symbol})" if ticker_symbol else ""
        
        prompt = f"""
Analyze stock performance for {company_name}{ticker_info}.

REQUIRED ANALYSIS:

1. CURRENT STOCK METRICS:
   - Current stock price
   - Current market capitalization
   - 52-week high and low
   - Average daily trading volume
   - Shares outstanding
   - Float (shares available for trading)

2. HISTORICAL PRICE PERFORMANCE:
   - Price performance last 1 month (%)
   - Price performance last 3 months (%)
   - Price performance last 6 months (%)
   - Price performance last 1 year (%)
   - Price performance last 5 years (%)
   - All-time high and low since IPO

3. VOLATILITY ANALYSIS:
   - Beta (vs. market index)
   - Price volatility measures
   - Major price swings and causes
   - Periods of unusual volatility

4. COMPARATIVE PERFORMANCE:
   - Performance vs. S&P 500 (or relevant index)
   - Performance vs. industry/sector index
   - Performance vs. direct competitors
   - Outperformance or underperformance periods

5. TRADING DYNAMICS:
   - Liquidity analysis
   - Institutional ownership percentage
   - Insider ownership percentage
   - Short interest
   - Options activity (if notable)

6. MAJOR STOCK EVENTS:
   - Stock splits or reverse splits
   - Major single-day moves (with reasons)
   - Earnings-related price movements
   - News-driven price changes

Provide current data, historical data, percentages, and sources.
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "current_metrics": self._extract_current_stock_metrics(response.get("content", "")),
            "performance_history": self._extract_performance_history(response.get("content", "")),
            "volatility": self._extract_volatility_metrics(response.get("content", "")),
            "comparative_analysis": self._extract_comparative_performance(response.get("content", "")),
            "ownership_structure": self._extract_ownership_structure(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 2.5: Financial Health Assessment
    # =========================================================================
    
    async def _assess_financial_health(
        self,
        company_name: str,
        ticker_symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Module 2.5: Financial Health Assessment
        
        Assesses:
        - Cash position and runway
        - Debt levels and leverage ratios
        - Liquidity ratios
        - Credit ratings
        - Financial stability indicators
        - Bankruptcy risk signals
        """
        ticker_info = f" (Ticker: {ticker_symbol})" if ticker_symbol else ""
        
        prompt = f"""
Assess financial health and stability for {company_name}{ticker_info}.

REQUIRED ANALYSIS:

1. CASH AND LIQUIDITY:
   - Cash and cash equivalents (current)
   - Cash from operations (last 12 months)
   - Free cash flow
   - Cash runway estimate (for unprofitable companies)
   - Working capital position

2. DEBT ANALYSIS:
   - Total debt (short-term and long-term)
   - Debt-to-equity ratio
   - Debt-to-EBITDA ratio
   - Interest coverage ratio
   - Debt maturity schedule
   - Recent debt refinancing

3. LIQUIDITY RATIOS:
   - Current ratio
   - Quick ratio
   - Cash ratio
   - Liquidity trend over time

4. CREDIT RATINGS:
   - Credit ratings from S&P, Moody's, Fitch
   - Recent rating changes (upgrades or downgrades)
   - Credit outlook (stable, positive, negative)
   - Reasons for rating changes

5. FINANCIAL STABILITY INDICATORS:
   - Altman Z-score (if calculable)
   - Piotroski F-score (if applicable)
   - Days Sales Outstanding (DSO)
   - Days Payable Outstanding (DPO)
   - Cash conversion cycle

6. FINANCIAL STRESS SIGNALS:
   - Going concern warnings
   - Covenant violations
   - Asset sales for liquidity
   - Delayed payments to suppliers
   - Restructuring discussions

7. FINANCIAL STRENGTH ASSESSMENT:
   Overall financial health classification: STRONG, STABLE, CONCERNING, or DISTRESSED
   - Rationale for classification
   - Key strengths
   - Key vulnerabilities
   - Near-term financial risks

Provide specific numbers, ratios, dates, and sources.
"""
        
        response = await self._query_perplexity(prompt)
        
        # Extract and classify financial health
        health_classification = self._classify_financial_health(response.get("content", ""))
        
        return {
            "raw_data": response.get("content", ""),
            "health_classification": health_classification,
            "cash_position": self._extract_cash_position(response.get("content", "")),
            "debt_analysis": self._extract_debt_analysis(response.get("content", "")),
            "liquidity_ratios": self._extract_liquidity_ratios(response.get("content", "")),
            "credit_ratings": self._extract_credit_ratings(response.get("content", "")),
            "stability_indicators": self._extract_stability_indicators(response.get("content", "")),
            "stress_signals": self._extract_health_stress_signals(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 2.6: Capital Allocation Patterns
    # =========================================================================
    
    async def _analyze_capital_allocation(
        self,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Module 2.6: Capital Allocation Patterns
        
        Analyzes:
        - R&D investment levels
        - Capital expenditures
        - M&A activity and spending
        - Share buybacks
        - Dividend policy
        - Investment priorities
        """
        prompt = f"""
Analyze capital allocation patterns and priorities for {company_name}.

REQUIRED ANALYSIS:

1. R&D INVESTMENT:
   - R&D spending (last 5 years)
   - R&D as percentage of revenue
   - R&D trends (increasing, stable, decreasing)
   - Key R&D focus areas
   - Innovation pipeline

2. CAPITAL EXPENDITURES:
   - CapEx spending (last 5 years)
   - CapEx as percentage of revenue
   - Major CapEx projects announced
   - Growth CapEx vs. maintenance CapEx
   - Asset-heavy vs. asset-light model

3. MERGERS AND ACQUISITIONS:
   - M&A activity (last 5-10 years)
   - Total spent on acquisitions
   - Strategic rationale for acquisitions
   - Integration success or challenges
   - M&A strategy (tuck-ins, transformational, etc.)

4. SHAREHOLDER RETURNS:
   - Share buyback programs and amounts
   - Dividend policy and history
   - Dividend yield
   - Total shareholder returns
   - Capital return philosophy

5. INVESTMENT PRIORITIES:
   - Management stated priorities for capital allocation
   - Balance between growth and returns
   - Organic vs. inorganic growth strategy
   - Geographic expansion investments
   - Digital transformation investments

6. CAPITAL ALLOCATION EFFECTIVENESS:
   - Return on invested capital (ROIC)
   - Return on equity (ROE)
   - Return on assets (ROA)
   - Capital efficiency trends

Provide specific dollar amounts, percentages, dates, and sources.
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "rd_investment": self._extract_rd_investment(response.get("content", "")),
            "capex_analysis": self._extract_capex_analysis(response.get("content", "")),
            "ma_activity": self._extract_ma_activity(response.get("content", "")),
            "shareholder_returns": self._extract_shareholder_returns(response.get("content", "")),
            "investment_priorities": self._extract_investment_priorities(response.get("content", "")),
            "capital_efficiency": self._extract_capital_efficiency(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 2.7: Financial Stress Signals Detection
    # =========================================================================
    
    async def _detect_stress_signals(
        self,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Module 2.7: Financial Stress Signals Detection
        
        Detects:
        - Cost cutting announcements
        - Hiring freezes or layoffs
        - Asset sales
        - Delayed investments
        - Covenant violations
        - Liquidity warnings
        """
        prompt = f"""
Detect and analyze financial stress signals for {company_name}.

REQUIRED ANALYSIS:

1. COST REDUCTION INITIATIVES:
   - Cost cutting programs announced
   - Restructuring charges
   - Headcount reduction plans
   - Facility closures for cost savings
   - Target savings amounts and timelines

2. HIRING AND COMPENSATION SIGNALS:
   - Hiring freezes announced
   - Salary freezes or cuts
   - Reduced hiring plans
   - Executive compensation cuts
   - Benefits reductions

3. ASSET SALES AND DIVESTITURES:
   - Non-core assets sold
   - Business unit divestitures
   - Real estate sales
   - Reasons stated (strategic vs. liquidity)
   - Proceeds and use of funds

4. DELAYED OR CANCELLED INVESTMENTS:
   - Projects delayed or cancelled
   - CapEx reductions announced
   - R&D budget cuts
   - Expansion plans postponed

5. DEBT AND LIQUIDITY CONCERNS:
   - Covenant violations or amendments
   - Debt refinancing at worse terms
   - Access to credit concerns
   - Liquidity warnings in filings
   - Draw-downs on credit facilities

6. OPERATIONAL STRESS INDICATORS:
   - Supplier payment delays
   - Extended payment terms negotiated
   - Inventory build-up or write-downs
   - Revenue concentration increasing
   - Customer churn accelerating

7. MANAGEMENT SIGNALS:
   - CFO or CEO departures (especially sudden)
   - Auditor changes
   - Restatements or accounting issues
   - Going concern warnings
   - Restructuring advisors hired

8. MARKET SIGNALS:
   - Stock price collapse
   - Credit spread widening
   - Short seller reports or activity
   - Analyst downgrades citing financial concerns

For each signal identified, provide:
- Date
- Specific details
- Severity (high, medium, low)
- Impact on operations and financial health
- Management's response or explanation
- Source

STRESS LEVEL ASSESSMENT:
Classify overall financial stress as: NONE, LOW, MODERATE, HIGH, or CRITICAL
"""
        
        response = await self._query_perplexity(prompt)
        
        stress_level = self._classify_stress_level(response.get("content", ""))
        
        return {
            "raw_data": response.get("content", ""),
            "stress_level": stress_level,
            "cost_reduction": self._extract_cost_reduction_signals(response.get("content", "")),
            "hiring_signals": self._extract_hiring_signals(response.get("content", "")),
            "asset_sales": self._extract_asset_sales(response.get("content", "")),
            "investment_delays": self._extract_investment_delays(response.get("content", "")),
            "debt_concerns": self._extract_debt_concerns(response.get("content", "")),
            "operational_stress": self._extract_operational_stress(response.get("content", "")),
            "management_signals": self._extract_management_signals(response.get("content", "")),
            "market_signals": self._extract_market_signals(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 2.8: Analyst Sentiment
    # =========================================================================
    
    async def _gather_analyst_sentiment(
        self,
        company_name: str,
        ticker_symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Module 2.8: Analyst Sentiment (Public Companies)
        
        Gathers:
        - Analyst ratings (buy, hold, sell)
        - Price targets
        - Earnings estimates
        - Analyst reports themes
        - Rating changes
        """
        ticker_info = f" (Ticker: {ticker_symbol})" if ticker_symbol else ""
        
        prompt = f"""
Gather analyst sentiment and research coverage for {company_name}{ticker_info}.

REQUIRED INFORMATION:

1. ANALYST RATINGS CONSENSUS:
   - Number of analysts covering the stock
   - Buy/Outperform ratings count
   - Hold/Neutral ratings count
   - Sell/Underperform ratings count
   - Consensus rating (weighted average)

2. PRICE TARGETS:
   - Consensus price target
   - High price target (analyst name if available)
   - Low price target (analyst name if available)
   - Price target range
   - Implied upside/downside from current price

3. RECENT RATING CHANGES (Last 6 months):
   - Upgrades (analyst, date, old rating, new rating, rationale)
   - Downgrades (analyst, date, old rating, new rating, rationale)
   - Price target changes
   - Initiations of coverage

4. EARNINGS ESTIMATES:
   - Consensus EPS estimate for current quarter
   - Consensus EPS estimate for current fiscal year
   - Consensus EPS estimate for next fiscal year
   - Revenue estimates (quarterly and annual)
   - Estimate revisions trend (up or down)

5. ANALYST THEMES AND CONCERNS:
   - Common bullish themes across analyst reports
   - Common bearish concerns
   - Key debates among analysts
   - Questions raised in earnings calls

6. EARNINGS SURPRISE HISTORY:
   - Last 4 quarters: beat, meet, or miss estimates
   - Magnitude of surprises
   - Stock reaction to earnings

7. SELL-SIDE RESEARCH FIRMS COVERING:
   - Major investment banks covering the stock
   - Independent research firms
   - Most bullish and bearish analysts

Provide specific numbers, analyst names (where available), dates, and sources.
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "ratings_consensus": self._extract_ratings_consensus(response.get("content", "")),
            "price_targets": self._extract_price_targets(response.get("content", "")),
            "rating_changes": self._extract_rating_changes(response.get("content", "")),
            "earnings_estimates": self._extract_earnings_estimates(response.get("content", "")),
            "analyst_themes": self._extract_analyst_themes(response.get("content", "")),
            "earnings_history": self._extract_earnings_history(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
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
                                    "content": "You are a financial intelligence analyst. Provide detailed, accurate financial data with specific numbers, dates, and citations."
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
                except Exception as e:
                    continue
            
            return {"content": "", "sources": [], "model_used": None}
    
    # =========================================================================
    # Helper Methods: Data Extraction (Stubs - to be implemented)
    # =========================================================================
    
    def _extract_historical_revenue(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_growth_metrics(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_revenue_breakdown(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_growth_drivers(self, content: str) -> List[str]:
        return []
    
    def _extract_revenue_guidance(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_margin_analysis(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_profitability_trends(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_segment_profitability(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_path_to_profitability(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_cost_structure(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_funding_rounds(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_total_capital(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_investors(self, content: str) -> List[str]:
        return []
    
    def _extract_valuation_history(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_ipo_details(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_current_stock_metrics(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_performance_history(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_volatility_metrics(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_comparative_performance(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_ownership_structure(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_cash_position(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_debt_analysis(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_liquidity_ratios(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_credit_ratings(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_stability_indicators(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_health_stress_signals(self, content: str) -> List[str]:
        return []
    
    def _classify_financial_health(self, content: str) -> str:
        """Classify financial health based on content analysis"""
        content_lower = content.lower()
        if any(word in content_lower for word in ["distressed", "bankruptcy", "liquidity crisis", "covenant violation"]):
            return FinancialHealth.DISTRESSED.value
        elif any(word in content_lower for word in ["concerning", "financial pressure", "cash crunch", "declining"]):
            return FinancialHealth.CONCERNING.value
        elif any(word in content_lower for word in ["stable", "adequate", "moderate"]):
            return FinancialHealth.STABLE.value
        elif any(word in content_lower for word in ["strong", "robust", "healthy", "excellent"]):
            return FinancialHealth.STRONG.value
        return FinancialHealth.STABLE.value
    
    def _extract_rd_investment(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_capex_analysis(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_ma_activity(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_shareholder_returns(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_investment_priorities(self, content: str) -> List[str]:
        return []
    
    def _extract_capital_efficiency(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _classify_stress_level(self, content: str) -> str:
        """Classify financial stress level"""
        content_lower = content.lower()
        critical_signals = ["bankruptcy", "insolvency", "going concern", "default"]
        high_signals = ["covenant violation", "liquidity warning", "mass layoffs", "asset fire sale"]
        moderate_signals = ["cost cutting", "hiring freeze", "delayed investment"]
        
        if any(signal in content_lower for signal in critical_signals):
            return "CRITICAL"
        elif any(signal in content_lower for signal in high_signals):
            return "HIGH"
        elif any(signal in content_lower for signal in moderate_signals):
            return "MODERATE"
        elif any(signal in content_lower for signal in ["pressure", "challenge", "concern"]):
            return "LOW"
        return "NONE"
    
    def _extract_cost_reduction_signals(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_hiring_signals(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_asset_sales(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_investment_delays(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_debt_concerns(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_operational_stress(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_management_signals(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_market_signals(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_ratings_consensus(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_price_targets(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_rating_changes(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_earnings_estimates(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_analyst_themes(self, content: str) -> Dict[str, List[str]]:
        return {"bullish": [], "bearish": []}
    
    def _extract_earnings_history(self, content: str) -> List[Dict[str, Any]]:
        return []
