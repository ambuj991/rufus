"""
Rufus: Intelligent Web Data Extraction for LLMs

An AI-driven web crawler and data extraction tool that intelligently
extracts structured data from websites based on natural language instructions.
"""

__version__ = '0.1.0'

from .client import RufusClient
from .utils import RufusError, setup_logger



from .client import RufusClient
from .utils import RufusError, setup_logger
from .crawler import Crawler, DynamicCrawler

__all__ = ['RufusClient', 'RufusError', 'setup_logger']