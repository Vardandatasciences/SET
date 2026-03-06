"""
Web Scraper Service
Uses Playwright to scrape content from any website
"""

import os
import sys
import asyncio
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse


class WebScraperService:
    """
    Service to scrape content from any website using Playwright
    Similar to LinkedIn scraper but for generic websites
    """
    
    def __init__(self):
        """Initialize web scraper service"""
        # Add linkedin_scraper to path to use BrowserManager
        linkedin_scraper_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'linkedin_scraper'
        )
        if linkedin_scraper_path not in sys.path:
            sys.path.insert(0, linkedin_scraper_path)
        
        try:
            from linkedin_scraper import BrowserManager
            self.BrowserManager = BrowserManager
            self.playwright_available = True
            print("✅ Web Scraper Service initialized (Playwright available)")
        except ImportError as e:
            print(f"⚠️  Web Scraper Service: Playwright not available: {e}")
            self.playwright_available = False
    
    async def scrape_url(self, url: str, max_length: int = 10000) -> Optional[Dict[str, Any]]:
        """
        Scrape content from a URL
        
        Args:
            url: URL to scrape
            max_length: Maximum length of content to extract (characters)
        
        Returns:
            Dictionary with 'url', 'title', 'content', 'metadata' or None if failed
        """
        if not self.playwright_available:
            print(f"❌ Cannot scrape {url}: Playwright not available")
            return None
        
        if not url or not url.startswith(('http://', 'https://')):
            print(f"⚠️  Invalid URL: {url}")
            return None
        
        print(f"\n🌐 Scraping URL: {url}")
        
        try:
            async with self.BrowserManager(headless=True) as browser:
                page = browser.page
                
                # Navigate to URL
                print(f"   Navigating to {url}...")
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)  # Wait for dynamic content
                
                # Extract title
                title = await page.title()
                print(f"   Title: {title[:100]}...")
                
                # Extract main content
                # Try different selectors for main content
                content_selectors = [
                    "article",
                    "main",
                    "[role='main']",
                    ".content",
                    ".main-content",
                    "#content",
                    "#main",
                    "body"
                ]
                
                content = ""
                for selector in content_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            content = await element.inner_text()
                            if len(content) > 100:  # Found substantial content
                                print(f"   Found content using selector: {selector}")
                                break
                    except Exception:
                        continue
                
                # If no content found, get body text
                if not content or len(content) < 100:
                    body = await page.query_selector("body")
                    if body:
                        content = await body.inner_text()
                
                # Clean and truncate content
                content = self._clean_text(content)
                if len(content) > max_length:
                    content = content[:max_length] + "... [truncated]"
                
                # Extract metadata
                metadata = await self._extract_metadata(page)
                
                # Extract links
                links = await self._extract_links(page, url)
                
                result = {
                    "url": url,
                    "title": title,
                    "content": content,
                    "content_length": len(content),
                    "metadata": metadata,
                    "links": links[:10]  # Limit to 10 links
                }
                
                print(f"   ✅ Scraped successfully: {len(content)} characters")
                return result
                
        except Exception as e:
            print(f"   ❌ Error scraping {url}: {e}")
            return None
    
    async def scrape_multiple_urls(
        self, 
        urls: List[str], 
        max_length_per_url: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs
        
        Args:
            urls: List of URLs to scrape
            max_length_per_url: Maximum content length per URL
        
        Returns:
            List of scraped content dictionaries
        """
        results = []
        
        print(f"\n🌐 Scraping {len(urls)} URLs...")
        
        for idx, url in enumerate(urls, 1):
            print(f"\n[{idx}/{len(urls)}] Processing: {url}")
            result = await self.scrape_url(url, max_length_per_url)
            if result:
                results.append(result)
            else:
                print(f"   ⚠️  Skipped (failed to scrape)")
            
            # Add delay between requests to avoid rate limiting
            if idx < len(urls):
                await asyncio.sleep(1)
        
        print(f"\n✅ Scraped {len(results)}/{len(urls)} URLs successfully")
        return results
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    async def _extract_metadata(self, page) -> Dict[str, Any]:
        """Extract metadata from page"""
        metadata = {}
        
        try:
            # Extract meta description
            meta_desc = await page.query_selector('meta[name="description"]')
            if meta_desc:
                metadata["description"] = await meta_desc.get_attribute("content")
            
            # Extract meta keywords
            meta_keywords = await page.query_selector('meta[name="keywords"]')
            if meta_keywords:
                metadata["keywords"] = await meta_keywords.get_attribute("content")
            
            # Extract Open Graph title
            og_title = await page.query_selector('meta[property="og:title"]')
            if og_title:
                metadata["og_title"] = await og_title.get_attribute("content")
            
            # Extract Open Graph description
            og_desc = await page.query_selector('meta[property="og:description"]')
            if og_desc:
                metadata["og_description"] = await og_desc.get_attribute("content")
            
        except Exception as e:
            print(f"   Warning: Failed to extract metadata: {e}")
        
        return metadata
    
    async def _extract_links(self, page, base_url: str) -> List[str]:
        """Extract relevant links from page"""
        links = []
        
        try:
            # Get all links
            link_elements = await page.query_selector_all("a[href]")
            
            for element in link_elements:
                try:
                    href = await element.get_attribute("href")
                    if href:
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            parsed = urlparse(base_url)
                            href = f"{parsed.scheme}://{parsed.netloc}{href}"
                        elif not href.startswith(('http://', 'https://')):
                            continue
                        
                        # Filter out common non-content links
                        if any(skip in href.lower() for skip in [
                            'javascript:', 'mailto:', 'tel:', '#', 
                            'facebook.com', 'twitter.com', 'linkedin.com',
                            'instagram.com', 'youtube.com'
                        ]):
                            continue
                        
                        links.append(href)
                except Exception:
                    continue
            
            # Remove duplicates
            links = list(dict.fromkeys(links))
            
        except Exception as e:
            print(f"   Warning: Failed to extract links: {e}")
        
        return links
