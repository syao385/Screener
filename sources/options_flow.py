import os
import json
import math
import logging
import datetime
import re
import requests
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from config import TZ_EST, DATA_DIR

logger = logging.getLogger("options_flow")

CACHE_DIR = Path(DATA_DIR) / "cache"
IV_CACHE_FILE = CACHE_DIR / "options_iv_cache.json"
GAMMA_CACHE_FILE = CACHE_DIR / "gamma_structure_cache.json"

def format_currency(val: float) -> str:
    """Format dollar premium into readable M / K format."""
    abs_val = abs(val)
    prefix = "-" if val < 0 else ""
    if abs_val >= 1.0e9:
        return f"{prefix}${abs_val / 1.0e9:.2f}B"
    if abs_val >= 1.0e6:
        return f"{prefix}${abs_val / 1.0e6:.2f}M"
    if abs_val >= 1.0e3:
        return f"{prefix}${abs_val / 1.0e3:.0f}K"
    return f"{prefix}${abs_val:.0f}"

class OptionsFlowScanner:
    """Computes 45-Day aggregated Gamma Structure (Call/Put Walls, Gamma Flip, Vol/OI, ATM IV, IV Rank, Net Flow)."""

    def __init__(self):
        self._cache_aggregated: Dict[str, Dict[str, Any]] = {}
        self._iv_cache: Dict[str, Dict[str, Any]] = self._load_iv_cache()
        self._gamma_disk_cache: Dict[str, Dict[str, Any]] = self._load_gamma_cache()
        self._session: Optional[requests.Session] = None
        self._crumb: Optional[str] = None
        self._last_crumb_time: float = 0.0

    def _load_iv_cache(self) -> Dict[str, Dict[str, Any]]:
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            if IV_CACHE_FILE.exists():
                with open(IV_CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Could not load IV cache: {e}")
        return {}

    def _save_iv_cache(self):
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(IV_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._iv_cache, f, indent=2)
        except Exception as e:
            logger.debug(f"Could not save IV cache: {e}")

    def _load_gamma_cache(self) -> Dict[str, Dict[str, Any]]:
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            if GAMMA_CACHE_FILE.exists():
                with open(GAMMA_CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Could not load Gamma cache: {e}")
        return {}

    def _save_gamma_cache(self):
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(GAMMA_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._gamma_disk_cache, f, indent=2)
        except Exception as e:
            logger.debug(f"Could not save Gamma cache: {e}")

    def _get_session_and_crumb(self) -> Tuple[requests.Session, Optional[str]]:
        now_ts = datetime.datetime.now().timestamp()
        if self._session and self._crumb and (now_ts - self._last_crumb_time < 3600):
            return self._session, self._crumb

        sess = requests.Session()
        sess.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

        crumb = None
        try:
            r = sess.get("https://finance.yahoo.com/quote/SPY/options/", timeout=10)
            m = re.findall(r'"crumb":"([^"]+)"', r.text)
            if m:
                crumb = m[0]
                sess.headers.update({"Accept": "application/json"})
        except Exception as e:
            logger.debug(f"Crumb acquisition error: {e}")

        self._session = sess
        self._crumb = crumb
        self._last_crumb_time = now_ts
        return self._session, self._crumb

    def compute_45d_ticker_gamma(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Compute aggregate 45-day Gamma structure, ATM IV, IV Rank, Net Premium, and whale trades for a ticker."""
        clean_sym = ticker.split(":")[-1] if ":" in ticker else ticker
        clean_sym = clean_sym.upper().strip()

        if clean_sym in self._cache_aggregated:
            return self._cache_aggregated[clean_sym]

        now = datetime.datetime.now(TZ_EST)
        today_str = now.strftime("%Y-%m-%d")

        # Check persistent disk cache first
        cached = self._gamma_disk_cache.get(clean_sym)
        if cached and cached.get("date") == today_str and cached.get("call_wall") != "—" and (not cached.get("whale_trades") or "contract_iv" in cached.get("whale_trades", [{}])[0]):
            self._cache_aggregated[clean_sym] = cached
            return cached

        sess, crumb = self._get_session_and_crumb()
        if not crumb:
            if cached and cached.get("call_wall") != "—":
                return cached
            return None

        url = f"https://query2.finance.yahoo.com/v7/finance/options/{clean_sym}?crumb={crumb}"
        try:
            res = sess.get(url, timeout=10)
            if res.status_code == 401 or res.status_code == 403:
                self._crumb = None
                sess, crumb = self._get_session_and_crumb()
                url = f"https://query2.finance.yahoo.com/v7/finance/options/{clean_sym}?crumb={crumb}"
                res = sess.get(url, timeout=10)

            if res.status_code != 200:
                if cached:
                    return cached
                return None

            data = res.json()
            result = data.get("optionChain", {}).get("result", [])
            if not result:
                return cached

            quote = result[0].get("quote", {})
            spot_price = float(quote.get("regularMarketPrice", 0.0) or 0.0)
            prev_close = float(quote.get("regularMarketPreviousClose", 0.0) or spot_price)
            stock_pct_chg = ((spot_price - prev_close) / prev_close * 100.0) if (prev_close > 0 and spot_price > 0) else 0.0

            exp_dates = result[0].get("expirationDates", [])
            cutoff_ts = (now + datetime.timedelta(days=45)).timestamp()

            all_calls = []
            all_puts = []
            whale_trades = []

            # First expiration
            opts0 = result[0].get("options", [{}])[0]
            calls0 = opts0.get("calls", [])
            puts0 = opts0.get("puts", [])
            all_calls.extend(calls0)
            all_puts.extend(puts0)

            # Subsequent expirations up to 45 days (limit to first 6 for speed)
            valid_exp_ts = [ts for ts in exp_dates[1:] if ts <= cutoff_ts]
            for ts in valid_exp_ts[:6]:
                exp_url = f"https://query2.finance.yahoo.com/v7/finance/options/{clean_sym}?crumb={crumb}&date={ts}"
                try:
                    exp_res = sess.get(exp_url, timeout=8)
                    if exp_res.status_code == 200:
                        e_data = exp_res.json()
                        e_opts = e_data.get("optionChain", {}).get("result", [{}])[0].get("options", [{}])[0]
                        all_calls.extend(e_opts.get("calls", []))
                        all_puts.extend(e_opts.get("puts", []))
                except Exception:
                    pass

            if not all_calls and not all_puts:
                return cached

            df_calls = pd.DataFrame(all_calls) if all_calls else pd.DataFrame()
            df_puts = pd.DataFrame(all_puts) if all_puts else pd.DataFrame()

            for df in [df_calls, df_puts]:
                if not df.empty:
                    for col in ["volume", "openInterest", "lastPrice", "strike", "impliedVolatility"]:
                        if col not in df.columns:
                            df[col] = 0.0
                        else:
                            df[col] = df[col].fillna(0.0)

            tot_call_vol = float(df_calls["volume"].sum()) if not df_calls.empty else 0.0
            tot_put_vol = float(df_puts["volume"].sum()) if not df_puts.empty else 0.0
            tot_call_oi = float(df_calls["openInterest"].sum()) if not df_calls.empty else 0.0
            tot_put_oi = float(df_puts["openInterest"].sum()) if not df_puts.empty else 0.0

            total_45d_vol = tot_call_vol + tot_put_vol
            total_45d_oi = tot_call_oi + tot_put_oi

            vol_oi_ratio = round(total_45d_vol / total_45d_oi, 2) if total_45d_oi > 0 else 1.0
            pc_ratio = round(tot_put_vol / tot_call_vol, 2) if tot_call_vol > 0 else 1.0

            # Call Wall & Put Wall
            call_wall = 0.0
            if not df_calls.empty and df_calls["openInterest"].max() > 0:
                cw_row = df_calls.loc[df_calls["openInterest"].idxmax()]
                call_wall = float(cw_row["strike"])

            put_wall = 0.0
            if not df_puts.empty and df_puts["openInterest"].max() > 0:
                pw_row = df_puts.loc[df_puts["openInterest"].idxmax()]
                put_wall = float(pw_row["strike"])

            # Gamma Flip
            total_weight = tot_call_oi + tot_put_oi
            if total_weight > 0:
                c_weight = (df_calls["strike"] * df_calls["openInterest"]).sum()
                p_weight = (df_puts["strike"] * df_puts["openInterest"]).sum()
                gamma_flip = round(float(c_weight + p_weight) / total_weight, 2)
            elif call_wall > 0 and put_wall > 0:
                gamma_flip = round((call_wall * 0.45 + put_wall * 0.55), 2)
            else:
                gamma_flip = round(spot_price, 2)

            # Skew
            if tot_call_oi > tot_put_oi * 1.25 or pc_ratio < 0.65:
                skew = "Bullish (Long Gamma)"
            elif tot_put_oi > tot_call_oi * 1.25 or pc_ratio > 1.25:
                skew = "Bearish (Put Hedge)"
            else:
                skew = "Neutral / Balanced"

            # ATM IV
            atm_iv = 0.0
            if not df_calls.empty and spot_price > 0:
                near_calls = df_calls.iloc[(df_calls['strike'] - spot_price).abs().argsort()[:3]]
                iv_vals = [float(v) * 100.0 for v in near_calls['impliedVolatility'] if float(v) > 0.05]
                if iv_vals:
                    atm_iv = round(float(np.mean(iv_vals)), 1)

            # Net Dollar Premium
            call_prem = float((df_calls["volume"] * df_calls["lastPrice"] * 100.0).sum()) if not df_calls.empty else 0.0
            put_prem = float((df_puts["volume"] * df_puts["lastPrice"] * 100.0).sum()) if not df_puts.empty else 0.0
            net_dollar_prem = call_prem - put_prem
            net_flow_sentiment = "Bullish" if net_dollar_prem >= 0 else "Bearish"
            net_dollar_str = f"{format_currency(net_dollar_prem)} ({net_flow_sentiment})"

            # Scan Whale Sweeps (> $200k)
            for opt_type, df in [("CALL", df_calls), ("PUT", df_puts)]:
                if df.empty:
                    continue
                for _, row in df.iterrows():
                    vol = int(float(row.get("volume") or 0.0))
                    price = float(row.get("lastPrice") or 0.0)
                    oi = int(float(row.get("openInterest") or 0.0))
                    prem = vol * price * 100.0
                    if prem >= 200000 and price >= 0.05:
                        c_iv = float(row.get("impliedVolatility") or 0.0) * 100.0
                        iv_str = f"{c_iv:.1f}%" if c_iv > 0.05 else "—"
                        c_ratio = round(vol / oi, 2) if oi > 0 else (round(float(vol), 2) if vol > 0 else 1.0)
                        
                        exp_ts = row.get("expiration")
                        if exp_ts and float(exp_ts) > 0:
                            try:
                                exp_dt = datetime.datetime.fromtimestamp(float(exp_ts))
                                dte = max(0, (exp_dt.date() - now.date()).days)
                                exp_str = exp_dt.strftime("%b %d, %Y")
                            except Exception:
                                exp_str = "Near-Term"
                                dte = 7
                        else:
                            exp_str = "Near-Term"
                            dte = 7

                        whale_trades.append({
                            "ticker": clean_sym,
                            "type": opt_type,
                            "strike": f"${float(row.get('strike') or 0):.2f}",
                            "volume": vol,
                            "open_interest": oi,
                            "vol_oi_ratio": c_ratio,
                            "contract_iv": iv_str,
                            "expiry": exp_str,
                            "dte": dte,
                            "premium": prem,
                            "premium_str": format_currency(prem),
                            "flow_tag": "🚀 Whale Sweep" if prem >= 500000 else "🐳 Block Trade",
                            "sentiment": "Bullish" if opt_type == "CALL" else "Bearish"
                        })

            whale_trades.sort(key=lambda x: x["premium"], reverse=True)

            vol_oi_pts = 25 if vol_oi_ratio >= 1.0 else (18 if vol_oi_ratio >= 0.5 else 10)
            skew_pts = 25 if "Bullish" in skew else (12 if "Neutral" in skew else 0)
            pc_pts = 20 if pc_ratio < 0.60 else (15 if pc_ratio < 0.85 else 8)
            net_pts = 15 if net_dollar_prem > 1_000_000 else (10 if net_dollar_prem >= 0 else 5)
            iv_pts = 15 if atm_iv > 0 else 10
            flow_score = min(100, max(0, vol_oi_pts + skew_pts + pc_pts + net_pts + iv_pts))

            flow_badge = f'<span class="pill pill-green">🟢 Flow: {flow_score}/100</span>' if flow_score >= 70 else (
                f'<span class="pill pill-yellow">🟡 Flow: {flow_score}/100</span>' if flow_score >= 45 else
                f'<span class="pill pill-red">🔴 Flow: {flow_score}/100</span>'
            )
            flow_mult = 1.25 if flow_score >= 70 else (1.00 if flow_score >= 45 else 0.80)

            # ATM IV Change session-over-session and IV Rank
            cached_ticker_iv = self._iv_cache.get(clean_sym, {})
            prev_iv = cached_ticker_iv.get("last_iv", atm_iv)
            last_date = cached_ticker_iv.get("date", today_str)

            iv_chg = round(atm_iv - prev_iv, 2) if (prev_iv > 0 and atm_iv > 0 and last_date != today_str) else 0.0
            iv_chg_str = f"{iv_chg:+.2f}%" if atm_iv > 0 else "+0.00%"

            iv_min_cached = min(cached_ticker_iv.get("iv_min", atm_iv * 0.75 if atm_iv > 0 else 12.0), atm_iv) if atm_iv > 0 else 12.0
            iv_max_cached = max(cached_ticker_iv.get("iv_max", atm_iv * 1.35 if atm_iv > 0 else 45.0), atm_iv) if atm_iv > 0 else 45.0
            iv_rank = round(((atm_iv - iv_min_cached) / (iv_max_cached - iv_min_cached) * 100.0), 1) if iv_max_cached > iv_min_cached else 50.0
            iv_rank = max(0.0, min(100.0, iv_rank))

            self._iv_cache[clean_sym] = {
                "date": today_str,
                "last_iv": atm_iv,
                "prev_iv": prev_iv if last_date != today_str else cached_ticker_iv.get("prev_iv", atm_iv),
                "iv_chg": iv_chg,
                "iv_min": iv_min_cached,
                "iv_max": iv_max_cached,
                "iv_rank": iv_rank,
            }

            agg_data = {
                "ticker": clean_sym,
                "date": today_str,
                "stock_price": spot_price,
                "stock_pct_chg": round(stock_pct_chg, 2),
                "stock_price_str": f"${spot_price:.2f}" if spot_price > 0 else "—",
                "stock_pct_chg_str": f"{stock_pct_chg:+.2f}%" if spot_price > 0 else "—",
                "vol_oi_ratio": vol_oi_ratio,
                "atm_iv": atm_iv,
                "atm_iv_str": f"{atm_iv:.1f}%" if atm_iv > 0 else "—",
                "iv_chg": iv_chg,
                "iv_chg_str": iv_chg_str,
                "iv_rank": iv_rank,
                "iv_rank_str": f"{iv_rank:.1f}%",
                "net_dollar_prem": net_dollar_prem,
                "net_dollar_str": net_dollar_str,
                "net_flow_sentiment": net_flow_sentiment,
                "call_wall": f"${call_wall:.2f}" if call_wall > 0 else "—",
                "put_wall": f"${put_wall:.2f}" if put_wall > 0 else "—",
                "gamma_flip": f"${gamma_flip:.2f}" if gamma_flip > 0 else "—",
                "pc_ratio": pc_ratio,
                "skew": skew,
                "flow_conviction_score": flow_score,
                "flow_conviction_badge": flow_badge,
                "flow_sizing_factor": flow_mult,
                "tot_call_vol": int(tot_call_vol),
                "tot_put_vol": int(tot_put_vol),
                "tot_call_oi": int(tot_call_oi),
                "tot_put_oi": int(tot_put_oi),
                "total_45d_vol": int(total_45d_vol),
                "total_45d_oi": int(total_45d_oi),
                "whale_trades": whale_trades,
                "whale_count": len(whale_trades),
            }

            self._cache_aggregated[clean_sym] = agg_data
            self._gamma_disk_cache[clean_sym] = agg_data
            return agg_data

        except Exception as e:
            logger.debug(f"45d gamma calculation error on {clean_sym}: {e}")
            if cached:
                return cached
            return None

    def get_market_options_flow(self, watchlist_tickers: Optional[List[str]] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """Compute 45-Day aggregated gamma structure for all watchlist tickers and market bellwethers."""
        logger.info("Computing 45-Day Aggregated Gamma Structure (Call/Put Walls, Vol/OI, ATM IV, IV Rank, Net Flow, Whale Sweeps)...")
        all_aggregated_list = []
        ticker_gamma_lookup = {}

        # Prioritize core macro bellwethers, portfolio tickers, and top watchlist setups
        scan_pool = ["SPY", "QQQ", "IWM", "DIA"]
        if watchlist_tickers:
            max_options_scan = 80
            for t in watchlist_tickers:
                if t:
                    clean = t.split(":")[-1] if ":" in t else t
                    clean = clean.upper().strip()
                    if clean not in scan_pool and len(clean) <= 5 and clean.isalpha():
                        scan_pool.append(clean)
                    if len(scan_pool) >= max_options_scan:
                        break

        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_sym = {executor.submit(self.compute_45d_ticker_gamma, sym): sym for sym in scan_pool}
            for future in as_completed(future_to_sym):
                try:
                    res = future.result()
                    if res:
                        all_aggregated_list.append(res)
                        ticker_gamma_lookup[res["ticker"]] = res
                except Exception as e:
                    logger.debug(f"Options future error: {e}")

        # Save caches to disk
        self._save_gamma_cache()
        self._save_iv_cache()

        all_aggregated_list.sort(key=lambda x: x.get("vol_oi_ratio", 0.0), reverse=True)
        logger.info(f"Generated 45-Day Gamma Structures for {len(all_aggregated_list)} tickers.")
        return all_aggregated_list, ticker_gamma_lookup

options_scanner = OptionsFlowScanner()
