# Web Search & Scraping Setup Guide

This guide explains how to set up web search and scraping capabilities for companies outside of LinkedIn.

## Features

✅ **Google Custom Search API** - Primary search engine (100 free searches/day)  
✅ **DuckDuckGo** - Free fallback search (no API key needed)  
✅ **Web Scraping** - Uses Playwright to scrape any website  
✅ **Automatic Integration** - Works seamlessly with existing LinkedIn scraper

## Setup Instructions

### 1. Google Custom Search API (Recommended)

**Step 1: Create a Custom Search Engine**
1. Go to https://programmablesearchengine.google.com/
2. Click "Add" to create a new search engine
3. Enter any website (e.g., `google.com`) - this is just for setup
4. Click "Create"
5. Note your **Search Engine ID** (CX)

**Step 2: Get API Key**
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable "Custom Search API"
4. Go to "Credentials" → "Create Credentials" → "API Key"
5. Copy your **API Key**

**Step 3: Configure**
Add to your `.env` file:
```
GOOGLE_CUSTOM_SEARCH_API_KEY=your_api_key_here
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_search_engine_id_here
```

**Cost:**
- FREE: 100 searches per day
- Paid: $5 per 1,000 searches after free tier

### 2. DuckDuckGo (Optional - Free Fallback)

DuckDuckGo is automatically used as a fallback if:
- Google API is not configured
- Google API fails or quota exceeded

**No setup needed!** It works automatically.

**Optional:** Install the library for better performance:
```bash
pip install duckduckgo-search
```

If not installed, the system will use Playwright to scrape DuckDuckGo results.

## How It Works

### Scenario 1: User Provides URLs
```
User provides: "Microsoft" + URLs: [microsoft.com, news.microsoft.com]
↓
System scrapes those URLs with Playwright
↓
Extracts real content from websites
↓
Passes content to Ollama for analysis
```

### Scenario 2: User Provides No URLs
```
User provides: "Tesla Inc" (no URLs)
↓
System searches web (Google/DuckDuckGo)
↓
Gets top 5-10 relevant URLs
↓
Scrapes those URLs with Playwright
↓
Extracts real content
↓
Passes content to Ollama for analysis
```

### Scenario 3: LinkedIn URLs
```
User provides: LinkedIn company URL
↓
Uses existing LinkedIn scraper (unchanged)
```

## Environment Variables

Add to `.env`:
```env
# Google Custom Search (Optional but recommended)
GOOGLE_CUSTOM_SEARCH_API_KEY=your_key_here
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_cx_here

# Ollama (existing)
OLLAMA_BASE_URL=http://13.205.15.232:11434
OLLAMA_MODEL=deepseek-r1:8b

# Disable AI web intelligence (if you only want scraping)
DISABLE_AI_WEB_INTELLIGENCE=false
```

## Testing

1. **Test with Google API:**
   - Set up Google Custom Search API
   - Search for a company without providing URLs
   - Should see "Google Search successful" in logs

2. **Test with DuckDuckGo fallback:**
   - Remove Google API keys from .env
   - Search for a company
   - Should see "Using DuckDuckGo search" in logs

3. **Test with provided URLs:**
   - Provide a company website URL
   - Should see "Scraping URL" in logs
   - Content should be extracted and analyzed

## Troubleshooting

**Google API not working:**
- Check API key and Search Engine ID are correct
- Verify Custom Search API is enabled in Google Cloud Console
- Check quota: 100 free searches/day

**DuckDuckGo not working:**
- Install: `pip install duckduckgo-search`
- Or it will use Playwright fallback automatically

**Web scraping fails:**
- Some websites block scrapers
- Check if website requires JavaScript (Playwright handles this)
- Some sites may need delays between requests

## Cost Summary

- **Google Custom Search:** FREE (100/day) → $5/1,000 after
- **DuckDuckGo:** FREE (unlimited)
- **Web Scraping:** FREE (uses existing Playwright)
- **Ollama:** FREE (local AI)

**Total cost for small usage:** $0 (using free tiers)
