# rufus-ai-web-extraction: Intelligent Web Data Extraction for LLMs

rufus-ai-web-extraction is an AI-driven web crawler and data extraction tool designed specifically for feeding structured data into Large Language Models (LLMs) and Retrieval Augmented Generation (RAG) systems. It uses AI to dynamically determine what content is relevant based on natural language instructions, eliminating the need for custom web scraping tools that break when site structures change.

## 🌟 Features

- 🧠 **AI-Driven Extraction**: Intelligently extracts only the content that matches your instructions
- 🕸️ **Smart Crawling**: Automatically follows links that are likely to contain relevant information
- 🔍 **Selective Relevance**: Assigns relevance scores to ensure you only get what matters
- 📊 **Structured Output**: Exports data in formats ready for RAG systems (JSON, CSV, Markdown)
- 🌐 **Dynamic Content Support**: Handles JavaScript-rendered pages using a headless browser
- 🧩 **Topic Clustering**: Organizes extracted content into meaningful topic clusters
- 🔒 **Respectful Crawling**: Built-in rate limiting and robots.txt compliance
- 🤝 **Authentication Support**: Handle sites requiring login (basic, form-based)
- 🤖 **RAG Integration**: Direct integration with popular frameworks like LangChain and LlamaIndex
- 🚀 **CLI Interface**: Easy-to-use command line tool for quick extractions

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Advanced Usage](#advanced-usage)
- [Command Line Interface](#command-line-interface)
- [Integrating with RAG Systems](#integrating-with-rag-systems)
- [Example Use Cases](#example-use-cases)
- [How It Works](#how-it-works)
- [Architecture](#architecture)

## 🔧 Installation

```bash
# From PyPI
pip install rufus-ai-web-extraction

# From TestPyPI
pip install -i https://test.pypi.org/simple/ rufus-ai-web-extraction==0.1.0

# With support for dynamic content (JS-rendered pages)
pip install rufus-ai-web-extraction[dynamic]

# With RAG framework integrations
pip install rufus-ai-web-extraction[rag]

# Development installation with testing tools
pip install rufus-ai-web-extraction[dev]

# Full installation with all features
pip install rufus-ai-web-extraction[dynamic,rag,dev]
```

For dynamic content support, you'll also need to install browser dependencies:

```bash
# After installing rufus-ai-web-extraction[dynamic]
python -m playwright install
```

## 🚀 Quick Start

```python
from rufus import RufusClient
import os

# Initialize with your API key
client = RufusClient(api_key=os.getenv('RUFUS_API_KEY'))

# Extract information based on instructions
instructions = "Find information about product features and pricing."
documents = client.scrape("https://example.com", instructions=instructions)

# Save the results
client.save(documents, "output.json")
```

### Using the Command Line

```bash
# Set your API key as an environment variable
export RUFUS_API_KEY=your_openai_api_key

# Run a simple extraction
rufus_cli.py --url https://example.com --instructions "Extract product information and pricing" --output results
```

## 🧩 Core Concepts

rufus-ai-web-extraction is built around several key concepts that make it powerful and flexible:

1. **Natural Language Instructions**: Instead of specifying CSS selectors or XPaths, you simply describe what information you need in plain English.

2. **Relevance Scoring**: Each extracted piece of content is assigned a relevance score (0-10) based on how well it matches your instructions.

3. **Intelligent Link Following**: Rufus analyzes links on each page and follows those most likely to contain relevant information.

4. **Document Structure**: Extracted content is organized into structured documents with:
   - Title and URL source
   - Summary of relevant content
   - Key points extracted from the content
   - Relevant sections with their content
   - Metadata including extraction timestamp and relevance score

5. **Memory-Aware Extraction**: When enabled, Rufus remembers what it has already learned to avoid duplicating information and to build a coherent understanding.

## 🔍 Advanced Usage

### Dynamic Content

For websites that load content dynamically with JavaScript:

```python
documents = client.scrape(
    url="https://example.com",
    instructions="Find pricing information",
    dynamic=True,  # Use browser rendering
    max_pages=15,
    max_depth=3
)
```

### Site Mapping

Before detailed crawling, you can map the site structure to understand its organization:

```python
site_map = client.map_site_structure(
    url="https://example.com",
    max_pages=20,
    max_depth=2
)

# Site map contains analysis of the structure
if "analysis" in site_map:
    print("Main sections:", site_map["analysis"].get("sections", []))
    print("Recommended crawl depth:", site_map["analysis"].get("recommended_depth"))
```

### Intelligent Scraping

For more control over the extraction process:

```python
results = client.intelligent_scrape(
    url="https://example.com",
    instructions="Find detailed product specifications and user reviews",
    max_pages=25,
    max_depth=3,
    map_first=True,      # Map the site before crawling
    use_memory=True,     # Use memory for coherent extraction
    cluster_results=True  # Organize results by topic
)

# Access the processed documents
documents = results.get("processed_documents", [])

# Access topic clusters
if "clusters" in results:
    for cluster_name, docs in results["clusters"].items():
        print(f"Cluster: {cluster_name} ({len(docs)} documents)")
```

### Authentication

For sites requiring authentication:

```python
# Basic authentication
documents = client.scrape(
    url="https://example.com/dashboard",
    instructions="Extract account information",
    auth_options={
        "auth_type": "basic",
        "auth_credentials": {
            "username": "user",
            "password": "pass"
        }
    }
)

# Form-based authentication
documents = client.scrape(
    url="https://example.com/dashboard",
    instructions="Extract account information",
    auth_options={
        "auth_type": "form",
        "login_url": "https://example.com/login",
        "auth_credentials": {
            "username": "user",
            "password": "pass"
        }
    }
)
```

### Batch Processing

Process multiple websites at once:

```python
urls = ["https://example.com", "https://another-example.com"]
batch_results = client.batch_scrape(
    urls, 
    instructions="Find contact information",
    max_pages_per_site=10
)

# Process results for each site
for url, documents in batch_results.items():
    print(f"Found {len(documents)} relevant documents on {url}")
    client.save(documents, f"results_{url.replace('://', '_').replace('/', '_')}.json")
```

### Export Formats

Export the extracted data in different formats:

```python
# Export to different formats
json_output = client.export(documents, format='json')
csv_output = client.export(documents, format='csv')
markdown_output = client.export(documents, format='markdown')

# Save directly to file
client.save(documents, "output.json")  # Format inferred from extension
client.save(documents, "output.csv", format="csv")
client.save(documents, "report.md", format="markdown")
```

### Configuration Options

Rufus can be configured with various options:

```python
client = RufusClient(
    api_key="your_api_key",
    user_agent="Custom User Agent",  # Custom user agent
    respect_robots=True,  # Respect robots.txt rules
    rate_limit=2.0,  # Wait time between requests (seconds)
    llm_model="gpt-4",  # LLM model to use
    output_format="json"  # Default output format
)
```

### Error Handling

Rufus provides robust error handling:

```python
from rufus import RufusClient, RufusError, setup_logger

# Enable verbose logging
setup_logger(level="DEBUG", log_file="rufus.log")

try:
    documents = client.scrape("https://example.com", instructions="Find information")
except RufusError as e:
    print(f"Error: {e}")
```

## 💻 Command Line Interface

Rufus includes a powerful command-line interface for quick extractions:

```bash
# Basic usage
rufus_cli.py --url https://example.com --instructions "Extract product information and pricing"

# Advanced options
rufus_cli.py --url https://example.com \
    --instructions "Extract product information and pricing" \
    --output product_data \
    --format markdown \
    --max-pages 20 \
    --max-depth 3 \
    --dynamic \
    --rate-limit 2.0 \
    --verbose

# Interactive mode
rufus_cli.py --interactive
```

## 🔌 Integrating with RAG Systems

### LangChain Integration

```python
from rufus import RufusClient
from rufus.integrations.langchain import create_langchain_documents
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# Extract data
client = RufusClient(api_key="your_api_key")
documents = client.scrape("https://example.com", "Find product documentation")

# Convert to LangChain documents
langchain_docs = create_langchain_documents(documents)

# Create vector store
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(langchain_docs, embeddings)

# Query
results = vectorstore.similarity_search("How do I install the product?")
```

### LlamaIndex Integration

```python
from rufus import RufusClient
from rufus.integrations.llamaindex import create_llamaindex_documents
from llama_index import VectorStoreIndex

# Extract data
client = RufusClient(api_key="your_api_key")
documents = client.scrape("https://example.com", "Find product documentation")

# Convert to LlamaIndex documents
llamaindex_docs = create_llamaindex_documents(documents)

# Create index
index = VectorStoreIndex.from_documents(llamaindex_docs)

# Query
query_engine = index.as_query_engine()
response = query_engine.query("How do I install the product?")
```

## 📚 Example Use Cases

### Building a Company FAQ Chatbot

```python
from rufus import RufusClient

# Initialize Rufus
client = RufusClient(api_key="your_api_key")

# Extract FAQ data
instructions = """
We're making a chatbot for customer support. Extract all FAQ information, 
product details, and troubleshooting guides. Focus on information that would 
help customers resolve common issues and understand product features.
"""

documents = client.scrape(
    url="https://company-website.com", 
    instructions=instructions, 
    max_pages=50,
    max_depth=3
)

# Save for use in a RAG system
client.save(documents, "company_knowledge_base.json")
client.save(documents, "company_knowledge_base.md", format="markdown")
```

### Creating a Research Database

```python
from rufus import RufusClient

# Initialize Rufus
client = RufusClient(api_key="your_api_key")

# Define research topics
research_sites = [
    "https://research-site.edu/topic1",
    "https://research-site.edu/topic2",
    "https://another-site.org/research"
]

# Extract research data
instructions = """
Extract detailed research findings, methodologies, and conclusions.
Focus on quantitative data, experimental results, and key findings.
Include information about authors, publication dates, and research affiliations.
"""

batch_results = client.batch_scrape(
    research_sites, 
    instructions=instructions, 
    max_pages_per_site=20
)

# Export as markdown for review
for site, documents in batch_results.items():
    site_name = site.split('//')[-1].replace('/', '_')
    client.save(documents, f"research_{site_name}.md", format="markdown")
```

### University Program Information Extraction

Extract comprehensive university information:

```python
from rufus import RufusClient

# Initialize Rufus
client = RufusClient(api_key="your_api_key")

# Extract academic programs info
instructions = """
Extract comprehensive information about the academic programs offered by this university.
Include program names, durations, eligibility criteria, course structures, and career outcomes.
"""

documents = client.intelligent_scrape(
    url="https://university-website.edu/academics",
    instructions=instructions,
    max_pages=25,
    max_depth=3,
    use_memory=True,
    cluster_results=True
)

# Save results
client.save(documents.get("processed_documents", []), "university_programs.json")
```

## ⚙️ How It Works

1. **Intelligent Crawling**: Rufus starts at the provided URL and analyzes the page content.
2. **Content Analysis**: The LLM evaluates the content to determine what's relevant based on your instructions.
3. **Link Analysis**: The LLM identifies which links are likely to contain more relevant information.
4. **Selective Extraction**: Only the content that matches your instructions is extracted and structured.
5. **Document Synthesis**: The extracted content is processed into clean, structured documents ready for use in RAG systems.

The entire process is powered by Large Language Models (currently using OpenAI's GPT-4) to provide human-like understanding of both your instructions and the web content.

**Intelligent Link Selection Process:**

```
User Instructions → Page Content Analysis → Link Relevance Prediction → Prioritized Crawling → Content Extraction
```

**Document Processing Pipeline:**

```
Raw HTML → Text Extraction → Relevance Analysis → Key Point Extraction → Document Structuring → Format Conversion
```

## 🏗️ Architecture

Rufus is built with a modular architecture:

- **Client (`RufusClient`)**: Main interface for interacting with Rufus
- **Crawler (`Crawler`, `DynamicCrawler`, `AuthenticatedCrawler`)**: Handles web requests and content extraction
- **LLM Handler (`LLMHandler`)**: Provides AI intelligence for content and link analysis
- **Document Processor (`DocumentProcessor`)**: Structures and formats the extracted data
- **Utils**: Helper functions and error handling

### Component Interaction Flow

```
┌────────┐    ┌───────────┐    ┌────────────┐    ┌──────────────┐
│ Client │───▶│  Crawler  │───▶│ LLM Handler│───▶│ Doc Processor│
└────────┘    └───────────┘    └────────────┘    └──────────────┘
     │              │                 │                  │
     └──────────────┼─────────────────┼──────────────────┘
                    │                 │
                    ▼                 ▼
             ┌─────────────┐   ┌────────────┐
             │ Web Content │   │OpenAI API  │
             └─────────────┘   └────────────┘
```

## 📝 License

MIT License

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
