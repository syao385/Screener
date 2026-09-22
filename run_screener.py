"""Main Orchestrator for Real-Time Institutional Market Intelligence Screener."""

import os
import sys
import json
import time
import argparse
import logging
import datetime
import webbrowser
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple, Optional

from config import (
    REPORT_HTML_PATH,
    DATA_DIR,
    DAY_TRADING_MIN_GAP,
    DAY_TRADING_MIN_PRICE,
    DAY_TRADING_MIN_MARKET_CAP,
    DAY_TRADING_MIN_AVG_VOLUME_30D,
    DAY_TRADING_MIN_RVOL,
    REALTIME_REFRESH_INTERVAL,
    TZ_EST,
)

from sources.tradingview_scanner import scanner
from sources.rvol_calculator import rvol_calc
from sources.catalyst_detector import catalyst_detector
from sources.setup_scorer import setup_scorer
from sources.macro_regime import macro_assessor
from sources.sector_flow_engine import sector_flow_engine
from sources.economic_calendar import economic_cal
from sources.earnings_calendar import earnings_cal
from sources.analyst_ratings import analyst_feed
from sources.options_flow import options_scanner
from sources.state_manager import state_mgr
from sources.pattern_detector import pattern_detector
from sources.earnings_intelligence import earnings_intel
from sources.earnings_scheduler import earnings_scheduler
from sources.thematic_intelligence import thematic_engine
from reporter.html_generator import html_generator
from reporter.terminal_viewer import terminal_viewer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("orchestrator")
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("peewee").setLevel(logging.CRITICAL)

def get_market_session(now_est: datetime.datetime) -> Tuple[str, str]:
    """
    Determine market session according to institutional anchor definitions:
    1. Premarket: 00:00 - 09:30 EST (Anchor: Midnight - 00:00 AM EST)
    2. Regular Hours: 09:30 - 16:30 EST (Anchor: 09:30 AM EST)
    3. After-Hours: 16:30 - 23:59:59 EST Mon-Thu (Anchor: 04:30 PM EST)
    4. Weekend: Friday 16:30 EST through Sunday 23:59:59 EST (Anchor: Friday 04:30 PM EST)
    """
    weekday = now_est.weekday()
    t = now_est.time()

    # Weekend: Friday 16:30 EST through Sunday 23:59:59 EST (until Monday 00:00 EST)
    if weekday >= 5:
        return "WEEKEND", "Weekend Review (Anchor: Friday 04:30 PM EST)"
    if weekday == 4 and t >= datetime.time(16, 30):
        return "WEEKEND", "Weekend Review (Anchor: Friday 04:30 PM EST)"

    # Weekdays (Mon-Thu, and Fri before 16:30 EST):
    if t < datetime.time(9, 30):
        return "PREMARKET", "Premarket Session (Anchor: 00:00 AM Midnight EST)"
    if datetime.time(9, 30) <= t < datetime.time(16, 30):
        return "REGULAR", "Regular Market Hours (Anchor: 09:30 AM EST)"
    return "POSTMARKET", "After-Hours Session (Anchor: 04:30 PM EST)"

def format_market_cap(val: float) -> str:
    """Format market cap in B / M format."""
    if pd.isna(val) or val <= 0:
        return "—"
    if val >= 1.0e12:
        return f"${val / 1.0e12:.2f}T"
    if val >= 1.0e9:
        return f"${val / 1.0e9:.2f}B"
    if val >= 1.0e6:
        return f"${val / 1.0e6:.1f}M"
    return f"${val:,.0f}"

def format_level_with_dist(level_val: Any, current_price: float, is_currency: bool = True) -> str:
    """Format price level with % distance: (current_price - level) / level * 100."""
    if level_val is None or pd.isna(level_val):
        return "—"
    try:
        raw_str = str(level_val).split("(")[0].replace("$", "").replace(",", "").strip()
        num = float(raw_str)
        if num <= 0 or current_price <= 0:
            return "—"
        dist = ((current_price - num) / num) * 100.0
        sign = "+" if dist > 0 else ""
        prefix = "$" if is_currency else ""
        return f"{prefix}{num:.2f} ({sign}{dist:.1f}%)"
    except Exception:
        return str(level_val) if level_val else "—"

import yfinance as yf

def build_yfinance_row(ticker: str) -> Optional[Dict[str, Any]]:
    """Fetch complete technical indicators for a ticker via yfinance when missing from TradingView."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1y", interval="1d")
        if hist.empty or len(hist) < 2:
            return None
        
        last_row = hist.iloc[-1]
        prev_row = hist.iloc[-2] if len(hist) > 1 else last_row
        
        close = float(last_row["Close"])
        prev_close = float(prev_row["Close"])
        open_p = float(last_row["Open"])
        high = float(last_row["High"])
        low = float(last_row["Low"])
        vol = float(last_row["Volume"])
        prev_high = float(prev_row["High"])
        prev_low = float(prev_row["Low"])
        week_high = float(hist["High"].tail(5).max()) if len(hist) >= 5 else high
        week_low = float(hist["Low"].tail(5).min()) if len(hist) >= 5 else low
        
        sma5 = float(hist["Close"].rolling(5).mean().iloc[-1]) if len(hist) >= 5 else close
        sma20 = float(hist["Close"].rolling(20).mean().iloc[-1]) if len(hist) >= 20 else close
        sma50 = float(hist["Close"].rolling(50).mean().iloc[-1]) if len(hist) >= 50 else close
        sma200 = float(hist["Close"].rolling(200).mean().iloc[-1]) if len(hist) >= 200 else close
        
        vwap = float(((hist["High"] + hist["Low"] + hist["Close"]) / 3 * hist["Volume"]).tail(5).sum() / max(1.0, hist["Volume"].tail(5).sum()))
        
        avg_vol_30 = float(hist["Volume"].tail(30).mean()) if len(hist) >= 30 else vol
        rvol_calc = vol / max(1.0, avg_vol_30)
        
        known_etfs = {
            "SOXL", "QQQ", "SPY", "SMH", "IWM", "GDXJ", "GLDM", "SILJ", "SLV",
            "COPX", "OIH", "MAGS", "SPGP", "SPMO", "CURE", "AVLV", "IEMG",
            "XLE", "XLF", "XLK", "XLV", "XLY", "XLP", "XLU", "XLI", "XLB", "VNQ", "ARKK", "TQQQ", "SQQQ"
        }
        if ticker.upper() in known_etfs:
            sector = "Exchange Traded Fund"
            industry = "ETF / Index Tracking"
            desc = f"{ticker} Index / ETF"
            mkt_cap = 50_000_000_000.0
        else:
            sector = "General"
            industry = "Diversified"
            desc = f"{ticker} Equity"
            mkt_cap = close * 100_000_000.0
            
        return {
            "name": ticker,
            "ticker": ticker,
            "description": desc,
            "close": close,
            "close[1]": prev_close,
            "open": open_p,
            "premarket_close": close,
            "premarket_change": ((open_p - prev_close) / prev_close * 100.0) if prev_close > 0 else 0.0,
            "premarket_volume": vol * 0.1,
            "premarket_high": high,
            "postmarket_close": close,
            "postmarket_change": 0.0,
            "postmarket_volume": 0.0,
            "postmarket_high": high,
            "volume": vol,
            "average_volume_30d_calc": avg_vol_30,
            "VWAP": vwap,
            "SMA5": sma5,
            "SMA20": sma20,
            "SMA50": sma50,
            "SMA200": sma200,
            "RSI": 50.0,
            "price_52_week_high": float(hist["High"].max()),
            "price_52_week_low": float(hist["Low"].min()),
            "high": high,
            "high[1]": prev_high,
            "high|1W": week_high,
            "low": low,
            "low[1]": prev_low,
            "low|1W": week_low,
            "week_high": week_high,
            "week_low": week_low,
            "yesterday_low": prev_low,
            "market_cap_basic": mkt_cap,
            "relative_volume_10d_calc": rvol_calc,
            "sector": sector,
            "industry": industry,
            "earnings_release_date": None,
            "earnings_release_next_date": None,
            "exchange": "US",
            "_sort_gap": ((close - prev_close) / prev_close * 100.0) if prev_close > 0 else 0.0
        }
    except Exception as e:
        logger.debug(f"Error fetching yfinance row for {ticker}: {e}")
        return None

def reconcile_live_quotes(eval_rows: List[Dict[str, Any]], session_type: str) -> None:
    """Reconcile real-time tick prices, previous close, and session % change via fast bulk download."""
    if not eval_rows:
        return
    
    symbols = [str(r.get("name") or r.get("ticker", "")).split(":")[-1] for r in eval_rows if str(r.get("name") or r.get("ticker", "")).split(":")[-1]]
    if not symbols:
        return

    try:
        import yfinance as yf
        chunk_size = 150
        for i in range(0, len(symbols), chunk_size):
            chunk_syms = symbols[i:i+chunk_size]
            df_bulk = yf.download(chunk_syms, period="5d", interval="1d", progress=False)
            if df_bulk is not None and not df_bulk.empty and "Close" in df_bulk:
                close_df = df_bulk["Close"]
                open_df = df_bulk["Open"] if "Open" in df_bulk else close_df
                high_df = df_bulk["High"] if "High" in df_bulk else close_df
                low_df = df_bulk["Low"] if "Low" in df_bulk else close_df
                vol_df = df_bulk["Volume"] if "Volume" in df_bulk else None
                
                is_multi = isinstance(close_df, pd.DataFrame)
                
                for r in eval_rows[i:i+chunk_size]:
                    sym = str(r.get("name") or r.get("ticker", "")).split(":")[-1]
                    try:
                        if is_multi:
                            if sym not in close_df.columns:
                                continue
                            c_series = close_df[sym].dropna()
                            o_series = open_df[sym].dropna() if sym in open_df else c_series
                            h_series = high_df[sym].dropna() if sym in high_df else c_series
                            l_series = low_df[sym].dropna() if sym in low_df else c_series
                            v_series = vol_df[sym].dropna() if (vol_df is not None and sym in vol_df) else None
                        else:
                            c_series = close_df.dropna()
                            o_series = open_df.dropna()
                            h_series = high_df.dropna()
                            l_series = low_df.dropna()
                            v_series = vol_df.dropna() if vol_df is not None else None

                        if len(c_series) >= 1:
                            live_close = float(c_series.iloc[-1])
                            prev_close = float(c_series.iloc[-2]) if len(c_series) >= 2 else live_close
                            live_open = float(o_series.iloc[-1]) if len(o_series) >= 1 else live_close
                            live_high = float(h_series.iloc[-1]) if len(h_series) >= 1 else live_close
                            live_low = float(l_series.iloc[-1]) if len(l_series) >= 1 else live_close
                            live_vol = float(v_series.iloc[-1]) if (v_series is not None and len(v_series) >= 1) else float(r.get("volume", 0.0) or 0.0)
                            
                            if live_close > 0:
                                r["close"] = live_close
                                r["open"] = live_open
                                r["high"] = live_high
                                r["low"] = live_low
                                r["close[1]"] = prev_close
                                if live_vol > 0:
                                    r["volume"] = live_vol
                                
                                if prev_close > 0:
                                    r["change"] = ((live_close - prev_close) / prev_close) * 100.0
                                if live_open > 0:
                                    r["change_from_open"] = ((live_close - live_open) / live_open) * 100.0
                    except Exception:
                        pass
    except Exception as e:
        logger.debug(f"Live quote reconciliation error: {e}")

def process_candidate(
    row: pd.Series,
    now_est: datetime.datetime,
    session_type: str,
    active_eps: Dict[str, Dict[str, Any]],
    earnings_lookup: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Process single universe candidate: compute session RVOL, evaluate Stockbee/VCP patterns, and arbitrate catalyst."""
    ticker = str(row.get("name") or row.get("ticker", "")).strip()
    clean_ticker = ticker.split(":")[-1] if ":" in ticker else ticker

    open_price = float(row.get("open", 0.0) or 0.0)
    close_price = float(row.get("close", 0.0) or 0.0)
    prev_close = float(row.get("close[1]", 0.0) or close_price)
    pre_close = float(row.get("premarket_close", 0.0) or 0.0)
    post_close = float(row.get("postmarket_close", 0.0) or 0.0)
    pre_high = float(row.get("premarket_high", 0.0) or 0.0)
    pre_low = float(row.get("premarket_low", 0.0) or 0.0)
    post_high = float(row.get("postmarket_high", 0.0) or 0.0)
    post_low = float(row.get("postmarket_low", 0.0) or 0.0)
    day_high = float(row.get("high", 0.0) or 0.0)
    prev_high = float(row.get("high[1]", 0.0) or day_high)
    mkt_cap = float(row.get("market_cap_basic", 0.0) or 0.0)
    avg_vol_30d = float(row.get("average_volume_30d_calc", 0.0) or row.get("volume", 0.0) or 0.0)
    tv_rvol = float(row.get("relative_volume_10d_calc", 1.0) or 1.0)
    pre_vol = float(row.get("premarket_volume", 0.0) or 0.0)
    post_vol = float(row.get("postmarket_volume", 0.0) or 0.0)
    cur_vol = float(row.get("volume", 0.0) or 0.0)
    sector = str(row.get("sector") or "General").strip()
    industry = str(row.get("industry") or "Diversified").strip()
    company_name = str(row.get("description") or "").strip()

    # Moving averages & VWAP (with fallback to close_price if zero)
    vwap_num = float(row.get("VWAP", 0.0) or 0.0)
    if vwap_num <= 0:
        vwap_num = close_price
    sma5_num = float(row.get("SMA5", 0.0) or 0.0)
    if sma5_num <= 0:
        sma5_num = close_price
    sma20_num = float(row.get("SMA20", 0.0) or 0.0)
    if sma20_num <= 0:
        sma20_num = close_price
    sma50_num = float(row.get("SMA50", 0.0) or 0.0)
    if sma50_num <= 0:
        sma50_num = close_price
    sma200_num = float(row.get("SMA200", 0.0) or 0.0)
    if sma200_num <= 0:
        sma200_num = close_price

    rsi_val = float(row.get("RSI", 50.0) or 50.0)
    price_52w_high = float(row.get("price_52_week_high", 0.0) or 0.0)
    price_52w_low = float(row.get("price_52_week_low", 0.0) or 0.0)

    # 1. Base % Chg
    tv_chg = row.get("change")
    if tv_chg is not None and not pd.isna(tv_chg):
        base_pct_change = float(tv_chg)
    elif close_price > 0 and prev_close > 0:
        base_pct_change = ((close_price - prev_close) / prev_close) * 100.0
    else:
        base_pct_change = 0.0

    # 2. Session Gap % & Evaluation Price
    base_prev = prev_close if prev_close > 0 else close_price
    day_gap = ((open_price - base_prev) / base_prev * 100.0) if (open_price > 0 and base_prev > 0) else 0.0

    if session_type == "PREMARKET":
        current_price = pre_close if pre_close > 0 else close_price
        ref_high = pre_high if pre_high > 0 else (day_high if day_high > 0 else prev_high)
        tv_pm_chg = row.get("premarket_change")
        if tv_pm_chg is not None and not pd.isna(tv_pm_chg) and pre_close > 0:
            gap_pct = float(tv_pm_chg)
        elif pre_close > 0 and base_prev > 0:
            gap_pct = ((pre_close - base_prev) / base_prev) * 100.0
        else:
            gap_pct = day_gap
        eval_vol = pre_vol
        pct_change = gap_pct if pre_close > 0 else base_pct_change

    elif session_type in ["POSTMARKET", "WEEKEND"]:
        has_post_trade = post_close > 0 and abs(post_close - close_price) > 0.001
        tv_post_chg = row.get("postmarket_change")
        if tv_post_chg is not None and not pd.isna(tv_post_chg) and has_post_trade:
            post_gap = float(tv_post_chg)
        elif has_post_trade and close_price > 0:
            post_gap = ((post_close - close_price) / close_price) * 100.0
        else:
            post_gap = 0.0

        if has_post_trade and abs(post_gap) >= 0.2:
            # Active extended-hours mover (e.g. after-hours earnings or breaking catalyst anchored to 16:30)
            current_price = post_close
            ref_high = post_high if post_high > 0 else (day_high if day_high > 0 else prev_high)
            gap_pct = post_gap
            pct_change = ((post_close - base_prev) / base_prev * 100.0) if base_prev > 0 else base_pct_change
            eval_vol = post_vol if post_vol > 0 else cur_vol
        else:
            # Normal overnight / weekend review of settled regular session (anchored to 09:30)
            current_price = close_price if close_price > 0 else (post_close if post_close > 0 else open_price)
            ref_high = prev_high if prev_high > 0 else day_high
            gap_pct = day_gap if abs(day_gap) > 0.0 else post_gap
            pct_change = base_pct_change
            eval_vol = cur_vol

    else: # REGULAR
        current_price = close_price if close_price > 0 else open_price
        ref_high = prev_high if prev_high > 0 else day_high
        if open_price > 0 and base_prev > 0:
            gap_pct = ((open_price - base_prev) / base_prev) * 100.0
        elif pre_close > 0 and base_prev > 0:
            gap_pct = ((pre_close - base_prev) / base_prev) * 100.0
        else:
            tv_pm_chg = row.get("premarket_change")
            gap_pct = float(tv_pm_chg) if (tv_pm_chg is not None and not pd.isna(tv_pm_chg)) else 0.0
        eval_vol = cur_vol
        pct_change = ((current_price - base_prev) / base_prev * 100.0) if (base_prev > 0 and current_price > 0) else base_pct_change

    # % from Open
    tv_open_chg = row.get("change_from_open")
    if tv_open_chg is not None and not pd.isna(tv_open_chg):
        pct_from_open = float(tv_open_chg)
    elif open_price > 0 and current_price > 0:
        pct_from_open = ((current_price - open_price) / open_price) * 100.0
    else:
        pct_from_open = 0.0

    # Moving Average % Distances
    vwap_dist = ((current_price - vwap_num) / vwap_num * 100.0) if vwap_num > 0 else 0.0
    sma5_dist = ((current_price - sma5_num) / sma5_num * 100.0) if sma5_num > 0 else 0.0
    sma20_dist = ((current_price - sma20_num) / sma20_num * 100.0) if sma20_num > 0 else 0.0
    sma50_dist = ((current_price - sma50_num) / sma50_num * 100.0) if sma50_num > 0 else 0.0
    sma200_dist = ((current_price - sma200_num) / sma200_num * 100.0) if sma200_num > 0 else 0.0

    # Session RVOL Calculation:
    # Anchored strictly to:
    # - PREMARKET: Midnight - 00:00 AM EST (cumulative volume [00:00 -> T] vs 20d avg [00:00 -> T])
    # - REGULAR: 09:30 AM EST (cumulative volume [09:30 -> T] vs 20d avg [09:30 -> T])
    # - POSTMARKET: 04:30 PM EST (cumulative volume [16:30 -> T] vs 20d avg [16:30 -> T])
    # - WEEKEND: Friday 04:30 PM EST (cumulative volume [Friday 16:30 -> 20:00] vs 20d avg [16:30 -> 20:00])
    is_active_pm_mover = (session_type in ["POSTMARKET", "WEEKEND"] and has_post_trade and abs(post_gap) >= 0.2 and post_vol > 0)
    effective_session = session_type if is_active_pm_mover else ("PREMARKET" if session_type == "PREMARKET" else "REGULAR")

    rvol = rvol_calc.calculate_session_rvol(
        ticker=clean_ticker,
        session_type=effective_session,
        current_volume=eval_vol,
        adv_20d=avg_vol_30d,
        tv_rvol=tv_rvol,
        target_time=now_est.time()
    )

    # Format Earnings Date (Prioritize Finviz Real-Time Calendar)
    earn_str = "—"
    if earnings_lookup and clean_ticker in earnings_lookup:
        earn_str = earnings_lookup[clean_ticker]
    else:
        next_earn_ts = row.get("earnings_release_next_date")
        prev_earn_ts = row.get("earnings_release_date")
        target_ts = next_earn_ts if (next_earn_ts and not pd.isna(next_earn_ts)) else prev_earn_ts
        if target_ts and not pd.isna(target_ts):
            try:
                ts_val = float(target_ts)
                if ts_val > 0:
                    dt_earn = datetime.datetime.fromtimestamp(ts_val, tz=datetime.timezone.utc)
                    earn_timing = " a" if dt_earn.hour >= 18 else (" b" if dt_earn.hour <= 14 else "")
                    earn_str = dt_earn.strftime("%b %d") + earn_timing
            except Exception:
                earn_str = "—"

    # Detect and arbitrate catalyst
    cat_res = catalyst_detector.detect_catalyst(clean_ticker, company_name=company_name, earnings_date=earn_str)
    if len(cat_res) == 6:
        cat_type, cat_stars, cat_headline, cat_url, is_positive, cat_date = cat_res
    else:
        cat_type, cat_stars, cat_headline, cat_url, is_positive = cat_res[:5]
        cat_date = "—"

    # Multi-level Breakout & Breakdown flags
    day_low_val = float(row.get("low", 0.0) or 0.0)
    prev_low = float(row.get("low[1]", 0.0) or row.get("yesterday_low", 0.0) or day_low_val)
    week_high = float(row.get("high|1W", 0.0) or row.get("week_high", 0.0) or day_high)
    week_low = float(row.get("low|1W", 0.0) or row.get("week_low", 0.0) or (day_low_val if day_low_val > 0 else current_price))

    breakout_week_high = (current_price >= week_high) if week_high > 0 else False
    breakout_last_high = (current_price >= ref_high) if ref_high > 0 else False
    breakout_pm_high = (pre_high > 0 and current_price >= pre_high)

    breakdown_pm_low = (pre_low > 0 and current_price <= pre_low)
    breakdown_week_low = (current_price <= week_low) if week_low > 0 else False
    breakdown_last_low = (current_price <= prev_low) if prev_low > 0 else False

    # Dynamic VWAP standard deviations
    intraday_rng = (day_high - day_low_val) if (day_high > day_low_val > 0) else (current_price * 0.02)
    vwap_std_val = max(vwap_num * 0.0075, intraday_rng / 2.8) if vwap_num > 0 else (current_price * 0.01)
    vwap_std_pct = (vwap_std_val / vwap_num * 100.0) if vwap_num > 0 else 1.0

    vwap_std_p1 = (vwap_dist >= vwap_std_pct)
    vwap_std_p2 = (vwap_dist >= 2.0 * vwap_std_pct)
    vwap_std_m1 = (vwap_dist <= -vwap_std_pct)
    vwap_std_m2 = (vwap_dist <= -2.0 * vwap_std_pct)

    # Crossing detections
    vwap_xo = (vwap_num > 0 and current_price >= vwap_num and (day_low_val < vwap_num or open_price < vwap_num) and vwap_dist <= 2.0)
    vwap_xu = (vwap_num > 0 and current_price <= vwap_num and (day_high > vwap_num or open_price > vwap_num) and vwap_dist >= -2.0)

    sma5_xo = (sma5_num > 0 and current_price >= sma5_num and (prev_close < sma5_num or day_low_val < sma5_num) and sma5_dist <= 2.0)
    sma5_xu = (sma5_num > 0 and current_price <= sma5_num and (prev_close > sma5_num or day_high > sma5_num) and sma5_dist >= -2.0)

    sma20_xo = (sma20_num > 0 and current_price >= sma20_num and (prev_close < sma20_num or day_low_val < sma20_num) and sma20_dist <= 2.0)
    sma20_xu = (sma20_num > 0 and current_price <= sma20_num and (prev_close > sma20_num or day_high > sma20_num) and sma20_dist >= -2.0)

    sma50_xo = (sma50_num > 0 and current_price >= sma50_num and (prev_close < sma50_num or day_low_val < sma50_num) and sma50_dist <= 2.0)
    sma50_xu = (sma50_num > 0 and current_price <= sma50_num and (prev_close > sma50_num or day_high > sma50_num) and sma50_dist >= -2.0)

    sma200_xo = (sma200_num > 0 and current_price >= sma200_num and (prev_close < sma200_num or day_low_val < sma200_num) and sma200_dist <= 2.0)
    sma200_xu = (sma200_num > 0 and current_price <= sma200_num and (prev_close > sma200_num or day_high > sma200_num) and sma200_dist >= -2.0)

    # -----------------------------------------------------------------
    # Stockbee & Minervini Pattern Recognition
    # -----------------------------------------------------------------
    active_ep = active_eps.get(clean_ticker)
    pattern_info = pattern_detector.evaluate_patterns(
        ticker=clean_ticker,
        price=current_price,
        open_price=open_price,
        pct_change=pct_change,
        gap_pct=gap_pct,
        pct_from_open=pct_from_open,
        rvol=rvol,
        volume=cur_vol if cur_vol > 0 else eval_vol,
        avg_vol_30d=avg_vol_30d,
        premarket_change=float(row.get("premarket_change", 0.0) or 0.0),
        premarket_high=pre_high,
        premarket_low=pre_low,
        yesterday_high=ref_high,
        yesterday_low=prev_low,
        week_high=week_high,
        week_low=week_low,
        vwap_num=vwap_num,
        sma5_num=sma5_num,
        sma20_num=sma20_num,
        sma50_num=sma50_num,
        sma200_num=sma200_num,
        rsi_val=rsi_val,
        price_52w_high=price_52w_high,
        price_52w_low=price_52w_low,
        catalyst_stars=cat_stars,
        catalyst_type=cat_type,
        is_positive_catalyst=is_positive,
        active_ep_record=active_ep
    )

    # Register Day 1 EP into SQLite if detected
    today_str = now_est.strftime("%Y-%m-%d")
    if pattern_info.get("is_ep_day1"):
        state_mgr.register_or_update_ep(
            ticker=clean_ticker,
            ep_date=today_str,
            day1_open=open_price,
            day1_high=day_high,
            day1_low=day_low_val,
            day1_close=current_price,
            day1_vwap=vwap_num,
            day1_volume=cur_vol,
            day1_gap_pct=gap_pct,
            catalyst_type=cat_type,
            catalyst_headline=cat_headline,
            catalyst_stars=cat_stars
        )

    # Record daily bar to SQLite
    state_mgr.record_daily_bar(
        ticker=clean_ticker,
        trade_date=today_str,
        open_p=open_price,
        high_p=day_high,
        low_p=day_low_val,
        close_p=current_price,
        volume=cur_vol,
        vwap=vwap_num,
        pct_change=pct_change
    )

    streak_data = state_mgr.get_streak_info(clean_ticker)

    return {
        "ticker": clean_ticker,
        "price": current_price,
        "prev_close": prev_close,
        "open_price": open_price,
        "regular_close": close_price,
        "pct_change": pct_change,
        "gap_pct": gap_pct,
        "pct_from_open": pct_from_open,
        "rvol": rvol,
        "market_cap": mkt_cap,
        "market_cap_str": format_market_cap(mkt_cap),
        "avg_vol_30d": avg_vol_30d,
        "yesterday_high": ref_high,
        "premarket_high": pre_high,
        "day_high": day_high,
        "day_low": day_low_val,
        "yesterday_high_dist": format_level_with_dist(ref_high, current_price),
        "premarket_high_dist": format_level_with_dist(pre_high, current_price),
        "sector": sector,
        "industry": industry,
        "earnings_date": earn_str,
        "catalyst_type": cat_type,
        "catalyst_stars": cat_stars,
        "catalyst_date": cat_date,
        "headline": cat_headline,
        "catalyst_url": cat_url,
        "is_positive": is_positive,
        "vwap": format_level_with_dist(vwap_num, current_price),
        "sma5": format_level_with_dist(sma5_num, current_price),
        "sma20": format_level_with_dist(sma20_num, current_price),
        "sma50": format_level_with_dist(sma50_num, current_price),
        "sma200": format_level_with_dist(sma200_num, current_price),
        "vwap_num": vwap_num,
        "sma5_num": sma5_num,
        "sma20_num": sma20_num,
        "sma50_num": sma50_num,
        "sma200_num": sma200_num,
        "rsi_val": rsi_val,
        "vwap_dist": vwap_dist,
        "vwap_std_p1": vwap_std_p1,
        "vwap_std_p2": vwap_std_p2,
        "vwap_std_m1": vwap_std_m1,
        "vwap_std_m2": vwap_std_m2,
        "sma5_dist": sma5_dist,
        "sma20_dist": sma20_dist,
        "sma50_dist": sma50_dist,
        "sma200_dist": sma200_dist,
        "vwap_xo": vwap_xo,
        "vwap_xu": vwap_xu,
        "sma5_xo": sma5_xo,
        "sma5_xu": sma5_xu,
        "sma20_xo": sma20_xo,
        "sma20_xu": sma20_xu,
        "sma50_xo": sma50_xo,
        "sma50_xu": sma50_xu,
        "sma200_xo": sma200_xo,
        "sma200_xu": sma200_xu,
        "breakout_last_high": breakout_last_high,
        "breakout_pm_high": breakout_pm_high,
        "breakout_week_high": breakout_week_high,
        "breakdown_pm_low": breakdown_pm_low,
        "breakdown_week_low": breakdown_week_low,
        "breakdown_last_low": breakdown_last_low,
        "week_high": week_high,
        "week_low": week_low,
        "yesterday_low": prev_low,
        # Pattern & Stockbee Enhancements
        "pattern_info": pattern_info,
        "primary_pattern": pattern_info.get("primary_pattern", "MOMENTUM_RUNNER"),
        "pattern_badge": pattern_info.get("badge_label", "⚡ Momentum"),
        "preset_tags": " ".join(
            pattern_info.get("preset_tags", ["ALL_SETUPS"]) + 
            (["THEMATIC_UNIVERSE"] if thematic_engine.get_ticker_meta(clean_ticker) else [])
        ),
        "thematic_meta": thematic_engine.get_ticker_meta(clean_ticker),
        "is_exhausted": pattern_info.get("is_exhausted", False),
        "exhaustion_flag": pattern_info.get("exhaustion_flag", "CLEAN"),
        "exhaustion_desc": pattern_info.get("exhaustion_desc", ""),
        "stockbee_score": pattern_info.get("stockbee_score", 5.0),
        "streak_direction": streak_data.get("direction", "NEUTRAL"),
        "streak_count": streak_data.get("count", 0),
    }

def run_screener_pipeline(open_browser: bool = True, force_refresh: bool = False) -> Any:
    """Execute complete real-time screening and report generation pipeline."""
    now_est = datetime.datetime.now(TZ_EST)
    session_type, session_label = get_market_session(now_est)
    today_str = now_est.strftime("%Y-%m-%d")
    logger.info(f"Starting Screener Pipeline [{session_label}] at {now_est.strftime('%Y-%m-%d %H:%M:%S %Z')}...")

    # Advance SQLite EP day counts
    state_mgr.advance_ep_day_counts(today_str)
    active_eps = state_mgr.get_active_eps()

    # 1. Ingest Macro Regime (01_macro-regime.md)
    logger.info("Step 1/6: Assessing Macro Regime...")
    macro_data = macro_assessor.assess_macro_regime(force_refresh=force_refresh)
    comp_regime = macro_data.get("composite_regime", "Neutral")

    # 1b. Ingest Sector & Thematic Flows (14_institutional-flows.md & 02_industry-funnel.md)
    logger.info("Step 1b: Assessing Sector & Sub-Industry ETF Capital Flows...")
    try:
        sector_flow_data = sector_flow_engine.get_sector_flow_matrix(force_refresh=force_refresh)
    except Exception as e:
        logger.warning(f"Could not compute sector flows: {e}")
        sector_flow_data = {"sectors": [], "top_inflows": [], "top_outflows": [], "sub_industries": {}}

    # 2. Ingest Economic Calendar (Weekly Outlook)
    logger.info("Step 2/6: Ingesting US Economic Calendar (Weekly Outlook)...")
    economic_events = economic_cal.get_week_events()

    # 3. Ingest Earnings Calendar
    logger.info("Step 3/6: Ingesting Finviz Earnings Calendar...")
    earnings_data = earnings_cal.get_earnings_dashboard()

    # 4. Scan US Equities Universe (TradingView Screener API)
    logger.info("Step 4/6: Scanning US Equities Universe from TradingView...")
    raw_df = scanner.scan_universe()

    candidate_rows = []
    if not raw_df.empty:
        for _, row in raw_df.iterrows():
            ticker = str(row.get("name") or row.get("ticker", "")).strip()
            clean_sym = ticker.split(":")[-1] if ":" in ticker else ticker
            if clean_sym in ("SPY", "QQQ", "IWM", "SQQQ", "TQQQ"):
                continue

            mkt_cap = float(row.get("market_cap_basic", 0.0) or 0.0)
            avg_vol = float(row.get("average_volume_30d_calc", 0.0) or row.get("volume", 0.0) or 0.0)
            cur_vol = float(row.get("volume", 0.0) or 0.0)
            close = float(row.get("close", 0.0) or 0.0)
            post_close = float(row.get("postmarket_close", 0.0) or 0.0)
            pre_close = float(row.get("premarket_close", 0.0) or 0.0)

            # Determine price & session gap for prioritization
            if session_type == "PREMARKET":
                price = pre_close if pre_close > 0 else close
                tv_pm_chg = row.get("premarket_change")
                if tv_pm_chg is not None and not pd.isna(tv_pm_chg) and pre_close > 0:
                    gap = float(tv_pm_chg)
                elif pre_close > 0 and close > 0:
                    gap = ((pre_close - close) / close) * 100.0
                else:
                    gap = 0.0
            elif session_type == "POSTMARKET":
                price = post_close if post_close > 0 else close
                tv_post_chg = row.get("postmarket_change")
                if tv_post_chg is not None and not pd.isna(tv_post_chg) and post_close > 0:
                    gap = float(tv_post_chg)
                elif post_close > 0 and close > 0:
                    gap = ((post_close - close) / close) * 100.0
                else:
                    gap = 0.0
            else:
                price = close
                open_val = float(row.get("open", 0.0) or 0.0)
                prev_close = float(row.get("close[1]", 0.0) or close)
                if open_val > 0 and prev_close > 0:
                    gap = ((open_val - prev_close) / prev_close * 100.0)
                elif pre_close > 0 and prev_close > 0:
                    gap = ((pre_close - prev_close) / prev_close * 100.0)
                else:
                    tv_pm_chg = row.get("premarket_change")
                    gap = float(tv_pm_chg) if (tv_pm_chg is not None and not pd.isna(tv_pm_chg)) else 0.0

            # Base Universal Ingestion Standards: Cap >= $1.0B, Vol >= 500k, Price >= $1.50
            if (mkt_cap >= DAY_TRADING_MIN_MARKET_CAP and 
                (avg_vol >= DAY_TRADING_MIN_AVG_VOLUME_30D or cur_vol >= DAY_TRADING_MIN_AVG_VOLUME_30D) and 
                price >= DAY_TRADING_MIN_PRICE):
                row_dict = row.to_dict()
                row_dict["_sort_gap"] = gap
                candidate_rows.append(row_dict)

    # Identify portfolio tickers to ensure 100% market intelligence coverage
    from sources.portfolio_manager import portfolio_mgr, extract_underlying_ticker
    raw_port_data = portfolio_mgr.load_portfolio()
    port_tickers_set = set()
    for p in raw_port_data.get("positions", []):
        u_sym = extract_underlying_ticker(p.get("raw_symbol") or p.get("symbol", ""))
        if u_sym:
            port_tickers_set.add(u_sym)

    # Prioritize universe candidates: Top Gainers (% change), Big Gappers, High RVOL, and Volume leaders
    candidate_rows.sort(
        key=lambda r: max(
            float(r.get("change", 0.0) or 0.0),
            abs(float(r.get("_sort_gap", 0.0) or 0.0)),
            float(r.get("relative_volume_10d_calc", 1.0) or 1.0) * 2.0
        ),
        reverse=True
    )
    selected_universe_rows = candidate_rows[:350]

    # Map TradingView rows by clean ticker symbol
    tv_rows_by_sym = {str(r.get("name") or r.get("ticker", "")).split(":")[-1]: r.to_dict() for _, r in raw_df.iterrows()}

    # Build Finviz real-time earnings timing lookup
    finviz_earnings_lookup = {}
    for item in earnings_data.get("today_bmo", []):
        finviz_earnings_lookup[item["ticker"]] = item.get("timing", f"{now_est.strftime('%b %d')} b")
    for item in earnings_data.get("today_amc", []):
        finviz_earnings_lookup[item["ticker"]] = item.get("timing", f"{now_est.strftime('%b %d')} a")
    for item in earnings_data.get("yesterday_amc", []):
        finviz_earnings_lookup[item["ticker"]] = item.get("timing", f"{(now_est - datetime.timedelta(days=1)).strftime('%b %d')} a")
    for item in earnings_data.get("tomorrow_bmo", []):
        finviz_earnings_lookup[item["ticker"]] = item.get("timing", f"{(now_est + datetime.timedelta(days=1)).strftime('%b %d')} b")
    for item in earnings_data.get("tomorrow_amc", []):
        finviz_earnings_lookup[item["ticker"]] = item.get("timing", f"{(now_est + datetime.timedelta(days=1)).strftime('%b %d')} a")

    # Dynamically batch-fetch full extended-hours quotes from TradingView for any missing portfolio, earnings & thematic chokepoint symbols
    thematic_tickers = {item["ticker"] for item in thematic_engine.get_curated_thematic_universe()}
    priority_syms_to_fetch = [
        s for s in (port_tickers_set | set(finviz_earnings_lookup.keys()) | thematic_tickers)
        if s not in tv_rows_by_sym and not s.startswith("$") and s != "SPAXX**"
    ]
    if priority_syms_to_fetch:
        try:
            from tradingview_screener import Query, col
            from sources.tradingview_scanner import scanner as tv_scan_inst
            q_extra = Query().set_markets("america").select(*tv_scan_inst.fields).where(col("name").isin(priority_syms_to_fetch[:100]))
            _, extra_df = q_extra.get_scanner_data()
            if extra_df is not None and not extra_df.empty:
                for _, r in extra_df.iterrows():
                    clean_s = str(r.get("name") or r.get("ticker", "")).split(":")[-1]
                    tv_rows_by_sym[clean_s] = r.to_dict()
                logger.info(f"Dynamically ingested {len(extra_df)} missing priority portfolio & earnings tickers from TradingView")
                try:
                    import pickle
                    from pathlib import Path
                    cache_file = Path(__file__).resolve().parent / "data" / "cache" / "tv_universe_cache.pkl"
                    if cache_file.exists():
                        with open(cache_file, "rb") as f:
                            cached_df = pickle.load(f)
                        combined_df = pd.concat([cached_df, extra_df], ignore_index=True).drop_duplicates(subset=["name"], keep="last")
                        with open(cache_file, "wb") as f:
                            pickle.dump(combined_df, f)
                        from sources.defeatbeta_client import defeatbeta_client
                        defeatbeta_client._tv_map_cache = {str(r.get("name") or r.get("ticker", "")).split(":")[-1].upper(): r.to_dict() for _, r in combined_df.iterrows()}
                except Exception:
                    pass
        except Exception as ex:
            logger.debug(f"Dynamic priority TradingView scan error: {ex}")

    # Guarantee full market row for every portfolio underlying ticker
    port_candidate_rows = []
    for u_sym in port_tickers_set:
        if u_sym in tv_rows_by_sym:
            port_candidate_rows.append(tv_rows_by_sym[u_sym])
        else:
            yf_row = build_yfinance_row(u_sym)
            if yf_row:
                port_candidate_rows.append(yf_row)

    # Merge universe candidates and portfolio rows without duplicates
    combined_eval_dict = {}
    for r in selected_universe_rows + port_candidate_rows:
        sym = str(r.get("name") or r.get("ticker", "")).split(":")[-1]
        if sym and sym not in combined_eval_dict:
            combined_eval_dict[sym] = r

    # Guarantee 100% inclusion for all Finviz Earnings Calendar tickers
    for ep_sym in finviz_earnings_lookup.keys():
        if ep_sym not in combined_eval_dict:
            if ep_sym in tv_rows_by_sym:
                combined_eval_dict[ep_sym] = tv_rows_by_sym[ep_sym]
            else:
                yf_row = build_yfinance_row(ep_sym)
                if yf_row:
                    combined_eval_dict[ep_sym] = yf_row

    all_eval_rows = list(combined_eval_dict.values())
    
    # Ensure SQLite state has seeded historical EPs across past 5 trading days
    if len(active_eps) < 10:
        seed_pool = [str(r.get("name") or r.get("ticker", "")).split(":")[-1] for r in all_eval_rows]
        state_mgr.backfill_historical_eps(seed_pool, lookback_days=5)
        active_eps = state_mgr.get_active_eps()
        logger.info(f"Active Multi-Day EPs in tracking: {len(active_eps)}")

    # Guarantee all active 5-day EP tickers from SQLite DB are included in evaluation
    for ep_sym in active_eps.keys():
        if ep_sym not in combined_eval_dict:
            if ep_sym in tv_rows_by_sym:
                combined_eval_dict[ep_sym] = tv_rows_by_sym[ep_sym]
            else:
                yf_row = build_yfinance_row(ep_sym)
                if yf_row:
                    combined_eval_dict[ep_sym] = yf_row

    # Guarantee 100% inclusion for all Curated Thematic & Chokepoint tickers
    thematic_universe_items = thematic_engine.get_curated_thematic_universe()
    for th_item in thematic_universe_items:
        th_sym = th_item["ticker"]
        if th_sym not in combined_eval_dict:
            if th_sym in tv_rows_by_sym:
                combined_eval_dict[th_sym] = tv_rows_by_sym[th_sym]
            else:
                yf_row = build_yfinance_row(th_sym)
                if yf_row:
                    combined_eval_dict[th_sym] = yf_row

    all_eval_rows = list(combined_eval_dict.values())
    reconcile_live_quotes(all_eval_rows, session_type)
    logger.info(f"Evaluating {len(all_eval_rows)} prioritized candidate, portfolio, 5-day EP & thematic tickers in parallel...")
    
    processed_candidates = []
    if all_eval_rows:
        with ThreadPoolExecutor(max_workers=25) as executor:
            future_to_sym = {executor.submit(process_candidate, pd.Series(row), now_est, session_type, active_eps, finviz_earnings_lookup): row for row in all_eval_rows}
            for future in as_completed(future_to_sym):
                try:
                    res = future.result()
                    if res and res.get("ticker"):
                        processed_candidates.append(res)
                except Exception as e:
                    logger.debug(f"Candidate processing error: {e}")

    # Compute Institutional Qualification Flag for each candidate
    for item in processed_candidates:
        gap_pct = item["gap_pct"]
        rvol = item["rvol"]
        cat_stars = item["catalyst_stars"]
        is_pos = item["is_positive"]
        breakout_last = item["breakout_last_high"]
        breakout_pm = item["breakout_pm_high"]

        # Strict institutional criteria
        if session_type == "REGULAR":
            inst_pass = (gap_pct >= DAY_TRADING_MIN_GAP and rvol >= DAY_TRADING_MIN_RVOL and cat_stars >= 2.0 and is_pos and breakout_last and breakout_pm)
        else:
            inst_pass = (gap_pct >= DAY_TRADING_MIN_GAP and rvol >= DAY_TRADING_MIN_RVOL and cat_stars >= 2.0 and is_pos and breakout_last)

        item["is_inst_qualified"] = inst_pass

    day_watchlist = processed_candidates
    logger.info(f"Screened Watchlist tickers: {len(day_watchlist)} (Institutional qualified: {sum(1 for x in day_watchlist if x.get('is_inst_qualified'))})")

    # 5. Ingest Analyst Actions & 45-Day Gamma Exposure Structure
    logger.info("Step 5/6: Fetching Analyst Actions & 45-Day Options Structure...")
    ordered_candidate_tickers = list(port_tickers_set) + ["SPY", "QQQ", "IWM"] + [x["ticker"] for x in day_watchlist if x["ticker"] not in port_tickers_set]
    analyst_actions = analyst_feed.get_market_upgrades(watchlist_tickers=ordered_candidate_tickers)
    options_aggregated, ticker_gamma_lookup = options_scanner.get_market_options_flow(watchlist_tickers=ordered_candidate_tickers)

    # Build analyst lookup
    analyst_lookup: Dict[str, str] = {}
    for act in analyst_actions:
        t_sym = act["ticker"]
        if t_sym not in analyst_lookup:
            analyst_lookup[t_sym] = f"{act.get('action', 'Rating')}: {act.get('rating', '')}"

    # Tiered Flash Earnings: Zero-Redundancy Fundamental Caching & Change Detection
    # Only pull remote fundamentals when there are breaking earnings releases or when force_refresh=True
    from sources.earnings_intelligence import KNOWN_ETFS
    
    is_weekend = (now_est.weekday() >= 5)

    breaking_earnings_syms = set()
    if earnings_data and not is_weekend:
        for bucket in ("yesterday_amc", "today_bmo", "today_amc"):
            for it in earnings_data.get(bucket, []):
                t_s = (it.get("ticker") or "").upper().strip()
                if t_s and t_s not in KNOWN_ETFS:
                    breaking_earnings_syms.add(t_s)

    # Catalyst & Event-Driven Set: Only re-evaluate fundamentals for tickers with active catalyst events
    material_catalyst_syms = set(breaking_earnings_syms) | set(port_tickers_set)
    for it in day_watchlist:
        sym = (it.get("ticker") or "").upper().strip()
        if not sym or sym in KNOWN_ETFS:
            continue
        stars = float(it.get("catalyst_stars", 0.0) or 0.0)
        c_type = str(it.get("catalyst_type", "") or "")
        if stars >= 4.0 or c_type in ("EARNINGS_BEAT", "CONTRACT_WIN", "FDA_APPROVAL", "MA_RUMOR", "GUIDANCE_RAISE", "PARTNERSHIP"):
            material_catalyst_syms.add(sym)

    flash_results_map = {}
    
    # 1. Reuse pre-cached batch reports from summary.json
    if not force_refresh:
        try:
            existing_summary = earnings_scheduler.get_summary_reports()
            for rep in existing_summary.get("reports", []):
                rep_sym = (rep.get("ticker") or "").upper().strip()
                if rep_sym and rep.get("flash_summary"):
                    f_factors = (rep.get("flash_summary") or {}).get("factors") or {}
                    # If this is not an active breaking earnings stock missing reported EPS, reuse cached summary
                    if rep_sym not in breaking_earnings_syms or f_factors.get("actual_eps") is not None:
                        flash_results_map[rep_sym] = rep["flash_summary"]
        except Exception as e:
            logger.debug(f"Error loading summary.json cache: {e}")

        # 2. Also check individual reports in data/earnings_reports/*.json
        try:
            reports_dir = DATA_DIR / "earnings_reports"
            if reports_dir.exists():
                for r_path in reports_dir.glob("*.json"):
                    r_sym = r_path.stem.upper().strip()
                    if r_sym and r_sym not in flash_results_map:
                        try:
                            with open(r_path, "r", encoding="utf-8") as f:
                                r_data = json.load(f)
                                if r_data.get("flash_summary"):
                                    flash_results_map[r_sym] = r_data["flash_summary"]
                        except Exception:
                            pass
        except Exception as e:
            logger.debug(f"Error loading earnings_reports cache: {e}")

    # 3. Catalyst-Driven Evaluation:
    # Only pull remote data or run fundamental calculations for:
    #   a) Breaking earnings symbols (today/yesterday)
    #   b) High-impact material catalysts (4-5 star news, FDA, Contract wins, Guidance revisions)
    #   c) Portfolio holdings
    #   d) When force_refresh is True
    # For all non-catalyst stocks over the weekend or regular hours, strictly read local cache (fetch_remote=False)
    tickers_to_evaluate = []
    for item in day_watchlist:
        sym = item["ticker"]
        if sym in KNOWN_ETFS:
            continue
        # If already cached in memory, re-use instantly with 0ms latency
        if sym in flash_results_map:
            continue
        if sym in earnings_intel._flash_cache and not force_refresh:
            flash_results_map[sym] = earnings_intel._flash_cache[sym]
            continue
        
        # Determine if remote fetch is permitted (Never remote on weekends unless forced)
        should_fetch_remote = (not is_weekend) and (force_refresh or (sym in breaking_earnings_syms))
        
        # Only spend compute on active catalyst events, breaking earnings, portfolio holdings, or forced refresh
        if sym in material_catalyst_syms or force_refresh:
            tickers_to_evaluate.append((item, should_fetch_remote))

    if tickers_to_evaluate:
        with ThreadPoolExecutor(max_workers=min(20, len(tickers_to_evaluate))) as flash_executor:
            future_to_item = {
                flash_executor.submit(
                    earnings_intel.analyze_flash_earnings,
                    item["ticker"],
                    item["price"],
                    item["gap_pct"],
                    item["rvol"],
                    fetch_remote
                ): item["ticker"]
                for item, fetch_remote in tickers_to_evaluate
            }
            for fut in as_completed(future_to_item):
                sym = future_to_item[fut]
                try:
                    flash_results_map[sym] = fut.result()
                except Exception as e:
                    logger.debug(f"Earnings flash error for {sym}: {e}")

    # Attach Analyst, Options Gamma, Setup Score, and Earnings Flash for ALL evaluated tickers
    for item in day_watchlist:
        sym = item["ticker"]
        cur_price = item["price"]
        gap_pct = item.get("gap_pct", 0.0)
        rvol = item.get("rvol", 1.0)
        item["analyst_rating"] = analyst_lookup.get(sym, "—")

        # Ensure earnings flash reflects real Day 1 metrics, with fallback to screener price
        ef = flash_results_map.get(sym)
        if ef:
            if not ef.get("current_price") or ef.get("current_price") == 0:
                ef["current_price"] = cur_price
            if ef.get("gap_pct") is None or ef.get("gap_pct") == 0:
                ef["gap_pct"] = gap_pct
            if not ef.get("rvol") or ef.get("rvol") == 1.0:
                ef["rvol"] = rvol
            item["earnings_flash"] = ef

        # Gamma & Options Structure
        gamma_info = ticker_gamma_lookup.get(sym)
        if gamma_info:
            raw_cw = gamma_info.get("call_wall", "—")
            raw_pw = gamma_info.get("put_wall", "—")
            raw_flip = gamma_info.get("gamma_flip", "—")
            item["call_wall"] = format_level_with_dist(raw_cw, cur_price)
            item["put_wall"] = format_level_with_dist(raw_pw, cur_price)
            item["gamma_flip"] = format_level_with_dist(raw_flip, cur_price)
            item["pc_ratio"] = str(gamma_info.get("pc_ratio", "—"))
            item["gamma_skew"] = str(gamma_info.get("skew", "—"))
            item["vol_oi_ratio"] = gamma_info.get("vol_oi_ratio", 1.0)
            item["atm_iv_str"] = gamma_info.get("atm_iv_str", "—")
            item["iv_chg_str"] = gamma_info.get("iv_chg_str", "—")
            item["iv_rank_str"] = gamma_info.get("iv_rank_str", "—")
            item["net_dollar_str"] = gamma_info.get("net_dollar_str", "—")
            item["net_dollar_val"] = gamma_info.get("net_dollar_val", 0.0)
            item["whale_trades_count"] = gamma_info.get("whale_trades_count", 0)
            item["flow_conviction_score"] = gamma_info.get("flow_conviction_score", 50)
            item["flow_conviction_badge"] = gamma_info.get("flow_conviction_badge", "🟡 Flow: 50/100")
            item["flow_sizing_factor"] = gamma_info.get("flow_sizing_factor", 1.00)

            # Check if whale flow or long gamma active to add preset tag
            if "Bullish" in str(gamma_info.get("skew", "")) or gamma_info.get("whale_trades_count", 0) > 0:
                item["preset_tags"] += " WHALE_FLOW"
        else:
            item["call_wall"] = "—"
            item["put_wall"] = "—"
            item["gamma_flip"] = "—"
            item["pc_ratio"] = "—"
            item["gamma_skew"] = "—"
            item["vol_oi_ratio"] = 1.0
            item["atm_iv_str"] = "—"
            item["iv_chg_str"] = "—"
            item["iv_rank_str"] = "—"
            item["net_dollar_str"] = "—"
            item["net_dollar_val"] = 0.0
            item["whale_trades_count"] = 0
            item["flow_conviction_score"] = 50
            item["flow_conviction_badge"] = "🟡 Flow: 50/100"
            item["flow_sizing_factor"] = 1.00

        # Compute Institutional 5-Star Setup Score with Pattern Quality & Exhaustion Modifier
        score_dict = setup_scorer.calculate_score(
            catalyst_stars=item["catalyst_stars"],
            rvol=item["rvol"],
            gap_pct=item["gap_pct"],
            price=cur_price,
            yesterday_high=item["yesterday_high"],
            premarket_high=item["premarket_high"],
            gamma_skew=item["gamma_skew"],
            call_wall=item["call_wall"],
            pc_ratio=item["pc_ratio"],
            macro_regime=comp_regime,
            pattern_info=item.get("pattern_info")
        )
        item["setup_score"] = score_dict["score"]
        item["setup_score_display"] = score_dict["display_str"]
        item["stars_visual"] = score_dict["stars_visual"]
        item["score_breakdown"] = score_dict.get("score_breakdown", {})
        item["trade_plan"] = score_dict.get("trade_plan", {}) or (item.get("pattern_info", {}).get("trade_plan", {}))
        item["criteria_checklist"] = score_dict.get("criteria_checklist", {}) or (item.get("pattern_info", {}).get("criteria_checklist", {}))

        # Cross-reference with ETF Sector & Sub-Industry Capital Flow
        is_hot_sec, sec_flow_rationale, sec_flow_mult = sector_flow_engine.is_stock_in_hot_sector(
            item.get("sector", ""),
            item.get("industry", ""),
            sector_flow_data
        )
        item["is_hot_sector"] = is_hot_sec
        item["sector_flow_rationale"] = sec_flow_rationale
        item["sector_flow_multiplier"] = sec_flow_mult

        # Compute Practical Dynamic Position Sizing (min of ATR Risk Parity and 10% Free Cash)
        macro_mult = macro_data.get("composite_multiplier", 0.95)
        raw_options_flow_fac = item.get("flow_sizing_factor", 1.00)
        combined_flow_fac = round(raw_options_flow_fac * sec_flow_mult, 2)
        item["combined_flow_factor"] = combined_flow_fac
        pattern_mult = item.get("trade_plan", {}).get("conviction_mult", 1.00)
        stop_level = item.get("trade_plan", {}).get("hard_stop", round(cur_price * 0.96, 2))
        has_gamma = score_dict.get("has_bullish_gamma") or score_dict.get("cw_above_price")
        
        port_nav = float(raw_port_data.get("total_nav", 336870.83) or 336870.83)
        port_cash = float(raw_port_data.get("cash_balance", 70830.35) or 70830.35)
        target_cash_alloc = float(raw_port_data.get("target_cash_allocation", port_nav * 0.10) or (port_nav * 0.10))

        sizing = setup_scorer.calculate_position_size(
            portfolio_nav=port_nav,
            available_cash=port_cash,
            target_cash_allocation=target_cash_alloc,
            price=cur_price,
            stop_loss=stop_level,
            risk_pct=0.75,
            macro_multiplier=macro_mult,
            flow_factor=combined_flow_fac,
            pattern_multiplier=pattern_mult,
            has_gamma_alignment=bool(has_gamma),
            is_exhausted=item.get("is_exhausted", False)
        )
        item["sizing"] = sizing

        # Quantitative Fast Flash Earnings & SUE Factor Extraction (Option A)
        flash = flash_results_map.get(sym)
        if flash:
            factors = flash.get("factors") or {}
            item["earnings_flash"] = flash
            item["earnings_sue"] = factors.get("sue", 0.0)
            item["earnings_pead"] = factors.get("pead_score", 50.0)
            item["earnings_badge"] = factors.get("category_label", "—")
            item["earnings_badge_color"] = factors.get("badge_color", "#6b7280")
            item["thesis_impact"] = flash.get("thesis_label", "🟡 MAINTAINED")
            item["earnings_playbook"] = flash.get("active_playbook", "Standard Hold")
            item["earnings_flash_json"] = json.dumps(flash)
        else:
            item["earnings_sue"] = 0.0
            item["earnings_pead"] = 50.0
            item["earnings_badge"] = "—"
            item["earnings_badge_color"] = "#6b7280"
            item["thesis_impact"] = "🟡 MAINTAINED"
            item["earnings_playbook"] = "Standard Hold"
            item["earnings_flash_json"] = "{}"

    # Sort watchlist: Institutional qualified first, then Setup Score desc, then Gap % desc, then RVOL desc
    day_watchlist.sort(key=lambda x: (x.get("is_inst_qualified", False), x.get("setup_score", 0.0), x.get("gap_pct", 0.0), x.get("rvol", 0.0)), reverse=True)

    # Build market lookup map for portfolio enrichment
    market_data_lookup = {item["ticker"]: item for item in day_watchlist}

    # Load & enrich real portfolio data with live market intelligence
    portfolio_data = portfolio_mgr.enrich_live_metrics(market_lookup=market_data_lookup)

    # Ingest batch 4-Master earnings summaries and 48H Portfolio Earnings Radar
    try:
        earnings_summary = earnings_scheduler.get_summary_reports()
    except Exception as e:
        logger.debug(f"Error fetching earnings batch summary: {e}")
        earnings_summary = {"reports": []}
    
    try:
        earnings_radar = portfolio_mgr.get_portfolio_earnings_radar(portfolio_data)
    except Exception as e:
        logger.debug(f"Error building earnings radar: {e}")
        earnings_radar = []

    # 6. Render Terminal Summary and Save HTML Report
    logger.info("Step 6/6: Rendering Report Output...")
    html_file = html_generator.generate_report(
        macro_data=macro_data,
        day_watchlist=day_watchlist,
        economic_events=economic_events,
        earnings_data=earnings_data,
        analyst_actions=analyst_actions,
        options_aggregated=options_aggregated,
        session_label=session_label,
        portfolio_data=portfolio_data,
        earnings_summary=earnings_summary,
        earnings_radar=earnings_radar,
        sector_flow_data=sector_flow_data,
    )

    # Print to console
    terminal_viewer.render_dashboard(
        macro_data=macro_data,
        day_watchlist=day_watchlist,
        economic_events=economic_events,
        earnings_data=earnings_data,
        analyst_actions=analyst_actions,
        options_aggregated=options_aggregated,
        session_label=session_label
    )

    print(f"\n[OK] Dashboard generated successfully: file:///{html_file.as_posix()}")

    # Start lightweight local portfolio sync server on port 8050 if not running
    try:
        from sources.portfolio_server import ensure_server_running
        ensure_server_running()
    except Exception as e:
        logger.debug(f"Could not start background portfolio server: {e}")

    if open_browser:
        try:
            logger.info("Opening dashboard in default web browser...")
            webbrowser.open(html_file.as_uri())
        except Exception as e:
            logger.warning(f"Could not auto-open browser: {e}")

    return html_file

def run_realtime_loop(open_browser: bool = True):
    """Continuous real-time screener loop with rate-limit and weekend cadence protection."""
    logger.info("Starting Real-Time Engine... Press Ctrl+C to stop.")
    first_run = True
    while True:
        try:
            run_screener_pipeline(open_browser=(open_browser and first_run), force_refresh=False)
            first_run = False
            
            now_est = datetime.datetime.now(TZ_EST)
            is_weekend = (now_est.weekday() >= 5)
            if is_weekend:
                sleep_secs = 300  # 5-minute calm cadence on weekends (markets closed, quotes & SEC filings static)
                logger.info(f"Weekend Cadence: Markets closed. Quotes & SEC filings static. Next routine check in {sleep_secs}s...")
            else:
                sleep_secs = REALTIME_REFRESH_INTERVAL
                logger.info(f"Sleeping {sleep_secs}s until next live refresh...")
            time.sleep(sleep_secs)
        except KeyboardInterrupt:
            logger.info("Real-Time Screener stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error in real-time screener loop: {e}", exc_info=True)
            time.sleep(15)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-Time Institutional Market Screener & Dashboard")
    parser.add_argument("--realtime", "-r", action="store_true", help="Run in continuous real-time mode (auto-refreshes every 60s)")
    parser.add_argument("--daemon", "-d", action="store_true", help="Launch autonomous institutional session daemon")
    parser.add_argument("--session", "-s", type=str, choices=["premarket", "opening_bell", "midday", "eod", "postmarket"], help="Run designated session workflow")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    parser.add_argument("--headless", action="store_true", help="Run headlessly (for cron / task scheduler)")
    parser.add_argument("--force-refresh", action="store_true", help="Bypass all caches and fetch fresh data")
    args = parser.parse_args()

    open_browser = not (args.no_browser or args.headless)

    if args.daemon:
        from scheduler.system_daemon import SystemDaemon
        SystemDaemon().run_continuous()
    elif args.session:
        from scheduler.system_daemon import SystemDaemon
        daemon = SystemDaemon()
        if args.session == "premarket":
            daemon.run_premarket_workflow()
        elif args.session == "opening_bell":
            daemon.run_opening_bell_workflow()
        elif args.session == "midday":
            daemon.run_midday_workflow()
        elif args.session == "eod":
            daemon.run_eod_workflow()
        elif args.session == "postmarket":
            daemon.run_postmarket_workflow()
    elif args.realtime:
        run_realtime_loop(open_browser=open_browser)
    else:
        run_screener_pipeline(open_browser=open_browser, force_refresh=args.force_refresh)

