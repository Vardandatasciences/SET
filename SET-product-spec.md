 # Vardaan’s Sales Enablement Tool (SET) – Product Specification

 ## 1. Product Overview

### 1.1 Product Name
- **Name**: Vardaan’s Sales Enablement Tool (SET)  
- **Alternate description**: Sales Enablement Intelligence Capsule Tool

### 1.2 Problem Statement
Modern B2B sales teams struggle to:
- Research target accounts and executives deeply enough before meetings.
- Stay on top of long-range news, financial health, regulatory issues, and controversies.
- Translate raw intelligence into concrete, customized sales talking points.
- Access this intelligence conveniently across desktop, mobile, CRM, email, and collaboration tools.

### 1.3 Solution Summary
Vardaan’s SET is an **intelligence platform** that:
- Aggregates **company, leadership, financial, news, strategic, and risk** intelligence from many public and commercial sources.
- Synthesizes that data into **professional “intelligence capsules”** (Word, PowerPoint, PDF) using NLG (natural language generation).
- Delivers those capsules and key insights through **web, mobile apps, email, CRM, Slack/Teams, WhatsApp, and APIs**.
- Provides **enterprise-grade security, privacy, compliance, and governance** across all intelligence.

### 1.4 Target Users & Personas
- **Account Executives (AEs)**: Use capsules for pre-meeting prep, talking points, and strategic account planning.
- **Sales Development Representatives (SDRs/BDRs)**: Use quick snapshots and talking points for outreach and qualification.
- **Sales Managers & Directors**: Monitor intelligence coverage, prioritize accounts, and coach teams using challenge- and priority-based insights.
- **Revenue Operations / Sales Operations**: Configure integrations, workflows, scoring, and reporting.
- **Marketing & ABM teams**: Use company and leadership intelligence for account-based campaigns.
- **Risk, Compliance, and Legal**: Govern use of sensitive news, regulatory data, and privacy/consent.

### 1.5 High-Level Capabilities
- **Core intelligence modules**:
  - Company Intelligence Discovery
  - Leadership Intelligence Extraction
  - Long-Range News & Event Tracking
  - Sensitive News & Controversy Handling
  - Financial Intelligence & Stress Indicators
  - Strategic Priorities & Vision Extraction
  - Challenge & Risk Intelligence
  - Intelligent Capsule Generation
- **Delivery & access**:
  - Web app, Mobile apps (iOS/Android), Email, Slack/Teams, WhatsApp, CRM widgets, REST APIs.
- **Enterprise platform features**:
  - Analytics dashboards, collaboration, task management, MDM, document management, real-time updates, privacy/compliance, backup & DR, and security monitoring.

---

## 2. System Architecture – High-Level View

### 2.1 Major Components
- **Data Ingestion Layer**
  - Collects data from:
    - Public company filings (e.g., SEC/EDGAR).
    - Financial data providers.
    - News, PR, and media sources (7–10 years history).
    - Regulatory and compliance databases.
    - Social media and professional networks (e.g., LinkedIn, Twitter/X).
    - Review and complaint sites (e.g., BBB, Trustpilot, Yelp).
    - Market research / industry reports (where licensed).
  - Performs:
    - Entity resolution (companies, people, competitors).
    - De-duplication across sources.
    - Timestamping and source attribution.

- **Intelligence Processing Layer**
  - **NLP and NER** to extract:
    - Company attributes, financial metrics, risk factors, events, leadership bios, themes, and sentiment.
  - **Classification & scoring**:
    - Sentiment analysis (positive/negative/neutral).
    - Impact and severity scoring (financial, operational, strategic, reputational).
    - Stress indicators and challenge severity.
  - **Timeline and pattern detection**:
    - Historical event timelines (7–10 years).
    - Recurring/chronic issues vs one-off incidents.

- **Capsule Generation Engine**
  - Template-based capsule generation in **DOCX, PPTX, PDF**.
  - Natural language generation to produce human-like narrative text.
  - Sales talking points and recommendations generator.
  - Configurable depth: executive summary vs standard vs comprehensive.

- **Delivery & Access Layer**
  - **Web application** (desktop browser).
  - **Mobile apps** (iOS & Android).
  - **Email notifications and attachments**.
  - **Collaboration integrations** (Slack, Microsoft Teams).
  - **CRM integrations** (Salesforce, HubSpot, Microsoft Dynamics 365, others).
  - **WhatsApp Business integration**.
  - **REST API** for custom integrations and programmatic use.

- **Enterprise Platform Layer**
  - Authentication, RBAC, MFA.
  - Master data management (companies, industries, competitors, technologies).
  - Document & version management for generated capsules.
  - Analytics, dashboards, and reporting.
  - Privacy, GDPR/CCPA compliance, consent management.
  - Audit logging, security monitoring, backup & disaster recovery.

---

## 3. Core Intelligence Modules & Features

### 3.1 Company Intelligence Discovery System

#### 3.1.1 Comprehensive Company Profiles
- **Basic company info**:
  - Legal entity name and standardized aliases.
  - Headquarters (city, state, country).
  - Industry classification (NAICS/SIC).
  - Company size (employee bands, revenue bands).
  - Public vs private status.
  - Parent/subsidiary relationships and corporate structure.
  - Official website URLs.
- **Public financial snapshot (for public companies)**:
  - Latest quarterly and annual revenues + YoY growth.
  - Profitability metrics (margins, trend).
  - Stock price and 52-week range.
  - Market capitalization.
  - Earnings reports, guidance, and analyst ratings.
- **Private company indicators**:
  - Employee count trends.
  - Funding rounds and investors.
  - Estimated revenue ranges.
  - Business credit ratings where available.

#### 3.1.2 Competitive Intelligence Gathering
- Identify, map, and profile major competitors via:
  - Industry databases, news mentions, and analyst reports.
- Track:
  - Relative market share and share trends.
  - Product and positioning differentiation.
  - Public pricing strategies.
  - Technological strengths/weaknesses.
  - Publicly disclosed wins/losses and vendor preferences.
  - News about competitive dynamics and strategic moves.

#### 3.1.3 Regulatory & Compliance Environment
- Detect and track:
  - Industry-specific regulators (SEC, FDA, FCC, etc.).
  - Regulatory filings and approvals/warnings.
  - Pending regulatory changes impacting the company/industry.
  - Violations, consent orders, fines, and enforcement actions.
  - Cross-border regulatory challenges (multi-jurisdiction).
- Categorize challenges by:
  - Impact level (high, medium, low).
  - Type (financial, operational, reputational, legal).

#### 3.1.4 Market Conditions & Economic Pressures
- Monitor:
  - Sector-specific economic indicators and cycles.
  - Commodity price fluctuations affecting input costs.
  - Demand reduction in key markets.
  - Supply chain disruptions and logistics constraints.
- Derive:
  - Capital expenditure changes.
  - Cost reduction programs, hiring freezes, layoffs.
  - Debt and credit rating changes.

#### 3.1.5 Workforce Changes & Restructuring
- Track:
  - Large-scale layoffs and restructuring.
  - Hiring surges by department and function.
  - Leadership changes (C-level and key roles).
  - Office closures, relocations, geographic footprint changes.
- Attach:
  - Dates, sources, and sales implications.

#### 3.1.6 Operational Disruptions
- Capture events like:
  - Factory/plant outages and production shutdowns.
  - Supply chain interruptions.
  - Technology outages and cybersecurity incidents.
  - Natural disasters impacting facilities.
  - Major quality issues and product recalls.
- Document:
  - Impact, recovery status, and potential solution angles.

#### 3.1.7 Consumer Sentiment & Reputation
- Aggregate:
  - BBB complaints and ratings.
  - Online review platforms (e.g., Trustpilot, Yelp, industry sites).
  - Social media mentions (LinkedIn, Twitter/X, Facebook, etc.).
  - Forums and discussion boards.
  - Regulatory complaint databases (e.g., CPSC).
- Analyze:
  - Sentiment (positive/negative/neutral).
  - Key recurring complaint themes (quality, billing, CX, delivery, UX, security).
  - Complaint volume and trend over time.
  - Response and resolution rates.
  - Comparison to industry benchmarks.

---

### 3.2 Leadership Intelligence Extraction System

#### 3.2.1 Executive Profiles
- Build rich profiles for:
  - C-suite and relevant decision-makers / influencers.
- Include:
  - Full name, title, tenure in role.
  - Internal career progression.
  - Prior companies and roles.
  - Education and board/advisory roles.
- Extract:
  - Leadership style and strategic focus from public statements.
  - Repeated themes (e.g., digital transformation, CX, efficiency, ESG).
  - Publicly acknowledged challenges and initiatives championed.

#### 3.2.2 Leadership Transitions
- Track:
  - Executive joins, departures, and internal promotions.
  - Announced reasons (retirement, performance, reorg, etc.).
  - Successor and interim arrangements.
  - Patterns of turnover (stability vs churn).
- Flag:
  - Opportunity triggers for new leadership outreach and vendor review.

#### 3.2.3 Leadership Challenges & Controversies
- Capture **only verified business-relevant** issues:
  - Investor or analyst criticism.
  - Governance concerns.
  - Compensation controversies tied to company performance.
  - Misconduct verified via official filings/media.
- Present:
  - Context, impact, and recommended caution in usage.

#### 3.2.4 Social Media & Public Communications
- Analyze:
  - Social media and thought leadership content.
  - Frequently discussed topics, tone, and engagement patterns.
  - Interest in specific technologies, markets, or trends.
- Provide:
  - Themes and authentic connection points for outreach.

#### 3.2.5 Leadership Network & Connections
- Build:
  - Network graphs from LinkedIn, boards, alumni, co-presentations, prior overlaps.
- Surface:
  - Introduction paths and degrees of separation.
  - Influence relationships and hiring patterns.
  - Shared history among executives in target organizations.

---

### 3.3 Long-Range News Intelligence & Event Tracking

#### 3.3.1 Positive News & Achievements
- Capture 7–10 years of:
  - Successful product launches.
  - Major customer wins.
  - Awards and industry rankings.
  - Strategic partnerships and expansions.
  - Funding rounds and growth milestones.
- Compute:
  - Positive momentum score and trend over time.

#### 3.3.2 Negative News & Challenges
- Track:
  - Financial losses/declines.
  - Legal/regulatory actions.
  - Product failures, recalls, outages.
  - Leadership/governance issues.
  - Cybersecurity incidents (details and responses).
  - PR and reputation crises.
- Annotate each with:
  - Date, source, description, sentiment.
  - Impact category and severity.
  - Temporal analysis (recent vs historical, isolated vs chronic).

#### 3.3.3 Neutral Industry & Market Context
- Maintain:
  - Industry trends and analyst insights.
  - Regulatory developments at sector level.
  - Technology disruptions.
  - Industry-specific economic conditions.

#### 3.3.4 Historical Timelines
- Build:
  - Color-coded, filterable event timelines (positive, negative, neutral).
  - Tools for filtering by date range, category, and impact.
  - Density analysis for periods of intense change vs stability.

---

### 3.4 Sensitive News & Controversy Module

#### 3.4.1 Sensitive Event Categorization
- Treat as sensitive:
  - Major fines, repeated violations.
  - Large lawsuits and class actions.
  - Verified leadership misconduct.
  - Major data breaches.
  - Harmful product failures.
  - Severe business losses (bankruptcy, closures, loss of key contracts).
  - Labor, environmental, consumer-protection, and ethical controversies.

#### 3.4.2 Access Control & Approval
- Role-based permissions:
  - Sales reps, managers, directors, executives, compliance.
- Approval workflow for:
  - Requesting and granting access to sensitive items per account.
- Complete audit trail of:
  - Who accessed what, when, and why.

#### 3.4.3 Contextual Presentation & Guidance
- Show:
  - Status (ongoing, resolved, remediating).
  - Company response and remediation steps.
  - Impact assessment and timeline of coverage.
- Provide:
  - Best-practice guidance on ethical, professional use.
  - Scenario-based recommendations for how/when to reference (or not reference) issues.
  - Explicit warnings against misuse (pressure tactics, sharing across companies, etc.).

---

### 3.5 Financial Intelligence & Stress Indicators

#### 3.5.1 Comprehensive Financial Profile
- For public companies:
  - Revenues, growth rates, margins.
  - Balance sheet and liquidity indicators.
  - Key ratios (P/E, P/S, ROE, FCF, leverage).
  - Stock performance and volatility.
  - Analyst estimates, ratings, and surprises.
- For private companies:
  - Employee and headcount trends.
  - Funding history and valuations.
  - Estimated revenues and credit scores.

#### 3.5.2 Financial Stress Detection
- Monitor:
  - Revenue and earnings warnings.
  - Credit rating downgrades.
  - Covenant breaches/renegotiations.
  - Dividend/buyback suspensions.
  - Restructuring and cost-cut programs.
  - Market-based stress (stock declines, CDS spreads, volatility).
- Score:
  - Severity (low/medium/high).
  - Chronic vs acute.

#### 3.5.3 Funding & Capital Access
- Track:
  - Funding rounds (private).
  - Equity and debt offerings (public).
  - Credit facilities, amendments, and covenants.
  - Asset sales and divestitures.
  - Failed/delayed rounds or IPOs, down rounds.

#### 3.5.4 Auditor Warnings & Risk Factors
- Capture:
  - Going concern warnings.
  - Material weaknesses in internal controls.
  - Qualified/adverse audit opinions.
  - SEC risk factor analysis and changes over time.

---

### 3.6 Strategic Priorities & Vision Extraction

#### 3.6.1 From Annual Reports & MD&A
- Extract:
  - Growth strategies (organic, inorganic, market and product expansion).
  - Operational improvement and cost programs.
  - Investment priorities (CapEx, R&D, tech, people).
  - Customer and market focus.
  - ESG and sustainability commitments (with metrics and timelines).

#### 3.6.2 From Investor Presentations & Calls
- Identify:
  - Roadmaps and timelines for major initiatives.
  - Market sizing, TAM/SAM/SOM, strategic bets.
  - Progress updates and execution status.
  - Analyst Q&A highlights and candid commentary.

#### 3.6.3 Executive Communications & Theme Analysis
- Analyze:
  - Blogs, LinkedIn, keynotes, interviews.
  - Recurring strategic themes across multiple executives.
  - Alignment or divergence between leadership voices.
  - Evolution of themes over time (emerging, persistent, fading).

#### 3.6.4 Digital Transformation & Technology Priorities
- Track:
  - Cloud strategies and migration.
  - Data platforms, analytics, AI/ML use cases.
  - Customer digital experience and omnichannel.
  - Automation (RPA, workflow, document).
  - Cybersecurity investments.
- Attach:
  - Objectives, scope, partners, budgets where available, and timelines.

#### 3.6.5 Competitive Response Strategies
- Detect:
  - Initiatives explicitly responding to competitor pressures.
  - Competitive repositioning, innovation accelerations, partnerships, and M&A.
- Connect:
  - Strategic responses to relevant solution positioning options.

---

### 3.7 Challenge & Risk Intelligence System

#### 3.7.1 External Challenges
- Cover:
  - Competitive pressures and disruptive entrants.
  - Regulatory/compliance burdens.
  - Economic and currency headwinds.
  - Technology disruption and cybersecurity risk.
  - Supply chain constraints.
  - Market and customer demand changes.

#### 3.7.2 Internal Challenges
- Identify:
  - Leadership and governance gaps.
  - Operational inefficiencies and quality issues.
  - Legacy tech, integration, and data problems.
  - Financial and capital allocation challenges.
  - Talent, skills, culture, and change-resistance issues.
  - Product and innovation pipeline weaknesses.

#### 3.7.3 Controversies & Reputation Risks
- Track:
  - Labor disputes, environmental issues, consumer protection problems.
  - Antitrust, discrimination, harassment, political, and supply-chain ethics controversies.
- Assess:
  - Reputational, operational, financial, and strategic impact.

#### 3.7.4 Patterns & Chronic Issues
- Detect:
  - Recurring breaches, recalls, leadership turnover, or other chronic issues.
  - Escalation trends and correlation patterns across risk types.

#### 3.7.5 Impact & Severity Scoring
- Score each challenge on:
  - Financial, operational, strategic, and reputational impact.
  - Time urgency and likelihood of escalation.
  - Overall severity (critical, major, moderate, minor).

#### 3.7.6 Sales Conversation Angles
- Auto-generate:
  - Challenge-based positioning angles for each major challenge category.
  - Specific value propositions, talking points, objections, and responses aligned to challenges.

---

### 3.8 Intelligent Capsule Generation System

#### 3.8.1 Automated Intelligence Aggregation
- For each capsule request:
  - Validate and resolve company identity.
  - Run parallel collectors across all modules.
  - Aggregate, deduplicate, classify, and score intelligence.
  - Flag missing or degraded data sources.

#### 3.8.2 Template-Based Document Generation
- Standard templates with:
  - Executive Summary.
  - Company Profile.
  - Financial Overview.
  - Leadership Profiles.
  - Strategic Priorities.
  - Recent News & Developments.
  - Challenges & Risks.
  - Sales Talking Points & Recommendations.
  - Appendices.
- Configuration options:
  - Included sections and order.
  - Detail level (summary/standard/comprehensive).
  - Coverage bias (positive-only, balanced, full including challenges).
  - Tone of sales content (consultative vs product-focused).

#### 3.8.3 Natural Language Generation
- Generate narrative text for:
  - Company, financial, news, leadership, and strategic summaries.
  - Analytic interpretations and trend descriptions.
  - Cohesive news narratives (grouping related events).
  - Professional third-person tone with clear attribution to sources.

#### 3.8.4 Talking Points & Recommendations
- For each selected challenge or opportunity:
  - Challenge description.
  - Solution relevance mapping (based on customer offerings).
  - Conversation starters and follow-up questions.
  - Supporting points and potential objections with responses.
  - Mapping to standard sales methodologies.

#### 3.8.5 Review & Customization Workflow
- Support:
  - Auto-approval mode.
  - Manager and compliance review.
  - Collaborative editing with change tracking.
  - Regeneration with modified parameters (length, emphasis, sections, format).

---

## 4. Delivery Channels & User Experiences

### 4.1 Web Application (Desktop)
- Features:
  - Company search and selection.
  - Capsule request form (depth, format, sections, sensitivity).
  - Capsule library (recent, favorites, shared).
  - Detailed module views (company, news, leadership, financial, risks).
  - Capsule editor and reviewer UI.

### 4.2 Mobile Intelligence Delivery (iOS & Android)
- Native mobile apps with:
  - Mobile-first, touch-optimized UX.
  - Feature parity for core actions (search, generate, view, annotate).
  - Offline caching of recent and downloaded capsules.
  - Background sync and push notifications:
    - Capsule generation completed.
    - High-severity new negative news for tracked accounts.
    - Meeting reminders with links to relevant capsules.
  - Capsule readers:
    - Mobile-optimized HTML for Word/PDF.
    - Slide-by-slide viewer for PowerPoint.
  - Quick intelligence views:
    - One-screen account snapshot.
    - Executive quick view.
    - Recent news mini-feed.
    - Top talking points preview.
  - Productivity features:
    - Voice search and voice commands.
    - Text-to-speech playback of capsules.
    - Meeting mode for discreet in-meeting reference.

### 4.3 Email Delivery
- Capabilities:
  - Automatic emails on capsule completion.
  - Executive summary embedded in email body.
  - Attachments: PDF, Word, PowerPoint (configurable default).
  - Links to open in web or mobile app.
  - Scheduled recurring capsule updates with change summaries.

### 4.4 Collaboration Tools (Slack, Microsoft Teams)
- Slack:
  - Bot for capsule notifications and summaries.
  - Inline previews and quick actions.
  - Slash commands to request new capsules and intelligence.
  - Channel subscriptions to key account feeds.
- Microsoft Teams:
  - Adaptive cards with capsule summaries.
  - Buttons for viewing full capsules and sections.
  - Meeting integration to surface relevant capsules for scheduled calls.
  - @mention bot for on-demand intelligence queries.

### 4.5 WhatsApp Business Integration
- Use cases:
  - Capsule-ready notifications via WhatsApp.
  - Executive summary delivered as text.
  - Links to full capsules/mobile app.
  - Request capsules by sending company name.
  - Interactive buttons for format choice, sharing, feedback.

### 4.6 CRM Integrations
- Salesforce:
  - Embedded capsule widget on Account and Opportunity records.
  - One-click capsule generation and refresh actions.
  - Activity logging of capsule events.
  - Custom fields to store capsule URLs and key metrics.
  - Flow integration to auto-generate capsules at specific opportunity stages.
- HubSpot, Dynamics 365, and others:
  - Similar patterns for embedded access, generation, and logging.

### 4.7 REST API
- Capabilities:
  - Generate, retrieve, list, update, and delete capsules.
  - Access individual intelligence components (e.g., news, financials) without full capsules.
  - OAuth2/API-key authentication and rate limiting.
  - Webhook support for event-driven integrations (capsule-complete, new high-severity news).

---

## 5. Enterprise Platform & Non-Functional Requirements

### 5.1 Analytics & Business Intelligence
- Dashboards for:
  - Capsule generation and usage volume.
  - User adoption and active users.
  - Intelligence coverage across accounts.
  - Correlation between capsule usage and sales outcomes.
  - ROI metrics and sales pipeline influence.

### 5.2 Collaboration & Task Management
- Features:
  - Shared annotations and comments on capsules.
  - Discussion threads per account or intelligence item.
  - Task assignment for research and follow-up actions.
  - Event-triggered tasks (e.g., new negative news).
  - Workflow automation for research and review processes.

### 5.3 Authentication & Security
- Requirements:
  - JWT-based authentication.
  - Multi-factor authentication (MFA).
  - Role-based access control for modules and data sensitivity.
  - Secure session management and timeouts.
  - Strong password policies (where applicable).
  - Encryption in transit (TLS) and at rest.
  - Comprehensive audit logs for access and actions.

### 5.4 Master Data Management
- Central repositories for:
  - Companies and aliases.
  - Industries and hierarchies.
  - Competitors and relationships.
  - Technologies and skills taxonomy.
  - Data sources with reliability scoring and metadata.

### 5.5 Document & File Management
- Capabilities:
  - Secure storage of capsules and intelligence exports.
  - Versioning and history of capsule edits.
  - Access controls based on user roles and sensitivity.
  - Full-text document search.
  - Integration with enterprise content management systems.

### 5.6 Real-Time Collaboration & Updates
- Use WebSockets or equivalent to:
  - Broadcast real-time updates when intelligence changes.
  - Support collaborative capsule editing and presence indicators.
  - Push high-severity event notifications to connected clients.

### 5.7 Privacy, Compliance, and Data Protection
- GDPR/CCPA and similar compliance:
  - Consent and preference management.
  - Data minimization by design.
  - Data subject rights (access, rectification, deletion, portability, restriction).
  - Documentation of legal basis for data processing.
- Data protection:
  - Field-level encryption for sensitive fields.
  - Data classification (public/internal/confidential/restricted) with handling rules.
  - Data lineage from source to capsule.

### 5.8 Backup, Disaster Recovery, and Business Continuity
- Requirements:
  - Automated daily backups and point-in-time recovery.
  - Cross-region replication for critical data.
  - Secure deletion policies for expired data.
  - Tested disaster recovery plans and documented RTO/RPO targets.
  - Business continuity practices to maintain service during disruptions.

### 5.9 Advanced Security Monitoring
- Capabilities:
  - Web application firewall (WAF).
  - Intrusion detection and prevention (IDS/IPS).
  - SIEM integration for centralized security event monitoring.
  - Regular security assessments and penetration testing.
  - Patch management and vulnerability remediation.
  - Incident response runbooks and escalation paths.

---

## 6. Implementation Notes and Roadmap Considerations (Optional)

> This section is not in the original document but summarizes how to phase delivery.

### 6.1 Recommended MVP Scope
- Web app with:
  - Company Intelligence Discovery.
  - Leadership Intelligence.
  - Long-Range News (positive/negative/neutral).
  - Basic challenge/risk classification.
  - Capsule generation to PDF and DOCX (single standard template).
  - Email delivery and basic Salesforce widget.

### 6.2 Phase 2 Enhancements
- Additional modules:
  - Financial stress indicators and funding intelligence.
  - Strategic priorities extraction.
  - Challenge-based talking point engine.
- UX & delivery:
  - Mobile apps with offline support.
  - Slack/Teams and extended CRM integrations.
  - REST API and webhooks.

### 6.3 Phase 3 – Enterprise & Compliance Maturity
- Full Sensitive News module with workflows.
- Advanced privacy, consent, and data subject rights tooling.
- Analytics dashboards for ROI and adoption.
- Backup/DR hardening and advanced security monitoring.

---

## 7. Selenium-Based Additions (flask_app & Data Ingestion)

The web app already uses Selenium (via `google_scraper.SeleniumScraper`) for:
- **Person search**: When Google/DuckDuckGo HTML returns no `site:linkedin.com/in` results, Selenium runs Google/Bing search to find LinkedIn profile URLs.
- **Organization search**: Same fallback for `site:linkedin.com/company` (Selenium used when HTML search returns no candidates).
- **Profile/org pipelines**: Full LinkedIn page fetch (Selenium or Playwright) + Groq for structured extraction.

**What you can add through Selenium** (aligned with SET spec and `flask_app.py`):

| Area | Addition | Why Selenium |
|------|----------|--------------|
| **Search & discovery** | Selenium fallback for org search when Google HTML is blocked | Already added in `_search_linkedin_org_candidates`. |
| **Company intelligence** | Scrape **BBB, Trustpilot, Yelp** company pages (reviews, ratings, complaint themes) | These sites are often JS-heavy; Selenium renders and you can extract text for sentiment/theme analysis (§3.1.7). |
| **News & filings** | Fetch **SEC EDGAR** or other JS-heavy filing/search pages | When search results or filing list are rendered by JS, Selenium can load and extract links/text. |
| **News sites** | Scrape **article body** from news URLs (for long-range news module) | Many news pages load content via JS; Selenium gets full DOM for NLG/summaries (§3.3). |
| **Company websites** | Crawl **About / Leadership / News** on target company domains | SPAs and JS-heavy corporate sites need a real browser to get visible text. |
| **Screenshots / PDF** | **Full-page screenshot** or **print-to-PDF** of a URL | Use `driver.save_screenshot()` or print PDF for capsule appendices or evidence. |
| **Resilient URL fetch** | Generic **“fetch URL with Selenium”** API | Single endpoint that, for any URL, returns rendered HTML or text when `requests` fails (blocked, CAPTCHA, or JS-only). |

**Suggested new Flask endpoints (optional):**

- `POST /api/fetch-url` — Body: `{ "url": "https://..." }`. Use Selenium to load URL and return `{ "text": "...", "title": "..." }` (and optionally screenshot path). Helps any module that needs JS-rendered content.
- `POST /api/company-reviews` — Body: `{ "company_name": "...", "source": "bbb" \| "trustpilot" \| "yelp" }`. Use Selenium to open the relevant review/complaint page, extract reviews/ratings, optionally call Groq for theme/sentiment; return structured JSON for §3.1.7 Consumer Sentiment & Reputation.

**Implementation note:** Reuse `SeleniumScraper` (or a thin wrapper) for all of the above: same headless Chrome options, same `_clean(html)`-style text extraction. For screenshot/PDF, add methods on `SeleniumScraper` such as `get_page_text(url)` and `save_screenshot(url, path)` so both the existing pipeline and new Flask routes can share one browser abstraction.

