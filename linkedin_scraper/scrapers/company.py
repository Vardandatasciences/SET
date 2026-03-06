"""
Company scraper for LinkedIn.

Extracts company information from LinkedIn company pages.
"""
import logging
from typing import Optional
from playwright.async_api import Page

from ..models.company import Company, Employee, SocialMediaLink, JobListing, Product, LifeUpdate
from ..core.exceptions import ProfileNotFoundError
from ..callbacks import ProgressCallback, SilentCallback
from .base import BaseScraper

logger = logging.getLogger(__name__)


class CompanyScraper(BaseScraper):
    """
    Scraper for LinkedIn company pages.
    
    Example:
        async with BrowserManager() as browser:
            scraper = CompanyScraper(browser.page)
            company = await scraper.scrape("https://www.linkedin.com/company/microsoft/")
            print(company.to_json())
    """
    
    def __init__(self, page: Page, callback: Optional[ProgressCallback] = None):
        """
        Initialize company scraper.
        
        Args:
            page: Playwright page object
            callback: Optional progress callback
        """
        super().__init__(page, callback or SilentCallback())
    
    async def scrape(self, linkedin_url: str) -> Company:
        """
        Scrape a LinkedIn company page.
        
        Args:
            linkedin_url: URL of the LinkedIn company page
            
        Returns:
            Company object with scraped data
            
        Raises:
            ProfileNotFoundError: If company page not found
        """
        logger.info(f"Starting company scraping: {linkedin_url}")
        await self.callback.on_start("company", linkedin_url)
        
        # Navigate to company page
        await self.navigate_and_wait(linkedin_url)
        await self.callback.on_progress("Navigated to company page", 10)
        
        # Check if page exists
        await self.check_rate_limit()
        
        # Extract basic info from main page
        name = await self._get_name()
        await self.callback.on_progress(f"Got company name: {name}", 20)
        
        # Navigate to About page to get detailed information
        about_url = linkedin_url.rstrip('/') + '/about/'
        await self.navigate_and_wait(about_url)
        await self.wait_and_focus(1.5)
        await self.callback.on_progress("Navigated to About page", 25)
        
        # Extract about/description section
        about_us = await self._get_about()
        await self.callback.on_progress("Got about section", 30)
        
        # Extract overview details from About page
        overview = await self._get_overview()
        await self.callback.on_progress("Got overview details", 50)
        
        # Navigate back to main page to get additional info
        await self.navigate_and_wait(linkedin_url)
        await self.wait_and_focus(1)
        await self.callback.on_progress("Back to main page", 60)
        
        # Extract additional info from main page
        followers_count = await self._get_followers_count()
        logo_url = await self._get_logo_url()
        social_media_links = await self._get_social_media_links()
        tags_keywords = await self._get_tags_keywords()
        await self.callback.on_progress("Got additional info", 65)
        
        # Navigate to People page to get employees
        employees = await self._get_employees(linkedin_url)
        await self.callback.on_progress(f"Got {len(employees)} employees", 70)
        
        # Navigate to Jobs page to get job listings
        job_listings = await self._get_job_listings(linkedin_url)
        await self.callback.on_progress(f"Got {len(job_listings)} job listings", 75)
        
        # Navigate to Posts page to get recent posts
        recent_posts = await self._get_recent_posts(linkedin_url, company_name=name)
        await self.callback.on_progress(f"Got {len(recent_posts)} recent posts", 80)
        
        # Navigate to Products page to get products/services
        products = await self._get_products(linkedin_url)
        await self.callback.on_progress(f"Got {len(products)} products", 82)
        
        # Navigate to Services page to get services
        services = await self._get_services(linkedin_url)
        await self.callback.on_progress(f"Got {len(services)} services", 83)
        
        # Navigate to Life page to get life/culture updates
        life_updates = await self._get_life_updates(linkedin_url)
        await self.callback.on_progress(f"Got {len(life_updates)} life updates", 84)
        
        # Navigate back to About page to get mission/values
        await self.navigate_and_wait(about_url)
        await self.wait_and_focus(1)
        mission, values = await self._get_mission_values()
        await self.callback.on_progress("Got mission and values", 86)
        
        # Parse employee count from company_size
        employee_count = self._parse_employee_count(overview.get('company_size'))
        
        # Create company object
        company = Company(
            linkedin_url=linkedin_url,
            name=name,
            about_us=about_us,
            employees=employees,
            followers_count=followers_count,
            logo_url=logo_url,
            social_media_links=social_media_links,
            recent_posts=recent_posts,
            job_listings=job_listings,
            products=products + services,  # Combine products and services
            life_updates=life_updates,
            tags_keywords=tags_keywords,
            mission=mission,
            values=values,
            headcount=employee_count,
            **overview
        )
        
        await self.callback.on_progress("Scraping complete", 100)
        await self.callback.on_complete("company", company)
        
        logger.info(f"Successfully scraped company: {name}")
        return company
    
    async def _get_name(self) -> str:
        """Extract company name."""
        try:
            # Try main heading
            name_elem = self.page.locator('h1').first
            name = await name_elem.inner_text()
            return name.strip()
        except Exception as e:
            logger.warning(f"Error getting company name: {e}")
            return "Unknown Company"
    
    async def _get_about(self) -> Optional[str]:
        """Extract about/description section."""
        try:
            # Look for "Overview" or "About us" section
            # Try multiple selectors for the about section
            about_selectors = [
                'section:has-text("Overview")',
                'section:has-text("About us")',
                '[data-view-name="profile-card"]:has-text("Overview")',
                'h2:has-text("Overview")',
            ]
            
            for selector in about_selectors:
                try:
                    section = self.page.locator(selector).first
                    if await section.count() > 0:
                        # Get the parent section
                        parent = section.locator('xpath=ancestor::section[1]')
                        if await parent.count() == 0:
                            parent = section.locator('xpath=ancestor::div[contains(@class, "section")][1]')
                        
                        if await parent.count() > 0:
                            # Get the content paragraph
                            paragraphs = await parent.locator('p').all()
                            if paragraphs:
                                about = await paragraphs[0].inner_text()
                                if about and len(about.strip()) > 20:
                                    return about.strip()
                except:
                    continue
            
            # Fallback: look for any section with "Overview" text
            sections = await self.page.locator('section').all()
            for section in sections:
                section_text = await section.inner_text()
                if 'Overview' in section_text[:100] or 'About us' in section_text[:100]:
                    paragraphs = await section.locator('p').all()
                    if paragraphs:
                        about = await paragraphs[0].inner_text()
                        if about and len(about.strip()) > 20:
                            return about.strip()
            
            return None
        except Exception as e:
            logger.debug(f"Error getting about section: {e}")
            return None
    
    async def _get_overview(self) -> dict:
        """
        Extract company overview details (website, phone, headquarters, founded, industry,
        company_type, company_size, specialties) from the About page.
        
        Returns dict with: website, phone, headquarters, founded, industry,
        company_type, company_size, specialties
        """
        overview = {
            "website": None,
            "phone": None,
            "headquarters": None,
            "founded": None,
            "industry": None,
            "company_type": None,
            "company_size": None,
            "specialties": None
        }
        
        try:
            # Scroll to load all content
            await self.scroll_page_to_half()
            await self.wait_and_focus(1)
            
            # Method 1: Try to find data using definition lists (dt/dd structure)
            dt_elements = await self.page.locator('dt').all()
            
            for dt in dt_elements:
                try:
                    label = await dt.inner_text()
                    if not label:
                        continue
                    label = label.strip().lower()
                    
                    dd = dt.locator('xpath=following-sibling::dd[1]')
                    if await dd.count() > 0:
                        value = await dd.inner_text()
                        if value:
                            value = value.strip()
                            
                            if 'website' in label:
                                # Try to get the actual URL from the link
                                link = dd.locator('a').first
                                if await link.count() > 0:
                                    href = await link.get_attribute('href')
                                    if href:
                                        overview['website'] = href
                                else:
                                    overview['website'] = value
                            elif 'phone' in label:
                                # Try to get phone from link or text
                                link = dd.locator('a').first
                                if await link.count() > 0:
                                    href = await link.get_attribute('href')
                                    if href and 'tel:' in href:
                                        overview['phone'] = href.replace('tel:', '')
                                    else:
                                        overview['phone'] = value
                                else:
                                    overview['phone'] = value
                            elif 'headquarters' in label or 'location' in label:
                                overview['headquarters'] = value
                            elif 'founded' in label:
                                overview['founded'] = value
                            elif 'industry' in label or 'industries' in label:
                                overview['industry'] = value
                            elif 'company type' in label or 'type' in label:
                                overview['company_type'] = value
                            elif 'company size' in label or 'size' in label:
                                overview['company_size'] = value
                            elif 'specialt' in label:
                                overview['specialties'] = value
                except Exception as e:
                    logger.debug(f"Error parsing dt/dd element: {e}")
                    continue
            
            # Method 2: Try LinkedIn's new structure with info items
            if not any([overview['website'], overview['phone'], overview['headquarters'], overview['founded']]):
                info_items = await self.page.locator('.org-top-card-summary-info-list__info-item, .org-about-company-module__info-item').all()
                
                for item in info_items:
                    try:
                        text = await item.inner_text()
                        if not text:
                            continue
                        text = text.strip()
                        text_lower = text.lower()
                        
                        # Check for website link
                        link = item.locator('a').first
                        if await link.count() > 0:
                            href = await link.get_attribute('href')
                            if href and 'linkedin' not in href.lower() and ('http' in href or 'www.' in href):
                                if not overview['website']:
                                    overview['website'] = href
                            elif href and 'tel:' in href:
                                if not overview['phone']:
                                    overview['phone'] = href.replace('tel:', '')
                        
                        # Detect what kind of information this is based on content patterns
                        if 'employee' in text_lower or ('k+' in text_lower or '-' in text and 'employee' in text_lower):
                            if not overview['company_size']:
                                overview['company_size'] = text
                        elif ',' in text and (any(loc in text for loc in ['Hyderabad', 'Telangana', 'Washington', 'California', 'New York', 'Texas', 'United States', 'United Kingdom', 'India', 'Bangalore', 'Mumbai', 'Delhi'])):
                            if not overview['headquarters']:
                                overview['headquarters'] = text
                        elif any(ind in text_lower for ind in ['software', 'technology', 'financial', 'healthcare', 'retail', 'manufacturing', 'consulting', 'education', 'services', 'it consulting']):
                            if not overview['industry']:
                                overview['industry'] = text
                        elif text.isdigit() and len(text) == 4 and int(text) >= 1800 and int(text) <= 2100:
                            # Likely a year (founded)
                            if not overview['founded']:
                                overview['founded'] = text
                        elif 'follower' in text_lower:
                            # Skip follower count
                            continue
                    except Exception as e:
                        logger.debug(f"Error parsing info item: {e}")
                        continue
            
            # Method 3: Look for website and phone in links throughout the page
            if not overview['website'] or not overview['phone']:
                links = await self.page.locator('a[href]').all()
                for link in links:
                    try:
                        href = await link.get_attribute('href')
                        if not href:
                            continue
                        
                        # Check for website
                        if not overview['website']:
                            if 'linkedin' not in href.lower() and ('http' in href or 'www.' in href):
                                link_text = await link.inner_text()
                                # Skip navigation and common LinkedIn links
                                if link_text and len(link_text.strip()) > 0:
                                    # Check if it's in the overview section
                                    parent = link.locator('xpath=ancestor::section[1] | ancestor::div[contains(@class, "overview")][1]')
                                    if await parent.count() > 0:
                                        overview['website'] = href
                                        break
                        
                        # Check for phone
                        if not overview['phone']:
                            if 'tel:' in href:
                                overview['phone'] = href.replace('tel:', '').strip()
                    except:
                        continue
            
            # Method 4: Look for specialties in a dedicated section
            if not overview['specialties']:
                # Try to find specialties section
                specialty_selectors = [
                    'dt:has-text("Specialties")',
                    'dt:has-text("Specialty")',
                    'h3:has-text("Specialties")',
                    '[data-view-name="profile-card"]:has-text("Specialties")',
                ]
                
                for selector in specialty_selectors:
                    try:
                        elem = self.page.locator(selector).first
                        if await elem.count() > 0:
                            # Get the value
                            parent = elem.locator('xpath=ancestor::section[1] | ancestor::div[contains(@class, "section")][1]')
                            if await parent.count() > 0:
                                # Try to get from dd if dt/dd structure
                                dd = elem.locator('xpath=following-sibling::dd[1]')
                                if await dd.count() > 0:
                                    specialties = await dd.inner_text()
                                    if specialties:
                                        overview['specialties'] = specialties.strip()
                                        break
                                else:
                                    # Get text from parent section
                                    text = await parent.inner_text()
                                    if 'Specialties' in text:
                                        # Extract text after "Specialties"
                                        parts = text.split('Specialties')
                                        if len(parts) > 1:
                                            specialties = parts[1].strip()
                                            # Clean up - take first meaningful line
                                            lines = [l.strip() for l in specialties.split('\n') if l.strip()]
                                            if lines:
                                                overview['specialties'] = lines[0]
                                                break
                    except:
                        continue
            
        except Exception as e:
            logger.debug(f"Error getting company overview: {e}")
        
        return overview
    
    async def _get_employees(self, linkedin_url: str, limit: int = 100) -> list[Employee]:
        """
        Extract employees/people from the People tab.
        
        Args:
            linkedin_url: Base company URL
            limit: Maximum number of employees to scrape
            
        Returns:
            List of Employee objects
        """
        employees = []
        
        try:
            # Navigate to People page
            people_url = linkedin_url.rstrip('/') + '/people/'
            await self.navigate_and_wait(people_url)
            await self.wait_and_focus(2)
            
            # Wait for content to load
            await self.page.wait_for_selector("main", timeout=10000)
            
            # Scroll to load more employees
            await self.scroll_page_to_half()
            await self.scroll_page_to_bottom(pause_time=1.0, max_scrolls=5)
            await self.wait_and_focus(1)
            
            # Try multiple selectors for employee cards
            employee_selectors = [
                'li.org-people-profile-card__profile-item',
                'li[data-view-name="org-people-profile-card"]',
                '.org-people-profile-card',
                'li:has(a[href*="/in/"])',
            ]
            
            employee_elements = []
            for selector in employee_selectors:
                elements = await self.page.locator(selector).all()
                if elements:
                    employee_elements = elements
                    break
            
            # If no specific employee cards found, try finding all profile links
            if not employee_elements:
                # Look for links to profiles within the main content
                main_section = self.page.locator('main').first
                if await main_section.count() > 0:
                    profile_links = await main_section.locator('a[href*="/in/"]').all()
                    # Filter to get unique employee cards
                    seen_urls = set()
                    for link in profile_links:
                        href = await link.get_attribute('href')
                        if href and '/in/' in href and href not in seen_urls:
                            # Check if this link is in an employee card structure
                            parent = link.locator('xpath=ancestor::li[1] | ancestor::div[contains(@class, "card")][1]')
                            if await parent.count() > 0:
                                employee_elements.append(parent)
                                seen_urls.add(href)
            
            # Extract employee information
            for i, elem in enumerate(employee_elements[:limit]):
                try:
                    # Get name
                    name = None
                    name_selectors = [
                        'span[aria-hidden="true"]',
                        '.org-people-profile-card__profile-title',
                        'h3',
                        'a[href*="/in/"] span',
                    ]
                    
                    for selector in name_selectors:
                        name_elem = elem.locator(selector).first
                        if await name_elem.count() > 0:
                            name_text = await name_elem.inner_text()
                            if name_text and len(name_text.strip()) > 0 and len(name_text.strip()) < 100:
                                name = name_text.strip()
                                break
                    
                    # If name not found, try getting from link text
                    if not name:
                        link = elem.locator('a[href*="/in/"]').first
                        if await link.count() > 0:
                            name_text = await link.inner_text()
                            if name_text and len(name_text.strip()) > 0:
                                name = name_text.strip()
                    
                    if not name:
                        continue
                    
                    # Get designation/role
                    designation = None
                    designation_selectors = [
                        '.org-people-profile-card__profile-info',
                        '.t-14.t-black--light',
                        'span.t-14',
                        'div:has-text(" at ")',
                    ]
                    
                    for selector in designation_selectors:
                        desig_elem = elem.locator(selector).first
                        if await desig_elem.count() > 0:
                            desig_text = await desig_elem.inner_text()
                            if desig_text and len(desig_text.strip()) > 0 and len(desig_text.strip()) < 200:
                                # Clean up designation text
                                desig_text = desig_text.strip()
                                # Remove common prefixes
                                for prefix in ['at ', 'At ', 'AT ']:
                                    if desig_text.startswith(prefix):
                                        desig_text = desig_text[len(prefix):].strip()
                                designation = desig_text
                                break
                    
                    # Get LinkedIn URL
                    linkedin_url_employee = None
                    link = elem.locator('a[href*="/in/"]').first
                    if await link.count() > 0:
                        href = await link.get_attribute('href')
                        if href:
                            # Clean up URL
                            if '?' in href:
                                href = href.split('?')[0]
                            if not href.startswith('http'):
                                href = f"https://www.linkedin.com{href}"
                            linkedin_url_employee = href
                    
                    # Create employee object
                    if name:
                        employees.append(Employee(
                            name=name,
                            designation=designation,
                            linkedin_url=linkedin_url_employee
                        ))
                
                except Exception as e:
                    logger.debug(f"Error parsing employee {i}: {e}")
                    continue
            
        except Exception as e:
            logger.warning(f"Error getting employees: {e}")
        
        return employees
    
    async def _get_followers_count(self) -> Optional[str]:
        """Extract follower count from company page."""
        try:
            # Look for follower count in various places
            follower_selectors = [
                'text=/\\d+[KMB]?\\s+followers/i',
                'span:has-text("followers")',
                '.org-top-card-summary-info-list__info-item:has-text("followers")',
            ]
            
            for selector in follower_selectors:
                try:
                    elem = self.page.locator(selector).first
                    if await elem.count() > 0:
                        text = await elem.inner_text()
                        if 'followers' in text.lower():
                            # Extract number
                            import re
                            match = re.search(r'(\d+[KMB]?)\s*followers', text, re.IGNORECASE)
                            if match:
                                return match.group(1) + ' followers'
                            return text.strip()
                except:
                    continue
            
            # Try to find in main page text
            body_text = await self.page.locator('body').inner_text()
            import re
            match = re.search(r'(\d+[KMB]?)\s*followers', body_text, re.IGNORECASE)
            if match:
                return match.group(1) + ' followers'
            
            return None
        except Exception as e:
            logger.debug(f"Error getting followers count: {e}")
            return None
    
    async def _get_logo_url(self) -> Optional[str]:
        """Extract company logo URL."""
        try:
            # Look for company logo
            logo_selectors = [
                '.org-top-card-primary-content__logo img',
                '.org-top-card__primary-content img',
                'img[alt*="logo"]',
                'img[alt*="Logo"]',
                '.org-top-card-summary__image img',
            ]
            
            for selector in logo_selectors:
                try:
                    img = self.page.locator(selector).first
                    if await img.count() > 0:
                        src = await img.get_attribute('src')
                        if src and 'linkedin' not in src.lower():
                            return src
                        # Try data-src or other attributes
                        data_src = await img.get_attribute('data-src')
                        if data_src:
                            return data_src
                except:
                    continue
            
            return None
        except Exception as e:
            logger.debug(f"Error getting logo URL: {e}")
            return None
    
    async def _get_social_media_links(self) -> list[SocialMediaLink]:
        """Extract social media links from company page."""
        social_links = []
        
        try:
            # Look for social media links
            links = await self.page.locator('a[href]').all()
            
            for link in links:
                try:
                    href = await link.get_attribute('href')
                    if not href:
                        continue
                    
                    href_lower = href.lower()
                    platform = None
                    
                    # Detect platform
                    if 'twitter.com' in href_lower or 'x.com' in href_lower:
                        platform = 'Twitter'
                    elif 'facebook.com' in href_lower:
                        platform = 'Facebook'
                    elif 'instagram.com' in href_lower:
                        platform = 'Instagram'
                    elif 'youtube.com' in href_lower:
                        platform = 'YouTube'
                    elif 'github.com' in href_lower:
                        platform = 'GitHub'
                    elif 'linkedin.com' not in href_lower and ('http' in href or 'www.' in href):
                        # Check if it's mentioned as social media
                        link_text = await link.inner_text()
                        if link_text and any(platform in link_text.lower() for platform in ['twitter', 'facebook', 'instagram', 'youtube']):
                            if 'twitter' in link_text.lower():
                                platform = 'Twitter'
                            elif 'facebook' in link_text.lower():
                                platform = 'Facebook'
                            elif 'instagram' in link_text.lower():
                                platform = 'Instagram'
                            elif 'youtube' in link_text.lower():
                                platform = 'YouTube'
                    
                    if platform:
                        social_links.append(SocialMediaLink(platform=platform, url=href))
                except:
                    continue
            
        except Exception as e:
            logger.debug(f"Error getting social media links: {e}")
        
        return social_links
    
    async def _get_tags_keywords(self) -> list[str]:
        """Extract tags/keywords from company page."""
        tags = []
        
        try:
            # Look for tags/keywords in various places
            tag_selectors = [
                '.org-top-card-summary__tag',
                '.org-top-card-summary-info-list__info-item',
                '[data-view-name="profile-card"] span',
            ]
            
            for selector in tag_selectors:
                try:
                    elements = await self.page.locator(selector).all()
                    for elem in elements:
                        text = await elem.inner_text()
                        if text and len(text.strip()) > 0 and len(text.strip()) < 100:
                            # Check if it looks like a tag/keyword
                            if not any(word in text.lower() for word in ['followers', 'employees', 'founded', 'headquarters']):
                                if text.strip() not in tags:
                                    tags.append(text.strip())
                except:
                    continue
            
            # Also check specialties as tags
            # This will be handled in overview, but we can add specialties to tags too
            
        except Exception as e:
            logger.debug(f"Error getting tags/keywords: {e}")
        
        return tags[:20]  # Limit to 20 tags
    
    async def _get_job_listings(self, linkedin_url: str, limit: int = 50) -> list[JobListing]:
        """Extract job listings from Jobs tab."""
        jobs = []
        
        try:
            # Navigate to Jobs page
            jobs_url = linkedin_url.rstrip('/') + '/jobs/'
            await self.navigate_and_wait(jobs_url)
            await self.wait_and_focus(4)
            
            # Wait for content - try multiple approaches
            try:
                await self.page.wait_for_selector("main", timeout=15000)
            except:
                pass
            
            # Aggressive scrolling to load ALL jobs
            logger.info("Scrolling to load job listings...")
            for i in range(10):  # Scroll 10 times
                await self.page.evaluate('window.scrollBy(0, 800)')
                await self.wait_and_focus(1.5)
            
            # Scroll to bottom
            await self.scroll_page_to_bottom(pause_time=2, max_scrolls=10)
            await self.wait_and_focus(2)
            
            # Try to get job count from page text
            page_text = await self.page.locator('body').inner_text()
            import re
            job_count_match = re.search(r'(\d+[\,\d]*)\s+job', page_text)
            if job_count_match:
                logger.info(f"Found job count: {job_count_match.group(1)}")
            
            # Look for job listings with multiple selector strategies
            job_elements = []
            seen_job_urls = set()
            
            # Strategy 1: Look for list items in results list
            try:
                selectors = [
                    'ul.jobs-search__results-list > li',
                    'ul[class*="jobs"] li',
                    'div.jobs-search-results-list li',
                    'li.job-search-card',
                    'div[data-job-id]',
                ]
                
                for selector in selectors:
                    elements = await self.page.locator(selector).all()
                    if elements and len(elements) > 5:  # Only use if we found multiple
                        job_elements = elements
                        logger.info(f"Found {len(job_elements)} job elements with selector: {selector}")
                        break
            except Exception as e:
                logger.debug(f"Strategy 1 failed: {e}")
            
            # Strategy 2: Look for all job links and their parent containers
            if len(job_elements) < 5:
                try:
                    job_links = await self.page.locator('a[href*="/jobs/view/"], a[href*="/jobs/collections/"]').all()
                    logger.info(f"Found {len(job_links)} job links")
                    
                    # Get parent containers of job links
                    for link in job_links[:limit * 2]:
                        try:
                            href = await link.get_attribute('href')
                            if href and '/jobs/view/' in href:
                                # Get job ID from URL
                                job_id = href.split('/jobs/view/')[-1].split('?')[0].split('/')[0]
                                if job_id and job_id not in seen_job_urls:
                                    seen_job_urls.add(job_id)
                                    # Get the parent card element
                                    parent = link.locator('xpath=ancestor::li[1]')
                                    if await parent.count() > 0:
                                        job_elements.append(parent.first)
                                    else:
                                        job_elements.append(link)
                                    
                                    if len(job_elements) >= limit:
                                        break
                        except:
                            continue
                    
                    logger.info(f"Strategy 2: Collected {len(job_elements)} job containers")
                except Exception as e:
                    logger.debug(f"Strategy 2 failed: {e}")
            
            # Strategy 3: Extract from page HTML directly
            if len(job_elements) < 5:
                try:
                    page_content = await self.page.content()
                    import re
                    # Find all job IDs in HTML
                    job_ids = re.findall(r'/jobs/view/(\d+)', page_content)
                    unique_job_ids = list(set(job_ids))[:limit]
                    logger.info(f"Strategy 3: Found {len(unique_job_ids)} unique job IDs in HTML")
                    
                    # For each job ID, try to find its element
                    for job_id in unique_job_ids:
                        try:
                            link = self.page.locator(f'a[href*="/jobs/view/{job_id}"]').first
                            if await link.count() > 0:
                                job_elements.append(link)
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"Strategy 3 failed: {e}")
            
            # Extract job information
            for i, elem in enumerate(job_elements):
                try:
                    # Get job title
                    title = None
                    title_selectors = [
                        'a[href*="/jobs/view/"]',
                        '.job-card-list__title',
                        '.job-search-card__title',
                        'h3',
                        'strong',
                    ]
                    
                    for selector in title_selectors:
                        try:
                            title_elem = elem.locator(selector).first
                            if await title_elem.count() > 0:
                                title = await title_elem.inner_text()
                                if title and len(title.strip()) > 0:
                                    title = title.strip()
                                    # Clean up title
                                    title = title.split('\n')[0].strip()
                                    break
                        except:
                            continue
                    
                    # Get job URL
                    job_url = None
                    try:
                        link = elem.locator('a[href*="/jobs/"]').first
                        if await link.count() > 0:
                            href = await link.get_attribute('href')
                            if href:
                                if '?' in href:
                                    href = href.split('?')[0]
                                if not href.startswith('http'):
                                    href = f"https://www.linkedin.com{href}"
                                job_url = href
                    except:
                        pass
                    
                    # Get location
                    location = None
                    location_selectors = [
                        '.job-search-card__location',
                        '.job-card-list__location',
                        'span:has-text("·")',
                    ]
                    
                    for selector in location_selectors:
                        try:
                            location_elem = elem.locator(selector).first
                            if await location_elem.count() > 0:
                                location = await location_elem.inner_text()
                                if location and len(location.strip()) > 0:
                                    location = location.strip()
                                    break
                        except:
                            continue
                    
                    # Get posted date
                    posted_date = None
                    try:
                        time_elem = elem.locator('time').first
                        if await time_elem.count() > 0:
                            posted_date = await time_elem.get_attribute('datetime')
                            if not posted_date:
                                posted_date = await time_elem.inner_text()
                    except:
                        pass
                    
                    if title or job_url:
                        jobs.append(JobListing(
                            title=title or "Job Opening",
                            location=location,
                            linkedin_url=job_url,
                            posted_date=posted_date
                        ))
                except Exception as e:
                    logger.debug(f"Error parsing job listing {i}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(jobs)} job listings")
            
        except Exception as e:
            logger.warning(f"Error getting job listings: {e}")
        
        return jobs
    
    async def _get_recent_posts(self, linkedin_url: str, limit: int = 50, company_name: Optional[str] = None) -> list[dict]:
        """Extract recent posts from Posts tab."""
        posts = []
        
        try:
            # Navigate to Posts page
            posts_url = linkedin_url.rstrip('/') + '/posts/?feedView=all'
            await self.navigate_and_wait(posts_url)
            await self.wait_and_focus(4)
            
            # Try to get company name from page if not provided
            if not company_name:
                try:
                    name_elem = self.page.locator('h1, span[class*="name"], a[class*="name"]').first
                    if await name_elem.count() > 0:
                        name_text = await name_elem.inner_text()
                        if name_text:
                            company_name = name_text.strip()
                except:
                    pass
            
            # Wait for content
            try:
                await self.page.wait_for_selector("main", timeout=15000)
            except:
                pass
            
            # Aggressive scrolling to load ALL posts
            logger.info("Scrolling to load all posts...")
            for i in range(15):  # Scroll 15 times to load more posts
                await self.page.evaluate('window.scrollBy(0, 1000)')
                await self.wait_and_focus(1.5)
                
                # Check if we've loaded enough posts
                current_posts = await self.page.locator('div[data-urn*="activity"], article').count()
                logger.info(f"Loaded {current_posts} posts so far...")
            
            # Final scroll to bottom
            await self.scroll_page_to_bottom(pause_time=2, max_scrolls=10)
            await self.wait_and_focus(3)
            
            # Strategy 1: Look for feed posts with multiple selectors
            post_containers = []
            try:
                # Try multiple selectors for post containers - more comprehensive
                selectors = [
                    'div[data-urn*="activity"]',
                    'div.feed-shared-update-v2',
                    'article[data-urn]',
                    'div[class*="feed-shared-update"]',
                    'li.feed-shared-update-v2',
                    'div[class*="update-components"]',
                    'article[class*="feed"]',
                    'div[data-test-id*="activity"]',
                    'div[data-test-id*="feed"]',
                    'li[class*="feed"]',
                ]
                
                for selector in selectors:
                    containers = await self.page.locator(selector).all()
                    if len(containers) > len(post_containers):
                        post_containers = containers
                        logger.info(f"Found {len(containers)} containers with selector: {selector}")
                
                if post_containers:
                    logger.info(f"Total post containers found: {len(post_containers)}")
                else:
                    # Try a more generic approach - look for any divs with activity URNs
                    logger.info("Trying generic approach to find posts...")
                    all_divs = await self.page.locator('div').all()
                    for div in all_divs[:200]:  # Limit to first 200 to avoid timeout
                        try:
                            data_urn = await div.get_attribute('data-urn')
                            if data_urn and 'activity' in data_urn:
                                post_containers.append(div)
                                if len(post_containers) >= limit:
                                    break
                        except:
                            continue
                    logger.info(f"Found {len(post_containers)} posts with generic approach")
            except Exception as e:
                logger.debug(f"Error finding post containers: {e}")
            
            # Extract posts from containers
            seen_urls = set()
            for container in post_containers:
                try:
                    # Get post URL
                    post_url = None
                    link_selectors = [
                        'a[href*="/feed/update/"]',
                        'a[href*="/posts/"]',
                        'a[data-urn*="activity"]',
                    ]
                    
                    for selector in link_selectors:
                        link = container.locator(selector).first
                        if await link.count() > 0:
                            href = await link.get_attribute('href')
                            if href:
                                if '?' in href:
                                    href = href.split('?')[0]
                                if not href.startswith('http'):
                                    href = f"https://www.linkedin.com{href}"
                                post_url = href
                                break
                    
                    if not post_url or post_url in seen_urls:
                        continue
                    
                    # Get post text/preview - improved extraction
                    post_text = None
                    text_selectors = [
                        '.feed-shared-update-v2__description',
                        '.feed-shared-text',
                        'div[data-test-id="main-feed-activity-card__commentary"]',
                        '.update-components-text',
                        'span[dir="ltr"]',
                        'div[class*="feed-shared-text"]',
                        'div[class*="update-components-text"]',
                        'p[class*="feed-shared-text"]',
                    ]
                    
                    for selector in text_selectors:
                        text_elem = container.locator(selector).first
                        if await text_elem.count() > 0:
                            text = await text_elem.inner_text()
                            if text and len(text.strip()) > 20:
                                # Clean text - remove company name if it's just the name
                                text_clean = text.strip()
                                # Skip if it's just company name or very short
                                if (len(text_clean) > 30 and 
                                    (not company_name or not text_clean.startswith(company_name))):
                                    post_text = text_clean
                                    break
                    
                    # If no text found, get any text from container but filter out company name
                    if not post_text:
                        try:
                            all_text = await container.inner_text()
                            if all_text and len(all_text.strip()) > 30:
                                # Split into lines and find meaningful content
                                lines = [l.strip() for l in all_text.split('\n') if l.strip()]
                                for line in lines:
                                    # Skip company name, connection info, etc.
                                    if (len(line) > 30 and 
                                        (not company_name or not line.startswith(company_name)) and
                                        'connection' not in line.lower() and
                                        'followers' not in line.lower() and
                                        'mutual' not in line.lower() and
                                        not line.startswith('·') and
                                        'degree' not in line.lower() and
                                        '1st' not in line and
                                        '2nd' not in line):
                                        post_text = line
                                        break
                        except:
                            pass
                    
                    # If still no text, try to get from span elements
                    if not post_text:
                        try:
                            spans = await container.locator('span[dir="ltr"]').all()
                            for span in spans[:5]:  # Check first 5 spans
                                text = await span.inner_text()
                                if text and len(text.strip()) > 30:
                                    text_clean = text.strip()
                                    if (not company_name or not text_clean.startswith(company_name)):
                                        post_text = text_clean
                                        break
                        except:
                            pass
                    
                    if post_url:
                        # Use post text if available, otherwise use URL
                        preview = post_text[:300] if post_text else f"Post: {post_url}"
                        posts.append({
                            'url': post_url,
                            'preview': preview
                        })
                        seen_urls.add(post_url)
                        
                        if len(posts) >= limit:
                            break
                        
                except Exception as e:
                    logger.debug(f"Error parsing post container: {e}")
                    continue
            
            # Strategy 2: Extract from page HTML directly
            if len(posts) < 10:
                try:
                    page_content = await self.page.content()
                    import re
                    
                    # Find all activity URNs in HTML
                    activity_urns = re.findall(r'urn:li:activity:(\d+)', page_content)
                    unique_urns = list(set(activity_urns))[:limit]
                    logger.info(f"Strategy 2: Found {len(unique_urns)} unique activity URNs in HTML")
                    
                    for urn in unique_urns:
                        if len(posts) >= limit:
                            break
                        
                        post_url = f"https://www.linkedin.com/feed/update/urn:li:activity:{urn}/"
                        if post_url not in seen_urls:
                            # Try to find text for this URN
                            try:
                                urn_elem = self.page.locator(f'[data-urn*="{urn}"]').first
                                if await urn_elem.count() > 0:
                                    text = await urn_elem.inner_text()
                                    if text and len(text.strip()) > 30:
                                        lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 20]
                                        preview = lines[0] if lines else text.strip()
                                        posts.append({
                                            'url': post_url,
                                            'preview': preview[:200]
                                        })
                                        seen_urls.add(post_url)
                            except:
                                # Add URL without preview
                                posts.append({
                                    'url': post_url,
                                    'preview': 'Post content'
                                })
                                seen_urls.add(post_url)
                except Exception as e:
                    logger.debug(f"Strategy 2 failed: {e}")
            
            # Strategy 3: Look for any activity links
            if len(posts) < 5:
                try:
                    activity_links = await self.page.locator('a[href*="/feed/update/"], a[href*="activity:"]').all()
                    logger.info(f"Strategy 3: Found {len(activity_links)} activity links")
                    
                    for link in activity_links:
                        if len(posts) >= limit:
                            break
                        
                        try:
                            href = await link.get_attribute('href')
                            if href and href not in seen_urls:
                                if '?' in href:
                                    href = href.split('?')[0]
                                if not href.startswith('http'):
                                    href = f"https://www.linkedin.com{href}"
                                
                                text = await link.inner_text()
                                preview = text.strip()[:200] if text and len(text.strip()) > 10 else 'Post content'
                                
                                posts.append({
                                    'url': href,
                                    'preview': preview
                                })
                                seen_urls.add(href)
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"Strategy 3 failed: {e}")
            
            logger.info(f"Successfully extracted {len(posts)} posts")
            
        except Exception as e:
            logger.warning(f"Error getting recent posts: {e}")
        
        return posts
    
    async def _get_mission_values(self) -> tuple[Optional[str], Optional[str]]:
        """Extract mission and values from About page."""
        mission = None
        values = None
        
        try:
            # Look for mission section
            mission_selectors = [
                'h2:has-text("Mission")',
                'h3:has-text("Mission")',
                'section:has-text("Mission")',
            ]
            
            for selector in mission_selectors:
                try:
                    elem = self.page.locator(selector).first
                    if await elem.count() > 0:
                        parent = elem.locator('xpath=ancestor::section[1] | ancestor::div[contains(@class, "section")][1]')
                        if await parent.count() > 0:
                            text = await parent.inner_text()
                            if 'Mission' in text:
                                # Extract mission text
                                parts = text.split('Mission')
                                if len(parts) > 1:
                                    mission_text = parts[1].strip()
                                    # Take first paragraph
                                    lines = [l.strip() for l in mission_text.split('\n') if l.strip()]
                                    if lines:
                                        mission = lines[0]
                                        break
                except:
                    continue
            
            # Look for values section
            values_selectors = [
                'h2:has-text("Values")',
                'h3:has-text("Values")',
                'section:has-text("Values")',
            ]
            
            for selector in values_selectors:
                try:
                    elem = self.page.locator(selector).first
                    if await elem.count() > 0:
                        parent = elem.locator('xpath=ancestor::section[1] | ancestor::div[contains(@class, "section")][1]')
                        if await parent.count() > 0:
                            text = await parent.inner_text()
                            if 'Values' in text:
                                # Extract values text
                                parts = text.split('Values')
                                if len(parts) > 1:
                                    values_text = parts[1].strip()
                                    # Take first paragraph
                                    lines = [l.strip() for l in values_text.split('\n') if l.strip()]
                                    if lines:
                                        values = lines[0]
                                        break
                except:
                    continue
            
        except Exception as e:
            logger.debug(f"Error getting mission/values: {e}")
        
        return mission, values
    
    def _parse_employee_count(self, company_size: Optional[str]) -> Optional[int]:
        """Parse employee count from company_size string."""
        if not company_size:
            return None
        
        try:
            import re
            # Extract numbers from strings like "11-50 employees", "1,001-5,000 employees", "10K+ employees"
            # Try to get the upper bound
            if '-' in company_size:
                # Range like "11-50"
                parts = company_size.split('-')
                if len(parts) >= 2:
                    upper = parts[1].strip()
                    # Remove "employees" and get number
                    upper = re.sub(r'[^\d]', '', upper)
                    if upper:
                        return int(upper)
            elif 'K+' in company_size or 'k+' in company_size:
                # Like "10K+"
                match = re.search(r'(\d+)K?\+', company_size)
                if match:
                    return int(match.group(1)) * 1000
            elif 'M+' in company_size or 'm+' in company_size:
                # Like "1M+"
                match = re.search(r'(\d+)M?\+', company_size)
                if match:
                    return int(match.group(1)) * 1000000
            else:
                # Try to extract any number
                numbers = re.findall(r'\d+', company_size.replace(',', ''))
                if numbers:
                    return int(numbers[-1])  # Get last number
        except:
            pass
        
        return None
    
    async def _get_products(self, linkedin_url: str, limit: int = 10) -> list[Product]:
        """Extract products/services from Products tab."""
        products = []
        
        try:
            # Navigate to Products page
            products_url = linkedin_url.rstrip('/') + '/products/'
            await self.navigate_and_wait(products_url)
            await self.wait_and_focus(2)
            
            # Wait for content
            await self.page.wait_for_selector("main", timeout=10000)
            await self.scroll_page_to_half()
            await self.wait_and_focus(1)
            
            # Look for product cards
            product_selectors = [
                '.org-products-module__product-card',
                '[data-view-name="org-products-module-product-card"]',
                'section:has-text("Products") div[class*="card"]',
            ]
            
            product_elements = []
            for selector in product_selectors:
                elements = await self.page.locator(selector).all()
                if elements:
                    product_elements = elements[:limit]
                    break
            
            # Extract product information
            for elem in product_elements:
                try:
                    # Get product name
                    name = None
                    name_selectors = [
                        'h3', 'h4', 
                        '.org-products-module__product-name',
                        'a[href*="/products/"]',
                    ]
                    for selector in name_selectors:
                        name_elem = elem.locator(selector).first
                        if await name_elem.count() > 0:
                            name = await name_elem.inner_text()
                            if name and len(name.strip()) > 0:
                                name = name.strip()
                                break
                    
                    # Get description
                    description = None
                    desc_selectors = [
                        '.org-products-module__product-description',
                        'p',
                        'div[class*="description"]',
                    ]
                    for selector in desc_selectors:
                        desc_elem = elem.locator(selector).first
                        if await desc_elem.count() > 0:
                            description = await desc_elem.inner_text()
                            if description and len(description.strip()) > 20:
                                description = description.strip()
                                break
                    
                    # Get product URL
                    product_url = None
                    link = elem.locator('a[href*="/products/"]').first
                    if await link.count() > 0:
                        href = await link.get_attribute('href')
                        if href:
                            if '?' in href:
                                href = href.split('?')[0]
                            if not href.startswith('http'):
                                href = f"https://www.linkedin.com{href}"
                            product_url = href
                    
                    # Get logo
                    logo_url = None
                    img = elem.locator('img').first
                    if await img.count() > 0:
                        src = await img.get_attribute('src')
                        if src:
                            logo_url = src
                    
                    # Get category (if available)
                    category = None
                    category_elem = elem.locator('.org-products-module__product-category, span[class*="category"]').first
                    if await category_elem.count() > 0:
                        category = await category_elem.inner_text()
                        if category:
                            category = category.strip()
                    
                    if name:
                        products.append(Product(
                            name=name,
                            description=description,
                            category=category,
                            linkedin_url=product_url,
                            logo_url=logo_url
                        ))
                except Exception as e:
                    logger.debug(f"Error parsing product: {e}")
                    continue
            
        except Exception as e:
            logger.warning(f"Error getting products: {e}")
        
        return products
    
    async def _get_life_updates(self, linkedin_url: str, limit: int = 10) -> list[LifeUpdate]:
        """Extract life/culture updates from Life tab."""
        life_updates = []
        
        try:
            # Navigate to Life page
            life_url = linkedin_url.rstrip('/') + '/life/'
            await self.navigate_and_wait(life_url)
            await self.wait_and_focus(2)
            
            # Wait for content
            await self.page.wait_for_selector("main", timeout=10000)
            await self.scroll_page_to_half()
            await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=3)
            await self.wait_and_focus(1)
            
            # Look for life update cards/posts
            update_selectors = [
                '.org-life-module__photo-card',
                '.org-life-module__video-card',
                '[data-view-name="org-life-module-photo-card"]',
                '[data-view-name="org-life-module-video-card"]',
                'article',
                'div[class*="life"]',
            ]
            
            update_elements = []
            for selector in update_selectors:
                elements = await self.page.locator(selector).all()
                if elements:
                    update_elements = elements[:limit * 2]  # Get more to filter
                    break
            
            # Extract life update information
            for elem in update_elements:
                try:
                    # Determine type
                    update_type = 'photo'  # default
                    elem_html = await elem.inner_html()
                    if 'video' in elem_html.lower():
                        update_type = 'video'
                    elif 'article' in elem_html.lower():
                        update_type = 'article'
                    
                    # Get caption/description
                    caption = None
                    caption_selectors = [
                        '.org-life-module__caption',
                        'p',
                        'div[class*="caption"]',
                        'div[class*="description"]',
                    ]
                    for selector in caption_selectors:
                        caption_elem = elem.locator(selector).first
                        if await caption_elem.count() > 0:
                            caption = await caption_elem.inner_text()
                            if caption and len(caption.strip()) > 5:
                                caption = caption.strip()
                                break
                    
                    # Get URL
                    url = None
                    link = elem.locator('a').first
                    if await link.count() > 0:
                        href = await link.get_attribute('href')
                        if href:
                            if '?' in href:
                                href = href.split('?')[0]
                            if not href.startswith('http'):
                                href = f"https://www.linkedin.com{href}"
                            url = href
                    
                    # Get image/video URL if no link
                    if not url:
                        img = elem.locator('img').first
                        if await img.count() > 0:
                            src = await img.get_attribute('src')
                            if src:
                                url = src
                    
                    # Get posted date (if available)
                    posted_date = None
                    date_selectors = [
                        'time',
                        'span[class*="date"]',
                        'span[class*="time"]',
                    ]
                    for selector in date_selectors:
                        date_elem = elem.locator(selector).first
                        if await date_elem.count() > 0:
                            posted_date = await date_elem.inner_text()
                            if posted_date:
                                posted_date = posted_date.strip()
                                break
                    
                    if caption or url:
                        life_updates.append(LifeUpdate(
                            type=update_type,
                            caption=caption,
                            url=url,
                            posted_date=posted_date
                        ))
                        
                        if len(life_updates) >= limit:
                            break
                except Exception as e:
                    logger.debug(f"Error parsing life update: {e}")
                    continue
            
        except Exception as e:
            logger.warning(f"Error getting life updates: {e}")
        
        return life_updates
    
    async def _get_services(self, linkedin_url: str, limit: int = 20) -> list[Product]:
        """Extract services from Services tab."""
        services = []
        
        try:
            # Navigate to Services page
            services_url = linkedin_url.rstrip('/') + '/services/'
            await self.navigate_and_wait(services_url)
            await self.wait_and_focus(3)
            
            # Wait for content
            try:
                await self.page.wait_for_selector("main", timeout=10000)
            except:
                pass
            
            await self.scroll_page_to_half()
            await self.wait_and_focus(2)
            
            # Look for services section
            service_selectors = [
                'section:has-text("Services provided")',
                'div[data-view-name="org-services-module"]',
                '.org-services-module',
                'section[class*="services"]',
            ]
            
            service_elements = []
            for selector in service_selectors:
                try:
                    elements = await self.page.locator(selector).all()
                    if elements:
                        # Get all service items within
                        service_items = await elements[0].locator('li, div[class*="service"], div[class*="card"]').all()
                        if service_items:
                            service_elements = service_items[:limit]
                            logger.info(f"Found {len(service_elements)} service elements with selector: {selector}")
                            break
                except:
                    continue
            
            # If no specific service elements found, try to extract from overview
            if not service_elements:
                try:
                    # Look for "Services provided" text
                    services_text_elem = await self.page.locator('text="Services provided"').first
                    if await services_text_elem.count() > 0:
                        # Get parent section
                        parent = services_text_elem.locator('xpath=ancestor::section[1] | ancestor::div[contains(@class, "section")][1]')
                        if await parent.count() > 0:
                            # Get all list items or service names
                            items = await parent.locator('li, span, div').all()
                            for item in items[:limit]:
                                text = await item.inner_text()
                                if text and len(text.strip()) > 3 and len(text.strip()) < 100:
                                    # Check if it looks like a service name
                                    if not any(skip in text.lower() for skip in ['services provided', 'availability', 'pricing', 'contact', 'request']):
                                        services.append(Product(
                                            name=text.strip(),
                                            description=None,
                                            category="Service"
                                        ))
                except Exception as e:
                    logger.debug(f"Error extracting services from overview: {e}")
            
            # Extract service information from elements
            for elem in service_elements:
                try:
                    # Get service name
                    name = None
                    name_selectors = ['h3', 'h4', 'span', 'div[class*="name"]', 'a']
                    for selector in name_selectors:
                        name_elem = elem.locator(selector).first
                        if await name_elem.count() > 0:
                            text = await name_elem.inner_text()
                            if text and len(text.strip()) > 2 and len(text.strip()) < 100:
                                name = text.strip()
                                break
                    
                    if not name:
                        # Try getting all text
                        all_text = await elem.inner_text()
                        if all_text:
                            lines = [l.strip() for l in all_text.split('\n') if l.strip()]
                            if lines:
                                name = lines[0][:100]  # First line, max 100 chars
                    
                    if name and len(name) > 2:
                        # Get description if available
                        description = None
                        desc_elem = elem.locator('p, div[class*="description"], div[class*="detail"]').first
                        if await desc_elem.count() > 0:
                            desc_text = await desc_elem.inner_text()
                            if desc_text and len(desc_text.strip()) > 10:
                                description = desc_text.strip()[:500]
                        
                        # Get URL if available
                        service_url = None
                        link_elem = elem.locator('a').first
                        if await link_elem.count() > 0:
                            href = await link_elem.get_attribute('href')
                            if href:
                                if not href.startswith('http'):
                                    service_url = f"https://www.linkedin.com{href}"
                                else:
                                    service_url = href
                        
                        services.append(Product(
                            name=name,
                            description=description,
                            category="Service",
                            linkedin_url=service_url
                        ))
                        
                        if len(services) >= limit:
                            break
                            
                except Exception as e:
                    logger.debug(f"Error parsing service element: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(services)} services")
            
        except Exception as e:
            logger.warning(f"Error getting services: {e}")
        
        return services