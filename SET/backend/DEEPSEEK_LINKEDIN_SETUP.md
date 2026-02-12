# DeepSeek + LinkedIn Scraper Integration Setup

## Overview

The SET (Sales Enablement Tool) now uses an intelligent routing system:

- **DeepSeek AI** → For all non-LinkedIn web sources
- **LinkedIn Scraper** → For LinkedIn profiles and company pages
- **Perplexity AI** → Optional fallback if DeepSeek fails

## Architecture

```
User Request
    ↓
Unified Intelligence Service
    ↓
    ├─→ LinkedIn URL? → LinkedIn Scraper → Direct scraping
    │
    └─→ Other sources? → DeepSeek AI → Web intelligence
```

## Required Configuration

### 1. DeepSeek API Key (Primary - Required)

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

**Get your key:**
- Visit: https://platform.deepseek.com/
- Sign up for an account
- Generate API key
- Cost-effective pricing for web intelligence

### 2. LinkedIn Credentials (Recommended)

```env
LINKEDIN_EMAIL=your_linkedin_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password
```

**Important Notes:**
- Use a **dedicated LinkedIn account**, not your personal one
- LinkedIn may restrict accounts that scrape aggressively
- Follow LinkedIn's rate limiting and terms of service
- The scraper uses Playwright to automate browser interactions

### 3. Perplexity API Key (Optional - Fallback)

```env
PERPLEXITY_API_KEY=your_perplexity_api_key_here
```

**When to use:**
- As a fallback if DeepSeek is unavailable
- If you already have a Perplexity subscription
- Not required if DeepSeek is configured

## Installation Steps

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `playwright==1.49.0` - For LinkedIn scraping
- `openai==1.59.0` - For DeepSeek API (OpenAI-compatible)

### 2. Install Playwright Browsers

```bash
python -m playwright install chromium
```

This downloads the Chromium browser needed for LinkedIn scraping.

### 3. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Primary AI Service (Required)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# LinkedIn Scraper (Recommended)
LINKEDIN_EMAIL=your_linkedin_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# Fallback (Optional)
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Server Config
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Run the Server

```bash
python main.py
```

The server will check your configuration on startup and show:
```
🔧 CHECKING CONFIGURATION
================================================================================
✅ DeepSeek API Key: Configured
✅ Perplexity API Key: Configured (fallback)
✅ LinkedIn Credentials: Configured
================================================================================
```

## How It Works

### For Individual Research

**With LinkedIn URL:**
```json
{
  "query": "John Doe",
  "research_type": "individual",
  "sources": [
    {
      "name": "LinkedIn Profile",
      "link": "https://www.linkedin.com/in/johndoe/"
    }
  ]
}
```

**Processing:**
1. ✅ Detects LinkedIn URL
2. 🔍 Scrapes LinkedIn profile directly (accurate, real-time data)
3. 🤖 Uses DeepSeek to find additional web intelligence
4. 🔄 Combines both sources into comprehensive report

**Without LinkedIn URL:**
```json
{
  "query": "John Doe",
  "research_type": "individual"
}
```

**Processing:**
1. 🤖 Uses DeepSeek to search across the web
2. 📊 Returns comprehensive profile from public sources

### For Organization Research

**With LinkedIn Company URL:**
```json
{
  "query": "Microsoft Corporation",
  "research_type": "organization",
  "sources": [
    {
      "name": "LinkedIn Company",
      "link": "https://www.linkedin.com/company/microsoft/"
    },
    {
      "name": "Company Website",
      "link": "https://www.microsoft.com"
    }
  ]
}
```

**Processing:**
1. ✅ Detects LinkedIn company URL
2. 🔍 Scrapes LinkedIn company page (employees, about, size, etc.)
3. 🤖 Uses DeepSeek for company website and other sources
4. 🔄 Combines for comprehensive intelligence

## Service Files Created

### New Files

1. **`services/deepseek_service.py`**
   - DeepSeek AI integration
   - Handles all non-LinkedIn web sources
   - OpenAI-compatible API client

2. **`services/linkedin_scraper_service.py`**
   - LinkedIn scraper integration
   - Person profile scraping
   - Company page scraping
   - Data transformation for SET

3. **`services/unified_intelligence_service.py`**
   - Main routing service
   - Intelligent source detection
   - Combines LinkedIn + DeepSeek data
   - Fallback handling

### Modified Files

1. **`main.py`**
   - Uses `UnifiedIntelligenceService` instead of `PerplexityService`
   - Enhanced configuration checking
   - Updated health endpoint

2. **`requirements.txt`**
   - Added `playwright==1.49.0`
   - Added `openai==1.59.0`

## Testing

### Check Configuration

```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "healthy",
  "api_keys_configured": {
    "deepseek": true,
    "perplexity": true,
    "linkedin": true
  },
  "services": {
    "unified_intelligence_service": "initialized",
    "deepseek_service": "available",
    "linkedin_scraper": "available",
    "perplexity_fallback": "available",
    "intelligence_extractor": "initialized",
    "document_generator": "initialized",
    "intelligence_capsule_service": "initialized"
  }
}
```

### Test Individual Research

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Satya Nadella",
    "research_type": "individual",
    "sources": [
      {
        "name": "LinkedIn",
        "link": "https://www.linkedin.com/in/satyanadella/"
      }
    ]
  }'
```

### Test Organization Research

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Microsoft Corporation",
    "research_type": "organization",
    "sources": [
      {
        "name": "LinkedIn",
        "link": "https://www.linkedin.com/company/microsoft/"
      }
    ]
  }'
```

## Benefits

### 1. Cost Efficiency
- **DeepSeek**: More cost-effective than Perplexity
- Pay only for what you use
- No need for expensive subscriptions

### 2. Accurate LinkedIn Data
- **Direct scraping**: Real-time, accurate data
- No reliance on third-party APIs
- Complete profile information

### 3. Comprehensive Intelligence
- **Best of both worlds**: LinkedIn + Web intelligence
- Combines structured (LinkedIn) + unstructured (web) data
- Single comprehensive report

### 4. Intelligent Routing
- **Automatic detection**: Knows when to use which service
- No manual configuration per request
- Seamless integration

## Troubleshooting

### DeepSeek API Errors

**Error:** `Authentication failed (401)`
- ✅ Check `DEEPSEEK_API_KEY` in `.env`
- ✅ Verify key starts with correct prefix
- ✅ Check account has credits

### LinkedIn Scraper Issues

**Error:** `LinkedIn credentials not configured`
- ✅ Set `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` in `.env`
- ✅ Verify credentials are correct

**Error:** `Login failed` or `Rate limit`
- ⚠️ LinkedIn may be blocking the account
- 💡 Use a different account
- 💡 Wait before retrying (LinkedIn rate limits)
- 💡 Use residential proxies if needed

**Error:** `Playwright browser not installed`
```bash
python -m playwright install chromium
```

### Fallback to Perplexity

If DeepSeek fails, the system will automatically fallback to Perplexity if configured.

Check logs for:
```
⚠️  DeepSeek not available, falling back to Perplexity
```

## Best Practices

### 1. LinkedIn Scraping
- ✅ Use dedicated accounts
- ✅ Respect rate limits (don't scrape too fast)
- ✅ Monitor for blocks/restrictions
- ✅ Consider using proxies for production

### 2. API Keys
- ✅ Never commit `.env` to version control
- ✅ Use environment variables in production
- ✅ Rotate keys periodically
- ✅ Monitor usage and costs

### 3. Error Handling
- ✅ Configure fallback (Perplexity)
- ✅ Monitor logs for failures
- ✅ Set up alerts for repeated failures

## Cost Comparison

| Service | Cost | Use Case |
|---------|------|----------|
| **DeepSeek** | $0.14-0.28 per 1M tokens | Primary web intelligence |
| **LinkedIn Scraper** | Free (requires account) | LinkedIn profiles/companies |
| **Perplexity** | $5-20/month or per-token | Fallback only |

**Recommendation:** DeepSeek + LinkedIn Scraper = Best value and accuracy

## Support

For issues or questions:
1. Check logs in terminal
2. Verify `.env` configuration
3. Test with `/api/health` endpoint
4. Review this documentation

## Future Enhancements

Planned features:
- [ ] Proxy rotation for LinkedIn scraping
- [ ] Rate limiting and retry logic
- [ ] Caching for repeated queries
- [ ] Additional AI providers
- [ ] Batch processing support
