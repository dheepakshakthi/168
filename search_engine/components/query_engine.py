from whoosh.index import open_dir
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.query import And, Or, Term
from whoosh.scoring import BM25F
import logging
import re

class QueryEngine:
    def __init__(self, index_dir="data/index"):
        self.index_dir = index_dir
        self.logger = logging.getLogger(__name__)
        
        try:
            self.index = open_dir(index_dir)
            self.searcher = self.index.searcher()
            
            # Create query parsers
            self.title_parser = QueryParser("title", self.index.schema)
            self.content_parser = QueryParser("content", self.index.schema)
            self.multifield_parser = MultifieldParser(
                ["title", "content", "meta_description", "headings"], 
                self.index.schema
            )
            
            self.logger.info("Query engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing query engine: {e}")
            raise
    
    def preprocess_query(self, query_string):
        """Clean and preprocess the query string"""
        # Remove special characters except quotes and common operators
        query_string = re.sub(r'[^\w\s\"\'\+\-\*\(\)]', ' ', query_string)
        
        # Collapse multiple spaces
        query_string = re.sub(r'\s+', ' ', query_string).strip()
        
        return query_string
    
    def search(self, query_string, limit=10, fields=None):
        """Perform a search query"""
        try:
            # Preprocess query
            clean_query = self.preprocess_query(query_string)
            
            if not clean_query:
                return []
            
            # Choose appropriate parser
            if fields:
                if len(fields) == 1:
                    parser = QueryParser(fields[0], self.index.schema)
                else:
                    parser = MultifieldParser(fields, self.index.schema)
            else:
                parser = self.multifield_parser
            
            # Parse query
            query = parser.parse(clean_query)
            
            # Perform search
            results = self.searcher.search(query, limit=limit)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_result = {
                    'url': result['url'],
                    'title': result['title'],
                    'content': result['content'][:300] + '...' if len(result['content']) > 300 else result['content'],
                    'meta_description': result['meta_description'],
                    'score': result.score,
                    'content_length': result['content_length'],
                    'crawl_time': result['crawl_time'],
                    'depth': result['depth']
                }
                formatted_results.append(formatted_result)
            
            self.logger.info(f"Search for '{query_string}' returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error performing search for '{query_string}': {e}")
            return []
    
    def suggest_query(self, partial_query, limit=5):
        """Suggest query completions based on indexed content"""
        try:
            # Simple suggestion based on title field
            suggestions = []
            
            # Search for partial matches in titles
            query = self.title_parser.parse(f"{partial_query}*")
            results = self.searcher.search(query, limit=limit*2)
            
            # Extract unique words from titles
            words = set()
            for result in results:
                title_words = result['title'].lower().split()
                for word in title_words:
                    if word.startswith(partial_query.lower()) and len(word) > len(partial_query):
                        words.add(word)
            
            suggestions = list(words)[:limit]
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating suggestions for '{partial_query}': {e}")
            return []
    
    def get_popular_queries(self, limit=10):
        """Get popular search terms based on content frequency"""
        try:
            # This is a simplified implementation
            # In a real system, you'd track actual search queries
            
            popular_terms = []
            
            # Get most frequent terms from title field
            field_terms = self.searcher.field_terms("title")
            term_freq = {}
            
            for term in field_terms:
                if len(term) > 3:  # Only consider words longer than 3 characters
                    freq = self.searcher.doc_frequency("title", term)
                    term_freq[term] = freq
            
            # Sort by frequency and return top terms
            sorted_terms = sorted(term_freq.items(), key=lambda x: x[1], reverse=True)
            popular_terms = [term for term, freq in sorted_terms[:limit]]
            
            return popular_terms
            
        except Exception as e:
            self.logger.error(f"Error getting popular queries: {e}")
            return []
    
    def close(self):
        """Close the searcher"""
        if hasattr(self, 'searcher'):
            self.searcher.close()
            self.logger.info("Query engine closed")
