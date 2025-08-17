#!/usr/bin/env python3
"""
Example usage of the Search Engine
This script demonstrates how to use the search engine components
"""

import sys
import os

# Add the search engine to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'search_engine'))

from search_engine import SearchEngine

def main():
    print("🔍 168.se Search Engine Demo")
    print("=" * 50)
    
    # Initialize the search engine
    print("Initializing search engine...")
    search_engine = SearchEngine(data_dir="search_engine/data")
    
    # Example URLs to crawl
    seed_urls = [
        "https://example.com",
        "https://httpbin.org",
        "https://jsonplaceholder.typicode.com"
    ]
    
    print(f"\n📡 Crawling {len(seed_urls)} websites...")
    print("This may take a few minutes...")
    
    # Crawl and index websites
    success = search_engine.crawl_and_index(
        seed_urls=seed_urls,
        max_pages=20,  # Limit to 20 pages for demo
        max_depth=2    # Only go 2 levels deep
    )
    
    if success:
        print("✅ Crawling and indexing completed successfully!")
        
        # Get index statistics
        stats = search_engine.get_index_stats()
        print(f"📊 Indexed {stats['document_count']} documents")
        
        # Perform some example searches
        example_queries = ["example", "API", "test", "JSON"]
        
        print(f"\n🔍 Performing example searches...")
        for query in example_queries:
            print(f"\nSearching for: '{query}'")
            results = search_engine.search(query, limit=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['title']}")
                    print(f"     {result['url']}")
                    print(f"     Score: {result.get('ranking_score', 0):.2f}")
            else:
                print("  No results found")
        
        # Add a scheduled crawl job
        print(f"\n⏰ Adding a scheduled crawl job...")
        job_id = search_engine.add_crawl_job(
            name="Daily Example Crawl",
            seed_urls=["https://example.com"],
            schedule_type="daily",
            schedule_time="02:00",
            max_pages=50,
            max_depth=2
        )
        print(f"✅ Added crawl job with ID: {job_id}")
        
        # Start the scheduler
        print(f"\n🕐 Starting the crawl scheduler...")
        search_engine.start_scheduler()
        print("✅ Scheduler started successfully!")
        
        print(f"\n🌐 You can now start the web interface:")
        print(f"   cd search_engine")
        print(f"   python app.py")
        print(f"   Then visit: http://localhost:5000")
        
    else:
        print("❌ Crawling failed!")
    
    # Cleanup
    search_engine.shutdown()
    print(f"\n🔚 168.se demo completed!")

if __name__ == "__main__":
    main()
