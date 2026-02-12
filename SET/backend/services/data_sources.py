"""
Standard data sources and search points for intelligence gathering
"""

# Standard executive roles to search for messages and communications
EXECUTIVE_ROLES = [
    "CEO",
    "CFO", 
    "CTO",
    "CIO",
    "Audit Committee Chair",
    "Advisory Board Members"
]

# Standard data sources for comprehensive research
STANDARD_DATA_SOURCES = {
    "company_websites_and_profiles": [
        {
            "name": "Official Company Website",
            "url": "[company-domain].com or .in",
            "description": "Primary source: company's official website pages (/about, /team, /leadership, /contact, /services, /news)",
            "focus": "Real company information, leadership team names, office locations, services, company background, recent news"
        },
        {
            "name": "LinkedIn Company Page",
            "url": "https://www.linkedin.com/company/",
            "description": "Company's LinkedIn profile and recent posts",
            "focus": "Company updates, employee count, recent posts, company news, leadership profiles"
        },
        {
            "name": "LinkedIn Individual Profiles",
            "url": "https://www.linkedin.com/in/",
            "description": "Individual LinkedIn profiles of executives and employees",
            "focus": "Real names, job titles, work history, education, recent activity"
        }
    ],
    "regulatory_and_financial": [
        {
            "name": "SEC (U.S. Securities and Exchange Commission)",
            "url": "https://www.sec.gov/search-filings",
            "description": "U.S. regulatory filings, 10-K, 10-Q, 8-K reports, proxy statements",
            "focus": "Financial data, risk factors, executive compensation, legal proceedings"
        },
        {
            "name": "SEBI (Securities and Exchange Board of India)",
            "url": "https://www.sebi.gov.in/",
            "description": "Indian regulatory filings and disclosures",
            "focus": "Indian company financials, compliance, corporate governance"
        }
    ],
    "financial_news": [
        {
            "name": "Yahoo Finance",
            "url": "https://finance.yahoo.com/",
            "description": "Financial data, stock prices, company news",
            "focus": "Real-time financial data, analyst ratings, earnings reports"
        },
        {
            "name": "Bloomberg Asia",
            "url": "https://www.bloomberg.com/asia",
            "description": "Financial news and analysis for Asian markets",
            "focus": "Asian market trends, company news, economic indicators"
        },
        {
            "name": "Bloomberg US",
            "url": "https://www.bloomberg.com/us",
            "description": "Financial news and analysis for U.S. markets",
            "focus": "U.S. market trends, company news, economic indicators"
        },
        {
            "name": "Bloomberg Europe",
            "url": "https://www.bloomberg.com/europe",
            "description": "Financial news and analysis for European markets",
            "focus": "European market trends, company news, economic indicators"
        }
    ],
    "investigative_and_legal": [
        {
            "name": "CBI (Central Bureau of Investigation)",
            "url": "https://cbi.gov.in/",
            "description": "Indian investigation agency",
            "focus": "Corporate fraud investigations, corruption cases"
        },
        {
            "name": "FBI",
            "url": "https://www.fbi.gov/investigate",
            "description": "U.S. Federal Bureau of Investigation",
            "focus": "Corporate fraud, white-collar crime, cyber crimes"
        }
    ],
    "general_information": [
        {
            "name": "Wikipedia",
            "url": "https://www.wikipedia.org/",
            "description": "General encyclopedia",
            "focus": "Company history, background, notable events"
        },
        {
            "name": "Investopedia",
            "url": "https://www.investopedia.com/",
            "description": "Financial education and definitions",
            "focus": "Industry terms, financial concepts, company analysis"
        }
    ],
    "news_media": [
        {
            "name": "NDTV",
            "url": "https://www.ndtv.com/",
            "description": "Indian news media",
            "focus": "Indian company news, business developments, controversies"
        }
    ],
    "industry_and_environment": [
        {
            "name": "CPCB (Central Pollution Control Board)",
            "url": "https://cpcb.nic.in/",
            "description": "Indian environmental regulatory body",
            "focus": "Industry standards, environmental compliance, industries in focus"
        }
    ]
}

# Standard search points for organization research
ORGANIZATION_SEARCH_POINTS = [
    {
        "category": "Executive Communications",
        "points": [
            "CEO message to shareholders",
            "CEO letter in annual report",
            "CFO financial outlook and commentary",
            "CTO technology vision and roadmap",
            "CIO digital transformation initiatives",
            "Audit committee report and findings",
            "Advisory board recommendations and guidance"
        ]
    },
    {
        "category": "Leadership Strategy",
        "points": [
            "Company targets set by leadership",
            "Focus points and priorities announced by executives",
            "Strategic initiatives and goals",
            "Vision statements from leadership team",
            "Multi-year plans and roadmaps"
        ]
    },
    {
        "category": "Company News",
        "points": [
            "Recent company announcements and press releases",
            "Product launches and developments",
            "Partnership and acquisition news",
            "Expansion and growth initiatives",
            "Restructuring and organizational changes",
            "Awards and recognitions",
            "Legal proceedings and regulatory actions",
            "Financial results and guidance",
            "Leadership appointments and departures",
            "Controversies and crisis events"
        ]
    }
]

# Data quality requirements
DATA_QUALITY_REQUIREMENTS = {
    "paraphrasing": "All extracted data must be paraphrased for clarity and easy understanding",
    "no_repetition": "Avoid repetition or overemphasis on the same topics",
    "source_citation": "Always mention the source in brackets after each piece of information",
    "clarity": "Present information in clear, concise language suitable for sales professionals",
    "structure": "Organize information logically with proper headings and sections",
    "balance": "Include both positive and negative aspects for balanced view"
}

def get_all_source_urls():
    """
    Get a list of all standard source URLs
    """
    urls = []
    for category in STANDARD_DATA_SOURCES.values():
        for source in category:
            urls.append(source["url"])
    return urls

def get_source_description(url):
    """
    Get description for a given source URL
    """
    for category in STANDARD_DATA_SOURCES.values():
        for source in category:
            if source["url"] == url:
                return f"{source['name']} - {source['description']}"
    return url

def format_sources_for_prompt():
    """
    Format all data sources for inclusion in research prompts
    """
    sections = []
    
    for category_name, sources in STANDARD_DATA_SOURCES.items():
        category_title = category_name.replace("_", " ").title()
        sources_text = "\n".join([
            f"   - {source['name']} ({source['url']}): {source['description']}"
            for source in sources
        ])
        sections.append(f"\n{category_title}:\n{sources_text}")
    
    return "\n".join(sections)

def format_search_points_for_prompt():
    """
    Format search points for inclusion in research prompts
    """
    sections = []
    
    for section in ORGANIZATION_SEARCH_POINTS:
        category = section["category"]
        points = "\n".join([f"   - {point}" for point in section["points"]])
        sections.append(f"\n{category}:\n{points}")
    
    return "\n".join(sections)

