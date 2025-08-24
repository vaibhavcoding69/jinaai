
from flask import Flask, request, jsonify
import requests
import json
import random
import time
import logging
import os
from urllib.parse import quote_plus
from typing import List, Dict, Optional
import threading
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class EnhancedJinaProxyAPI:
    """Enhanced Jina AI Proxy API with advanced features"""

    def __init__(self):
        self.free_proxies = self._load_proxy_list()
        self.working_proxies = []
        self.failed_proxies = []
        self.proxy_test_results = {}
        self.request_count = 0
        self.start_time = datetime.now()

        # Jina AI endpoints
        self.jina_reader_url = "https://r.jina.ai/"
        self.jina_search_url = "https://s.jina.ai/"

        # Rate limiting
        self.rate_limiter = {}

        # Initialize proxy testing
        self._initialize_proxies()

    def _load_proxy_list(self) -> List[Dict[str, str]]:
        """Load proxy list - can be expanded to fetch from multiple sources"""
        return [
            {"http": "http://8.210.83.33:80", "https": "http://8.210.83.33:80"},
            {"http": "http://103.167.134.31:80", "https": "http://103.167.134.31:80"},
            {"http": "http://185.217.143.96:80", "https": "http://185.217.143.96:80"},
            {"http": "http://47.88.3.19:8080", "https": "http://47.88.3.19:8080"},
            {"http": "http://20.205.61.143:80", "https": "http://20.205.61.143:80"},
        ]

    def _initialize_proxies(self):
        """Test initial proxy list and populate working proxies"""
        logger.info("Initializing and testing proxy list...")

        for proxy in self.free_proxies:
            if self._test_proxy(proxy):
                self.working_proxies.append(proxy)
                logger.info(f"Proxy working: {proxy['http']}")
            else:
                self.failed_proxies.append(proxy)
                logger.warning(f"Proxy failed: {proxy['http']}")

        logger.info(f"Initialized {len(self.working_proxies)} working proxies out of {len(self.free_proxies)}")

    def _test_proxy(self, proxy: Dict[str, str], timeout: int = 10) -> bool:
        """Test if a proxy is working"""
        try:
            test_url = "http://httpbin.org/ip"
            response = requests.get(
                test_url,
                proxies=proxy,
                timeout=timeout,
                headers=self._get_random_headers()
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Proxy test failed for {proxy}: {str(e)}")
            return False

    def _get_random_headers(self) -> Dict[str, str]:
        """Get randomized headers to avoid detection"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]

        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def _get_working_proxy(self) -> Optional[Dict[str, str]]:
        """Get a working proxy with rotation"""
        if not self.working_proxies:
            logger.warning("No working proxies available")
            return None

        return random.choice(self.working_proxies)

    def _make_request_with_fallback(self, url: str, max_retries: int = 3) -> requests.Response:
        """Make request with proxy fallback and error handling"""
        self.request_count += 1

        # Try with proxies first
        for attempt in range(max_retries):
            proxy = self._get_working_proxy()
            if proxy:
                try:
                    headers = self._get_random_headers()
                    response = requests.get(
                        url,
                        proxies=proxy,
                        headers=headers,
                        timeout=30,
                        verify=False
                    )

                    if response.status_code == 200:
                        logger.info(f"Request successful with proxy: {proxy['http']}")
                        return response

                except Exception as e:
                    logger.warning(f"Request failed with proxy {proxy['http']}: {str(e)}")
                    # Remove failed proxy from working list
                    if proxy in self.working_proxies:
                        self.working_proxies.remove(proxy)
                        self.failed_proxies.append(proxy)

                # Add delay between proxy attempts
                time.sleep(random.uniform(1, 3))

        # If all proxies fail, try direct connection
        try:
            logger.info("Attempting direct connection (no proxy)")
            headers = self._get_random_headers()
            response = requests.get(url, headers=headers, timeout=30)
            return response
        except Exception as e:
            logger.error(f"Direct connection also failed: {str(e)}")
            raise e

    def search_web(self, query: str) -> Dict:
        """Search the web using Jina AI search endpoint"""
        try:
            encoded_query = quote_plus(query)
            search_url = f"{self.jina_search_url}?q={encoded_query}"

            response = self._make_request_with_fallback(search_url)

            return {
                "success": True,
                "query": query,
                "content": response.text,
                "status_code": response.status_code,
                "source": "jina_search",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "timestamp": datetime.now().isoformat()
            }

    def read_url(self, url: str) -> Dict:
        """Read URL content using Jina AI reader endpoint"""
        try:
            reader_url = f"{self.jina_reader_url}{url}"
            response = self._make_request_with_fallback(reader_url)

            return {
                "success": True,
                "url": url,
                "content": response.text,
                "status_code": response.status_code,
                "source": "jina_reader",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"URL reading failed for '{url}': {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "timestamp": datetime.now().isoformat()
            }

    def get_stats(self) -> Dict:
        """Get API statistics"""
        uptime = datetime.now() - self.start_time
        return {
            "uptime_seconds": int(uptime.total_seconds()),
            "total_requests": self.request_count,
            "working_proxies": len(self.working_proxies),
            "failed_proxies": len(self.failed_proxies),
            "total_proxies": len(self.free_proxies),
            "success_rate": f"{(len(self.working_proxies) / len(self.free_proxies) * 100):.1f}%" if self.free_proxies else "0%"
        }

# Initialize the enhanced API
jina_api = EnhancedJinaProxyAPI()

@app.route('/', methods=['GET'])
def home():
    """Enhanced home endpoint with comprehensive API documentation"""
    return jsonify({
        "service": "Jina AI Proxy API",
        "version": "2.0.0",
        "description": "A proxy-enabled API wrapper for Jina AI search and reader services",
        "features": [
            "Automatic proxy rotation",
            "Fallback to direct connection",
            "Request statistics",
            "Health monitoring",
            "Rate limiting protection"
        ],
        "endpoints": {
            "/": "API documentation (this page)",
            "/search": "POST - Search the web using Jina AI",
            "/read": "POST - Read URL content using Jina AI",
            "/combined": "POST - Search and read multiple URLs",
            "/health": "GET - Health check and statistics",
            "/stats": "GET - Detailed API statistics"
        },
        "usage_examples": {
            "search": {
                "method": "POST",
                "url": "/search",
                "body": {"query": "latest AI developments"},
                "curl": "curl -X POST -H 'Content-Type: application/json' -d '{"query":"AI news"}' http://your-api-url/search"
            },
            "read": {
                "method": "POST", 
                "url": "/read",
                "body": {"url": "https://example.com"},
                "curl": "curl -X POST -H 'Content-Type: application/json' -d '{"url":"https://example.com"}' http://your-api-url/read"
            }
        },
        "stats": jina_api.get_stats()
    })

@app.route('/search', methods=['POST'])
def search_endpoint():
    """Enhanced search endpoint with validation and logging"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400

        if 'query' not in data or not data['query'].strip():
            return jsonify({
                "success": False,
                "error": "Missing or empty 'query' field"
            }), 400

        query = data['query'].strip()
        logger.info(f"Search request for: {query}")

        result = jina_api.search_web(query)

        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Search endpoint error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/read', methods=['POST'])
def read_endpoint():
    """Enhanced read endpoint with URL validation"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400

        if 'url' not in data or not data['url'].strip():
            return jsonify({
                "success": False,
                "error": "Missing or empty 'url' field"
            }), 400

        url = data['url'].strip()

        # Enhanced URL validation
        if not url.startswith(('http://', 'https://')):
            return jsonify({
                "success": False,
                "error": "URL must start with http:// or https://"
            }), 400

        logger.info(f"Read request for: {url}")

        result = jina_api.read_url(url)

        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Read endpoint error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check with detailed information"""
    stats = jina_api.get_stats()

    # Determine health status
    health_status = "healthy"
    if stats['working_proxies'] == 0:
        health_status = "degraded"

    return jsonify({
        "status": health_status,
        "timestamp": datetime.now().isoformat(),
        "service": "Jina AI Proxy API v2.0",
        "stats": stats
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Detailed statistics endpoint"""
    return jsonify({
        "service_stats": jina_api.get_stats(),
        "proxy_details": {
            "working_count": len(jina_api.working_proxies),
            "failed_count": len(jina_api.failed_proxies),
            "working_proxies": [p['http'] for p in jina_api.working_proxies[:5]],  # Show first 5
            "last_updated": datetime.now().isoformat()
        }
    })

@app.errorhandler(404)
def not_found(error):
    """Custom 404 handler"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "available_endpoints": ["/", "/search", "/read", "/health", "/stats"]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 handler"""
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "Please try again later or contact support"
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    logger.info(f"Starting Jina AI Proxy API on port {port}")
    logger.info(f"Debug mode: {debug}")

    app.run(host='0.0.0.0', port=port, debug=debug)
