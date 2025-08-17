from bs4 import BeautifulSoup
import re
import logging

class WebParser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def clean_text(self, text):
        """Clean and normalize text"""
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    def extract_title(self, soup):
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return self.clean_text(title_tag.get_text())
        
        # Fallback to h1 tag
        h1_tag = soup.find('h1')
        if h1_tag:
            return self.clean_text(h1_tag.get_text())
        
        return "No Title"
    
    def extract_meta_description(self, soup):
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return self.clean_text(meta_desc['content'])
        return ""
    
    def extract_content(self, soup):
        """Extract main content from the page"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try to find main content areas
        main_content = ""
        
        # Look for main content tags
        content_tags = soup.find_all(['main', 'article', 'div'], 
                                   class_=re.compile(r'content|main|article|body', re.I))
        
        if content_tags:
            for tag in content_tags:
                main_content += tag.get_text() + " "
        else:
            # Fallback to body content
            body = soup.find('body')
            if body:
                main_content = body.get_text()
        
        return self.clean_text(main_content)
    
    def extract_headings(self, soup):
        """Extract all headings (h1-h6)"""
        headings = []
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                headings.append({
                    'level': i,
                    'text': self.clean_text(heading.get_text())
                })
        return headings
    
    def extract_links(self, soup, base_url):
        """Extract all links from the page"""
        from urllib.parse import urljoin
        
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            link_text = self.clean_text(link.get_text())
            
            links.append({
                'url': absolute_url,
                'text': link_text,
                'title': link.get('title', '')
            })
        
        return links
    
    def parse_page(self, page_data):
        """Parse a single page and extract structured data"""
        try:
            soup = BeautifulSoup(page_data['content'], 'html.parser')
            
            parsed_data = {
                'url': page_data['url'],
                'title': self.extract_title(soup),
                'meta_description': self.extract_meta_description(soup),
                'content': self.extract_content(soup),
                'headings': self.extract_headings(soup),
                'links': self.extract_links(soup, page_data['url']),
                'crawl_time': page_data.get('crawl_time', 0),
                'depth': page_data.get('depth', 0)
            }
            
            # Calculate content length
            parsed_data['content_length'] = len(parsed_data['content'])
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"Error parsing page {page_data.get('url', 'unknown')}: {e}")
            return None
    
    def parse_pages(self, crawled_pages):
        """Parse multiple pages"""
        parsed_pages = []
        
        for page_data in crawled_pages:
            parsed_page = self.parse_page(page_data)
            if parsed_page:
                parsed_pages.append(parsed_page)
        
        self.logger.info(f"Parsed {len(parsed_pages)} pages successfully.")
        return parsed_pages
