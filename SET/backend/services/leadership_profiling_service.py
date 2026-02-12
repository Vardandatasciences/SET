"""
Leadership Profiling System
Module 4 from Sales Enablement Tool (SET)

This module provides comprehensive leadership intelligence including executive profiling,
communication styles, decision-making patterns, career trajectories, and influence mapping.
"""

import httpx
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class DecisionMakingStyle(Enum):
    """Decision-making style classification"""
    ANALYTICAL = "analytical"
    DIRECTIVE = "directive"
    CONCEPTUAL = "conceptual"
    BEHAVIORAL = "behavioral"


class CommunicationStyle(Enum):
    """Communication style classification"""
    DIRECT = "direct"
    SPIRITED = "spirited"
    CONSIDERATE = "considerate"
    SYSTEMATIC = "systematic"


class LeadershipProfilingService:
    """
    Leadership Profiling System
    Comprehensive executive intelligence including:
    - Executive identification and org chart mapping
    - Individual leader profiling
    - Communication and decision-making styles
    - Career trajectory analysis
    - Executive messages and priorities
    - Leadership turnover tracking
    - Influence and power mapping
    - Executive compensation and incentives
    """
    
    def __init__(self, perplexity_api_key: str):
        self.api_key = perplexity_api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def gather_leadership_intelligence(
        self,
        company_name: str,
        specific_executives: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main orchestrator for leadership intelligence gathering
        
        Returns comprehensive leadership intelligence covering:
        - Executive team identification
        - Individual executive profiles
        - Leadership structure and reporting lines
        - Communication styles and preferences
        - Executive priorities and initiatives
        - Leadership stability and turnover
        - Board of directors information
        - Advisory board members
        """
        print("\n" + "="*80)
        print("👔 LEADERSHIP PROFILING SYSTEM")
        print("="*80)
        print(f"🏢 Target Company: {company_name}")
        print(f"🎯 Specific Executives: {', '.join(specific_executives) if specific_executives else 'All executives'}")
        print("="*80 + "\n")
        
        leadership_intel = {
            "company_name": company_name,
            "gathered_at": datetime.now().isoformat(),
            "modules": {}
        }
        
        # Module 4.1: Executive Team Identification
        print("👥 Module 4.1: Identifying Executive Team...")
        leadership_intel["modules"]["executive_team"] = await self._identify_executive_team(
            company_name
        )
        
        # Module 4.2: C-Suite Profiling
        print("\n🎩 Module 4.2: Profiling C-Suite Executives...")
        leadership_intel["modules"]["csuite_profiles"] = await self._profile_csuite(
            company_name, specific_executives
        )
        
        # Module 4.3: Board of Directors
        print("\n🏛️ Module 4.3: Gathering Board of Directors Information...")
        leadership_intel["modules"]["board_of_directors"] = await self._gather_board_info(
            company_name
        )
        
        # Module 4.4: Executive Messages and Priorities
        print("\n📣 Module 4.4: Analyzing Executive Messages and Priorities...")
        leadership_intel["modules"]["executive_messages"] = await self._analyze_executive_messages(
            company_name
        )
        
        # Module 4.5: Leadership Turnover and Stability
        print("\n🔄 Module 4.5: Tracking Leadership Turnover and Stability...")
        leadership_intel["modules"]["leadership_turnover"] = await self._track_leadership_turnover(
            company_name
        )
        
        # Module 4.6: Organizational Structure
        print("\n📊 Module 4.6: Mapping Organizational Structure...")
        leadership_intel["modules"]["org_structure"] = await self._map_org_structure(
            company_name
        )
        
        # Module 4.7: Executive Compensation and Incentives
        print("\n💰 Module 4.7: Analyzing Executive Compensation...")
        leadership_intel["modules"]["compensation"] = await self._analyze_compensation(
            company_name
        )
        
        # Module 4.8: Decision-Making Intelligence
        print("\n🧠 Module 4.8: Analyzing Decision-Making Patterns...")
        leadership_intel["modules"]["decision_making"] = self._analyze_decision_making(
            leadership_intel["modules"]
        )
        
        print("\n" + "="*80)
        print("✅ LEADERSHIP INTELLIGENCE GATHERING COMPLETED")
        print("="*80 + "\n")
        
        return leadership_intel
    
    # =========================================================================
    # Module 4.1: Executive Team Identification
    # =========================================================================
    
    async def _identify_executive_team(
        self,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Module 4.1: Executive Team Identification
        
        Identifies:
        - CEO and top executives
        - C-suite members (CFO, CTO, COO, CMO, etc.)
        - Senior VPs and key decision-makers
        - Department heads
        - Reporting structure
        """
        prompt = f"""
Identify the executive team and leadership structure for {company_name}.

REQUIRED INFORMATION:

1. C-SUITE EXECUTIVES:
   - CEO (Chief Executive Officer)
   - CFO (Chief Financial Officer)
   - CTO/CIO (Chief Technology/Information Officer)
   - COO (Chief Operating Officer)
   - CMO (Chief Marketing Officer)
   - CPO (Chief Product Officer)
   - CHRO (Chief Human Resources Officer)
   - Chief Legal Officer / General Counsel
   - Chief Compliance Officer
   - Other C-level executives
   
   For each executive, provide:
   - Full name
   - Official title
   - Years in current role
   - Years with company
   - Email (if available from company website)
   - LinkedIn profile URL
   - Photo (if available from company website)

2. SENIOR VICE PRESIDENTS AND KEY DECISION MAKERS:
   - SVP/VP of Sales
   - SVP/VP of Engineering
   - SVP/VP of Operations
   - SVP/VP of Business Development
   - SVP/VP of Strategy
   - SVP/VP of Product Management
   - Other senior leadership
   
   For each, provide: Name, title, tenure

3. DEPARTMENT HEADS AND DIRECTORS:
   - Director-level roles that are key decision makers
   - Department heads
   - Regional leaders (if multinational)
   
   For each, provide: Name, title, department/region

4. REPORTING STRUCTURE:
   - Who reports to whom (org chart structure)
   - Reporting lines and hierarchies
   - Matrix reporting (if applicable)

5. EXECUTIVE TEAM COMPOSITION:
   - Total size of executive team
   - Tenure analysis (average years in role)
   - Diversity metrics (if available)
   - Internal promotions vs. external hires

6. KEY DECISION MAKERS FOR TECHNOLOGY/SOLUTION PURCHASES:
   - Who typically makes buying decisions for:
     * Technology solutions
     * Enterprise software
     * Professional services
     * Infrastructure
   - Procurement/purchasing leadership
   - Budget holders

Provide specific names, titles, and LinkedIn URLs where available.
Focus on publicly available information from company website, press releases, and professional networks.
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "csuite": self._extract_csuite_list(response.get("content", "")),
            "senior_vps": self._extract_senior_vps(response.get("content", "")),
            "department_heads": self._extract_department_heads(response.get("content", "")),
            "org_chart": self._extract_org_chart(response.get("content", "")),
            "team_composition": self._extract_team_composition(response.get("content", "")),
            "key_decision_makers": self._extract_key_decision_makers(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 4.2: C-Suite Profiling
    # =========================================================================
    
    async def _profile_csuite(
        self,
        company_name: str,
        specific_executives: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Module 4.2: Deep C-Suite Profiling
        
        Profiles:
        - Career background and trajectory
        - Education and credentials
        - Previous companies and roles
        - Expertise areas
        - Public statements and viewpoints
        - Communication style
        - Professional network
        - Awards and recognition
        """
        # First get list of executives to profile
        execs_to_profile = specific_executives if specific_executives else [
            "CEO", "CFO", "CTO", "COO", "CMO"
        ]
        
        profiles = {}
        
        for exec_role in execs_to_profile:
            print(f"   🔍 Profiling {exec_role}...")
            
            prompt = f"""
Create a comprehensive profile of the {exec_role} at {company_name}.

REQUIRED INFORMATION:

1. BASIC INFORMATION:
   - Full name
   - Official title
   - Age or age range (if publicly available)
   - Location/office
   - Years in current role
   - Start date with {company_name}

2. CAREER BACKGROUND:
   - Previous companies (in chronological order)
   - Previous roles and responsibilities
   - Career progression and trajectory
   - Notable achievements at previous companies
   - Total years of experience
   - Industry experience

3. EDUCATION:
   - Universities attended
   - Degrees earned (with majors)
   - Graduation years
   - Notable achievements or honors
   - Continuing education or certifications

4. EXPERTISE AND SPECIALIZATIONS:
   - Core areas of expertise
   - Industry knowledge areas
   - Technical skills or specializations
   - Languages spoken
   - Domain expertise

5. PROFESSIONAL ACCOMPLISHMENTS:
   - Awards and recognition
   - Published articles or books
   - Patents or innovations
   - Board memberships (other companies)
   - Advisory roles
   - Speaking engagements

6. PUBLIC PRESENCE AND VIEWPOINTS:
   - LinkedIn activity and posts
   - Twitter/X presence and activity
   - Media interviews and quotes
   - Podcast appearances
   - Conference speaking
   - Blog posts or articles authored
   - Public statements on industry trends
   - Vision for the company

7. COMMUNICATION STYLE:
   - Based on public communications, assess:
     * Communication style (direct, diplomatic, technical, visionary)
     * Preferred communication channels
     * Frequency of public communication
     * Tone (formal, casual, inspirational, data-driven)

8. DECISION-MAKING INDICATORS:
   - Past decisions at current or previous companies
   - Strategic focus areas
   - Risk tolerance (conservative vs. aggressive)
   - Innovation orientation
   - Decision-making style (data-driven, intuitive, collaborative)

9. PRIORITIES AND INITIATIVES:
   - Current priorities for the company (from public statements)
   - Initiatives they're leading
   - Goals they've articulated
   - Challenges they've acknowledged

10. PROFESSIONAL NETWORK:
    - Connections to other industry leaders
    - Mentor relationships (if known)
    - Professional associations
    - University alumni networks

11. PERSONAL INTERESTS (if publicly shared):
    - Hobbies or interests
    - Philanthropic involvement
    - Causes they support
    - Personal brand elements

12. SALES ENGAGEMENT INTELLIGENCE:
    - Best approach for engagement (based on style)
    - Topics they care about
    - Pain points they've mentioned
    - Preferred communication style for sales outreach
    - Referral paths (who might introduce you)

Provide specific examples, dates, quotes, and sources.
Focus on publicly available professional information.
"""
            
            response = await self._query_perplexity(prompt)
            
            profiles[exec_role] = {
                "raw_data": response.get("content", ""),
                "basic_info": self._extract_basic_info(response.get("content", "")),
                "career_background": self._extract_career_background(response.get("content", "")),
                "education": self._extract_education(response.get("content", "")),
                "expertise": self._extract_expertise(response.get("content", "")),
                "accomplishments": self._extract_accomplishments(response.get("content", "")),
                "public_presence": self._extract_public_presence(response.get("content", "")),
                "communication_style": self._assess_communication_style(response.get("content", "")),
                "decision_making_style": self._assess_decision_making_style(response.get("content", "")),
                "priorities": self._extract_priorities(response.get("content", "")),
                "professional_network": self._extract_network(response.get("content", "")),
                "personal_interests": self._extract_personal_interests(response.get("content", "")),
                "sales_intelligence": self._extract_sales_intelligence(response.get("content", "")),
                "sources": response.get("sources", []),
                "profiled_at": datetime.now().isoformat()
            }
        
        return profiles
    
    # =========================================================================
    # Module 4.3: Board of Directors
    # =========================================================================
    
    async def _gather_board_info(
        self,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Module 4.3: Board of Directors Information
        
        Gathers:
        - Board members and their backgrounds
        - Board composition (independent vs. insider)
        - Board committees
        - Recent board changes
        - Board expertise areas
        """
        prompt = f"""
Research the Board of Directors for {company_name}.

REQUIRED INFORMATION:

1. BOARD MEMBERS:
   For each board member, provide:
   - Full name
   - Board role (Chair, Lead Independent Director, Member)
   - Board committees they serve on
   - Year joined board
   - Independent or insider/management director
   - Primary background/expertise
   - Current primary occupation (if not full-time with {company_name})
   - Other board seats held
   - Notable career achievements
   - LinkedIn profile URL

2. BOARD COMPOSITION:
   - Total number of board members
   - Number of independent directors
   - Number of inside directors
   - Diversity metrics (if available)
   - Average tenure on board
   - Skills matrix of board (what expertise areas are represented)

3. BOARD COMMITTEES:
   - Audit Committee (members and chair)
   - Compensation Committee (members and chair)
   - Nominating/Governance Committee (members and chair)
   - Other special committees
   - Committee charters or focus areas

4. RECENT BOARD CHANGES:
   - New board members added (last 2 years)
   - Board members who departed (last 2 years)
   - Reasons for changes
   - Board refreshment initiatives

5. BOARD EXPERTISE:
   - Industry expertise represented
   - Functional expertise (finance, tech, operations, etc.)
   - Geographic expertise
   - Strategic value board brings

6. BOARD LEADERSHIP:
   - Board chair (name and background)
   - Lead independent director (if separate)
   - Board governance practices
   - Board meeting frequency

7. SHAREHOLDER PERSPECTIVES:
   - Large shareholders with board representation
   - Investor directors
   - Founder board seats
   - Activist investor involvement

Provide specific names, dates, and sources.
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "board_members": self._extract_board_members(response.get("content", "")),
            "board_composition": self._extract_board_composition(response.get("content", "")),
            "board_committees": self._extract_board_committees(response.get("content", "")),
            "recent_changes": self._extract_board_changes(response.get("content", "")),
            "board_expertise": self._extract_board_expertise(response.get("content", "")),
            "board_leadership": self._extract_board_leadership(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 4.4: Executive Messages and Priorities
    # =========================================================================
    
    async def _analyze_executive_messages(
        self,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Module 4.4: Executive Messages and Priorities Analysis
        
        Analyzes:
        - CEO letters and messages
        - Earnings call commentary
        - Strategic priorities communicated
        - Vision statements
        - Values and culture messages
        """
        prompt = f"""
Analyze executive messages and communications from {company_name} leadership.

REQUIRED ANALYSIS:

1. CEO MESSAGES:
   - Recent CEO letters to shareholders
   - CEO blog posts or articles
   - CEO media interviews (key quotes)
   - CEO vision statements
   - CEO priorities communicated
   - Key themes in CEO communications

2. CFO COMMENTARY:
   - Financial guidance and outlook
   - Capital allocation priorities
   - Investment areas highlighted
   - Cost management initiatives
   - Financial strategy

3. EARNINGS CALL ANALYSIS (Last 4 quarters):
   - Key themes from prepared remarks
   - Strategic priorities discussed
   - Challenges acknowledged
   - Opportunities highlighted
   - Questions analysts asked (indicating areas of concern/interest)
   - Management's forward-looking statements

4. EXECUTIVE SOCIAL MEDIA:
   - LinkedIn posts from executives
   - Twitter/X activity
   - Themes in social posts
   - Engagement levels

5. STRATEGIC PRIORITIES (from all executive communications):
   - Top 3-5 strategic priorities
   - Digital transformation initiatives
   - Growth strategies
   - Operational excellence goals
   - Innovation focus areas
   - Customer experience priorities
   - Sustainability/ESG commitments

6. ORGANIZATIONAL VALUES AND CULTURE:
   - Stated company values
   - Culture initiatives from leadership
   - Diversity and inclusion priorities
   - Employee experience focus

7. INDUSTRY VIEWPOINTS:
   - Executive perspectives on industry trends
   - Competitive positioning statements
   - Market outlook from leadership
   - Technology trends they emphasize

8. LEADERSHIP MESSAGING CONSISTENCY:
   - Consistency of messages across executives
   - Evolution of messaging over time
   - Alignment between different C-suite messages

For each message or theme, include:
- Date
- Executive name and role
- Source (letter, call, interview, etc.)
- Key quotes
- Link to source

SALES ENABLEMENT INSIGHT:
- How can these priorities inform sales conversations?
- What pain points do executives acknowledge?
- What solutions are they seeking?
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "ceo_messages": self._extract_ceo_messages(response.get("content", "")),
            "cfo_commentary": self._extract_cfo_commentary(response.get("content", "")),
            "earnings_themes": self._extract_earnings_themes(response.get("content", "")),
            "social_media_activity": self._extract_social_activity(response.get("content", "")),
            "strategic_priorities": self._extract_strategic_priorities(response.get("content", "")),
            "org_values": self._extract_org_values(response.get("content", "")),
            "industry_viewpoints": self._extract_industry_viewpoints(response.get("content", "")),
            "messaging_consistency": self._extract_messaging_consistency(response.get("content", "")),
            "sales_enablement_insights": self._extract_sales_enablement_insights(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 4.5: Leadership Turnover and Stability
    # =========================================================================
    
    async def _track_leadership_turnover(
        self,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Module 4.5: Leadership Turnover and Stability Tracking
        
        Tracks:
        - Recent executive departures
        - Executive appointments
        - Turnover rate
        - Succession planning
        - Interim leadership
        - Reasons for departures
        """
        prompt = f"""
Research leadership turnover and stability at {company_name} over the last 5 years.

REQUIRED INFORMATION:

1. EXECUTIVE DEPARTURES (Last 5 years):
   For each departure:
   - Executive name and role
   - Departure date
   - Years in role before departure
   - Reason for departure (resignation, retirement, termination, etc.)
   - Circumstances (planned succession, sudden departure, etc.)
   - Public statement or reason given
   - Where they went next (if known)
   - Impact on company

2. EXECUTIVE APPOINTMENTS (Last 5 years):
   For each new hire/promotion:
   - Executive name and role
   - Appointment date
   - Background (previous company/role)
   - Internal promotion vs. external hire
   - Reason for hire stated
   - Expected impact

3. TURNOVER ANALYSIS:
   - Overall turnover rate in C-suite
   - Which roles have high turnover
   - Stable roles with long tenure
   - Average tenure of current executives
   - Pattern analysis (is there a turnover problem?)

4. SUCCESSION PLANNING:
   - Evidence of succession planning
   - Announced succession plans
   - Internal development programs
   - Bench strength indicators

5. INTERIM LEADERSHIP:
   - Any interim appointments
   - Duration of interim periods
   - Reasons for interim arrangements

6. LEADERSHIP STABILITY INDICATORS:
   - Roles that have been stable
   - Long-tenured executives
   - Promoted-from-within examples
   - Executive retention initiatives

7. IMPACT ON ORGANIZATION:
   - How has turnover affected strategy
   - Disruption from leadership changes
   - Cultural impacts
   - Stability concerns

8. SALES IMPLICATIONS:
   - New decision-makers who might reconsider vendors
   - Relationship continuity risks
   - Fresh start opportunities with new leadership
   - Stability concerns affecting purchasing decisions

Provide specific names, dates, reasons, and sources.
"""
        
        response = await self._query_perplexity(prompt)
        
        stability_assessment = self._assess_leadership_stability(response.get("content", ""))
        
        return {
            "raw_data": response.get("content", ""),
            "stability_assessment": stability_assessment,
            "departures": self._extract_departures(response.get("content", "")),
            "appointments": self._extract_appointments(response.get("content", "")),
            "turnover_analysis": self._extract_turnover_analysis(response.get("content", "")),
            "succession_planning": self._extract_succession_planning(response.get("content", "")),
            "interim_leadership": self._extract_interim_leadership(response.get("content", "")),
            "stability_indicators": self._extract_stability_indicators(response.get("content", "")),
            "organizational_impact": self._extract_organizational_impact(response.get("content", "")),
            "sales_implications": self._extract_turnover_sales_implications(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 4.6: Organizational Structure Mapping
    # =========================================================================
    
    async def _map_org_structure(
        self,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Module 4.6: Organizational Structure Mapping
        
        Maps:
        - Organizational hierarchy
        - Reporting lines
        - Business units and divisions
        - Functional organization
        - Geographic structure
        - Matrix organization (if applicable)
        """
        prompt = f"""
Map the organizational structure for {company_name}.

REQUIRED INFORMATION:

1. ORGANIZATIONAL HIERARCHY:
   - CEO at the top
   - Direct reports to CEO (with names)
   - Second-level reporting (who reports to each C-suite member)
   - Key managers at third level

2. BUSINESS UNITS/DIVISIONS:
   - Major business units or divisions
   - Leaders of each business unit
   - Reporting structure for BUs
   - Revenue or size of each BU

3. FUNCTIONAL ORGANIZATION:
   - How is the company organized functionally?
   - Sales organization structure
   - Engineering/Product organization
   - Operations structure
   - Support functions structure

4. GEOGRAPHIC STRUCTURE:
   - Regional leadership (Americas, EMEA, APAC, etc.)
   - Country leaders (if applicable)
   - Headquarters vs. regional autonomy

5. MATRIX ORGANIZATION:
   - Is there matrix reporting?
   - Functional vs. business unit reporting
   - How does the matrix work?

6. ORGANIZATION SIZE:
   - Approximate size of each major organization
   - Spans of control
   - Organization growth or contraction

7. REORGANIZATION HISTORY:
   - Recent org structure changes
   - Reorganizations announced
   - Rationale for changes

Provide names, titles, and reporting relationships where available.
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "hierarchy": self._extract_hierarchy(response.get("content", "")),
            "business_units": self._extract_business_units(response.get("content", "")),
            "functional_org": self._extract_functional_org(response.get("content", "")),
            "geographic_structure": self._extract_geographic_structure(response.get("content", "")),
            "matrix_details": self._extract_matrix_details(response.get("content", "")),
            "org_size": self._extract_org_size(response.get("content", "")),
            "reorg_history": self._extract_reorg_history(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 4.7: Executive Compensation Analysis
    # =========================================================================
    
    async def _analyze_compensation(
        self,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Module 4.7: Executive Compensation and Incentives Analysis
        
        Analyzes:
        - Executive compensation levels
        - Incentive structures
        - Performance metrics tied to compensation
        - Equity holdings
        - Alignment with shareholders
        """
        prompt = f"""
Analyze executive compensation structure for {company_name} (if public or information is available).

REQUIRED INFORMATION:

1. EXECUTIVE COMPENSATION LEVELS (for public companies):
   For CEO and named executive officers (NEOs):
   - Base salary
   - Annual cash bonus
   - Long-term incentive (equity awards)
   - Total compensation
   - Year-over-year changes
   - Peer group comparison

2. INCENTIVE STRUCTURES:
   - What metrics drive annual bonuses?
   - What metrics drive long-term incentives?
   - Performance targets (if disclosed)
   - Payout curves
   - Clawback provisions

3. EQUITY HOLDINGS:
   - CEO equity ownership (shares and value)
   - Other executive equity holdings
   - Vesting schedules
   - Recent insider buying or selling
   - Equity as % of total compensation

4. ALIGNMENT WITH SHAREHOLDERS:
   - Pay-for-performance analysis
   - Stock ownership guidelines
   - Holding requirements
   - Say-on-pay vote results (if applicable)

5. COMPENSATION PHILOSOPHY:
   - Company's stated compensation philosophy
   - Market positioning (e.g., target 50th percentile)
   - Mix of fixed vs. variable pay
   - Use of peer comparisons

6. SPECIAL ARRANGEMENTS:
   - Sign-on bonuses for new executives
   - Retention bonuses
   - Change-in-control provisions
   - Severance agreements

7. SALES INTELLIGENCE IMPLICATIONS:
   - What do compensation structures tell us about priorities?
   - If executives are incentivized on specific metrics, what does that mean for buying decisions?
   - Budget authority and spending patterns

Provide specific figures, dates, and sources (typically from proxy statements/DEF 14A for public companies).
"""
        
        response = await self._query_perplexity(prompt)
        
        return {
            "raw_data": response.get("content", ""),
            "compensation_levels": self._extract_compensation_levels(response.get("content", "")),
            "incentive_structures": self._extract_incentive_structures(response.get("content", "")),
            "equity_holdings": self._extract_equity_holdings(response.get("content", "")),
            "shareholder_alignment": self._extract_shareholder_alignment(response.get("content", "")),
            "compensation_philosophy": self._extract_compensation_philosophy(response.get("content", "")),
            "special_arrangements": self._extract_special_arrangements(response.get("content", "")),
            "sales_implications": self._extract_compensation_sales_insights(response.get("content", "")),
            "sources": response.get("sources", []),
            "collected_at": datetime.now().isoformat()
        }
    
    # =========================================================================
    # Module 4.8: Decision-Making Intelligence
    # =========================================================================
    
    def _analyze_decision_making(
        self,
        modules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Module 4.8: Decision-Making Intelligence
        
        Synthesizes insights about:
        - How decisions are made
        - Who the real decision makers are
        - Decision-making speed
        - Consensus vs. top-down
        - Influencers and gatekeepers
        """
        # Synthesize from other modules
        decision_intel = {
            "decision_makers": [],
            "decision_making_process": "",
            "influencers": [],
            "gatekeepers": [],
            "decision_speed": "",
            "procurement_process": "",
            "budget_cycles": ""
        }
        
        # Extract from executive profiles and messages
        csuite_profiles = modules.get("csuite_profiles", {})
        executive_messages = modules.get("executive_messages", {})
        
        # Identify key decision makers
        if csuite_profiles:
            for role, profile in csuite_profiles.items():
                decision_intel["decision_makers"].append({
                    "role": role,
                    "influence_level": "high",
                    "decision_areas": self._infer_decision_areas(role)
                })
        
        # General decision-making insights
        decision_intel["decision_making_process"] = "Synthesized from executive communications and organizational structure"
        decision_intel["decision_speed"] = "Typical enterprise decision cycle: 3-9 months"
        
        return decision_intel
    
    def _infer_decision_areas(self, role: str) -> List[str]:
        """Infer decision areas based on executive role"""
        decision_areas_map = {
            "CEO": ["Strategic direction", "Major investments", "M&A", "Enterprise initiatives"],
            "CFO": ["Financial systems", "Budgets", "ROI decisions", "Cost management solutions"],
            "CTO": ["Technology stack", "Architecture", "Infrastructure", "Development tools"],
            "CIO": ["Enterprise IT", "Security", "Data management", "IT operations"],
            "COO": ["Operational tools", "Process automation", "Supply chain", "Productivity"],
            "CMO": ["Marketing technology", "CRM", "Analytics", "Customer engagement"],
            "CHRO": ["HR systems", "Talent management", "Learning platforms", "Employee experience"]
        }
        return decision_areas_map.get(role, ["Department-specific decisions"])
    
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
                                    "content": "You are a leadership intelligence analyst. Provide detailed, accurate information about executives and organizational leadership with specific names, titles, and citations."
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
    
    def _extract_csuite_list(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_senior_vps(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_department_heads(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_org_chart(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_team_composition(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_key_decision_makers(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_basic_info(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_career_background(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_education(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_expertise(self, content: str) -> List[str]:
        return []
    
    def _extract_accomplishments(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_public_presence(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _assess_communication_style(self, content: str) -> str:
        """Assess communication style based on content"""
        content_lower = content.lower()
        if any(word in content_lower for word in ["direct", "decisive", "concise", "to the point"]):
            return CommunicationStyle.DIRECT.value
        elif any(word in content_lower for word in ["enthusiastic", "energetic", "dynamic"]):
            return CommunicationStyle.SPIRITED.value
        elif any(word in content_lower for word in ["collaborative", "empathetic", "team"]):
            return CommunicationStyle.CONSIDERATE.value
        elif any(word in content_lower for word in ["analytical", "methodical", "systematic", "data-driven"]):
            return CommunicationStyle.SYSTEMATIC.value
        return "unknown"
    
    def _assess_decision_making_style(self, content: str) -> str:
        """Assess decision-making style based on content"""
        content_lower = content.lower()
        if any(word in content_lower for word in ["data-driven", "analytical", "metrics", "analysis"]):
            return DecisionMakingStyle.ANALYTICAL.value
        elif any(word in content_lower for word in ["quick", "decisive", "action-oriented", "results"]):
            return DecisionMakingStyle.DIRECTIVE.value
        elif any(word in content_lower for word in ["visionary", "strategic", "innovation", "future"]):
            return DecisionMakingStyle.CONCEPTUAL.value
        elif any(word in content_lower for word in ["team", "collaborative", "consensus", "people"]):
            return DecisionMakingStyle.BEHAVIORAL.value
        return "unknown"
    
    def _extract_priorities(self, content: str) -> List[str]:
        return []
    
    def _extract_network(self, content: str) -> Dict[str, List[str]]:
        return {}
    
    def _extract_personal_interests(self, content: str) -> List[str]:
        return []
    
    def _extract_sales_intelligence(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_board_members(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_board_composition(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_board_committees(self, content: str) -> Dict[str, List[str]]:
        return {}
    
    def _extract_board_changes(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_board_expertise(self, content: str) -> List[str]:
        return []
    
    def _extract_board_leadership(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_ceo_messages(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_cfo_commentary(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_earnings_themes(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_social_activity(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_strategic_priorities(self, content: str) -> List[str]:
        return []
    
    def _extract_org_values(self, content: str) -> List[str]:
        return []
    
    def _extract_industry_viewpoints(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_messaging_consistency(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_sales_enablement_insights(self, content: str) -> List[str]:
        return []
    
    def _assess_leadership_stability(self, content: str) -> str:
        """Assess leadership stability level"""
        content_lower = content.lower()
        if any(word in content_lower for word in ["high turnover", "frequent changes", "instability"]):
            return "unstable"
        elif any(word in content_lower for word in ["moderate turnover", "some changes"]):
            return "moderate"
        elif any(word in content_lower for word in ["stable", "long tenure", "low turnover"]):
            return "stable"
        return "unknown"
    
    def _extract_departures(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_appointments(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_turnover_analysis(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_succession_planning(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_interim_leadership(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_stability_indicators(self, content: str) -> List[str]:
        return []
    
    def _extract_organizational_impact(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_turnover_sales_implications(self, content: str) -> List[str]:
        return []
    
    def _extract_hierarchy(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_business_units(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_functional_org(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_geographic_structure(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_matrix_details(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_org_size(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_reorg_history(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_compensation_levels(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_incentive_structures(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_equity_holdings(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_shareholder_alignment(self, content: str) -> Dict[str, Any]:
        return {}
    
    def _extract_compensation_philosophy(self, content: str) -> str:
        return ""
    
    def _extract_special_arrangements(self, content: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_compensation_sales_insights(self, content: str) -> List[str]:
        return []
