import math
import logging
from collections import defaultdict

class SearchRanking:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Ranking weights
        self.weights = {
            'title_match': 3.0,
            'content_match': 1.0,
            'meta_description_match': 2.0,
            'heading_match': 2.5,
            'url_match': 1.5,
            'freshness': 1.0,
            'content_length': 0.5,
            'depth_penalty': -0.2
        }
    
    def calculate_tf_idf(self, term, document, all_documents):
        """Calculate Term Frequency-Inverse Document Frequency"""
        # Term frequency in document
        tf = document.lower().count(term.lower()) / len(document.split())
        
        # Document frequency (how many documents contain the term)
        df = sum(1 for doc in all_documents if term.lower() in doc.lower())
        
        # Inverse document frequency
        idf = math.log(len(all_documents) / (df + 1))
        
        return tf * idf
    
    def calculate_title_score(self, query_terms, title):
        """Calculate score based on title matches"""
        if not title:
            return 0
        
        title_lower = title.lower()
        score = 0
        
        for term in query_terms:
            term_lower = term.lower()
            if term_lower in title_lower:
                # Exact match gets higher score
                if term_lower == title_lower:
                    score += 10
                # Word boundary match
                elif f" {term_lower} " in f" {title_lower} ":
                    score += 5
                # Partial match
                else:
                    score += 2
        
        return score
    
    def calculate_content_score(self, query_terms, content, all_contents):
        """Calculate score based on content matches"""
        if not content:
            return 0
        
        score = 0
        content_lower = content.lower()
        
        for term in query_terms:
            term_lower = term.lower()
            
            # Count occurrences
            occurrences = content_lower.count(term_lower)
            
            # Calculate TF-IDF
            tf_idf = self.calculate_tf_idf(term, content, all_contents)
            
            # Position bonus (terms appearing early get higher score)
            first_occurrence = content_lower.find(term_lower)
            position_bonus = 1.0
            if first_occurrence != -1:
                position_bonus = 1.0 - (first_occurrence / len(content)) * 0.5
            
            score += occurrences * tf_idf * position_bonus
        
        return score
    
    def calculate_url_score(self, query_terms, url):
        """Calculate score based on URL matches"""
        if not url:
            return 0
        
        url_lower = url.lower()
        score = 0
        
        for term in query_terms:
            term_lower = term.lower()
            if term_lower in url_lower:
                score += 1
        
        return score
    
    def calculate_freshness_score(self, crawl_time):
        """Calculate freshness score based on when the page was crawled"""
        import time
        
        if not crawl_time:
            return 0
        
        # Convert to timestamp if it's a datetime object
        if hasattr(crawl_time, 'timestamp'):
            crawl_timestamp = crawl_time.timestamp()
        else:
            crawl_timestamp = crawl_time
        
        current_time = time.time()
        age_days = (current_time - crawl_timestamp) / (24 * 3600)
        
        # Fresher content gets higher score
        # Score decreases exponentially with age
        freshness_score = math.exp(-age_days / 30)  # 30-day half-life
        
        return freshness_score
    
    def calculate_content_length_score(self, content_length):
        """Calculate score based on content length"""
        if not content_length:
            return 0
        
        # Optimal content length is around 1000-2000 characters
        optimal_length = 1500
        
        if content_length < 100:
            return 0.1  # Too short
        elif content_length > 10000:
            return 0.3  # Too long
        else:
            # Bell curve around optimal length
            diff = abs(content_length - optimal_length)
            score = math.exp(-(diff ** 2) / (2 * (optimal_length / 2) ** 2))
            return score
    
    def calculate_depth_penalty(self, depth):
        """Calculate penalty based on crawl depth"""
        # Pages deeper in the site hierarchy get lower scores
        return depth * 0.1
    
    def rank_results(self, results, query_string):
        """Rank search results based on multiple factors"""
        if not results:
            return results
        
        query_terms = query_string.lower().split()
        all_contents = [result.get('content', '') for result in results]
        
        ranked_results = []
        
        for result in results:
            # Calculate individual scores
            title_score = self.calculate_title_score(query_terms, result.get('title', ''))
            content_score = self.calculate_content_score(
                query_terms, result.get('content', ''), all_contents
            )
            url_score = self.calculate_url_score(query_terms, result.get('url', ''))
            freshness_score = self.calculate_freshness_score(result.get('crawl_time'))
            content_length_score = self.calculate_content_length_score(
                result.get('content_length', 0)
            )
            depth_penalty = self.calculate_depth_penalty(result.get('depth', 0))
            
            # Meta description and heading scores
            meta_score = self.calculate_title_score(
                query_terms, result.get('meta_description', '')
            )
            heading_score = self.calculate_title_score(
                query_terms, result.get('headings', '')
            )
            
            # Calculate weighted total score
            total_score = (
                title_score * self.weights['title_match'] +
                content_score * self.weights['content_match'] +
                meta_score * self.weights['meta_description_match'] +
                heading_score * self.weights['heading_match'] +
                url_score * self.weights['url_match'] +
                freshness_score * self.weights['freshness'] +
                content_length_score * self.weights['content_length'] -
                depth_penalty * abs(self.weights['depth_penalty'])
            )
            
            # Add the original Whoosh score if available
            if 'score' in result:
                total_score += result['score']
            
            # Add detailed scoring information
            result['ranking_score'] = total_score
            result['score_breakdown'] = {
                'title_score': title_score,
                'content_score': content_score,
                'meta_score': meta_score,
                'heading_score': heading_score,
                'url_score': url_score,
                'freshness_score': freshness_score,
                'content_length_score': content_length_score,
                'depth_penalty': depth_penalty
            }
            
            ranked_results.append(result)
        
        # Sort by total score (descending)
        ranked_results.sort(key=lambda x: x['ranking_score'], reverse=True)
        
        self.logger.info(f"Ranked {len(ranked_results)} results for query: '{query_string}'")
        
        return ranked_results
    
    def update_weights(self, new_weights):
        """Update ranking weights"""
        self.weights.update(new_weights)
        self.logger.info("Ranking weights updated")
    
    def get_weights(self):
        """Get current ranking weights"""
        return self.weights.copy()
