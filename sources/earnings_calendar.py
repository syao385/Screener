"""Earnings Calendar module: Real-time Yesterday AMC, Today BMO/AMC, Tomorrow BMO/AMC (Zero fake data)."""

import logging
import datetime
from bs4 import BeautifulSoup
from typing import Dict, List, Any
from config import TZ_EST
from sources.fallback_manager import resilient_session

logger = logging.getLogger("earnings_calendar")

class EarningsCalendar:
    """Fetches real-time Finviz earnings strictly for Yesterday AMC, Today BMO/AMC, and Tomorrow BMO/AMC."""

    def _scrape_finviz_screener(self, filter_code: str, timing_label: str, target_date_iso: str = None, max_pages: int = 2) -> List[Dict[str, Any]]:
        """Helper to scrape Finviz screener for an earnings filter across pages."""
        items = []
        try:
            for page in range(1, max_pages + 1):
                offset_param = f"&r={(page - 1) * 20 + 1}" if page > 1 else ""
                url = f"https://finviz.com/screener.ashx?v=111&f={filter_code}{offset_param}&o=-marketcap"
                resp = resilient_session.get(url, timeout=6)
                if not resp or resp.status_code != 200:
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                rows_found = 0
                for row in soup.find_all("tr"):
                    tds = row.find_all("td")
                    if len(tds) == 11 and tds[0].text.strip().isdigit():
                        ticker = tds[1].get("data-boxover-ticker")
                        if not ticker:
                            tab_link = tds[1].find("a", class_="tab-link")
                            ticker = tab_link.text.strip() if tab_link else None

                        if ticker and ticker != "Ticker":
                            company = tds[1].get("data-boxover-company") or tds[2].text.strip()
                            sector = tds[3].text.strip()
                            industry = tds[1].get("data-boxover-industry") or tds[4].text.strip()
                            mkt_cap = tds[1].get("data-boxover-value") or tds[6].text.strip()
                            price = tds[8].text.strip() if len(tds) > 8 else "—"
                            change = tds[9].text.strip() if len(tds) > 9 else "—"
                            try:
                                clean_chg = change.replace("%", "").replace("+", "").strip()
                                pct_val = float(clean_chg)
                            except Exception:
                                pct_val = 0.0

                            if not any(x["ticker"] == ticker for x in items):
                                rows_found += 1
                                items.append({
                                    "ticker": ticker,
                                    "company": company,
                                    "sector": sector,
                                    "industry": industry,
                                    "date": target_date_iso,
                                    "timing": timing_label,
                                    "market_cap": mkt_cap,
                                    "price": price,
                                    "change": change,
                                    "pct_change": pct_val,
                                    "url": f"https://finviz.com/quote.ashx?t={ticker}",
                                })

                if rows_found < 20:
                    break
        except Exception as e:
            logger.debug(f"Error scraping Finviz earnings for {filter_code}: {e}")

        return items

    def get_earnings_dashboard(self) -> Dict[str, Any]:
        """Fetch all Yesterday AMC, Today BMO/AMC, and Tomorrow BMO/AMC earnings (No next week)."""
        now_est = datetime.datetime.now(TZ_EST)
        if hasattr(self, "_cached_dashboard") and getattr(self, "_cached_dashboard_time", None):
            age = (now_est - self._cached_dashboard_time).total_seconds()
            if age < 300:
                return self._cached_dashboard

        logger.info("Fetching Finviz-style Earnings Calendar (Yesterday, Today & Tomorrow)...")
        today_str = now_est.strftime("%b %d")
        yest_str = (now_est - datetime.timedelta(days=1)).strftime("%b %d")
        tom_str = (now_est + datetime.timedelta(days=1)).strftime("%b %d")

        today_iso = now_est.strftime("%Y-%m-%d")
        yest_iso = (now_est - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        tom_iso = (now_est + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        today_bmo = self._scrape_finviz_screener("earningsdate_todaybefore", timing_label=f"{today_str} b", target_date_iso=today_iso, max_pages=1)
        yesterday_amc = self._scrape_finviz_screener("earningsdate_yesterdayafter", timing_label=f"{yest_str} a", target_date_iso=yest_iso, max_pages=1)
        today_amc = self._scrape_finviz_screener("earningsdate_todayafter", timing_label=f"{today_str} a", target_date_iso=today_iso, max_pages=1)
        tomorrow_bmo = self._scrape_finviz_screener("earningsdate_tomorrowbefore", timing_label=f"{tom_str} b", target_date_iso=tom_iso, max_pages=1)
        tomorrow_amc = self._scrape_finviz_screener("earningsdate_tomorrowafter", timing_label=f"{tom_str} a", target_date_iso=tom_iso, max_pages=1)

        # Merge unique upcoming items (Today AMC + Tomorrow BMO + Tomorrow AMC)
        existing_tickers = {x["ticker"] for x in today_bmo} | {x["ticker"] for x in yesterday_amc}
        upcoming_combined = []
        for item in today_amc + tomorrow_bmo + tomorrow_amc:
            if item["ticker"] not in existing_tickers:
                existing_tickers.add(item["ticker"])
                upcoming_combined.append(item)

        logger.info(f"Retrieved Earnings: Today BMO ({len(today_bmo)}), Yesterday AMC ({len(yesterday_amc)}), Today AMC ({len(today_amc)}), Tomorrow BMO/AMC ({len(tomorrow_bmo) + len(tomorrow_amc)})")

        res = {
            "today_bmo": today_bmo,
            "yesterday_amc": yesterday_amc,
            "today_amc": today_amc,
            "tomorrow_bmo": tomorrow_bmo,
            "tomorrow_amc": tomorrow_amc,
            "upcoming_5d": upcoming_combined,
            "today_str": today_str,
            "yest_str": yest_str,
            "tom_str": tom_str,
            "source": "Finviz Earnings Screener (finviz.com/screener.ashx)",
            "timestamp": now_est.strftime("%Y-%m-%d %H:%M ET"),
        }
        self._cached_dashboard = res
        self._cached_dashboard_time = now_est
        return res

    def get_full_calendar(self) -> Dict[str, Any]:
        """Alias for get_earnings_dashboard for backward compatibility."""
        return self.get_earnings_dashboard()

earnings_cal = EarningsCalendar()
