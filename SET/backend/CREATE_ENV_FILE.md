# How to Create Your .env File

## Quick Setup

1. **Create a file named `.env` in the `backend` directory**

2. **Add the following content:**
   ```
   # Google Search API (Required for non-LinkedIn data extraction)
   GOOGLE_CUSTOM_SEARCH_API_KEY=your_google_api_key_here
   GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_search_engine_id_here
   
   # LinkedIn Scraper (Required for LinkedIn data)
   LINKEDIN_EMAIL=your_linkedin_email@example.com
   LINKEDIN_PASSWORD=your_linkedin_password
   
   # Ollama Configuration (Optional - for AI analysis)
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=deepseek-r1:8b
   
   # Server Configuration
   API_HOST=0.0.0.0
   API_PORT=8000
   ```

3. **Replace the placeholder values with your actual credentials**

## Getting Your Google Custom Search API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable "Custom Search API"
4. Go to "Credentials" → "Create Credentials" → "API Key"
5. Copy your **API Key**

## Creating a Custom Search Engine

1. Go to [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" to create a new search engine
3. Enter any website (e.g., `google.com`) - this is just for setup
4. Click "Create"
5. Note your **Search Engine ID** (CX)

## Getting Your Perplexity API Key (Optional - for comprehensive capsule)

1. Go to [Perplexity AI](https://www.perplexity.ai/)
2. Sign up or log in to your account
3. Navigate to Settings → API (or visit https://www.perplexity.ai/settings/api)
4. Generate a new API key
5. Copy the API key
6. Paste it into your `.env` file

## Alternative: Use the Setup Script

**Windows:**
```bash
setup-env.bat
```

**Linux/Mac:**
```bash
chmod +x setup-env.sh
./setup-env.sh
```

## Important Notes

- Never commit the `.env` file to version control (it's already in .gitignore)
- Keep your API key secure and private
- If you get a 401 error, check that:
  - The API key is correct
  - There are no extra spaces in the .env file
  - Your account has credits/balance
  - The API key hasn't expired

## Example .env File

```
PERPLEXITY_API_KEY=pplx-1234567890abcdefghijklmnopqrstuvwxyz
API_HOST=0.0.0.0
API_PORT=8000
```

