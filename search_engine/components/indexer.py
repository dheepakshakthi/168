from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID, DATETIME, NUMERIC
from whoosh.analysis import StemmingAnalyzer
from whoosh.writing import AsyncWriter
import os
import logging
from datetime import datetime

class SearchIndexer:
    def __init__(self, index_dir="data/index"):
        self.index_dir = index_dir
        self.logger = logging.getLogger(__name__)
        
        # Create index directory if it doesn't exist
        os.makedirs(index_dir, exist_ok=True)
        
        # Define schema for the search index
        self.schema = Schema(
            url=ID(stored=True, unique=True),
            title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
            content=TEXT(stored=True, analyzer=StemmingAnalyzer()),
            meta_description=TEXT(stored=True),
            headings=TEXT(stored=True),
            content_length=NUMERIC(stored=True),
            crawl_time=DATETIME(stored=True),
            depth=NUMERIC(stored=True)
        )
        
        # Create or open index
        if not exists_in(index_dir):
            self.index = create_in(index_dir, self.schema)
            self.logger.info("Created new search index")
        else:
            self.index = open_dir(index_dir)
            self.logger.info("Opened existing search index")
    
    def add_document(self, writer, parsed_page):
        """Add a single document to the index"""
        try:
            # Combine headings into a single text field
            headings_text = " ".join([h['text'] for h in parsed_page.get('headings', [])])
            
            # Convert crawl_time to datetime
            crawl_datetime = datetime.fromtimestamp(parsed_page.get('crawl_time', 0))
            
            writer.add_document(
                url=parsed_page['url'],
                title=parsed_page.get('title', ''),
                content=parsed_page.get('content', ''),
                meta_description=parsed_page.get('meta_description', ''),
                headings=headings_text,
                content_length=parsed_page.get('content_length', 0),
                crawl_time=crawl_datetime,
                depth=parsed_page.get('depth', 0)
            )
            
        except Exception as e:
            self.logger.error(f"Error adding document {parsed_page.get('url', 'unknown')}: {e}")
    
    def index_pages(self, parsed_pages):
        """Index multiple parsed pages"""
        writer = self.index.writer()
        
        try:
            for parsed_page in parsed_pages:
                self.add_document(writer, parsed_page)
            
            writer.commit()
            self.logger.info(f"Indexed {len(parsed_pages)} pages successfully")
            
        except Exception as e:
            writer.cancel()
            self.logger.error(f"Error during indexing: {e}")
            raise
    
    def update_document(self, parsed_page):
        """Update a single document in the index"""
        writer = self.index.writer()
        
        try:
            # Delete existing document with same URL
            writer.delete_by_term('url', parsed_page['url'])
            
            # Add updated document
            self.add_document(writer, parsed_page)
            
            writer.commit()
            self.logger.info(f"Updated document: {parsed_page['url']}")
            
        except Exception as e:
            writer.cancel()
            self.logger.error(f"Error updating document {parsed_page.get('url', 'unknown')}: {e}")
            raise
    
    def delete_document(self, url):
        """Delete a document from the index by URL"""
        writer = self.index.writer()
        
        try:
            writer.delete_by_term('url', url)
            writer.commit()
            self.logger.info(f"Deleted document: {url}")
            
        except Exception as e:
            writer.cancel()
            self.logger.error(f"Error deleting document {url}: {e}")
            raise
    
    def get_index_stats(self):
        """Get statistics about the index"""
        with self.index.searcher() as searcher:
            doc_count = searcher.doc_count()
            return {
                'document_count': doc_count,
                'index_directory': self.index_dir
            }
    
    def optimize_index(self):
        """Optimize the index for better search performance"""
        try:
            with self.index.writer() as writer:
                writer.mergetype = self.index.CLEAR
            self.logger.info("Index optimized successfully")
        except Exception as e:
            self.logger.error(f"Error optimizing index: {e}")
            raise
