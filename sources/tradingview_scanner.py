"""TradingView universe scanner for US equities."""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from tradingview_screener import Query, col
from config import (
    DAY_TRADING_MIN_GAP,
    DAY_TRADING_MIN_PRICE,
    DAY_TRADING_MIN_MARKET_CAP,
    DAY_TRADING_MIN_AVG_VOLUME_30D,
)

logger = logging.getLogger("tradingview_scanner")

class TradingViewScanner:
    """Scans US equities using TradingView Screener API."""

    def __init__(self):
        self.fields = [
            "name",
            "description",
            "close",
            "close[1]",
            "open",
            "change",
            "change_from_open",
            "premarket_close",
            "premarket_change",
            "premarket_volume",
            "premarket_high",
            "premarket_low",
            "postmarket_close",
            "postmarket_change",
            "postmarket_volume",
            "postmarket_high",
            "postmarket_low",
            "volume",
            "average_volume_30d_calc",
            "VWAP",
            "SMA5",
            "SMA20",
            "SMA50",
            "SMA200",
            "RSI",
            "price_52_week_high",
            "price_52_week_low",
            "high",
            "high[1]",  # Yesterday's High
            "high|1W",  # Last Week's High
            "low",
            "low[1]",   # Yesterday's Low
            "low|1W",   # Last Week's Low
            "market_cap_basic",
            "relative_volume_10d_calc",
            "sector",
            "industry",
            "earnings_release_date",
            "earnings_release_next_date",
            "total_revenue",
            "gross_profit",
            "operating_income",
            "net_income",
            "earnings_per_share_fq",
            "earnings_per_share_fq_est",
            "earnings_per_share_surprise_fq_percent",
            "revenue_fq",
            "revenue_fq_est",
            "revenue_surprise_fq_percent",
            "total_debt",
            "exchange",
        ]

    def scan_universe(self) -> pd.DataFrame:
        """Scan US equities with market cap >= $1.0B and price >= $1.50 across Volume, RVOL, and Change vectors."""
        try:
            logger.info("Querying TradingView Screener for US Equities (Multi-Vector: Volume, RVOL, Gainers)...")
            
            import time
            cache_file = Path(__file__).resolve().parent.parent / "data" / "cache" / "tv_universe_cache.pkl"
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Query 1: Top Raw Volume
            q1 = (
                Query()
                .set_markets("america")
                .select(*self.fields)
                .where(
                    col("market_cap_basic") >= DAY_TRADING_MIN_MARKET_CAP,
                    col("close") >= DAY_TRADING_MIN_PRICE,
                    col("average_volume_30d_calc") >= DAY_TRADING_MIN_AVG_VOLUME_30D,
                )
                .order_by("volume", ascending=False)
                .limit(750)
            )
            df1 = None
            for attempt in range(3):
                try:
                    _, df1 = q1.get_scanner_data()
                    break
                except Exception as ex:
                    if "429" in str(ex):
                        time.sleep(1.5 * (attempt + 1))
                    else:
                        break

            time.sleep(0.3)
            # Query 2: Top Relative Volume (RVOL)
            q2 = (
                Query()
                .set_markets("america")
                .select(*self.fields)
                .where(
                    col("market_cap_basic") >= DAY_TRADING_MIN_MARKET_CAP,
                    col("close") >= DAY_TRADING_MIN_PRICE,
                    col("average_volume_30d_calc") >= DAY_TRADING_MIN_AVG_VOLUME_30D,
                )
                .order_by("relative_volume_10d_calc", ascending=False)
                .limit(500)
            )
            df2 = None
            for attempt in range(3):
                try:
                    _, df2 = q2.get_scanner_data()
                    break
                except Exception as ex:
                    if "429" in str(ex):
                        time.sleep(1.5 * (attempt + 1))
                    else:
                        break

            time.sleep(0.3)
            # Query 3: Top % Gainers / Session Momentum
            q3 = (
                Query()
                .set_markets("america")
                .select(*self.fields)
                .where(
                    col("market_cap_basic") >= DAY_TRADING_MIN_MARKET_CAP,
                    col("close") >= DAY_TRADING_MIN_PRICE,
                    col("average_volume_30d_calc") >= DAY_TRADING_MIN_AVG_VOLUME_30D,
                )
                .order_by("change", ascending=False)
                .limit(500)
            )
            df3 = None
            for attempt in range(3):
                try:
                    count, df3 = q3.get_scanner_data()
                    break
                except Exception as ex:
                    if "429" in str(ex):
                        time.sleep(1.5 * (attempt + 1))
                    else:
                        break

            # Combine and deduplicate
            dfs = [d for d in [df1, df2, df3] if d is not None and not d.empty]
            if not dfs:
                if cache_file.exists():
                    logger.info("Using cached TradingView universe due to temporary 429 rate limit.")
                    df = pd.read_pickle(cache_file)
                else:
                    return pd.DataFrame()
            else:
                df = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=["name"], keep="first")
                try:
                    df.to_pickle(cache_file)
                except Exception:
                    pass
            logger.info(f"Retrieved {len(df)} candidate tickers from TradingView (Multi-Vector Pool)")
            
            # Clean and normalize columns
            if not df.empty:
                # Ensure numeric conversions
                numeric_cols = [
                    "close", "close[1]", "open", "change", "change_from_open", "premarket_close", "premarket_change", "premarket_volume",
                    "premarket_high", "premarket_low", "postmarket_close", "postmarket_change", "postmarket_volume",
                    "postmarket_high", "postmarket_low", "volume", "average_volume_30d_calc", "high", "high[1]", "high|1W",
                    "low", "low[1]", "low|1W", "market_cap_basic", "relative_volume_10d_calc",
                    "VWAP", "SMA5", "SMA20", "SMA50", "SMA200", "RSI", "price_52_week_high", "price_52_week_low",
                    "total_revenue", "gross_profit", "operating_income", "net_income",
                    "earnings_per_share_fq", "earnings_per_share_fq_est", "earnings_per_share_surprise_fq_percent",
                    "revenue_fq", "revenue_fq_est", "revenue_surprise_fq_percent", "total_debt"
                ]
                for col_name in numeric_cols:
                    if col_name in df.columns:
                        df[col_name] = pd.to_numeric(df[col_name], errors="coerce")

                # Column aliases
                df["yesterday_high"] = df["high[1]"] if "high[1]" in df.columns else df["high"]
                df["yesterday_low"] = df["low[1]"] if "low[1]" in df.columns else df["low"]
                df["week_high"] = df["high|1W"] if "high|1W" in df.columns else df["high"]
                df["week_low"] = df["low|1W"] if "low|1W" in df.columns else df["low"]

                # Fill default strings for sector/industry if missing
                if "sector" in df.columns:
                    df["sector"] = df["sector"].fillna("General").astype(str)
                else:
                    df["sector"] = "General"

                if "industry" in df.columns:
                    df["industry"] = df["industry"].fillna("Diversified").astype(str)
                else:
                    df["industry"] = "Diversified"

            return df
        except Exception as e:
            logger.error(f"Error querying TradingView Screener API: {e}")
            return pd.DataFrame()

scanner = TradingViewScanner()
