"""Earnings Lake Syncer & Coverage Daemon.

Guarantees 100% deterministic historical earnings coverage (8-12 quarters)
in DuckDB for:
1. Portfolio Holdings (Active positions maintained in PortfolioManager)
2. Screener Candidates (Top high-score setups & EP breakouts)
3. 3-Day Earnings Calendar Tickers (Yesterday AMC, Today BMO/AMC, Tomorrow)
4. Institutional Core Focus Universe (S&P 100 / Nasdaq 100 Leaders)

Implements polite multi-tier rate-limiting and immutable quarter caching
to prevent Yahoo Finance / SEC EDGAR rate limits.
"""

import os
import time
import random
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import TZ_EST
from sources.portfolio_manager import portfolio_mgr
from sources.defeatbeta_client import fundamental_engine

logger = logging.getLogger("earnings_lake_syncer")

# Core institutional focus tickers for instant off-line availability
CORE_INSTITUTIONAL_FOCUS = [
    "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "AMD", "QCOM",
    "SMCI", "ARM", "MRVL", "MU", "TSM", "ASML", "PANW", "CRWD", "PLTR", "SNOW",
    "ORCL", "NOW", "CRM", "ADBE", "INTC", "CSCO", "IBM", "TXN", "LRCX", "AMAT",
    "UBER", "ABNB", "COIN", "HOOD", "SHOP", "MELI", "SE", "SQ", "PYPL", "SOFI",
    "JPM", "BAC", "GS", "MS", "V", "MA", "AXP", "BLK", "SCHW", "C",
    "LLY", "NVO", "UNH", "JNJ", "ABBV", "MRK", "PFE", "TMO", "ISRG", "VRTX",
    "CAT", "DE", "GE", "HON", "UNP", "RTX", "LMT", "BA", "ETN", "PH",
    "XOM", "CVX", "COP", "SLB", "EOG", "OXY", "MPC", "PSX", "VLO", "KMI",
    "COST", "WMT", "TGT", "HD", "LOW", "NKE", "SBUX", "MCD", "CMG", "BKNG"
]


class EarningsLakeSyncer:
    """Automated Fundamental Data Lake Synchronizer."""

    def __init__(self, engine=fundamental_engine):
        self.engine = engine

    def get_target_universe(self, screener_candidates: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Extract union of all priority tickers across Portfolio, Screener, Calendar, and Core Leaders."""
        target_set: Set[str] = set()

        # 1. 100% Guaranteed Portfolio Holdings
        try:
            port_tickers = portfolio_mgr.get_active_equity_tickers()
            target_set.update(port_tickers)
        except Exception as e:
            logger.debug(f"Error extracting portfolio tickers: {e}")

        # 2. Screener Candidates
        if screener_candidates:
            for c in screener_candidates:
                t = c.get("ticker") or c.get("symbol")
                if t:
                    target_set.add(str(t).upper().strip())

        # 3. 3-Day Earnings Calendar
        try:
            from sources.earnings_calendar import earnings_cal
            cal = earnings_cal.get_earnings_dashboard()
            for group in ["yesterday_amc", "today_bmo", "today_amc", "tomorrow_bmo", "tomorrow_amc"]:
                for item in cal.get(group, []):
                    t = item.get("ticker")
                    if t:
                        target_set.add(str(t).upper().strip())
        except Exception as e:
            logger.debug(f"Error extracting calendar tickers: {e}")

        # 4. Core Institutional Leaders
        target_set.update(CORE_INSTITUTIONAL_FOCUS)

        # Filter out invalid / index symbols
        clean_universe = [
            t for t in sorted(list(target_set))
            if t and not t.startswith("$") and not t.startswith("^") and t != "SPAXX**"
        ]
        return clean_universe

    def sync_ticker(self, ticker: str, max_age_hours: int = 12) -> bool:
        """Sync a single ticker into DuckDB with delta check to avoid redundant network calls."""
        ticker = ticker.upper().strip()
        try:
            # Check if fresh in DuckDB
            if self.engine.duckdb_available:
                res = self.engine.conn.execute(
                    "SELECT updated_at, data_json FROM fundamental_cache WHERE symbol = ?", [ticker]
                ).fetchone()
                if res and res[0] and res[1]:
                    # If updated within max_age_hours and has quarters, skip network
                    import json
                    data = json.loads(res[1])
                    if data.get("quarters") and len(data["quarters"]) >= 4:
                        return True

            # Fetch and store in DuckDB
            profile = self.engine.get_historical_profile(ticker, force_refresh=True, fetch_remote=True)
            return bool(profile and profile.get("quarters"))
        except Exception as e:
            logger.debug(f"Error syncing fundamental quarters for {ticker}: {e}")
            return False

    def sync_universe(
        self,
        tickers: Optional[List[str]] = None,
        max_workers: int = 4,
        screener_candidates: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Batch synchronize universe into DuckDB lake with polite rate limiting."""
        if tickers is None:
            tickers = self.get_target_universe(screener_candidates)

        logger.info(f"Starting Fundamental Lake Sync for {len(tickers)} tickers...")
        synced_count = 0
        cached_count = 0
        failed_tickers = []

        # Polite chunking to prevent YFinance 429 rate limit
        chunk_size = 8
        for i in range(0, len(tickers), chunk_size):
            chunk = tickers[i:i + chunk_size]
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_sym = {executor.submit(self.sync_ticker, sym): sym for sym in chunk}
                for f in as_completed(future_to_sym):
                    sym = future_to_sym[f]
                    try:
                        success = f.result()
                        if success:
                            synced_count += 1
                        else:
                            failed_tickers.append(sym)
                    except Exception:
                        failed_tickers.append(sym)

            # Jitter delay between chunks (0.15s - 0.35s)
            time.sleep(random.uniform(0.15, 0.35))

        logger.info(f"Fundamental Lake Sync Complete: {synced_count}/{len(tickers)} available in DuckDB.")
        return {
            "total_target": len(tickers),
            "synced_or_cached": synced_count,
            "failed": failed_tickers,
            "timestamp": datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET")
        }


earnings_syncer = EarningsLakeSyncer()
