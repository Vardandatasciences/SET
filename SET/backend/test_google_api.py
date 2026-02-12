"""
Test script to verify Google Custom Search API is working
Run this to check if your API key is properly configured
"""

import os
import httpx
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_google_api():
    """Test Google Custom Search API"""
    api_key = os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
    cse_id = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
    
    print("\n" + "="*80)
    print("TESTING GOOGLE CUSTOM SEARCH API")
    print("="*80)
    
    # Check configuration
    if not api_key:
        print("ERROR: GOOGLE_CUSTOM_SEARCH_API_KEY is not set in .env file")
        return False
    
    if not cse_id:
        print("ERROR: GOOGLE_CUSTOM_SEARCH_ENGINE_ID is not set in .env file")
        return False
    
    print(f"OK: API Key found: {api_key[:10]}...{api_key[-4:]}")
    print(f"OK: Search Engine ID found: {cse_id[:10]}...{cse_id[-4:]}")
    
    # Test API call
    print("\nTesting API call with query: 'test'...")
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
                print("SUCCESS! Google API is working!")
                data = response.json()
                results = data.get("items", [])
                print(f"Found {len(results)} search result(s)")
                if results:
                    print(f"   First result: {results[0].get('title', 'N/A')}")
                return True
            else:
                print(f"FAILED with status code: {response.status_code}")
                try:
                    error_data = response.json()
                    error_info = error_data.get("error", {})
                    print(f"\nError Details:")
                    print(f"   Code: {error_info.get('code', 'N/A')}")
                    print(f"   Status: {error_info.get('status', 'N/A')}")
                    print(f"   Message: {error_info.get('message', 'N/A')}")
                    
                    if response.status_code == 403:
                        print(f"\nFix for 403 Error:")
                        print(f"   1. Go to: https://console.cloud.google.com/apis/credentials")
                        print(f"   2. Click on your API key")
                        print(f"   3. Try 'Don't restrict key' (temporarily)")
                        print(f"   4. Click 'Save'")
                        print(f"   5. Wait 5-10 minutes for changes to propagate")
                        print(f"   6. Run this test again")
                except:
                    print(f"   Raw response: {response.text[:200]}")
                
                return False
    
    except Exception as e:
        print(f"ERROR: Exception occurred: {str(e)}")
        return False

async def test_duckduckgo():
    """Test DuckDuckGo search"""
    print("\n" + "="*80)
    print("TESTING DUCKDUCKGO SEARCH")
    print("="*80)
    
    try:
        # Try new ddgs library first
        try:
            from ddgs import DDGS
            print("OK: ddgs library is installed (new)")
        except ImportError:
            # Fallback to old library
            from duckduckgo_search import DDGS
            print("OK: duckduckgo-search library is installed (old)")
        
        print("\nTesting DuckDuckGo search with query: 'test'...")
        ddgs = DDGS()
        results = list(ddgs.text("test", max_results=3))
        
        if results:
            print(f"SUCCESS! DuckDuckGo is working!")
            print(f"Found {len(results)} search result(s)")
            print(f"   First result: {results[0].get('title', 'N/A')}")
            return True
        else:
            print("WARNING: No results returned")
            return False
    
    except ImportError:
        print("ERROR: Neither ddgs nor duckduckgo-search library is installed")
        print("   Install with: pip install ddgs")
        return False
    except Exception as e:
        print(f"ERROR: Exception occurred: {str(e)}")
        import traceback
        print(f"   Details: {traceback.format_exc()[:200]}")
        return False

async def main():
    """Run all tests"""
    import sys
    import codecs
    
    # Fix Windows console encoding
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
    
    print("\n" + "="*80)
    print("SEARCH API TESTING TOOL")
    print("="*80)
    print("This script will test both Google and DuckDuckGo search APIs")
    print("="*80)
    
    # Test Google
    google_works = await test_google_api()
    
    # Test DuckDuckGo
    duckduckgo_works = await test_duckduckgo()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Google Custom Search API: {'WORKING' if google_works else 'NOT WORKING'}")
    print(f"DuckDuckGo Search:        {'WORKING' if duckduckgo_works else 'NOT WORKING'}")
    print("="*80)
    
    if google_works:
        print("\nYour Google API is working perfectly!")
        print("   Your backend should now be able to search with Google.")
    elif duckduckgo_works:
        print("\nDuckDuckGo is working as a fallback!")
        print("   Your backend can search using DuckDuckGo.")
        print("   To fix Google API, follow the steps above.")
    else:
        print("\nNeither search method is working.")
        print("   Please install DuckDuckGo: pip install duckduckgo-search")
    
    print("\nNext step: Restart your backend server")
    print("   cd SET/backend")
    print("   python main.py")
    print()

if __name__ == "__main__":
    asyncio.run(main())
