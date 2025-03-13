"""
Example demonstrating the enhanced Rufus features on NMIMS University website
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

# Create the enhanced Rufus client - with polite settings
client = RufusClient(
    api_key=api_key,
    respect_robots=True,  # Respect robots.txt
    rate_limit=2.0,  # 2 seconds between requests to be polite
    user_agent="Educational Research Bot (academic research project)" # Custom user agent
)

def extract_academic_programs():
    """
    Extract information about academic programs from NMIMS.
    """
    print("=== Extracting Academic Programs from NMIMS ===")
    
    # Define specific instructions for what to extract
    instructions = """
    Extract comprehensive information about the academic programs offered by NMIMS University.
    Specifically, I need:
    1. Program names, durations, and eligibility criteria
    2. School/faculty information
    3. Course structures and specializations
    4. Admission processes and requirements
    5. Career outcomes and opportunities
    Focus on MBA programs, engineering programs, and any other major disciplines.
    Organize information by school/faculty and then by program level (undergraduate, postgraduate, doctoral).
    """
    
    print(f"Starting intelligent scrape of NMIMS website with these instructions...")
    
    # First map the site to understand its structure
    print("\nMapping website structure to plan crawling strategy...")
    site_map = client.map_site_structure(
        url="https://nmims.edu/",
        max_pages=15,
        max_depth=2
    )
    
    # Print site structure insights if available
    if "analysis" in site_map and "sections" in site_map["analysis"]:
        print("\nWebsite Structure Analysis:")
        for section in site_map["analysis"].get("sections", []):
            print(f"  - {section}")
    
    # Execute the enhanced scraping
    print("\nBeginning detailed content extraction...")
    results = client.intelligent_scrape(
        url="https://nmims.edu/academics/",  # Start from academics section
        instructions=instructions,
        max_pages=25,
        max_depth=3,
        map_first=False,  # We already mapped the site
        use_memory=True,  # Enable memory for coherent information
        cluster_results=True  # Organize results by topics
    )
    
    # Print statistics
    print(f"\nScraping complete!")
    print(f"Pages visited: {results['stats']['pages_visited']}")
    print(f"Pages with relevant content: {results['stats']['pages_with_content']}")
    print(f"Total extraction time: {results['stats']['total_extraction_time']:.2f} seconds")
    
    # Print discovered topics
    print("\nDiscovered Academic Areas:")
    for topic in results.get('discovered_topics', []):
        print(f"  - {topic}")
    
    # Print content clusters
    if 'clusters' in results:
        print("\nContent Clusters:")
        for cluster_name, docs in results['clusters'].items():
            print(f"  {cluster_name} ({len(docs)} documents)")
    
    # Save the results in multiple formats
    with open("nmims_academic_programs.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Create markdown version for easy reading
    if "processed_documents" in results:
        markdown = client.export(results["processed_documents"], format="markdown")
        with open("nmims_academic_programs.md", "w") as f:
            f.write(markdown)
    
    print("\nSaved results to nmims_academic_programs.json and nmims_academic_programs.md")
    return results

def extract_research_activities():
    """
    Extract information about research at NMIMS.
    """
    print("\n=== Extracting Research Activities from NMIMS ===")
    
    instructions = """
    Extract comprehensive information about research activities at NMIMS University.
    Specifically, I need:
    1. Research centers and their focus areas
    2. Notable research projects and their outcomes
    3. Faculty research interests and specializations
    4. Publications and intellectual contributions
    5. Research partnerships and collaborations
    Focus on current research initiatives, interdisciplinary research, and industry collaborations.
    """
    
    print(f"Starting intelligent scrape for research information...")
    
    # Use more focused crawling on research pages
    results = client.intelligent_scrape(
        url="https://nmims.edu/research/",  # Start from research section if available
        instructions=instructions,
        max_pages=20,
        max_depth=3,
        use_memory=True,
        cluster_results=True
    )
    
    # Print statistics
    print(f"\nResearch information extraction complete!")
    print(f"Pages visited: {results['stats']['pages_visited']}")
    print(f"Pages with relevant content: {results['stats']['pages_with_content']}")
    
    # Save the results
    with open("nmims_research.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Create markdown version
    if "processed_documents" in results:
        markdown = client.export(results["processed_documents"], format="markdown")
        with open("nmims_research.md", "w") as f:
            f.write(markdown)
    
    print("\nSaved results to nmims_research.json and nmims_research.md")
    return results

def extract_campus_information():
    """
    Extract information about NMIMS campuses.
    """
    print("\n=== Extracting Campus Information from NMIMS ===")
    
    instructions = """
    Extract detailed information about all NMIMS University campuses.
    Specifically, I need:
    1. Campus locations and their specific addresses
    2. Facilities available at each campus (libraries, labs, sports, etc.)
    3. Schools and programs offered at each campus
    4. Campus life, housing options, and student activities
    5. Transportation and accessibility information
    Create a comprehensive profile of each campus with distinguishing features.
    """
    
    print(f"Starting intelligent scrape for campus information...")
    
    # Focus on campus-specific pages
    results = client.intelligent_scrape(
        url="https://nmims.edu/about-us/",  # About section likely has campus info
        instructions=instructions,
        max_pages=15,
        max_depth=2,
        use_memory=True,
        cluster_results=True
    )
    
    # Print statistics
    print(f"\nCampus information extraction complete!")
    print(f"Pages visited: {results['stats']['pages_visited']}")
    print(f"Pages with relevant content: {results['stats']['pages_with_content']}")
    
    # Save the results
    with open("nmims_campuses.json", "w") as f:
        json.dump(results, f, indent=2)
    
    if "processed_documents" in results:
        markdown = client.export(results["processed_documents"], format="markdown")
        with open("nmims_campuses.md", "w") as f:
            f.write(markdown)
    
    print("\nSaved results to nmims_campuses.json and nmims_campuses.md")
    return results

def create_combined_report(program_data, research_data, campus_data):
    """
    Create a comprehensive report combining all extracted information.
    """
    print("\n=== Creating Comprehensive NMIMS Report ===")
    
    # Prepare a consolidated dataset
    consolidated = {
        "university_name": "NMIMS University",
        "website": "https://nmims.edu/",
        "extraction_date": time.strftime("%Y-%m-%d"),
        "academic_programs": program_data.get("processed_documents", []),
        "research_activities": research_data.get("processed_documents", []),
        "campuses": campus_data.get("processed_documents", []),
        "topics": list(set(
            program_data.get("discovered_topics", []) + 
            research_data.get("discovered_topics", []) + 
            campus_data.get("discovered_topics", [])
        ))
    }
    
    # Save consolidated JSON
    with open("nmims_comprehensive_report.json", "w") as f:
        json.dump(consolidated, f, indent=2)
    
    # Create a comprehensive markdown report
    try:
        # Use LLM to create a structured report
        from openai import OpenAI
        
        # Initialize OpenAI client
        openai_client = OpenAI(api_key=api_key)
        
        # Create a summary of the collected data for the LLM
        summary = {
            "programs": [doc.get("summary", "") for doc in consolidated["academic_programs"][:5]],
            "research": [doc.get("summary", "") for doc in consolidated["research_activities"][:5]],
            "campuses": [doc.get("summary", "") for doc in consolidated["campuses"][:5]],
        }
        
        # Generate report using LLM
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an educational research analyst creating a comprehensive report."},
                {"role": "user", "content": f"""
                Create a comprehensive markdown report about NMIMS University based on the following extracted data:
                
                ACADEMIC PROGRAMS:
                {summary['programs']}
                
                RESEARCH ACTIVITIES:
                {summary['research']}
                
                CAMPUSES:
                {summary['campuses']}
                
                Structure the report with the following sections:
                1. Executive Summary
                2. Academic Programs Overview
                3. Research and Innovation
                4. Campus Facilities and Infrastructure
                5. Conclusions and Recommendations for Prospective Students
                
                Format the report in markdown with proper headings, lists, and emphasis.
                """}
            ],
            temperature=0.7
        )
        
        # Write the report to a file
        with open("nmims_comprehensive_report.md", "w") as f:
            f.write(response.choices[0].message.content)
        
        print("\nCreated comprehensive report in nmims_comprehensive_report.md")
    
    except Exception as e:
        print(f"Error creating comprehensive report: {str(e)}")
        print("Saving raw consolidated data only.")
    
    print("\nAll extraction tasks completed successfully!")

if __name__ == "__main__":
    print("NMIMS University Information Extraction Tool")
    print("==========================================")
    print("This tool will extract and analyze information from the NMIMS University website.")
    print("Choose an option:")
    print("1. Extract Academic Programs Information")
    print("2. Extract Research Activities Information")
    print("3. Extract Campus Information")
    print("4. Run All Extractions and Create Comprehensive Report")
    
    choice = input("Enter your choice (1-4): ")
    
    program_data = None
    research_data = None
    campus_data = None
    
    if choice == '1' or choice == '4':
        program_data = extract_academic_programs()
    
    if choice == '2' or choice == '4':
        research_data = extract_research_activities()
    
    if choice == '3' or choice == '4':
        campus_data = extract_campus_information()
    
    if choice == '4':
        create_combined_report(program_data, research_data, campus_data)