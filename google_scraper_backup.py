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
            log.warning("  Could not find LinkedIn URL, using search snippets only")
            # Return Google snippets if we have them
            if all_text_parts:
                combined = "\n\n".join(all_text_parts)
                log.info(f"  ✓ Returning {len(combined)} chars from search snippets")
                return combined, f"Google search for: {query_or_url}"
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
        """Get Google search snippets using Selenium."""
        try:
            # Try multiple search queries
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
                    # Google search result snippets
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
        if not results: return {}
        if len(results) == 1: return results[0]
        base = results[0].copy()
        for r in results[1:]:
            for k in ("name", "headline", "location", "about"):
                if len(r.get(k, "")) > len(base.get(k, "")):
                    base[k] = r[k]
            for k in ("experience", "education", "skills", "certifications"):
                seen = {json.dumps(x, sort_keys=True) for x in base.get(k, [])}
                for item in r.get(k, []):
                    s = json.dumps(item, sort_keys=True)
                    if s not in seen:
                        base.setdefault(k, []).append(item)
                        seen.add(s)
        return base

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
def process_query(query: str) -> dict:
    """
    Core pipeline logic extracted for reuse.

    Given a name or LinkedIn URL, it:
      1) Scrapes raw text (Selenium preferred, then requests fallback)
      2) Sends text to Groq for structured extraction
      3) Returns a plain dict that is easy to use in a UI / API
    """
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
        # Return a structured error that a frontend / API can handle
        return {
            "query": query,
            "error": (
                "No profile data found. Try adding more context like company/city "
                "or paste a direct LinkedIn profile URL."
            ),
        }

    log.info(f"✓ Got {len(raw_text)} chars from: {source_url}")

    # 2. Extract with Groq
    extractor = GroqExtractor()
    profile = extractor.extract(raw_text, query=query)
    profile.source_url = source_url

    # 3. Return as plain dict (including source_url)
    result = profile.to_dict()
    result["source_url"] = profile.source_url
    result["query"] = query
    return result


def run(query: str, output_file: str = "profile_output.json"):
    """
    CLI-friendly wrapper around process_query.
    Still prints to console and saves JSON to disk.
    """
    print(f"\n{'='*60}")
    print(f"  LinkedIn RAG Pipeline  |  Selenium + Groq")
    print(f"  Query: {query}")
    print(f"{'='*60}\n")

    result = process_query(query)

    if not result or result.get("error"):
        print("\n✗ No data found. Tips:")
        print("  • Add more context: \"John Smith Google Senior Engineer\"")
        print("  • Try their full name + company + city")
        print("  • Paste LinkedIn URL directly")
        print("  • Make sure Selenium/ChromeDriver is installed for best results")
        if result and result.get("error"):
            print(f"\nDetails: {result['error']}")
        return None

    print(f"\n✓ Got profile from: {result.get('source_url', '')}\n")

    print("\n── Extracted Profile ──────────────────────────────────")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("───────────────────────────────────────────────────────\n")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved → {output_file}")
    return result


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
name = "Muni syam putthuru"  # Add the name/query here

# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not name:
        print(__doc__)
        print("Examples:")
        print('  Set name = "Satya Nadella Microsoft CEO"')
        print('  Set name = "https://www.linkedin.com/in/satyanadella"')
        exit(1)

    run(name)