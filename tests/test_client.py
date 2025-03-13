import pytest
import os
from unittest.mock import MagicMock, patch

from rufus import RufusClient, RufusError
from rufus.crawler import Crawler
from rufus.llm_handler import LLMHandler
from rufus.processor import DocumentProcessor


@pytest.fixture
def mock_llm_handler():
    """Mock LLM handler for testing."""
    mock = MagicMock(spec=LLMHandler)
    
    # Setup extract_relevant_content to return meaningful data
    mock.extract_relevant_content.return_value = {
        "relevant_sections": [
            {"title": "Test Section", "content": "Test content"}
        ],
        "key_points": ["Key point 1", "Key point 2"],
        "relevance_score": 8,
        "summary": "Test summary"
    }
    
    # Setup identify_relevant_links to return a list of links
    mock.identify_relevant_links.return_value = [
        "https://example.com/page1",
        "https://example.com/page2"
    ]
    
    return mock


@pytest.fixture
def mock_crawler():
    """Mock crawler for testing."""
    mock = MagicMock(spec=Crawler)
    
    # Setup fetch_page to return page content
    mock.fetch_page.return_value = {
        "url": "https://example.com",
        "title": "Example Page",
        "meta_description": "An example page",
        "text": "This is example content",
        "html": "<html><body>This is example content</body></html>",
        "links": [
            {"url": "https://example.com/page1", "text": "Page 1"},
            {"url": "https://example.com/page2", "text": "Page 2"}
        ],
        "structured_data": {}
    }
    
    return mock


@pytest.fixture
def client(mock_llm_handler, mock_crawler):
    """Create a client with mocked dependencies."""
    with patch("rufus.client.LLMHandler", return_value=mock_llm_handler):
        with patch("rufus.client.Crawler", return_value=mock_crawler):
            client = RufusClient(api_key="test-api-key")
            # Replace the processor with a mock
            client.processor = MagicMock(spec=DocumentProcessor)
            return client


def test_client_initialization():
    """Test client initialization with API key."""
    # Test with direct API key
    client = RufusClient(api_key="test-api-key")
    assert client.api_key == "test-api-key"
    
    # Test with environment variable
    with patch.dict(os.environ, {"RUFUS_API_KEY": "env-api-key"}):
        client = RufusClient()
        assert client.api_key == "env-api-key"
    
    # Test with missing API key
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RufusError):
            _ = RufusClient()


def test_scrape(client, mock_crawler, mock_llm_handler):
    """Test the scrape method."""
    # Mock processor to return specific document structure
    client.processor.create_document.return_value = {
        "source_url": "https://example.com",
        "content": mock_llm_handler.extract_relevant_content.return_value,
        "timestamp": "2023-01-01T00:00:00"
    }
    
    client.processor.process_documents.return_value = [
        {
            "url": "https://example.com",
            "title": "Test summary",
            "sections": [{"title": "Test Section", "content": "Test content"}],
            "key_points": ["Key point 1", "Key point 2"],
            "relevance_score": 8,
            "summary": "Test summary",
            "timestamp": "2023-01-01T00:00:00"
        }
    ]
    
    # Perform scrape
    result = client.scrape(
        url="https://example.com",
        instructions="Test instructions",
        max_pages=2
    )
    
    # Verify interactions
    mock_crawler.fetch_page.assert_called()
    mock_llm_handler.extract_relevant_content.assert_called()
    mock_llm_handler.identify_relevant_links.assert_called()
    client.processor.create_document.assert_called()
    client.processor.process_documents.assert_called()
    
    # Verify result
    assert isinstance(result, list)
    assert len(result) > 0
    assert "url" in result[0]
    assert "title" in result[0]
    assert "sections" in result[0]
    assert "key_points" in result[0]
    assert "relevance_score" in result[0]
    assert "summary" in result[0]


def test_batch_scrape(client):
    """Test the batch_scrape method."""
    # Mock scrape method to return specific results
    client.scrape = MagicMock(return_value=[
        {
            "url": "https://example.com",
            "title": "Test Document",
            "sections": [],
            "key_points": [],
            "relevance_score": 8,
            "summary": "Test summary"
        }
    ])
    
    # Test with multiple URLs
    urls = ["https://example.com", "https://example.org"]
    result = client.batch_scrape(
        urls=urls,
        instructions="Test instructions"
    )
    
    # Verify scrape was called for each URL
    assert client.scrape.call_count == len(urls)
    
    # Verify result structure
    assert isinstance(result, dict)
    for url in urls:
        assert url in result
        assert isinstance(result[url], list)


def test_export_and_save(client):
    """Test the export and save methods."""
    # Setup test data
    documents = [
        {
            "url": "https://example.com",
            "title": "Test Document",
            "sections": [{"title": "Section", "content": "Content"}],
            "key_points": ["Point 1", "Point 2"],
            "relevance_score": 8,
            "summary": "Summary",
            "timestamp": "2023-01-01T00:00:00"
        }
    ]
    
    # Mock processor export method
    client.processor.export_documents.return_value = '{"test": "data"}'
    
    # Test export with different formats
    client.export(documents, format='json')
    client.processor.export_documents.assert_called_with(documents, 'json')
    
    client.export(documents, format='csv')
    client.processor.export_documents.assert_called_with(documents, 'csv')
    
    client.export(documents, format='markdown')
    client.processor.export_documents.assert_called_with(documents, 'markdown')
    
    # Test save with mocked open
    with patch("builtins.open", MagicMock()) as mock_open:
        client.save(documents, "test.json")
        mock_open.assert_called_once()


def test_dynamic_crawler(client):
    """Test using the dynamic crawler."""
    # Mock dynamic crawler context manager
    dynamic_mock = MagicMock()
    dynamic_mock.__enter__ = MagicMock(return_value=dynamic_mock)
    dynamic_mock.__exit__ = MagicMock(return_value=None)
    
    with patch("rufus.client.DynamicCrawler", return_value=dynamic_mock):
        # Set up dynamic crawler to return the same data as the standard crawler
        dynamic_mock.fetch_page.return_value = client.crawler.fetch_page.return_value
        
        # Test with dynamic=True
        result = client.scrape(
            url="https://example.com",
            instructions="Test instructions",
            dynamic=True
        )
        
        # Verify dynamic crawler was used
        dynamic_mock.__enter__.assert_called_once()
        dynamic_mock.__exit__.assert_called_once()