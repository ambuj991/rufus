import json
import csv
import io
import datetime
from typing import List, Dict, Any, Optional, Set

from .utils import logger

class DocumentProcessor:
    """
    Processor for creating and formatting documents from extracted content.
    """
    
    def __init__(self):
        """Initialize the document processor."""
        pass
    
    def cluster_documents(self, documents: List[Dict[str, Any]], max_clusters: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Organize documents into topic clusters.
        
        Args:
            documents: List of documents to cluster
            max_clusters: Maximum number of clusters to create
            
        Returns:
            Dictionary mapping cluster names to lists of documents
        """
        if not documents:
            return {}
        
        # Extract document texts and titles for clustering
        texts = []
        for doc in documents:
            doc_text = doc.get('summary', '')
            doc_title = doc.get('title', '')
            key_points = ' '.join(doc.get('key_points', []))
            texts.append(f"{doc_title}. {doc_text} {key_points}")
        
        # Use LLM to identify clusters
        prompt = f"""
You are an AI assistant specialized in organizing information.

I have a collection of {len(documents)} documents with the following content:

{chr(10).join([f"{i+1}. {text[:300]}..." for i, text in enumerate(texts)])}

Please organize these documents into at most {max_clusters} topical clusters. Each cluster should have a descriptive name.

Return your analysis as a JSON object with the following structure:
{{
  "clusters": [
    {{
      "name": "Cluster Name",
      "description": "Brief description of what this cluster contains",
      "document_indices": [0, 2, 5]  // Indices of documents that belong to this cluster
    }}
  ]
}}

Each document should be assigned to exactly one cluster. The document_indices should refer to the 0-indexed position in the original list.
"""
        
        try:
            # This assumes the LLM handler is available to the processor
            # In a real implementation, you might need to adjust this
            from .llm_handler import LLMHandler
            
            # Check if we have access to an API key
            api_key = getattr(self, 'api_key', None)
            if not api_key:
                # Try to get it from environment variable
                import os
                api_key = os.getenv('RUFUS_API_KEY')
                if not api_key:
                    logger.error("No API key available for clustering")
                    return {"All Documents": documents}
            
            llm_handler = LLMHandler(api_key=api_key, model="gpt-4")
            
            response = llm_handler.client.chat.completions.create(
                model=llm_handler.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that organizes documents into topic clusters."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Organize documents by cluster
            clustered_docs = {}
            for cluster in result.get("clusters", []):
                cluster_name = cluster["name"]
                clustered_docs[cluster_name] = []
                
                for idx in cluster.get("document_indices", []):
                    if 0 <= idx < len(documents):
                        clustered_docs[cluster_name].append(documents[idx])
            
            return clustered_docs
        except Exception as e:
            logger.error(f"Error clustering documents: {str(e)}")
            # Fallback: return a single cluster with all documents
            return {"All Documents": documents}
    
    def create_document(self, url: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a structured document from extracted content.
        
        Args:
            url: The URL the content was extracted from
            content: The extracted content
            
        Returns:
            A structured document
        """
        return {
            'source_url': url,
            'content': content,
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    def process_documents(self, documents: List[Dict[str, Any]], instructions: str) -> List[Dict[str, Any]]:
        """
        Process a list of documents and prepare them for output.
        
        Args:
            documents: List of documents to process
            instructions: The user's instructions
            
        Returns:
            Processed documents ready for output
        """
        # Sort documents by relevance
        sorted_docs = sorted(
            documents, 
            key=lambda x: x.get('content', {}).get('relevance_score', 0), 
            reverse=True
        )
        
        # Process and clean the documents
        processed = []
        for doc in sorted_docs:
            # Skip documents with no relevance
            if doc.get('content', {}).get('relevance_score', 0) == 0:
                continue
            
            # Create a clean document structure
            processed_doc = {
                'url': doc.get('source_url', ''),
                'title': doc.get('content', {}).get('summary', ''),
                'sections': doc.get('content', {}).get('relevant_sections', []),
                'key_points': doc.get('content', {}).get('key_points', []),
                'relevance_score': doc.get('content', {}).get('relevance_score', 0),
                'summary': doc.get('content', {}).get('summary', ''),
                'timestamp': doc.get('timestamp', datetime.datetime.now().isoformat())
            }
            
            processed.append(processed_doc)
        
        return processed
    
    def export_documents(self, documents: List[Dict[str, Any]], format: str = 'json') -> str:
        """
        Export documents in the specified format.
        
        Args:
            documents: List of documents to export
            format: Output format ('json', 'csv', 'markdown')
            
        Returns:
            String representation of the documents in the specified format
        """
        if format.lower() == 'json':
            return self._export_json(documents)
        elif format.lower() == 'csv':
            return self._export_csv(documents)
        elif format.lower() == 'markdown':
            return self._export_markdown(documents)
        else:
            logger.warning(f"Unsupported format: {format}, defaulting to JSON")
            return self._export_json(documents)
    
    def _export_json(self, documents: List[Dict[str, Any]]) -> str:
        """Export documents as JSON."""
        return json.dumps(documents, indent=2, ensure_ascii=False)
    
    def _export_csv(self, documents: List[Dict[str, Any]]) -> str:
        """Export documents as CSV."""
        if not documents:
            return ""
        
        output = io.StringIO()
        
        # Flatten the document structure
        flattened_docs = []
        for doc in documents:
            flat_doc = {
                'url': doc.get('url', ''),
                'title': doc.get('title', ''),
                'summary': doc.get('summary', ''),
                'relevance_score': doc.get('relevance_score', 0),
                'timestamp': doc.get('timestamp', '')
            }
            
            # Add key points as separate columns
            for i, point in enumerate(doc.get('key_points', [])):
                flat_doc[f'key_point_{i+1}'] = point
            
            # Add sections as separate entries or columns
            for i, section in enumerate(doc.get('sections', [])):
                flat_doc[f'section_{i+1}_title'] = section.get('title', '')
                flat_doc[f'section_{i+1}_content'] = section.get('content', '')
            
            flattened_docs.append(flat_doc)
        
        # Get all possible keys
        all_keys: Set[str] = set()
        for doc in flattened_docs:
            all_keys.update(doc.keys())
        
        # Write to CSV
        writer = csv.DictWriter(output, fieldnames=sorted(all_keys))
        writer.writeheader()
        
        for doc in flattened_docs:
            # Fill in missing keys with empty strings
            row = {key: doc.get(key, '') for key in all_keys}
            writer.writerow(row)
        
        return output.getvalue()
    
    def _export_markdown(self, documents: List[Dict[str, Any]]) -> str:
        """Export documents as Markdown."""
        if not documents:
            return ""
        
        md_lines = []
        
        md_lines.append("# Extracted Web Content")
        md_lines.append(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md_lines.append("")
        
        # Table of contents
        md_lines.append("## Table of Contents")
        for i, doc in enumerate(documents):
            title = doc.get('title', f"Document {i+1}")
            md_lines.append(f"{i+1}. [{title}](#{i+1})")
        
        md_lines.append("")
        md_lines.append("---")
        
        # Document content
        for i, doc in enumerate(documents):
            md_lines.append(f"<a id='{i+1}'></a>")
            md_lines.append(f"## {i+1}. {doc.get('title', f'Document {i+1}')}")
            md_lines.append(f"**Source:** [{doc.get('url', 'No URL')}]({doc.get('url', '#')})")
            md_lines.append(f"**Relevance Score:** {doc.get('relevance_score', 0)}/10")
            md_lines.append("")
            
            if doc.get('summary'):
                md_lines.append("### Summary")
                md_lines.append(doc.get('summary', ''))
                md_lines.append("")
            
            if doc.get('key_points'):
                md_lines.append("### Key Points")
                for point in doc.get('key_points', []):
                    md_lines.append(f"- {point}")
                md_lines.append("")
            
            if doc.get('sections'):
                for section in doc.get('sections', []):
                    md_lines.append(f"### {section.get('title', 'Section')}")
                    md_lines.append(section.get('content', ''))
                    md_lines.append("")
            
            md_lines.append("---")
            md_lines.append("")
        
        return "\n".join(md_lines)