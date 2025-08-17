import os
import logging
from components.crawler import WebCrawler
from components.parser import WebParser
from components.indexer import SearchIndexer
from components.query_engine import QueryEngine
from components.scheduler import CrawlScheduler
from components.ranking import SearchRanking

class SearchEngine:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.index_dir = os.path.join(data_dir, "index")
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize components
        self.crawler = WebCrawler()
        self.parser = WebParser()
        self.indexer = SearchIndexer(self.index_dir)
        self.scheduler = CrawlScheduler(data_dir)
        self.ranking = SearchRanking()
        
        # Query engine will be initialized when needed
        self.query_engine = None
        
        self.logger.info("Search engine initialized successfully")
    
    def crawl_and_index(self, seed_urls, max_pages=50, max_depth=2):
        """Crawl websites and add them to the search index"""
        try:
            self.logger.info(f"Starting crawl for {len(seed_urls)} seed URLs")
            
            # Find or create a job for tracking this manual crawl
            job_id = self.scheduler.find_or_create_manual_job(seed_urls, max_pages, max_depth)
            
            # Update job status to running
            from datetime import datetime
            self.scheduler.update_job_status(job_id, 'running', datetime.now().isoformat())
            
            # Configure crawler
            self.crawler.max_pages = max_pages
            self.crawler.max_depth = max_depth
            
            # Crawl pages
            crawled_pages = self.crawler.crawl(seed_urls)
            
            if not crawled_pages:
                self.logger.warning("No pages were crawled")
                self.scheduler.update_job_status(job_id, 'failed')
                return False
            
            # Parse pages
            self.logger.info("Parsing crawled pages...")
            parsed_pages = self.parser.parse_pages(crawled_pages)
            
            if not parsed_pages:
                self.logger.warning("No pages were parsed successfully")
                self.scheduler.update_job_status(job_id, 'failed')
                return False
            
            # Index pages
            self.logger.info("Indexing parsed pages...")
            self.indexer.index_pages(parsed_pages)
            
            # Update job status to completed
            self.scheduler.update_job_status(job_id, 'completed')
            
            self.logger.info(f"Successfully crawled and indexed {len(parsed_pages)} pages")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during crawl and index: {e}")
            # Update job status to failed if we have a job_id
            if 'job_id' in locals():
                self.scheduler.update_job_status(job_id, 'failed')
            return False
    
    def search(self, query_string, limit=10, enable_ranking=True):
        """Search the indexed content"""
        try:
            # Initialize query engine if not already done
            if not self.query_engine:
                self.query_engine = QueryEngine(self.index_dir)
            
            # Perform search
            results = self.query_engine.search(query_string, limit=limit*2)  # Get more results for ranking
            
            if not results:
                return []
            
            # Apply custom ranking if enabled
            if enable_ranking:
                results = self.ranking.rank_results(results, query_string)
            
            # Return only the requested number of results
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"Error during search: {e}")
            return []
    
    def add_crawl_job(self, name, seed_urls, schedule_type="daily", schedule_time="02:00", 
                      max_pages=100, max_depth=3):
        """Add a scheduled crawl job"""
        return self.scheduler.add_crawl_job(
            name, seed_urls, schedule_type, schedule_time, max_pages, max_depth
        )
    
    def start_scheduler(self):
        """Start the crawl scheduler"""
        self.scheduler.start_scheduler()
    
    def stop_scheduler(self):
        """Stop the crawl scheduler"""
        self.scheduler.stop_scheduler()
    
    def get_crawl_jobs(self):
        """Get all crawl jobs"""
        return self.scheduler.get_job_status()
    
    def run_crawl_job(self, job_id):
        """Run a specific crawl job immediately"""
        return self.scheduler.run_job_now(job_id)
    
    def get_index_stats(self):
        """Get search index statistics"""
        return self.indexer.get_index_stats()
    
    def optimize_index(self):
        """Optimize the search index"""
        self.indexer.optimize_index()
    
    def get_suggestions(self, partial_query, limit=5):
        """Get query suggestions"""
        if not self.query_engine:
            self.query_engine = QueryEngine(self.index_dir)
        
        return self.query_engine.suggest_query(partial_query, limit)
    
    def get_popular_queries(self, limit=10):
        """Get popular search terms"""
        if not self.query_engine:
            self.query_engine = QueryEngine(self.index_dir)
        
        return self.query_engine.get_popular_queries(limit)
    
    def update_ranking_weights(self, weights):
        """Update ranking algorithm weights"""
        self.ranking.update_weights(weights)
    
    def get_ranking_weights(self):
        """Get current ranking weights"""
        return self.ranking.get_weights()
    
    def shutdown(self):
        """Shutdown the search engine"""
        try:
            if self.query_engine:
                self.query_engine.close()
            
            self.stop_scheduler()
            self.logger.info("Search engine shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
