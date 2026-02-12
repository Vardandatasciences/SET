"""
LinkedIn Scraper Service
Integrates the linkedin_scraper package for LinkedIn data extraction
"""

import os
import sys
import re
from typing import Dict, Any, Optional, List
import asyncio
import json

# Add the linkedin_scraper to the path
linkedin_scraper_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'linkedin_scraper')
if linkedin_scraper_path not in sys.path:
    sys.path.insert(0, linkedin_scraper_path)

try:
    from linkedin_scraper import (
        BrowserManager,
        PersonScraper,
        CompanyScraper,
        login_with_credentials,
        load_credentials_from_env,
        ConsoleCallback
    )
    LINKEDIN_SCRAPER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  LinkedIn scraper not available: {e}")
    LINKEDIN_SCRAPER_AVAILABLE = False


class LinkedInScraperService:
    """
    Service to scrape LinkedIn profiles and companies using the linkedin_scraper package
    
    This service handles:
    - LinkedIn profile scraping (individuals)
    - LinkedIn company page scraping
    - Authentication management
    - Data transformation for SET
    """
    
    def __init__(self):
        self.linkedin_email = os.getenv("LINKEDIN_EMAIL")
        self.linkedin_password = os.getenv("LINKEDIN_PASSWORD")
        # Path to session file (saved in backend directory)
        self.session_file = os.path.join(os.path.dirname(__file__), "..", "linkedin_session.json")
        
        if not LINKEDIN_SCRAPER_AVAILABLE:
            print("⚠️  LinkedIn scraper package not available")
            print("💡 TIP: Make sure the linkedin_scraper directory is present")
    
    async def scrape_person(self, linkedin_url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a LinkedIn person profile
        
        Args:
            linkedin_url: URL of the LinkedIn profile (e.g., https://www.linkedin.com/in/username/)
        
        Returns:
            Dictionary with person data or None if failed
        """
        if not LINKEDIN_SCRAPER_AVAILABLE:
            print("❌ LinkedIn scraper not available")
            return None
        
        # Check if we have credentials OR a saved session
        has_credentials = self.linkedin_email and self.linkedin_password
        has_session = os.path.exists(self.session_file)
        
        if not has_credentials and not has_session:
            print("⚠️  LinkedIn credentials not configured and no saved session found")
            print("💡 TIP: Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env file")
            print("💡 OR: Create a session using create_linkedin_session.py")
            return None
        
        # Clean and normalize LinkedIn URL
        linkedin_url = self._normalize_linkedin_url(linkedin_url)
        
        print("\n" + "="*80)
        print("🔗 LINKEDIN PROFILE SCRAPING")
        print("="*80)
        print(f"📎 URL: {linkedin_url}")
        print("="*80 + "\n")
        
        try:
            async with BrowserManager(headless=True) as browser:
                # Try to load saved session first
                session_loaded = False
                if os.path.exists(self.session_file):
                    try:
                        print("🔄 Loading saved LinkedIn session...")
                        await browser.load_session(self.session_file)
                        # Don't verify the session - just trust it
                        # Verification can trigger LinkedIn's bot detection
                        print("✅ Session loaded!\n")
                        session_loaded = True
                    except Exception as e:
                        print(f"⚠️  Failed to load session: {e}")
                        if has_credentials:
                            print("   Will login with credentials...")
                        else:
                            raise Exception("Failed to load session and no credentials available")
                
                # If session not loaded, login with credentials
                if not session_loaded:
                    if not has_credentials:
                        raise Exception("No session file and no credentials available")
                    print("🔐 Logging in to LinkedIn with credentials...")
                    await login_with_credentials(
                        browser.page,
                        self.linkedin_email,
                        self.linkedin_password
                    )
                    print("✅ Login successful!")
                    # Save session for future use
                    print("💾 Saving session for future use...")
                    await browser.save_session(self.session_file)
                    print("✅ Session saved!\n")
                
                # Scrape the profile
                print("🔍 Scraping profile...")
                scraper = PersonScraper(browser.page, callback=ConsoleCallback())
                person = await scraper.scrape(linkedin_url)
                
                # Convert to dictionary
                person_data = {
                    "linkedin_url": linkedin_url,
                    "full_name": person.name,
                    "headline": getattr(person, 'headline', None),
                    "location": person.location,
                    "about": person.about,
                    "experiences": [],
                    "education": [],
                    "skills": getattr(person, 'skills', []),
                    "languages": getattr(person, 'languages', []),
                    "certifications": [],
                    "volunteer_experience": getattr(person, 'volunteer_experience', []),
                    "honors_awards": getattr(person, 'honors_awards', [])
                }
                
                # Process experiences
                if person.experiences:
                    for exp in person.experiences:
                        person_data["experiences"].append({
                            "title": getattr(exp, 'position_title', getattr(exp, 'title', None)),
                            "company": getattr(exp, 'institution_name', getattr(exp, 'company', None)),
                            "company_url": getattr(exp, 'linkedin_url', getattr(exp, 'company_url', None)),
                            "location": getattr(exp, 'location', None),
                            "start_date": getattr(exp, 'from_date', getattr(exp, 'start_date', None)),
                            "end_date": getattr(exp, 'to_date', getattr(exp, 'end_date', None)),
                            "description": getattr(exp, 'description', None),
                            "duration": getattr(exp, 'duration', None)
                        })
                
                # Process education
                if person.educations:
                    for edu in person.educations:
                        person_data["education"].append({
                            "school": getattr(edu, 'institution_name', getattr(edu, 'school', None)),
                            "school_url": getattr(edu, 'linkedin_url', getattr(edu, 'school_url', None)),
                            "degree": getattr(edu, 'degree', None),
                            "field_of_study": getattr(edu, 'field_of_study', None),
                            "start_date": getattr(edu, 'from_date', getattr(edu, 'start_date', None)),
                            "end_date": getattr(edu, 'to_date', getattr(edu, 'end_date', None)),
                            "description": getattr(edu, 'description', None)
                        })
                
                # Process certifications (from accomplishments)
                if hasattr(person, 'accomplishments') and person.accomplishments:
                    certifications = [a for a in person.accomplishments if getattr(a, 'category', '') == 'certification']
                    for cert in certifications:
                        person_data["certifications"].append({
                            "name": getattr(cert, 'title', None),
                            "issuer": getattr(cert, 'issuer', None),
                            "issue_date": getattr(cert, 'issued_date', None),
                            "expiry_date": getattr(cert, 'expiry_date', None),
                            "credential_id": getattr(cert, 'credential_id', None),
                            "credential_url": getattr(cert, 'credential_url', None)
                        })
                
                print("\n" + "="*80)
                print("✅ LINKEDIN PROFILE SCRAPED SUCCESSFULLY")
                print("="*80)
                print(f"👤 Name: {person_data.get('full_name', 'N/A')}")
                print(f"💼 Headline: {person_data.get('headline', 'N/A')}")
                print(f"📍 Location: {person_data.get('location', 'N/A')}")
                print(f"💼 Experiences: {len(person_data.get('experiences', []))}")
                print(f"🎓 Education: {len(person_data.get('education', []))}")
                print("="*80 + "\n")
                
                return person_data
                
        except Exception as e:
            print(f"❌ Error scraping LinkedIn profile: {str(e)}")
            print(f"💥 Details: {type(e).__name__}")
            return None
    
    async def scrape_company(self, linkedin_url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a LinkedIn company page
        
        Args:
            linkedin_url: URL of the LinkedIn company page (e.g., https://www.linkedin.com/company/microsoft/)
        
        Returns:
            Dictionary with company data or None if failed
        """
        if not LINKEDIN_SCRAPER_AVAILABLE:
            print("❌ LinkedIn scraper not available")
            return None
        
        # Check if we have credentials OR a saved session
        has_credentials = self.linkedin_email and self.linkedin_password
        has_session = os.path.exists(self.session_file)
        
        if not has_credentials and not has_session:
            print("⚠️  LinkedIn credentials not configured and no saved session found")
            print("💡 TIP: Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env file")
            print("💡 OR: Create a session using create_linkedin_session.py")
            return None
        
        # Clean and normalize LinkedIn URL
        linkedin_url = self._normalize_linkedin_url(linkedin_url)
        
        print("\n" + "="*80)
        print("🏢 LINKEDIN COMPANY SCRAPING")
        print("="*80)
        print(f"📎 URL: {linkedin_url}")
        print("="*80 + "\n")
        
        try:
            async with BrowserManager(headless=True) as browser:
                # Try to load saved session first
                session_loaded = False
                if os.path.exists(self.session_file):
                    try:
                        print("🔄 Loading saved LinkedIn session...")
                        await browser.load_session(self.session_file)
                        # Don't verify the session - just trust it
                        # Verification can trigger LinkedIn's bot detection
                        print("✅ Session loaded!\n")
                        session_loaded = True
                    except Exception as e:
                        print(f"⚠️  Failed to load session: {e}")
                        if has_credentials:
                            print("   Will login with credentials...")
                        else:
                            raise Exception("Failed to load session and no credentials available")
                
                # If session not loaded, login with credentials
                if not session_loaded:
                    if not has_credentials:
                        raise Exception("No session file and no credentials available")
                    print("🔐 Logging in to LinkedIn with credentials...")
                    await login_with_credentials(
                        browser.page,
                        self.linkedin_email,
                        self.linkedin_password
                    )
                    print("✅ Login successful!")
                    # Save session for future use
                    print("💾 Saving session for future use...")
                    await browser.save_session(self.session_file)
                    print("✅ Session saved!\n")
                
                # Scrape the company
                print("🔍 Scraping company page...")
                scraper = CompanyScraper(browser.page, callback=ConsoleCallback())
                company = await scraper.scrape(linkedin_url)
                
                # Convert to dictionary
                company_data = {
                    "linkedin_url": linkedin_url,
                    "name": company.name,
                    "about": company.about_us,
                    "website": company.website,
                    "industry": company.industry,
                    "company_size": company.company_size,
                    "headquarters": company.headquarters,
                    "founded": company.founded,
                    "specialties": company.specialties,
                    "employees": []
                }
                
                # Process employees
                if company.employees:
                    for emp in company.employees:
                        company_data["employees"].append({
                            "name": emp.name,
                            "title": getattr(emp, 'designation', 'N/A'),
                            "profile_url": getattr(emp, 'linkedin_url', None)
                        })
                
                print("\n" + "="*80)
                print("✅ LINKEDIN COMPANY SCRAPED SUCCESSFULLY")
                print("="*80)
                print(f"🏢 Name: {company_data.get('name', 'N/A')}")
                print(f"🌐 Website: {company_data.get('website', 'N/A')}")
                print(f"🏭 Industry: {company_data.get('industry', 'N/A')}")
                print(f"👥 Company Size: {company_data.get('company_size', 'N/A')}")
                print(f"📍 HQ: {company_data.get('headquarters', 'N/A')}")
                print(f"👨‍💼 Employees Scraped: {len(company_data.get('employees', []))}")
                print("="*80 + "\n")
                
                return company_data
                
        except Exception as e:
            print(f"❌ Error scraping LinkedIn company: {str(e)}")
            print(f"💥 Details: {type(e).__name__}")
            return None
    
    def _normalize_linkedin_url(self, url: str) -> str:
        """
        Normalize and clean LinkedIn URL
        - Remove spaces
        - Ensure proper format
        - URL encode if needed
        """
        import urllib.parse
        
        # Remove leading/trailing whitespace
        url = url.strip()
        
        # Replace spaces with hyphens (common in LinkedIn URLs)
        url = url.replace(' ', '-')
        
        # Remove multiple consecutive hyphens
        while '--' in url:
            url = url.replace('--', '-')
        
        # Ensure URL ends with /
        if not url.endswith('/'):
            url = url + '/'
        
        # Parse and reconstruct to ensure proper encoding
        parsed = urllib.parse.urlparse(url)
        
        # Encode the path properly
        path = urllib.parse.quote(parsed.path, safe='/-')
        
        # Reconstruct URL
        normalized_url = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        print(f"🔧 Normalized URL: {url} → {normalized_url}")
        
        return normalized_url
    
    async def get_person_from_url(self, linkedin_url: str) -> Optional[Dict[str, Any]]:
        """
        Main method to get person data from LinkedIn URL
        Wrapper for scrape_person with additional error handling
        """
        if not linkedin_url or 'linkedin.com/in/' not in linkedin_url:
            print("⚠️  Invalid LinkedIn profile URL")
            return None
        
        return await self.scrape_person(linkedin_url)
    
    async def get_company_from_url(self, linkedin_url: str) -> Optional[Dict[str, Any]]:
        """
        Main method to get company data from LinkedIn URL
        Wrapper for scrape_company with additional error handling
        """
        if not linkedin_url or 'linkedin.com/company/' not in linkedin_url:
            print("⚠️  Invalid LinkedIn company URL")
            return None
        
        return await self.scrape_company(linkedin_url)
    
    def transform_person_for_set(self, linkedin_data: Dict[str, Any]) -> str:
        """
        Transform LinkedIn person data into formatted text for SET
        
        Args:
            linkedin_data: Dictionary from scrape_person
        
        Returns:
            Formatted string with person information
        """
        if not linkedin_data:
            return "No LinkedIn data available"
        
        output = []
        output.append("="*80)
        output.append("LINKEDIN PROFILE DATA")
        output.append("="*80)
        output.append("")
        
        # Basic Info
        output.append(f"Name: {linkedin_data.get('full_name', 'N/A')}")
        output.append(f"Headline: {linkedin_data.get('headline', 'N/A')}")
        output.append(f"Location: {linkedin_data.get('location', 'N/A')}")
        output.append(f"LinkedIn: {linkedin_data.get('linkedin_url', 'N/A')}")
        output.append("")
        
        # About
        if linkedin_data.get('about'):
            output.append("ABOUT:")
            output.append(linkedin_data['about'])
            output.append("")
        
        # Experience
        if linkedin_data.get('experiences'):
            output.append("EXPERIENCE:")
            for exp in linkedin_data['experiences']:
                output.append(f"  • {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}")
                if exp.get('start_date') or exp.get('end_date'):
                    output.append(f"    {exp.get('start_date', '')} - {exp.get('end_date', 'Present')}")
                if exp.get('location'):
                    output.append(f"    Location: {exp['location']}")
                if exp.get('description'):
                    output.append(f"    {exp['description']}")
                output.append("")
        
        # Education
        if linkedin_data.get('education'):
            output.append("EDUCATION:")
            for edu in linkedin_data['education']:
                output.append(f"  • {edu.get('school', 'N/A')}")
                if edu.get('degree') or edu.get('field_of_study'):
                    output.append(f"    {edu.get('degree', '')} {edu.get('field_of_study', '')}")
                if edu.get('start_date') or edu.get('end_date'):
                    output.append(f"    {edu.get('start_date', '')} - {edu.get('end_date', '')}")
                output.append("")
        
        # Skills
        if linkedin_data.get('skills'):
            output.append("SKILLS:")
            output.append(f"  {', '.join(linkedin_data['skills'][:20])}")
            if len(linkedin_data['skills']) > 20:
                output.append(f"  ... and {len(linkedin_data['skills']) - 20} more")
            output.append("")
        
        # Certifications
        if linkedin_data.get('certifications'):
            output.append("CERTIFICATIONS:")
            for cert in linkedin_data['certifications']:
                output.append(f"  • {cert.get('name', 'N/A')} - {cert.get('issuer', 'N/A')}")
                if cert.get('issue_date'):
                    output.append(f"    Issued: {cert['issue_date']}")
                output.append("")
        
        output.append("="*80)
        
        return "\n".join(output)
    
    def transform_company_for_set(self, linkedin_data: Dict[str, Any]) -> str:
        """
        Transform LinkedIn company data into formatted text for SET
        
        Args:
            linkedin_data: Dictionary from scrape_company
        
        Returns:
            Formatted string with company information
        """
        if not linkedin_data:
            return "No LinkedIn data available"
        
        output = []
        output.append("="*80)
        output.append("LINKEDIN COMPANY DATA")
        output.append("="*80)
        output.append("")
        
        # Basic Info
        output.append(f"Company: {linkedin_data.get('name', 'N/A')}")
        output.append(f"Website: {linkedin_data.get('website', 'N/A')}")
        output.append(f"Industry: {linkedin_data.get('industry', 'N/A')}")
        output.append(f"Company Size: {linkedin_data.get('company_size', 'N/A')}")
        output.append(f"Headquarters: {linkedin_data.get('headquarters', 'N/A')}")
        output.append(f"Founded: {linkedin_data.get('founded', 'N/A')}")
        output.append(f"LinkedIn: {linkedin_data.get('linkedin_url', 'N/A')}")
        output.append("")
        
        # About
        if linkedin_data.get('about'):
            output.append("ABOUT:")
            output.append(linkedin_data['about'])
            output.append("")
        
        # Specialties
        if linkedin_data.get('specialties'):
            output.append("SPECIALTIES:")
            output.append(f"  {', '.join(linkedin_data['specialties'])}")
            output.append("")
        
        # Employees
        if linkedin_data.get('employees'):
            output.append(f"KEY EMPLOYEES ({len(linkedin_data['employees'])} found):")
            for emp in linkedin_data['employees'][:20]:  # Show first 20
                output.append(f"  • {emp.get('name', 'N/A')} - {emp.get('title', 'N/A')}")
            if len(linkedin_data['employees']) > 20:
                output.append(f"  ... and {len(linkedin_data['employees']) - 20} more")
            output.append("")
        
        output.append("="*80)
        
        return "\n".join(output)
    
    async def search_people_by_name(self, name: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Search LinkedIn for people by name and return all matching profiles
        
        Args:
            name: Name to search for
            max_results: Maximum number of results to return (default: 100, 0 = unlimited)
        
        Returns:
            List of dictionaries with name, company, title, location, and linkedin_url
        """
        if not LINKEDIN_SCRAPER_AVAILABLE:
            print("❌ LinkedIn scraper not available for search")
            return []
        
        # Check if we have credentials OR a saved session
        has_credentials = self.linkedin_email and self.linkedin_password
        has_session = os.path.exists(self.session_file)
        
        if not has_credentials and not has_session:
            print("⚠️  LinkedIn credentials not configured for search")
            return []
        
        print("\n" + "="*80)
        print("🔍 LINKEDIN PEOPLE SEARCH")
        print("="*80)
        print(f"📋 Searching for: {name}")
        print(f"🔢 Max results: {max_results if max_results > 0 else 'Unlimited'}")
        print("="*80 + "\n")
        
        results = []
        
        try:
            async with BrowserManager(headless=True) as browser:
                # Try to load saved session first
                session_loaded = False
                if os.path.exists(self.session_file):
                    try:
                        print("🔄 Loading saved LinkedIn session...")
                        await browser.load_session(self.session_file)
                        print("✅ Session loaded!\n")
                        session_loaded = True
                    except Exception as e:
                        print(f"⚠️  Failed to load session: {e}")
                        if has_credentials:
                            print("   Will login with credentials...")
                        else:
                            return []
                
                # If session not loaded, login with credentials
                if not session_loaded:
                    if not has_credentials:
                        return []
                    print("🔐 Logging in to LinkedIn with credentials...")
                    await login_with_credentials(
                        browser.page,
                        self.linkedin_email,
                        self.linkedin_password
                    )
                    print("✅ Login successful!")
                    # Save session for future use
                    print("💾 Saving session for future use...")
                    await browser.save_session(self.session_file)
                    print("✅ Session saved!\n")
                
                # Navigate to LinkedIn search
                search_url = f"https://www.linkedin.com/search/results/people/?keywords={name.replace(' ', '%20')}"
                print(f"🌐 Navigating to LinkedIn search: {search_url}")
                
                # Try with a more lenient wait condition
                try:
                    await browser.page.goto(search_url, wait_until="domcontentloaded", timeout=90000)
                    print("✅ Page loaded (domcontentloaded)")
                except Exception as e:
                    print(f"⚠️  domcontentloaded timeout, trying load...")
                    try:
                        await browser.page.goto(search_url, wait_until="load", timeout=90000)
                        print("✅ Page loaded (load)")
                    except Exception as e2:
                        print(f"⚠️  load timeout, trying commit...")
                        await browser.page.goto(search_url, wait_until="commit", timeout=90000)
                        print("✅ Page loaded (commit)")
                
                # Wait for search results to appear
                print("⏳ Waiting for search results to load...")
                max_wait = 30  # Maximum 30 seconds
                waited = 0
                while waited < max_wait:
                    # Check if search results are present
                    result_elements = await browser.page.query_selector_all('li.reusable-search__result-container, li.search-result, div.search-result__wrapper, li[data-chameleon-result-urn]')
                    if result_elements:
                        print(f"✅ Search results found after {waited} seconds")
                        break
                    await asyncio.sleep(2)
                    waited += 2
                
                if waited >= max_wait:
                    print("⚠️  Search results did not appear, but continuing anyway...")
                
                await asyncio.sleep(2)  # Additional wait for dynamic content
                
                # Scroll to load more results - more aggressive scrolling to get all results
                print("📜 Scrolling to load all results...")
                scroll_count = 0
                max_scrolls = 50  # Increased from 20 to load more results
                last_height = 0
                no_change_count = 0  # Track consecutive scrolls with no new content
                max_no_change = 3  # Stop after 3 consecutive scrolls with no new content
                
                while scroll_count < max_scrolls:
                    # Scroll down
                    await browser.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(3)  # Increased wait time from 2 to 3 seconds for content to load
                    
                    # Check if we've reached the bottom
                    current_height = await browser.page.evaluate("document.body.scrollHeight")
                    
                    # Count how many results we currently have
                    current_results = await browser.page.query_selector_all('li.reusable-search__result-container, li.search-result, div.search-result__wrapper, li[data-chameleon-result-urn], div.entity-result')
                    current_count = len(current_results)
                    
                    if current_height == last_height:
                        no_change_count += 1
                        # Try clicking "Show more results" or pagination buttons
                        try:
                            # Try multiple button selectors
                            show_more_selectors = [
                                'button[aria-label*="Show more results"]',
                                'button[aria-label*="See more"]',
                                'button:has-text("Show more")',
                                'button:has-text("See more")',
                                'a[aria-label*="Show more"]',
                                'a:has-text("Next")',
                                'button:has-text("Next")'
                            ]
                            
                            clicked = False
                            for selector in show_more_selectors:
                                try:
                                    show_more = await browser.page.query_selector(selector)
                                    if show_more:
                                        await show_more.click()
                                        await asyncio.sleep(3)
                                        clicked = True
                                        no_change_count = 0  # Reset counter
                                        break
                                except:
                                    continue
                            
                            if not clicked and no_change_count >= max_no_change:
                                print(f"   No new content after {no_change_count} scrolls, stopping...")
                                break
                        except:
                            if no_change_count >= max_no_change:
                                break
                    else:
                        no_change_count = 0  # Reset counter if we got new content
                    
                    last_height = current_height
                    scroll_count += 1
                    
                    # Log progress every 10 scrolls
                    if scroll_count % 10 == 0:
                        print(f"   Scrolled {scroll_count} times, found {current_count} results so far...")
                
                print(f"✅ Finished scrolling ({scroll_count} scrolls)")
                
                # Extract search results
                print("🔍 Extracting search results...")
                
                # Try to click "Show all people results" if it exists to get the full list
                try:
                    show_all_button = await browser.page.query_selector('button:has-text("Show all people results"), a:has-text("Show all people results")')
                    if show_all_button:
                        print("   Clicking 'Show all people results' button...")
                        await show_all_button.click()
                        await asyncio.sleep(3)  # Wait for results to load
                except Exception as e:
                    print(f"   Could not click 'Show all people results': {e}")
                
                # LinkedIn search results - try multiple selectors
                result_selectors = [
                    'li.reusable-search__result-container',
                    'li.search-result',
                    'div.search-result__wrapper',
                    'li[data-chameleon-result-urn]',
                    'div.entity-result',
                    'div.search-result__info',
                    'div[data-chameleon-result-urn]',
                    'li[class*="search-result"]',
                    'div[class*="entity-result"]'
                ]
                
                result_elements = []
                for selector in result_selectors:
                    elements = await browser.page.query_selector_all(selector)
                    if elements:
                        result_elements = elements
                        print(f"   Found {len(elements)} results using selector: {selector}")
                        break
                
                # Also try to get the main featured result (if it exists)
                featured_selectors = [
                    'div[data-chameleon-result-urn]',
                    'div.entity-result__item',
                    'div.search-result__wrapper',
                    'div[class*="search-result"]'
                ]
                
                if not result_elements:
                    for selector in featured_selectors:
                        elements = await browser.page.query_selector_all(selector)
                        if elements:
                            result_elements = elements
                            print(f"   Found {len(elements)} featured results using selector: {selector}")
                            break
                
                if not result_elements:
                    print("⚠️  No search results found with standard selectors")
                    print("   Trying alternative extraction method...")
                    
                    # Try to find profile cards/containers by looking for elements containing profile links
                    # LinkedIn often wraps profiles in divs or other containers
                    profile_links = await browser.page.query_selector_all('a[href*="/in/"]')
                    if profile_links:
                        print(f"   Found {len(profile_links)} profile links")
                        # For each link, try to find its parent container to extract more info
                        containers = []
                        seen_urls = set()
                        for link in profile_links:
                            try:
                                url = await link.get_attribute('href')
                                if url and '/in/' in url:
                                    # Clean URL
                                    if not url.startswith('http'):
                                        url = f"https://www.linkedin.com{url}"
                                    if '?' in url:
                                        url = url.split('?')[0]
                                    
                                    if url not in seen_urls:
                                        seen_urls.add(url)
                                        # Find parent container (usually 3-5 levels up)
                                        parent = link
                                        for _ in range(5):
                                            parent = await parent.evaluate_handle('(el) => el.parentElement')
                                            if parent:
                                                # Check if this parent has other useful info
                                                containers.append(parent)
                                                break
                            except:
                                continue
                        
                        if containers:
                            result_elements = containers[:50]
                            print(f"   Using {len(result_elements)} profile containers for extraction")
                        else:
                            # Fallback: use links directly
                            result_elements = profile_links[:50]
                            print(f"   Using {len(result_elements)} profile links directly")
                    else:
                        print("⚠️  No search results found at all")
                        return []
                
                # Extract data from each result
                for idx, element in enumerate(result_elements, 1):
                    try:
                        # Debug: Get all text from element to see what we're working with
                        try:
                            element_text = await element.inner_text()
                            if idx <= 3:  # Only log first 3 for debugging
                                print(f"   [DEBUG {idx}] Element text preview: {element_text[:200]}...")
                        except:
                            pass
                        # First, find the profile link - this is the most reliable anchor
                        link_elem = await element.query_selector('a[href*="/in/"]')
                        profile_url = ""
                        if link_elem:
                            profile_url = await link_elem.get_attribute('href')
                            if profile_url and not profile_url.startswith('http'):
                                profile_url = f"https://www.linkedin.com{profile_url}"
                            # Clean URL - remove query parameters
                            if '?' in profile_url:
                                profile_url = profile_url.split('?')[0]
                        
                        # Extract name - try multiple approaches
                        name_text = ""
                        
                        # Method 1: Try entity-result__title-text (most reliable for LinkedIn search)
                        name_elem = await element.query_selector('span.entity-result__title-text a, span.entity-result__title-text')
                        if name_elem:
                            name_text = await name_elem.inner_text()
                            name_text = name_text.strip()
                            # Clean name - remove connection degree indicators like "• 1st"
                            name_text = re.sub(r'\s*•\s*\d+(st|nd|rd|th)\+?\s*', '', name_text)
                            name_text = name_text.strip()
                        
                        # Method 2: If no name found, try getting from link text (but be careful - might have extra text)
                        if not name_text and link_elem:
                            link_text = await link_elem.inner_text()
                            link_text = link_text.strip()
                            # Clean the link text - remove connection indicators
                            link_text = re.sub(r'\s*•\s*\d+(st|nd|rd|th)\+?\s*', '', link_text)
                            # Take only the first line (name should be first)
                            name_text = link_text.split('\n')[0].strip()
                            # Remove any remaining connection text patterns
                            if 'mutual connections' in name_text.lower():
                                name_text = ""
                        
                        # Method 3: Try to extract from all text - find the first line that looks like a name
                        if not name_text:
                            try:
                                all_text = await element.inner_text()
                                lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                                for line in lines:
                                    # Skip connection text, location patterns, etc.
                                    if any(skip in line.lower() for skip in ['mutual connections', 'message', 'follow', 'connect', 'india', 'telangana', 'hyderabad']):
                                        continue
                                    # Skip if it's just a connection degree
                                    if re.match(r'^\s*•\s*\d+(st|nd|rd|th)\+?\s*$', line):
                                        continue
                                    # If line looks like a name (2-4 words, no special patterns)
                                    if 2 <= len(line.split()) <= 4 and not '@' in line and not 'http' in line.lower():
                                        name_text = line
                                        break
                            except:
                                pass
                        
                        # Extract title/headline - try multiple selectors
                        title_selectors = [
                            'div.entity-result__primary-subtitle',
                            'span.entity-result__primary-subtitle',
                            'div.entity-result__summary',
                            'span.entity-result__summary',
                            'p.search-result__snippets',
                            'div[class*="subtitle"]',
                            'span[class*="subtitle"]',
                            'p[class*="subline"]',
                            'div[class*="subline"]',
                            'span[class*="subline"]',
                            'div[class*="headline"]',
                            'span[class*="headline"]'
                        ]
                        
                        title_text = ""
                        for title_selector in title_selectors:
                            title_elem = await element.query_selector(title_selector)
                            if title_elem:
                                title_text = await title_elem.inner_text()
                                title_text = title_text.strip()
                                if title_text:
                                    break
                        
                        # If still no title, try to get text from nearby elements
                        if not title_text:
                            # Try getting all text and finding the subtitle-like text
                            try:
                                all_text = await element.inner_text()
                                lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                                # Usually the title is the second or third line (after name)
                                # Skip connection degree indicators and name
                                for i, line in enumerate(lines):
                                    # Skip if it's the name or connection degree
                                    if line == name_text or re.match(r'^\s*•\s*\d+(st|nd|rd|th)\+?\s*$', line):
                                        continue
                                    # Skip connection text
                                    if 'mutual connections' in line.lower() or 'message' in line.lower():
                                        continue
                                    # Skip location patterns
                                    if any(loc in line.lower() for loc in ['india', 'telangana', 'hyderabad', 'bangalore', 'mumbai']):
                                        continue
                                    # Check if it looks like a title (contains common job-related words or "at" or "@")
                                    if line and len(line) > 5 and len(line) < 200:
                                        if any(word in line.lower() for word in ['at', '@', 'engineer', 'manager', 'director', 'lead', 'developer', 'analyst', 'specialist', 'consultant', 'founder', 'ceo', 'cto', 'cfo', 'president', 'vp', 'head']):
                                            title_text = line
                                            break
                            except:
                                pass
                        
                        # Extract location - try multiple selectors
                        location_selectors = [
                            'div.entity-result__secondary-subtitle',
                            'span.entity-result__secondary-subtitle',
                            'div[class*="secondary-subtitle"]',
                            'span[class*="location"]',
                            'div[class*="location"]',
                            'span[class*="geo"]'
                        ]
                        
                        location_text = ""
                        for location_selector in location_selectors:
                            location_elem = await element.query_selector(location_selector)
                            if location_elem:
                                location_text = await location_elem.inner_text()
                                location_text = location_text.strip()
                                if location_text:
                                    break
                        
                        # If still no location, try to extract from all text
                        if not location_text:
                            try:
                                all_text = await element.inner_text()
                                lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                                # Location is usually at the end or contains city/country patterns
                                for line in reversed(lines):
                                    if line and (',' in line or any(word in line.lower() for word in ['india', 'usa', 'uk', 'city', 'state', 'region', 'area'])):
                                        if len(line) < 100:  # Locations are usually short
                                            location_text = line
                                            break
                            except:
                                pass
                        
                        # Extract company from title (usually format: "Title at Company" or "Title @Company")
                        company = ""
                        if title_text:
                            # Try "Title at Company" format
                            if " at " in title_text:
                                parts = title_text.split(" at ")
                                if len(parts) > 1:
                                    company = parts[-1].strip()
                            # Try "Title @Company" format
                            elif "@" in title_text:
                                parts = title_text.split("@")
                                if len(parts) > 1:
                                    company = parts[-1].strip()
                            elif title_text and not any(keyword in title_text.lower() for keyword in ['student', 'university', 'college']):
                                # Sometimes the title is just the company
                                company = title_text
                        
                        # If still no company, try to extract from all text in the element
                        if not company or company == "N/A":
                            try:
                                all_text = await element.inner_text()
                                lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                                
                                # Look for company patterns
                                for line in lines:
                                    # Skip if it's the name, location, or connection text
                                    if line == name_text or line == location_text:
                                        continue
                                    if 'mutual connections' in line.lower() or 'message' in line.lower():
                                        continue
                                    # Skip connection degree indicators
                                    if re.match(r'^\s*•\s*\d+(st|nd|rd|th)\+?\s*$', line):
                                        continue
                                    # Look for "at Company" or "@Company" pattern
                                    if " at " in line.lower() or "@" in line.lower():
                                        if " at " in line:
                                            parts = line.split(" at ")
                                        else:
                                            parts = line.split("@")
                                        if len(parts) > 1:
                                            potential_company = parts[-1].strip()
                                            if potential_company and len(potential_company) > 2:
                                                company = potential_company
                                                break
                            except:
                                pass
                        
                        # Only add if we have at least a name or profile URL
                        if name_text or profile_url:
                            # If we have URL but no name, try to extract name from URL
                            if not name_text and profile_url:
                                # Extract name from URL like /in/susheel-ramadoss/
                                url_parts = profile_url.split('/in/')
                                if len(url_parts) > 1:
                                    name_from_url = url_parts[-1].split('/')[0].replace('-', ' ').title()
                                    name_text = name_from_url
                            
                            results.append({
                                "name": name_text or "LinkedIn Member",
                                "company": company or "N/A",
                                "title": title_text.split(" at ")[0] if " at " in title_text else title_text or "N/A",
                                "location": location_text,
                                "linkedin_url": profile_url
                            })
                            
                            if idx <= 5:
                                print(f"   [{idx}] {name_text or 'N/A'} - {company or 'N/A'}")
                    
                    except Exception as e:
                        print(f"   ⚠️  Error extracting result {idx}: {e}")
                        import traceback
                        print(f"   Traceback: {traceback.format_exc()}")
                        continue
                
                # Remove duplicates based on LinkedIn URL
                seen_urls = set()
                unique_results = []
                for result in results:
                    url = result.get('linkedin_url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        unique_results.append(result)
                
                results = unique_results
                
                # Limit results if max_results is specified
                if max_results > 0 and len(results) > max_results:
                    results = results[:max_results]
                
                print(f"\n✅ Extracted {len(results)} unique LinkedIn profiles")
                print("="*80 + "\n")
                
                return results
                
        except Exception as e:
            print(f"❌ Error searching LinkedIn: {str(e)}")
            import traceback
            print(f"💥 Details: {traceback.format_exc()}")
            return []