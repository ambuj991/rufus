"""
Example demonstrating the enhanced features of Rufus
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

# Create the enhanced Rufus client - disabling robots.txt restriction for testing
# NOTE: In production, you should respect robots.txt unless you have explicit permission
client = RufusClient(
    api_key=api_key,
    respect_robots=False,  # Only for testing purposes
    rate_limit=1.0  # Be polite with request frequency
)

# Example 1: Basic intelligent scraping
def example_basic_intelligent_scrape():
    print("=== Example 1: Basic Intelligent Scraping ===")
    
    # Define your instructions - using Wikipedia which is more scraper-friendly
    instructions = "We're writing an article about Python programming language. Extract information about its history, features, design philosophy, usage in different domains, and community."
    
    print(f"Starting intelligent scrape of Python Wikipedia page with instructions: {instructions}")
    
    # Execute the enhanced scraping
    results = client.intelligent_scrape(
        url="https://en.wikipedia.org/wiki/Python_(programming_language)",
        instructions=instructions,
        max_pages=10,
        max_depth=2,
        map_first=True,    # First map the site structure to plan the crawl
        use_memory=True,   # Use memory to avoid duplication and build coherent understanding
        cluster_results=True  # Organize results into topic clusters
    )
    
    # Print statistics
    print(f"\nScraping complete!")
    print(f"Pages visited: {results['stats']['pages_visited']}")
    print(f"Pages with relevant content: {results['stats']['pages_with_content']}")
    print(f"Total extraction time: {results['stats']['total_extraction_time']:.2f} seconds")
    
    # Print discovered topics
    print("\nDiscovered Topics:")
    for topic in results['discovered_topics']:
        print(f"  - {topic}")
    
    # Print content clusters
    if 'clusters' in results:
        print("\nContent Clusters:")
        for cluster_name, docs in results['clusters'].items():
            print(f"  {cluster_name} ({len(docs)} documents)")
    
    # Save the results
    with open("python_wiki_data.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nSaved results to python_wiki_data.json")


# Example 2: Site mapping
def example_site_mapping():
    print("\n=== Example 2: Site Mapping ===")
    
    print("Mapping site structure...")
    site_map = client.map_site_structure(
        url="https://en.wikipedia.org/wiki/Python_(programming_language)",
        max_pages=15,
        max_depth=2
    )
    
    # Print site map insights
    print("\nSite Structure Analysis:")
    if "analysis" in site_map:
        analysis = site_map["analysis"]
        
        print("\nMain Sections:")
        for section in analysis.get("sections", []):
            print(f"  - {section}")
        
        print("\nRecommended Priorities:")
        for priority in analysis.get("priorities", []):
            print(f"  - {priority}")
        
        print("\nPotential Challenges:")
        for challenge in analysis.get("challenges", []):
            print(f"  - {challenge}")
        
        print(f"\nRecommended Crawl Depth: {analysis.get('recommended_depth', 'Not specified')}")
    
    # Save the site map
    with open("python_wiki_site_map.json", "w") as f:
        json.dump(site_map, f, indent=2)
    
    print("\nSaved site map to python_wiki_site_map.json")


# Example 3: Authenticated scraping (demonstration with dummy credentials)
def example_authenticated_scraping():
    print("\n=== Example 3: Authenticated Scraping ===")
    
    # Define auth options (these are dummy credentials, replace with real ones)
    auth_options = {
        "auth_type": "form",
        "login_url": "https://example.com/login",
        "auth_credentials": {
            "username": "demo_user",
            "password": "demo_password"
        }
    }
    
    print("Note: This is a demonstration of the authentication feature.")
    print("Using dummy credentials that won't actually work.")
    print("Replace with real credentials for your target site.")
    
    # In a real scenario, you would do:
    """
    results = client.intelligent_scrape(
        url="https://example.com/dashboard",
        instructions="Extract user account information and recent activities",
        max_pages=10,
        auth_options=auth_options
    )
    """
    
    # For the demo, just print the options
    print("\nAuthentication Options:")
    print(json.dumps(auth_options, indent=2))


# Example 4: Deep nested link exploration with memory
def example_deep_exploration():
    print("\n=== Example 4: Deep Nested Link Exploration ===")
    
    # Define instructions for deep exploration
    instructions = "Create a comprehensive overview of programming languages, their features, histories, and use cases. Focus on Python, JavaScript, Java, C++, and other major languages."
    
    print(f"Starting deep exploration with instructions: {instructions}")
    
    # Execute deep exploration with higher depth limit
    results = client.intelligent_scrape(
        url="https://en.wikipedia.org/wiki/Programming_language",
        instructions=instructions,
        max_pages=20,
        max_depth=3,  # Deeper exploration
        use_memory=True,  # Critical for building coherent understanding
        cluster_results=True
    )
    
    # Print statistics
    print(f"\nDeep exploration complete!")
    print(f"Pages visited: {results['stats']['pages_visited']}")
    print(f"Pages with relevant content: {results['stats']['pages_with_content']}")
    
    # Save detailed results
    with open("programming_languages_deep.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Also save as markdown for easy reading
    documents = results.get("processed_documents", [])
    if documents:
        markdown = client.export(documents, format="markdown")
        with open("programming_languages_deep.md", "w") as f:
            f.write(markdown)
        print("\nSaved results to programming_languages_deep.json and programming_languages_deep.md")


# Run the examples
if __name__ == "__main__":
    # Choose which examples to run
    print("Which example would you like to run?")
    print("1. Basic Intelligent Scraping (Python Wikipedia)")
    print("2. Site Mapping")
    print("3. Authenticated Scraping Demo")
    print("4. Deep Nested Link Exploration (Programming Languages)")
    print("5. Run All Examples")
    
    choice = input("Enter your choice (1-5): ")
    
    if choice == '1' or choice == '5':
        example_basic_intelligent_scrape()
    if choice == '2' or choice == '5':
        example_site_mapping()
    if choice == '3' or choice == '5':
        example_authenticated_scraping()
    if choice == '4' or choice == '5':
        example_deep_exploration()