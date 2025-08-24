
import os
from typing import Dict, List

class Config:
    """Configuration settings for the Jina Proxy API"""

    # Flask settings
    FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.environ.get('FLASK_PORT', 5000))
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    # Jina AI endpoints
    JINA_READER_URL = "https://r.jina.ai/"
    JINA_SEARCH_URL = "https://s.jina.ai/"
    JINA_API_KEY = os.environ.get('JINA_API_KEY', '')  # Optional API key

    # Proxy settings
    USE_PROXIES = os.environ.get('USE_PROXIES', 'True').lower() == 'true'
    MAX_PROXY_RETRIES = int(os.environ.get('MAX_PROXY_RETRIES', 3))
    PROXY_TIMEOUT = int(os.environ.get('PROXY_TIMEOUT', 30))

    # Rate limiting
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', 60))

    # Request settings
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 30))
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]

    @classmethod
    def get_jina_headers(cls) -> Dict[str, str]:
        """Get headers for Jina AI requests"""
        headers = {
            'User-Agent': 'JinaProxyAPI/1.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        if cls.JINA_API_KEY:
            headers['Authorization'] = f'Bearer {cls.JINA_API_KEY}'

        return headers
