from typing import List, Dict, Any, Optional

from ..utils import logger


def create_llamaindex_documents(documents: List[Dict[str, Any]]) -> List:
    """
    Convert Rufus documents to LlamaIndex Document objects.
    
    Args:
        documents: List of documents from Rufus
        
    Returns:
        List of LlamaIndex Document objects
    """
    try:
        from llama_index.schema import Document
    except ImportError:
        logger.error("LlamaIndex is not installed. Install with 'pip install llama-index'")
        raise ImportError("LlamaIndex is not installed. Install with 'pip install llama-index'")
    
    llamaindex_docs = []
    
    for doc in documents:
        # Extract metadata
        metadata = {
            "source": doc.get("url", ""),
            "title": doc.get("title", ""),
            "relevance_score": doc.get("relevance_score", 0),
            "timestamp": doc.get("timestamp", "")
        }
        
        # Build content from sections
        content_parts = []
        
        # Add summary if available
        if doc.get("summary"):
            content_parts.append(f"Summary: {doc['summary']}")
        
        # Add key points if available
        if doc.get("key_points"):
            content_parts.append("Key Points:")
            for point in doc["key_points"]:
                content_parts.append(f"- {point}")
        
        # Add sections if available
        for section in doc.get("sections", []):
            content_parts.append(f"## {section.get('title', 'Section')}")
            content_parts.append(section.get("content", ""))
        
        # Join all content
        content = "\n\n".join(content_parts)
        
        # Create LlamaIndex document
        llamaindex_docs.append(Document(
            text=content,
            metadata=metadata
        ))
    
    return llamaindex_docs


def create_llamaindex_index(documents: List[Dict[str, Any]], embed_model: Optional[str] = None):
    """
    Create a LlamaIndex from Rufus documents.
    
    Args:
        documents: List of documents from Rufus
        embed_model: Optional embedding model name
        
    Returns:
        LlamaIndex index
    """
    try:
        from llama_index import VectorStoreIndex, ServiceContext
        from llama_index.embeddings import OpenAIEmbedding
    except ImportError:
        logger.error("LlamaIndex is not installed. Install with 'pip install llama-index'")
        raise ImportError("LlamaIndex is not installed. Install with 'pip install llama-index'")
    
    # Convert to LlamaIndex documents
    llamaindex_docs = create_llamaindex_documents(documents)
    
    # Set up embedding model if specified
    if embed_model:
        embed_model = OpenAIEmbedding(model=embed_model)
        service_context = ServiceContext.from_defaults(embed_model=embed_model)
        index = VectorStoreIndex.from_documents(llamaindex_docs, service_context=service_context)
    else:
        index = VectorStoreIndex.from_documents(llamaindex_docs)
    
    return index