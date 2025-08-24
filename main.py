
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

# Import the complete proxy list
try:
    from proxy_list_complete import PROXY_LIST
except ImportError:
    # Fallback proxy list if the file is not found
    PROXY_LIST = [
        {"http": "http://8.210.83.33:80", "https": "http://8.210.83.33:80"},
        {"http": "http://47.74.152.29:8888", "https": "http://47.74.152.29:8888"},
    ]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class UltraEnhancedJinaProxyAPI:
    """Ultra Enhanced Jina AI Proxy API with 180+ proxy rotation"""

    def __init__(self):
        self.free_proxies = PROXY_LIST  # Use complete proxy list
        self.working_proxies = []
        self.failed_proxies = []
        self.proxy_test_results = {}
        self.request_count = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time = datetime.now()
        self.current_proxy_index = 0

        # Jina AI endpoints
        self.jina_reader_url = "https://r.jina.ai/"
        self.jina_search_url = "https://s.jina.ai/"

        # Rate limiting and performance tracking
        self.rate_limiter = {}
        self.proxy_performance = {}
        self.last_proxy_test = None

        logger.info(f"Initialized with {len(self.free_proxies)} total proxies")

        # Initialize proxy testing in background
        self._initialize_proxies()

    def _initialize_proxies(self):
        """Test initial proxy list and populate working proxies (faster initialization)"""
        logger.info("Initializing proxy pool...")

        # Test a subset initially for faster startup
        test_proxies = self.free_proxies[:20]  # Test first 20 for quick start

        for proxy in test_proxies:
            if self._test_proxy(proxy, timeout=5):  # Shorter timeout for init
                self.working_proxies.append(proxy)
                self.proxy_performance[str(proxy)] = {"success": 1, "total": 1}
                logger.info(f"✓ Proxy working: {proxy['http']}")
            else:
                self.failed_proxies.append(proxy)

        # Add remaining untested proxies to working list (will be tested on use)
        remaining_proxies = self.free_proxies[20:]
        self.working_proxies.extend(remaining_proxies)

        logger.info(f"Quick init complete: {len(self.working_proxies)} proxies available")

        # Schedule background testing of remaining proxies
        threading.Thread(target=self._background_proxy_testing, daemon=True).start()

    def _background_proxy_testing(self):
        """Test remaining proxies in background"""
        logger.info("Starting background proxy testing...")

        for proxy in self.free_proxies[20:]:
            if proxy not in self.working_proxies and proxy not in self.failed_proxies:
                if self._test_proxy(proxy, timeout=10):
                    if proxy not in self.working_proxies:
                        self.working_proxies.append(proxy)
                        self.proxy_performance[str(proxy)] = {"success": 1, "total": 1}
                else:
                    if proxy in self.working_proxies:
                        self.working_proxies.remove(proxy)
                    if proxy not in self.failed_proxies:
                        self.failed_proxies.append(proxy)

                time.sleep(0.5)  # Small delay between tests

        logger.info(f"Background testing complete: {len(self.working_proxies)} working proxies")

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
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]

        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Cache-Control': 'max-age=0'
        }

    def _get_next_proxy(self) -> Optional[Dict[str, str]]:
        """Get next proxy using round-robin rotation"""
        if not self.working_proxies:
            logger.warning("No working proxies available")
            return None

        # Round-robin selection
        proxy = self.working_proxies[self.current_proxy_index % len(self.working_proxies)]
        self.current_proxy_index += 1

        return proxy

    def _update_proxy_performance(self, proxy: Dict[str, str], success: bool):
        """Update proxy performance statistics"""
        proxy_key = str(proxy)
        if proxy_key not in self.proxy_performance:
            self.proxy_performance[proxy_key] = {"success": 0, "total": 0}

        self.proxy_performance[proxy_key]["total"] += 1
        if success:
            self.proxy_performance[proxy_key]["success"] += 1

        # Remove consistently failing proxies
        perf = self.proxy_performance[proxy_key]
        if perf["total"] >= 5 and perf["success"] / perf["total"] < 0.2:  # Less than 20% success rate
            if proxy in self.working_proxies:
                self.working_proxies.remove(proxy)
                self.failed_proxies.append(proxy)
                logger.info(f"Removed failing proxy: {proxy['http']}")

    def _make_request_with_smart_rotation(self, url: str, max_retries: int = 5) -> requests.Response:
        """Make request with intelligent proxy rotation and fallback"""
        self.request_count += 1

        # Try with multiple proxies using smart rotation
        for attempt in range(max_retries):
            proxy = self._get_next_proxy()
            if proxy:
                try:
                    headers = self._get_random_headers()

                    # Add random delay to avoid rate limiting
                    time.sleep(random.uniform(0.1, 0.5))

                    response = requests.get(
                        url,
                        proxies=proxy,
                        headers=headers,
                        timeout=25,
                        verify=False
                    )

                    if response.status_code == 200:
                        self._update_proxy_performance(proxy, True)
                        self.successful_requests += 1
                        logger.info(f"✓ Request successful with proxy: {proxy['http']}")
                        return response
                    else:
                        self._update_proxy_performance(proxy, False)
                        logger.warning(f"Proxy returned status {response.status_code}: {proxy['http']}")

                except Exception as e:
                    self._update_proxy_performance(proxy, False)
                    logger.warning(f"Request failed with proxy {proxy['http']}: {str(e)}")

                # Add delay between proxy attempts
                time.sleep(random.uniform(0.5, 1.5))

        # If all proxies fail, try direct connection
        try:
            logger.info("Attempting direct connection (no proxy)")
            headers = self._get_random_headers()
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                self.successful_requests += 1
            return response
        except Exception as e:
            self.failed_requests += 1
            logger.error(f"Direct connection also failed: {str(e)}")
            raise e

    def search_web(self, query: str) -> Dict:
        """Enhanced web search using Jina AI with smart proxy rotation"""
        try:
            encoded_query = quote_plus(query)
            search_url = f"{self.jina_search_url}{encoded_query}"

            response = self._make_request_with_smart_rotation(search_url)

            return {
                "success": True,
                "query": query,
                "content": response.text[:10000],  # Limit content size
                "content_length": len(response.text),
                "status_code": response.status_code,
                "source": "jina_search",
                "timestamp": datetime.now().isoformat(),
                "proxy_used": "rotated"
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
        """Enhanced URL reading using Jina AI with smart proxy rotation"""
        try:
            reader_url = f"{self.jina_reader_url}{url}"
            response = self._make_request_with_smart_rotation(reader_url)

            return {
                "success": True,
                "url": url,
                "content": response.text[:15000],  # Limit content size
                "content_length": len(response.text),
                "status_code": response.status_code,
                "source": "jina_reader",
                "timestamp": datetime.now().isoformat(),
                "proxy_used": "rotated"
            }

        except Exception as e:
            logger.error(f"URL reading failed for '{url}': {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "timestamp": datetime.now().isoformat()
            }

    def get_comprehensive_stats(self) -> Dict:
        """Get comprehensive API and proxy statistics"""
        uptime = datetime.now() - self.start_time
        success_rate = (self.successful_requests / max(self.request_count, 1)) * 100

        # Get top performing proxies
        top_proxies = []
        for proxy_key, stats in list(self.proxy_performance.items())[:5]:
            if stats["total"] > 0:
                success_pct = (stats["success"] / stats["total"]) * 100
                top_proxies.append({
                    "proxy": proxy_key,
                    "success_rate": f"{success_pct:.1f}%",
                    "total_requests": stats["total"]
                })

        return {
            "uptime_seconds": int(uptime.total_seconds()),
            "total_requests": self.request_count,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": f"{success_rate:.1f}%",
            "proxy_stats": {
                "total_proxies": len(self.free_proxies),
                "working_proxies": len(self.working_proxies),
                "failed_proxies": len(self.failed_proxies),
                "proxy_pool_health": f"{(len(self.working_proxies) / len(self.free_proxies) * 100):.1f}%"
            },
            "top_performing_proxies": top_proxies,
            "current_proxy_index": self.current_proxy_index % len(self.working_proxies) if self.working_proxies else 0
        }

# Initialize the ultra-enhanced API
jina_api = UltraEnhancedJinaProxyAPI()

@app.route('/', methods=['GET'])
def home():
    """Enhanced home endpoint with comprehensive documentation"""
    stats = jina_api.get_comprehensive_stats()

    return jsonify({
        "service": "Ultra Enhanced Jina AI Proxy API",
        "version": "3.0.0",
        "description": "Advanced proxy-enabled API wrapper for Jina AI with 180+ proxy rotation",
        "features": [
            f"{len(PROXY_LIST)} proxy rotation pool",
            "Smart proxy performance tracking",
            "Automatic failing proxy removal",
            "Background proxy health testing",
            "Round-robin proxy selection",
            "Advanced rate limiting protection",
            "Comprehensive statistics",
            "Real-time health monitoring"
        ],
        "endpoints": {
            "/": "API documentation and statistics",
            "/search": "POST - Web search with proxy rotation",
            "/read": "POST - URL content extraction with proxy rotation",
            "/combined": "POST - Search and read multiple URLs",
            "/health": "GET - Quick health check",
            "/stats": "GET - Comprehensive statistics",
            "/proxy-stats": "GET - Detailed proxy performance"
        },
        "current_stats": stats,
        "usage_examples": {
            "search": {
                "method": "POST",
                "endpoint": "/search",
                "body": {"query": "latest technology trends 2025"},
                "description": "Search the web using Jina AI with automatic proxy rotation"
            },
            "read": {
                "method": "POST",
                "endpoint": "/read", 
                "body": {"url": "https://techcrunch.com"},
                "description": "Extract clean content from any URL"
            }
        }
    })

@app.route('/search', methods=['POST'])
def search_endpoint():
    """Ultra-enhanced search endpoint"""
    try:
        data = request.get_json()

        if not data or 'query' not in data or not data['query'].strip():
            return jsonify({
                "success": False,
                "error": "Missing or empty 'query' field",
                "example": {"query": "artificial intelligence news"}
            }), 400

        query = data['query'].strip()
        logger.info(f"🔍 Search request: {query}")

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
    """Ultra-enhanced read endpoint"""
    try:
        data = request.get_json()

        if not data or 'url' not in data or not data['url'].strip():
            return jsonify({
                "success": False,
                "error": "Missing or empty 'url' field",
                "example": {"url": "https://example.com"}
            }), 400

        url = data['url'].strip()

        if not url.startswith(('http://', 'https://')):
            return jsonify({
                "success": False,
                "error": "URL must start with http:// or https://"
            }), 400

        logger.info(f"📄 Read request: {url}")

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

@app.route('/combined', methods=['POST'])
def combined_endpoint():
    """Enhanced combined search and read endpoint"""
    try:
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'query' field"
            }), 400

        query = data['query'].strip()
        urls_to_read = data.get('urls', [])
        max_urls = min(data.get('max_urls', 3), 10)  # Limit to max 10 URLs

        logger.info(f"🔍📄 Combined request: {query} + {len(urls_to_read)} URLs")

        # Search first
        search_result = jina_api.search_web(query)

        results = {
            "success": True,
            "query": query,
            "search_result": search_result,
            "url_contents": [],
            "timestamp": datetime.now().isoformat()
        }

        # Read URLs if provided
        for url in urls_to_read[:max_urls]:
            url_result = jina_api.read_url(url)
            results["url_contents"].append(url_result)
            time.sleep(0.5)  # Small delay between URL reads

        return jsonify(results)

    except Exception as e:
        logger.error(f"Combined endpoint error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Quick health check"""
    stats = jina_api.get_comprehensive_stats()

    # Determine health status
    if stats['proxy_stats']['working_proxies'] > 10:
        status = "excellent"
    elif stats['proxy_stats']['working_proxies'] > 5:
        status = "good"
    elif stats['proxy_stats']['working_proxies'] > 0:
        status = "degraded"
    else:
        status = "critical"

    return jsonify({
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "service": "Ultra Enhanced Jina AI Proxy API v3.0",
        "quick_stats": {
            "working_proxies": stats['proxy_stats']['working_proxies'],
            "total_requests": stats['total_requests'],
            "success_rate": stats['success_rate'],
            "uptime_hours": round(stats['uptime_seconds'] / 3600, 1)
        }
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Comprehensive statistics endpoint"""
    return jsonify({
        "comprehensive_stats": jina_api.get_comprehensive_stats(),
        "service_info": {
            "version": "3.0.0",
            "proxy_pool_size": len(PROXY_LIST),
            "features": [
                "180+ proxy rotation",
                "Smart performance tracking",
                "Auto-scaling proxy pool",
                "Background health monitoring"
            ]
        }
    })

@app.route('/proxy-stats', methods=['GET'])
def get_proxy_stats():
    """Detailed proxy performance statistics"""
    proxy_details = []

    for proxy_key, stats in list(jina_api.proxy_performance.items())[:20]:  # Top 20
        if stats["total"] > 0:
            success_rate = (stats["success"] / stats["total"]) * 100
            proxy_details.append({
                "proxy": proxy_key.replace("{'http': 'http://", "").replace("', 'https': 'http://", " -> ").replace("'}", ""),
                "success_rate": f"{success_rate:.1f}%",
                "successful_requests": stats["success"],
                "total_requests": stats["total"],
                "status": "active" if success_rate > 50 else "poor"
            })

    return jsonify({
        "proxy_performance": proxy_details,
        "summary": {
            "total_proxies_loaded": len(PROXY_LIST),
            "currently_working": len(jina_api.working_proxies),
            "currently_failed": len(jina_api.failed_proxies),
            "tested_proxies": len(jina_api.proxy_performance),
            "rotation_index": jina_api.current_proxy_index
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    logger.info(f"🚀 Starting Ultra Enhanced Jina AI Proxy API")
    logger.info(f"📊 Loaded {len(PROXY_LIST)} proxies")
    logger.info(f"🌐 Server starting on port {port}")

    app.run(host='0.0.0.0', port=port, debug=debug)
