import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
import json
import os

class CrawlScheduler:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.logger = logging.getLogger(__name__)
        self.crawl_jobs = []
        self.is_running = False
        self.scheduler_thread = None
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # File to store crawl configuration
        self.config_file = os.path.join(data_dir, "crawl_config.json")
        
        # Load existing configuration
        self.load_configuration()
    
    def load_configuration(self):
        """Load crawl configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.crawl_jobs = config.get('crawl_jobs', [])
                    self.logger.info(f"Loaded {len(self.crawl_jobs)} crawl jobs from configuration")
            else:
                self.crawl_jobs = []
                self.logger.info("No existing configuration found, starting with empty job list")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.crawl_jobs = []
    
    def save_configuration(self):
        """Save crawl configuration to file"""
        try:
            config = {
                'crawl_jobs': self.crawl_jobs,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            self.logger.info("Configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
    
    def add_crawl_job(self, name, seed_urls, schedule_type="daily", schedule_time="02:00", 
                      max_pages=100, max_depth=3):
        """Add a new crawl job to the scheduler"""
        job = {
            'id': len(self.crawl_jobs) + 1,
            'name': name,
            'seed_urls': seed_urls,
            'schedule_type': schedule_type,  # daily, weekly, hourly
            'schedule_time': schedule_time,
            'max_pages': max_pages,
            'max_depth': max_depth,
            'created_at': datetime.now().isoformat(),
            'last_run': None,
            'next_run': None,
            'status': 'scheduled'
        }
        
        self.crawl_jobs.append(job)
        self.save_configuration()
        
        self.logger.info(f"Added crawl job: {name}")
        return job['id']
    
    def remove_crawl_job(self, job_id):
        """Remove a crawl job"""
        self.crawl_jobs = [job for job in self.crawl_jobs if job['id'] != job_id]
        self.save_configuration()
        self.logger.info(f"Removed crawl job with ID: {job_id}")
    
    def update_job_status(self, job_id, status, last_run=None, next_run=None):
        """Update job status and last run time"""
        for job in self.crawl_jobs:
            if job['id'] == job_id:
                job['status'] = status
                if last_run:
                    job['last_run'] = last_run
                if next_run:
                    job['next_run'] = next_run
                elif status == 'completed' and job['schedule_type'] == 'daily':
                    # Calculate next run for daily jobs
                    from datetime import datetime, timedelta
                    try:
                        next_run_time = datetime.now() + timedelta(days=1)
                        next_run_time = next_run_time.replace(
                            hour=int(job['schedule_time'][:2]),
                            minute=int(job['schedule_time'][3:]),
                            second=0,
                            microsecond=0
                        )
                        job['next_run'] = next_run_time.isoformat()
                        job['status'] = 'scheduled'  # Reset to scheduled for next run
                    except Exception as e:
                        self.logger.error(f"Error calculating next run: {e}")
                break
        self.save_configuration()
    
    def find_or_create_manual_job(self, seed_urls, max_pages, max_depth):
        """Find existing job with same parameters or create a temporary one for manual crawls"""
        # Look for existing job with same URLs and parameters
        for job in self.crawl_jobs:
            if (set(job['seed_urls']) == set(seed_urls) and 
                job['max_pages'] == max_pages and 
                job['max_depth'] == max_depth):
                return job['id']
        
        # Create a temporary manual job
        job_name = f"Manual Crawl - {seed_urls[0][:50]}..." if len(seed_urls[0]) > 50 else f"Manual Crawl - {seed_urls[0]}"
        job_id = self.add_crawl_job(
            name=job_name,
            seed_urls=seed_urls,
            schedule_type="manual",
            schedule_time="00:00",
            max_pages=max_pages,
            max_depth=max_depth
        )
        return job_id
    
    def execute_crawl_job(self, job):
        """Execute a single crawl job"""
        try:
            self.logger.info(f"Starting crawl job: {job['name']}")
            self.update_job_status(job['id'], 'running', datetime.now().isoformat())
            
            # Import here to avoid circular imports
            from .crawler import WebCrawler
            from .parser import WebParser
            from .indexer import SearchIndexer
            
            # Initialize components
            crawler = WebCrawler(
                max_pages=job['max_pages'], 
                max_depth=job['max_depth']
            )
            parser = WebParser()
            indexer = SearchIndexer(index_dir=os.path.join(self.data_dir, "index"))
            
            # Crawl pages
            crawled_pages = crawler.crawl(job['seed_urls'])
            
            if crawled_pages:
                # Parse pages
                parsed_pages = parser.parse_pages(crawled_pages)
                
                if parsed_pages:
                    # Index pages
                    indexer.index_pages(parsed_pages)
                    
                    self.logger.info(f"Crawl job '{job['name']}' completed successfully. "
                                   f"Processed {len(parsed_pages)} pages.")
                else:
                    self.logger.warning(f"No pages were parsed for job '{job['name']}'")
            else:
                self.logger.warning(f"No pages were crawled for job '{job['name']}'")
            
            self.update_job_status(job['id'], 'completed', datetime.now().isoformat())
            
        except Exception as e:
            self.logger.error(f"Error executing crawl job '{job['name']}': {e}")
            self.update_job_status(job['id'], 'failed')
    
    def schedule_jobs(self):
        """Schedule all crawl jobs"""
        schedule.clear()  # Clear existing schedules
        
        for job in self.crawl_jobs:
            if job['status'] in ['scheduled', 'completed', 'failed']:
                if job['schedule_type'] == 'daily':
                    schedule.every().day.at(job['schedule_time']).do(
                        self.execute_crawl_job, job
                    )
                elif job['schedule_type'] == 'weekly':
                    schedule.every().week.at(job['schedule_time']).do(
                        self.execute_crawl_job, job
                    )
                elif job['schedule_type'] == 'hourly':
                    schedule.every().hour.do(self.execute_crawl_job, job)
                
                self.logger.info(f"Scheduled job '{job['name']}' to run {job['schedule_type']} "
                               f"at {job['schedule_time'] if job['schedule_type'] != 'hourly' else 'every hour'}")
    
    def start_scheduler(self):
        """Start the scheduler in a separate thread"""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.schedule_jobs()
        
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Scheduler started successfully")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Scheduler stopped")
    
    def get_job_status(self):
        """Get status of all jobs"""
        return self.crawl_jobs
    
    def run_job_now(self, job_id):
        """Run a specific job immediately"""
        job = next((j for j in self.crawl_jobs if j['id'] == job_id), None)
        
        if job:
            # Run in a separate thread to avoid blocking
            thread = threading.Thread(target=self.execute_crawl_job, args=(job,), daemon=True)
            thread.start()
            self.logger.info(f"Started immediate execution of job '{job['name']}'")
            return True
        else:
            self.logger.error(f"Job with ID {job_id} not found")
            return False
