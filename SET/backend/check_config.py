"""
Script to check if the Perplexity API key is configured correctly
"""
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("PERPLEXITY_API_KEY")

print("=" * 60)
print("Perplexity API Configuration Check")
print("=" * 60)
print()

if not api_key:
    print("[ERROR] PERPLEXITY_API_KEY is not set!")
    print()
    print("Please create a .env file in the backend directory with:")
    print("PERPLEXITY_API_KEY=your_api_key_here")
    print()
    print("See CREATE_ENV_FILE.md for detailed instructions.")
elif api_key == "your_perplexity_api_key_here" or api_key.strip() == "":
    print("[ERROR] PERPLEXITY_API_KEY is set to placeholder value!")
    print()
    print("Please replace 'your_perplexity_api_key_here' with your actual API key.")
    print("Get your API key from: https://www.perplexity.ai/settings/api")
else:
    print("[OK] PERPLEXITY_API_KEY is set")
    print(f"   Key length: {len(api_key)} characters")
    print(f"   Key starts with: {api_key[:10]}...")
    print()
    print("[WARNING] If you're still getting 401 errors, check:")
    print("   1. The API key is correct (no typos)")
    print("   2. Your account has sufficient credits")
    print("   3. The API key hasn't expired")
    print("   4. There are no extra spaces in the .env file")

print()
print("=" * 60)

