#!/usr/bin/env python
"""
Rufus CLI - Universal Web Extraction Tool

A command-line interface for extracting structured data from any website
using natural language instructions.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List
import time

try:
    from rufus import RufusClient, RufusError, setup_logger
except ImportError:
    print("Error: Rufus package not found. Make sure it's installed.")
    print("Install with: pip install rufus")
    sys.exit(1)

def setup_argparse() -> argparse.ArgumentParser:
    """Set up command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Rufus - Intelligent Web Data Extraction Tool",
        epilog="Example: rufus_cli.py --url https://example.com --instructions 'Extract product information and pricing'"
    )
    
    # Required arguments
    parser.add_argument("--url", "-u", type=str, required=True,
                        help="URL of the website to scrape")
    
    # Optional arguments
    parser.add_argument("--instructions", "-i", type=str, default="",
                        help="Natural language instructions for what to extract")
    parser.add_argument("--output", "-o", type=str, default="rufus_output",
                        help="Base filename for output (without extension)")
    parser.add_argument("--format", "-f", type=str, choices=["json", "markdown", "csv", "all"], default="all",
                        help="Output format(s)")
    parser.add_argument("--max-pages", type=int, default=15,
                        help="Maximum number of pages to crawl")
    parser.add_argument("--max-depth", type=int, default=3,
                        help="Maximum depth of links to follow")
    parser.add_argument("--dynamic", action="store_true",
                        help="Use browser rendering for JavaScript-heavy sites")
    parser.add_argument("--ignore-robots", action="store_true",
                        help="Ignore robots.txt restrictions (use responsibly)")
    parser.add_argument("--rate-limit", type=float, default=1.0,
                        help="Time to wait between requests in seconds")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose logging")
    parser.add_argument("--log-file", type=str,
                        help="File to write logs to")
    parser.add_argument("--interactive", action="store_true",
                        help="Run in interactive mode with prompts")
    
    return parser

def interactive_mode() -> Dict[str, Any]:
    """Run interactive mode to get parameters from user."""
    print("\n=== Rufus Interactive Mode ===")
    print("Enter the details for your extraction task:")
    
    # Get basic parameters
    url = input("Website URL to scrape: ")
    instructions = input("What information would you like to extract? ")
    
    # Get advanced parameters
    print("\nAdvanced options (press Enter for defaults):")
    
    output = input("Output filename base (default: 'rufus_output'): ")
    if not output:
        output = "rufus_output"
    
    format_input = input("Output format [json/markdown/csv/all] (default: all): ")
    if not format_input:
        format_input = "all"
    
    max_pages_input = input("Maximum pages to crawl (default: 15): ")
    max_pages = int(max_pages_input) if max_pages_input.isdigit() else 15
    
    max_depth_input = input("Maximum link depth (default: 3): ")
    max_depth = int(max_depth_input) if max_depth_input.isdigit() else 3
    
    dynamic = input("Use browser rendering for JavaScript? [y/N]: ").lower() == 'y'
    ignore_robots = input("Ignore robots.txt restrictions? [y/N]: ").lower() == 'y'
    
    rate_limit_input = input("Rate limit in seconds (default: 1.0): ")
    rate_limit = float(rate_limit_input) if rate_limit_input and rate_limit_input.replace('.', '', 1).isdigit() else 1.0
    
    return {
        "url": url,
        "instructions": instructions,
        "output": output,
        "format": format_input,
        "max_pages": max_pages,
        "max_depth": max_depth,
        "dynamic": dynamic,
        "ignore_robots": ignore_robots,
        "rate_limit": rate_limit,
        "verbose": True
    }

def save_results(client: RufusClient, documents: List[Dict[str, Any]], 
                output_base: str, formats: List[str]) -> None:
    """Save extraction results in specified formats."""
    success_messages = []
    
    for fmt in formats:
        try:
            output_file = f"{output_base}.{fmt if fmt != 'markdown' else 'md'}"
            client.save(documents, output_file, format=fmt)
            success_messages.append(f"Saved {fmt} output to {output_file}")
        except Exception as e:
            print(f"Error saving {fmt} output: {str(e)}")
    
    return success_messages

def print_extraction_summary(documents: List[Dict[str, Any]]) -> None:
    """Print a summary of the extracted information."""
    print("\n=== Extraction Summary ===")
    print(f"Total documents: {len(documents)}")
    
    if not documents:
        print("No documents were extracted.")
        return
    
    # Check if there was an error
    if 'error' in documents[0]:
        print(f"Error during extraction: {documents[0]['error']}")
        return
    
    # Print document information
    print("\nExtracted documents:")
    for i, doc in enumerate(documents[:5]):  # Show first 5 documents
        print(f"  {i+1}. {doc.get('title', 'Untitled')} (Relevance: {doc.get('relevance_score', 0)}/10)")
        if 'key_points' in doc and doc['key_points']:
            print(f"     Key points: {len(doc['key_points'])}")
            for j, point in enumerate(doc['key_points'][:3]):  # Show first 3 key points
                print(f"       • {point}")
    
    if len(documents) > 5:
        print(f"  ... and {len(documents) - 5} more documents")
    
    # Print extraction metadata if available
    if 'extraction_metadata' in documents[0]:
        metadata = documents[0]['extraction_metadata']
        print("\nExtraction details:")
        if 'total_pages_visited' in metadata:
            print(f"  Pages visited: {metadata['total_pages_visited']}")
        if 'extraction_time' in metadata:
            print(f"  Extraction time: {metadata['extraction_time']:.2f} seconds")

def main():
    """Main entry point for the Rufus CLI."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    # If interactive mode is selected, get parameters from user
    if args.interactive:
        params = interactive_mode()
    else:
        params = vars(args)
    
    # Set up logging
    log_level = "DEBUG" if params.get("verbose") else "INFO"
    log_file = params.get("log_file")
    setup_logger(level=log_level, log_file=log_file)
    
    # Get API key
    api_key = os.getenv("RUFUS_API_KEY")
    if not api_key:
        print("Error: RUFUS_API_KEY environment variable not set")
        print("Please set it with: export RUFUS_API_KEY=your_openai_api_key")
        sys.exit(1)
    
    # Initialize client
    client = RufusClient(
        api_key=api_key,
        respect_robots=not params.get("ignore_robots", False),
        rate_limit=params.get("rate_limit", 1.0)
    )
    
    # Display extraction parameters
    print("\n=== Rufus Extraction Task ===")
    print(f"URL: {params['url']}")
    print(f"Instructions: {params['instructions']}")
    print(f"Max pages: {params['max_pages']}")
    print(f"Max depth: {params['max_depth']}")
    print(f"Dynamic rendering: {'Enabled' if params.get('dynamic') else 'Disabled'}")
    print(f"Respect robots.txt: {'No' if params.get('ignore_robots') else 'Yes'}")
    print(f"Rate limit: {params.get('rate_limit', 1.0)} seconds")
    
    # Start extraction
    print("\nStarting extraction...")
    start_time = time.time()
    
    try:
        # Use the generalized scrape method
        documents = client.scrape(
            url=params['url'],
            instructions=params['instructions'],
            max_pages=params['max_pages'],
            max_depth=params['max_depth'],
            dynamic=params.get('dynamic', False),
            respect_robots=not params.get('ignore_robots', False),
            rate_limit=params.get('rate_limit', 1.0)
        )
        
        # Save results in the specified format(s)
        formats = params['format'].split(',') if ',' in params['format'] else [params['format']]
        if 'all' in formats:
            formats = ['json', 'markdown', 'csv']
        
        success_messages = save_results(client, documents, params['output'], formats)
        
        # Print extraction summary
        print_extraction_summary(documents)
        
        # Print success messages
        for msg in success_messages:
            print(msg)
        
        # Print total time
        elapsed_time = time.time() - start_time
        print(f"\nTotal processing time: {elapsed_time:.2f} seconds")
        
    except RufusError as e:
        print(f"Rufus extraction error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()