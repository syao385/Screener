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

# Load local .env if present (strictly gitignored)
env_file = BASE_DIR / ".env"
if env_file.exists():
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass

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

# ==========================================
# Phase 3: Telegram, Alerts & Scheduler Config
# ==========================================
# Telegram Bot API Configuration (Tokens can be set in environment or config.py)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_NOTIFICATION_LEVEL = os.environ.get("TELEGRAM_NOTIFICATION_LEVEL", "ALL")  # ALL, URGENT_ONLY, OFF

# Local Alert Dispatcher
ENABLE_DESKTOP_NOTIFICATIONS = True
ENABLE_AUDIO_CHIMES = True

# Windows Task Scheduler & Daemon Parameters
DAEMON_HEARTBEAT_FILE = DATA_DIR / "daemon_heartbeat.json"
ORDER_DESK_FILE = DATA_DIR / "order_desk.json"
DAEMON_POLL_INTERVAL_ACTIVE = 60    # seconds during market hours
DAEMON_POLL_INTERVAL_IDLE = 300     # seconds outside market hours

# ==========================================
# Phase 4: Alpha Attribution & Parameter Auto-Tuning Config
# ==========================================
ATTRIBUTION_DB_PATH = DATA_DIR / "attribution_lake.duckdb"
CALIBRATED_PARAMS_FILE = CACHE_DIR / "calibrated_parameters.json"
# Forward incremental fills default OFF, can be toggled on/off and overridden
ENABLE_FORWARD_INCREMENTAL_FILLS = False  
# Hard safety clamps for automatic parameter tuning
TUNING_MIN_CLAMP = 0.50
TUNING_MAX_CLAMP = 1.35
DEFAULT_RISK_FREE_RATE = 0.050  # 5.0% Fidelity SPAXX / 3M Treasury baseline

# ==========================================
# Phase 5: Risk Governance, Circuit Breakers & Autonomous Execution Config
# ==========================================
CIRCUIT_BREAKER_LEVEL1_PCT = -1.0       # -1.0% intraday loss: Soft Warning & Stop Ratchet
CIRCUIT_BREAKER_LEVEL2_PCT = -2.0       # -2.0% intraday loss: Tactical De-Risking (0.50x Clamp)
CIRCUIT_BREAKER_LEVEL3_PCT = -3.0       # -3.0% intraday loss: Emergency Session Kill-Switch
CIRCUIT_BREAKER_STATE_FILE = DATA_DIR / "circuit_breaker_state.json"

# Paper Trading & Order Router Config
PAPER_TRADING_DB_PATH = DATA_DIR / "paper_trading.duckdb"
ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets/v2")
WEBHOOK_EXECUTION_URL = os.environ.get("WEBHOOK_EXECUTION_URL", "")

# Stress Testing & Monte Carlo Defaults
MONTE_CARLO_SIMULATION_PATHS = 10000
DEFAULT_VAR_CONFIDENCE_1 = 0.95
DEFAULT_VAR_CONFIDENCE_2 = 0.99
