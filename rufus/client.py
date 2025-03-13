import os
import time
import datetime
import requests
from typing import List, Dict, Any, Union, Optional, Set
import json

from .crawler import Crawler, DynamicCrawler, AuthenticatedCrawler
from .llm_handler import LLMHandler
from .processor import DocumentProcessor
from .utils import logger, RufusError, is_same_domain


class RufusClient:
    """
    Main client class for Rufus web data extraction.
    
    Provides methods to extract structured data from websites
    based on natural language instructions.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        user_agent: Optional[str] = None,
        respect_robots: bool = True,
        rate_limit: float = 1.0,
        llm_model: str = "gpt-4",
        output_format: str = "json"
    ):
        """
        Initialize the Rufus client.
        
        Args:
            api_key: API key for LLM service (OpenAI by default)
            user_agent: Custom user agent for web requests
            respect_robots: Whether to respect robots.txt rules
            rate_limit: Time to wait between requests in seconds
            llm_model: LLM model to use for content analysis
            output_format: Default output format (json, csv, markdown)
        """
        self.api_key = api_key or os.getenv('RUFUS_API_KEY')
        if not self.api_key:
            raise RufusError("API key is required. Pass it directly or set RUFUS_API_KEY environment variable.")
        
        self.llm_handler = LLMHandler(api_key=self.api_key, model=llm_model)
        self.crawler = Crawler(
            user_agent=user_agent,
            respect_robots=respect_robots,
            rate_limit=rate_limit
        )
        self.processor = DocumentProcessor()
        self.output_format = output_format
    
    def scrape(
        self, 
        url: str, 
        instructions: str = "", 
        max_pages: int = 15,
        max_depth: int = 3,
        dynamic: bool = False,
        respect_robots: bool = None,
        rate_limit: float = None,
        timeout: int = 60,
        auth_options: Dict[str, Any] = None,
        advanced_options: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        General-purpose method to scrape any website based on natural language instructions.
        
        This is the main method developers should use for easy integration with RAG pipelines.
        It's designed to work with any URL and any set of instructions.
        
        Args:
            url: The starting URL to scrape
            instructions: Natural language instructions for what to extract
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum depth of links to follow
            dynamic: Whether to use a browser to render JavaScript
            respect_robots: Whether to respect robots.txt rules (defaults to client setting)
            rate_limit: Time to wait between requests in seconds (defaults to client setting)
            timeout: Request timeout in seconds
            auth_options: Authentication options if the site requires login
            advanced_options: Additional options for fine-tuning the extraction
                
        Returns:
            A list of structured documents ready for use in LLM pipelines
        """
        logger.info(f"Starting scrape of {url} with instructions: {instructions}")
        
        # Use client-level settings if not specified
        if respect_robots is None:
            respect_robots = self.crawler.respect_robots
        if rate_limit is None:
            rate_limit = self.crawler.rate_limit
        
        # Create a temporary crawler with specified parameters if they differ from defaults
        temp_crawler = None
        if respect_robots != self.crawler.respect_robots or rate_limit != self.crawler.rate_limit:
            temp_crawler = Crawler(
                user_agent=self.crawler.user_agent,
                respect_robots=respect_robots,
                rate_limit=rate_limit
            )
        
        # Use the crawler
        crawler_to_use = temp_crawler or self.crawler
        
        # Store original crawler and swap temporarily if needed
        original_crawler = self.crawler
        if temp_crawler:
            self.crawler = temp_crawler
        
        # Process advanced options
        if not advanced_options:
            advanced_options = {}
        
        map_first = advanced_options.get('map_first', True)
        use_memory = advanced_options.get('use_memory', True)
        cluster_results = advanced_options.get('cluster_results', False)
        extract_metadata = advanced_options.get('extract_metadata', True)
        extract_structured_data = advanced_options.get('extract_structured_data', True)
        
        # Determine if URL is valid before proceeding
        try:
            # Just check if the URL is accessible
            test_response = requests.head(url, timeout=timeout)
            test_response.raise_for_status()
        except requests.RequestException as e:
            logger.warning(f"URL check failed for {url}: {str(e)}")
            # Continue anyway, as the crawler will handle errors appropriately
        
        try:
            # Analyze the instruction to determine best extraction parameters
            instruction_analysis = self._analyze_instruction(instructions)
            
            # Adjust parameters based on instruction analysis
            actual_max_depth = instruction_analysis.get('recommended_depth', max_depth)
            actual_max_pages = instruction_analysis.get('recommended_pages', max_pages)
            
            # Use intelligent_scrape internally with optimized parameters
            results = self.intelligent_scrape(
                url=url,
                instructions=instructions,
                max_pages=actual_max_pages,
                max_depth=actual_max_depth,
                dynamic=dynamic,
                map_first=map_first,
                use_memory=use_memory,
                cluster_results=cluster_results,
                auth_options=auth_options
            )
            
            # Extract just the processed documents for a cleaner, simpler API
            if "processed_documents" in results:
                documents = results["processed_documents"]
            elif "documents" in results:
                documents = self.processor.process_documents(results["documents"], instructions)
            else:
                logger.warning("No documents found in scraping results")
                documents = []
            
            # Add extraction metadata if requested
            if extract_metadata:
                for doc in documents:
                    doc['extraction_metadata'] = {
                        'timestamp': datetime.datetime.now().isoformat(),
                        'total_pages_visited': results['stats']['pages_visited'],
                        'extraction_time': results['stats']['total_extraction_time'],
                        'success': True
                    }
            
            return documents
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            # Return empty list with error information
            return [{
                'error': str(e),
                'url': url,
                'extraction_metadata': {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'success': False,
                    'error_type': type(e).__name__
                }
            }]
        finally:
            # Restore original crawler if we created a temporary one
            if temp_crawler:
                self.crawler = original_crawler
    
    def _analyze_instruction(self, instruction: str) -> Dict[str, Any]:
        """
        Analyze the instruction to determine optimal extraction parameters.
        
        Args:
            instruction: The user's natural language instruction
            
        Returns:
            Dictionary with recommended parameters
        """
        # Default recommendations
        recommendations = {
            'recommended_depth': 3,
            'recommended_pages': 15,
            'requires_javascript': False,
            'complexity': 'medium'
        }
        
        # If the instruction is empty or very short, use conservative defaults
        if not instruction or len(instruction) < 20:
            recommendations['recommended_depth'] = 2
            recommendations['recommended_pages'] = 10
            return recommendations
        
        try:
            # Use the LLM to analyze the instruction
            prompt = f"""
Analyze this web scraping instruction and recommend optimal parameters:
"{instruction}"

Determine:
1. The appropriate depth for link following (1-5)
2. The appropriate number of pages to crawl (5-50)
3. Whether JavaScript rendering is likely needed (true/false)
4. The complexity of the extraction task (low, medium, high)

Return your analysis as a JSON object with these keys:
recommended_depth, recommended_pages, requires_javascript, complexity
"""
            
            response = self.llm_handler.client.chat.completions.create(
                model=self.llm_handler.model,
                messages=[
                    {"role": "system", "content": "You analyze web scraping instructions to determine optimal parameters."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate and apply the LLM's recommendations
            if 'recommended_depth' in result:
                depth = int(result['recommended_depth'])
                recommendations['recommended_depth'] = min(max(depth, 1), 5)  # Clamp between 1-5
                
            if 'recommended_pages' in result:
                pages = int(result['recommended_pages'])
                recommendations['recommended_pages'] = min(max(pages, 5), 50)  # Clamp between 5-50
                
            if 'requires_javascript' in result:
                recommendations['requires_javascript'] = bool(result['requires_javascript'])
                
            if 'complexity' in result:
                recommendations['complexity'] = result['complexity']
                
        except Exception as e:
            logger.warning(f"Error analyzing instruction: {str(e)}")
            # Fall back to defaults if analysis fails
            
        return recommendations
    
    def map_site_structure(
        self,
        url: str,
        max_pages: int = 20,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Create a map of the site structure before detailed crawling.
        
        Args:
            url: The starting URL to map
            max_pages: Maximum number of pages to include in the map
            max_depth: Maximum depth of links to follow
            
        Returns:
            A dictionary representing the site structure
        """
        logger.info(f"Mapping site structure for {url}")
        
        # Use a lightweight crawler for mapping
        crawler = Crawler(
            user_agent=self.crawler.user_agent,
            respect_robots=self.crawler.respect_robots,
            rate_limit=0.5  # Faster rate limit for mapping
        )
        
        # Track visited URLs and their depths
        visited = set()
        pages_by_depth = {url: 0}
        site_map = {
            "base_url": url,
            "pages": [],
            "structure": {}
        }
        
        links_to_visit = [url]
        
        while links_to_visit and len(visited) < max_pages:
            current_url = links_to_visit.pop(0)
            
            if current_url in visited:
                continue
            
            current_depth = pages_by_depth.get(current_url, 0)
            if current_depth > max_depth:
                continue
            
            visited.add(current_url)
            
            try:
                logger.debug(f"Mapping page: {current_url}")
                page_content = crawler.fetch_page(current_url)
                
                # Add to site map
                page_info = {
                    "url": current_url,
                    "title": page_content.get('title', ''),
                    "depth": current_depth,
                    "outgoing_links": len(page_content.get('links', [])),
                    "content_size": len(page_content.get('text', ''))
                }
                site_map["pages"].append(page_info)
                
                # Update structure
                if current_depth not in site_map["structure"]:
                    site_map["structure"][current_depth] = []
                site_map["structure"][current_depth].append(current_url)
                
                # Find more links if not at max depth
                if current_depth < max_depth:
                    new_links = []
                    for link in page_content.get('links', []):
                        link_url = link['url']
                        # Only include links from the same domain
                        if link_url.startswith(url) or is_same_domain(url, link_url):
                            new_links.append(link_url)
                    
                    # Add new links to queue
                    for link in new_links:
                        if link not in visited and link not in links_to_visit:
                            links_to_visit.append(link)
                            pages_by_depth[link] = current_depth + 1
            
            except Exception as e:
                logger.error(f"Error mapping {current_url}: {str(e)}")
        
        # Use LLM to analyze the site structure
        try:
            # Create a text representation of the site structure
            structure_text = []
            for depth, urls in sorted(site_map["structure"].items()):
                structure_text.append(f"Depth {depth}: {len(urls)} pages")
                if depth < 2:  # Only show details for first two levels
                    for url in urls[:5]:  # Limit to 5 example URLs per level
                        page = next((p for p in site_map["pages"] if p["url"] == url), None)
                        if page:
                            structure_text.append(f"  - {page['title']} ({url})")
            
            structure_summary = "\n".join(structure_text)
            
            prompt = f"""
Analyze this website structure:

{structure_summary}

Provide strategic insights for crawling this website effectively. Include:
1. The main sections or content areas identified
2. Recommended crawling priority (which parts to focus on)
3. Potential challenges in extracting information
4. Suggested depth for thorough crawling

Return your analysis as JSON with these keys: sections, priorities, challenges, recommended_depth
"""
            
            response = self.llm_handler.client.chat.completions.create(
                model=self.llm_handler.model,
                messages=[
                    {"role": "system", "content": "You analyze website structures to optimize web crawling."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            insights = json.loads(content)
            site_map["analysis"] = insights
        
        except Exception as e:
            logger.error(f"Error analyzing site structure: {str(e)}")
        
        return site_map
    
    def intelligent_scrape(
        self, 
        url: str, 
        instructions: str, 
        max_pages: int = 20,
        max_depth: int = 3,
        dynamic: bool = False,
        map_first: bool = True,
        use_memory: bool = True,
        cluster_results: bool = True,
        auth_options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Enhanced scraping with site mapping, memory, and content clustering.
        
        Args:
            url: The starting URL to scrape
            instructions: Natural language instructions for what to extract
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum depth of links to follow
            dynamic: Whether to use a browser to render JavaScript
            map_first: Whether to map the site structure before detailed crawling
            use_memory: Whether to use memory for content extraction
            cluster_results: Whether to cluster the results by topic
            auth_options: Authentication options if needed
            
        Returns:
            A dictionary with the scraped content and metadata
        """
        results = {
            "base_url": url,
            "instructions": instructions,
            "documents": [],
            "stats": {
                "pages_visited": 0,
                "pages_with_content": 0,
                "total_extraction_time": 0
            },
            "metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "parameters": {
                    "max_pages": max_pages,
                    "max_depth": max_depth,
                    "dynamic": dynamic,
                    "map_first": map_first,
                    "use_memory": use_memory,
                    "cluster_results": cluster_results,
                    "auth_required": auth_options is not None
                }
            }
        }
        
        # Step 1: Map the site structure if requested
        site_map = None
        if map_first:
            site_map = self.map_site_structure(url, max_pages=min(20, max_pages), max_depth=min(2, max_depth))
            results["site_map"] = site_map
            
            # Adjust crawl parameters based on site analysis
            if "analysis" in site_map and "recommended_depth" in site_map["analysis"]:
                recommended_depth = site_map["analysis"]["recommended_depth"]
                if isinstance(recommended_depth, int) and recommended_depth < max_depth:
                    logger.info(f"Adjusting max depth from {max_depth} to {recommended_depth} based on site analysis")
                    max_depth = recommended_depth
        
        # Step 2: Perform the scrape with enhanced understanding
        start_time = time.time()
        memory = None if not use_memory else {"summaries": [], "key_concepts": set(), "entities": set(), "contradictions": []}
        discovered_topics = []
        
        # Choose the appropriate crawler
        if auth_options:
            logger.info("Using authenticated crawler")
            crawler_class = AuthenticatedCrawler
            crawler_kwargs = {
                "user_agent": self.crawler.user_agent,
                "respect_robots": self.crawler.respect_robots,
                "rate_limit": self.crawler.rate_limit,
                **auth_options
            }
        elif dynamic:
            logger.info("Using dynamic crawler with JavaScript rendering")
            crawler_class = DynamicCrawler
            crawler_kwargs = {
                "user_agent": self.crawler.user_agent,
                "respect_robots": self.crawler.respect_robots,
                "rate_limit": self.crawler.rate_limit
            }
        else:
            logger.info("Using standard crawler")
            crawler_class = Crawler
            crawler_kwargs = {
                "user_agent": self.crawler.user_agent,
                "respect_robots": self.crawler.respect_robots,
                "rate_limit": self.crawler.rate_limit
            }
        
        # Initialize crawler inside a context manager if it supports it
        with_context = hasattr(crawler_class, "__enter__") and hasattr(crawler_class, "__exit__")
        if with_context:
            with crawler_class(**crawler_kwargs) as crawler:
                results = self._perform_intelligent_scrape(
                    url, instructions, crawler, max_pages, max_depth,
                    use_memory, memory, discovered_topics, results
                )
        else:
            crawler = crawler_class(**crawler_kwargs)
            results = self._perform_intelligent_scrape(
                url, instructions, crawler, max_pages, max_depth,
                use_memory, memory, discovered_topics, results
            )
        
        # Calculate total time
        end_time = time.time()
        results["stats"]["total_extraction_time"] = end_time - start_time
        
        # Process documents
        processed_documents = self.processor.process_documents(results["documents"], instructions)
        
        # Cluster results if requested
        if cluster_results and processed_documents:
            # Inject API key to processor for clustering
            self.processor.api_key = self.api_key
            clusters = self.processor.cluster_documents(processed_documents)
            results["clusters"] = clusters
        else:
            results["processed_documents"] = processed_documents
        
        # Include discovered topics
        results["discovered_topics"] = discovered_topics
        
        logger.info(f"Intelligent scraping complete. Extracted content from {results['stats']['pages_with_content']} pages.")
        return results
    
    def _perform_intelligent_scrape(
        self,
        url: str,
        instructions: str,
        crawler: Union[Crawler, DynamicCrawler, AuthenticatedCrawler],
        max_pages: int,
        max_depth: int,
        use_memory: bool,
        memory: Dict[str, Any],
        discovered_topics: List[str],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Internal method to perform the intelligent scraping.
        
        This method is called by intelligent_scrape and handles the actual crawling logic.
        """
        # Start with the main URL
        visited_urls = set()
        links_to_visit = [url]
        pages_by_depth = {url: 0}
        
        # Track relevance of each visited page
        page_relevance = {}
        
        while links_to_visit and len(visited_urls) < max_pages:
            current_url = links_to_visit.pop(0)
            
            if current_url in visited_urls:
                continue
            
            current_depth = pages_by_depth.get(current_url, 0)
            if current_depth > max_depth:
                continue
            
            visited_urls.add(current_url)
            results["stats"]["pages_visited"] += 1
            
            try:
                logger.info(f"Fetching page {len(visited_urls)}/{max_pages}: {current_url}")
                
                # Check if we need to handle dynamic crawler differently
                if isinstance(crawler, DynamicCrawler):
                    page_content = crawler.fetch_page(current_url)
                else:
                    page_content = crawler.fetch_page(current_url)
                
                # Extract content with memory if enabled
                if use_memory:
                    relevant_content = self.llm_handler.extract_with_memory(page_content, instructions, memory)
                else:
                    relevant_content = self.llm_handler.extract_relevant_content(page_content, instructions)
                
                # Save relevance score
                page_relevance[current_url] = relevant_content.get('relevance_score', 0)
                
                # Only save if relevant
                if relevant_content.get('relevance_score', 0) > 0:
                    results["stats"]["pages_with_content"] += 1
                    document = self.processor.create_document(current_url, relevant_content)
                    results["documents"].append(document)
                
                # Find more links with enhanced prioritization
                if current_depth < max_depth:
                    links_result = self.llm_handler.enhanced_identify_relevant_links(
                        page_content, 
                        current_url, 
                        instructions,
                        visited_links=list(visited_urls),
                        current_depth=current_depth,
                        max_depth=max_depth,
                        discovered_topics=discovered_topics
                    )
                    
                    # Update discovered topics
                    if "new_topics" in links_result:
                        discovered_topics.extend(links_result["new_topics"])
                        # Remove duplicates while preserving order
                        discovered_topics = list(dict.fromkeys(discovered_topics))
                    
                    # Add new links to queue
                    for link in links_result.get("links", []):
                        if link not in visited_urls and link not in links_to_visit:
                            links_to_visit.append(link)
                            pages_by_depth[link] = current_depth + 1
            
            except Exception as e:
                logger.error(f"Error processing {current_url}: {str(e)}")
        
        return results
    
    def _perform_scrape(
        self,
        url: str,
        instructions: str,
        crawler: Union[Crawler, DynamicCrawler],
        max_pages: int,
        wait_for_selector: Optional[str] = None,
        wait_time: int = 5000,
        max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Internal method to perform the actual scraping.
        
        Args:
            url: The starting URL to scrape
            instructions: Natural language instructions for what to extract
            crawler: The crawler instance to use
            max_pages: Maximum number of pages to crawl
            wait_for_selector: Optional CSS selector to wait for when using dynamic mode
            wait_time: Time to wait for dynamic content in ms
            max_depth: Maximum depth of links to follow
            
        Returns:
            A list of structured documents
        """
        # Initial crawl of the main page
        if isinstance(crawler, DynamicCrawler):
            content = crawler.fetch_page(
                url=url,
                wait_for_selector=wait_for_selector,
                wait_time=wait_time
            )
        else:
            content = crawler.fetch_page(url)
        
        # Let the LLM analyze the content and decide what's relevant
        relevant_content = self.llm_handler.extract_relevant_content(content, instructions)
        
        # Identify links to follow based on instructions
        links_to_follow = self.llm_handler.identify_relevant_links(content, url, instructions)
        
        # Create initial document
        documents = []
        if relevant_content.get('relevance_score', 0) > 0:
            documents.append(self.processor.create_document(url, relevant_content))
        
        # Track visited URLs to avoid duplicates
        visited_urls = {url}
        
        # Track current page depth
        pages_by_depth = {url: 0}
        
        # Follow links if we haven't reached the max pages
        pages_visited = 1
        while links_to_follow and pages_visited < max_pages:
            next_link = links_to_follow.pop(0)
            
            # Skip if we've already visited this URL
            if next_link in visited_urls:
                continue
            
            # Skip if we've reached max depth for this link
            current_depth = pages_by_depth.get(next_link, max_depth + 1)
            if current_depth >= max_depth:
                continue
            
            visited_urls.add(next_link)
            
            try:
                logger.info(f"Fetching page {pages_visited + 1}/{max_pages}: {next_link}")
                
                # Fetch the page
                if isinstance(crawler, DynamicCrawler):
                    page_content = crawler.fetch_page(
                        url=next_link,
                        wait_for_selector=wait_for_selector,
                        wait_time=wait_time
                    )
                else:
                    page_content = crawler.fetch_page(next_link)
                
                # Extract relevant content
                relevant_page_content = self.llm_handler.extract_relevant_content(page_content, instructions)
                
                # Only create a document if relevant content was found
                if relevant_page_content.get('relevance_score', 0) > 0:
                    documents.append(self.processor.create_document(next_link, relevant_page_content))
                
                # Find more links on this page
                if current_depth < max_depth:
                    new_links = self.llm_handler.identify_relevant_links(page_content, next_link, instructions)
                    
                    # Add depth information for new links
                    for link in new_links:
                        if link not in pages_by_depth:
                            pages_by_depth[link] = current_depth + 1
                    
                    # Add new links to the queue
                    for link in new_links:
                        if link not in visited_urls and link not in links_to_follow:
                            links_to_follow.append(link)
                
                pages_visited += 1
                
            except Exception as e:
                # Log the error but continue with other links
                logger.error(f"Error processing {next_link}: {str(e)}")
        
        # Final processing of documents
        processed_documents = self.processor.process_documents(documents, instructions)
        
        logger.info(f"Scraping complete. Extracted {len(processed_documents)} documents.")
        return processed_documents
    
    def batch_scrape(
        self,
        urls: List[str],
        instructions: str = "",
        max_pages_per_site: int = 5,
        **kwargs
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape multiple websites in batch.
        
        Args:
            urls: List of URLs to scrape
            instructions: Natural language instructions for what to extract
            max_pages_per_site: Maximum number of pages to crawl per site
            **kwargs: Additional arguments to pass to scrape()
            
        Returns:
            Dictionary mapping URLs to their respective results
        """
        results = {}
        for url in urls:
            try:
                results[url] = self.scrape(url, instructions, max_pages=max_pages_per_site, **kwargs)
            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                results[url] = []
        
        return results
    
    def export(self, documents: List[Dict[str, Any]], format: Optional[str] = None) -> str:
        """
        Export documents in the specified format.
        
        Args:
            documents: List of documents to export
            format: Output format (json, csv, markdown)
            
        Returns:
            String representation of the documents in the specified format
        """
        format = format or self.output_format
        return self.processor.export_documents(documents, format)
    
    def save(self, documents: List[Dict[str, Any]], filename: str, format: Optional[str] = None) -> None:
        """
        Save documents to a file.
        
        Args:
            documents: List of documents to save
            filename: Name of the file to save to
            format: Output format (json, csv, markdown)
        """
        format = format or self.output_format
        
        # Infer format from filename if not specified
        if not format:
            if filename.endswith('.json'):
                format = 'json'
            elif filename.endswith('.csv'):
                format = 'csv'
            elif filename.endswith('.md'):
                format = 'markdown'
            else:
                format = 'json'  # Default to JSON
        
        # Export the documents
        exported = self.export(documents, format)
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(exported)
        
        logger.info(f"Saved {len(documents)} documents to {filename}")