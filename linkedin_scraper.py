"""
LinkedIn Scraper + Groq RAG — WITH SELENIUM
================================================
Strategy:
  1. Search Google/DuckDuckGo for the LinkedIn profile URL
  2. Use Selenium to fetch the full LinkedIn page content
  3. Extract all text from the page
  4. Feed raw text into Groq (llama-3.1-8b-instant) for structured extraction
  5. Output clean JSON with name, experience, education, skills

Requires: pip install groq requests beautifulsoup4 python-dotenv selenium

Usage:
  python linkedin_scraper.py
  (Edit the 'name' variable at the top of the file)
"""

import os, re, json, time, logging
from dataclasses import dataclass, field
from typing import Optional

import requests
from bs4 import BeautifulSoup
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    if __name__ == "__main__":
        print("⚠️  Selenium not installed. Install with: pip install selenium")

# ── Config ────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_groq_api_key_here")
GROQ_MODEL   = "llama-3.1-8b-instant"   # free tier, fast
MAX_TOKENS   = 4096
CHUNK_SIZE   = 6000

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
}


# ── Data model ────────────────────────────────────────────────────────────────
@dataclass
class LinkedInProfile:
    query: str
    name: str = ""
    headline: str = ""
    location: str = ""
    about: str = ""
    experience: list = field(default_factory=list)
    education:  list = field(default_factory=list)
    skills:     list = field(default_factory=list)
    certifications: list = field(default_factory=list)
    source_url: str = ""
    error: Optional[str] = None

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if k != "error"}


# ── Selenium scraper ───────────────────────────────────────────────────────────
class SeleniumScraper:
    """
    Uses Selenium to fetch full LinkedIn page content.
    This gets the actual rendered page with all dynamic content.
    """

    def __init__(self):
        self.driver = None
        self._setup_driver()

    def _setup_driver(self):
        """Setup Chrome driver with anti-detection options."""
        if not SELENIUM_AVAILABLE:
            return
        
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in background
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"--user-agent={HEADERS['User-Agent']}")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Try to create driver (will fail if ChromeDriver not installed)
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Hide webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except Exception as e:
            log.warning(f"Selenium setup failed: {e}")
            log.warning("  Install ChromeDriver: https://chromedriver.chromium.org/")
            self.driver = None

    def get_profile_text(self, query_or_url: str) -> tuple[str, str]:
        """Returns (cleaned_text, source_url) using Selenium. Also gets Google snippets."""
        if not self.driver:
            return "", ""
        
        is_url = query_or_url.startswith("http")
        linkedin_url = query_or_url if is_url else ""
        
        all_text_parts = []
        
        # First, get Google search snippets (these often have good profile info)
        if not is_url:
            log.info("  Getting Google search snippets...")
            google_snippets = self._get_google_snippets_selenium(query_or_url)
            if google_snippets:
                all_text_parts.append(google_snippets)
                log.info(f"  Got {len(google_snippets)} chars from Google snippets")
        
        # Find LinkedIn URL if not provided (but don't fail if we can't find it)
        if not linkedin_url:
            linkedin_url = self._find_linkedin_url(query_or_url)
        
        if not linkedin_url:
            log.warning("  Could not find LinkedIn URL")
            # If we have LinkedIn snippets, use them
            if all_text_parts:
                combined = "\n\n".join(all_text_parts)
                log.info(f"  ✓ Returning {len(combined)} chars from LinkedIn search snippets")
                return combined, f"Google search for: {query_or_url}"
            
            # If no LinkedIn data, try broad Google search for professional info
            log.info("  No LinkedIn data found, searching Google broadly...")
            broad_info = self._get_broad_google_info(query_or_url)
            if broad_info:
                log.info(f"  ✓ Got {len(broad_info)} chars from Google sources")
                return broad_info, f"Google search for: {query_or_url}"
            
            return "", ""
        
        # Try to get content from LinkedIn page
        try:
            log.info(f"  Navigating to: {linkedin_url}")
            self.driver.get(linkedin_url)
            
            # Wait for page to load
            time.sleep(5)
            
            # Try to wait for main content
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                pass
            
            # Get page title and meta description (sometimes has info even on login wall)
            try:
                title = self.driver.title
                if title and "LinkedIn" not in title and len(title) > 10:
                    all_text_parts.append(f"Page Title: {title}")
            except:
                pass
            
            # Try to get meta tags
            try:
                meta_desc = self.driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
                if meta_desc:
                    desc = meta_desc.get_attribute("content")
                    if desc:
                        all_text_parts.append(f"Description: {desc}")
            except:
                pass
            
            # Multiple scrolls to trigger lazy loading
            for i in range(5):
                scroll_position = (i + 1) * 500
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(1.5)
            
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Scroll back up slowly
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Try to get text from body element (visible text)
            visible_text = ""
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                visible_text = body.text
                
                # Also try to get text from main content areas
                try:
                    selectors = [
                        "main",
                        "[role='main']",
                        ".core-rail",
                        ".profile",
                        ".pv-profile-section",
                        "article",
                        ".scaffold-layout__main",
                        ".ph5"
                    ]
                    for selector in selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                element_text = element.text
                                if element_text and len(element_text) > len(visible_text):
                                    visible_text = element_text
                        except:
                            continue
                except:
                    pass
                
            except Exception as e:
                log.warning(f"  Could not get visible text: {e}")
            
            # Get page source and extract all text
            page_source = self.driver.page_source
            html_text = self._clean(page_source)
            
            # Add LinkedIn page content to parts
            if visible_text and len(visible_text.strip()) > 50:
                all_text_parts.append(f"LinkedIn Page Content:\n{visible_text}")
            elif html_text and len(html_text.strip()) > 50:
                all_text_parts.append(f"LinkedIn Page Content:\n{html_text}")
            
        except Exception as e:
            log.warning(f"  Selenium error: {e}")
        
        # Combine all text parts
        combined_text = "\n\n".join(all_text_parts)
        
        if combined_text and len(combined_text.strip()) > 50:
            log.info(f"  ✓ Got {len(combined_text)} chars total (combined sources)")
            return combined_text, linkedin_url
        elif combined_text:
            log.warning(f"  Got minimal content ({len(combined_text)} chars), but will try extraction")
            return combined_text, linkedin_url
        else:
            return "", linkedin_url
    
    def _get_google_snippets_selenium(self, query: str) -> str:
        """Get Google search snippets using Selenium - focused on LinkedIn."""
        try:
            # Try multiple search queries for LinkedIn
            search_queries = [
                f'"{query}" linkedin',
                f"site:linkedin.com/in {query}",
                f"{query} linkedin profile"
            ]
            
            all_snippets = []
            
            for search_q in search_queries:
                try:
                    search_url = f"https://www.google.com/search?q={requests.utils.quote(search_q)}&num=10"
                    log.info(f"    Searching: {search_q}")
                    
                    self.driver.get(search_url)
                    time.sleep(3)
                    
                    # Get page source and parse with BeautifulSoup (more reliable)
                    page_source = self.driver.page_source
                    soup = BeautifulSoup(page_source, "html.parser")
                    
                    # Extract from various Google result elements
                    for elem in soup.find_all(["h3", "span", "div", "p"]):
                        text = elem.get_text(strip=True)
                        # Look for text that mentions the query or LinkedIn
                        if (query.lower() in text.lower() or "linkedin" in text.lower()) and len(text) > 30:
                            if text not in all_snippets:
                                all_snippets.append(text)
                    
                    # Also try Selenium element extraction
                    try:
                        result_selectors = [
                        ".g .VwiC3b",  # Snippet text
                        ".g .s",       # Alternative snippet
                        ".g .IsZvec",  # Another snippet variant
                        ".g h3",       # Titles
                    ]
                    
                        for selector in result_selectors:
                            try:
                                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                for elem in elements[:10]:
                                    text = elem.text.strip()
                                    if text and len(text) > 20:
                                        if text not in all_snippets:
                                            all_snippets.append(text)
                            except:
                                continue
                    except:
                        pass
                    
                except Exception as e:
                    log.warning(f"    Search query failed: {e}")
                    continue
            
            result = "\n".join(all_snippets[:30])  # Get up to 30 snippets
            return result
            
        except Exception as e:
            log.warning(f"  Google snippets search failed: {e}")
            return ""
    
    def _get_broad_google_info(self, query: str) -> str:
        """Get comprehensive information from Google search - not just LinkedIn."""
        """Searches for person across multiple sources: news, company sites, directories, etc."""
        if not self.driver:
            return ""
        
        try:
            log.info("  Gathering information from Google sources...")
            all_info = []
            
            # Multiple search strategies to find professional information
            search_queries = [
                f'"{query}"',  # Exact name search
                f"{query} professional",  # Professional info
                f"{query} biography",  # Biography
                f"{query} CEO OR director OR manager",  # Job titles
                f"{query} company OR organization",  # Company info
            ]
            
            for search_q in search_queries:
                try:
                    search_url = f"https://www.google.com/search?q={requests.utils.quote(search_q)}&num=10"
                    log.info(f"    Searching: {search_q}")
                    
                    self.driver.get(search_url)
                    time.sleep(3)
                    
                    # Wait for results
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                    except TimeoutException:
                        pass
                    
                    page_source = self.driver.page_source
                    soup = BeautifulSoup(page_source, "html.parser")
                    
                    # Extract knowledge panel (if available)
                    try:
                        knowledge_panel = soup.find("div", class_=re.compile(r"knowledge|kp-|kno-"))
                        if knowledge_panel:
                            kp_text = knowledge_panel.get_text(separator="\n", strip=True)
                            if kp_text and len(kp_text) > 50:
                                all_info.append(f"Knowledge Panel:\n{kp_text}")
                                log.info(f"    Found knowledge panel ({len(kp_text)} chars)")
                    except:
                        pass
                    
                    # Extract search result snippets
                    snippets = []
                    
                    # Try different selectors for Google results
                    result_selectors = [
                        ".g .VwiC3b",  # Main snippet
                        ".g .s",       # Alternative snippet
                        ".g .IsZvec",  # Another variant
                        ".g h3",       # Titles
                        ".g .LC20lb",  # Result titles
                    ]
                    
                    for selector in result_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for elem in elements[:15]:
                                text = elem.text.strip()
                                if text and len(text) > 30:
                                    # Check if it's relevant to the person
                                    if query.lower() in text.lower() or any(word in text.lower() for word in ["ceo", "director", "manager", "engineer", "founder", "president", "executive"]):
                                        if text not in snippets:
                                            snippets.append(text)
                        except:
                            continue
                    
                    # Also extract from HTML using BeautifulSoup
                    for elem in soup.find_all(["h3", "span", "div", "p"]):
                        text = elem.get_text(strip=True)
                        if text and len(text) > 40:
                            # Check relevance
                            query_words = query.lower().split()
                            if any(word in text.lower() for word in query_words) or any(word in text.lower() for word in ["professional", "career", "experience", "company", "university", "education"]):
                                if text not in snippets:
                                    snippets.append(text)
                    
                    if snippets:
                        all_info.append(f"Search Results for '{search_q}':\n" + "\n".join(snippets[:20]))
                        log.info(f"    Found {len(snippets)} relevant snippets")
                    
                    time.sleep(2)  # Be respectful with requests
                    
                except Exception as e:
                    log.warning(f"    Search query '{search_q}' failed: {e}")
                    continue
            
            combined = "\n\n".join(all_info)
            if combined:
                log.info(f"  ✓ Got {len(combined)} chars from Google sources")
            return combined
            
        except Exception as e:
            log.warning(f"  Broad Google search failed: {e}")
            return ""

    def _find_linkedin_url(self, query: str) -> str:
        """Search Google for LinkedIn profile URL - get the first/latest profile."""
        if not self.driver:
            return ""
        
        try:
            # Try multiple search strategies
            search_queries = [
                f"site:linkedin.com/in {query}",
                f'"{query}" linkedin',
                f"{query} linkedin profile"
            ]
            
            for search_q in search_queries:
                try:
                    search_url = f"https://www.google.com/search?q={requests.utils.quote(search_q)}&num=10"
                    log.info(f"  Searching: {search_q}")
                    
                    self.driver.get(search_url)
                    time.sleep(3)
                    
                    # Wait for results to load
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                    except TimeoutException:
                        pass
                    
                    # Get all links from the page
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    linkedin_urls = []
                    
                    for link in links:
                        try:
                            href = link.get_attribute("href") or ""
                            # Look for LinkedIn profile URLs
                            m = re.search(r"linkedin\.com/in/([\w\-]+)", href, re.IGNORECASE)
                            if m:
                                found = f"https://www.linkedin.com/in/{m.group(1)}"
                                # Avoid duplicates
                                if found not in linkedin_urls:
                                    linkedin_urls.append(found)
                        except:
                            continue
                    
                    if linkedin_urls:
                        # Return the first (most relevant) LinkedIn URL
                        found_url = linkedin_urls[0]
                        log.info(f"  Found LinkedIn URL: {found_url}")
                        return found_url
                    
                except Exception as e:
                    log.warning(f"  Search query failed: {e}")
                    continue
            
            # If no LinkedIn URL found in search results, try extracting from page source
            try:
                page_source = self.driver.page_source
                # Search for LinkedIn URLs in the page source
                matches = re.findall(r'https?://(?:www\.)?linkedin\.com/in/[\w\-]+', page_source, re.IGNORECASE)
                if matches:
                    found_url = matches[0]
                    log.info(f"  Found LinkedIn URL in page source: {found_url}")
                    return found_url
            except:
                pass
                
        except Exception as e:
            log.warning(f"  LinkedIn URL search failed: {e}")
        
        return ""

    def _clean(self, html: str) -> str:
        """Extract clean text from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove unwanted elements
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "meta", "link", "noscript", "iframe", "svg",
                         "img", "button", "form"]):
            tag.decompose()
        
        # Get all text
        text = soup.get_text(separator="\n")
        
        # Clean up whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        
        return text.strip()

    def close(self):
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


# ── No-auth scraper (fallback) ────────────────────────────────────────────────
class NoAuthScraper:
    """
    Fallback scraper using requests (no Selenium).
    Tries Google Cache, DuckDuckGo, Google, Bing, then direct LinkedIn.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def get_profile_text(self, query_or_url: str) -> tuple[str, str]:
        """Returns (cleaned_text, source_url). Tries strategies until one works."""
        is_url = query_or_url.startswith("http")
        linkedin_url = query_or_url if is_url else ""

        def find_url():
            nonlocal linkedin_url
            if not linkedin_url:
                linkedin_url = self._find_linkedin_url(query_or_url)
            return linkedin_url

        strategies = [
            ("Google Cache",     lambda: self._google_cache(find_url())),
            ("DuckDuckGo",       lambda: self._duckduckgo(query_or_url)),
            ("Google Snippets",  lambda: self._google_snippets(query_or_url)),
            ("Bing Snippets",    lambda: self._bing_snippets(query_or_url)),
            ("Direct LinkedIn",  lambda: self._direct(find_url())),
        ]

        for name, fn in strategies:
            log.info(f"Trying: {name}")
            try:
                text, url = fn()
                if text and len(text.strip()) > 80:
                    log.info(f"  ✓ Got {len(text)} chars via {name}")
                    return text, url
                log.warning(f"  Too little content ({len(text) if text else 0} chars)")
            except Exception as e:
                log.warning(f"  Failed: {e}")
            time.sleep(1.5)

        return "", ""

    # ── Strategy 1: Google Cache ─────────────────────────────────────────────
    def _find_linkedin_url(self, query: str) -> str:
        search_q = f"site:linkedin.com/in {query}"
        url = f"https://www.google.com/search?q={requests.utils.quote(search_q)}&num=5"
        r = self.session.get(url, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            m = re.search(r"linkedin\.com/in/([\w\-]+)", a["href"])
            if m:
                found = f"https://www.linkedin.com/in/{m.group(1)}"
                log.info(f"  Found: {found}")
                return found
        return ""

    def _google_cache(self, linkedin_url: str) -> tuple[str, str]:
        if not linkedin_url:
            return "", ""
        cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{linkedin_url}"
        r = self.session.get(cache_url, timeout=15)
        if r.status_code == 200:
            return self._clean(r.text), cache_url
        return "", ""

    # ── Strategy 2: DuckDuckGo HTML ──────────────────────────────────────────
    def _duckduckgo(self, query: str) -> tuple[str, str]:
        q = f"linkedin {query}"
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(q)}"
        r = self.session.get(url, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")

        lines = []
        for result in soup.find_all("div", class_="result"):
            for cls in ("result__a", "result__snippet", "result__url"):
                tag = result.find(class_=cls)
                if tag:
                    lines.append(tag.get_text(strip=True))
            lines.append("---")

        return "\n".join(lines), url

    # ── Strategy 3: Google snippets ──────────────────────────────────────────
    def _google_snippets(self, query: str) -> tuple[str, str]:
        q = f"linkedin.com/in {query}"
        url = f"https://www.google.com/search?q={requests.utils.quote(q)}&num=10"
        r = self.session.get(url, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        snippets = []
        for tag in soup.find_all(["h3", "span", "div"]):
            t = tag.get_text(strip=True)
            if len(t) > 40 and "linkedin" in r.text.lower():
                snippets.append(t)
        return "\n\n".join(snippets[:20]), url

    # ── Strategy 4: Bing snippets ────────────────────────────────────────────
    def _bing_snippets(self, query: str) -> tuple[str, str]:
        q = f"site:linkedin.com/in {query}"
        url = f"https://www.bing.com/search?q={requests.utils.quote(q)}"
        r = self.session.get(url, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        snippets = []
        for li in soup.find_all("li", class_=re.compile(r"b_algo")):
            t = li.get_text(separator=" ", strip=True)
            if len(t) > 30:
                snippets.append(t)
        return "\n\n".join(snippets[:12]), url

    # ── Strategy 5: Direct LinkedIn ──────────────────────────────────────────
    def _direct(self, linkedin_url: str) -> tuple[str, str]:
        if not linkedin_url:
            return "", ""
        r = self.session.get(linkedin_url, timeout=15)
        if r.status_code == 200 and "authwall" not in r.url:
            return self._clean(r.text), linkedin_url
        return "", ""

    # ── HTML cleaner ─────────────────────────────────────────────────────────
    def _clean(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "meta", "link", "noscript", "iframe", "svg",
                         "img", "button", "form"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+",  " ",   text)
        return text.strip()


# ── Groq extractor ────────────────────────────────────────────────────────────
class GroqExtractor:

    SYSTEM = (
        "You are an expert LinkedIn profile parser. "
        "Extract ALL available professional information from ANY text, even if it's minimal or from a login page. "
        "If you see ANY name, job title, company, location, or other professional info, extract it. "
        "ALWAYS return ONLY valid JSON — no markdown fences, no explanation."
    )

    PROMPT = """Extract a LinkedIn professional profile from this raw text.
Even if the text is minimal, partial, or from a login page, extract ANY available information.

Return ONLY this JSON (use empty string "" or [] if not found):
{{
  "name": "Full name (extract from ANY mention of a person's name)",
  "headline": "Current job title and company (any job title or company mentioned)",
  "location": "City, Country (any location mentioned)",
  "about": "Bio / summary (any description or bio text)",
  "experience": [
    {{
      "title": "Job Title (any job title found)",
      "company": "Company Name (any company mentioned)",
      "duration": "Time period if mentioned",
      "years": "",
      "description": "Any job description or responsibilities",
      "location": "City if mentioned"
    }}
  ],
  "education": [
    {{
      "degree": "Degree if mentioned",
      "institution": "University/School name if mentioned",
      "years": "Years if mentioned",
      "grade": ""
    }}
  ],
  "skills": ["Any skills mentioned"],
  "certifications": [
    {{
      "name": "Certification name if mentioned",
      "issuer": "Issuer if mentioned",
      "date": "Date if mentioned"
    }}
  ]
}}

IMPORTANT: Extract ANY information you can find, even if incomplete. If you see a name like "Sundar Pichai" or "CEO" or "Google", extract it!

Raw text:
{text}"""

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def extract(self, raw_text: str, query: str) -> LinkedInProfile:
        profile = LinkedInProfile(query=query)
        chunks = self._chunk(raw_text)
        log.info(f"Sending {len(chunks)} chunk(s) to Groq")

        parts = []
        for i, chunk in enumerate(chunks):
            log.info(f"  Chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
            result = self._call(chunk)
            if result:
                parts.append(result)

        self._fill(profile, self._merge(parts))
        return profile

    def _chunk(self, text: str) -> list[str]:
        # Reduce chunk size to account for prompt overhead (roughly 500 tokens)
        # Model limit is 6000 tokens, so we want chunks around 4000-4500 chars max
        safe_chunk_size = min(CHUNK_SIZE, 4000)
        
        if len(text) <= safe_chunk_size:
            return [text]
        
        chunks, cur, cur_len = [], [], 0
        for para in text.split("\n\n"):
            para_len = len(para)
            # If a single paragraph is too large, split it by sentences
            if para_len > safe_chunk_size:
                # Save current chunk if any
                if cur:
                    chunks.append("\n\n".join(cur))
                    cur, cur_len = [], 0
                # Split large paragraph by sentences
                sentences = re.split(r'[.!?]+\s+', para)
                for sentence in sentences:
                    if cur_len + len(sentence) > safe_chunk_size and cur:
                        chunks.append("\n\n".join(cur))
                        cur, cur_len = [], 0
                    cur.append(sentence)
                    cur_len += len(sentence)
            elif cur_len + para_len > safe_chunk_size and cur:
                chunks.append("\n\n".join(cur))
                cur, cur_len = [], 0
                cur.append(para)
                cur_len = para_len
            else:
                cur.append(para)
                cur_len += para_len
        
        if cur:
            chunks.append("\n\n".join(cur))
        
        return chunks

    def _call(self, text: str) -> dict:
        try:
            resp = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM},
                    {"role": "user",   "content": self.PROMPT.format(text=text)},
                ],
                max_tokens=MAX_TOKENS,
                temperature=0.1,
            )
            return self._parse(resp.choices[0].message.content.strip())
        except Exception as e:
            log.error(f"Groq error: {e}")
            return {}

    def _parse(self, text: str) -> dict:
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$",           "", text, flags=re.MULTILINE).strip()
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return {}

    def _merge(self, results: list[dict]) -> dict:
        if not results: 
            return {}
        if len(results) == 1: 
            return self._clean_data(results[0])
        
        base = results[0].copy()
        for r in results[1:]:
            # Merge text fields - keep the longest/most complete
            for k in ("name", "headline", "location", "about"):
                r_val = r.get(k, "").strip()
                base_val = base.get(k, "").strip()
                if len(r_val) > len(base_val) and r_val:
                    base[k] = r_val
            
            # Merge lists with deduplication
            for k in ("experience", "education", "skills", "certifications"):
                base_list = base.get(k, [])
                for item in r.get(k, []):
                    if not self._is_duplicate(item, base_list, k):
                        base_list.append(item)
                base[k] = base_list
        
        # Clean the merged data
        cleaned = self._clean_data(base)
        return cleaned
    
    def _clean_data(self, data: dict) -> dict:
        """Clean and organize the extracted data professionally."""
        cleaned = {
            "query": data.get("query", ""),
            "name": self._clean_text(data.get("name", "")),
            "headline": self._clean_text(data.get("headline", "")),
            "location": self._clean_text(data.get("location", "")),
            "about": self._clean_text(data.get("about", "")),
            "experience": self._clean_experience(data.get("experience", [])),
            "education": self._clean_education(data.get("education", [])),
            "skills": self._clean_skills(data.get("skills", [])),
            "certifications": self._clean_certifications(data.get("certifications", [])),
        }
        return cleaned
    
    def _clean_text(self, text: str) -> str:
        """Clean text fields."""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove common LinkedIn boilerplate
        text = re.sub(r'750 million\+ members.*', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    def _clean_experience(self, exp_list: list) -> list:
        """Clean and organize experience entries."""
        if not exp_list:
            return []
        
        cleaned = []
        seen = set()
        
        # Invalid title/company patterns to skip
        invalid_patterns = [
            "experience", "education", "skills", "certifications",
            "linkedin", "profile", "view", "see", "more", "less",
            "sign", "login", "join", "connect", "follow"
        ]
        
        for exp in exp_list:
            if not isinstance(exp, dict):
                continue
            
            # Extract and clean fields
            title = self._clean_text(exp.get("title", ""))
            company = self._clean_text(exp.get("company", ""))
            location = self._clean_text(exp.get("location", ""))
            duration = self._clean_text(exp.get("duration", ""))
            years = self._clean_text(exp.get("years", ""))
            description = self._clean_text(exp.get("description", ""))
            
            # Skip if title/company is invalid
            title_lower = title.lower()
            company_lower = company.lower()
            
            # Skip entries with invalid patterns
            if any(pattern in title_lower for pattern in invalid_patterns):
                continue
            if any(pattern in company_lower for pattern in invalid_patterns):
                continue
            
            # Skip if title is too short or looks like a location
            if title and (len(title) < 3 or title.count(",") > 1):
                continue
            
            # Skip if company is too short
            if company and len(company) < 2:
                continue
            
            # Must have at least title or company
            if not title and not company:
                continue
            
            # Normalize title and company for deduplication (remove common variations)
            title_norm = re.sub(r'[^\w\s]', '', title.lower().strip())
            company_norm = re.sub(r'[^\w\s]', '', company.lower().strip())
            
            # Remove common suffixes/prefixes for better matching
            title_norm = re.sub(r'\b(pvt|ltd|llc|inc|corp|limited|corporation)\b', '', title_norm)
            company_norm = re.sub(r'\b(pvt|ltd|llc|inc|corp|limited|corporation)\b', '', company_norm)
            
            # Create unique key for deduplication
            key = f"{title_norm}|{company_norm}".strip()
            if key in seen or not key.strip("|"):
                continue
            seen.add(key)
            
            # Build cleaned entry (only include non-empty fields)
            entry = {}
            if title:
                entry["title"] = title
            if company:
                entry["company"] = company
            if location:
                entry["location"] = location
            if duration:
                entry["duration"] = duration
            if years:
                entry["years"] = years
            if description:
                entry["description"] = description
            
            # Only add if it has meaningful content
            if entry:
                cleaned.append(entry)
        
        # Sort by relevance (entries with more info first, then by title/company quality)
        cleaned.sort(key=lambda x: (
            bool(x.get("description")),
            bool(x.get("duration")),
            bool(x.get("years")),
            len(x.get("title", "")) > 5,  # Prefer proper titles
            len(x.get("company", "")) > 3,  # Prefer proper company names
            len(x.get("description", "")),
            len(x.get("title", "")),
        ), reverse=True)
        
        # Final deduplication pass - remove near-duplicates
        final_cleaned = []
        for entry in cleaned[:15]:
            is_duplicate = False
            title = entry.get("title", "").lower()
            company = entry.get("company", "").lower()
            
            for existing in final_cleaned:
                existing_title = existing.get("title", "").lower()
                existing_company = existing.get("company", "").lower()
                
                # Check if title and company are very similar (fuzzy match)
                if title and existing_title:
                    # If titles are very similar and companies match
                    if (title in existing_title or existing_title in title) and company == existing_company:
                        is_duplicate = True
                        # Keep the one with more information
                        if len(entry.get("description", "")) > len(existing.get("description", "")):
                            final_cleaned.remove(existing)
                            final_cleaned.append(entry)
                        break
                    # If same title and similar company
                    if title == existing_title:
                        # Normalize company names
                        comp1 = re.sub(r'[^\w\s]', '', company)
                        comp2 = re.sub(r'[^\w\s]', '', existing_company)
                        if comp1 == comp2 or (comp1 in comp2 or comp2 in comp1):
                            is_duplicate = True
                            if len(entry.get("description", "")) > len(existing.get("description", "")):
                                final_cleaned.remove(existing)
                                final_cleaned.append(entry)
                            break
            
            if not is_duplicate:
                final_cleaned.append(entry)
        
        return final_cleaned
    
    def _clean_education(self, edu_list: list) -> list:
        """Clean and organize education entries."""
        if not edu_list:
            return []
        
        cleaned = []
        seen = set()
        
        invalid_patterns = ["education", "university", "college", "school", "linkedin"]
        
        for edu in edu_list:
            if not isinstance(edu, dict):
                continue
            
            degree = self._clean_text(edu.get("degree", ""))
            institution = self._clean_text(edu.get("institution", ""))
            years = self._clean_text(edu.get("years", ""))
            grade = self._clean_text(edu.get("grade", ""))
            
            # Skip if no institution
            if not institution:
                continue
            
            institution_lower = institution.lower()
            
            # Skip if institution is too short or just generic words
            if len(institution) < 3:
                continue
            
            # Skip if institution is just generic terms
            if institution_lower in invalid_patterns:
                continue
            
            # Create unique key
            key = f"{degree}|{institution}".lower().strip()
            if key in seen or not key.strip("|"):
                continue
            seen.add(key)
            
            # Build entry (only include non-empty fields)
            entry = {}
            if institution:
                entry["institution"] = institution
            if degree:
                entry["degree"] = degree
            if years:
                entry["years"] = years
            if grade:
                entry["grade"] = grade
            
            if entry:
                cleaned.append(entry)
        
        return cleaned[:10]  # Limit to top 10
    
    def _clean_skills(self, skills_list: list) -> list:
        """Clean and organize skills."""
        if not skills_list:
            return []
        
        cleaned = []
        seen = set()
        
        for skill in skills_list:
            if isinstance(skill, str):
                skill = self._clean_text(skill)
            elif isinstance(skill, dict):
                skill = self._clean_text(skill.get("name", "") or skill.get("skill", ""))
            else:
                continue
            
            if not skill or len(skill) < 2:
                continue
            
            # Normalize skill name
            skill_lower = skill.lower().strip()
            if skill_lower not in seen:
                seen.add(skill_lower)
                cleaned.append(skill)
        
        # Sort alphabetically
        cleaned.sort(key=str.lower)
        return cleaned[:50]  # Limit to top 50
    
    def _clean_certifications(self, cert_list: list) -> list:
        """Clean and organize certifications."""
        if not cert_list:
            return []
        
        cleaned = []
        seen = set()
        
        for cert in cert_list:
            if not isinstance(cert, dict):
                continue
            
            name = self._clean_text(cert.get("name", ""))
            issuer = self._clean_text(cert.get("issuer", ""))
            date = self._clean_text(cert.get("date", ""))
            
            # Skip if no name
            if not name:
                continue
            
            key = f"{name}|{issuer}".lower()
            if key in seen:
                continue
            seen.add(key)
            
            entry = {
                "name": name,
                "issuer": issuer,
                "date": date
            }
            
            cleaned.append(entry)
        
        return cleaned[:20]  # Limit to top 20
    
    def _is_duplicate(self, item: dict, existing_list: list, category: str) -> bool:
        """Check if an item is a duplicate."""
        if category == "experience":
            item_key = f"{item.get('title', '')}|{item.get('company', '')}".lower()
            for existing in existing_list:
                existing_key = f"{existing.get('title', '')}|{existing.get('company', '')}".lower()
                if item_key == existing_key and item_key.strip("|"):
                    return True
        elif category == "education":
            item_key = f"{item.get('degree', '')}|{item.get('institution', '')}".lower()
            for existing in existing_list:
                existing_key = f"{existing.get('degree', '')}|{existing.get('institution', '')}".lower()
                if item_key == existing_key and item_key.strip("|"):
                    return True
        elif category == "skills":
            item_skill = str(item).lower() if isinstance(item, str) else str(item.get("name", "")).lower()
            for existing in existing_list:
                existing_skill = str(existing).lower() if isinstance(existing, str) else str(existing.get("name", "")).lower()
                if item_skill == existing_skill:
                    return True
        elif category == "certifications":
            item_key = f"{item.get('name', '')}|{item.get('issuer', '')}".lower()
            for existing in existing_list:
                existing_key = f"{existing.get('name', '')}|{existing.get('issuer', '')}".lower()
                if item_key == existing_key and item_key.strip("|"):
                    return True
        
        return False

    def _fill(self, p: LinkedInProfile, d: dict):
        p.name           = d.get("name", "")
        p.headline       = d.get("headline", "")
        p.location       = d.get("location", "")
        p.about          = d.get("about", "")
        p.experience     = d.get("experience", [])
        p.education      = d.get("education", [])
        p.skills         = d.get("skills", [])
        p.certifications = d.get("certifications", [])


# ── Pipeline ──────────────────────────────────────────────────────────────────
def run(query: str, output_file: str = "profile_output.json"):
    print(f"\n{'='*60}")
    print(f"  LinkedIn RAG Pipeline  |  Selenium + Groq")
    print(f"  Query: {query}")
    print(f"{'='*60}\n")

    # 1. Scrape with Selenium (preferred) or fallback to requests
    scraper = None
    raw_text = ""
    source_url = ""
    
    # Try Selenium first
    if SELENIUM_AVAILABLE:
        try:
            log.info("Trying: Selenium (full page extraction)")
            selenium_scraper = SeleniumScraper()
            if selenium_scraper.driver:
                raw_text, source_url = selenium_scraper.get_profile_text(query)
                selenium_scraper.close()
        except Exception as e:
            log.warning(f"Selenium failed: {e}, falling back to requests")
    
    # Fallback to requests-based scraper
    if not raw_text:
        log.info("Using fallback scraper (requests)")
    scraper = NoAuthScraper()
    raw_text, source_url = scraper.get_profile_text(query)

    if not raw_text:
        print("\n✗ No data found from LinkedIn or Google. Tips:")
        print("  • Add more context: \"John Smith Google Senior Engineer\"")
        print("  • Try their full name + company + city")
        print("  • Paste LinkedIn URL directly")
        print("  • Make sure Selenium/ChromeDriver is installed for best results")
        return None
    
    # Check if we got minimal data and try to enhance with Google
    if len(raw_text.strip()) < 500:
        log.info("Minimal data found, trying to enhance with Google sources...")
        if SELENIUM_AVAILABLE:
            try:
                selenium_scraper = SeleniumScraper()
                if selenium_scraper.driver:
                    # Extract name from query for Google search
                    search_query = query if not query.startswith("http") else query.split("/")[-1]
                    google_info = selenium_scraper._get_broad_google_info(search_query)
                    if google_info and len(google_info) > len(raw_text):
                        log.info(f"Enhanced with {len(google_info)} chars from Google")
                        raw_text = f"{raw_text}\n\n--- Additional Information from Google ---\n\n{google_info}"
                        source_url = f"{source_url} + Google sources"
                    selenium_scraper.close()
            except Exception as e:
                log.warning(f"Failed to enhance with Google: {e}")

    print(f"\n✓ Got {len(raw_text)} chars from: {source_url}\n")

    # 2. Extract with Groq
    extractor = GroqExtractor()
    profile = extractor.extract(raw_text, query=query)
    profile.source_url = source_url

    # 3. Output
    result = profile.to_dict()
    print("\n── Extracted Profile ──────────────────────────────────")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("───────────────────────────────────────────────────────\n")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved → {output_file}")
    return profile


def run_batch(queries: list[str], output_dir: str = "profiles"):
    """Process a list of names/URLs."""
    os.makedirs(output_dir, exist_ok=True)
    profiles = []
    for i, q in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}]")
        safe = re.sub(r"[^\w]", "_", q.split("/")[-1])[:40] or f"profile_{i}"
        profile = run(q, output_file=os.path.join(output_dir, f"{safe}.json"))
        profiles.append(profile)
        time.sleep(2)
    print(f"\n✓ Done — {len(profiles)} profiles in ./{output_dir}/")
    return profiles


# ── Config: Add name here ─────────────────────────────────────────────────────
name = "Bhaskar Rao Allu"  # Add the name/query here

# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not name:
        print(__doc__)
        print("Examples:")
        print('  Set name = "Satya Nadella Microsoft CEO"')
        print('  Set name = "https://www.linkedin.com/in/satyanadella"')
        exit(1)

    run(name)