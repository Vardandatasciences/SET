"""Person/Profile scraper for LinkedIn."""

import asyncio
import logging
import re
from typing import Optional
from urllib.parse import urljoin
from playwright.async_api import Page

from .base import BaseScraper
from ..models import Person, Experience, Education, Accomplishment, Contact
from ..callbacks import ProgressCallback, SilentCallback
from ..core.exceptions import ScrapingError

logger = logging.getLogger(__name__)


class PersonScraper(BaseScraper):
    """Async scraper for LinkedIn person profiles."""

    def __init__(self, page: Page, callback: Optional[ProgressCallback] = None):
        """
        Initialize person scraper.

        Args:
            page: Playwright page object
            callback: Progress callback
        """
        super().__init__(page, callback)

    async def scrape(self, linkedin_url: str) -> Person:
        """
        Scrape a LinkedIn person profile.

        Args:
            linkedin_url: LinkedIn profile URL

        Returns:
            Person object with all scraped data

        Raises:
            AuthenticationError: If not logged in
            ScrapingError: If scraping fails
        """
        await self.callback.on_start("person", linkedin_url)

        try:
            # Navigate to profile first (this loads the page with our session)
            await self.navigate_and_wait(linkedin_url)
            await self.callback.on_progress("Navigated to profile", 10)

            # Now check if logged in
            await self.ensure_logged_in()

            # Wait for main content
            await self.page.wait_for_selector("main", timeout=10000)
            await self.wait_and_focus(2)  # Wait longer for dynamic content
            
            # Wait for profile content to load
            try:
                # Wait for any profile content indicators
                await self.page.wait_for_selector("main > div", timeout=5000)
            except:
                pass

            # Get name and location
            name, location = await self._get_name_and_location()
            await self.callback.on_progress(f"Got name: {name}", 20)

            # Check open to work
            open_to_work = await self._check_open_to_work()

            # Scroll to load content
            await self.scroll_page_to_half()
            await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=3)

            # Get experiences
            experiences = await self._get_experiences(linkedin_url)
            await self.callback.on_progress(f"Got {len(experiences)} experiences", 40)

            educations = await self._get_educations(linkedin_url)
            await self.callback.on_progress(f"Got {len(educations)} educations", 50)

            accomplishments = await self._get_accomplishments(linkedin_url)
            await self.callback.on_progress(
                f"Got {len(accomplishments)} accomplishments", 60
            )

            # Get certifications separately with improved extraction
            certifications = await self._get_certifications(linkedin_url)
            await self.callback.on_progress(f"Got {len(certifications)} certifications", 70)
            
            # Merge certifications into accomplishments
            accomplishments.extend(certifications)

            skills = await self._get_skills(linkedin_url)
            await self.callback.on_progress(f"Got {len(skills)} skills", 80)

            contacts = await self._get_contacts(linkedin_url)
            await self.callback.on_progress(f"Got {len(contacts)} contacts", 90)

            person = Person(
                linkedin_url=linkedin_url,
                name=name,
                location=location,
                open_to_work=open_to_work,
                experiences=experiences,
                educations=educations,
                accomplishments=accomplishments,
                contacts=contacts,
                skills=skills,
            )

            await self.callback.on_progress("Scraping complete", 100)
            await self.callback.on_complete("person", person)

            return person

        except Exception as e:
            await self.callback.on_error(e)
            raise ScrapingError(f"Failed to scrape person profile: {e}")

    async def _get_name_and_location(self) -> tuple[str, Optional[str]]:
        """Extract name and location from profile."""
        try:
            # Wait a bit more for dynamic content
            await asyncio.sleep(1)
            
            # Try multiple selectors for name (LinkedIn changes their structure frequently)
            name = None
            
            # First, try to extract from page title as fallback
            try:
                page_title = await self.page.title()
                if "| LinkedIn" in page_title:
                    name_from_title = page_title.split("|")[0].strip()
                    if name_from_title and len(name_from_title) < 100:
                        name = name_from_title
            except:
                pass
            
            name_selectors = [
                "h1.text-heading-xlarge",
                "h1.inline.t-24.v-align-middle.break-words",
                "h1[data-anonymize='person-name']",
                "main h1",
                "h1",
                "[data-view-name='profile-card'] h1",
                "span.text-heading-xlarge",
                "div.text-heading-xlarge",
            ]
            
            for selector in name_selectors:
                try:
                    name_text = await self.safe_extract_text(selector, default="", timeout=1000)
                    if name_text and name_text.strip() and name_text != "Unknown" and len(name_text.strip()) < 100:
                        name = name_text.strip()
                        break
                except:
                    continue
            
            # If still no name, try to find it in the main content area using more flexible approach
            if not name or name == "Unknown":
                try:
                    # Look for the profile header section - try multiple strategies
                    main_section = self.page.locator("main").first
                    if await main_section.count() > 0:
                        # Strategy 1: Look for any heading or large text elements
                        # Try to find text that looks like a name (2-4 words, reasonable length)
                        all_text_elements = await main_section.locator("h1, h2, span, div, a").all()
                        for elem in all_text_elements[:20]:  # Check first 20 elements
                            try:
                                text = await elem.text_content()
                                if text:
                                    text = text.strip()
                                    # Check if it looks like a name
                                    word_count = len(text.split())
                                    if 2 <= word_count <= 4 and 5 < len(text) < 80:
                                        # Filter out common non-name text
                                        text_lower = text.lower()
                                        if not any(word in text_lower for word in [
                                            'connection', 'follower', 'view', 'message', 'more', 
                                            'home', 'feed', 'messaging', 'notifications', 'jobs',
                                            'linkedin', 'sign in', 'join now'
                                        ]):
                                            # Check if it contains letters (likely a name)
                                            if any(c.isalpha() for c in text):
                                                name = text
                                                break
                            except:
                                continue
                except Exception as e:
                    logger.debug(f"Error in fallback name extraction: {e}")
                    pass
            
            # Try multiple selectors for location
            location = None
            location_selectors = [
                ".text-body-small.inline.t-black--light.break-words",
                ".pv-text-details__left-panel .text-body-small",
                "[data-view-name='profile-card'] .text-body-small",
                "span.text-body-small",
                ".inline-show-more-text",
            ]
            
            for selector in location_selectors:
                try:
                    location_text = await self.safe_extract_text(selector, default="", timeout=1000)
                    if location_text and location_text.strip():
                        # Filter out non-location text (like "X connections")
                        if any(word in location_text.lower() for word in ['connection', 'follower', 'contact']):
                            continue
                        location = location_text.strip()
                        break
                except:
                    continue
            
            # If still no location, try to find it near the name
            if not location:
                try:
                    main_section = self.page.locator("main").first
                    if await main_section.count() > 0:
                        location_elements = await main_section.locator(".text-body-small, .t-black--light").all()
                        for elem in location_elements[:5]:  # Check first 5
                            text = await elem.text_content()
                            if text and text.strip() and len(text.strip()) < 100:
                                # Skip if it looks like connection count or other metadata
                                if any(word in text.lower() for word in ['connection', 'follower', 'contact', 'mutual']):
                                    continue
                                # Likely a location if it contains common location indicators
                                if any(char in text for char in [',', '•']) or len(text.split()) <= 5:
                                    location = text.strip()
                                    break
                except:
                    pass
            
            return name if name else "Unknown", location if location else None
        except Exception as e:
            logger.warning(f"Error getting name/location: {e}")
            return "Unknown", None

    async def _check_open_to_work(self) -> bool:
        """Check if profile has open to work badge."""
        try:
            # Look for open to work indicator
            img_title = await self.get_attribute_safe(
                ".pv-top-card-profile-picture img", "title", default=""
            )
            return "#OPEN_TO_WORK" in img_title.upper()
        except:
            return False

    async def _get_about(self) -> Optional[str]:
        """Extract about section."""
        try:
            # Find the profile card that contains "About"
            profile_cards = await self.page.locator(
                '[data-view-name="profile-card"]'
            ).all()

            for card in profile_cards:
                card_text = await card.inner_text()
                # Check if this card contains "About" heading
                if card_text.strip().startswith("About"):
                    # Get the span with aria-hidden to avoid duplication
                    about_spans = await card.locator('span[aria-hidden="true"]').all()
                    # Skip the first span (it's the "About" heading), get the content
                    if len(about_spans) > 1:
                        about_text = await about_spans[1].text_content()
                        return about_text.strip() if about_text else None

            return None
        except Exception as e:
            logger.debug(f"Error getting about section: {e}")
            return None

    async def _get_experiences(self, base_url: str) -> list[Experience]:
        """Extract experiences from the main profile page Experience section."""
        experiences = []

        try:
            # Wait a bit for dynamic content
            await asyncio.sleep(1)
            
            # Try to find Experience section on main page with multiple strategies
            experience_heading = None
            heading_selectors = [
                'h2:has-text("Experience")',
                'h2[id*="experience"]',
                '[data-view-name="profile-card"]:has-text("Experience")',
                'text="Experience"',
            ]
            
            for selector in heading_selectors:
                try:
                    heading = self.page.locator(selector).first
                    if await heading.count() > 0:
                        experience_heading = heading
                        break
                except:
                    continue
            
            if experience_heading and await experience_heading.count() > 0:
                # Try to find the section container
                experience_section = None
                section_strategies = [
                    ("parent then following sibling", experience_heading.locator('xpath=parent::*/following-sibling::*[1]')),
                    ("ancestor 2 levels up", experience_heading.locator('xpath=ancestor::*[2]')),
                    ("following sibling", experience_heading.locator('xpath=following-sibling::*[1]')),
                    ("ancestor section", experience_heading.locator('xpath=ancestor::section[1]')),
                    ("ancestor with ul/ol", experience_heading.locator('xpath=ancestor::*[.//ul or .//ol][1]')),
                    ("ancestor 4 levels up", experience_heading.locator('xpath=ancestor::*[4]')),
                ]
                
                for strategy_name, section_locator in section_strategies:
                    if await section_locator.count() > 0:
                        section = section_locator.first
                        section_text = await section.text_content()
                        
                        # Prefer sections with reasonable text length (not too large, indicating whole page)
                        if 1000 < len(section_text) < 10000:
                            experience_section = section
                            logger.debug(f"Using experience section strategy: {strategy_name}")
                            break
                        elif experience_section is None:
                            experience_section = section
                
                if experience_section and await experience_section.count() > 0:
                    # Try multiple item selectors - LinkedIn now uses div structure instead of ul/li
                    item_selectors = ['> div', 'ul > li', 'ol > li', 'li', '[data-view-name="profile-component-entity"]']
                    items = []
                    for item_sel in item_selectors:
                        found_items = await experience_section.locator(item_sel).all()
                        if found_items and 1 <= len(found_items) <= 20:
                            items = found_items
                            logger.debug(f"Found {len(items)} experience items with selector: {item_sel}")
                            break
                    
                    for item in items:
                        try:
                            result = await self._parse_main_page_experience(item)
                            if result:
                                # Handle both single Experience and list of Experiences
                                if isinstance(result, list):
                                    for exp in result:
                                        if exp and exp.position_title:
                                            experiences.append(exp)
                                elif result.position_title:
                                    experiences.append(result)
                        except Exception as e:
                            logger.debug(f"Error parsing experience from main page: {e}")
                            continue
            
            # If no experiences found on main page, try the details page
            if not experiences:
                logger.debug("No experiences found on main page, trying details page...")
                exp_url = urljoin(base_url, "details/experience")
                await self.navigate_and_wait(exp_url)
                await self.page.wait_for_selector("main", timeout=10000)
                await self.wait_and_focus(2)  # Wait longer for content
                await self.scroll_page_to_half()
                await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=5)

                items = []
                # Try multiple selectors for experience items
                item_selectors = [
                    'list > listitem',
                    'ul > li',
                    'ol > li',
                    '.pvs-list__paged-list-item',
                    '[data-view-name="profile-component-entity"]',
                    'li[data-view-name*="experience"]',
                    'li',
                    '[role="listitem"]',
                ]
                
                main_element = self.page.locator('main')
                if await main_element.count() > 0:
                    # Wait a bit more for content to load
                    await asyncio.sleep(1)
                    
                    # Try to find the actual experience list container
                    # Look for sections that might contain experiences
                    experience_containers = [
                        main_element.locator('[id*="experience"]'),
                        main_element.locator('[data-section*="experience"]'),
                        main_element.locator('section:has-text("Experience")'),
                        main_element.locator('ul, ol'),
                    ]
                    
                    for container_sel in experience_containers:
                        if await container_sel.count() > 0:
                            container = container_sel.first
                            # Get items from this container
                            found_items = await container.locator('li, [role="listitem"]').all()
                            if found_items:
                                # Filter and validate items
                                for item in found_items:
                                    try:
                                        text = await item.text_content()
                                        if text:
                                            text_lower = text.lower()
                                            # Skip footer/help items
                                            if any(skip in text_lower for skip in [
                                                'help center', 'settings', 'privacy', 'recommendation',
                                                'transparency', 'cookie', 'terms', 'about', 'accessibility',
                                                'questions?', 'manage your account'
                                            ]):
                                                continue
                                            # Must have reasonable length
                                            if len(text.strip()) > 20:
                                                items.append(item)
                                    except:
                                        continue
                                
                                if items:
                                    logger.debug(f"Found {len(items)} experience items from container")
                                    break
                    
                    # If still no items, try selectors
                    if not items:
                        for item_sel in item_selectors:
                            found_items = await main_element.locator(item_sel).all()
                            if found_items:
                                # Filter out footer/help items
                                filtered_items = []
                                for item in found_items:
                                    try:
                                        text = await item.text_content()
                                        if text:
                                            text_lower = text.lower()
                                            # Skip footer/help items
                                            if any(skip in text_lower for skip in [
                                                'help center', 'settings', 'privacy', 'recommendation',
                                                'transparency', 'cookie', 'terms', 'about', 'accessibility',
                                                'questions?', 'manage your account'
                                            ]):
                                                continue
                                            # Must have reasonable length
                                            if len(text.strip()) > 20:
                                                filtered_items.append(item)
                                    except:
                                        continue
                                
                                if filtered_items:
                                    items = filtered_items
                                    logger.debug(f"Found {len(items)} experience items using selector: {item_sel} (after filtering)")
                                    break
                    
                    # Fallback: try to get all list items and filter
                    if not items:
                        all_lis = await main_element.locator('li').all()
                        if all_lis:
                            logger.debug(f"Found {len(all_lis)} total li elements in main")
                            # Filter to likely experience items (have links and reasonable text)
                            for li in all_lis:
                                try:
                                    text = await li.text_content()
                                    if text:
                                        text_lower = text.lower()
                                        # Skip footer/help items
                                        if any(skip in text_lower for skip in [
                                            'help center', 'settings', 'privacy', 'recommendation',
                                            'transparency', 'cookie', 'terms', 'about', 'accessibility'
                                        ]):
                                            continue
                                        links = await li.locator('a').count()
                                        # Experience items usually have links to companies
                                        if links > 0 and len(text.strip()) > 15:
                                            items.append(li)
                                            if len(items) >= 10:  # Limit to first 10 valid items
                                                break
                                except:
                                    continue

                for i, item in enumerate(items):
                    try:
                        # Debug: log item text
                        item_text = await item.text_content()
                        logger.debug(f"Parsing experience item {i+1}: {item_text[:100] if item_text else 'No text'}")
                        
                        result = await self._parse_experience_item(item)
                        if result:
                            if isinstance(result, list):
                                for exp in result:
                                    if exp and exp.position_title:
                                        logger.debug(f"Added experience: {exp.position_title} at {exp.institution_name}")
                                        experiences.append(exp)
                            else:
                                if result.position_title:
                                    logger.debug(f"Added experience: {result.position_title} at {result.institution_name}")
                                experiences.append(result)
                        else:
                            logger.debug(f"Failed to parse experience item {i+1}")
                    except Exception as e:
                        logger.debug(f"Error parsing experience item {i+1}: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
                        continue

        except Exception as e:
            logger.warning(
                f"Error getting experiences: {e}. The experience section may not be available or the page structure has changed."
            )

        logger.info(f"Extracted {len(experiences)} experiences")
        return experiences
    
    async def _parse_main_page_experience(self, item):
        """Parse experience from main profile page list item with improved extraction.
        Returns either a single Experience or a list of Experiences (for nested positions)."""
        try:
            # Check if this is a nested experience (multiple roles at same company)
            # Nested experiences have a different structure with nested lists
            nested_list = await item.locator('ul, ol').count()
            if nested_list > 0:
                # This item contains nested positions
                logger.debug("Detected nested experience structure")
                result = await self._parse_nested_main_page_experience(item)
                if result:
                    return result
            
            links = await item.locator('a').all()
            if len(links) < 1:
                return None
            
            # Get company URL from first link
            company_url = await links[0].get_attribute('href')
            
            # Use the detail link if available, otherwise use first link
            detail_link = links[1] if len(links) > 1 else links[0]
            
            # Get full text content first
            full_text = await detail_link.text_content()
            if not full_text or len(full_text.strip()) < 10:
                return None
            
            full_text = full_text.strip()
            logger.debug(f"Parsing experience text: {full_text[:200]}")
            
            # LinkedIn concatenates text without spaces in format:
            # "PositionTitleCompanyName · Employment TypeDate Range · DurationLocation"
            # Example: "Co-Founder, Board ChairManas AI · Part-timeJan 2025 - Present · 1 yr 2 mos"
            
            import re
            
            position_title = None
            company_name = None
            from_date = None
            to_date = None
            duration = None
            location = None
            
            # Strategy: Find the date range first, then parse what's before it
            # Date pattern: "Mon YYYY - Present · X yrs Y mos" or just "Mon YYYY - Mon YYYY"
            date_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\s*[-–]\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|Present)'
            date_match = re.search(date_pattern, full_text, re.IGNORECASE)
            
            if date_match:
                from_date = date_match.group(1).strip()
                to_date = date_match.group(2).strip()
                
                # Extract duration if present (after the dates with ·)
                duration_text = full_text[date_match.end():].strip()
                if duration_text.startswith('·'):
                    duration_text = duration_text[1:].strip()
                    # Duration is until we hit a capital letter (indicating location) or end of string
                    duration_match = re.match(r'([^A-Z]+)', duration_text)
                    if duration_match:
                        duration = duration_match.group(1).strip()
                        # Location is what's after duration
                        location = duration_text[duration_match.end():].strip()
                        if location and len(location) < 100:
                            pass  # keep location
                        else:
                            location = None
                
                # Text before dates contains position and company
                before_dates = full_text[:date_match.start()].strip()
            else:
                # No date pattern found
                before_dates = full_text
            
            # Parse position and company from text before dates
            # Strategy: Find "· Employment Type" first, then split position and company
            # Pattern: look for employment type marker
            employment_pattern = r'·\s*(Part-time|Full-time|Contract|Freelance|Temporary|Self-employed|Seasonal|Internship)'
            employment_match = re.search(employment_pattern, before_dates, re.IGNORECASE)
            
            if employment_match:
                # Text before employment type contains position and company
                before_employment = before_dates[:employment_match.start()].strip()
                logger.debug(f"Before employment type: '{before_employment}'")
                
                # LinkedIn concatenates position and company without space
                # E.g., "Co-Founder, Board ChairManas AI" where "Chair" and "Manas" are joined
                # Split on camelCase boundaries (lowercase followed by uppercase)
                split_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', before_employment)
                logger.debug(f"After camelCase split: '{split_text}'")
                
                # Now split by spaces
                words = split_text.split()
                if len(words) >= 2:
                    # Find where company name starts
                    # Position titles with commas: "Co-Founder, Board Chair" + "Manas AI"
                    # Position titles without commas: "Partner" + "Greylock"
                    
                    # Strategy: Company is the last 1-3 capitalized words
                    # But if there are commas, look for pattern after last content word with comma
                    
                    # First, check if we have commas in the text
                    has_comma = any(',' in w for w in words)
                    
                    if has_comma:
                        # Position title likely has multiple parts separated by commas
                        # Company name comes after all comma-separated position parts
                        # Look for a break in the comma pattern
                        # E.g., "Co-Founder, Board Chair Manas AI" 
                        # -> "Co-Founder," "Board" "Chair" "Manas" "AI"
                        # The pattern changes from comma-separated to space-separated
                        
                        # Find the last word with a comma
                        last_comma_idx = -1
                        for i in range(len(words) - 1, -1, -1):
                            if ',' in words[i]:
                                last_comma_idx = i
                                break
                        
                        # If we found a comma and there are words after it
                        if last_comma_idx >= 0 and last_comma_idx < len(words) - 1:
                            # Check how many words after the comma
                            remaining = len(words) - last_comma_idx - 1
                            if remaining <= 3:
                                # These are likely company name words
                                # Take last 1-2 words as company
                                if remaining == 1:
                                    company_start_idx = len(words) - 1
                                else:
                                    # Check if last 2 words are both capitalized
                                    if remaining >= 2 and words[-1][0].isupper() and words[-2][0].isupper():
                                        company_start_idx = len(words) - 2
                                    else:
                                        company_start_idx = len(words) - 1
                            else:
                                # Many words after comma, take last 2
                                company_start_idx = len(words) - 2
                        else:
                            # Comma is in last word, everything before is position
                            company_start_idx = len(words)
                    else:
                        # No commas - use simple heuristic
                        # Check for common position title keywords
                        position_keywords = ['Member', 'Partner', 'Chair', 'Director', 'Manager', 'Officer', 'Lead', 'Head']
                        
                        # If second-to-last word is a position keyword, keep it with position
                        if len(words) >= 3 and words[-2] in position_keywords:
                            # E.g., "Board Member Microsoft" -> "Board Member" + "Microsoft"
                            company_start_idx = len(words) - 1
                        elif len(words) == 2:
                            company_start_idx = 1
                        elif len(words) == 3:
                            if words[-1][0].isupper() and words[-2][0].isupper():
                                company_start_idx = len(words) - 2
                            else:
                                company_start_idx = len(words) - 1
                        else:
                            if len(words) >= 2 and words[-1][0].isupper() and words[-2][0].isupper():
                                company_start_idx = len(words) - 2
                            else:
                                company_start_idx = len(words) - 1
                    
                    company_name = ' '.join(words[company_start_idx:])
                    position_title = ' '.join(words[:company_start_idx])
                    
                    # Clean up trailing commas from position
                    if position_title:
                        position_title = position_title.rstrip(' ,')
                    
                    logger.debug(f"Split result - Position: '{position_title}', Company: '{company_name}'")
                else:
                    position_title = before_employment
                    company_name = None
            else:
                # Try without employment type - just look for last capitalized word(s) as company
                # Find the last sequence of capital letters that could be a company name
                # This is tricky because position can also have capitals
                # Heuristic: split by capital letter that comes after lowercase
                words = before_dates.split()
                # Company name is usually 1-4 words at the end
                if len(words) >= 2:
                    # Try last 2 words as company, rest as position
                    company_name = ' '.join(words[-2:])
                    position_title = ' '.join(words[:-2])
                    
                    # If position is too short, try just last word as company
                    if len(position_title) < 3 and len(words) >= 1:
                        company_name = words[-1]
                        position_title = ' '.join(words[:-1])
                else:
                    position_title = before_dates
            
            # Clean up
            if position_title:
                position_title = position_title.strip(' ,·\t\n')
            if company_name:
                company_name = company_name.strip(' ,·\t\n')
            
            return Experience(
                position_title=position_title,
                institution_name=company_name,
                linkedin_url=company_url,
                from_date=from_date,
                to_date=to_date,
                duration=duration,
                location=location,
                description=None,
            )
            
        except Exception as e:
            logger.debug(f"Error parsing main page experience: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    async def _parse_nested_main_page_experience(self, item):
        """Parse nested experience positions from main page (multiple roles at the same company).
        Returns a list of Experience objects."""
        experiences = []
        
        try:
            # Get all links - first link should be company
            all_links = await item.locator('a').all()
            if len(all_links) == 0:
                return None
            
            # Try to get company name and URL
            company_url = None
            company_name = ""
            
            # Strategy 1: Get from first link
            first_link = all_links[0]
            company_url = await first_link.get_attribute('href')
            
            # Try to extract company name from various locations
            # Check if first link has visible text
            company_text = await first_link.text_content()
            if company_text and len(company_text.strip()) > 0:
                # Parse the text - might have company name and duration like "Vardaan Data Sciences Pvt. Ltd.2 yrs"
                import re
                # Remove trailing years/duration pattern
                clean_text = re.sub(r'\d+\s*(yr|year|mo|month)s?.*$', '', company_text.strip())
                if len(clean_text) > 3:
                    company_name = clean_text.strip()
            
            # Strategy 2: Look for company name in parent spans
            if not company_name:
                parent_spans = await item.locator('span[aria-hidden="true"]').all()
                for span in parent_spans[:3]:  # Check first 3 spans
                    text = await span.text_content()
                    if text and len(text.strip()) > 5:
                        # Check if it looks like a company name (not a position title with common keywords)
                        text_lower = text.lower()
                        if not any(keyword in text_lower for keyword in ['developer', 'intern', 'engineer', 'manager', 'full-time', 'part-time']):
                            company_name = text.strip()
                            break
            
            logger.debug(f"Parsing nested positions at {company_name}")
            
            # Find the nested list of positions
            nested_list = item.locator('ul, ol').first
            if await nested_list.count() == 0:
                logger.debug("No nested list found")
                return None
            
            # Get all position items from the nested list
            position_items = await nested_list.locator('li').all()
            logger.debug(f"Found {len(position_items)} position items in nested list")
            
            for idx, pos_item in enumerate(position_items):
                try:
                    # Get text content from the position item - same approach as education
                    pos_text = await pos_item.text_content()
                    if not pos_text or len(pos_text.strip()) < 10:
                        logger.debug(f"Position {idx+1}: text too short or empty")
                        continue
                    
                    pos_text = pos_text.strip()
                    logger.debug(f"Parsing nested position {idx+1}: {pos_text[:150]}")
                    
                    # Parse the concatenated text - similar to education parsing
                    # Format: "DeveloperFull-timeJul 2024 - Present · 1 yr 8 mos Databases and Programming"
                    # Or: "InternInternshipMar 2024 - Jun 2024 · 4 mos Generative AI, Front-End Development and +5 skills"
                    
                    import re
                    
                    position_title = None
                    work_times = ""
                    location = None
                    from_date = None
                    to_date = None
                    duration = None
                    
                    # Strategy: Find date pattern first
                    # Pattern: "Mon YYYY - Mon YYYY · duration" or "Mon YYYY - Present · duration"
                    date_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\s*[-–]\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|Present)\s*[·•]\s*([^A-Z]+)'
                    date_match = re.search(date_pattern, pos_text, re.IGNORECASE)
                    
                    if date_match:
                        from_date = date_match.group(1).strip()
                        to_date = date_match.group(2).strip()
                        duration = date_match.group(3).strip()
                        work_times = f"{from_date} - {to_date} · {duration}"
                        
                        # Text before dates is position title + employment type
                        before_dates = pos_text[:date_match.start()].strip()
                        
                        # Remove employment type keywords
                        employment_types = ['Full-time', 'Part-time', 'Contract', 'Freelance', 'Internship', 'Temporary', 'Self-employed']
                        for emp_type in employment_types:
                            before_dates = before_dates.replace(emp_type, '').strip()
                        
                        position_title = before_dates
                        
                        # Text after the duration might be location or skills
                        after_dates = pos_text[date_match.end():].strip()
                        # If it's short and doesn't look like skills list, it might be location
                        if after_dates and len(after_dates) < 100 and ',' in after_dates and 'skills' not in after_dates.lower():
                            location = after_dates
                        
                        logger.debug(f"Position {idx+1}: title='{position_title}', from='{from_date}', to='{to_date}', duration='{duration}'")
                    else:
                        # No date pattern found - try simpler parsing
                        logger.debug(f"Position {idx+1}: No date pattern found in text")
                        # Just use the first part as position title
                        parts = pos_text.split('\n')
                        if parts:
                            position_title = parts[0].strip()
                            # Remove employment type if present
                            for emp_type in ['Full-time', 'Part-time', 'Contract', 'Freelance', 'Internship']:
                                position_title = position_title.replace(emp_type, '').strip()
                    
                    if not position_title or len(position_title) < 3:
                        logger.debug(f"Position {idx+1}: No valid position title found")
                        continue
                    
                    # If from_date and to_date weren't set by regex, try parsing work_times
                    if not from_date and work_times:
                        from_date, to_date, duration = self._parse_work_times(work_times)
                    
                    exp = Experience(
                        position_title=position_title.strip(),
                        institution_name=company_name.strip() if company_name else "Unknown",
                        linkedin_url=company_url,
                        from_date=from_date,
                        to_date=to_date,
                        duration=duration,
                        location=location.strip() if location else None,
                        description=None,
                    )
                    experiences.append(exp)
                    logger.debug(f"Added nested position: {position_title} at {company_name} ({from_date} - {to_date})")
                    
                except Exception as e:
                    logger.debug(f"Error parsing nested position item {idx+1}: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                    continue
            
            # Apply filtering: return only current role if present
            if experiences:
                logger.debug(f"Total experiences before filtering: {len(experiences)}")
                for exp in experiences:
                    logger.debug(f"  - {exp.position_title}: from={exp.from_date}, to={exp.to_date}")
                
                current_roles = [
                    exp for exp in experiences 
                    if not exp.to_date or exp.to_date.lower() in ["present", "current", "now"]
                ]
                if current_roles:
                    logger.debug(f"Found {len(current_roles)} current role(s) out of {len(experiences)} total roles at {company_name}")
                    logger.debug(f"Returning only current role(s): {[r.position_title for r in current_roles]}")
                    return current_roles
                
                logger.debug(f"No current roles found, returning all {len(experiences)} past roles")
            else:
                logger.debug("No experiences parsed from nested structure")
            
        except Exception as e:
            logger.error(f"Error parsing nested main page experience: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return experiences if experiences else None
    
    async def _extract_unique_texts_from_element(self, element) -> list[str]:
        """Extract unique text content from nested elements, avoiding duplicates from parent/child overlap."""
        text_elements = await element.locator('span[aria-hidden="true"], div > span').all()
        
        if not text_elements:
            text_elements = await element.locator('span, div').all()
        
        seen_texts = set()
        unique_texts = []
        
        for el in text_elements:
            text = await el.text_content()
            if text and text.strip():
                text = text.strip()
                if text not in seen_texts and len(text) < 200 and not any(text in t or t in text for t in seen_texts if len(t) > 3):
                    seen_texts.add(text)
                    unique_texts.append(text)
        
        return unique_texts

    async def _parse_experience_item(self, item):
        """Parse experience item. Returns Experience or list for nested positions."""
        try:
            # Get all text from the item first
            item_text = await item.text_content()
            if not item_text or len(item_text.strip()) < 10:
                logger.debug("Item text too short or empty")
                return None
            
            logger.debug(f"Parsing experience with text: {item_text[:200]}")
            
            # Try to extract structured data
            links = await item.locator('a').all()
            company_url = None
            if links:
                # First link is usually company
                company_url = await links[0].get_attribute('href')
            
            # Try multiple strategies to extract text
            texts = []
            
            # Strategy 1: Get all spans with aria-hidden
            aria_spans = await item.locator('span[aria-hidden="true"]').all()
            for span in aria_spans:
                text = await span.text_content()
                if text and text.strip():
                    text = text.strip()
                    # Filter out description text - longer paragraphs or sentences
                    # Descriptions typically start with "As a", "As an", or contain full sentences
                    if (len(text) < 200 and 
                        not text.startswith("As a ") and 
                        not text.startswith("As an ") and
                        not text.count('.') > 1):  # Multiple sentences indicate description
                        texts.append(text)
            
            # Strategy 2: If no aria-hidden spans, get all text nodes
            if not texts:
                all_spans = await item.locator('span').all()
                for span in all_spans[:10]:  # Limit to first 10
                    text = await span.text_content()
                    if text and text.strip():
                        text = text.strip()
                        if (len(text) < 200 and 
                            not text.startswith("As a ") and 
                            not text.startswith("As an ") and
                            not text.count('.') > 1):
                            texts.append(text)
            
            # Remove duplicates while preserving order
            unique_texts = []
            seen = set()
            for text in texts:
                text_lower = text.lower()
                # Skip common non-content text
                if any(skip in text_lower for skip in ['linkedin', 'view profile', 'show more', 'hide']):
                    continue
                # Skip long descriptions (very long text with description markers)
                is_description = (
                    text.startswith("As a ") or 
                    text.startswith("As an ") or
                    (len(text) > 150 and text.count(',') > 3)  # Very long with many commas
                )
                if is_description:
                    continue
                if text not in seen and len(text) > 2:
                    seen.add(text)
                    unique_texts.append(text)
            
            # Try to identify position, company, dates from the texts
            # Parse from lines of text (more reliable)
            lines = [line.strip() for line in item_text.split('\n') if line.strip() and len(line.strip()) > 2]
            
            # Filter out description lines (longer sentences with descriptions)
            filtered_lines = []
            for line in lines:
                # Skip lines that look like descriptions
                if (line.startswith("As a ") or 
                    line.startswith("As an ") or
                    line.count('.') > 1 or  # Multiple sentences
                    (len(line) > 100 and line.count(',') > 2)):  # Long with multiple commas
                    continue
                filtered_lines.append(line)
            lines = filtered_lines
            
            position_title = None
            company_name = None
            work_times = ""
            location = ""
            
            # Helper function to clean concatenated text (remove dates and skills)
            def clean_experience_text(text):
                """Remove dates, duration, and skills from concatenated text."""
                if not text:
                    return text
                
                # Pattern to match month names followed by year (e.g., "Nov 2024", "January 2023")
                # Also match "Skills:" and everything after
                date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}'
                
                # Find first occurrence of date pattern
                match = re.search(date_pattern, text)
                if match:
                    # Take text before the date
                    text = text[:match.start()].strip()
                
                # Also remove if "Skills:" appears
                if "Skills:" in text:
                    text = text.split("Skills:")[0].strip()
                
                # Remove trailing separators
                text = text.rstrip('·-–—').strip()
                return text
            
            # Strategy 1: Try to extract from unique_texts (structured data)
            if len(unique_texts) >= 2:
                # Usually: position, company, dates
                # But sometimes position + dates are concatenated, need to split
                raw_title = unique_texts[0] if len(unique_texts[0]) > 3 else None
                raw_company = unique_texts[1] if len(unique_texts[1]) > 3 else None
                
                # Clean the text
                position_title = clean_experience_text(raw_title) if raw_title else None
                company_name = clean_experience_text(raw_company) if raw_company else None
                
                # If cleaning made it too short, use original
                if position_title and len(position_title) < 3:
                    position_title = raw_title
                if company_name and len(company_name) < 3:
                    company_name = raw_company
                
                work_times = unique_texts[2] if len(unique_texts) > 2 else ""
                location = unique_texts[3] if len(unique_texts) > 3 else ""
            elif len(unique_texts) == 1:
                # Might be just position or company, try to clean it
                raw_text = unique_texts[0] if len(unique_texts[0]) > 3 else None
                position_title = clean_experience_text(raw_text) if raw_text else None
                if position_title and len(position_title) < 3:
                    position_title = raw_text
            
            # Strategy 2: Parse from lines (fallback)
            if not position_title or not company_name:
                if lines:
                    # Filter out common non-content lines and descriptions
                    valid_lines = [l for l in lines if not any(skip in l.lower() for skip in [
                        'linkedin', 'view', 'more', 'show', 'hide', 'see', 'as a ', 'as an '
                    ]) and len(l) < 150]  # Limit line length to avoid descriptions
                    
                    if valid_lines:
                        # First valid line is usually position or company
                        if not position_title:
                            raw_pos = valid_lines[0]
                            position_title = clean_experience_text(raw_pos)
                            # If cleaning made it too short, use original
                            if len(position_title) < 3:
                                position_title = raw_pos
                        # Second line is usually the other one
                        if not company_name and len(valid_lines) > 1:
                            raw_comp = valid_lines[1]
                            company_name = clean_experience_text(raw_comp)
                            # If cleaning made it too short, use original
                            if len(company_name) < 3:
                                company_name = raw_comp
                        # Look for date patterns in remaining lines
                        if not work_times:
                            for line in valid_lines[2:]:
                                if any(char in line for char in ['-', '·', 'to']) or \
                                   any(word in line.lower() for word in ['year', 'month', 'yr', 'mo', 'present', 'jan', 'feb', 'mar']):
                                    work_times = line
                                    break
            
            # Final validation - we need at least position or company
            # Also filter out obviously non-experience items
            if position_title or company_name:
                # Filter out help/footer items
                combined_text = f"{position_title} {company_name}".lower()
                if any(skip in combined_text for skip in [
                    'help center', 'settings', 'privacy', 'recommendation',
                    'transparency', 'cookie', 'terms', 'about', 'accessibility',
                    'questions?', 'manage your account'
                ]):
                    logger.debug("Filtered out non-experience item")
                    return None
                
                from_date, to_date, duration = self._parse_work_times(work_times)
                
                # If we only have one, use it for both (better than nothing)
                if not position_title and company_name:
                    position_title = company_name
                elif not company_name and position_title:
                    company_name = position_title
                
                return Experience(
                    position_title=position_title,
                    institution_name=company_name,
                    linkedin_url=company_url,
                    from_date=from_date,
                    to_date=to_date,
                    duration=duration,
                    location=location if location else None,
                    description=None,
                )
            
            # Fallback: try to parse from links
            if len(links) >= 2:
                company_url = await links[0].get_attribute('href')
                detail_link = links[1]
                
                generics = await detail_link.locator('generic, span, div').all()
                texts = []
                for g in generics:
                    text = await g.text_content()
                    if text and text.strip() and len(text.strip()) < 200:
                        texts.append(text.strip())
                
                unique_texts = list(dict.fromkeys(texts))
                
                if len(unique_texts) >= 2:
                    position_title = unique_texts[0]
                    company_name = unique_texts[1]
                    work_times = unique_texts[2] if len(unique_texts) > 2 else ""
                    location = unique_texts[3] if len(unique_texts) > 3 else ""
                    
                    from_date, to_date, duration = self._parse_work_times(work_times)
                    
                    return Experience(
                        position_title=position_title,
                        institution_name=company_name,
                        linkedin_url=company_url,
                        from_date=from_date,
                        to_date=to_date,
                        duration=duration,
                        location=location,
                        description=None,
                    )
            
            entity = item.locator('div[data-view-name="profile-component-entity"]').first
            if await entity.count() == 0:
                return None

            children = await entity.locator("> *").all()
            if len(children) < 2:
                return None

            company_link = children[0].locator("a").first
            company_url = await company_link.get_attribute("href")

            detail_container = children[1]
            detail_children = await detail_container.locator("> *").all()

            if len(detail_children) == 0:
                return None

            has_nested_positions = False
            if len(detail_children) > 1:
                nested_list = await detail_children[1].locator(".pvs-list__container").count()
                has_nested_positions = nested_list > 0

            if has_nested_positions:
                return await self._parse_nested_experience(item, company_url, detail_children)
            else:
                first_detail = detail_children[0]
                nested_elements = await first_detail.locator("> *").all()

                if len(nested_elements) == 0:
                    return None

                span_container = nested_elements[0]
                outer_spans = await span_container.locator("> *").all()

                position_title = ""
                company_name = ""
                work_times = ""
                location = ""

                if len(outer_spans) >= 1:
                    aria_span = outer_spans[0].locator('span[aria-hidden="true"]').first
                    position_title = await aria_span.text_content()
                if len(outer_spans) >= 2:
                    aria_span = outer_spans[1].locator('span[aria-hidden="true"]').first
                    company_name = await aria_span.text_content()
                if len(outer_spans) >= 3:
                    aria_span = outer_spans[2].locator('span[aria-hidden="true"]').first
                    work_times = await aria_span.text_content()
                if len(outer_spans) >= 4:
                    aria_span = outer_spans[3].locator('span[aria-hidden="true"]').first
                    location = await aria_span.text_content()

                from_date, to_date, duration = self._parse_work_times(work_times)

                # Don't extract description as per user requirement
                # description = ""
                # if len(detail_children) > 1:
                #     description = await detail_children[1].inner_text()

                return Experience(
                    position_title=position_title.strip(),
                    institution_name=company_name.strip(),
                    linkedin_url=company_url,
                    from_date=from_date,
                    to_date=to_date,
                    duration=duration,
                    location=location.strip(),
                    description=None,  # User requested to not scrape job descriptions
                )

        except Exception as e:
            logger.debug(f"Error parsing experience: {e}")
            return None

    async def _parse_nested_experience(
        self, item, company_url: str, detail_children
    ) -> list[Experience]:
        """
        Parse nested experience positions (multiple roles at the same company).
        Returns a list of Experience objects.
        """
        experiences = []

        try:
            # Get company name from first detail
            first_detail = detail_children[0]
            nested_elements = await first_detail.locator("> *").all()
            if len(nested_elements) == 0:
                return []

            span_container = nested_elements[0]
            outer_spans = await span_container.locator("> *").all()

            # First span is company name for nested positions
            company_name = ""
            if len(outer_spans) >= 1:
                aria_span = outer_spans[0].locator('span[aria-hidden="true"]').first
                company_name = await aria_span.text_content()

            # Get the nested list from detail_children[1]
            nested_container = detail_children[1].locator(".pvs-list__container").first
            nested_items = await nested_container.locator(
                ".pvs-list__paged-list-item"
            ).all()

            for nested_item in nested_items:
                try:
                    # Each nested item has a link with position details
                    link = nested_item.locator("a").first
                    link_children = await link.locator("> *").all()

                    if len(link_children) == 0:
                        continue

                    # Navigate to get the spans
                    first_child = link_children[0]
                    nested_els = await first_child.locator("> *").all()
                    if len(nested_els) == 0:
                        continue

                    spans_container = nested_els[0]
                    position_spans = await spans_container.locator("> *").all()

                    # Extract position details
                    position_title = ""
                    work_times = ""
                    location = ""

                    if len(position_spans) >= 1:
                        aria_span = (
                            position_spans[0].locator('span[aria-hidden="true"]').first
                        )
                        position_title = await aria_span.text_content()
                    if len(position_spans) >= 2:
                        aria_span = (
                            position_spans[1].locator('span[aria-hidden="true"]').first
                        )
                        work_times = await aria_span.text_content()
                    if len(position_spans) >= 3:
                        aria_span = (
                            position_spans[2].locator('span[aria-hidden="true"]').first
                        )
                        location = await aria_span.text_content()

                    # Parse dates
                    from_date, to_date, duration = self._parse_work_times(work_times)

                    # Don't extract description as per user requirement
                    # description = ""
                    # if len(link_children) > 1:
                    #     description = await link_children[1].inner_text()

                    experiences.append(
                        Experience(
                            position_title=position_title.strip(),
                            institution_name=company_name.strip(),
                            linkedin_url=company_url,
                            from_date=from_date,
                            to_date=to_date,
                            duration=duration,
                            location=location.strip(),
                            description=None,  # User requested to not scrape job descriptions
                        )
                    )

                except Exception as e:
                    logger.debug(f"Error parsing nested position: {e}")
                    continue

        except Exception as e:
            logger.debug(f"Error parsing nested experience: {e}")

        # Filter to only return current role if present, otherwise return all
        if experiences:
            # Check for current roles (to_date is "Present" or None/empty)
            current_roles = [
                exp for exp in experiences 
                if not exp.to_date or exp.to_date.lower() in ["present", "current", "now"]
            ]
            if current_roles:
                logger.debug(f"Found {len(current_roles)} current role(s) out of {len(experiences)} total roles at {experiences[0].institution_name}")
                return current_roles  # Only return current role(s)
            
            logger.debug(f"No current roles found, returning all {len(experiences)} past roles")
        
        return experiences

    def _parse_work_times(
        self, work_times: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse work times string into from_date, to_date, duration.

        Examples:
        - "2000 - Present · 26 yrs 1 mo" -> ("2000", "Present", "26 yrs 1 mo")
        - "Jan 2020 - Dec 2022 · 2 yrs" -> ("Jan 2020", "Dec 2022", "2 yrs")
        - "2015 - Present" -> ("2015", "Present", None)
        """
        if not work_times:
            return None, None, None

        try:
            # Split by · to separate date range from duration
            parts = work_times.split("·")
            times = parts[0].strip() if len(parts) > 0 else ""
            duration = parts[1].strip() if len(parts) > 1 else None

            # Parse dates - split by " - " to get from and to
            if " - " in times:
                date_parts = times.split(" - ")
                from_date = date_parts[0].strip()
                to_date = date_parts[1].strip() if len(date_parts) > 1 else ""
            else:
                from_date = times
                to_date = ""

            return from_date, to_date, duration
        except Exception as e:
            logger.debug(f"Error parsing work times '{work_times}': {e}")
            return None, None, None

    async def _get_educations(self, base_url: str) -> list[Education]:
        """Extract educations from the main profile page Education section."""
        educations = []

        try:
            # Wait a bit for dynamic content
            await asyncio.sleep(1)
            
            # Try to find Education section on main page with multiple strategies
            education_heading = None
            heading_selectors = [
                'h2:has-text("Education")',
                'h2[id*="education"]',
                '[data-view-name="profile-card"]:has-text("Education")',
                'text="Education"',
            ]
            
            for selector in heading_selectors:
                try:
                    heading = self.page.locator(selector).first
                    if await heading.count() > 0:
                        education_heading = heading
                        break
                except:
                    continue
            
            if education_heading and await education_heading.count() > 0:
                # Try to find the section container
                education_section = None
                section_strategies = [
                    education_heading.locator('xpath=ancestor::*[.//ul or .//ol][1]'),
                    education_heading.locator('xpath=ancestor::*[4]'),
                    education_heading.locator('xpath=following-sibling::*[1]'),
                    education_heading.locator('xpath=ancestor::section[1]'),
                ]
                
                for section_locator in section_strategies:
                    if await section_locator.count() > 0:
                        education_section = section_locator
                        break
                
                if education_section and await education_section.count() > 0:
                    # Try multiple item selectors
                    item_selectors = ['ul > li', 'ol > li', 'li', '[data-view-name="profile-component-entity"]']
                    items = []
                    for item_sel in item_selectors:
                        found_items = await education_section.locator(item_sel).all()
                        if found_items:
                            items = found_items
                            break
                    
                    for item in items:
                        try:
                            edu = await self._parse_main_page_education(item)
                            if edu and edu.institution_name:
                                educations.append(edu)
                        except Exception as e:
                            logger.debug(f"Error parsing education from main page: {e}")
                            continue
            
            # If no educations found on main page, try the details page
            if not educations:
                logger.debug("No educations found on main page, trying details page...")
                edu_url = urljoin(base_url, "details/education")
                await self.navigate_and_wait(edu_url)
                await self.page.wait_for_selector("main", timeout=10000)
                await self.wait_and_focus(2)  # Wait longer for content
                await self.scroll_page_to_half()
                await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=5)

                items = []
                # Try multiple selectors for education items
                item_selectors = [
                    'ul > li',
                    'ol > li',
                    '.pvs-list__paged-list-item',
                    '[data-view-name="profile-component-entity"]',
                    'li[data-view-name*="education"]',
                    'li',
                    '[role="listitem"]',
                ]
                
                main_element = self.page.locator('main')
                if await main_element.count() > 0:
                    # Wait a bit more for content to load
                    await asyncio.sleep(3)  # Wait longer for dynamic content
                    await self.scroll_page_to_half()  # Scroll to trigger lazy loading
                    await asyncio.sleep(1)
                    
                    # Try multiple strategies to find education items
                    # Strategy 1: Look for any elements containing institution links (not just li)
                    institution_links = await main_element.locator('a[href*="/school/"], a[href*="/company/"], a[href*="/in/company/"]').all()
                    logger.debug(f"Found {len(institution_links)} institution links in main")
                    
                    if institution_links:
                        seen_items = set()
                        for link in institution_links[:20]:  # Check first 20 links
                            try:
                                # Get the closest parent that looks like an education item
                                # Try to find a container element
                                href = await link.get_attribute('href')
                                link_text = await link.text_content()
                                logger.debug(f"Institution link found: {link_text} -> {href}")
                                
                                # Try to find parent container - could be various elements
                                parent_strategies = [
                                    link.locator('xpath=ancestor::*[@role="listitem"][1]'),
                                    link.locator('xpath=ancestor::li[1]'),
                                    link.locator('xpath=ancestor::div[contains(@class, "pvs")][1]'),
                                    link.locator('xpath=ancestor::*[contains(@data-view-name, "profile")][1]'),
                                ]
                                
                                parent_item = None
                                for strategy in parent_strategies:
                                    if await strategy.count() > 0:
                                        parent_item = strategy.first
                                        break
                                
                                # Get text from parent or from link's surrounding context
                                text = None
                                item_to_add = None
                                
                                if parent_item:
                                    text = await parent_item.text_content()
                                    item_to_add = parent_item
                                else:
                                    # If no parent found, try to get text from the link's parent container
                                    link_parent = link.locator('xpath=parent::*')
                                    if await link_parent.count() > 0:
                                        text = await link_parent.text_content()
                                        item_to_add = link_parent.first
                                    else:
                                        # Last resort: use the link itself and get its text content
                                        text = await link.text_content()
                                        # Also try to get sibling elements
                                        link_container = link.locator('xpath=ancestor::*[position()<=3]')
                                        if await link_container.count() > 0:
                                            container_text = await link_container.first.text_content()
                                            if container_text and len(container_text) > len(text):
                                                text = container_text
                                                item_to_add = link_container.first
                                
                                if text and len(text.strip()) > 20:
                                    text_lower = text.lower()
                                    # Skip footer/help items
                                    if not any(skip in text_lower for skip in [
                                        'help center', 'settings', 'privacy', 'recommendation',
                                        'transparency', 'cookie', 'terms', 'about', 'accessibility',
                                        'questions?', 'manage your account', 'promoted', 'more profiles'
                                    ]):
                                        item_id = f"{href}_{text[:30]}"
                                        if item_id not in seen_items and item_to_add:
                                            items.append(item_to_add)
                                            seen_items.add(item_id)
                                            logger.debug(f"Added education item candidate {len(items)}: {text[:80]}")
                                            if len(items) >= 10:
                                                break
                            except Exception as e:
                                logger.debug(f"Error processing institution link: {e}")
                                continue
                        
                        if items:
                            logger.debug(f"Found {len(items)} education items from institution links")
                    
                    # Strategy 2: Get all list items and check if they contain institution links
                    all_lis = await main_element.locator('li').all()
                    logger.debug(f"Found {len(all_lis)} total li elements in main for education")
                    if all_lis and not items:
                        seen_items = set()
                        for i, li in enumerate(all_lis[:30]):  # Check first 30
                            try:
                                # Check if this li contains an institution link
                                has_institution_link = await li.locator('a[href*="/school/"], a[href*="/company/"], a[href*="/in/company/"]').count() > 0
                                
                                if has_institution_link:
                                    text = await li.text_content()
                                    logger.debug(f"Li {i+1} has institution link, text: {text[:100] if text else 'None'}")
                                    if text and len(text.strip()) > 20:
                                        text_lower = text.lower()
                                        # Skip footer/help items
                                        if not any(skip in text_lower for skip in [
                                            'help center', 'settings', 'privacy', 'recommendation',
                                            'transparency', 'cookie', 'terms', 'about', 'accessibility',
                                            'questions?', 'manage your account', 'promoted', 'more profiles'
                                        ]):
                                            # Create a unique ID
                                            item_id = text[:50]
                                            if item_id not in seen_items:
                                                items.append(li)
                                                seen_items.add(item_id)
                                                logger.debug(f"Added education item candidate {len(items)}: {text[:80]}")
                                                if len(items) >= 10:
                                                    break
                            except Exception as e:
                                logger.debug(f"Error processing li {i+1}: {e}")
                                continue
                        
                        if items:
                            logger.debug(f"Found {len(items)} education items from list items with institution links")
                        else:
                            logger.debug("No education items found with institution links")
                    
                    # Strategy 2: Try to find the actual education list container
                    if not items:
                        education_containers = [
                            main_element.locator('[id*="education"]'),
                            main_element.locator('[data-section*="education"]'),
                            main_element.locator('section:has-text("Education")'),
                            main_element.locator('ul, ol'),
                        ]
                        
                        for container_sel in education_containers:
                            if await container_sel.count() > 0:
                                container = container_sel.first
                                # Get items from this container
                                found_items = await container.locator('li, [role="listitem"]').all()
                                if found_items:
                                    # Filter and validate items
                                    for item in found_items:
                                        try:
                                            text = await item.text_content()
                                            if text:
                                                text_lower = text.lower()
                                                # Skip footer/help items
                                                if any(skip in text_lower for skip in [
                                                    'help center', 'settings', 'privacy', 'recommendation',
                                                    'transparency', 'cookie', 'terms', 'about', 'accessibility',
                                                    'questions?', 'manage your account'
                                                ]):
                                                    continue
                                                # Must have reasonable length and look like education (has institution-like text)
                                                if len(text.strip()) > 20 and any(word in text_lower for word in ['university', 'college', 'school', 'institute', 'degree', 'doctorate', 'bachelor', 'master']):
                                                    items.append(item)
                                        except:
                                            continue
                                    
                                    if items:
                                        logger.debug(f"Found {len(items)} education items from container")
                                        break
                    
                    # If still no items, try selectors
                    if not items:
                        for item_sel in item_selectors:
                            found_items = await main_element.locator(item_sel).all()
                            if found_items:
                                # Filter out footer/help items
                                filtered_items = []
                                for item in found_items:
                                    try:
                                        text = await item.text_content()
                                        if text:
                                            text_lower = text.lower()
                                            # Skip footer/help items
                                            if any(skip in text_lower for skip in [
                                                'help center', 'settings', 'privacy', 'recommendation',
                                                'transparency', 'cookie', 'terms', 'about', 'accessibility',
                                                'questions?', 'manage your account'
                                            ]):
                                                continue
                                            # Must have reasonable length
                                            if len(text.strip()) > 20:
                                                filtered_items.append(item)
                                    except:
                                        continue
                                
                                if filtered_items:
                                    items = filtered_items
                                    logger.debug(f"Found {len(items)} education items using selector: {item_sel} (after filtering)")
                                    break
                    
                    # Fallback: try to get all list items and filter
                    if not items:
                        all_lis = await main_element.locator('li').all()
                        if all_lis:
                            logger.debug(f"Found {len(all_lis)} total li elements in main for education")
                            # Filter to likely education items (have links and reasonable text)
                            for li in all_lis:
                                try:
                                    text = await li.text_content()
                                    if text:
                                        text_lower = text.lower()
                                        # Skip footer/help items
                                        if any(skip in text_lower for skip in [
                                            'help center', 'settings', 'privacy', 'recommendation',
                                            'transparency', 'cookie', 'terms', 'about', 'accessibility',
                                            'questions?', 'manage your account'
                                        ]):
                                            continue
                                        links = await li.locator('a').count()
                                        # Education items usually have links to institutions
                                        if links > 0 and len(text.strip()) > 15:
                                            items.append(li)
                                            if len(items) >= 10:  # Limit to first 10 valid items
                                                break
                                except:
                                    continue

                for i, item in enumerate(items):
                    try:
                        # Debug: log item text
                        item_text = await item.text_content()
                        logger.debug(f"Parsing education item {i+1}: {item_text[:200] if item_text else 'No text'}")
                        
                        # Debug: log item HTML structure
                        item_html = await item.inner_html()
                        logger.debug(f"Item {i+1} HTML structure: {item_html[:500] if item_html else 'No HTML'}")
                        
                        edu = await self._parse_education_item(item)
                        if edu and edu.institution_name:
                            logger.debug(f"Added education: {edu.institution_name} - {edu.degree}")
                            educations.append(edu)
                        else:
                            logger.debug(f"Failed to parse education item {i+1}: edu={edu}, institution_name={edu.institution_name if edu else 'None'}")
                    except Exception as e:
                        logger.debug(f"Error parsing education item {i+1}: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
                        continue

        except Exception as e:
            logger.warning(
                f"Error getting educations: {e}. The education section may not be publicly visible or the page structure has changed."
            )

        logger.info(f"Extracted {len(educations)} educations")
        return educations
    
    async def _parse_main_page_education(self, item) -> Optional[Education]:
        """Parse education from main profile page list item with [logo_link, details_link] structure."""
        try:
            links = await item.locator('a').all()
            if not links:
                return None
            
            institution_url = await links[0].get_attribute('href')
            detail_link = links[1] if len(links) > 1 else links[0]
            
            unique_texts = await self._extract_unique_texts_from_element(detail_link)
            
            if not unique_texts:
                return None
            
            institution_name = unique_texts[0]
            degree = None
            times = ""
            
            if len(unique_texts) == 3:
                degree = unique_texts[1]
                times = unique_texts[2]
            elif len(unique_texts) == 2:
                second = unique_texts[1]
                if " - " in second or any(c.isdigit() for c in second):
                    times = second
                else:
                    degree = second
            
            from_date, to_date = self._parse_education_times(times)
            
            return Education(
                institution_name=institution_name,
                degree=degree.strip() if degree else None,
                linkedin_url=institution_url,
                from_date=from_date,
                to_date=to_date,
                description=None,
            )
            
        except Exception as e:
            logger.debug(f"Error parsing main page education: {e}")
            return None

    async def _parse_education_item(self, item) -> Optional[Education]:
        """Parse a single education item - handles concatenated text format from LinkedIn."""
        try:
            # Get all text from the item first
            item_text = await item.text_content()
            if not item_text or len(item_text.strip()) < 10:
                logger.debug("Education item text too short or empty")
                return None
            
            logger.debug(f"Parsing education with text: {item_text[:200]}")
            
            # Try to extract structured data
            links = await item.locator('a').all()
            institution_url = None
            if links:
                # First link is usually institution
                institution_url = await links[0].get_attribute('href')
            
            # LinkedIn often concatenates text like: "UniversityNameDegree, FieldDateRange"
            # Example: "Stanford UniversityB.S., Symbolic Systems1985 û 1990"
            
            import re
            
            institution_name = None
            degree = None
            times = ""
            
            # Strategy 1: Parse concatenated text using regex patterns
            # Find date range pattern (handles both - and û as separators)
            date_range_pattern = r'((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+)?\d{4}\s*[û\-–—]\s*((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+)?\d{4}'
            date_match = re.search(date_range_pattern, item_text, re.IGNORECASE)
            
            if date_match:
                times = date_match.group(0)
                # Everything before the date range
                before_dates = item_text[:date_match.start()].strip()
                
                # Now split institution from degree
                # Look for degree keywords to find the split point
                degree_keywords = [
                    'honorary doctorate', 'honorary doctor', 'doctor of laws',
                    'bachelor', 'master', 'doctorate', 'doctor', 'phd', 'ph.d',
                    'm.st.', 'm.st', 'b.s.', 'b.s', 'm.a.', 'm.a', 'b.a.', 'b.a',
                    'm.sc.', 'm.sc', 'b.sc.', 'b.sc', 'mba', 'm.b.a',
                    'b.tech', 'm.tech', 'llb', 'llm', 'jd', 'md', 'dds', 'dvm'
                ]
                
                # Try to find where the degree starts
                best_split_pos = -1
                best_keyword = None
                for keyword in degree_keywords:
                    keyword_pos = before_dates.lower().find(keyword)
                    if keyword_pos > 0:  # Must be after some institution text
                        # Check if this is the earliest keyword match (institution comes first)
                        if best_split_pos == -1 or keyword_pos < best_split_pos:
                            best_split_pos = keyword_pos
                            best_keyword = keyword
                
                if best_split_pos > 0:
                    # Found a good split point
                    institution_name = before_dates[:best_split_pos].strip()
                    degree = before_dates[best_split_pos:].strip()
                    
                    # Clean up institution name (remove trailing punctuation)
                    institution_name = institution_name.rstrip('.,;:')
                else:
                    # No clear degree keyword found
                    # Try to split by common patterns like ", " or capital letter followed by period
                    # Example: "University NameB.S." -> split before "B.S."
                    degree_abbrev_pattern = r'([A-Z]\.(?:[A-Z]\.)+|[A-Z]\.[A-Z][a-z]+)'
                    degree_match = re.search(degree_abbrev_pattern, before_dates)
                    if degree_match:
                        institution_name = before_dates[:degree_match.start()].strip()
                        degree = before_dates[degree_match.start():].strip()
                    else:
                        # Last resort: assume first comma separates degree field
                        if ',' in before_dates:
                            parts = before_dates.split(',', 1)
                            # Check which part is more likely the institution
                            # Institution usually has "University", "College", "Institute"
                            if any(word in parts[0].lower() for word in ['university', 'college', 'institute', 'school']):
                                institution_name = parts[0].strip()
                                degree = parts[1].strip() if len(parts) > 1 else None
                            else:
                                # Maybe it's reversed
                                institution_name = before_dates  # Take whole thing as institution
                                degree = None
                        else:
                            # No comma, no clear pattern - use whole text as institution
                            institution_name = before_dates
                            degree = None
            else:
                # No date range found - try other strategies
                # Split by newlines
                lines = [line.strip() for line in item_text.split('\n') if line.strip() and len(line.strip()) > 2]
                
                # Filter out "Activities and societies" lines
                valid_lines = [l for l in lines if not any(skip in l.lower() for skip in [
                    'activities and societies', 'linkedin', 'view', 'more', 'show', 'hide'
                ])]
                
                if valid_lines:
                    # First line is usually institution
                    institution_name = valid_lines[0]
                    # Second line is usually degree
                    if len(valid_lines) > 1:
                        degree = valid_lines[1]
                    # Third line might be dates
                    if len(valid_lines) > 2:
                        times = valid_lines[2]
            
            # Final validation - filter out non-education items
            if institution_name:
                combined_text = f"{institution_name} {degree or ''}".lower()
                if any(skip in combined_text for skip in [
                    'help center', 'settings', 'privacy', 'recommendation',
                    'transparency', 'cookie', 'terms', 'accessibility',
                    'questions?', 'manage your account'
                ]):
                    logger.debug("Filtered out non-education item")
                    return None
                
                # Parse date range
                from_date, to_date = self._parse_education_times(times)
                
                return Education(
                    institution_name=institution_name.strip(),
                    degree=degree.strip() if degree else None,
                    linkedin_url=institution_url,
                    from_date=from_date,
                    to_date=to_date,
                    description=None,
                )
            
            logger.debug("Failed to extract institution name from education item")
            return None

        except Exception as e:
            logger.debug(f"Error parsing education: {e}")
            return None

    def _parse_education_times(self, times: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse education times string into from_date, to_date.

        Examples:
        - "1973 - 1977" -> ("1973", "1977")
        - "2015 û 2020" -> ("2015", "2020")
        - "May 2024 – May 2024" -> ("May 2024", "May 2024")
        - "2015" -> ("2015", "2015")
        - "" -> (None, None)
        """
        if not times:
            return None, None

        try:
            import re
            # Handle multiple types of dashes: -, û, –, —
            # Split by any dash-like character with optional spaces
            parts = re.split(r'\s*[û\-–—]\s*', times, maxsplit=1)
            
            if len(parts) >= 2:
                from_date = parts[0].strip()
                to_date = parts[1].strip()
            else:
                # Single date/year
                from_date = times.strip()
                to_date = times.strip()

            return from_date if from_date else None, to_date if to_date else None
        except Exception as e:
            logger.debug(f"Error parsing education times '{times}': {e}")
            return None, None

    async def _get_accomplishments(self, base_url: str) -> list[Accomplishment]:
        accomplishments = []

        accomplishment_sections = [
            # Certifications are now handled by _get_certifications method
            ("publications", "publication"),
            ("courses", "course"),
            ("projects", "project"),
            ("languages", "language"),
        ]

        for url_path, category in accomplishment_sections:
            try:
                section_url = urljoin(base_url, f"details/{url_path}/")
                await self.navigate_and_wait(section_url)
                await self.page.wait_for_selector("main", timeout=10000)
                await self.wait_and_focus(1)

                nothing_to_see = await self.page.locator(
                    'text="Nothing to see for now"'
                ).count()
                if nothing_to_see > 0:
                    logger.debug(f"No {category} items found on profile")
                    continue

                # Try to find the main container with multiple strategies
                main_element = self.page.locator("main")
                if await main_element.count() == 0:
                    continue
                
                # LinkedIn now uses div structure, try multiple selectors
                items = []
                item_selectors = [
                    ".pvs-list__paged-list-item",
                    "ul > li",
                    "ol > li",
                    "> div > div",  # New structure
                ]
                
                # Try to find a container first
                container_selectors = [".pvs-list__container", "ul", "ol", "div.pvs-list"]
                container = None
                for cont_sel in container_selectors:
                    cont = main_element.locator(cont_sel).first
                    if await cont.count() > 0:
                        container = cont
                        break
                
                if container:
                    # Search within container
                    for item_sel in item_selectors:
                        found_items = await container.locator(item_sel).all()
                        if found_items and 1 <= len(found_items) <= 50:
                            items = found_items
                            logger.debug(f"Found {len(items)} {category} items with selector: {item_sel}")
                            break
                else:
                    # Search in main element directly
                    for item_sel in item_selectors:
                        found_items = await main_element.locator(item_sel).all()
                        if found_items and 1 <= len(found_items) <= 50:
                            items = found_items
                            logger.debug(f"Found {len(items)} {category} items with selector: {item_sel}")
                            break
                
                if not items:
                    logger.debug(f"No items found for {category}")
                    continue

                seen_titles = set()
                for item in items:
                    try:
                        accomplishment = await self._parse_accomplishment_item(
                            item, category
                        )
                        if accomplishment and accomplishment.title not in seen_titles:
                            seen_titles.add(accomplishment.title)
                            accomplishments.append(accomplishment)
                    except Exception as e:
                        logger.debug(f"Error parsing {category} item: {e}")
                        continue

            except Exception as e:
                logger.debug(f"Error getting {category}s: {e}")
                continue

        return accomplishments

    async def _parse_accomplishment_item(
        self, item, category: str
    ) -> Optional[Accomplishment]:
        try:
            # Get full text content first for debugging
            full_text = await item.text_content()
            if not full_text or len(full_text.strip()) < 5:
                return None
            
            logger.debug(f"Parsing {category} item: {full_text[:200]}")
            
            # Try to find entity div
            entity = item.locator(
                'div[data-view-name="profile-component-entity"]'
            ).first
            if await entity.count() > 0:
                spans = await entity.locator('span[aria-hidden="true"]').all()
            else:
                spans = await item.locator('span[aria-hidden="true"]').all()
            
            # If no spans with aria-hidden, try getting all spans
            if not spans:
                spans = await item.locator('span').all()

            title = ""
            issuer = ""
            issued_date = ""
            credential_id = ""
            description = ""

            # Extract text from spans
            texts = []
            for span in spans[:10]:  # Check more spans
                text = await span.text_content()
                if text and text.strip() and len(text.strip()) < 500:
                    texts.append(text.strip())
            
            # Remove duplicates while preserving order
            seen = set()
            unique_texts = []
            for text in texts:
                if text not in seen:
                    seen.add(text)
                    unique_texts.append(text)
            
            logger.debug(f"Unique texts found: {unique_texts[:5]}")
            
            # If no spans found or texts extracted, try to get all text nodes from links
            if not unique_texts:
                logger.debug("No spans found, trying alternative extraction")
                # Try to find links and get their text
                links = await item.locator('a').all()
                for link in links[:3]:
                    link_text = await link.text_content()
                    if link_text and link_text.strip() and len(link_text.strip()) < 300:
                        link_text = link_text.strip()
                        if link_text not in seen:
                            seen.add(link_text)
                            unique_texts.append(link_text)
                
                # Also try to get text from divs
                if not unique_texts:
                    divs = await item.locator('div > span').all()
                    for div in divs[:10]:
                        div_text = await div.text_content()
                        if div_text and div_text.strip() and len(div_text.strip()) < 300:
                            div_text = div_text.strip()
                            if div_text not in seen:
                                seen.add(div_text)
                                unique_texts.append(div_text)
                
                logger.debug(f"Alternative extraction found: {unique_texts[:5]}")

            # Parse the texts
            for i, text in enumerate(unique_texts[:10]):
                if i == 0 and not title:
                    # First text is usually the title
                    title = text
                elif "Issued by" in text or "Issuing Organization" in text:
                    # Extract issuer and date
                    parts = text.split("·")
                    issuer_text = parts[0].replace("Issued by", "").replace("Issuing Organization", "").strip()
                    if issuer_text:
                        issuer = issuer_text
                    if len(parts) > 1:
                        issued_date = parts[1].strip()
                elif "Issued " in text and not issued_date:
                    # Date line
                    issued_date = text.replace("Issued ", "").strip()
                elif "Credential ID" in text:
                    credential_id = text.replace("Credential ID ", "").replace("Credential ID:", "").strip()
                elif i == 1 and not issuer and not any(x in text.lower() for x in ['show credential', 'see credential', 'credential id']):
                    # Second line might be issuer
                    issuer = text
                elif (
                    any(
                        month in text
                        for month in [
                            "Jan",
                            "Feb",
                            "Mar",
                            "Apr",
                            "May",
                            "Jun",
                            "Jul",
                            "Aug",
                            "Sep",
                            "Oct",
                            "Nov",
                            "Dec",
                        ]
                    )
                    and not issued_date
                    and not any(x in text.lower() for x in ['expires', 'expiration'])
                ):
                    # Date found
                    if "·" in text:
                        parts = text.split("·")
                        issued_date = parts[0].strip()
                    else:
                        issued_date = text

            # Try to find credential URL
            link = item.locator('a[href*="credential"], a[href*="verify"], a[href*="cert"]').first
            credential_url = (
                await link.get_attribute("href") if await link.count() > 0 else None
            )

            if not title or len(title) > 300:
                logger.debug(f"Invalid title for {category}: {title[:100] if title else 'empty'}")
                return None

            return Accomplishment(
                category=category,
                title=title,
                issuer=issuer if issuer else None,
                issued_date=issued_date if issued_date else None,
                credential_id=credential_id if credential_id else None,
                credential_url=credential_url,
                description=description if description else None,
            )

        except Exception as e:
            logger.debug(f"Error parsing accomplishment: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None

    async def _get_certifications(self, base_url: str) -> list[Accomplishment]:
        """
        Extract certifications from LinkedIn profile using improved extraction.
        
        This method specifically handles the newer LinkedIn certification structure.
        """
        certifications = []
        
        try:
            # Navigate to certifications detail page
            cert_url = urljoin(base_url, "details/certifications/")
            await self.navigate_and_wait(cert_url)
            await self.page.wait_for_selector("main", timeout=10000)
            await self.wait_and_focus(2)
            
            # Scroll to load all certifications
            await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=3)
            await asyncio.sleep(1)
            
            # Check for "Nothing to see" message
            nothing_to_see = await self.page.locator('text="Nothing to see for now"').count()
            if nothing_to_see > 0:
                logger.debug("No certifications found on profile")
                return certifications
            
            main_element = self.page.locator('main')
            if await main_element.count() == 0:
                logger.debug("No main element found on certifications page")
                return certifications
            
            logger.debug("Looking for certification items on page")
            
            # LinkedIn's new structure uses divs with specific classes
            # Each certification block is separated by <hr> tags
            # Try to find certification containers
            
            # Strategy 1: Look for divs that contain both certification name and issuer
            # Each cert has a structure with company logo + text content
            
            # Find all <hr> elements which separate certifications
            hr_elements = await main_element.locator('hr').all()
            logger.debug(f"Found {len(hr_elements)} hr separator elements")
            
            # If we have hr separators, try to extract blocks between them
            if len(hr_elements) > 0:
                # Get all paragraphs within the main content area before the first "More profiles" section
                # Look for the main certifications container
                
                # Try to find all certification item containers
                # They are typically in divs that contain a logo and text
                cert_containers = await main_element.locator('div._86f1bd63, div[class*="_86f1bd63"]').all()
                logger.debug(f"Found {len(cert_containers)} potential certification containers")
                
                if not cert_containers:
                    # Fallback: try to find divs containing logos/images
                    cert_containers = await main_element.locator('div:has(img[alt*="logo"])').all()
                    logger.debug(f"Found {len(cert_containers)} containers with logos (fallback)")
                
                seen_titles = set()
                
                for idx, container in enumerate(cert_containers):
                    try:
                        # Get all text from this container
                        full_text = await container.text_content()
                        if not full_text or len(full_text.strip()) < 10:
                            continue
                        
                        # Get all paragraphs within this container
                        paragraphs = await container.locator('p').all()
                        if len(paragraphs) < 2:
                            continue
                        
                        texts = []
                        for p in paragraphs[:10]:  # Limit to first 10 paragraphs
                            p_text = await p.text_content()
                            if p_text and len(p_text.strip()) > 2:
                                texts.append(p_text.strip())
                        
                        if len(texts) < 2:
                            continue
                        
                        # Extract certification details
                        title = ""
                        issuer = ""
                        issued_date = ""
                        
                        # First meaningful text is usually the title
                        # Second is the issuer
                        # Third might be the issued date or skills
                        
                        for text in texts:
                            # Skip navigation and UI elements
                            if any(skip in text for skip in [
                                "Licenses & certifications",
                                "Skills:",
                                "Navigate back",
                                "Why am I seeing this",
                                "Manage your ad",
                                "Hide or report",
                                "Tell us why",
                                "Your feedback",
                                ".pdf",  # Skip PDF filenames
                                "ASZ Cybersecurity",  # Skip PDF references
                                "Show credential",
                                "See credential",
                            ]):
                                continue
                            
                            if not title:
                                # First valid text is the title
                                if len(text) > 10 and not text.startswith("Issued"):
                                    title = text
                            elif not issuer and not text.startswith("Issued"):
                                # Second valid text is the issuer
                                if len(text) < 100:
                                    issuer = text
                            elif text.startswith("Issued"):
                                # Date line
                                issued_date = text
                                break
                        
                        # Validate and add certification
                        if title and issuer and title not in seen_titles:
                            # Clean up whitespace
                            title = " ".join(title.split())
                            issuer = " ".join(issuer.split())
                            
                            # Additional validation: title should be reasonable
                            if (len(title) > 10 and 
                                len(title) < 200 and
                                len(issuer) < 100 and
                                not any(bad in title.lower() for bad in ["why am i", "manage your", "tell us"])):
                                
                                logger.debug(f"Found certification {idx+1}: {title} by {issuer} ({issued_date})")
                                
                                certifications.append(
                                    Accomplishment(
                                        category="certification",
                                        title=title,
                                        issuer=issuer,
                                        issued_date=issued_date if issued_date else None,
                                    )
                                )
                                seen_titles.add(title)
                    
                    except Exception as e:
                        logger.debug(f"Error processing certification container {idx}: {e}")
                        continue
            
            logger.info(f"Extracted {len(certifications)} certifications")
            
        except Exception as e:
            logger.warning(f"Error getting certifications: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return certifications

    async def _get_skills(self, base_url: str) -> list[str]:
        """Extract skills from the LinkedIn profile."""
        skills = []
        
        try:
            # Navigate to skills detail page
            skills_url = urljoin(base_url, "details/skills/")
            await self.navigate_and_wait(skills_url)
            await self.page.wait_for_selector("main", timeout=10000)
            await self.wait_and_focus(2)
            
            # Scroll to load all skills
            await self.scroll_page_to_half()
            await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=5)
            
            # Wait a bit more for dynamic content
            await asyncio.sleep(2)
            
            main_element = self.page.locator('main')
            if await main_element.count() == 0:
                logger.debug("No main element found on skills page")
                return skills
            
            seen_skills = set()
            
            # Strategy: Find all "Endorse" buttons (one per skill) and extract skill names
            # LinkedIn concatenates skill names with organization names without spaces
            # Examples:
            # - "ProgrammingAnil Neerukonda Institute...Endorse"
            # - "Computer VisionMachine Learning Intern at Ziegler...Endorse"
            # - "Python (Programming Language)Endorse"
            
            logger.debug("Looking for Endorse buttons to extract skills")
            
            endorse_buttons = await main_element.locator('button:has-text("Endorse")').all()
            logger.debug(f"Found {len(endorse_buttons)} Endorse buttons")
            
            for idx, button in enumerate(endorse_buttons):
                try:
                    # Try to find the parent container
                    parent_containers = [
                        button.locator('xpath=ancestor::li[1]'),
                        button.locator('xpath=ancestor::div[contains(@class, "pvs-list__item")][1]'),
                        button.locator('xpath=ancestor::div[1]'),
                        button.locator('xpath=..'),  # Direct parent
                    ]
                    
                    parent = None
                    for container in parent_containers:
                        if await container.count() > 0:
                            parent = container
                            break
                    
                    if not parent:
                        logger.debug(f"No parent container found for button {idx+1}")
                        continue
                    
                    # Get full text of the parent
                    full_text = await parent.text_content()
                    if not full_text or not full_text.strip():
                        logger.debug(f"Empty text content for skill {idx+1}")
                        continue
                    
                    full_text = full_text.strip()
                    
                    # Remove "Endorse" from the end
                    if full_text.endswith('Endorse'):
                        full_text = full_text[:-7].strip()
                    
                    logger.debug(f"Processing skill {idx+1}: {full_text[:80]}...")
                    
                    # Now extract the skill name from the beginning
                    # The skill name ends when we hit organization/job title patterns
                    skill_name = full_text  # Default to full text
                    matched = False
                    
                    # Strategy 1: Try to find where job title/organization starts
                    # Look for patterns like "Machine Learning Intern at", "Anil Neerukonda", etc.
                    
                    # First, try splitting by " at " (indicates job title)
                    if ' at ' in full_text:
                        parts = full_text.split(' at ')
                        # Check if the part before " at " contains a job title pattern
                        before_at = parts[0]
                        # Look for job titles at the end (e.g., "Computer VisionMachine Learning Intern")
                        job_title_pattern = r'(.*?)([A-Z][a-z]+ [A-Z][a-z]+ Intern|Developer|Engineer|Analyst)$'
                        job_match = re.match(job_title_pattern, before_at)
                        if job_match and job_match.group(1).strip():
                            skill_name = job_match.group(1).strip()
                            matched = True
                            logger.debug(f"Extracted before job title: {skill_name}")
                    
                    # Strategy 2: Try organization patterns (e.g., "Anil Neerukonda Institute")
                    if not matched:
                        org_start_pattern = r'^(.*?)([A-Z][a-z]+\s+[A-Z][a-z]+\s+Institute|[A-Z][a-z]+\s+University|Anil\s+Neerukonda)'
                        match = re.match(org_start_pattern, full_text)
                        if match:
                            skill_name = match.group(1).strip()
                            matched = True
                            logger.debug(f"Extracted before organization: {skill_name}")
                    
                    # Strategy 3: Detect camelCase concatenation (e.g., "ProgrammingAnil")
                    # Find first occurrence of lowercase followed by uppercase (without space)
                    if not matched and len(full_text) > 3:
                        camel_pattern = r'^(.*?[a-z])([A-Z][a-z].*)'
                        camel_match = re.match(camel_pattern, full_text)
                        if camel_match:
                            potential = camel_match.group(1).strip()
                            # Make sure it's reasonable (not too short)
                            if len(potential) > 2:
                                skill_name = potential
                                matched = True
                                logger.debug(f"Extracted using camelCase split: {skill_name}")
                    
                    # Clean up endorsement information
                    # Remove patterns like "(0 endorsements)", "(5 endorsements)", etc.
                    endorsement_patterns = [
                        r'\s*\(\d+\s+endorsements?\)',  # (0 endorsements), (5 endorsement)
                        r'\s*\d+\s+endorsements?',       # 5 endorsements
                    ]
                    for pattern in endorsement_patterns:
                        skill_name = re.sub(pattern, '', skill_name, flags=re.IGNORECASE)
                    
                    skill_name = skill_name.strip()
                    
                    # Final validation
                    if skill_name and skill_name not in ['Endorse', 'Show all', '']:
                        if skill_name not in seen_skills:
                            skills.append(skill_name)
                            seen_skills.add(skill_name)
                            logger.debug(f"✓ Extracted skill {idx+1}: {skill_name}")
                        else:
                            logger.debug(f"Already extracted: {skill_name}")
                    else:
                        logger.debug(f"Invalid skill name: {skill_name}")
                
                except Exception as e:
                    logger.debug(f"Error extracting skill from button {idx+1}: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                    continue
            
            logger.info(f"Extracted {len(skills)} skills: {skills[:10] if len(skills) <= 10 else skills[:10] + ['...']}")
            
        except Exception as e:
            logger.warning(f"Error getting skills: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return skills
    
    async def _get_contacts(self, base_url: str) -> list[Contact]:
        """Extract phone and email from the contact-info overlay dialog."""
        contacts = []

        try:
            contact_url = urljoin(base_url, "overlay/contact-info/")
            await self.navigate_and_wait(contact_url)
            await self.wait_and_focus(2)

            # Try multiple selectors for the modal/dialog
            modal = None
            modal_selectors = [
                'dialog',
                '[role="dialog"]',
                '.artdeco-modal',
                '#artdeco-modal-outlet dialog',
                'div[data-view-name="overlay-modal"]'
            ]
            
            for selector in modal_selectors:
                modal = self.page.locator(selector).first
                if await modal.count() > 0:
                    logger.debug(f"Found modal with selector: {selector}")
                    break
            
            if not modal or await modal.count() == 0:
                logger.warning("Contact info modal not found")
                return contacts

            # Get all text content from modal for debugging
            modal_text = await modal.text_content()
            logger.debug(f"Modal text content: {modal_text[:200]}")

            # Strategy 1: Look for email links (mailto:)
            email_links = await modal.locator('a[href^="mailto:"]').all()
            for link in email_links:
                try:
                    href = await link.get_attribute('href')
                    if href and "mailto:" in href:
                        email_value = href.replace("mailto:", "").strip()
                        # Try to find label
                        label = None
                        parent = link.locator('xpath=ancestor::*[2]')
                        if await parent.count() > 0:
                            parent_text = await parent.text_content()
                            if "(" in parent_text and ")" in parent_text:
                                import re
                                label_match = re.search(r'\(([^)]+)\)', parent_text)
                                if label_match:
                                    label = label_match.group(1)
                        
                        contacts.append(Contact(type="email", value=email_value, label=label))
                        logger.debug(f"Found email: {email_value}")
                except Exception as e:
                    logger.debug(f"Error extracting email: {e}")

            # Strategy 2: Look for phone numbers by searching for "Phone" text and nearby numbers
            import re
            # Find all text that contains "phone" (case insensitive)
            phone_sections = await modal.locator('*:has-text("Phone"), *:has-text("phone")').all()
            
            for section in phone_sections:
                try:
                    section_text = await section.text_content()
                    if not section_text:
                        continue
                    
                    # Look for phone number patterns
                    # Matches: 1234567890, 123-456-7890, (123) 456-7890, +1 123 456 7890, etc.
                    phone_patterns = [
                        r'\d{10}',  # 10 digits
                        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
                        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # International
                        r'\d{3,}',  # Any sequence of 3+ digits
                    ]
                    
                    for pattern in phone_patterns:
                        matches = re.findall(pattern, section_text)
                        for match in matches:
                            # Clean up the phone number
                            phone_value = match.strip()
                            # Skip if it's too short or looks like a year
                            if len(phone_value.replace('-', '').replace('.', '').replace(' ', '')) < 7:
                                continue
                            if phone_value.startswith('20') or phone_value.startswith('19'):
                                continue
                            
                            # Extract label (Mobile, Work, etc.)
                            label = None
                            if "(" in section_text and ")" in section_text:
                                label_match = re.search(r'\(([^)]+)\)', section_text)
                                if label_match:
                                    potential_label = label_match.group(1)
                                    # Check if it's actually a label and not part of phone number
                                    if not re.match(r'^\d+$', potential_label):
                                        label = potential_label
                            
                            # Avoid duplicates
                            if not any(c.type == "phone" and c.value == phone_value for c in contacts):
                                contacts.append(Contact(type="phone", value=phone_value, label=label))
                                logger.debug(f"Found phone: {phone_value}")
                                break  # Found a phone in this section, move to next
                        
                        if contacts and contacts[-1].type == "phone":
                            break  # Found a phone, don't try other patterns
                            
                except Exception as e:
                    logger.debug(f"Error extracting phone: {e}")

        except Exception as e:
            logger.warning(f"Error getting contacts: {e}")
            import traceback
            logger.debug(traceback.format_exc())

        return contacts
    
    def _map_contact_heading_to_type(self, heading: str) -> Optional[str]:
        """Map contact section heading to contact type (phone and email only)."""
        heading = heading.lower()
        if "email" in heading:
            return "email"
        elif "phone" in heading:
            return "phone"
        return None

