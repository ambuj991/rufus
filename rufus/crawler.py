import requests
import time
import json
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from .utils import logger, RufusError


class Crawler:
    """
    Base crawler class responsible for fetching web pages.
    """
    
    def __init__(
        self,
        user_agent: Optional[str] = None,
        respect_robots: bool = True,
        rate_limit: float = 1.0
    ):
        """
        Initialize the crawler.
        
        Args:
            user_agent: Custom user agent for web requests
            respect_robots: Whether to respect robots.txt rules
            rate_limit: Time to wait between requests in seconds
        """
        self.session = requests.Session()
        self.user_agent = user_agent or 'Rufus Web Crawler (https://github.com/yourusername/rufus)'
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br'
        })
        self.respect_robots = respect_robots
        self.rate_limit = rate_limit
        self.robot_parsers = {}
        self.last_request_time = {}
    
    def can_fetch(self, url: str) -> bool:
        """
        Check if we're allowed to fetch a URL according to robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            Boolean indicating if we can fetch the URL
        """
        if not self.respect_robots:
            return True
        
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if base_url not in self.robot_parsers:
            # Initialize the parser for this domain
            parser = RobotFileParser()
            parser.set_url(f"{base_url}/robots.txt")
            try:
                parser.read()
            except Exception as e:
                logger.warning(f"Failed to read robots.txt for {base_url}: {str(e)}")
                # If we can't read robots.txt, assume we can fetch
                return True
            self.robot_parsers[base_url] = parser
        
        return self.robot_parsers[base_url].can_fetch(self.user_agent, url)
    
    def respect_rate_limits(self, url: str) -> None:
        """
        Ensure we don't make requests too quickly to the same domain.
        
        Args:
            url: URL being requested
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        current_time = time.time()
        if domain in self.last_request_time:
            elapsed = current_time - self.last_request_time[domain]
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed)
        
        self.last_request_time[domain] = time.time()
    
    def fetch_page(self, url: str) -> Dict[str, Any]:
        """
        Fetch a page and return its content.
        
        Args:
            url: The URL to fetch
            
        Returns:
            A dictionary with the page content and metadata
        """
        logger.debug(f"Fetching page: {url}")
        
        if not self.can_fetch(url):
            raise RufusError(f"Not allowed to fetch {url} according to robots.txt")
        
        self.respect_rate_limits(url)
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Get content type from headers
            content_type = response.headers.get('Content-Type', '').lower()
            
            # Check if the content is HTML
            if 'text/html' not in content_type:
                logger.warning(f"URL {url} returned non-HTML content: {content_type}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Extract links
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(url, href)
                link_text = a_tag.get_text(strip=True)
                links.append({
                    'url': full_url,
                    'text': link_text or "(No link text)"
                })
            
            # Extract metadata
            title = soup.title.string if soup.title else ""
            meta_description = ""
            meta_tag = soup.find('meta', attrs={'name': 'description'})
            if meta_tag:
                meta_description = meta_tag.get('content', '')
            
            # Extract structured data if available
            structured_data = {}
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    structured_data = json.loads(script.string)
                    break  # Just take the first one for simplicity
                except json.JSONDecodeError:
                    pass
            
            return {
                'url': url,
                'title': title,
                'meta_description': meta_description,
                'text': text_content,
                'html': str(soup),
                'links': links,
                'structured_data': structured_data
            }
        except requests.RequestException as e:
            raise RufusError(f"Failed to fetch {url}: {str(e)}")
        except Exception as e:
            raise RufusError(f"Error processing {url}: {str(e)}")


class DynamicCrawler(Crawler):
    """
    Dynamic crawler that uses a headless browser to render JavaScript.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the dynamic crawler with Playwright."""
        super().__init__(*args, **kwargs)
        self.playwright = None
        self.browser = None
    
    def __enter__(self):
        """Set up Playwright when entering context."""
        try:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=True)
            return self
        except ImportError:
            raise RufusError("Playwright is required for dynamic crawling. Install with 'pip install playwright' and 'playwright install'")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up Playwright resources."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def fetch_page(
        self, 
        url: str, 
        wait_for_selector: Optional[str] = None,
        wait_time: int = 5000
    ) -> Dict[str, Any]:
        """
        Fetch a page with dynamic content using Playwright.
        
        Args:
            url: The URL to fetch
            wait_for_selector: CSS selector to wait for before extracting content
            wait_time: Time to wait in ms if no selector is provided
            
        Returns:
            A dictionary with the page content and metadata
        """
        logger.debug(f"Fetching dynamic page: {url}")
        
        if not self.can_fetch(url):
            raise RufusError(f"Not allowed to fetch {url} according to robots.txt")
        
        self.respect_rate_limits(url)
        
        if not self.browser:
            raise RufusError("Dynamic crawler not initialized. Use with 'with' statement.")
        
        page = self.browser.new_page()
        try:
            # Set user agent
            page.set_extra_http_headers({
                'User-Agent': self.user_agent
            })
            
            # Go to the page
            response = page.goto(url, wait_until='networkidle', timeout=60000)
            if not response:
                raise RufusError(f"Failed to load {url}")
            
            # Wait for content to load
            if wait_for_selector:
                try:
                    page.wait_for_selector(wait_for_selector, timeout=wait_time)
                except Exception as e:
                    logger.warning(f"Selector '{wait_for_selector}' not found on {url}: {str(e)}")
            else:
                page.wait_for_timeout(wait_time)
            
            # Extract content
            content = page.content()
            title = page.title()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Extract links
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(url, href)
                link_text = a_tag.get_text(strip=True)
                links.append({
                    'url': full_url,
                    'text': link_text or "(No link text)"
                })
            
            # Extract metadata
            meta_description = ""
            meta_tag = soup.find('meta', attrs={'name': 'description'})
            if meta_tag:
                meta_description = meta_tag.get('content', '')
            
            # Extract structured data
            structured_data = {}
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    structured_data = json.loads(script.string)
                    break  # Just take the first one for simplicity
                except json.JSONDecodeError:
                    pass
            
            return {
                'url': url,
                'title': title,
                'meta_description': meta_description,
                'text': text_content,
                'html': content,
                'links': links,
                'structured_data': structured_data
            }
        finally:
            page.close()



class AuthenticatedCrawler(Crawler):
    """
    Crawler with support for authentication.
    """
    
    def __init__(
        self,
        auth_type: str = "basic",  # "basic", "form", "oauth", "custom"
        auth_credentials: Dict[str, str] = None,
        login_url: str = None,
        form_selectors: Dict[str, str] = None,
        auth_headers: Dict[str, str] = None,
        cookies: Dict[str, str] = None,
        *args, **kwargs
    ):
        """Initialize the authenticated crawler."""
        super().__init__(*args, **kwargs)
        self.auth_type = auth_type
        self.auth_credentials = auth_credentials or {}
        self.login_url = login_url
        self.form_selectors = form_selectors or {}
        self.auth_headers = auth_headers or {}
        
        # Add cookies if provided
        if cookies:
            cookie_jar = requests.cookies.RequestsCookieJar()
            for name, value in cookies.items():
                cookie_jar.set(name, value)
            self.session.cookies.update(cookie_jar)
        
        # Add headers if provided
        if auth_headers:
            self.session.headers.update(auth_headers)
        
        # Handle basic auth
        if auth_type == "basic" and "username" in self.auth_credentials and "password" in self.auth_credentials:
            self.session.auth = (self.auth_credentials["username"], self.auth_credentials["password"])
        
        # Initialize authentication
        if auth_type == "form" and login_url:
            self._authenticate_form()
    
    def _authenticate_form(self):
        """Handle form-based authentication."""
        try:
            # Get the login page
            response = self.session.get(self.login_url, timeout=30)
            response.raise_for_status()
            
            # Prepare form data
            form_data = {}
            for field, value in self.auth_credentials.items():
                form_data[field] = value
            
            # Submit the login form
            login_response = self.session.post(
                self.login_url,
                data=form_data,
                headers={"Referer": self.login_url},
                allow_redirects=True,
                timeout=30
            )
            login_response.raise_for_status()
            
            # Check if login was successful
            if any(text in login_response.text.lower() for text in ["incorrect", "failed", "invalid password", "login error"]):
                raise RufusError("Form authentication failed. Check credentials.")
            
            logger.info("Form authentication successful")
        except requests.RequestException as e:
            raise RufusError(f"Authentication error: {str(e)}")
