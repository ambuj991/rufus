"""
Generalized Rufus testing script for any website
"""

from rufus import RufusClient
import os
import json
import time

# Set up your OpenAI API key
api_key = os.getenv("RUFUS_API_KEY")
if not api_key:
    print("Error: RUFUS_API_KEY environment variable not set")
    print("Please set it with: export RUFUS_API_KEY=your_openai_api_key")
    exit(1)

# Create the Rufus client with proper settings for commercial sites
client = RufusClient(
    api_key=api_key,
    respect_robots=True,  # Respect robots.txt (important for commercial sites)
    rate_limit=2.0,  # Be polite with request frequency (2 seconds between requests)
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"  # Use a common user agent
)

def extract_from_website():
    """
    Extract information from any website based on user input.
    """
    # Get user input
    print("=== Rufus Generalized Web Extraction ===")
    url = input("Enter the website URL to scrape: ")
    instructions = input("Enter your instructions (what information to extract): ")
    
    max_pages_input = input("Maximum pages to crawl (default: 10): ")
    max_pages = int(max_pages_input) if max_pages_input.isdigit() else 10
    
    max_depth_input = input("Maximum link depth (default: 2): ")
    max_depth = int(max_depth_input) if max_depth_input.isdigit() else 2
    
    dynamic = input("Use browser rendering for JavaScript? [y/N]: ").lower() == 'y'
    
    print(f"\nStarting extraction from {url} with instructions: {instructions}")
    print(f"Max pages: {max_pages}, Max depth: {max_depth}, Dynamic rendering: {'Enabled' if dynamic else 'Disabled'}")
    
    start_time = time.time()
    
    # Execute the scraping
    try:
        documents = client.scrape(
            url=url,
            instructions=instructions,
            max_pages=max_pages,
            max_depth=max_depth,
            dynamic=dynamic
        )
        
        # Print what we found
        print(f"\nExtraction complete!")
        print(f"Extracted {len(documents)} relevant documents:")
        
        for i, doc in enumerate(documents):
            print(f"  {i+1}. {doc.get('title', 'Untitled')} (Relevance: {doc.get('relevance_score', 0)}/10)")
            if 'key_points' in doc and doc['key_points']:
                print(f"     Key points: {len(doc['key_points'])}")
                for j, point in enumerate(doc['key_points'][:3]):  # Show first 3 key points
                    print(f"       • {point}")
        
        # Save the results
        output_file = input("\nEnter filename to save results (default: extracted_data): ") or "extracted_data"
        client.save(documents, f"{output_file}.json")
        print(f"\nSaved results to {output_file}.json")
        
        # Also save as markdown for easy reading
        client.save(documents, f"{output_file}.md", format="markdown")
        print(f"Saved readable version to {output_file}.md")
        
        elapsed_time = time.time() - start_time
        print(f"\nTotal processing time: {elapsed_time:.2f} seconds")
        
    except Exception as e:
        print(f"Error during extraction: {str(e)}")

if __name__ == "__main__":
    extract_from_website()