"""Main Orchestrator for Real-Time Institutional Market Intelligence Screener."""

import os
import sys
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
from sources.economic_calendar import economic_cal
from sources.earnings_calendar import earnings_cal
from sources.analyst_ratings import analyst_feed
from sources.options_flow import options_scanner
from sources.state_manager import state_mgr
from sources.pattern_detector import pattern_detector
from reporter.html_generator import html_generator
from reporter.terminal_viewer import terminal_viewer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("orchestrator")

def get_market_session(now_est: datetime.datetime) -> Tuple[str, str]:
    """Determine market session: PREMARKET | REGULAR | POSTMARKET."""
    weekday = now_est.weekday()
    t = now_est.time()

    if weekday >= 5:
        return "POSTMARKET", "Weekend Review (Post-Market Close)"
    if t < datetime.time(4, 0):
        return "POSTMARKET", "Overnight (Post-Market Close)"
    if datetime.time(4, 0) <= t < datetime.time(9, 30):
        return "PREMARKET", "Premarket Session (04:00 - 09:30 EST)"
    if datetime.time(9, 30) <= t < datetime.time(16, 0):
        return "REGULAR", "Regular Market Hours (09:30 - 16:00 EST)"
    if datetime.time(16, 0) <= t < datetime.time(20, 0):
        return "POSTMARKET", "After-Hours Session (16:00 - 20:00 EST)"
    return "POSTMARKET", "Post-Market Close (20:00 - 04:00 EST)"

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

    # 1. Base % Chg is ALWAYS: (Current Close - Previous Close) / Previous Close * 100%
    tv_chg = row.get("change")
    if tv_chg is not None and not pd.isna(tv_chg):
        pct_change = float(tv_chg)
    elif close_price > 0 and prev_close > 0:
        pct_change = ((close_price - prev_close) / prev_close) * 100.0
    else:
        pct_change = 0.0

    # 2. Session Gap % & Evaluation Price
    if session_type == "PREMARKET":
        current_price = pre_close if pre_close > 0 else close_price
        ref_high = day_high if day_high > 0 else prev_high
        base_prev = prev_close if prev_close > 0 else close_price
        gap_pct = ((current_price - base_prev) / base_prev * 100.0) if (base_prev > 0 and current_price > 0) else float(row.get("premarket_change", 0.0) or 0.0)
        eval_vol = pre_vol
    elif session_type == "POSTMARKET":
        current_price = post_close if post_close > 0 else close_price
        ref_high = day_high if day_high > 0 else prev_high
        base_reg_close = close_price if close_price > 0 else prev_close
        gap_pct = ((current_price - base_reg_close) / base_reg_close * 100.0) if (base_reg_close > 0 and current_price > 0) else float(row.get("postmarket_change", 0.0) or 0.0)
        eval_vol = post_vol if post_vol > 0 else cur_vol
    else: # REGULAR
        current_price = close_price if close_price > 0 else open_price
        ref_high = prev_high if prev_high > 0 else day_high
        base_prev = prev_close if prev_close > 0 else close_price
        if pre_close > 0 and base_prev > 0:
            gap_pct = ((pre_close - base_prev) / base_prev) * 100.0
        elif open_price > 0 and base_prev > 0:
            gap_pct = ((open_price - base_prev) / base_prev) * 100.0
        else:
            gap_pct = float(row.get("premarket_change", 0.0) or 0.0)
        eval_vol = cur_vol
        if base_prev > 0 and current_price > 0:
            pct_change = ((current_price - base_prev) / base_prev) * 100.0

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

    # Session RVOL
    rvol = rvol_calc.calculate_session_rvol(
        ticker=clean_ticker,
        session_type=session_type,
        current_volume=eval_vol,
        tv_rvol=tv_rvol,
        target_time=now_est.time()
    )

    # Detect and arbitrate catalyst
    cat_res = catalyst_detector.detect_catalyst(clean_ticker, company_name=company_name)
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
        "preset_tags": " ".join(pattern_info.get("preset_tags", ["ALL_SETUPS"])),
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

    # 2. Ingest Economic Calendar
    logger.info("Step 2/6: Ingesting Economic Calendar...")
    economic_events = economic_cal.get_today_events()

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
                gap = float(row.get("premarket_change", 0.0) or 0.0)
                if gap == 0.0 and close > 0:
                    gap = ((price - close) / close) * 100.0
            elif session_type == "POSTMARKET":
                price = post_close if post_close > 0 else close
                gap = ((price - close) / close * 100.0) if close > 0 else float(row.get("postmarket_change", 0.0) or 0.0)
            else:
                price = close
                open_val = float(row.get("open", 0.0) or 0.0)
                prev_close = float(row.get("close[1]", 0.0) or close)
                gap = ((open_val - prev_close) / prev_close * 100.0) if (open_val > 0 and prev_close > 0) else float(row.get("premarket_change", 0.0) or 0.0)

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

    all_eval_rows = list(combined_eval_dict.values())
    logger.info(f"Evaluating {len(all_eval_rows)} prioritized candidate, portfolio & 5-day EP tickers in parallel...")
    
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

    # Attach Analyst, Options Gamma, and Compute 5-Star Setup Score for ALL evaluated tickers
    for item in day_watchlist:
        sym = item["ticker"]
        cur_price = item["price"]
        item["analyst_rating"] = analyst_lookup.get(sym, "—")

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

        # Compute Dynamic ATR-Parity Position Sizing with Gamma Gating, Conviction Multiplier & Exhaustion Limit
        macro_mult = macro_data.get("composite_multiplier", 0.95)
        flow_fac = item.get("flow_sizing_factor", 1.00)
        pattern_mult = item.get("trade_plan", {}).get("conviction_mult", 1.00)
        stop_level = item.get("trade_plan", {}).get("hard_stop", round(cur_price * 0.96, 2))
        has_gamma = score_dict.get("has_bullish_gamma") or score_dict.get("cw_above_price")
        
        sizing = setup_scorer.calculate_position_size(
            portfolio_nav=336870.83,
            risk_pct=0.75,
            price=cur_price,
            stop_loss=stop_level,
            macro_multiplier=macro_mult,
            flow_factor=flow_fac,
            pattern_multiplier=pattern_mult,
            has_gamma_alignment=bool(has_gamma),
            is_exhausted=item.get("is_exhausted", False)
        )
        item["sizing"] = sizing

    # Sort watchlist: Institutional qualified first, then Setup Score desc, then Gap % desc, then RVOL desc
    day_watchlist.sort(key=lambda x: (x.get("is_inst_qualified", False), x.get("setup_score", 0.0), x.get("gap_pct", 0.0), x.get("rvol", 0.0)), reverse=True)

    # Build market lookup map for portfolio enrichment
    market_data_lookup = {item["ticker"]: item for item in day_watchlist}

    # Load & enrich real portfolio data with live market intelligence
    portfolio_data = portfolio_mgr.enrich_live_metrics(market_lookup=market_data_lookup)

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
        portfolio_data=portfolio_data
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

    if open_browser:
        try:
            logger.info("Opening dashboard in default web browser...")
            webbrowser.open(html_file.as_uri())
        except Exception as e:
            logger.warning(f"Could not auto-open browser: {e}")

    return html_file

def run_realtime_loop(open_browser: bool = True):
    """Continuous real-time screener loop with rate-limit protection."""
    logger.info(f"Starting Real-Time Engine (Polling cycle: {REALTIME_REFRESH_INTERVAL}s)... Press Ctrl+C to stop.")
    first_run = True
    while True:
        try:
            run_screener_pipeline(open_browser=(open_browser and first_run), force_refresh=False)
            first_run = False
            logger.info(f"Sleeping {REALTIME_REFRESH_INTERVAL}s until next live refresh...")
            time.sleep(REALTIME_REFRESH_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Real-Time Screener stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error in real-time screener loop: {e}")
            time.sleep(15)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-Time Institutional Market Screener & Dashboard")
    parser.add_argument("--realtime", "-r", action="store_true", help="Run in continuous real-time mode (auto-refreshes every 60s)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    parser.add_argument("--headless", action="store_true", help="Run headlessly (for cron / task scheduler)")
    parser.add_argument("--force-refresh", action="store_true", help="Bypass all caches and fetch fresh data")
    args = parser.parse_args()

    open_browser = not (args.no_browser or args.headless)
    if args.realtime:
        run_realtime_loop(open_browser=open_browser)
    else:
        run_screener_pipeline(open_browser=open_browser, force_refresh=args.force_refresh)
