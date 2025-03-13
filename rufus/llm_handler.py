import json
from typing import Dict, List, Any, Optional, Union
import openai
from .utils import logger, RufusError, truncate_text

# Remove circular import
# from client import RufusClient

class LLMHandler:
    """
    Handler for LLM integration to provide intelligence to the crawler.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize the LLM handler.
        
        Args:
            api_key: API key for the LLM service
            model: LLM model to use (default: gpt-4)
        """
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)

    def enhanced_identify_relevant_links(
        self, 
        page_content: Dict[str, Any], 
        base_url: str, 
        instructions: str,
        max_links: int = 10,
        visited_links: List[str] = [],
        current_depth: int = 0,
        max_depth: int = 3,
        discovered_topics: List[str] = []
    ) -> Dict[str, Any]:
        """
        Enhanced version that uses context from previously visited pages.
        
        Args:
            page_content: The page content dictionary from the crawler
            base_url: The base URL for the page
            instructions: The user's instructions
            max_links: Maximum number of links to return
            visited_links: List of already visited links
            current_depth: Current depth in the crawl
            max_depth: Maximum depth to crawl
            discovered_topics: Topics already discovered during crawling
            
        Returns:
            A dictionary with prioritized links and contextual information
        """
        links = page_content.get('links', [])
        if not links:
            return {"links": [], "new_topics": []}
        
        # Limit to reasonable number to avoid token limits
        links = links[:30]
        
        # Create a string representation of links
        links_text = "\n".join([f"{i+1}. {link['text']} - {link['url']}" for i, link in enumerate(links)])
        
        # Include information about already visited pages and discovered topics
        visited_context = f"You have already visited {len(visited_links)} pages."
        if visited_links:
            visited_context += f" Including: {', '.join(visited_links[-5:])}"
        
        topic_context = ""
        if discovered_topics:
            topic_context = f"You have already discovered information about: {', '.join(discovered_topics)}"
        
        # Add depth context
        depth_context = f"Current depth: {current_depth}/{max_depth}."
        if current_depth == max_depth - 1:
            depth_context += " This is the last level you'll explore, so choose links that directly contain valuable information rather than navigation pages."
        
        prompt = f"""
You are an AI web scraping assistant. Your task is to identify which links are worth following based on these instructions:
"{instructions}"

Current page: {page_content.get('url', '')}
Current page title: {page_content.get('title', '')}

Context:
{visited_context}
{topic_context}
{depth_context}

Available links:
{links_text}

Analyze these links and identify which ones are most likely to contain information relevant to the instructions.
For each link you recommend following, explain WHY it's relevant and what specific information you expect to find there.

Also identify any new topics or information categories you expect to discover that aren't covered by already visited pages.

Return your response as a JSON object with two keys:
1. "links": An array of URL strings for the links that should be followed, in order of priority (most relevant first)
2. "new_topics": An array of strings describing new information categories you expect to find

Return no more than {max_links} links.

If none of the links are relevant to the instructions, return an empty links array.
Your response should be valid JSON without any additional text.
"""
        
        try:
            # Call the OpenAI API using the new client format
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI web scraping assistant that identifies relevant links to follow."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3  # Low temperature for more deterministic responses
            )
            
            # Parse the response as JSON
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                # Ensure it has the required structure
                if not isinstance(result, dict):
                    logger.warning(f"LLM response is not a dictionary: {content}")
                    return {"links": [], "new_topics": []}
                
                if "links" not in result:
                    result["links"] = []
                
                if "new_topics" not in result:
                    result["new_topics"] = []
                
                # Limit to max_links
                result["links"] = result["links"][:max_links]
                
                return result
            except json.JSONDecodeError:
                # Handle error and try to extract JSON
                logger.error(f"Failed to parse LLM response as JSON")
                return {"links": [], "new_topics": []}
        except Exception as e:
            logger.error(f"Error calling LLM API: {str(e)}")
            return {"links": [], "new_topics": []}

    def extract_with_memory(
        self, 
        page_content: Dict[str, Any], 
        instructions: str,
        memory: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Extract content with awareness of previously extracted information.
        
        Args:
            page_content: The page content dictionary from the crawler
            instructions: The user's instructions
            memory: Previously extracted information and summaries
            
        Returns:
            A dictionary with the relevant content and updated memory
        """
        if memory is None:
            memory = {
                "summaries": [],
                "key_concepts": set(),
                "entities": set(),
                "contradictions": []
            }
        
        # Create a prompt for the LLM
        page_text = page_content.get('text', '')
        page_title = page_content.get('title', '')
        page_url = page_content.get('url', '')
        
        # Truncate the text to avoid token limits
        truncated_text = truncate_text(page_text, max_length=6000)
        
        # Context from memory
        memory_context = ""
        if memory["summaries"]:
            memory_context = "Previous information collected:\n"
            # Include the last 3 summaries
            for i, summary in enumerate(memory["summaries"][-3:]):
                memory_context += f"{i+1}. {summary}\n"
        
        # Key concepts found so far
        concepts_context = ""
        if memory["key_concepts"]:
            concepts_context = "Key concepts already identified: " + ", ".join(list(memory["key_concepts"])[:20])
        
        prompt = f"""
You are an AI web scraping assistant. Your task is to extract relevant information based on these instructions:
"{instructions}"

From the following web page content, extract only the information that is relevant to the instructions.

Title: {page_title}
URL: {page_url}

{memory_context}
{concepts_context}

Page Content:
{truncated_text}

Extract information in the following JSON format:
{{
  "relevant_sections": [
    {{
      "title": "Section title",
      "content": "Extracted content"
    }}
  ],
  "key_points": ["Key point 1", "Key point 2"],
  "new_concepts": ["New concept 1", "New concept 2"],
  "relevance_score": (0-10 score indicating how relevant this content is to the instructions),
  "summary": "A brief summary of the relevant information",
  "contradictions": ["Any contradiction with previously collected information"]
}}

Focus on extracting NEW information not already covered in the previous summaries.
If the page contains contradictory information compared to what was previously collected, highlight this in the "contradictions" field.
If the page has no relevant content, set relevance_score to 0 and leave the other fields empty.
Your response should be valid JSON without any additional text.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI web scraping assistant that extracts relevant information from web pages."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                
                # Update memory
                if result.get("summary"):
                    memory["summaries"].append(result["summary"])
                
                if result.get("new_concepts"):
                    memory["key_concepts"].update(result["new_concepts"])
                
                if result.get("contradictions"):
                    memory["contradictions"].extend(result["contradictions"])
                
                # Add memory to the result
                result["memory"] = memory
                
                return result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON")
                return {
                    "relevant_sections": [],
                    "key_points": [],
                    "relevance_score": 0,
                    "summary": "",
                    "memory": memory
                }
        except Exception as e:
            logger.error(f"Error calling LLM API: {str(e)}")
            return {
                "relevant_sections": [],
                "key_points": [],
                "relevance_score": 0,
                "summary": "",
                "memory": memory
            }
    
    def extract_relevant_content(self, page_content: Dict[str, Any], instructions: str) -> Dict[str, Any]:
        """
        Use LLM to extract relevant content from a page.
        
        Args:
            page_content: The page content dictionary from the crawler
            instructions: The user's instructions
            
        Returns:
            A dictionary with the relevant content
        """
        # Create a prompt for the LLM
        page_text = page_content.get('text', '')
        page_title = page_content.get('title', '')
        page_url = page_content.get('url', '')
        meta_description = page_content.get('meta_description', '')
        
        # Truncate the text to avoid token limits
        truncated_text = truncate_text(page_text, max_length=6000)
        
        prompt = f"""
You are an AI web scraping assistant. Your task is to extract relevant information based on these instructions:
"{instructions}"

From the following web page content, extract only the information that is relevant to the instructions.

Title: {page_title}
URL: {page_url}
Description: {meta_description}

Page Content:
{truncated_text}

Extract information in the following JSON format:
{{
  "relevant_sections": [
    {{
      "title": "Section title",
      "content": "Extracted content"
    }}
  ],
  "key_points": ["Key point 1", "Key point 2"],
  "relevance_score": (0-10 score indicating how relevant this content is to the instructions),
  "summary": "A brief summary of the relevant information"
}}

If the page has no relevant content, set relevance_score to 0 and leave the other fields empty.
Your response should be valid JSON without any additional text.
"""
        
        try:
            # Call the OpenAI API using the new client format
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI web scraping assistant that extracts relevant information from web pages."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3  # Low temperature for more deterministic responses
            )
            
            # Parse the response as JSON
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
                # Try to extract JSON from the response
                try:
                    json_str = content.strip()
                    if json_str.startswith('```json'):
                        json_str = json_str.replace('```json', '', 1)
                    if json_str.endswith('```'):
                        json_str = json_str[:-3]
                    
                    result = json.loads(json_str.strip())
                    return result
                except:
                    logger.error(f"Could not extract JSON from LLM response: {content}")
                    # Fallback if JSON parsing fails
                    return {
                        "relevant_sections": [],
                        "key_points": [],
                        "relevance_score": 0,
                        "summary": ""
                    }
        except Exception as e:
            logger.error(f"Error calling LLM API: {str(e)}")
            raise RufusError(f"LLM API error: {str(e)}")
    
    def identify_relevant_links(
        self, 
        page_content: Dict[str, Any], 
        base_url: str, 
        instructions: str,
        max_links: int = 10
    ) -> List[str]:
        """
        Use LLM to identify which links are worth following.
        
        Args:
            page_content: The page content dictionary from the crawler
            base_url: The base URL for the page
            instructions: The user's instructions
            max_links: Maximum number of links to return
            
        Returns:
            A list of URLs to follow
        """
        links = page_content.get('links', [])
        if not links:
            return []
        
        # Limit to 20 links to avoid token limits
        links = links[:20]
        
        # Create a string representation of links
        links_text = "\n".join([f"{i+1}. {link['text']} - {link['url']}" for i, link in enumerate(links)])
        
        prompt = f"""
You are an AI web scraping assistant. Your task is to identify which links are worth following based on these instructions:
"{instructions}"

Current page: {page_content.get('url', '')}
Current page title: {page_content.get('title', '')}

Available links:
{links_text}

Analyze these links and identify which ones are most likely to contain information relevant to the instructions.
Return your response as a JSON array of URL strings for the links that should be followed, in order of priority (most relevant first).
Return no more than {max_links} links.

If none of the links are relevant to the instructions, return an empty array.
Your response should be valid JSON without any additional text.
"""
        
        try:
            # Call the OpenAI API using the new client format
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI web scraping assistant that identifies relevant links to follow."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3  # Low temperature for more deterministic responses
            )
            
            # Parse the response as JSON
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                # Ensure it's a list
                if not isinstance(result, list):
                    logger.warning(f"LLM response is not a list: {content}")
                    return []
                
                # Limit to max_links
                result = result[:max_links]
                
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
                # Try to extract JSON from the response
                try:
                    json_str = content.strip()
                    if json_str.startswith('```json'):
                        json_str = json_str.replace('```json', '', 1)
                    if json_str.endswith('```'):
                        json_str = json_str[:-3]
                    
                    result = json.loads(json_str.strip())
                    if not isinstance(result, list):
                        return []
                    
                    return result[:max_links]
                except:
                    logger.error(f"Could not extract JSON from LLM response: {content}")
                    return []
        except Exception as e:
            logger.error(f"Error calling LLM API: {str(e)}")
            return []