# How to Verify Your Perplexity API Key

## Quick Verification Steps

### Step 1: Check API Key Format
Your API key should:
- Start with `pplx-`
- Be 50-60 characters long
- Have no spaces or quotes around it in the `.env` file

Run this to check:
```bash
python check_config.py
```

### Step 2: Verify API Key in Perplexity Dashboard

1. **Go to Perplexity Settings:**
   - Visit: https://www.perplexity.ai/settings/api
   - Or: https://www.perplexity.ai/settings (then click "API")

2. **Check Your API Key:**
   - Find your API key in the list
   - Verify it matches the one in your `.env` file
   - Check if it's marked as "Active" or "Enabled"

3. **Generate a New Key (if needed):**
   - If your key is expired or you're unsure, generate a new one
   - Copy the new key
   - Update your `.env` file with the new key

### Step 3: Check Account Status

1. **Verify API Access is Enabled:**
   - Some accounts may need to enable API access
   - Check if there's an "Enable API" or "Activate API" button

2. **Check Account Credits/Balance:**
   - Free tier accounts may have limited or no API access
   - Check your account balance/credits
   - You may need to upgrade to a paid plan for API access

3. **Check Usage Limits:**
   - Verify you haven't exceeded your usage limits
   - Check your API usage statistics

### Step 4: Test Your API Key

Use the test script:
```bash
python test_api_key.py
```

This will:
- Verify the API key format
- Test the connection to Perplexity API
- Show detailed error messages

### Step 5: Test with Official Perplexity Tools

1. **Use Perplexity API Key Tester:**
   - Visit: https://codeforgeek.com/free-perplexity-api-key-tester/
   - Paste your API key
   - Test if it works

2. **Check Perplexity API Documentation:**
   - Visit: https://docs.perplexity.ai/
   - Review the authentication requirements
   - Check for any recent changes

### Step 6: Common Issues and Solutions

#### Issue: HTML Response (Cloudflare)
**Symptom:** Getting HTML instead of JSON
**Solution:**
- API key is likely invalid or expired
- Generate a new API key
- Verify account has API access enabled

#### Issue: "401 Authorization Required"
**Possible Causes:**
1. API key is incorrect (typo in .env file)
2. API key has expired
3. Account doesn't have API access
4. Account has no credits
5. IP address is restricted

**Solutions:**
- Double-check the API key in `.env` file (no quotes, no spaces)
- Generate a new API key
- Check account status and credits
- Verify IP restrictions in API key settings

#### Issue: API Key Not Working
**Check:**
- Is your account on a free tier? (Free tier may not have API access)
- Do you need to upgrade to a paid plan?
- Is API access enabled for your account?

### Step 7: Contact Support

If none of the above works:
1. Check Perplexity Status: https://status.perplexity.ai
2. Contact Perplexity Support with:
   - Your API key (they can verify if it's valid)
   - Error messages you're seeing
   - Account details

## Alternative: Use Perplexity SDK

If the REST API continues to have issues, you can use the official Perplexity SDK:

```bash
pip install perplexity
```

Then in your code:
```python
from perplexity import Perplexity

client = Perplexity(api_key=os.getenv("PERPLEXITY_API_KEY"))
response = client.search.create(query="your query")
```

However, the current implementation uses the REST API which should work once your API key is valid.

## Quick Checklist

- [ ] API key starts with `pplx-`
- [ ] API key is 50-60 characters
- [ ] No quotes or spaces in `.env` file
- [ ] API key is active in Perplexity dashboard
- [ ] Account has API access enabled
- [ ] Account has sufficient credits/balance
- [ ] IP address is not restricted
- [ ] Tested with `test_api_key.py`
- [ ] Verified with Perplexity API key tester

