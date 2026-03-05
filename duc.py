import json
import asyncio
from typing import Dict, Any, Optional
import sys
from urllib.parse import quote

# Try to import Playwright
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Installing Playwright...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True

async def search_linkedin_with_browser(name: str, debug: bool = False) -> Optional[Dict[str, Any]]:
    """Search for LinkedIn profile using browser automation"""
    if not PLAYWRIGHT_AVAILABLE:
        return None
    
    async with async_playwright() as p:
        # Launch browser with stealth settings
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        # Create context with realistic settings
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
        )
        
        # Enhanced stealth - hide automation signals
        await context.add_init_script("""
            // Hide webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Add Chrome object
            window.chrome = { runtime: {} };
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        page = await context.new_page()
        
        try:
            # Try multiple search strategies
            query1 = f'"{name}" site:linkedin.com/in'
            query2 = f'{name} linkedin'
            
            search_strategies = [
                {
                    "name": "DuckDuckGo (site search)",
                    "url": f"https://duckduckgo.com/?q={quote(query1)}",
                    "engine": "duckduckgo"
                },
                {
                    "name": "DuckDuckGo (simple)",
                    "url": f"https://duckduckgo.com/?q={quote(query2)}",
                    "engine": "duckduckgo"
                },
                {
                    "name": "Google (site search)",
                    "url": f"https://www.google.com/search?q={quote(query1)}",
                    "engine": "google"
                },
                {
                    "name": "Google (simple)",
                    "url": f"https://www.google.com/search?q={quote(query2)}",
                    "engine": "google"
                },
            ]
            
            for strategy in search_strategies:
                print(f"   Trying: {strategy['name']}")
                try:
                    await page.goto(strategy["url"], wait_until="domcontentloaded", timeout=15000)
                    await asyncio.sleep(2.5)  # Realistic delay
                    
                    # Scroll a bit to simulate human behavior
                    await page.evaluate("window.scrollTo(0, 300)")
                    await asyncio.sleep(0.5)
                    
                    # Extract LinkedIn URLs from this page
                    linkedin_urls = []
                    import re
                    linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-]+/?'
                    
                    # Method 1: Search in page text
                    try:
                        page_text = await page.inner_text('body')
                        found_urls = re.findall(linkedin_pattern, page_text)
                        for url in found_urls:
                            clean_url = url.rstrip('/').split('?')[0]
                            if clean_url not in [u["url"] for u in linkedin_urls]:
                                linkedin_urls.append({
                                    "url": clean_url,
                                    "title": f"{name} - LinkedIn"
                                })
                    except:
                        pass
                    
                    # Method 2: Check all links
                    try:
                        all_links = await page.query_selector_all('a[href]')
                        for link in all_links:
                            try:
                                href = await link.get_attribute('href')
                                if not href:
                                    continue
                                
                                # Handle Google's URL wrapping
                                if '/url?q=' in href and strategy['engine'] == 'google':
                                    from urllib.parse import urlparse, parse_qs, unquote
                                    try:
                                        parsed = urlparse(href)
                                        params = parse_qs(parsed.query)
                                        if 'q' in params:
                                            href = unquote(params['q'][0])
                                    except:
                                        continue
                                
                                if 'linkedin.com/in/' in href.lower():
                                    # Clean URL
                                    if '?' in href:
                                        href = href.split('?')[0]
                                    if href.startswith('/'):
                                        href = 'https://www.linkedin.com' + href
                                    elif not href.startswith('http'):
                                        continue
                                    
                                    clean_url = href.rstrip('/')
                                    if clean_url not in [u["url"] for u in linkedin_urls]:
                                        # Try to get title
                                        try:
                                            title = await link.inner_text()
                                            if not title or len(title) < 3:
                                                title = f"{name} - LinkedIn"
                                        except:
                                            title = f"{name} - LinkedIn"
                                        
                                        linkedin_urls.append({
                                            "url": clean_url,
                                            "title": title.strip()
                                        })
                            except:
                                continue
                    except:
                        pass
                    
                    # Remove duplicates and check if we found any
                    seen = set()
                    unique_urls = []
                    for item in linkedin_urls:
                        if item["url"] not in seen:
                            seen.add(item["url"])
                            unique_urls.append(item)
                    
                    if unique_urls:
                        result = unique_urls[0]
                        print(f"   ✅ Found LinkedIn URL: {result['url']}")
                        await browser.close()
                        return {
                            "url": result["url"],
                            "title": result["title"],
                            "snippet": ""
                        }
                    
                except Exception as e:
                    print(f"   Search failed: {str(e)[:50]}")
                    continue
            
            # All search strategies failed
            await browser.close()
            return None
            
        except Exception as e:
            print(f"   Browser search error: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()[:300]}")
            try:
                await browser.close()
            except:
                pass
            return None

async def get_linkedin_info(linkedin_url: str) -> Dict[str, Any]:
    """Extract information from LinkedIn profile using browser"""
    if not linkedin_url:
        return None
    
    info = {
        "linkedin_url": linkedin_url,
        "name": "",
        "headline": "",
        "location": "",
        "about": "",
        "experience": [],
        "education": [],
        "skills": []
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
        )
        
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = { runtime: {} };
        """)
        
        page = await context.new_page()
        
        try:
            print(f"   Fetching LinkedIn profile...")
            await page.goto(linkedin_url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)  # Wait for content to load
            
            # Extract name from title
            title = await page.title()
            if title and '|' in title:
                info["name"] = title.split('|')[0].strip()
            
            # Try to get meta description for headline
            try:
                meta_desc = await page.query_selector('meta[name="description"]')
                if meta_desc:
                    info["headline"] = await meta_desc.get_attribute('content') or ""
            except:
                pass
            
            # Try to extract structured data
            try:
                json_scripts = await page.query_selector_all('script[type="application/ld+json"]')
                for script in json_scripts:
                    try:
                        script_text = await script.inner_text()
                        data = json.loads(script_text)
                        if isinstance(data, dict):
                            if 'name' in data and not info["name"]:
                                info["name"] = data.get('name', '')
                            if 'jobTitle' in data and not info["headline"]:
                                info["headline"] = data.get('jobTitle', '')
                    except:
                        continue
            except:
                pass
            
            # Try to get about section
            try:
                about_selectors = [
                    'section[data-section="summary"]',
                    'div[data-section="summary"]',
                    'section.about',
                    '.about-section',
                    'div.about'
                ]
                
                for selector in about_selectors:
                    about_elem = await page.query_selector(selector)
                    if about_elem:
                        about_text = await about_elem.inner_text()
                        if len(about_text) > 50:
                            info["about"] = about_text[:500]
                            break
            except:
                pass
            
            # Try to get location
            try:
                location_elem = await page.query_selector('.text-body-small.inline, .pv-text-details__left-panel span')
                if location_elem:
                    info["location"] = (await location_elem.inner_text()).strip()
            except:
                pass
            
            await browser.close()
            return info
            
        except Exception as e:
            error_msg = str(e)
            await browser.close()
            
            if "999" in error_msg or "403" in error_msg or "blocked" in error_msg.lower():
                return {
                    "linkedin_url": linkedin_url,
                    "error": "LinkedIn blocked the request. Profile may require login.",
                    "note": "LinkedIn profiles often require authentication to view full details."
                }
            
            return {
                "linkedin_url": linkedin_url,
                "error": error_msg,
                "note": "Could not fully extract profile information"
            }

async def get_person_info(name: str) -> Dict[str, Any]:
    """Main function to get LinkedIn URL and information"""
    print(f"Searching for LinkedIn profile of: {name}")
    
    # Step 1: Find LinkedIn URL using browser automation
    linkedin_result = await search_linkedin_with_browser(name)
    
    if not linkedin_result:
        return {
            "name": name,
            "linkedin_url": None,
            "error": "LinkedIn profile not found via automated search",
            "information": None
        }
    
    linkedin_url = linkedin_result["url"]
    print(f"Found LinkedIn URL: {linkedin_url}")
    
    # Step 2: Get information from LinkedIn profile
    print(f"Extracting information from LinkedIn profile...")
    await asyncio.sleep(1)  # Be respectful
    linkedin_info = await get_linkedin_info(linkedin_url)
    
    # Combine results
    result = {
        "name": name,
        "linkedin_url": linkedin_url,
        "search_result": {
            "title": linkedin_result.get("title", ""),
            "snippet": linkedin_result.get("snippet", "")
        },
        "information": linkedin_info
    }
    
    return result

def main():
    """Main entry point"""
    # Get name from command line or use default
    if len(sys.argv) > 1:
        name = " ".join(sys.argv[1:])
    else:
        name = "Susheel Ramadoss"
    
    print("="*80)
    print(f"Searching for: {name}")
    print("="*80)
    print("Using browser automation for reliable search...\n")
    
    # Run async function
    result = asyncio.run(get_person_info(name))
    
    
    # Output as JSON
    print("\n" + "="*80)
    print("RESULTS (JSON):")
    print("="*80)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Save to file
    output_file = f"{name.replace(' ', '_')}_info.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved to: {output_file}")

if __name__ == "__main__":
    main()
