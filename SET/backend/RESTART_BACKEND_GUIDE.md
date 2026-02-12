# How to Restart Backend with Working Search

## Current Status:
- ✅ LinkedIn search: WORKING
- ❌ Google API: 403 error (needs configuration time)
- ⚠️ DuckDuckGo: Installed but needs backend restart

## Quick Fix - Restart Backend:

**Windows PowerShell:**
```powershell
cd C:\Users\louky\Downloads\SET\SET\backend
python main.py
```

**What This Will Do:**
1. Backend will try Google API first
2. If Google fails (403), automatically falls back to DuckDuckGo
3. You can still search - results will come from LinkedIn + DuckDuckGo

## Expected Output:
```
================================================================================
🔧 CHECKING CONFIGURATION (100% FREE SETUP!)
================================================================================
🤖 Ollama URL: http://13.205.15.232:11434
🧠 Ollama Model: deepseek-r1:8b
✅ LinkedIn Credentials: Configured
⚠️  AI Web Intelligence: ENABLED
================================================================================

✅ Ollama is running and ready!
✅ Model 'deepseek-r1:8b' is available
✅ Google Custom Search API configured
✅ DuckDuckGo search available (free fallback)
```

## When You Search for "likitha":
1. LinkedIn will find profiles ✅
2. Google will try and fail with 403 ❌
3. DuckDuckGo will activate as fallback ✅
4. You'll still get results!

## To Fix Google API Permanently:

### Step 1: Remove API Key Restrictions
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click your API key
3. Under "API restrictions": Select "Don't restrict key"
4. Click "Save"

### Step 2: Wait 10 Minutes
Google needs time to propagate changes globally. Have coffee ☕

### Step 3: Test Again
```powershell
cd C:\Users\louky\Downloads\SET\SET\backend
python test_google_api.py
```

If you see "SUCCESS! Google API is working!" - you're done!

## Alternative: Just Use DuckDuckGo

If you don't want to deal with Google API:
1. Remove Google API keys from `.env` file
2. DuckDuckGo will be your primary search
3. Still works great!

---

**TL;DR:** 
- Restart backend now → Search will work with DuckDuckGo
- Remove Google API restrictions → Wait 10 min → Google will work too
