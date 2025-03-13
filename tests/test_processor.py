import pytest
import json
import datetime
from unittest.mock import patch

from rufus.processor import DocumentProcessor


@pytest.fixture
def processor():
    """Create a processor instance for testing."""
    return DocumentProcessor()


@pytest.fixture
def sample_content():
    """Sample content extracted from a page."""
    return {
        "relevant_sections": [
            {"title": "Section 1", "content": "Content 1"},
            {"title": "Section 2", "content": "Content 2"}
        ],
        "key_points": ["Key point 1", "Key point 2"],
        "relevance_score": 8,
        "summary": "Sample summary"
    }


@pytest.fixture
def sample_documents():
    """Sample list of documents for testing."""
    return [
        {
            "source_url": "https://example.com/page1",
            "content": {
                "relevant_sections": [
                    {"title": "Section 1", "content": "Content 1"}
                ],
                "key_points": ["Key point 1"],
                "relevance_score": 8,
                "summary": "Summary 1"
            },
            "timestamp": "2023-01-01T00:00:00"
        },
        {
            "source_url": "https://example.com/page2",
            "content": {
                "relevant_sections": [
                    {"title": "Section 2", "content": "Content 2"}
                ],
                "key_points": ["Key point 2"],
                "relevance_score": 5,
                "summary": "Summary 2"
            },
            "timestamp": "2023-01-02T00:00:00"
        },
        {
            "source_url": "https://example.com/page3",
            "content": {
                "relevant_sections": [],
                "key_points": [],
                "relevance_score": 0,
                "summary": ""
            },
            "timestamp": "2023-01-03T00:00:00"
        }
    ]


def test_create_document(processor, sample_content):
    """Test creating a document from extracted content."""
    url = "https://example.com"
    
    with patch("datetime.datetime") as mock_datetime:
        # Mock datetime.now()
        mock_now = datetime.datetime(2023, 1, 1, 0, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Create document
        result = processor.create_document(url, sample_content)
    
    # Verify structure
    assert result["source_url"] == url
    assert result["content"] == sample_content
    assert result["timestamp"] == "2023-01-01T00:00:00"


def test_process_documents(processor, sample_documents):
    """Test processing a list of documents."""
    # Process documents
    instructions = "Test instructions"
    result = processor.process_documents(sample_documents, instructions)
    
    # Verify result
    assert len(result) == 2  # Should exclude the one with relevance_score = 0
    
    # Check sorting by relevance
    assert result[0]["relevance_score"] > result[1]["relevance_score"]
    
    # Check structure
    for doc in result:
        assert "url" in doc
        assert "title" in doc
        assert "sections" in doc
        assert "key_points" in doc
        assert "relevance_score" in doc
        assert "summary" in doc
        assert "timestamp" in doc


def test_export_json(processor, sample_documents):
    """Test exporting documents as JSON."""
    # Process documents first
    processed = processor.process_documents(sample_documents, "Test instructions")
    
    # Export as JSON
    result = processor._export_json(processed)
    
    # Verify result is valid JSON
    parsed = json.loads(result)
    assert isinstance(parsed, list)
    assert len(parsed) == 2


def test_export_csv(processor, sample_documents):
    """Test exporting documents as CSV."""
    # Process documents first
    processed = processor.process_documents(sample_documents, "Test instructions")
    
    # Export as CSV
    result = processor._export_csv(processed)
    
    # Verify result structure
    assert isinstance(result, str)
    assert result.startswith("url,")  # Header row
    assert "https://example.com/page1" in result
    assert "https://example.com/page2" in result


def test_export_markdown(processor, sample_documents):
    """Test exporting documents as Markdown."""
    # Process documents first
    processed = processor.process_documents(sample_documents, "Test instructions")
    
    # Mock datetime.now() for consistent output
    with patch("datetime.datetime") as mock_datetime:
        mock_now = datetime.datetime(2023, 1, 1, 0, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Export as Markdown
        result = processor._export_markdown(processed)
    
    # Verify result structure
    assert "# Extracted Web Content" in result
    assert "Generated on: 2023-01-01" in result
    assert "## Table of Contents" in result
    assert "## 1. Summary 1" in result
    assert "## 2. Summary 2" in result
    assert "**Source:**" in result
    assert "**Relevance Score:**" in result
    assert "### Summary" in result
    assert "### Key Points" in result
    assert "### Section 1" in result
    assert "### Section 2" in result


def test_export_documents(processor, sample_documents):
    """Test the export_documents method with different formats."""
    # Process documents first
    processed = processor.process_documents(sample_documents, "Test instructions")
    
    # Mock individual export methods
    processor._export_json = lambda docs: "JSON_OUTPUT"
    processor._export_csv = lambda docs: "CSV_OUTPUT"
    processor._export_markdown = lambda docs: "MARKDOWN_OUTPUT"
    
    # Test each format
    assert processor.export_documents(processed, format='json') == "JSON_OUTPUT"
    assert processor.export_documents(processed, format='csv') == "CSV_OUTPUT"
    assert processor.export_documents(processed, format='markdown') == "MARKDOWN_OUTPUT"
    
    # Test invalid format defaults to JSON
    assert processor.export_documents(processed, format='invalid') == "JSON_OUTPUT"