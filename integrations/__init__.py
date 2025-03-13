"""
Rufus integrations with popular RAG frameworks.

This package provides connectors and utilities for integrating
Rufus with various Retrieval-Augmented Generation frameworks.
"""

from .langchain import create_langchain_documents, create_langchain_retriever
from .llamaindex import create_llamaindex_documents, create_llamaindex_index

__all__ = [
    'create_langchain_documents',
    'create_langchain_retriever',
    'create_llamaindex_documents',
    'create_llamaindex_index'
]