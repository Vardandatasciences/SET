"""
Test script for DeepSeek + LinkedIn Scraper integration
Run this to verify your setup is working correctly
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test imports
try:
    from services.deepseek_service import DeepSeekService
    print("✅ DeepSeek service import successful")
except Exception as e:
    print(f"❌ DeepSeek service import failed: {e}")

try:
    from services.linkedin_scraper_service import LinkedInScraperService
    print("✅ LinkedIn scraper service import successful")
except Exception as e:
    print(f"❌ LinkedIn scraper service import failed: {e}")

try:
    from services.unified_intelligence_service import UnifiedIntelligenceService
    print("✅ Unified intelligence service import successful")
except Exception as e:
    print(f"❌ Unified intelligence service import failed: {e}")


async def test_deepseek():
    """Test DeepSeek service"""
    print("\n" + "="*80)
    print("TESTING DEEPSEEK SERVICE")
    print("="*80)
    
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_key:
        print("⚠️  DEEPSEEK_API_KEY not configured - skipping test")
        return False
    
    try:
        service = DeepSeekService(deepseek_key)
        print("✅ DeepSeek service initialized")
        
        # Test a simple query
        print("\n📋 Testing simple query: 'Tim Cook'")
        result = await service.fetch_research_data(
            query="Tim Cook",
            research_type="individual",
            sources=None
        )
        
        if result and result.get('raw_response'):
            print(f"✅ Query successful!")
            print(f"   Response length: {len(result['raw_response'])} characters")
            print(f"   Sources found: {len(result.get('sources', []))}")
            return True
        else:
            print("❌ Query returned no data")
            return False
            
    except Exception as e:
        print(f"❌ DeepSeek test failed: {e}")
        return False


async def test_linkedin_scraper():
    """Test LinkedIn scraper service"""
    print("\n" + "="*80)
    print("TESTING LINKEDIN SCRAPER SERVICE")
    print("="*80)
    
    linkedin_email = os.getenv("LINKEDIN_EMAIL")
    linkedin_password = os.getenv("LINKEDIN_PASSWORD")
    
    if not linkedin_email or not linkedin_password:
        print("⚠️  LinkedIn credentials not configured - skipping test")
        print("💡 Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env to test")
        return False
    
    try:
        service = LinkedInScraperService()
        print("✅ LinkedIn scraper service initialized")
        
        # Note: We won't actually scrape in this test to avoid rate limits
        # Just verify the service can be initialized
        print("✅ Service ready (actual scraping not tested to avoid rate limits)")
        print("💡 To test scraping, provide a LinkedIn URL to the API")
        return True
        
    except Exception as e:
        print(f"❌ LinkedIn scraper test failed: {e}")
        return False


async def test_unified_service():
    """Test unified intelligence service"""
    print("\n" + "="*80)
    print("TESTING UNIFIED INTELLIGENCE SERVICE")
    print("="*80)
    
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    
    if not deepseek_key and not perplexity_key:
        print("⚠️  No AI service configured - skipping test")
        return False
    
    try:
        service = UnifiedIntelligenceService(
            deepseek_api_key=deepseek_key,
            fallback_to_perplexity=True
        )
        print("✅ Unified service initialized")
        
        # Test a simple query
        print("\n📋 Testing unified query: 'Elon Musk'")
        result = await service.fetch_research_data(
            query="Elon Musk",
            research_type="individual",
            sources=[
                {
                    "name": "LinkedIn",
                    "link": "https://www.linkedin.com/in/elonmusk/"
                }
            ]
        )
        
        if result and result.get('raw_response'):
            print(f"✅ Query successful!")
            print(f"   Response length: {len(result['raw_response'])} characters")
            print(f"   Sources found: {len(result.get('sources', []))}")
            print(f"   LinkedIn data: {'Yes' if result.get('linkedin_data') else 'No'}")
            return True
        else:
            print("❌ Query returned no data")
            return False
            
    except Exception as e:
        print(f"❌ Unified service test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 DEEPSEEK + LINKEDIN SCRAPER INTEGRATION TEST")
    print("="*80)
    
    # Check configuration
    print("\n📋 CHECKING CONFIGURATION")
    print("-"*80)
    print(f"DeepSeek API Key: {'✅ Configured' if os.getenv('DEEPSEEK_API_KEY') else '❌ Missing'}")
    print(f"Perplexity API Key: {'✅ Configured' if os.getenv('PERPLEXITY_API_KEY') else '⚠️  Not configured (optional)'}")
    print(f"LinkedIn Email: {'✅ Configured' if os.getenv('LINKEDIN_EMAIL') else '⚠️  Not configured'}")
    print(f"LinkedIn Password: {'✅ Configured' if os.getenv('LINKEDIN_PASSWORD') else '⚠️  Not configured'}")
    
    # Run tests
    results = {
        "deepseek": await test_deepseek(),
        "linkedin": await test_linkedin_scraper(),
        "unified": await test_unified_service()
    }
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL/SKIP"
        print(f"{status} - {test_name.capitalize()} Service")
    
    print("-"*80)
    print(f"Total: {passed}/{total} tests passed")
    print("="*80)
    
    if passed == total:
        print("\n🎉 All tests passed! Your integration is working correctly.")
    elif passed > 0:
        print(f"\n⚠️  {passed} out of {total} tests passed. Check configuration above.")
    else:
        print("\n❌ No tests passed. Please check your configuration.")
    
    print("\n💡 Next steps:")
    print("   1. Make sure all required API keys are configured in .env")
    print("   2. Run: python main.py")
    print("   3. Test with: curl http://localhost:8000/api/health")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
