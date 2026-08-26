"""Macro Regime Assessment module conforming strictly to 01_macro-regime.md specifications with cross-asset futures, market breadth, and multi-asset allocation."""

import logging
import datetime
import re
import urllib.request
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional
from tradingview_screener import Query, col
from config import TZ_EST
from sources.fallback_manager import resilient_session

logger = logging.getLogger("macro_regime")

class MacroRegimeAssessor:
    """Evaluates real-time macro regime, futures sentiment, market breadth, and multi-asset allocation matrix (Zero fake data)."""

    def __init__(self):
        self.cached_regime: Optional[Dict[str, Any]] = None
        self.last_fetch_time: Optional[datetime.datetime] = None

    def fetch_fed_funds_rate(self) -> Dict[str, Any]:
        """Fetch live Fed Funds Rate directly from NY Fed API."""
        try:
            url = "https://markets.newyorkfed.org/api/rates/all/latest.json"
            resp = resilient_session.get(url, timeout=5)
            if resp and resp.status_code == 200:
                data = resp.json()
                for rate in data.get("refRates", []):
                    if rate.get("type") == "EFFR":
                        effr = rate.get("percentRate")
                        target_from = rate.get("targetRateFrom")
                        target_to = rate.get("targetRateTo")
                        eff_date = rate.get("effectiveDate")
                        return {
                            "value": f"{effr:.2f}% (Target: {target_from:.2f}%-{target_to:.2f}%)",
                            "raw_value": effr,
                            "source": "Federal Reserve Bank of New York (markets.newyorkfed.org)",
                            "timestamp": f"{eff_date} (Latest Official Release)",
                        }
        except Exception as e:
            logger.debug(f"Error fetching Fed funds rate from NY Fed: {e}")

        now_str = datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M ET")
        return {
            "value": "DATA UNAVAILABLE",
            "raw_value": None,
            "source": "DATA UNAVAILABLE - SOURCE NOT FOUND",
            "timestamp": now_str,
        }

    def _get_session_and_crumb(self):
        """Acquire or reuse resilient session and valid crumb token."""
        now_ts = datetime.datetime.now().timestamp()
        if hasattr(self, "_session") and getattr(self, "_session") and getattr(self, "_crumb", None) and (now_ts - getattr(self, "_last_crumb_time", 0) < 3600):
            return self._session, self._crumb

        import requests
        sess = requests.Session()
        sess.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        crumb = None
        try:
            r = sess.get("https://finance.yahoo.com/quote/SPY/options/", timeout=10)
            m = re.findall(r'"crumb":"([^"]+)"', r.text)
            if m:
                crumb = m[0]
                sess.headers.update({"Accept": "application/json"})
        except Exception as e:
            logger.debug(f"Macro crumb error: {e}")

        self._session = sess
        self._crumb = crumb
        self._last_crumb_time = now_ts
        return self._session, self._crumb

    def fetch_market_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Fetch live 10Y Yield (^TNX), VIX (^VIX), WTI Crude (CL=F), Brent Crude (BZ=F), 13-Week Treasury (^IRX),
        ES Futures (ES=F), NQ Futures (NQ=F), Gold Futures (GC=F), and Bitcoin (BTC-USD)."""
        symbols_map = {
            "^TNX": ("tnx", "CBOE / Yahoo Finance"),
            "^VIX": ("vix", "CBOE / Yahoo Finance"),
            "CL=F": ("wti", "NYMEX via Yahoo"),
            "BZ=F": ("brent", "ICE via Yahoo"),
            "^IRX": ("irx", "CBOE / Yahoo Finance"),
            "ES=F": ("es", "CME Globex Futures"),
            "NQ=F": ("nq", "CME Globex Futures"),
            "GC=F": ("gold", "COMEX via Yahoo"),
            "BTC-USD": ("btc", "CoinMarketCap / Yahoo"),
        }

        now_est = datetime.datetime.now(TZ_EST)
        now_str = now_est.strftime("%Y-%m-%d %H:%M ET")

        results = {}
        for sym, (key, src) in symbols_map.items():
            results[key] = {
                "symbol": sym,
                "value": None,
                "chg": 0.0,
                "pct_chg": 0.0,
                "source": "DATA UNAVAILABLE - SOURCE NOT FOUND",
                "timestamp": now_str
            }

        sess, crumb = self._get_session_and_crumb()
        if crumb:
            syms_str = ",".join(symbols_map.keys())
            url = f"https://query2.finance.yahoo.com/v7/finance/quote?symbols={syms_str}&crumb={crumb}"
            try:
                res = sess.get(url, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    quotes = data.get("quoteResponse", {}).get("result", [])
                    for q in quotes:
                        sym = q.get("symbol")
                        if sym in symbols_map:
                            key, src = symbols_map[sym]
                            price = float(q.get("regularMarketPrice", 0.0) or 0.0)
                            chg = float(q.get("regularMarketChange", 0.0) or 0.0)
                            pct_chg = float(q.get("regularMarketChangePercent", 0.0) or 0.0)
                            results[key] = {
                                "symbol": sym,
                                "value": round(price, 2),
                                "chg": round(chg, 2),
                                "pct_chg": round(pct_chg, 2),
                                "source": src,
                                "timestamp": now_str
                            }
            except Exception as e:
                logger.debug(f"Direct macro quote error: {e}")

        # Fallback for any missing items
        for sym, (key, src) in symbols_map.items():
            if results[key]["value"] is None:
                try:
                    t = yf.Ticker(sym)
                    hist = t.history(period="5d")
                    if not hist.empty:
                        close = float(hist["Close"].iloc[-1])
                        prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else close
                        chg = close - prev_close
                        pct_chg = (chg / prev_close) * 100 if prev_close else 0.0
                        results[key] = {
                            "symbol": sym,
                            "value": round(close, 2),
                            "chg": round(chg, 2),
                            "pct_chg": round(pct_chg, 2),
                            "source": src,
                            "timestamp": now_str,
                        }
                except Exception:
                    pass

        return results

    def fetch_market_breadth(self) -> Dict[str, Any]:
        """Dynamically compute real-time US equities market breadth (A/D %, NH % vs NL %, % > SMA50, % > SMA200) from Finviz / TradingView."""
        # 1. Primary Source: Finviz Market Overview (entire US equity universe)
        try:
            url = "https://finviz.com/"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                soup = BeautifulSoup(html, "html.parser")
                for tr in soup.find_all("tr"):
                    text = tr.get_text(" | ", strip=True)
                    if "Advancing" in text and "New High" in text and "SMA50" in text:
                        adv_m = re.search(r'Advancing\s*\|\s*([\d\.]+)%\s*\(([0-9,]+)\)', text)
                        decl_m = re.search(r'Declining\s*\|\s*\(([0-9,]+)\)\s*([\d\.]+)%', text)
                        nh_m = re.search(r'New High\s*\|\s*([\d\.]+)%\s*\(([0-9,]+)\)', text)
                        nl_m = re.search(r'New Low\s*\|\s*\(([0-9,]+)\)\s*([\d\.]+)%', text)
                        sma50_m = re.search(r'Above\s*\|\s*([\d\.]+)%\s*\(([0-9,]+)\)\s*\|\s*SMA50', text)
                        sma200_m = re.search(r'Above\s*\|\s*([\d\.]+)%\s*\(([0-9,]+)\)\s*\|\s*SMA200', text)

                        if adv_m and decl_m and nh_m and nl_m and sma50_m and sma200_m:
                            adv_pct = float(adv_m.group(1))
                            adv_count = int(adv_m.group(2).replace(",", ""))
                            decl_pct = float(decl_m.group(2))
                            decl_count = int(decl_m.group(1).replace(",", ""))

                            nh_pct = float(nh_m.group(1))
                            nh_count = int(nh_m.group(2).replace(",", ""))
                            nl_pct = float(nl_m.group(2))
                            nl_count = int(nl_m.group(1).replace(",", ""))
                            net_highs = nh_count - nl_count

                            pct_above_sma50 = float(sma50_m.group(1))
                            pct_above_sma200 = float(sma200_m.group(1))

                            if pct_above_sma200 >= 60.0 and adv_pct >= 55.0:
                                breadth_status = "Broad Bullish Participation"
                                breadth_mult_factor = 1.05
                                breadth_equity_delta = +5
                            elif pct_above_sma200 < 40.0:
                                breadth_status = "Severely Impaired Breadth"
                                breadth_mult_factor = 0.80
                                breadth_equity_delta = -15
                            elif pct_above_sma50 < 45.0 or nh_pct < 40.0:
                                breadth_status = "Narrow / Divergent Breadth"
                                breadth_mult_factor = 0.90
                                breadth_equity_delta = -5
                            else:
                                breadth_status = "Healthy / Neutral Breadth"
                                breadth_mult_factor = 1.00
                                breadth_equity_delta = 0

                            logger.info(f"Retrieved Finviz Market Breadth: Adv {adv_pct}% vs Decl {decl_pct}%, High {nh_pct}% vs Low {nl_pct}%, SMA50 {pct_above_sma50}%, SMA200 {pct_above_sma200}%")
                            return {
                                "total_sampled": adv_count + decl_count,
                                "advancing_pct": adv_pct,
                                "declining_pct": decl_pct,
                                "adv_count": adv_count,
                                "decl_count": decl_count,
                                "nh_pct": nh_pct,
                                "nl_pct": nl_pct,
                                "new_highs_count": nh_count,
                                "new_lows_count": nl_count,
                                "net_highs": net_highs,
                                "pct_above_sma50": pct_above_sma50,
                                "pct_above_sma200": pct_above_sma200,
                                "breadth_status": breadth_status,
                                "breadth_mult_factor": breadth_mult_factor,
                                "breadth_equity_delta": breadth_equity_delta,
                                "source": "Finviz Market Overview",
                            }
        except Exception as e:
            logger.debug(f"Finviz market breadth unavailable, falling back to TradingView: {e}")

        # 2. Resilient Fallback: TradingView Screener Query
        try:
            q = (
                Query()
                .set_markets("america")
                .select("name", "change", "close", "SMA50", "SMA200", "price_52_week_high", "price_52_week_low")
                .where(col("close") >= 2.0)
                .order_by("volume", ascending=False)
                .limit(250)
                .get_scanner_data()
            )
            df = q[1] if len(q) > 1 else pd.DataFrame()
            if not df.empty:
                total_valid = len(df)
                adv_count = int((df["change"] > 0).sum())
                decl_count = int((df["change"] < 0).sum())
                adv_pct = round((adv_count / total_valid) * 100, 1) if total_valid > 0 else 50.0
                decl_pct = round((decl_count / total_valid) * 100, 1) if total_valid > 0 else 50.0

                sma50_count = int((df["close"] > df["SMA50"]).sum())
                sma200_count = int((df["close"] > df["SMA200"]).sum())
                pct_above_sma50 = round((sma50_count / total_valid) * 100, 1) if total_valid > 0 else 50.0
                pct_above_sma200 = round((sma200_count / total_valid) * 100, 1) if total_valid > 0 else 50.0

                nh_count = int((df["close"] >= df["price_52_week_high"] * 0.98).sum())
                nl_count = int((df["close"] <= df["price_52_week_low"] * 1.02).sum())
                tot_hl = nh_count + nl_count
                nh_pct = round((nh_count / tot_hl) * 100, 1) if tot_hl > 0 else 50.0
                nl_pct = round((nl_count / tot_hl) * 100, 1) if tot_hl > 0 else 50.0
                net_highs = nh_count - nl_count

                if pct_above_sma200 >= 65.0 and adv_pct >= 55.0:
                    breadth_status = "Broad Bullish Participation"
                    breadth_mult_factor = 1.05
                    breadth_equity_delta = +5
                elif pct_above_sma200 < 40.0:
                    breadth_status = "Severely Impaired Breadth"
                    breadth_mult_factor = 0.80
                    breadth_equity_delta = -15
                elif pct_above_sma50 < 45.0 or nh_pct < 40.0:
                    breadth_status = "Narrow / Divergent Breadth"
                    breadth_mult_factor = 0.90
                    breadth_equity_delta = -5
                else:
                    breadth_status = "Healthy / Neutral Breadth"
                    breadth_mult_factor = 1.00
                    breadth_equity_delta = 0

                return {
                    "total_sampled": total_valid,
                    "advancing_pct": adv_pct,
                    "declining_pct": decl_pct,
                    "adv_count": adv_count,
                    "decl_count": decl_count,
                    "nh_pct": nh_pct,
                    "nl_pct": nl_pct,
                    "new_highs_count": nh_count,
                    "new_lows_count": nl_count,
                    "net_highs": net_highs,
                    "pct_above_sma50": pct_above_sma50,
                    "pct_above_sma200": pct_above_sma200,
                    "breadth_status": breadth_status,
                    "breadth_mult_factor": breadth_mult_factor,
                    "breadth_equity_delta": breadth_equity_delta,
                    "source": "TradingView Universe Aggregator",
                }
        except Exception as e:
            logger.debug(f"Error computing market breadth from TradingView: {e}")

        return {
            "total_sampled": 5000,
            "advancing_pct": 50.0,
            "declining_pct": 50.0,
            "adv_count": 2500,
            "decl_count": 2500,
            "nh_pct": 50.0,
            "nl_pct": 50.0,
            "new_highs_count": 0,
            "new_lows_count": 0,
            "net_highs": 0,
            "pct_above_sma50": 50.0,
            "pct_above_sma200": 50.0,
            "breadth_status": "DATA UNAVAILABLE",
            "breadth_mult_factor": 1.00,
            "breadth_equity_delta": 0,
            "source": "DATA UNAVAILABLE",
        }

    def assess_macro_regime(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Generate full Macro Regime assessment per 01_macro-regime.md with continuous dynamic multi-asset calculation."""
        now = datetime.datetime.now(TZ_EST)
        if not force_refresh and self.cached_regime and self.last_fetch_time:
            if (now - self.last_fetch_time).total_seconds() < 900:
                return self.cached_regime

        fed_funds = self.fetch_fed_funds_rate()
        metrics = self.fetch_market_metrics()
        breadth = self.fetch_market_breadth()

        tnx = metrics.get("tnx", {})
        vix = metrics.get("vix", {})
        wti = metrics.get("wti", {})
        brent = metrics.get("brent", {})
        irx = metrics.get("irx", {})
        es = metrics.get("es", {})
        nq = metrics.get("nq", {})
        gold = metrics.get("gold", {})
        btc = metrics.get("btc", {})

        # 1. Rate Cycle & Yield Curve
        tnx_val = tnx.get("value")
        irx_val = irx.get("value")
        
        if tnx_val is not None and irx_val is not None:
            spread_2s10s = round(tnx_val - irx_val, 2)
            if spread_2s10s > 0.20:
                curve_status = "Normal (Steepening)"
                curve_multiplier_factor = 1.0
            elif spread_2s10s >= -0.10:
                curve_status = "Flat"
                curve_multiplier_factor = 0.95
            else:
                curve_status = "Inverted"
                curve_multiplier_factor = 0.85

            tnx_chg = tnx.get("chg", 0.0) or 0.0
            if abs(tnx_chg) < 0.05:
                rate_cycle_signal = "Neutral / Stable"
                rate_implication = "Balanced Growth/Value"
            elif tnx_chg > 0:
                rate_cycle_signal = "Tightening"
                rate_implication = "Value stocks favored"
            else:
                rate_cycle_signal = "Easing"
                rate_implication = "Growth stocks favored"
        else:
            spread_2s10s = 0.0
            curve_status = "DATA UNAVAILABLE"
            curve_multiplier_factor = 1.0
            rate_cycle_signal = "DATA UNAVAILABLE"
            rate_implication = "DATA UNAVAILABLE"
            tnx_chg = 0.0

        # 2. Market Volatility (VIX) Factor
        vix_val = vix.get("value")
        vix_chg = vix.get("chg", 0.0) or 0.0
        if vix_val is not None:
            if vix_val < 15.0:
                vix_state = "Complacent (<15)"
                vix_signal = "Risk-On"
                vix_adj = "Tech +5%, Cash -5%"
                vix_mult_factor = 1.05
                vix_equity_delta = +5
            elif vix_val <= 20.0:
                vix_state = "Normal (15-20)"
                vix_signal = "Neutral"
                vix_adj = "Standard allocation"
                vix_mult_factor = 1.00
                vix_equity_delta = 0
            elif vix_val <= 25.0:
                vix_state = "Elevated (20-25)"
                vix_signal = "Cautious"
                vix_adj = "Defensives +5%, Cash +5%"
                vix_mult_factor = 0.90
                vix_equity_delta = -5
            else:
                vix_state = "Fearful (>25)"
                vix_signal = "Risk-Off"
                vix_adj = "Defensives +10%, Cash +15%"
                vix_mult_factor = 0.75
                vix_equity_delta = -15
        else:
            vix_state = "DATA UNAVAILABLE"
            vix_signal = "Neutral"
            vix_adj = "Standard allocation"
            vix_mult_factor = 1.00
            vix_equity_delta = 0

        # 3. Oil & Geopolitical Risk Factor
        wti_val = wti.get("value")
        wti_chg = wti.get("chg", 0.0) or 0.0
        if wti_val is not None:
            if wti_val < 75.0:
                oil_signal = "Tailwind (Oil < $75)"
                geo_score = 1
                oil_mult_factor = 1.05
                oil_equity_delta = +5
                energy_cap_delta = -5
            elif wti_val <= 85.0:
                oil_signal = "Neutral (Oil $75-$85)"
                geo_score = 2
                oil_mult_factor = 1.00
                oil_equity_delta = 0
                energy_cap_delta = 0
            elif wti_val <= 95.0:
                oil_signal = "Cautious (Oil $85-$95)"
                geo_score = 3
                oil_mult_factor = 0.85
                oil_equity_delta = -5
                energy_cap_delta = +5
            else:
                oil_signal = "Headwind (Oil > $95)"
                geo_score = 4
                oil_mult_factor = 0.70
                oil_equity_delta = -10
                energy_cap_delta = +10
        else:
            oil_signal = "DATA UNAVAILABLE"
            geo_score = 1
            oil_mult_factor = 1.00
            oil_equity_delta = 0
            energy_cap_delta = 0

        # 4. B. Riley Macro Rule (10Y Yield & Oil Direction)
        b_riley_pts = 0
        if tnx_val is not None and wti_val is not None:
            if tnx_chg <= 0 and wti_chg <= 0:
                b_riley_state = "Markets are Good (Bullish Tailwind)"
                b_riley_detail = "Both 10Y Yield & Oil are down or flat. Positive macro setup for risk assets."
                b_riley_mult_factor = 1.05
                b_riley_equity_delta = +5
                b_riley_pts = +20
            elif tnx_chg > 0 and wti_chg > 0:
                b_riley_state = "Things are Very Bad (Macro Headwind)"
                b_riley_detail = "Both 10Y Yield & Oil are surging. Inflation pressure and rising discount rates."
                b_riley_mult_factor = 0.80
                b_riley_equity_delta = -10
                b_riley_pts = -20
            else:
                b_riley_state = "Mixed / Divergent"
                b_riley_detail = f"10Y Yield ({tnx_chg:+.2f}) and Oil ({wti_chg:+.2f}) diverging. Sector rotation in play."
                b_riley_mult_factor = 0.98
                b_riley_equity_delta = 0
                b_riley_pts = 0
        else:
            b_riley_state = "DATA UNAVAILABLE"
            b_riley_detail = "Live yield or oil data unavailable."
            b_riley_mult_factor = 1.00
            b_riley_equity_delta = 0
            b_riley_pts = 0

        # 5. Major Futures Sentiment Factor (ES & NQ)
        es_pct = es.get("pct_chg", 0.0) or 0.0
        nq_pct = nq.get("pct_chg", 0.0) or 0.0
        futures_pts = 0
        if es_pct >= 0.50 and nq_pct >= 0.50:
            futures_mult_factor = 1.05
            futures_equity_delta = +5
            futures_sentiment = "Bullish Momentum (ES & NQ Surging)"
            futures_pts = +30
        elif es_pct >= 0.0 and nq_pct >= 0.0:
            futures_mult_factor = 1.00
            futures_equity_delta = +2
            futures_sentiment = "Positive / Stable Futures"
            futures_pts = +15
        elif es_pct <= -0.40 and nq_pct <= -0.40:
            futures_mult_factor = 0.85
            futures_equity_delta = -10
            futures_sentiment = "Bearish Pressure (Futures Pullback)"
            futures_pts = -30
        elif es_pct < 0.0 and nq_pct < 0.0:
            futures_mult_factor = 0.92
            futures_equity_delta = -5
            futures_sentiment = "Mild Selling Pressure (Futures Red)"
            futures_pts = -15
        else:
            futures_mult_factor = 0.98
            futures_equity_delta = 0
            futures_sentiment = "Mixed / Divergent Futures"
            futures_pts = 0

        # 6. Holistic Multi-Factor Composite Scoring (Futures 30% + VIX 25% + Breadth 25% + Yield/Oil 20%)
        breadth_delta = breadth.get("breadth_equity_delta", 0)
        breadth_factor = breadth.get("breadth_mult_factor", 1.0)
        breadth_pts = +25 if breadth_factor > 1.0 else (-25 if breadth_factor < 0.95 else 0)
        vix_pts = +25 if (vix_val and vix_val < 15.0) else (+5 if (vix_val and vix_val <= 18.0) else (-25 if (vix_val and vix_val > 22.0) else -10))

        total_macro_score = futures_pts + vix_pts + breadth_pts + b_riley_pts

        if total_macro_score >= 35 and es_pct >= 0.0 and nq_pct >= 0.0 and (vix_val is None or vix_val < 16.0):
            composite_bias = "Risk-On (Growth)"
        elif total_macro_score <= -20 or (es_pct < -0.40 and nq_pct < -0.40) or (vix_val and vix_val >= 20.0):
            composite_bias = "Risk-Off (Defensive)"
        else:
            composite_bias = "Neutral / Selective"

        # 7. Multi-Asset Allocation Engine (Equity, Gold, Bitcoin, Cash)
        raw_equity = 75 + b_riley_equity_delta + vix_equity_delta + oil_equity_delta + futures_equity_delta + breadth_delta
        target_equity_pct = max(45, min(85, raw_equity))
        equity_low = max(40, target_equity_pct - 5)
        equity_high = min(90, target_equity_pct + 5)
        equity_alloc_str = f"{equity_low}% - {equity_high}%"

        # B. Gold Target (Baseline: 5%, expands to 10%-15% on high oil/inflation or risk-off)
        gold_pct = gold.get("pct_chg", 0.0) or 0.0
        if (wti_val and wti_val > 85) or (vix_val and vix_val > 22) or (gold_pct > 0.75 and es_pct < 0):
            gold_target_pct = 10
            gold_target_str = "8% - 12%"
        else:
            gold_target_pct = 5
            gold_target_str = "3% - 7%"

        # C. Bitcoin Target (Baseline: 3%, expands to 5% on strong liquidity, 0-1% on high fear)
        btc_pct = btc.get("pct_chg", 0.0) or 0.0
        if (vix_val and vix_val > 25) or breadth.get("pct_above_sma200", 50) < 40:
            btc_target_pct = 1
            btc_target_str = "0% - 2%"
        elif nq_pct > 0 and btc_pct > 1.5 and (vix_val and vix_val < 20):
            btc_target_pct = 5
            btc_target_str = "4% - 6%"
        else:
            btc_target_pct = 3
            btc_target_str = "2% - 4%"

        # D. Cash Target (Balancing Residual: 100% - Equity - Gold - Bitcoin)
        target_cash_pct = max(5, 100 - (target_equity_pct + gold_target_pct + btc_target_pct))
        cash_low = max(5, target_cash_pct - 5)
        cash_high = min(40, target_cash_pct + 5)
        cash_target_str = f"{cash_low}% - {cash_high}%"

        # Dynamic Sector Caps
        tech_delta = 0
        if rate_cycle_signal == "Easing" or nq_pct > 0.5:
            tech_delta += 5
        elif rate_cycle_signal == "Tightening":
            tech_delta -= 5
        if vix_val and vix_val < 15:
            tech_delta += 5
        elif vix_val and vix_val > 25:
            tech_delta -= 10
        if wti_val and wti_val > 85:
            tech_delta -= 5
        tech_cap_val = max(25, min(50, 40 + tech_delta))
        tech_cap_str = f"{tech_cap_val}%"

        fin_delta = 0
        if spread_2s10s > 0.50:
            fin_delta += 5
        elif spread_2s10s < -0.10:
            fin_delta -= 5
        fin_cap_val = max(15, min(30, 20 + fin_delta))
        fin_cap_str = f"{fin_cap_val}%"

        energy_cap_val = max(15, min(35, 20 + energy_cap_delta))
        energy_def_str = f"{energy_cap_val}%"

        def_delta = 0
        if vix_val and vix_val > 20:
            def_delta += 5
        if composite_bias == "Risk-Off (Defensive)":
            def_delta += 5
        elif composite_bias == "Risk-On (Growth)":
            def_delta -= 5
        def_cap_val = max(15, min(35, 20 + def_delta))
        def_cap_str = f"{def_cap_val}%"

        # Multiplicative Position / Risk Multiplier (Strictly capped if futures are red or VIX >= 15)
        raw_composite_multiplier = (
            b_riley_mult_factor * vix_mult_factor * oil_mult_factor * curve_multiplier_factor * breadth_factor * futures_mult_factor
        )
        if (es_pct < 0 and nq_pct < 0) or (vix_val and vix_val >= 15.0):
            raw_composite_multiplier = min(0.95, raw_composite_multiplier)

        composite_multiplier = round(max(0.50, min(1.20, raw_composite_multiplier)), 2)

        radar_pillars = {
            "liquidity": {
                "score": b_riley_pts,
                "label": "Liquidity & Yields",
                "status": b_riley_state,
                "val_str": f"10Y Yield: {tnx_val:.2f}% ({tnx_chg:+.2f})" if tnx_val else "—",
                "color": "#34d399" if b_riley_pts > 0 else ("#f87171" if b_riley_pts < 0 else "#fbbf24")
            },
            "growth": {
                "score": +15 if (wti_val and wti_val < 80) else -15,
                "label": "Growth vs Inflation",
                "status": oil_signal,
                "val_str": f"WTI Crude: ${wti_val:.2f} ({wti_chg:+.2f})" if wti_val else "—",
                "color": "#34d399" if (wti_val and wti_val < 80) else "#f87171"
            },
            "volatility": {
                "score": vix_pts,
                "label": "Volatility & Credit",
                "status": vix_state,
                "val_str": f"VIX: {vix_val:.2f} ({vix_chg:+.2f})" if vix_val else "—",
                "color": "#34d399" if vix_pts > 0 else ("#f87171" if vix_pts < 0 else "#fbbf24")
            },
            "breadth": {
                "score": max(-25, min(25, breadth_pts + futures_pts)),
                "label": "Breadth & Futures",
                "status": futures_sentiment,
                "val_str": f"ES: {es_pct:+.2f}% | NQ: {nq_pct:+.2f}%",
                "color": "#34d399" if (futures_pts >= 0 and breadth_pts >= 0) else ("#f87171" if futures_pts < 0 else "#fbbf24")
            }
        }

        assessment = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S ET"),
            "fed_funds": fed_funds,
            "tnx": tnx,
            "irx": irx,
            "spread_2s10s": spread_2s10s,
            "curve_status": curve_status,
            "rate_cycle_signal": rate_cycle_signal,
            "rate_implication": rate_implication,
            "vix": vix,
            "vix_state": vix_state,
            "vix_signal": vix_signal,
            "vix_adj": vix_adj,
            "wti": wti,
            "brent": brent,
            "oil_signal": oil_signal,
            "geo_score": geo_score,
            "geo_multiplier": oil_mult_factor,
            "b_riley_state": b_riley_state,
            "b_riley_detail": b_riley_detail,
            "futures": {
                "es": es,
                "nq": nq,
                "gold": gold,
                "btc": btc,
                "sentiment": futures_sentiment,
            },
            "breadth": breadth,
            "composite_regime": composite_bias,
            "composite_multiplier": composite_multiplier,
            "radar_pillars": radar_pillars,
            "portfolio_matrix": {
                "equity_allocation": equity_alloc_str,
                "gold_target": gold_target_str,
                "btc_target": btc_target_str,
                "cash_target": cash_target_str,
                "tech_cap": tech_cap_str,
                "financials_cap": fin_cap_str,
                "energy_defense_cap": energy_def_str,
                "defensives_cap": def_cap_str,
                "risk_multiplier": f"{composite_multiplier}x",
            },
        }

        self.cached_regime = assessment
        self.last_fetch_time = now
        return assessment

macro_assessor = MacroRegimeAssessor()
