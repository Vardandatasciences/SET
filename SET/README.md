# Sales Enablement Intelligence Capsule Tool

A unified intelligence engine for sales teams conducting prospect research. This tool consolidates public information—company background, leadership, financials, public challenges, news events, and strategic priorities—and delivers an automatically generated capsule in Word, PDF, or PowerPoint format.

## Data Extraction Architecture

**The tool uses specialized services for different data sources:**
- 🔗 **LinkedIn URLs** → Direct scraping via LinkedIn Scraper (accurate, real-time data)
- 🌐 **All other sources** → Google Search API (extracts data directly from search results)
- 🤖 **AI Analysis** → Ollama (FREE, runs locally on your machine - optional)

**Benefits:**
- ✅ **Accurate** - Direct LinkedIn scraping + Google Search API for comprehensive data
- ✅ **Efficient** - Google Search API provides structured data without web scraping
- ✅ **Cost-Effective** - Google Search API: 100 free searches/day, then $5 per 1,000 searches
- ✅ **Private AI** - Ollama runs locally (optional, for AI analysis)

📖 **Quick Start**: See [FREE_SETUP_GUIDE.md](FREE_SETUP_GUIDE.md)  
📖 **Ollama Setup**: See [OLLAMA_SETUP.md](OLLAMA_SETUP.md)

## Features

### For Organizations
- **Company Intelligence Discovery**: Background, competitive pressures, regulatory challenges, market slowdowns, workforce changes, operational disruptions
- **Leadership Intelligence Extraction**: Key executives, public-facing challenges, controversies, turnover patterns
- **Executive Communications Extraction**: CEO, CFO, CTO, CIO messages, Audit Committee reports, Advisory Board guidance
- **Leadership Targets & Focus Points**: Strategic targets and priorities set by leadership team
- **Long-Range News Intelligence (7-10 years)**: Positive, negative, and neutral news with structured extraction
- **Financial Information Extraction**: Revenue trends, funding, financial stress events, risk factors
- **Strategic Priorities Extraction**: Initiatives, digital transformation, market expansion, cost reduction measures
- **Key Challenges & Risk Intelligence**: External/internal challenges, public controversies, impact assessment
- **Sales Talking Points**: Automatically generated based on identified challenges
- **Multi-Source Intelligence**: Automatically searches and consolidates data from 10+ standard sources

### For Individuals
- **Professional Background**: Current and previous positions, career history, industry expertise
- **Education**: Universities, degrees, achievements
- **Company Information**: Current company details and recent developments
- **Public Presence**: LinkedIn, articles, publications, speaking engagements
- **Professional Network**: Key connections and industry involvement
- **Recent Activity**: Latest posts, projects, public statements

## Tech Stack

- **Backend**: Python 3.9+, FastAPI
- **Frontend**: React 18, Vite
- **Data Extraction Services**: 
  - **LinkedIn Scraper** - Direct LinkedIn profile/company scraping
  - **Google Custom Search API** - Extracts data from all other sources
  - **Ollama** - FREE local AI (optional, for analyzing extracted data)
- **Document Generation**: python-docx, python-pptx
- **Browser Automation**: Playwright (for LinkedIn scraping)

## Setup Instructions

### Prerequisites
- Python 3.9 or higher
- Node.js 18 or higher
- **Google Custom Search API** (Required for non-LinkedIn data extraction)
  - Get API key: https://console.cloud.google.com/
  - Create Search Engine: https://programmablesearchengine.google.com/
- **LinkedIn credentials** (Required for LinkedIn scraping)
- **Ollama** (Optional - FREE, for AI analysis - Download from https://ollama.ai/)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Install Ollama (FREE AI):
   - **Windows/Mac**: Download from https://ollama.ai/download
   - **Linux**: `curl -fsSL https://ollama.ai/install.sh | sh`

5. Download AI model:
```bash
ollama pull deepseek-r1:latest
# OR for faster/smaller: ollama pull llama3.1:8b
```

6. Install dependencies:
```bash
pip install -r requirements.txt
python -m playwright install chromium
```

7. Create a `.env` file in the backend directory:
```env
# Google Search API (Required for non-LinkedIn data extraction)
GOOGLE_CUSTOM_SEARCH_API_KEY=your_google_api_key_here
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_search_engine_id_here

# LinkedIn Scraper (Required for LinkedIn data)
LINKEDIN_EMAIL=your_linkedin_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# Ollama Configuration (Optional - for AI analysis)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:latest

# Server Config
API_HOST=0.0.0.0
API_PORT=8000
```

**API Setup:**
- **Google Custom Search API**: Required for extracting data from non-LinkedIn sources
  - Free tier: 100 searches/day
  - Paid: $5 per 1,000 searches after free tier
- **LinkedIn**: Use a dedicated account (not your personal one)
- **Ollama**: FREE, runs locally (optional, for AI analysis)

8. Create the output directory:
```bash
mkdir output
```

9. Run the backend server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage

1. Open the application in your browser at `http://localhost:3000`
2. Select research type (Individual or Organization)
3. Enter the name of the person or organization
4. Choose output format (Word, PDF, or PowerPoint)
5. Click "Generate Intelligence Capsule"
6. Review the results and download the generated document

## API Endpoints

### POST `/api/research`
Conduct research and generate intelligence capsule.

**Request Body:**
```json
{
  "query": "Microsoft Corporation",
  "research_type": "organization",
  "output_format": "word"
}
```

**Response:**
```json
{
  "status": "success",
  "intelligence": { ... },
  "file_path": "output/Microsoft_Corporation_organization_20231215_120000.docx",
  "message": "Document generated successfully"
}
```

### GET `/api/download/{filename}`
Download generated document.

## Project Structure

```
.
├── backend/
│   ├── main.py                          # FastAPI application
│   ├── services/
│   │   ├── perplexity_service.py        # Perplexity API integration
│   │   ├── intelligence_extractor.py    # Data extraction and structuring
│   │   ├── document_generator.py        # Word/PPT/PDF generation
│   │   └── data_sources.py              # Standard data sources configuration
│   ├── requirements.txt
│   ├── .env.example
│   └── output/                          # Generated documents
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ResearchForm.jsx
│   │   │   └── ResultsDisplay.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── README.md
└── STANDARD_SEARCH_POINTS.md            # Documentation for data sources
```

For detailed information about standard search points and data sources, see [STANDARD_SEARCH_POINTS.md](STANDARD_SEARCH_POINTS.md).

## Standard Data Sources

The tool automatically searches and extracts information from the following standard sources:

### Regulatory & Financial Filings
- **SEC (U.S. Securities and Exchange Commission)**: https://www.sec.gov/search-filings
  - 10-K, 10-Q, 8-K reports, proxy statements, risk factors, executive compensation
- **SEBI (Securities and Exchange Board of India)**: https://www.sebi.gov.in/
  - Indian regulatory filings, corporate governance, compliance disclosures

### Financial News & Market Data
- **Yahoo Finance**: https://finance.yahoo.com/
  - Real-time financial data, stock prices, analyst ratings, earnings reports
- **Bloomberg Asia**: https://www.bloomberg.com/asia
  - Asian market trends, company news, economic indicators
- **Bloomberg US**: https://www.bloomberg.com/us
  - U.S. market trends, company news, economic indicators
- **Bloomberg Europe**: https://www.bloomberg.com/europe
  - European market trends, company news, economic indicators

### Investigative & Legal Sources
- **CBI (Central Bureau of Investigation)**: https://cbi.gov.in/
  - Corporate fraud investigations, corruption cases (India)
- **FBI**: https://www.fbi.gov/investigate
  - Corporate fraud, white-collar crime, cyber crimes (U.S.)

### General Information & Industry Standards
- **Wikipedia**: https://www.wikipedia.org/
  - Company history, background, notable events
- **Investopedia**: https://www.investopedia.com/
  - Industry terms, financial concepts, company analysis
- **NDTV**: https://www.ndtv.com/
  - Indian company news, business developments
- **CPCB (Central Pollution Control Board)**: https://cpcb.nic.in/
  - Industry standards, environmental compliance, industries in focus

## Data Quality Standards

All extracted intelligence follows these quality standards:
- **Paraphrased Content**: All information is paraphrased for clarity and easy understanding
- **Source Citation**: Every piece of information includes source citation in brackets (e.g., [SEC 10-K 2023])
- **No Repetition**: Information is presented once without overemphasis or redundancy
- **Balanced View**: Includes both positive developments and challenges/risks
- **Clear Language**: Written in clear, concise language suitable for sales professionals

## Notes

- **Data Extraction**: 
  - LinkedIn URLs → LinkedIn Scraper (direct scraping)
  - All other sources → Google Search API (extracts data from search results)
  - Optional: Ollama for AI analysis (FREE, runs locally)
- **Cost**: 
  - Google Search API: 100 free searches/day, then $5 per 1,000 searches
  - LinkedIn Scraper: FREE (requires credentials)
  - Ollama: FREE (optional, for AI analysis)
- **LinkedIn Scraping**: Requires LinkedIn credentials. Use a dedicated account, not your personal one. LinkedIn may restrict accounts that scrape too aggressively.
- **PDF Generation**: Requires LibreOffice or pandoc to be installed on the system.
- **Output**: Generated documents are saved in the `backend/output/` directory.
- **Data Quality**: The tool provides a balanced view including both positive developments and challenges/risks.
- **Sources**: All data is automatically sourced from 10+ standard sources plus any user-provided sources.

## Documentation

- **[FREE_SETUP_GUIDE.md](FREE_SETUP_GUIDE.md)** - Quick FREE setup guide (5 minutes)
- **[OLLAMA_SETUP.md](OLLAMA_SETUP.md)** - Detailed Ollama installation and configuration
- **[QUICK_START.md](QUICK_START.md)** - Quick reference guide
- **[SETUP.md](SETUP.md)** - General setup instructions
- **[DATA_SOURCES_QUICK_REFERENCE.md](DATA_SOURCES_QUICK_REFERENCE.md)** - Standard data sources reference

## License

This project is proprietary software.

