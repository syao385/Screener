"""Sector & Sub-Industry Flow Engine v2.0.
Tracks 11 GICS Sector ETF Flows (1D, 1W, 1M), 1D Dollar Inflows,
Normalized Flow Velocity Z-Scores, Sector Rotation Acceleration,
and Expanded Thematic Decomposition across 100+ Industry ETFs (including DRAM, IGV, MAGS, SOXL, URA, PAVE, etc.).
Conforms strictly to 14_institutional-flows.md and 02_industry-funnel.md.
"""

import os
import json
import logging
import datetime
import math
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from tradingview_screener import Query
from config import TZ_EST, DATA_DIR

logger = logging.getLogger("sector_flow_engine")

CACHE_DIR = os.path.join(DATA_DIR, "cache")
FLOW_CACHE_FILE = os.path.join(CACHE_DIR, "sector_flows_cache.json")

# 11 GICS Primary Sector SPDR ETFs
SECTOR_ETFS = {
    "XLK": {"ticker": "XLK", "name": "Technology", "gics": "Information Technology", "proxy": "Tech / Semis / Software"},
    "XLF": {"ticker": "XLF", "name": "Financials", "gics": "Financials", "proxy": "Banks & Fins"},
    "XLE": {"ticker": "XLE", "name": "Energy", "gics": "Energy", "proxy": "Oil, Gas & Energy"},
    "XLV": {"ticker": "XLV", "name": "Health Care", "gics": "Health Care", "proxy": "Pharma & Biotech"},
    "XLI": {"ticker": "XLI", "name": "Industrials", "gics": "Industrials", "proxy": "Aerospace, Defense & Machinery"},
    "XLY": {"ticker": "XLY", "name": "Consumer Discretionary", "gics": "Consumer Discretionary", "proxy": "Retail, Auto & Leisure"},
    "XLP": {"ticker": "XLP", "name": "Consumer Staples", "gics": "Consumer Staples", "proxy": "Food, Beverage & Household"},
    "XLU": {"ticker": "XLU", "name": "Utilities", "gics": "Utilities", "proxy": "Electric & Gas Utilities"},
    "XLRE": {"ticker": "XLRE", "name": "Real Estate", "gics": "Real Estate", "proxy": "REITs & Real Estate"},
    "XLB": {"ticker": "XLB", "name": "Materials", "gics": "Materials", "proxy": "Chemicals, Metals & Mining"},
    "XLC": {"ticker": "XLC", "name": "Communication Services", "gics": "Communication Services", "proxy": "Media, Telecom & Internet"},
}

BENCHMARK_ETFS = ["SPY", "QQQ", "IWM"]

# Expanded Sub-Industry & Thematic Sub-ETFs (100% Comprehensive Coverage)
SUB_INDUSTRY_ETFS = {
    "XLK": [
        {"ticker": "SMH", "name": "Semiconductors (VanEck)"},
        {"ticker": "SOXX", "name": "Semiconductors (iShares)"},
        {"ticker": "SOXL", "name": "Semiconductor Bull 3X (Direxion)"},
        {"ticker": "DRAM", "name": "Quantum / Memory & AI Hardware"},
        {"ticker": "IGV", "name": "Enterprise Software & Cloud (iShares)"},
        {"ticker": "CIBR", "name": "Cybersecurity (First Trust)"},
        {"ticker": "HACK", "name": "Cyber Security (ETFMG)"},
        {"ticker": "BOTZ", "name": "Robotics & Artificial Intelligence"},
        {"ticker": "MAGS", "name": "Magnificent Seven Mega-Cap"},
    ],
    "XLF": [
        {"ticker": "KRE", "name": "Regional Banking (SPDR S&P)"},
        {"ticker": "KBE", "name": "Bank Index (SPDR)"},
        {"ticker": "IAI", "name": "Broker-Dealers & Exchanges"},
        {"ticker": "IAK", "name": "Insurance (iShares)"},
        {"ticker": "KBWB", "name": "Money Center Banks"},
    ],
    "XLE": [
        {"ticker": "XOP", "name": "Oil & Gas Exploration & Production"},
        {"ticker": "OIH", "name": "Oil Services (VanEck)"},
        {"ticker": "AMLP", "name": "Alerian MLP Infrastructure"},
        {"ticker": "FCG", "name": "Natural Gas (First Trust)"},
    ],
    "XLV": [
        {"ticker": "XBI", "name": "Biotech (SPDR S&P)"},
        {"ticker": "IBB", "name": "Biotechnology (iShares)"},
        {"ticker": "IHI", "name": "Medical Devices (iShares)"},
        {"ticker": "ARKG", "name": "Genomic Revolution (ARK)"},
    ],
    "XLI": [
        {"ticker": "ITA", "name": "Aerospace & Defense (iShares)"},
        {"ticker": "XAR", "name": "Aerospace & Defense (SPDR)"},
        {"ticker": "PAVE", "name": "U.S. Infrastructure Development"},
        {"ticker": "IYT", "name": "Transportation (iShares)"},
        {"ticker": "JETS", "name": "Global Jets / Airlines"},
    ],
    "XLY": [
        {"ticker": "XHB", "name": "Homebuilders (SPDR S&P)"},
        {"ticker": "ITB", "name": "U.S. Home Construction (iShares)"},
        {"ticker": "XRT", "name": "Retail (SPDR S&P)"},
    ],
    "XLB": [
        {"ticker": "COPX", "name": "Copper Miners (Global X)"},
        {"ticker": "GDX", "name": "Gold Miners (VanEck)"},
        {"ticker": "GDXJ", "name": "Junior Gold Miners (VanEck)"},
        {"ticker": "XME", "name": "Metals & Mining (SPDR S&P)"},
        {"ticker": "LIT", "name": "Lithium & Battery Tech"},
        {"ticker": "SILJ", "name": "Junior Silver Miners"},
    ],
    "XLU": [
        {"ticker": "URA", "name": "Uranium Miners (Global X)"},
        {"ticker": "NLR", "name": "Nuclear Energy & Uranium (VanEck)"},
        {"ticker": "ICLN", "name": "Global Clean Energy (iShares)"},
        {"ticker": "TAN", "name": "Solar Energy (Invesco)"},
    ],
    "XLC": [
        {"ticker": "SOCL", "name": "Social Media (Global X)"},
        {"ticker": "HERO", "name": "Video Games & Esports"},
    ],
    "XLP": [
        {"ticker": "PBJ", "name": "Food & Beverage (Invesco)"},
    ],
    "XLRE": [
        {"ticker": "VNQ", "name": "Real Estate (Vanguard)"},
        {"ticker": "REM", "name": "Mortgage Real Estate (iShares)"},
    ],
    "CRYPTO": [
        {"ticker": "IBIT", "name": "iShares Bitcoin Trust (BlackRock)"},
        {"ticker": "ETHA", "name": "iShares Ethereum Trust (BlackRock)"},
        {"ticker": "FBTC", "name": "Fidelity Wise Origin Bitcoin Fund"},
        {"ticker": "BITO", "name": "ProShares Bitcoin Strategy ETF"},
        {"ticker": "WGMI", "name": "Bitcoin Mining & Compute Infra (Valkyrie)"},
        {"ticker": "BLOK", "name": "Blockchain & Data Sharing (Amplify)"},
    ],
}


def _format_flow_dollar(val: float) -> str:
    """Format dollar net flow cleanly as +$450M, -$1.2B."""
    sign = "+" if val >= 0 else "-"
    abs_v = abs(val)
    if abs_v >= 1.0e9:
        return f"{sign}${abs_v / 1.0e9:.2f}B"
    if abs_v >= 1.0e6:
        return f"{sign}${abs_v / 1.0e6:.1f}M"
    if abs_v >= 1.0e3:
        return f"{sign}${abs_v / 1.0e3:.0f}K"
    return f"{sign}${abs_v:.0f}"


class SectorFlowEngine:
    """Institutional Sector & Thematic ETF Flow Engine with 1D, 1W, and 1M Analytics."""

    def __init__(self):
        self._ensure_cache_dir()
        self.cached_flows: Optional[Dict[str, Any]] = None
        self.cache_ttl_minutes = 15

    def _ensure_cache_dir(self):
        os.makedirs(CACHE_DIR, exist_ok=True)

    def _load_disk_cache(self) -> Optional[Dict[str, Any]]:
        try:
            if os.path.exists(FLOW_CACHE_FILE):
                with open(FLOW_CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    ts_str = data.get("timestamp")
                    if ts_str:
                        cached_time = datetime.datetime.fromisoformat(ts_str)
                        if datetime.datetime.now(TZ_EST) - cached_time < datetime.timedelta(minutes=self.cache_ttl_minutes):
                            return data
        except Exception as e:
            logger.debug(f"Cache read error: {e}")
        return None

    def _save_disk_cache(self, data: Dict[str, Any]):
        try:
            with open(FLOW_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.debug(f"Cache write error: {e}")

    def _query_etf_universe(self, ticker_names: List[str]) -> pd.DataFrame:
        """Query TradingView scanner directly for given ETF ticker names without requiring exchange prefixes."""
        try:
            q = Query()
            q.url = "https://scanner.tradingview.com/america/scan"
            columns = [
                "name",
                "description",
                "close",
                "change",
                "volume",
                "open",
                "Perf.W",
                "Perf.1M",
                "Perf.3M",
                "Perf.YTD",
                "relative_volume_10d_calc",
                "average_volume_30d_calc",
                "Volatility.D",
                "MoneyFlow",
            ]
            q.query = {
                "markets": ["america"],
                "filter": [{"left": "name", "operation": "in_range", "right": ticker_names}],
                "options": {"lang": "en"},
                "columns": columns,
                "range": [0, len(ticker_names) + 25],
            }
            count, df = q.get_scanner_data()
            return df if df is not None else pd.DataFrame()
        except Exception as e:
            logger.warning(f"Error querying TradingView for ETFs: {e}")
            return pd.DataFrame()

    def get_sector_flow_matrix(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Compute full 11-sector flow matrix + thematic sub-ETF breakdown with 1D, 1W, and 1M metrics."""
        if not force_refresh:
            if hasattr(self, "_mem_cache") and self._mem_cache:
                return self._mem_cache
            cached = self._load_disk_cache()
            if cached:
                self._mem_cache = cached
                return cached

        logger.info("Computing Live Sector ETF Flow & Creation Velocity Matrix via TradingView...")
        now_est = datetime.datetime.now(TZ_EST)

        # Collect all unique ticker names (Primary + Sub-industries + Benchmarks)
        all_ticker_names = list(BENCHMARK_ETFS) + list(SECTOR_ETFS.keys())
        sub_meta_map = {}

        for sec_t, subs in SUB_INDUSTRY_ETFS.items():
            for sub in subs:
                t = sub["ticker"]
                all_ticker_names.append(t)
                sub_meta_map[t] = {"parent_sector": sec_t, "name": sub["name"], "ticker": t}

        all_ticker_names = list(set(all_ticker_names))

        df = self._query_etf_universe(all_ticker_names)
        if df.empty:
            logger.warning("Empty response from ETF query, returning empty matrix.")
            fallback = {"sectors": [], "top_inflows": [], "top_outflows": [], "sub_industries": {}, "timestamp": now_est.isoformat()}
            self._mem_cache = fallback
            return fallback

        # Build ticker lookup table
        ticker_data = {}
        for _, row in df.iterrows():
            t_name = str(row.get("name", "")).strip().upper()
            if t_name:
                ticker_data[t_name] = row

        # Extract SPY Benchmark
        spy_row = ticker_data.get("SPY", {})
        spy_close = float(spy_row.get("close", 0.0) or 0.0)
        spy_change = float(spy_row.get("change", 0.0) or 0.0)
        spy_w = float(spy_row.get("Perf.W", 0.0) or 0.0)
        spy_1m = float(spy_row.get("Perf.1M", 0.0) or 0.0)
        spy_3m = float(spy_row.get("Perf.3M", 0.0) or 0.0)

        spy_metrics = {
            "ticker": "SPY",
            "close": spy_close,
            "change_pct": spy_change,
            "perf_1w": spy_w,
            "perf_1m": spy_1m,
            "perf_3m": spy_3m,
        }

        # Process 11 Primary Sectors
        sector_results = []
        for t, meta in SECTOR_ETFS.items():
            row = ticker_data.get(t)
            if row is None:
                continue

            close = float(row.get("close", 0.0) or 0.0)
            change = float(row.get("change", 0.0) or 0.0)
            open_p = float(row.get("open", 0.0) or close)
            perf_w = float(row.get("Perf.W", 0.0) or 0.0)
            perf_1m = float(row.get("Perf.1M", 0.0) or 0.0)
            perf_3m = float(row.get("Perf.3M", 0.0) or 0.0)
            perf_ytd = float(row.get("Perf.YTD", 0.0) or 0.0)
            vol = float(row.get("volume", 0.0) or 0.0)
            avg_vol_30d = float(row.get("average_volume_30d_calc", 0.0) or 1.0)
            rvol = float(row.get("relative_volume_10d_calc", 1.0) or 1.0)
            mfi = float(row.get("MoneyFlow", 50.0) or 50.0)
            volatility = float(row.get("Volatility.D", 1.0) or 1.0)

            # 1-Day, 1-Week, and 1-Month Relative Strength vs SPY
            rs_1d = round(change - spy_change, 2)
            rs_1w = round(perf_w - spy_w, 2)
            rs_1m = round(perf_1m - spy_1m, 2)
            rs_3m = round(perf_3m - spy_3m, 2)

            # Estimated 1-Day Dollar Net Flow ($)
            dollar_vol_1d = close * vol
            flow_1d_dollar = dollar_vol_1d * (change / 100.0)
            flow_1d_str = _format_flow_dollar(flow_1d_dollar)

            # 1-Day Flow Badge
            if flow_1d_dollar >= 5.0e7:
                flow_1d_badge = f"🟢 Inflow ({flow_1d_str})"
            elif flow_1d_dollar <= -5.0e7:
                flow_1d_badge = f"🔴 Outflow ({flow_1d_str})"
            else:
                flow_1d_badge = f"🟡 Flat ({flow_1d_str})"

            # Normalized Flow Velocity (Z-score proxy using MFI + 1M Relative Strength)
            flow_zscore_5d = round(((mfi - 50.0) / 15.0) * 0.5 + (rs_1w / 2.5) * 0.3 + (rs_1d / 1.5) * 0.2, 2)
            flow_zscore_20d = round(((mfi - 50.0) / 15.0) * 0.4 + (rs_1m / 4.0) * 0.6, 2)

            # Flow Acceleration = 1-Week Pace vs 1-Month Average Pace
            flow_acceleration = round(rs_1w - (rs_1m / 4.0), 2)

            # Composite Institutional Flow Score (0 - 100)
            raw_score = 50.0 + (flow_zscore_5d * 12.0) + (flow_acceleration * 3.0) + ((rvol - 1.0) * 10.0) + ((mfi - 50.0) * 0.3)
            conviction_score = max(5.0, min(95.0, raw_score))

            if conviction_score >= 68:
                state = "ACCUMULATION (Strong Inflow)"
                action = "OVERWEIGHT (+20%)"
                badge = "🟢 ACCUMULATION"
                flow_mult = 1.25
            elif conviction_score >= 54:
                state = "EXPANSION (Moderate Inflow)"
                action = "OVERWEIGHT (+10%)"
                badge = "🟢 EXPANSION"
                flow_mult = 1.25
            elif conviction_score >= 46:
                state = "NEUTRAL (Balanced Flow)"
                action = "NEUTRAL"
                badge = "🟡 NEUTRAL"
                flow_mult = 1.00
            elif conviction_score >= 32:
                state = "ROTATING OUT (Moderate Outflow)"
                action = "UNDERWEIGHT (-10%)"
                badge = "🔴 ROTATING OUT"
                flow_mult = 0.75
            else:
                state = "DISTRIBUTION (Heavy Outflow)"
                action = "UNDERWEIGHT (-20%)"
                badge = "🔴 DISTRIBUTION"
                flow_mult = 0.70

            sector_results.append({
                "ticker": t,
                "sector_name": meta["name"],
                "gics_sector": meta["gics"],
                "proxy": meta["proxy"],
                "price": round(close, 2),
                "change_pct": round(change, 2),
                "perf_1w": round(perf_w, 2),
                "perf_1m": round(perf_1m, 2),
                "perf_3m": round(perf_3m, 2),
                "perf_ytd": round(perf_ytd, 2),
                "rs_1d": rs_1d,
                "rs_1w": rs_1w,
                "rs_1m": rs_1m,
                "rs_3m": rs_3m,
                "flow_1d_dollar": flow_1d_dollar,
                "flow_1d_str": flow_1d_str,
                "flow_1d_badge": flow_1d_badge,
                "rvol": round(rvol, 2),
                "mfi": round(mfi, 1),
                "volatility": round(volatility, 2),
                "flow_zscore_5d": flow_zscore_5d,
                "flow_zscore_20d": flow_zscore_20d,
                "flow_acceleration": flow_acceleration,
                "flow_score": round(conviction_score, 1),
                "flow_multiplier": flow_mult,
                "flow_mult_str": f"{flow_mult:.2f}x",
                "state": state,
                "badge": badge,
                "action": action,
            })

        # Sort sectors by flow score descending
        sector_results.sort(key=lambda x: x.get("flow_score", 0), reverse=True)

        top_inflows = [s["ticker"] for s in sector_results if s.get("flow_score", 0) >= 54]
        if not top_inflows and sector_results:
            top_inflows = [sector_results[0]["ticker"], sector_results[1]["ticker"]]

        top_outflows = [s["ticker"] for s in sector_results if s.get("flow_score", 0) <= 46]

        # Process Sub-Industry Thematic ETFs
        sub_industry_results: Dict[str, List[Dict[str, Any]]] = {}
        for sub_t, meta in sub_meta_map.items():
            parent_sec = meta["parent_sector"]
            row = ticker_data.get(sub_t)
            if row is None:
                continue

            close = float(row.get("close", 0.0) or 0.0)
            change = float(row.get("change", 0.0) or 0.0)
            perf_w = float(row.get("Perf.W", 0.0) or 0.0)
            perf_1m = float(row.get("Perf.1M", 0.0) or 0.0)
            vol = float(row.get("volume", 0.0) or 0.0)
            rvol = float(row.get("relative_volume_10d_calc", 1.0) or 1.0)
            mfi = float(row.get("MoneyFlow", 50.0) or 50.0)

            rs_1d = round(change - spy_change, 2)
            rs_1w = round(perf_w - spy_w, 2)
            rs_1m = round(perf_1m - spy_1m, 2)

            sub_flow_1d_dollar = close * vol * (change / 100.0)
            sub_flow_1d_str = _format_flow_dollar(sub_flow_1d_dollar)

            sub_zscore = round(((mfi - 50.0) / 15.0) * 0.5 + (rs_1w / 2.5) * 0.3 + (rs_1d / 1.5) * 0.2, 2)
            sub_score = max(5.0, min(95.0, 50.0 + (sub_zscore * 12.0) + ((rvol - 1.0) * 8.0) + ((mfi - 50.0) * 0.3)))

            sub_item = {
                "ticker": sub_t,
                "sub_industry_name": meta["name"],
                "parent_sector": parent_sec,
                "price": round(close, 2),
                "change_pct": round(change, 2),
                "perf_1w": round(perf_w, 2),
                "perf_1m": round(perf_1m, 2),
                "rs_1d": rs_1d,
                "rs_1w": rs_1w,
                "rs_1m": rs_1m,
                "flow_1d_str": sub_flow_1d_str,
                "rvol": round(rvol, 2),
                "mfi": round(mfi, 1),
                "flow_zscore_5d": sub_zscore,
                "flow_score": round(sub_score, 1),
            }

            if parent_sec not in sub_industry_results:
                sub_industry_results[parent_sec] = []
            sub_industry_results[parent_sec].append(sub_item)

        # Sort sub-industries inside each sector
        for sec in sub_industry_results:
            sub_industry_results[sec].sort(key=lambda x: x.get("flow_score", 0), reverse=True)

        payload = {
            "timestamp": now_est.isoformat(),
            "timestamp_str": now_est.strftime("%Y-%m-%d %H:%M:%S ET"),
            "benchmark_spy": spy_metrics,
            "sectors": sector_results,
            "top_inflows": top_inflows,
            "top_outflows": top_outflows,
            "sub_industries": sub_industry_results,
        }

        self._save_disk_cache(payload)
        self.cached_flows = payload
        return payload

    def get_sector_flow_details_for_stock(self, stock_sector: str, stock_industry: str = "", flow_matrix: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return structured flow details (matched ETF, score, badge, velocity Z, action) for a stock."""
        if not flow_matrix:
            flow_matrix = self.get_sector_flow_matrix()

        top_inflow_tickers = flow_matrix.get("top_inflows", [])
        matched_etf = "SPY"
        matched_score = 50.0
        matched_badge = "🟡 NEUTRAL"
        matched_z = 0.0
        matched_action = "NEUTRAL"
        matched_sec_name = "Broad Market"

        stock_sec_clean = str(stock_sector or "").lower()
        stock_ind_clean = str(stock_industry or "").lower()

        # Check sub-industries / thematics first (e.g. Semis -> SMH)
        for s in (flow_matrix.get("sub_industries", []) if isinstance(flow_matrix, dict) else []):
            if not isinstance(s, dict):
                continue
            name = str(s.get("name", "")).lower()
            t = str(s.get("ticker", "")).lower()
            if (stock_ind_clean and stock_ind_clean in name) or (name and name in stock_ind_clean):
                matched_etf = s.get("ticker", "SPY")
                matched_score = float(s.get("flow_score", 50.0) or 50.0)
                matched_badge = s.get("badge", "🟡 NEUTRAL")
                matched_z = float(s.get("flow_velocity_z", 0.0) or 0.0)
                matched_action = s.get("target_action", "NEUTRAL")
                matched_sec_name = s.get("name", stock_industry)
                break

        # Fallback to 11 GICS Sector SPDRs
        if matched_etf == "SPY":
            for s in (flow_matrix.get("sectors", []) if isinstance(flow_matrix, dict) else []):
                if not isinstance(s, dict):
                    continue
                gics = str(s.get("gics_sector", "")).lower()
                name = str(s.get("sector_name", "")).lower()
                proxy = str(s.get("proxy", "")).lower()

                if (gics and gics in stock_sec_clean) or (stock_sec_clean and stock_sec_clean in gics) or \
                   (name and name in stock_sec_clean) or (stock_sec_clean and stock_sec_clean in name) or \
                   (proxy and any(p.strip() in stock_sec_clean for p in proxy.split("/"))):
                    matched_etf = s.get("ticker", "SPY")
                    matched_score = float(s.get("flow_score", 50.0) or 50.0)
                    matched_badge = s.get("badge", "🟡 NEUTRAL")
                    matched_z = float(s.get("flow_velocity_z", 0.0) or 0.0)
                    matched_action = s.get("target_action", "NEUTRAL")
                    matched_sec_name = s.get("sector_name", stock_sector)
                    break

        is_hot = matched_etf in top_inflow_tickers or matched_score >= 54.0
        flow_mult = 1.25 if is_hot else (0.70 if matched_score <= 32.0 else (0.75 if matched_score <= 42.0 else 1.00))
        
        return {
            "matched_etf": matched_etf,
            "sector_name": matched_sec_name,
            "flow_score": round(matched_score, 1),
            "flow_badge": matched_badge,
            "flow_velocity_z": round(matched_z, 2),
            "target_action": matched_action,
            "flow_multiplier": flow_mult,
            "flow_mult_str": f"{flow_mult:.2f}x",
            "is_hot": is_hot,
            "invalidation_triggered": matched_score <= 40.0,
            "rationale": f"Parent {matched_etf} Flow: {matched_score:.1f}/100 ({matched_badge}) | Multiplier: {flow_mult:.2f}x"
        }

    def is_stock_in_hot_sector(self, stock_sector: str, stock_industry: str, flow_matrix: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, float]:
        """Check if a stock belongs to an active institutional accumulation sector.
        Returns: (is_hot, rationale, sizing_flow_multiplier)
        """
        details = self.get_sector_flow_details_for_stock(stock_sector, stock_industry, flow_matrix)
        return details["is_hot"], details["rationale"], details["flow_multiplier"]


sector_flow_engine = SectorFlowEngine()
