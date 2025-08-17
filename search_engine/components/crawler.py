import requests
import time
import urllib.parse
from urllib.robotparser import RobotFileParser
from collections import deque
import threading
import logging

class WebCrawler:
    def __init__(self, max_pages=100, delay=1, max_depth=3):
        self.max_pages = max_pages
        self.delay = delay
        self.max_depth = max_depth
        self.visited_urls = set()
        self.url_queue = deque()
        self.crawled_pages = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': '168.se Bot 1.0'
        })
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def can_fetch(self, url):
        """Check robots.txt to see if we can crawl this URL"""
        try:
            parsed_url = urllib.parse.urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return rp.can_fetch('*', url)
        except:
            return True  # If we can't check robots.txt, assume we can crawl
    
    def normalize_url(self, url, base_url):
        """Normalize and resolve relative URLs"""
        return urllib.parse.urljoin(base_url, url)
    
    def extract_links(self, content, base_url):
        """Extract links from HTML content"""
        from bs4 import BeautifulSoup
        
        links = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link['href']
                normalized_url = self.normalize_url(href, base_url)
                
                # Only include HTTP/HTTPS links
                if normalized_url.startswith(('http://', 'https://')):
                    links.append(normalized_url)
        except Exception as e:
            self.logger.error(f"Error extracting links from {base_url}: {e}")
        
        return links
    
    def crawl_page(self, url, depth=0):
        """Crawl a single page"""
        if (url in self.visited_urls or 
            len(self.crawled_pages) >= self.max_pages or
            depth > self.max_depth):
            return None
        
        if not self.can_fetch(url):
            self.logger.info(f"Robots.txt disallows crawling: {url}")
            return None
        
        try:
            self.logger.info(f"Crawling: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Only process HTML content
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return None
            
            self.visited_urls.add(url)
            
            page_data = {
                'url': url,
                'title': '',
                'content': response.text,
                'links': [],
                'depth': depth,
                'crawl_time': time.time()
            }
            
            # Extract links for further crawling
            links = self.extract_links(response.text, url)
            page_data['links'] = links
            
            # Add new links to queue
            for link in links:
                if link not in self.visited_urls:
                    self.url_queue.append((link, depth + 1))
            
            self.crawled_pages.append(page_data)
            return page_data
            
        except Exception as e:
            self.logger.error(f"Error crawling {url}: {e}")
            return None
    
    def crawl(self, seed_urls):
        """Start crawling from seed URLs"""
        # Add seed URLs to queue
        for url in seed_urls:
            self.url_queue.append((url, 0))
        
        while self.url_queue and len(self.crawled_pages) < self.max_pages:
            url, depth = self.url_queue.popleft()
            
            if url not in self.visited_urls:
                self.crawl_page(url, depth)
                time.sleep(self.delay)  # Be polite to servers
        
        self.logger.info(f"Crawling completed. Crawled {len(self.crawled_pages)} pages.")
        return self.crawled_pages
    
    def get_crawled_data(self):
        """Return crawled data"""
        return self.crawled_pages
