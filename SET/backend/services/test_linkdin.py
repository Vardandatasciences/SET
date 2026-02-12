"""
Test Script: Verify Perplexity API can fetch LinkedIn URLs

Run this script to test if Perplexity API can access LinkedIn profiles.

Usage:
    python test_linkedin_perplexity.py

Make sure to set PERPLEXITY_API_KEY in your .env file or environment.
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("PERPLEXITY_API_KEY")
TEST_LINKEDIN_URL = "https://www.linkedin.com/in/sajindal/"  # Change this to test


async def test_method_1_direct_url():
    """
    Method 1: Direct URL query (like pasting URL in Perplexity website)
    """
    print("\n" + "="*70)
    print("TEST 1: Direct URL Query (mimics Perplexity website)")
    print("="*70)
    
    prompt = f"""Visit this LinkedIn profile and tell me about this person:
{TEST_LINKEDIN_URL}

Extract:
1. Their full name
2. Current job title
3. Current company
4. Location
5. A brief summary of their experience"""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sonar-pro",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"\n✅ Response received ({len(content)} chars):")
            print("-"*70)
            print(content[:2000])
            if len(content) > 2000:
                print(f"\n... (truncated, {len(content) - 2000} more chars)")
            return content
        else:
            print(f"\n❌ Error {response.status_code}: {response.text[:500]}")
            return None


async def test_method_2_explicit_fetch():
    """
    Method 2: Explicitly ask to fetch/browse the URL
    """
    print("\n" + "="*70)
    print("TEST 2: Explicit Fetch Request")
    print("="*70)
    
    prompt = f"""I need you to browse to this LinkedIn URL and extract the profile information:

URL to visit: {TEST_LINKEDIN_URL}

Please go to this URL and extract:
- Full Name (exactly as shown on profile)
- Headline (text below their name)
- Current Position (title and company)
- Location
- About section (if visible)
- Last 3 work experiences with dates

This is the specific LinkedIn profile I need information about. Do not search for other profiles."""

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sonar-pro",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a research assistant with web browsing capabilities. When given a URL, visit it directly and extract the requested information."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"\n✅ Response received ({len(content)} chars):")
            print("-"*70)
            print(content[:2000])
            return content
        else:
            print(f"\n❌ Error {response.status_code}: {response.text[:500]}")
            return None


async def test_method_3_search_with_url():
    """
    Method 3: Search with URL as context
    """
    print("\n" + "="*70)
    print("TEST 3: Search with URL Context")
    print("="*70)
    
    prompt = f"""Research the person at this LinkedIn profile: {TEST_LINKEDIN_URL}

Who is this person? What is their current role and company? 
Provide details from their LinkedIn profile."""

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sonar",  # Try regular sonar
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "search_recency_filter": "week"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = result.get("citations", [])
            print(f"\n✅ Response received ({len(content)} chars)")
            print(f"📚 Citations: {citations}")
            print("-"*70)
            print(content[:2000])
            return content
        else:
            print(f"\n❌ Error {response.status_code}: {response.text[:500]}")
            return None


async def test_method_4_two_step():
    """
    Method 4: Two-step approach - first get profile data, then research more
    """
    print("\n" + "="*70)
    print("TEST 4: Two-Step Approach")
    print("="*70)
    
    # Step 1: Get basic profile info
    prompt1 = f"""What can you tell me about the LinkedIn profile at {TEST_LINKEDIN_URL}?
Just give me the name, current job title, and company."""

    async with httpx.AsyncClient(timeout=60.0) as client:
        response1 = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sonar-pro",
                "messages": [{"role": "user", "content": prompt1}],
                "temperature": 0.1
            }
        )
        
        if response1.status_code == 200:
            result1 = response1.json()
            content1 = result1.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"\n📋 Step 1 - Basic Info:")
            print("-"*70)
            print(content1[:1000])
            
            # Step 2: Use extracted info for deeper search
            # Extract name and company from response (simple approach)
            prompt2 = f"""Based on this information about a LinkedIn profile:
{content1}

Now search for more details about this person including:
- Their complete work history
- Education
- Any news articles or mentions
- Speaking engagements
- Publications

Use their name and current company in your searches."""

            response2 = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar-pro",
                    "messages": [{"role": "user", "content": prompt2}],
                    "temperature": 0.1
                }
            )
            
            if response2.status_code == 200:
                result2 = response2.json()
                content2 = result2.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"\n📋 Step 2 - Detailed Research:")
                print("-"*70)
                print(content2[:2000])
                return content1, content2
        
        print(f"\n❌ Error: {response1.text[:500]}")
        return None


async def main():
    print("\n" + "🔍"*35)
    print("     PERPLEXITY LINKEDIN FETCH TEST")
    print("🔍"*35)
    
    if not API_KEY:
        print("\n❌ ERROR: PERPLEXITY_API_KEY not found!")
        print("Please set it in your .env file or environment variables.")
        return
    
    print(f"\n📎 API Key: {API_KEY[:15]}...")
    print(f"🔗 Test URL: {TEST_LINKEDIN_URL}")
    
    # Run all tests
    results = {}
    
    try:
        results['method1'] = await test_method_1_direct_url()
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
    
    try:
        results['method2'] = await test_method_2_explicit_fetch()
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")
    
    try:
        results['method3'] = await test_method_3_search_with_url()
    except Exception as e:
        print(f"❌ Method 3 failed: {e}")
    
    try:
        results['method4'] = await test_method_4_two_step()
    except Exception as e:
        print(f"❌ Method 4 failed: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for method, result in results.items():
        status = "✅ Got response" if result else "❌ Failed"
        print(f"{method}: {status}")
    
    print("\n💡 ANALYSIS:")
    print("-"*70)
    print("""
If all methods return similar/consistent data → Perplexity CAN access LinkedIn
If methods return different people → Perplexity is searching, not fetching URL
If methods fail or return generic info → LinkedIn blocking or API limitation

RECOMMENDATION:
- If Method 1 or 2 works → Use the _build_linkedin_url_prompt approach
- If only Method 4 works → Use two-step approach  
- If nothing works → Need Proxycurl or manual company name input
""")


if __name__ == "__main__":
    asyncio.run(main())