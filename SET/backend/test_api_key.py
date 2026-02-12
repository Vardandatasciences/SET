"""
Test script to verify Perplexity API key and endpoint
"""
import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_perplexity_api():
    api_key = os.getenv("PERPLEXITY_API_KEY")
    
    if not api_key:
        print("ERROR: PERPLEXITY_API_KEY not found in .env file")
        return
    
    # Clean the API key
    api_key = api_key.strip().strip('"').strip("'")
    
    print("=" * 60)
    print("Testing Perplexity API Connection")
    print("=" * 60)
    print(f"API Key: {api_key[:15]}... (length: {len(api_key)})")
    print(f"Starts with 'pplx-': {api_key.startswith('pplx-')}")
    print()
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Try different model names to find one that works
    models_to_try = [
        "sonar",
        "sonar-pro",
        "sonar-online",
        "pplx-7b-online",
        "pplx-70b-online",
        "llama-3.1-sonar-large-128k-online"  # Fallback
    ]
    
    print(f"Endpoint: {url}")
    print(f"Testing models: {', '.join(models_to_try[:3])}...")
    print()
    print("Sending test request...")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            last_error = None
            for model in models_to_try:
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Say hello"
                        }
                    ],
                    "max_tokens": 10
                }
                
                try:
                    print(f"Trying model: {model}...")
                    response = await client.post(url, headers=headers, json=payload)
                    
                    print(f"Status Code: {response.status_code}")
                    print()
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"✅ SUCCESS! Model '{model}' is working. API key is valid.")
                        print(f"Response: {result.get('choices', [{}])[0].get('message', {}).get('content', '')}")
                        return  # Exit on success
                    elif response.status_code == 401:
                        print(f"❌ FAILED: 401 Unauthorized with model '{model}'")
                        print()
                        response_text = response.text
                        if "<html>" in response_text.lower():
                            print("Received HTML response (likely Cloudflare protection)")
                            print()
                            print("This strongly suggests your API key is INVALID or EXPIRED.")
                            print()
                            print("ACTION REQUIRED:")
                            print("1. Go to https://www.perplexity.ai/settings/api")
                            print("2. Verify your API key is active")
                            print("3. Generate a NEW API key if needed")
                            print("4. Update your .env file with the new key")
                            print("5. Check if your account has API access enabled")
                            print("6. Verify your account has credits/balance")
                            print()
                            print("NOTE: Free tier accounts may not have API access.")
                            print("      You may need to upgrade to a paid plan.")
                            return  # Exit on 401
                        else:
                            print(f"Response: {response_text[:500]}")
                            print()
                            print("Check:")
                            print("  - API key is correct (no typos)")
                            print("  - API key hasn't expired")
                            print("  - Account has sufficient credits")
                            print("  - IP address is not restricted")
                            return  # Exit on 401
                    elif response.status_code == 400:
                        # Model not found, try next one
                        error_data = response.json() if response.text else {}
                        error_msg = error_data.get('error', {}).get('message', response.text[:200])
                        last_error = f"Model '{model}' not found (400): {error_msg}"
                        print(f"  ⚠️  Model '{model}' not available, trying next...")
                        continue  # Try next model
                    else:
                        last_error = f"Status {response.status_code}: {response.text[:200]}"
                        print(f"  ⚠️  Error with model '{model}' (status {response.status_code}), trying next...")
                        continue  # Try next model
                        
                except Exception as e:
                    last_error = f"Exception with model '{model}': {str(e)}"
                    print(f"  ⚠️  Exception with model '{model}': {str(e)[:100]}")
                    continue  # Try next model
            
            # If we get here, all models failed
            print()
            print(f"❌ All model attempts failed. Last error: {last_error}")
            print()
            print("Please check:")
            print("1. Perplexity API documentation for current model names")
            print("2. Visit: https://docs.perplexity.ai/getting-started/models")
            print("3. Your API key may need a different model or plan")
                
    except Exception as e:
        print(f"ERROR: {str(e)}")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_perplexity_api())

