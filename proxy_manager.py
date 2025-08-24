
import requests
import json
import random
import time
from typing import List, Dict, Optional
import logging
from proxy_list import PROXY_LIST

class ProxyManager:
    """Advanced proxy manager with health checking and rotation"""

    def __init__(self):
        self.proxies = []
        self.working_proxies = []
        self.failed_proxies = []
        self.current_index = 0
        self.logger = logging.getLogger(__name__)

        # Load initial proxy list
        self.load_free_proxies()

    def load_free_proxies(self):
        """Load free proxies from various sources"""
        self.proxies = PROXY_LIST
        self.working_proxies = self.proxies.copy()

    def test_proxy(self, proxy: Dict[str, str], test_url: str = "http://httpbin.org/ip") -> bool:
        """Test if a proxy is working"""
        try:
            response = requests.get(
                test_url,
                proxies=proxy,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.debug(f"Proxy test failed: {e}")
            return False

    def get_working_proxy(self) -> Optional[Dict[str, str]]:
        """Get a working proxy with round-robin rotation"""
        if not self.working_proxies:
            self.logger.warning("No working proxies available, trying to reload...")
            self.load_free_proxies()
            return None

        proxy = self.working_proxies[self.current_index % len(self.working_proxies)]
        self.current_index += 1

        return proxy

    def mark_proxy_failed(self, proxy: Dict[str, str]):
        """Mark a proxy as failed and remove from working list"""
        if proxy in self.working_proxies:
            self.working_proxies.remove(proxy)
            self.failed_proxies.append(proxy)
            self.logger.info(f"Marked proxy as failed: {proxy}")

    def refresh_proxy_list(self):
        """Refresh the proxy list by retesting failed proxies"""
        self.logger.info("Refreshing proxy list...")

        # Test failed proxies again
        recovered_proxies = []
        for proxy in self.failed_proxies:
            if self.test_proxy(proxy):
                recovered_proxies.append(proxy)

        # Add recovered proxies back to working list
        for proxy in recovered_proxies:
            self.failed_proxies.remove(proxy)
            self.working_proxies.append(proxy)

        self.logger.info(f"Recovered {len(recovered_proxies)} proxies")

class FreeProxyFetcher:
    """Fetch free proxies from various sources"""

    @staticmethod
    def fetch_from_free_proxy_list():
        """Fetch proxies from free-proxy-list.net (example implementation)"""
        # This is a basic example - in production you'd implement proper scraping
        try:
            url = "https://free-proxy-list.net/"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)

            # You would parse the HTML here to extract proxy IPs and ports
            # This is just a placeholder implementation
            return []

        except Exception as e:
            logging.error(f"Failed to fetch free proxies: {e}")
            return []

    @staticmethod 
    def get_proxy_list() -> List[Dict[str, str]]:
        """Get a comprehensive list of free proxies"""
        # You can implement multiple sources here
        return [
            {"http": "http://8.210.83.33:80", "https": "http://8.210.83.33:80"},
            {"http": "http://47.74.152.29:8888", "https": "http://47.74.152.29:8888"},
            {"http": "http://20.205.61.143:80", "https": "http://20.205.61.143:80"},
        ]
