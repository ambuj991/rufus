from typing import List, Dict, Any, Optional, Callable, Union

from ..utils import logger


def create_langchain_documents(documents: List[Dict[str, Any]], chunk_size: Optional[int] = None) -> List:
    """
    Convert Rufus documents to LangChain Document objects.
    
    Args:
        documents: List of documents from Rufus
        chunk_size: Optional size to chunk content
        
    Returns:
        List of LangChain Document objects
    """
    try:
        from langchain.schema import Document
    except ImportError:
        logger.error("LangChain is not installed. Install with 'pip install langchain'")
        raise ImportError("LangChain is not installed. Install with 'pip install langchain'")
    
    langchain_docs = []
    
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
        
        # Create LangChain document
        if chunk_size and len(content) > chunk_size:
            # Create chunked documents
            chunks = _chunk_text(content, chunk_size)
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk"] = i
                chunk_metadata["chunk_total"] = len(chunks)
                
                langchain_docs.append(Document(
                    page_content=chunk,
                    metadata=chunk_metadata
                ))
        else:
            # Create a single document
            langchain_docs.append(Document(
                page_content=content,
                metadata=metadata
            ))
    
    return langchain_docs


def _chunk_text(text: str, chunk_size: int) -> List[str]:
    """Split text into chunks of approximately chunk_size characters."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    for paragraph in text.split("\n\n"):
        if len(current_chunk) + len(paragraph) + 2 <= chunk_size:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            # If paragraph is longer than chunk_size, split it further
            if len(paragraph) > chunk_size:
                # Split by sentence
                sentences = paragraph.split(". ")
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 2 <= chunk_size:
                        if current_chunk:
                            current_chunk += ". " + sentence
                        else:
                            current_chunk = sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk + ".")
                        
                        # If sentence is still too long, just chunk it by size
                        if len(sentence) > chunk_size:
                            sentence_chunks = [sentence[i:i+chunk_size] for i in range(0, len(sentence), chunk_size)]
                            chunks.extend(sentence_chunks[:-1])
                            current_chunk = sentence_chunks[-1]
                        else:
                            current_chunk = sentence
            else:
                current_chunk = paragraph
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def create_langchain_retriever(documents: List[Dict[str, Any]], embedding_function: Optional[Callable] = None):
    """
    Create a LangChain retriever from Rufus documents.
    
    Args:
        documents: List of documents from Rufus
        embedding_function: Function to create embeddings
        
    Returns:
        LangChain retriever
    """
    try:
        from langchain.vectorstores import Chroma
        from langchain.embeddings import OpenAIEmbeddings
    except ImportError:
        logger.error("LangChain is not installed. Install with 'pip install langchain'")
        raise ImportError("LangChain is not installed. Install with 'pip install langchain'")
    
    # Convert to LangChain documents
    langchain_docs = create_langchain_documents(documents)
    
    # Set up embedding function
    embeddings = embedding_function or OpenAIEmbeddings()
    
    # Create vector store
    vectorstore = Chroma.from_documents(langchain_docs, embeddings)
    
    # Return retriever
    return vectorstore.as_retriever()