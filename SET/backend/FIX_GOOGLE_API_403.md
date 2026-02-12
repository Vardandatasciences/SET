# How to Fix Google API 403 Error

## 🔴 Error You're Seeing:
```
Error Code: 403
Error Status: PERMISSION_DENIED
Error Message: This project does not have the access to Custom Search JSON API.
```

## ✅ Solution: Enable Google Custom Search API

### **Option 1: Enable Google Custom Search API (Recommended)**

Follow these steps to enable Google Search:

#### **Step 1: Enable the Custom Search API**
1. Go to **Google Cloud Console**: https://console.cloud.google.com/
2. Select your project (or create a new one)
3. Go to **"APIs & Services"** → **"Library"**
4. Search for **"Custom Search API"**
5. Click on it and click **"ENABLE"**

#### **Step 2: Verify API Key Has Access**
1. Go to **"APIs & Services"** → **"Credentials"**
2. Find your API key
3. Click "Edit" (pencil icon)
4. Under **"API restrictions"**:
   - Select **"Restrict key"**
   - Make sure **"Custom Search API"** is checked ✓
5. Click **"Save"**

#### **Step 3: Enable Billing (Required for Google APIs)**
⚠️ **IMPORTANT**: Even though the Custom Search API has a free tier (100 queries/day), Google requires billing to be enabled.

1. Go to **"Billing"** in Google Cloud Console
2. Link a billing account (credit card required)
3. Don't worry - you won't be charged unless you exceed the free tier

**Free Tier Limits:**
- **100 queries per day** - completely free
- After 100 queries, you'll be charged (but you can set budget alerts)

#### **Step 4: Test the API**
Restart your backend server and test again:
```bash
cd SET/backend
python main.py
```

---

### **Option 2: Use DuckDuckGo Only (Free, No API Key)**

If you don't want to set up Google API, you can rely on DuckDuckGo (free, no API key needed):

#### **Step 1: Install DuckDuckGo Search Library**
```bash
cd SET/backend
pip install -r requirements.txt
```

This will install `duckduckgo-search` which is now included in requirements.

#### **Step 2: Remove Google API Keys (Optional)**
If you don't want to use Google at all, remove these from your `.env` file:
```
# Comment out or remove:
# GOOGLE_CUSTOM_SEARCH_API_KEY=your_key_here
# GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_cse_id_here
```

#### **Step 3: Restart Backend**
```bash
python main.py
```

The system will automatically use DuckDuckGo as the primary search method.

---

### **Option 3: Mixed Approach (Best of Both Worlds)**

Keep Google API for when it works, but have solid DuckDuckGo fallback:

1. **Leave Google API keys in `.env`** (even if getting 403)
2. **Install DuckDuckGo library**:
   ```bash
   pip install -r requirements.txt
   ```
3. System will automatically fall back to DuckDuckGo when Google fails

---

## 🔍 Current Status

Based on your terminal output:
- ✅ **LinkedIn Search**: Working perfectly (found 18 profiles, filtered to 6)
- ❌ **Google Search**: 403 error (API not accessible)
- ⚠️  **DuckDuckGo Fallback**: Not working (library not installed)

---

## 📊 Comparison: Google vs DuckDuckGo

| Feature | Google Custom Search | DuckDuckGo |
|---------|---------------------|------------|
| **Cost** | Free (100/day), then $5/1000 | Completely Free |
| **Setup** | Complex (API key, CSE ID, billing) | Simple (no setup) |
| **Quality** | Excellent | Good |
| **Limit** | 100 queries/day (free) | Unlimited |
| **Speed** | Fast | Moderate |
| **Reliability** | High | Moderate |

---

## 🚀 Quick Fix (Recommended)

**Install DuckDuckGo library right now:**

```bash
cd SET/backend
pip install duckduckgo-search==6.3.5
python main.py
```

Then try your search again. DuckDuckGo will work immediately!

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'duckduckgo_search'"
**Fix:**
```bash
pip install duckduckgo-search
```

### "Google API still returns 403 after enabling API"
**Fix:**
1. Wait 5-10 minutes for changes to propagate
2. Make sure billing is enabled
3. Check API key restrictions
4. Try creating a new API key

### "DuckDuckGo returns no results"
**Fix:**
- DuckDuckGo has rate limiting
- Wait a few seconds between searches
- Results may be less comprehensive than Google

---

## ✅ Testing

After fixing, test with:
```bash
# Search for "likitha"
# Expected: Results from both LinkedIn and DuckDuckGo (or Google if enabled)
```

You should see:
```
✅ Found 6 people from all sources
📊 Source Breakdown:
   • LinkedIn Profile: 6 people
   • Google Search: 5 people (if Google works)
   or
   • DuckDuckGo: 5 people (if using DDG)
```

---

## 💡 Recommendation

**For immediate results:**
1. Run: `pip install duckduckgo-search`
2. Restart backend
3. Search will work via DuckDuckGo

**For best quality (later):**
1. Set up Google Custom Search API properly
2. Enable billing (stay within free tier)
3. Get better search quality

---

**Current Status**: LinkedIn working perfectly ✅  
**Quick Fix**: Install DuckDuckGo library for Google fallback  
**Long-term**: Set up Google API for better results
