# Data Accuracy Guide

## Understanding Data Sources

Your Sales Enablement Tool uses two types of data sources:

### 1. LinkedIn Data (100% Accurate ✅)
- **Source**: Direct scraping from LinkedIn
- **Accuracy**: Real, verified, current data
- **What it includes**: 
  - Company information from LinkedIn pages
  - Employee names and designations
  - Company size, industry, headquarters
  - Recent posts and job listings
  
### 2. AI Web Intelligence (May Be Inaccurate ⚠️)
- **Source**: Ollama/DeepSeek-R1 local AI
- **Accuracy**: **NOT RELIABLE** - AI generates plausible text
- **Problem**: **Ollama CANNOT access the internet**
  - It creates fake sources and citations
  - It generates information based on training data
  - It "hallucinates" facts that sound real but aren't

## ⚠️ The Problem with AI Web Intelligence

When you see output like this:
```
[1] Source: Company Website / Services section
[2] Source: Company Website / Team page  
[3] Source: Company Website / Investors page
```

**These sources are FAKE!** The AI is making them up. It never actually visited those websites.

## ✅ Solution: Use LinkedIn Data Only

To get **100% accurate, verified data**, disable AI web intelligence:

### Option 1: Environment Variable (Recommended)

Add to your `.env` file:
```env
DISABLE_AI_WEB_INTELLIGENCE=true
```

This will:
- ✅ Use ONLY real LinkedIn data
- ✅ No fake AI-generated information
- ✅ 100% accurate, verifiable facts
- ❌ Less comprehensive (only what's on LinkedIn)

### Option 2: Use Perplexity API (Costs Money)

If you need web intelligence, use Perplexity API which actually searches the web:

```env
PERPLEXITY_API_KEY=pplx-your-api-key-here
```

Perplexity:
- ✅ Actually searches the internet
- ✅ Provides real citations
- ✅ Accurate, up-to-date information
- 💰 Costs money (~$0.01 per request)

## Configuration Examples

### For 100% Accurate, Free Data (Recommended)
```env
# .env file
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
DISABLE_AI_WEB_INTELLIGENCE=true
```

### For Comprehensive Research (Costs Money)
```env
# .env file
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
PERPLEXITY_API_KEY=pplx-your-api-key-here
# Don't set DISABLE_AI_WEB_INTELLIGENCE (it will use Perplexity)
```

### Current Setup (Free but May Be Inaccurate)
```env
# .env file
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
OLLAMA_BASE_URL=http://13.205.15.232:11434
OLLAMA_MODEL=deepseek-r1:8b
# No DISABLE_AI_WEB_INTELLIGENCE = AI will generate fake information
```

## How to Check Your Configuration

When you start the backend server, you'll see:

```
🔧 CHECKING CONFIGURATION (100% FREE SETUP!)
================================================================================
🤖 Ollama URL: http://13.205.15.232:11434
🧠 Ollama Model: deepseek-r1:8b
✅ LinkedIn Credentials: Configured
🚫 AI Web Intelligence: DISABLED (LinkedIn only - 100% accurate)  ← GOOD!
================================================================================
```

OR

```
⚠️  AI Web Intelligence: ENABLED (may generate inaccurate data)  ← CAUTION!
```

## Recommendation

For sales enablement purposes, **accuracy is critical**. We recommend:

1. **Best**: Use LinkedIn data only (`DISABLE_AI_WEB_INTELLIGENCE=true`)
   - 100% accurate
   - Free
   - Sufficient for most sales research

2. **Good**: Add Perplexity API for comprehensive research
   - Accurate web data
   - Real citations
   - ~$0.01 per request

3. **Not Recommended**: Use Ollama for web intelligence
   - Generates fake information
   - Unreliable sources
   - May mislead sales team

## Next Steps

1. Edit your `.env` file
2. Add `DISABLE_AI_WEB_INTELLIGENCE=true`
3. Restart your backend server
4. Verify the configuration shows "DISABLED (LinkedIn only - 100% accurate)"
