from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import sys
import logging
import google.generativeai as genai

# Add the search engine to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from search_engine import SearchEngine

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyA65OUYYQZPgRPWQHd1RIt9Sclt9gJdWQE"
genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Initialize search engine
search_engine = SearchEngine(data_dir=os.path.join(os.path.dirname(__file__), 'data'))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Home page with search interface"""
    stats = search_engine.get_index_stats()
    popular_queries = search_engine.get_popular_queries(5)
    
    return render_template('index.html', 
                         stats=stats, 
                         popular_queries=popular_queries)

def get_gemini_answer(query, search_results):
    """Get AI-generated answer from Gemini"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Create context from search results
        context = ""
        for i, result in enumerate(search_results[:3], 1):
            snippet = result.get('meta_description') or result.get('content', '')[:300]
            context += f"\n[Source {i}]: {snippet}\n"
        
        # Create prompt
        prompt = f"""Based on the search query and the following search results, provide a comprehensive and accurate answer to the user's question. Be concise but informative.

Query: {query}

Search Results Context:{context}

Please provide a helpful answer based on the available information. If the search results don't contain relevant information, provide a general answer based on your knowledge and mention that specific sources weren't found."""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error getting Gemini answer: {str(e)}")
        return None

@app.route('/search')
def search():
    """Handle search requests"""
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 10
    
    if not query:
        return redirect(url_for('index'))
    
    # Calculate offset for pagination
    offset = (page - 1) * per_page
    
    # Perform search
    results = search_engine.search(query, limit=per_page * page)
    
    # Get results for current page
    page_results = results[offset:offset + per_page]
    
    # Get AI answer from Gemini (only for first page)
    ai_answer = None
    if page == 1 and results:
        ai_answer = get_gemini_answer(query, results)
    
    # Check if there are more results
    has_next = len(results) > offset + per_page
    has_prev = page > 1
    
    return render_template('search_results.html',
                         query=query,
                         results=page_results,
                         page=page,
                         has_next=has_next,
                         has_prev=has_prev,
                         total_results=len(results),
                         ai_answer=ai_answer)

@app.route('/api/search')
def api_search():
    """API endpoint for search"""
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    results = search_engine.search(query, limit=limit)
    
    return jsonify({
        'query': query,
        'results': results,
        'total': len(results)
    })

@app.route('/api/suggestions')
def api_suggestions():
    """API endpoint for query suggestions"""
    partial_query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 5))
    
    if not partial_query:
        return jsonify({'suggestions': []})
    
    suggestions = search_engine.get_suggestions(partial_query, limit)
    
    return jsonify({'suggestions': suggestions})

@app.route('/admin')
def admin():
    """Admin interface"""
    stats = search_engine.get_index_stats()
    crawl_jobs = search_engine.get_crawl_jobs()
    ranking_weights = search_engine.get_ranking_weights()
    
    return render_template('admin.html',
                         stats=stats,
                         crawl_jobs=crawl_jobs,
                         ranking_weights=ranking_weights)

@app.route('/admin/crawl', methods=['POST'])
def admin_crawl():
    """Add URLs to crawl"""
    urls_text = request.form.get('urls', '').strip()
    max_pages = int(request.form.get('max_pages', 50))
    max_depth = int(request.form.get('max_depth', 2))
    
    if not urls_text:
        return jsonify({'error': 'URLs are required'}), 400
    
    # Parse URLs
    urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
    
    # Start crawling
    success = search_engine.crawl_and_index(urls, max_pages, max_depth)
    
    if success:
        return jsonify({'message': f'Successfully crawled {len(urls)} URLs'})
    else:
        return jsonify({'error': 'Crawling failed'}), 500

@app.route('/admin/add_job', methods=['POST'])
def admin_add_job():
    """Add a scheduled crawl job"""
    name = request.form.get('name', '').strip()
    urls_text = request.form.get('urls', '').strip()
    schedule_type = request.form.get('schedule_type', 'daily')
    schedule_time = request.form.get('schedule_time', '02:00')
    max_pages = int(request.form.get('max_pages', 100))
    max_depth = int(request.form.get('max_depth', 3))
    
    if not name or not urls_text:
        return jsonify({'error': 'Name and URLs are required'}), 400
    
    # Parse URLs
    urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
    
    # Add job
    job_id = search_engine.add_crawl_job(
        name, urls, schedule_type, schedule_time, max_pages, max_depth
    )
    
    return jsonify({'message': f'Job "{name}" added successfully', 'job_id': job_id})

@app.route('/admin/run_job/<int:job_id>', methods=['POST'])
def admin_run_job(job_id):
    """Run a crawl job immediately"""
    success = search_engine.run_crawl_job(job_id)
    
    if success:
        return jsonify({'message': 'Job started successfully'})
    else:
        return jsonify({'error': 'Job not found or failed to start'}), 404

@app.route('/admin/optimize', methods=['POST'])
def admin_optimize():
    """Optimize the search index"""
    try:
        search_engine.optimize_index()
        return jsonify({'message': 'Index optimized successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/update_weights', methods=['POST'])
def admin_update_weights():
    """Update ranking weights"""
    try:
        weights = {}
        for key in ['title_match', 'content_match', 'meta_description_match', 
                   'heading_match', 'url_match', 'freshness', 'content_length', 'depth_penalty']:
            value = request.form.get(key)
            if value:
                weights[key] = float(value)
        
        search_engine.update_ranking_weights(weights)
        return jsonify({'message': 'Ranking weights updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error='Internal server error'), 500

if __name__ == '__main__':
    # Start the scheduler
    search_engine.start_scheduler()
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        # Cleanup
        search_engine.shutdown()
