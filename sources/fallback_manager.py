"""Resilient HTTP session and multi-source rate limit fallback manager."""

import time
import random
import logging
import requests
from typing import Optional, Dict, Any
from requests.adapters import HTTPAdapter
from config import DEFAULT_HEADERS, REQUEST_TIMEOUT, MAX_RETRIES, BACKOFF_FACTOR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("fallback_manager")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]

class ResilientSession:
    """HTTP Session wrapper with auto-retry, user-agent rotation, and rate-limit handling."""
    
    def __init__(self):
        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=60, pool_maxsize=60, max_retries=1)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = dict(DEFAULT_HEADERS)
        headers["User-Agent"] = random.choice(USER_AGENTS)
        if custom_headers:
            headers.update(custom_headers)
        return headers

    def get(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, timeout: int = REQUEST_TIMEOUT) -> Optional[requests.Response]:
        merged_headers = self.get_headers(headers)
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.get(url, params=params, headers=merged_headers, timeout=timeout)
                if resp.status_code == 200:
                    return resp
                elif resp.status_code == 404:
                    return None
                elif resp.status_code in (429, 403, 500, 502, 503, 504):
                    logger.warning(f"Rate limited or status {resp.status_code} on {url}. Attempt {attempt}/{MAX_RETRIES}")
                    sleep_time = (BACKOFF_FACTOR ** attempt) + random.uniform(0.3, 0.7)
                    time.sleep(sleep_time)
                else:
                    return None
            except Exception as e:
                logger.debug(f"Request exception on {url}: {e}")
                time.sleep(0.5)

        return None

    def post(self, url: str, json_data: Optional[Dict[str, Any]] = None, data: Optional[Any] = None, headers: Optional[Dict[str, str]] = None, timeout: int = REQUEST_TIMEOUT) -> Optional[requests.Response]:
        merged_headers = self.get_headers(headers)
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.post(url, json=json_data, data=data, headers=merged_headers, timeout=timeout)
                if resp.status_code == 200:
                    return resp
                elif resp.status_code == 404:
                    return None
                elif resp.status_code in (429, 403, 500, 502, 503, 504):
                    logger.warning(f"Rate limited or status {resp.status_code} on {url}. Attempt {attempt}/{MAX_RETRIES}")
                    sleep_time = (BACKOFF_FACTOR ** attempt) + random.uniform(0.3, 0.7)
                    time.sleep(sleep_time)
                else:
                    return None
            except Exception as e:
                logger.debug(f"Request exception on {url}: {e}")
                time.sleep(0.5)

        return None

# Global singleton session
resilient_session = ResilientSession()
