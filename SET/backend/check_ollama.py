"""
Quick script to check if Ollama is running and help you start it
Run this before starting the main server
"""

import httpx
import sys
import os

def check_ollama():
    """Check if Ollama is running"""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    print("\n" + "="*80)
    print("🔍 CHECKING OLLAMA STATUS")
    print("="*80)
    print(f"📍 Checking: {base_url}")
    print()
    
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=3.0)
        if response.status_code == 200:
            print("✅ Ollama is RUNNING!")
            print()
            
            # Check available models
            data = response.json()
            models = [m.get('name', '') for m in data.get('models', [])]
            
            if models:
                print(f"📦 Available models ({len(models)}):")
                for model in models:
                    print(f"   • {model}")
            else:
                print("⚠️  No models downloaded yet")
                print("   Download one with: ollama pull deepseek-r1:latest")
            
            print()
            print("="*80)
            print("✅ READY TO USE! You can start the server now.")
            print("="*80)
            return True
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False
    except httpx.ConnectError:
        print("❌ Ollama is NOT running!")
        print()
        print("="*80)
        print("📋 TO START OLLAMA:")
        print("="*80)
        print()
        print("Windows:")
        print("  1. Press Windows key")
        print("  2. Type 'Ollama' and press Enter")
        print("  3. Wait for Ollama to start (check system tray)")
        print()
        print("Mac:")
        print("  1. Open Finder → Applications")
        print("  2. Find and open 'Ollama'")
        print("  3. Wait for it to start")
        print()
        print("Linux:")
        print("  1. Run: systemctl start ollama")
        print("  2. Or: ollama serve")
        print()
        print("Download:")
        print("  Visit: https://ollama.ai/download")
        print()
        print("="*80)
        print("💡 After starting Ollama, run this script again to verify")
        print("="*80)
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False

if __name__ == "__main__":
    is_running = check_ollama()
    sys.exit(0 if is_running else 1)
