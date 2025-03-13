
import os
from rufus import RufusClient# Set API key
api_key = os.getenv("RUFUS_API_KEY")
if not api_key:
    print("Error: RUFUS_API_KEY environment variable not set")
    exit(1)

# Create client
client = RufusClient(api_key=api_key)

# Test a very simple extraction
print("Starting simple web extraction...")
documents = client.scrape(
    url="https://example.com",
    instructions="Extract the main content of this page",
    max_pages=1  # Just one page for testing
)

print(f"Extracted {len(documents)} documents")
if documents:
    print(f"First document title: {documents[0].get('title', 'No title')}")
    print(f"First document relevance: {documents[0].get('relevance_score', 0)}")

client.save(documents, "test_output.json")
print("Results saved to test_output.json")