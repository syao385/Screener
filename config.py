"""Configuration module for Premarket Screener & Dashboard."""

import os
from pathlib import Path
import pytz

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)
DOCS_DIR = BASE_DIR / "docs"
DOCS_DIR.mkdir(exist_ok=True)
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

REPORT_HTML_PATH = BASE_DIR / "latest_report.html"

# Timezone
TZ_EST = pytz.timezone("America/New_York")
TZ_PST = pytz.timezone("America/Los_Angeles")

# Target Schedule Time (Eastern Time)
SCHEDULE_HOUR = 8
SCHEDULE_MINUTE = 45

# Screener Universe Filters
DAY_TRADING_MIN_GAP = 3.0           # Minimum gap > 3% (Default filter)
DAY_TRADING_MIN_PRICE = 1.50        # Minimum price >= $1.50
DAY_TRADING_MIN_MARKET_CAP = 1.0e9  # Minimum market cap >= $1.0B
DAY_TRADING_MIN_AVG_VOLUME_30D = 500_000  # 30-day average volume >= 500k
DAY_TRADING_MIN_RVOL = 1.5          # Minimum RVOL >= 1.5 (Default filter)
RVOL_LOOKBACK_DAYS = 20             # 20-day historical lookback for session RVOL

# Real-Time Engine Settings
REALTIME_REFRESH_INTERVAL = 60      # Loop cycle in seconds
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0
AFTER_HOURS_CLOSE_HOUR = 20
AFTER_HOURS_CLOSE_MINUTE = 0

# Request Headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

# Timeout settings
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.5
