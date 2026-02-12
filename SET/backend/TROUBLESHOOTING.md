# Troubleshooting Guide

## 401 Authorization Required Error

**IMPORTANT:** If you're getting an HTML response (with Cloudflare script), this **strongly indicates your API key is invalid, expired, or your account doesn't have API access enabled.**

If you're getting a `401 Authorization Required` error, follow these steps:

> **See `VERIFY_API_KEY.md` for a comprehensive verification guide.**

### Step 1: Verify Your API Key

Run the configuration check script:
```bash
python check_config.py
```

This will tell you if your API key is set correctly.

### Step 2: Check Your API Key Validity

**CRITICAL:** If you're getting HTML responses, your API key is likely invalid.

1. Go to [Perplexity AI Settings](https://www.perplexity.ai/settings/api)
2. Verify your API key is active and matches the one in your `.env` file
3. Check if it has expired or been revoked
4. **Generate a NEW API key** if you're unsure
5. Update your `.env` file with the new key (no quotes, no spaces)
6. **Check if your account has API access enabled** (free tier may not have access)
7. **Verify your account has credits/balance**

### Step 3: Check Account Credits

1. Log in to your Perplexity account
2. Check your account balance/credits
3. If credits are depleted, purchase additional credits
4. Free tier accounts may have limited API access

### Step 4: Verify IP Restrictions

Some API keys are restricted to specific IP addresses:
1. Check your API key settings in the Perplexity dashboard
2. Ensure your current IP address is authorized
3. If using a VPN, try disabling it or adding the VPN IP to allowed IPs

### Step 5: Verify .env File Format

Your `.env` file should look like this (no quotes, no spaces around the `=`):

```
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
API_HOST=0.0.0.0
API_PORT=8000
```

**Common mistakes:**
- ❌ `PERPLEXITY_API_KEY="pplx-xxx"` (quotes not needed)
- ❌ `PERPLEXITY_API_KEY = pplx-xxx` (spaces around =)
- ❌ `PERPLEXITY_API_KEY= pplx-xxx` (space after =)
- ✅ `PERPLEXITY_API_KEY=pplx-xxx` (correct)

### Step 6: Test API Key Directly

You can test your API key using curl:

```bash
curl https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.1-sonar-large-128k-online",
    "messages": [
      {
        "role": "user",
        "content": "Hello"
      }
    ]
  }'
```

Replace `YOUR_API_KEY` with your actual API key.

### Step 7: Check Server Logs

When you run the server, it will show warnings if the API key is missing:
```
WARNING: PERPLEXITY_API_KEY not found in environment variables!
```

### Still Having Issues?

1. **Double-check the API key**: Copy it directly from the Perplexity dashboard
2. **Try a new API key**: Generate a fresh one and update your `.env` file
3. **Check Perplexity status**: Visit [Perplexity Status Page](https://status.perplexity.ai/) to see if there are any service issues
4. **Contact Perplexity Support**: If none of the above works, contact Perplexity support with your API key (they can check if it's valid)

## Other Common Errors

### Import Errors
- Make sure you've installed all requirements: `pip install -r requirements.txt`
- Activate your virtual environment before running

### Port Already in Use
- Change the port in `.env`: `API_PORT=8001`
- Or stop the process using port 8000

### Module Not Found
- Ensure you're in the backend directory when running the server
- Check that all dependencies are installed in the correct Python environment

