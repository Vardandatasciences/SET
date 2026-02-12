#!/usr/bin/env python3
"""
Create LinkedIn Session for Sales Enablement Tool

This script helps you create a linkedin_session.json file by logging in manually.
This session will be used by the backend to scrape LinkedIn profiles without
triggering security checkpoints.

Usage:
    python create_linkedin_session.py
    
The script will:
1. Open a browser window with LinkedIn login page
2. Wait for you to manually log in (up to 5 minutes)
3. Automatically detect when login is complete
4. Save your session to linkedin_session.json
5. The backend will use this session to scrape LinkedIn profiles

Note: The session file contains authentication cookies and should never be committed to git.
"""
import asyncio
import sys
import os

# Add the linkedin_scraper to the path
linkedin_scraper_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'linkedin_scraper')
if linkedin_scraper_path not in sys.path:
    sys.path.insert(0, linkedin_scraper_path)

from linkedin_scraper import BrowserManager, wait_for_manual_login


async def create_session():
    """Create a LinkedIn session file through manual login."""
    print("\n" + "="*80)
    print("LinkedIn Session Creator for Sales Enablement Tool")
    print("="*80)
    print("\nThis script will help you create a session file for LinkedIn scraping.")
    print("\n📋 STEPS:")
    print("   1. A browser window will open")
    print("   2. Log in to LinkedIn manually (with your LinkedIn account)")
    print("   3. Complete any 2FA or CAPTCHA challenges")
    print("   4. Wait for your feed to load")
    print("   5. The script will detect when you're logged in")
    print("   6. Your session will be saved to linkedin_session.json")
    print("\n⚠️  IMPORTANT:")
    print("   - Use the SAME credentials as in your .env file")
    print("   - You have 5 minutes to complete the login")
    print("   - This only needs to be done ONCE")
    print("   - The session will be reused for future scraping")
    print("\n" + "="*80 + "\n")
    
    input("Press Enter to continue...")
    print()
    
    async with BrowserManager(headless=False) as browser:
        # Navigate to LinkedIn login page
        print("🌐 Opening LinkedIn login page...")
        await browser.page.goto("https://www.linkedin.com/login")
        
        print("\n🔐 Please log in to LinkedIn in the browser window...")
        print("   (You have 5 minutes to complete the login)")
        print("\n   👉 Steps:")
        print("      1. Enter your email and password")
        print("      2. Complete any 2FA or CAPTCHA challenges")
        print("      3. Wait for your LinkedIn feed to load")
        print("      4. Do NOT close the browser window")
        print("\n⏳ Waiting for login completion...\n")
        
        # Wait for manual login (5 minutes timeout)
        try:
            await wait_for_manual_login(browser.page, timeout=300000)
        except Exception as e:
            print(f"\n❌ Login failed: {e}")
            print("\n💡 Please try again and make sure you:")
            print("   - Complete the login within 5 minutes")
            print("   - Wait until your LinkedIn feed loads")
            print("   - Don't close the browser window during login")
            return False
        
        # Save session to backend directory
        session_path = os.path.join(os.path.dirname(__file__), "linkedin_session.json")
        print(f"\n💾 Saving session to {session_path}...")
        await browser.save_session(session_path)
        
        print("\n" + "="*80)
        print("✅ SUCCESS! LinkedIn Session Created")
        print("="*80)
        print(f"\n📁 Session saved to: {session_path}")
        print("\n🎉 YOU'RE ALL SET!")
        print("\n✓ Now you can:")
        print("   1. Close this script")
        print("   2. Restart your backend server (python main.py)")
        print("   3. Use the application to scrape LinkedIn profiles")
        print("   4. The system will use this session automatically")
        print("\n💡 Tips:")
        print("   - Session will be reused automatically")
        print("   - No more security checkpoints!")
        print("   - If session expires, just run this script again")
        print("   - Keep the session file secure (don't commit to git)")
        print("\n" + "="*80 + "\n")
        
        return True


if __name__ == "__main__":
    print("\n🚀 LinkedIn Session Creator Starting...\n")
    success = asyncio.run(create_session())
    
    if success:
        print("✅ Done! You can now use LinkedIn scraping in the application.\n")
    else:
        print("\n❌ Session creation failed. Please try again.\n")
        sys.exit(1)
