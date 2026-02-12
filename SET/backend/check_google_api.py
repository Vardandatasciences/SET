"""
Script to check if the Google Custom Search API is configured correctly
"""
import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_google_api():
    """Test Google Custom Search API configuration"""
    api_key = os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
    cse_id = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
    
    print("=" * 80)
    print("Google Custom Search API Configuration Check")
    print("=" * 80)
    print()
    
    # Check if variables are set
    if not api_key:
        print("[ERROR] GOOGLE_CUSTOM_SEARCH_API_KEY is not set!")
        print()
        print("Please add to your .env file:")
        print("GOOGLE_CUSTOM_SEARCH_API_KEY=your_api_key_here")
        return False
    
    if not cse_id:
        print("[ERROR] GOOGLE_CUSTOM_SEARCH_ENGINE_ID is not set!")
        print()
        print("Please add to your .env file:")
        print("GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_search_engine_id_here")
        print()
        print("Get your Search Engine ID from: https://programmablesearchengine.google.com/")
        return False
    
    print("[OK] Both API key and Search Engine ID are set")
    print(f"   API Key: {'*' * 20}...{api_key[-4:] if len(api_key) > 4 else '****'}")
    print(f"   Search Engine ID: {cse_id[:10]}...{cse_id[-4:] if len(cse_id) > 14 else cse_id}")
    print()
    
    # Test the API
    print("Testing Google Custom Search API...")
    print("-" * 80)
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": "test",
        "num": 1
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                print("[✅ SUCCESS] Google Custom Search API is working!")
                data = response.json()
                if "items" in data:
                    print(f"   Found {len(data.get('items', []))} test result(s)")
                return True
            elif response.status_code == 403:
                error_data = response.json() if response.text else {}
                error_info = error_data.get("error", {})
                error_msg = error_info.get("message", "Unknown error")
                error_code = error_info.get("code", response.status_code)
                
                print(f"[❌ ERROR] API returned 403 PERMISSION_DENIED")
                print(f"   Error Code: {error_code}")
                print(f"   Error Message: {error_msg}")
                print()
                print("🔧 TROUBLESHOOTING STEPS:")
                print()
                print("1. Check API Key Restrictions:")
                print("   → Go to: https://console.cloud.google.com/apis/credentials")
                print("   → Click on your API key")
                print("   → Under 'API restrictions':")
                print("     • If 'Restrict key' is selected, ensure 'Custom Search API' is in the list")
                print("     • OR set to 'Don't restrict key' (for testing)")
                print()
                print("2. Enable Billing (Required even for free tier):")
                print("   → Go to: https://console.cloud.google.com/billing")
                print("   → Link a billing account to your project")
                print("   → You won't be charged for the first 100 searches/day")
                print()
                print("3. Verify API Key Project:")
                print("   → Ensure the API key was created in the same project where")
                print("     Custom Search API is enabled (SET-tool)")
                print()
                print("4. Verify Custom Search API is enabled:")
                print("   → Go to: https://console.cloud.google.com/apis/library/customsearch.googleapis.com")
                print("   → Ensure it shows 'API Enabled'")
                print()
                print("5. ⚠️  ACCOUNT VERIFICATION (Most Common Issue):")
                print("   → If you see 'Account verification under review' in Google Cloud Console,")
                print("     Google may be blocking API access during the review process")
                print("   → This can take a few days to complete")
                print("   → Check: https://console.cloud.google.com/apis/library/customsearch.googleapis.com")
                print("   → Look for any yellow warning banners about account verification")
                print("   → Google will email you when verification is complete")
                print()
                print("6. Verify API Key Project Match:")
                print("   → Ensure your API key was created in the 'SET-tool' project")
                print("   → Check: https://console.cloud.google.com/apis/credentials")
                print("   → Click on your API key and verify the project name matches")
                return False
            elif response.status_code == 400:
                error_data = response.json() if response.text else {}
                error_info = error_data.get("error", {})
                error_msg = error_info.get("message", "Unknown error")
                print(f"[❌ ERROR] Bad Request (400)")
                print(f"   Error Message: {error_msg}")
                print()
                print("   This usually means:")
                print("   • Search Engine ID (CX) is incorrect")
                print("   • API key format is invalid")
                return False
            else:
                error_data = response.json() if response.text else {}
                error_info = error_data.get("error", {})
                error_msg = error_info.get("message", response.text)
                print(f"[❌ ERROR] API returned status {response.status_code}")
                print(f"   Error Message: {error_msg}")
                return False
                
    except Exception as e:
        print(f"[❌ ERROR] Failed to connect to Google API: {e}")
        return False
    
    print()
    print("=" * 80)


async def main():
    """Run the check"""
    result = await test_google_api()
    
    if result:
        print("\n✅ Your Google Custom Search API is configured correctly!")
        print("   The system will use Google Search when available.")
    else:
        print("\n⚠️  Google Custom Search API is not working.")
        print("   The system will automatically use DuckDuckGo as fallback.")
        print("   (DuckDuckGo works without any API keys)")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())
