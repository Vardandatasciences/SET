"""
Test Ollama connection and model availability
Run this to diagnose Ollama issues
"""

import httpx
import sys
import os
import asyncio

async def test_ollama():
    """Test Ollama connection and model"""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "deepseek-r1:latest")
    
    print("\n" + "="*80)
    print("🧪 OLLAMA DIAGNOSTIC TEST")
    print("="*80)
    print(f"📍 Ollama URL: {base_url}")
    print(f"🧠 Model: {model}")
    print("="*80)
    print()
    
    # Test 1: Check if Ollama is running
    print("Test 1: Checking if Ollama is running...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{base_url}/api/tags")
            if response.status_code == 200:
                print("✅ Ollama is running!")
            else:
                print(f"❌ Ollama returned status {response.status_code}")
                return False
    except httpx.ConnectError:
        print("❌ Cannot connect to Ollama!")
        print("   → Make sure Ollama is started")
        print("   → Windows: Search for 'Ollama' in Start menu")
        print("   → Mac: Open from Applications")
        print("   → Linux: systemctl start ollama")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print()
    
    # Test 2: Check available models
    print("Test 2: Checking available models...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{base_url}/api/tags")
            data = response.json()
            models = [m.get('name', '') for m in data.get('models', [])]
            
            if models:
                print(f"✅ Found {len(models)} model(s):")
                for m in models:
                    print(f"   • {m}")
            else:
                print("⚠️  No models found!")
                print("   → Download one: ollama pull deepseek-r1:latest")
                return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print()
    
    # Test 3: Check if requested model exists
    print(f"Test 3: Checking if model '{model}' is available...")
    model_base = model.split(':')[0]
    model_found = any(model_base in m for m in models)
    
    if model_found:
        print(f"✅ Model '{model}' is available!")
    else:
        print(f"❌ Model '{model}' not found!")
        print(f"   Available models: {', '.join(models)}")
        print(f"   → Download it: ollama pull {model}")
        print(f"   → OR update .env: OLLAMA_MODEL={models[0] if models else 'llama3.1:8b'}")
        return False
    
    print()
    
    # Test 4: Try a simple API call
    print("Test 4: Testing API call with simple query...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Say 'Hello, Ollama is working!' if you can read this."
                        }
                    ],
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "")
                if content:
                    print(f"✅ API call successful!")
                    print(f"   Response: {content[:100]}...")
                else:
                    print("⚠️  API call succeeded but got empty response")
                    print("   This might indicate the model needs to be reloaded")
                    return False
            else:
                error_text = response.text[:300] if response.text else "No details"
                print(f"❌ API call failed: {response.status_code}")
                print(f"   Error: {error_text}")
                return False
    except httpx.TimeoutException:
        print("❌ Request timed out!")
        print("   → Model might be too slow")
        print("   → Try a smaller model: ollama pull llama3.1:8b")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"   Details: {traceback.format_exc()}")
        return False
    
    print()
    print("="*80)
    print("✅ ALL TESTS PASSED! Ollama is working correctly.")
    print("="*80)
    print()
    print("💡 Your SET tool should work now. Try your request again!")
    print()
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_ollama())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
