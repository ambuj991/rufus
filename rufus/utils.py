import logging
import sys
from typing import Optional


# Set up logging
logger = logging.getLogger("rufus")
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class RufusError(Exception):
    """Base exception class for Rufus errors."""
    pass


def truncate_text(text: str, max_length: int = 6000, truncation_msg: Optional[str] = None) -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: The text to truncate
        max_length: Maximum length in characters
        truncation_msg: Optional message to append if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    if truncation_msg:
        return truncated + truncation_msg
    return truncated


def setup_logger(level: str = 'INFO', log_file: Optional[str] = None) -> None:
    """
    Set up the logger with custom settings.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path to write logs
    """
    # Set log level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    console_handler.setLevel(numeric_level)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def is_same_domain(url1: str, url2: str) -> bool:
    """
    Check if two URLs are from the same domain.
    
    Args:
        url1: First URL
        url2: Second URL
        
    Returns:
        True if URLs are from the same domain
    """
    from urllib.parse import urlparse
    
    parsed1 = urlparse(url1)
    parsed2 = urlparse(url2)
    
    return parsed1.netloc == parsed2.netloc


def normalize_url(url: str) -> str:
    """
    Normalize a URL by removing fragments and some query parameters.
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL
    """
    from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
    
    # Parse the URL
    parsed = urlparse(url)
    
    # Remove fragment
    fragment = ""
    
    # Get query parameters
    query_params = parse_qs(parsed.query)
    
    # Remove tracking parameters
    tracking_params = [
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'dclid', 'zanpid', 'msclkid'
    ]
    
    for param in tracking_params:
        if param in query_params:
            del query_params[param]
    
    # Rebuild query string
    query = urlencode(query_params, doseq=True) if query_params else ""
    
    # Rebuild URL
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        query,
        fragment
    ))
    
    return normalized