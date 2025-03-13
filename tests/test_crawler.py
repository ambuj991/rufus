import pytest
import requests
from unittest.mock import MagicMock, patch
from urllib.robotparser import RobotFileParser

from rufus.crawler import Crawler, DynamicCrawler
from rufus.utils import RufusError


@pytest.fixture
def crawler():
    """Create a crawler instance for testing."""
    return Crawler(
        user_agent="Test User Agent",
        respect_robots=True,
        rate_limit=0.01  # Fast for testing
    )


@pytest.fixture
def mock_session():
    """Mock requests session for testing."""
    mock = MagicMock()
    
    # Mock response
    response = MagicMock()
    response.text = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
            <script type="application/ld+json">{"@type": "WebPage", "name": "Test"}</script>
        </head>
        <body>
            <h1>Test Content</h1>
            <p>This is a test paragraph.</p>
            <a href="/page1">Page 1</a>
            <a href="https://example.com/page2">Page 2</a>
            <a href="#">Empty Link</a>
        </body>
    </html>
    """
    response.headers = {"Content-Type": "text/html"}
    mock.get.return_value = response
    
    return mock


def test_crawler_initialization(crawler):
    """Test crawler initialization."""
    assert crawler.user_agent == "Test User Agent"
    assert crawler.respect_robots is True
    assert crawler.rate_limit == 0.01
    
    # Verify session headers
    assert "User-Agent" in crawler.session.headers
    assert crawler.session.headers["User-Agent"] == "Test User Agent"


def test_can_fetch(crawler):
    """Test robots.txt checking."""
    # Mock RobotFileParser
    mock_parser = MagicMock(spec=RobotFileParser)
    mock_parser.can_fetch.return_value = True
    
    with patch.object(crawler, "robot_parsers", {"https://example.com": mock_parser}):
        result = crawler.can_fetch("https://example.com/page")
    
    assert result is True
    mock_parser.can_fetch.assert_called_with("Test User Agent", "https://example.com/page")
    
    # Test with respect_robots=False
    crawler.respect_robots = False
    assert crawler.can_fetch("https://example.com/page") is True


def test_respect_rate_limits(crawler):
    """Test rate limiting."""
    # Set up test conditions
    crawler.last_request_time = {}
    
    # First request should not wait
    start_time = crawler.last_request_time.get("example.com", 0)
    crawler.respect_rate_limits("https://example.com/page1")
    assert "example.com" in crawler.last_request_time
    
    # Second request to same domain should respect rate limit
    with patch("time.sleep") as mock_sleep:
        crawler.respect_rate_limits("https://example.com/page2")
        mock_sleep.assert_called()
    
    # Request to different domain should not be rate limited
    with patch("time.sleep") as mock_sleep:
        crawler.respect_rate_limits("https://different.com/page")
        mock_sleep.assert_not_called()


def test_fetch_page(crawler, mock_session):
    """Test fetching a page."""
    # Replace session with mock
    crawler.session = mock_session
    
    # Mock can_fetch to allow this URL
    crawler.can_fetch = MagicMock(return_value=True)
    
    # Fetch page
    result = crawler.fetch_page("https://example.com")
    
    # Verify session was used correctly
    mock_session.get.assert_called_with("https://example.com", timeout=30)
    
    # Verify result structure
    assert "url" in result
    assert "title" in result
    assert "meta_description" in result
    assert "text" in result
    assert "html" in result
    assert "links" in result
    assert "structured_data" in result
    
    # Verify content
    assert result["url"] == "https://example.com"
    assert result["title"] == "Test Page"
    assert result["meta_description"] == "Test description"
    assert "Test Content" in result["text"]
    assert "This is a test paragraph" in result["text"]
    assert len(result["links"]) == 3
    assert isinstance(result["structured_data"], dict)
    assert "@type" in result["structured_data"]


def test_fetch_page_not_allowed(crawler):
    """Test fetching a page that is not allowed by robots.txt."""
    # Mock can_fetch to disallow this URL
    crawler.can_fetch = MagicMock(return_value=False)
    
    # Fetch page should raise error
    with pytest.raises(RufusError):
        crawler.fetch_page("https://example.com")


def test_fetch_page_request_error(crawler):
    """Test error handling when request fails."""
    # Mock session to raise exception
    crawler.session = MagicMock()
    crawler.session.get.side_effect = requests.RequestException("Test error")
    
    # Mock can_fetch to allow this URL
    crawler.can_fetch = MagicMock(return_value=True)
    
    # Fetch page should raise error
    with pytest.raises(RufusError):
        crawler.fetch_page("https://example.com")


@pytest.mark.skip("Requires Playwright")
def test_dynamic_crawler():
    """Test dynamic crawler functionality."""
    # This is a basic skeleton for testing the dynamic crawler
    # Full testing would require Playwright to be installed
    
    with patch("playwright.sync_api.sync_playwright") as mock_playwright:
        # Mock the browser and page
        mock_browser = MagicMock()
        mock_page = MagicMock()
        
        # Set up mock response
        mock_page.content.return_value = "<html><body>Dynamic content</body></html>"
        mock_page.title.return_value = "Dynamic Page"
        
        # Set up chain of mocks
        mock_browser.new_page.return_value = mock_page
        mock_playwright_instance = MagicMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.start.return_value = mock_playwright_instance
        
        # Create and use dynamic crawler
        with DynamicCrawler(user_agent="Test User Agent") as crawler:
            # Mock can_fetch to allow this URL
            crawler.can_fetch = MagicMock(return_value=True)
            
            # Fetch page
            result = crawler.fetch_page("https://example.com")
            
            # Verify page was used correctly
            mock_page.goto.assert_called_with("https://example.com", wait_until='networkidle', timeout=60000)
            
            # Verify result
            assert "Dynamic content" in result["html"]
            assert result["title"] == "Dynamic Page"