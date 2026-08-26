"""Analyst Ratings module: Real-time dynamic analyst upgrades, downgrades, and price targets (Zero hardcoding)."""

import re
import time
import logging
import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Set
from config import TZ_EST
from sources.fallback_manager import resilient_session

logger = logging.getLogger("analyst_ratings")

class AnalystRatings:
    """Aggregates real-time structured analyst upgrades, downgrades, and price target revisions dynamically."""

    def __init__(self):
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    def fetch_ratings_for_ticker(self, ticker: str, min_date: datetime.date) -> List[Dict[str, Any]]:
        """Fetch latest clean analyst actions for a given ticker from Finviz quote ratings table (Yesterday & Today)."""
        clean_sym = ticker.split(":")[-1] if ":" in ticker else ticker
        clean_sym = clean_sym.upper().strip()

        if not re.match(r"^[A-Z]{1,5}$", clean_sym):
            return []

        if clean_sym in self._cache:
            return self._cache[clean_sym]

        actions = []

        try:
            time.sleep(0.12)  # Polite spacing to prevent 429
            url = f"https://finviz.com/quote.ashx?t={clean_sym}"
            resp = resilient_session.get(url, timeout=5)
            if resp and resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for tr in soup.find_all("tr"):
                    tds = [td.text.strip().encode("ascii", "ignore").decode("ascii") for td in tr.find_all("td")]
                    if len(tds) == 5 and tds[1] in ("Upgrade", "Downgrade", "Initiated", "Reiterated", "Maintains", "Resumed"):
                        date_val, action_val, firm_val, rating_val, target_val = tds
                        
                        # Date filter: check if yesterday or today
                        is_recent = False
                        if date_val.lower() in ("today", "yesterday"):
                            is_recent = True
                        else:
                            try:
                                parsed_d = datetime.datetime.strptime(date_val, "%b-%d-%y").date()
                                if parsed_d >= min_date:
                                    is_recent = True
                            except Exception:
                                pass

                        if is_recent:
                            rating_clean = rating_val.replace("  ", " -> ").replace("&rarr;", "->")
                            target_clean = target_val.replace("  ", " -> ").replace("&rarr;", "->")

                            if firm_val and len(firm_val) < 50:
                                actions.append({
                                    "ticker": clean_sym,
                                    "date": date_val,
                                    "firm": firm_val,
                                    "action": action_val,
                                    "rating": rating_clean or "—",
                                    "price_target": target_clean or "—",
                                    "source": "Finviz Analyst Feed",
                                })
        except Exception as e:
            logger.debug(f"Finviz analyst scrape failed for {clean_sym}: {e}")

        self._cache[clean_sym] = actions
        return actions

    def _discover_dynamic_screener_tickers(self) -> Set[str]:
        """Dynamically discover tickers from live Finviz signal screeners without any static hardcoding."""
        discovered = set()
        # Query Finviz live signal screeners for upgrades, downgrades, major news, and momentum
        for signal_code in ["n_upgrades", "n_downgrades", "n_majornews", "ta_topgainers"]:
            try:
                url = f"https://finviz.com/screener.ashx?v=111&s={signal_code}&o=-marketcap"
                resp = resilient_session.get(url, timeout=5)
                if resp and resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for tr in soup.find_all("tr"):
                        tds = tr.find_all("td")
                        if len(tds) == 11 and tds[0].text.strip().isdigit():
                            ticker = tds[1].get("data-boxover-ticker")
                            if not ticker:
                                a_tag = tds[1].find("a")
                                ticker = a_tag.text.strip() if a_tag else None
                            if ticker and re.match(r"^[A-Z]{1,5}$", ticker):
                                discovered.add(ticker)
            except Exception as e:
                logger.debug(f"Error scraping {signal_code} screener: {e}")

        return discovered

    def get_market_upgrades(self, watchlist_tickers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Dynamically fetch all analyst actions strictly from Yesterday and Today in parallel (Zero hardcoded tickers)."""
        logger.info("Aggregating Analyst Upgrades and Downgrades (100% Dynamic Discovery)...")
        now_est = datetime.datetime.now(TZ_EST)
        yesterday_date = now_est.date() - datetime.timedelta(days=1)

        all_actions = []
        discovered = list(self._discover_dynamic_screener_tickers())
        target_tickers = []
        
        # Priority 1: Watchlist candidate tickers (top 15)
        if watchlist_tickers:
            for sym in watchlist_tickers:
                clean = sym.split(":")[-1] if ":" in sym else sym
                clean = clean.upper().strip()
                if re.match(r"^[A-Z]{1,5}$", clean) and clean not in target_tickers:
                    target_tickers.append(clean)
                if len(target_tickers) >= 15:
                    break

        # Priority 2: Discovered market signal tickers (up to 20 total)
        for sym in discovered:
            if sym not in target_tickers:
                target_tickers.append(sym)
            if len(target_tickers) >= 20:
                break

        logger.info(f"Dynamically evaluating {len(target_tickers)} priority tickers for Yesterday/Today analyst actions...")

        # Parallel fetch with controlled rate spacing (3 workers)
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_sym = {executor.submit(self.fetch_ratings_for_ticker, sym, yesterday_date): sym for sym in target_tickers}
            for future in as_completed(future_to_sym):
                try:
                    ticker_actions = future.result()
                    for act in ticker_actions:
                        if not any(a["ticker"] == act["ticker"] and a["firm"] == act["firm"] and a["date"] == act["date"] for a in all_actions):
                            all_actions.append(act)
                except Exception as e:
                    logger.debug(f"Analyst future error: {e}")

        # Sort: Upgrades first, then by ticker alphabetically
        def action_sort_key(x):
            is_up = 0 if "upgrade" in x.get("action", "").lower() else 1
            return (is_up, x.get("ticker", ""))

        all_actions.sort(key=action_sort_key)

        logger.info(f"Retrieved {len(all_actions)} recent analyst actions (Yesterday & Today).")
        return all_actions

analyst_feed = AnalystRatings()
