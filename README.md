# 168.se

## 🏗️ Architecture

The search engine follows a modular architecture with the following components:

1. **Crawler** - Discovers and fetches web pages
2. **Parser** - Extracts content from HTML pages  
3. **Indexer** - Creates searchable indexes using Whoosh
4. **Query Engine** - Processes search queries
5. **Ranking System** - Ranks results based on relevance
6. **Scheduler** - Manages automated crawling tasks
7. **Web Interface** - Flask-based user interface

## 🚀 Features

- **Web Crawling**: Respects robots.txt, handles relative URLs, and manages crawl depth
- **Content Parsing**: Extracts titles, meta descriptions, headings, and main content
- **Full-Text Search**: Powered by Whoosh search library with stemming
- **Custom Ranking**: Multi-factor ranking algorithm considering title matches, content relevance, freshness, and more
- **Scheduled Crawling**: Automated crawl jobs with configurable schedules
- **Web Interface**: Clean, responsive web UI for searching and administration
- **Admin Panel**: Manage crawl jobs, optimize indexes, and configure ranking weights
- **API Endpoints**: RESTful API for integration with other applications

## 📋 Requirements

- Python 3.7+
- Flask
- Whoosh
- BeautifulSoup4
- Requests
- Schedule
- NLTK

## 🛠️ Installation

1. **Clone or download the project**
   ```bash
   cd d:\168.se
   ```

2. **Install dependencies**
   ```bash
   uv pip install requests beautifulsoup4 flask whoosh nltk lxml urllib3 schedule
   ```

3. **Run the demo** (optional)
   ```bash
   python demo.py
   ```

4. **Start the web interface**
   ```bash
   cd search_engine
   python app.py
   ```

5. **Open your browser**
   - Visit: http://localhost:5000
   - Admin panel: http://localhost:5000/admin

## 📁 Project Structure

```
search_engine/
├── components/
│   ├── __init__.py
│   ├── crawler.py          # Web crawler
│   ├── parser.py           # HTML parser
│   ├── indexer.py          # Search indexer
│   ├── query_engine.py     # Query processor
│   ├── scheduler.py        # Crawl scheduler
│   └── ranking.py          # Ranking algorithm
├── templates/
│   ├── base.html           # Base template
│   ├── index.html          # Home page
│   ├── search_results.html # Search results
│   ├── admin.html          # Admin panel
│   └── error.html          # Error page
├── data/                   # Data directory (created automatically)
│   ├── index/              # Search index files
│   └── crawl_config.json   # Crawl job configuration
├── app.py                  # Flask web application
└── search_engine.py       # Main search engine class
```

## 🔍 Usage

### Basic Search

```python
from search_engine import SearchEngine

# Initialize search engine
engine = SearchEngine()

# Crawl and index websites
engine.crawl_and_index([
    "https://example.com",
    "https://httpbin.org"
], max_pages=50, max_depth=2)

# Search
results = engine.search("example query", limit=10)
for result in results:
    print(f"{result['title']} - {result['url']}")
```

### Scheduled Crawling

```python
# Add a scheduled job
job_id = engine.add_crawl_job(
    name="Daily News Crawl",
    seed_urls=["https://news.example.com"],
    schedule_type="daily",
    schedule_time="02:00",
    max_pages=100,
    max_depth=3
)

# Start the scheduler
engine.start_scheduler()
```

### Web Interface

1. **Home Page**: Search interface with suggestions
2. **Search Results**: Ranked results with pagination
3. **Admin Panel**: 
   - Manual crawling
   - Scheduled job management
   - Index optimization
   - Ranking weight configuration

## 🎛️ Configuration

### Ranking Weights

The ranking algorithm uses the following weights (configurable via admin panel):

- `title_match`: 3.0 - Matches in page title
- `content_match`: 1.0 - Matches in page content
- `meta_description_match`: 2.0 - Matches in meta description
- `heading_match`: 2.5 - Matches in headings
- `url_match`: 1.5 - Matches in URL
- `freshness`: 1.0 - How recently the page was crawled
- `content_length`: 0.5 - Optimal content length scoring
- `depth_penalty`: -0.2 - Penalty for deeper pages

### Crawler Settings

- `max_pages`: Maximum pages to crawl per job
- `max_depth`: Maximum depth to crawl from seed URLs
- `delay`: Delay between requests (default: 1 second)
- Respects robots.txt automatically

## 🌐 API Endpoints

- `GET /api/search?q=query&limit=10` - Search API
- `GET /api/suggestions?q=partial&limit=5` - Query suggestions
- `POST /admin/crawl` - Manual crawl trigger
- `POST /admin/add_job` - Add scheduled job
- `POST /admin/run_job/<id>` - Run job immediately

## 🔧 Advanced Features

### Custom Ranking Algorithm

The search engine implements a sophisticated ranking algorithm that considers:

1. **TF-IDF** for content relevance
2. **Position bias** (terms appearing early get higher scores)
3. **Title and heading emphasis**
4. **Freshness decay** (newer content ranked higher)
5. **Content length optimization**
6. **URL relevance**

### Scheduled Crawling

- **Daily, Weekly, or Hourly** schedules
- **Background processing** without blocking the web interface
- **Job status tracking** and management
- **Automatic index updates**

### Search Features

- **Multi-field search** across title, content, meta description, and headings
- **Query suggestions** based on indexed content
- **Popular queries** tracking
- **Pagination** for large result sets
- **Score breakdown** for debugging and optimization

