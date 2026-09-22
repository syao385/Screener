"""Scheduled Batch Runner for Earnings Intelligence Engine.

Processes 20-40 tickers per batch covering:
- Yesterday AMC
- Today BMO
- Today AMC (if in after-hours or post-market session)
- Priority queue: Portfolio holdings > EP Day 1-5 (RVOL > 2.0) > Large Cap ($10B+)
"""

import os
import json
import logging
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import TZ_EST
from sources.earnings_calendar import earnings_cal
from sources.earnings_intelligence import earnings_intel
from sources.portfolio_manager import PortfolioManager

logger = logging.getLogger("earnings_scheduler")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "earnings_reports"
SUMMARY_FILE = REPORTS_DIR / "summary.json"


class EarningsScheduler:
    """Institutional Batch Orchestrator for Daily Earnings 4-Master Processing."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.port_mgr = PortfolioManager()

    def get_priority_earnings_universe(self, max_tickers: int = 35) -> List[Dict[str, Any]]:
        """Collect and prioritize tickers from Earnings Calendar and Portfolio."""
        cal_data = earnings_cal.get_earnings_dashboard()
        yest_amc = cal_data.get("yesterday_amc", [])
        today_bmo = cal_data.get("today_bmo", [])
        today_amc = cal_data.get("today_amc", [])

        # Ingest active portfolio tickers for top priority
        port_data = self.port_mgr.load_portfolio()
        port_tickers = {p.get("symbol", "").upper() for p in port_data.get("positions", []) if p.get("symbol")}

        all_candidates = []
        seen = set()

        for item in yest_amc + today_bmo + today_amc:
            sym = item.get("ticker", "").upper().strip()
            if sym and sym not in seen:
                seen.add(sym)
                is_port = sym in port_tickers
                pct_chg = abs(item.get("pct_change", 0.0))
                all_candidates.append({
                    "ticker": sym,
                    "company": item.get("company", sym),
                    "timing": item.get("timing", "—"),
                    "market_cap": item.get("market_cap", "—"),
                    "pct_change": pct_chg,
                    "is_portfolio": is_port,
                })

        # Dynamic EP Day 1-5 Universe Discovery from SQLite State Manager (Zero hardcoded seed tickers)
        try:
            from sources.state_manager import state_mgr
            active_eps = state_mgr.get_active_eps()
            for ep in active_eps:
                sym = ep.get("ticker", "").upper().strip()
                if sym and sym not in seen:
                    seen.add(sym)
                    all_candidates.append({
                        "ticker": sym,
                        "company": ep.get("company_name", sym),
                        "timing": f"EP Day {ep.get('day_count', 1)}",
                        "market_cap": "Mid/Large",
                        "pct_change": abs(ep.get("day1_gap_pct", 5.0)),
                        "is_portfolio": sym in port_tickers,
                    })
        except Exception as e:
            logger.debug(f"Dynamic EP discovery lookup: {e}")

        # Priority Sorting:
        # 1. Portfolio holdings (score = 1000)
        # 2. EP Day 1-5 setups with large price movements (|chg| >= 4%)
        # 3. Market Cap / Liquidity
        def sort_key(x):
            score = 0.0
            if x["is_portfolio"]:
                score += 1000.0
            score += min(100.0, x["pct_change"] * 10.0)
            return score

        all_candidates.sort(key=sort_key, reverse=True)
        return all_candidates[:max_tickers]

    def run_batch_review(self, max_tickers: int = 30) -> Dict[str, Any]:
        """Execute parallel 4-Master reviews on prioritized earnings universe."""
        universe = self.get_priority_earnings_universe(max_tickers=max_tickers)
        logger.info(f"Starting Earnings Intelligence batch run for {len(universe)} priority tickers...")

        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_item = {
                executor.submit(earnings_intel.run_four_masters_analysis, item["ticker"]): item
                for item in universe
            }

            for future in as_completed(future_to_item):
                item = future_to_item[future]
                sym = item["ticker"]
                try:
                    res = future.result()
                    results.append(res)
                    logger.info(f"Completed 4-Master analysis for {sym} (Quality Score: {res.get('composite_quality_score')})")
                except Exception as e:
                    logger.error(f"Failed analysis for {sym}: {e}")

        # Build summary file
        summary_payload = {
            "last_batch_run": datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET"),
            "total_processed": len(results),
            "tickers": [r.get("ticker") for r in results if r],
            "reports": results,
        }

        try:
            with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
                json.dump(summary_payload, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving batch summary: {e}")

        return summary_payload

    def get_summary_reports(self) -> Dict[str, Any]:
        """Load latest batch summary from disk or run on-demand if empty."""
        if SUMMARY_FILE.exists():
            try:
                with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return self.run_batch_review(max_tickers=10)

    def check_sec_10q_filing_updates(self, rebuild_ui: bool = True) -> Dict[str, Any]:
        """
        Off-Hours / Nightly SEC 10-Q & 10-K Poller.
        Scans all portfolio holdings for newly audited financial filings.
        Upgrades preliminary flash reviews to AUDITED_10Q_FINAL with true Sloan accruals,
        Beneish M-scores, and updated Thesis Drift history in DuckDB.
        """
        logger.info("Executing SEC 10-Q / 10-K audited filing audit across portfolio...")
        port_data = self.port_mgr.load_portfolio()
        upgraded = []
        unchanged = []

        from sources.earnings_intelligence import KNOWN_ETFS
        equities = []
        for pos in port_data.get("positions", []):
            sym = (pos.get("symbol") or "").upper().strip()
            if not sym or sym in KNOWN_ETFS or "-" in sym or sym.startswith("$") or sym == "SPAXX**":
                continue
            equities.append(sym)

        for sym in equities:
            clean_sym = sym.replace("/", "_").replace(":", "_").replace("\\", "_")
            json_file = REPORTS_DIR / f"{clean_sym}_Latest.json"
            if not json_file.exists():
                json_file = REPORTS_DIR / f"{clean_sym}.json"

            was_prelim = False
            if json_file.exists():
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                    was_prelim = cached.get("filing_stage") == "PRELIMINARY_RELEASE"
                except Exception:
                    pass

            # Check lake profile
            try:
                from sources.defeatbeta_client import fundamental_engine
                profile = fundamental_engine.get_historical_profile(sym, fetch_remote=False)
                quarters = profile.get("quarters") or []
                if quarters:
                    lq = quarters[0]
                    # If quarter has audited balance sheet/cash flow, ensure audited upgrade
                    has_audited_data = (
                        lq.get("operating_cash_flow") is not None
                        and lq.get("total_cash") is not None
                        and lq.get("revenue") is not None
                    )
                    if was_prelim and has_audited_data:
                        logger.info(f"Detected newly audited 10-Q filing for {sym} ({lq.get('period')}). Upgrading...")
                        rep, _ = earnings_intel.get_or_run_earnings_review(sym, force_refresh=True)
                        upgraded.append(sym)
                    else:
                        unchanged.append(sym)
            except Exception as e:
                logger.debug(f"Filing update check error for {sym}: {e}")

        logger.info(f"SEC 10-Q audit completed. Upgraded: {len(upgraded)}, Unchanged: {len(unchanged)}")

        if upgraded and rebuild_ui:
            try:
                from scripts.rebuild_report_fast import rebuild_report_fast
                logger.info("Regenerating latest_report.html with newly audited SEC filings...")
                rebuild_report_fast()
            except Exception as e_ui:
                logger.error(f"Error rebuilding report after 10-Q upgrade: {e_ui}")

        return {"upgraded": upgraded, "unchanged_count": len(unchanged)}

    def check_and_process_daily_earnings(self, session: str = "AUTO", rebuild_ui: bool = True) -> Dict[str, Any]:
        """
        Hands-off daily earnings processor for BMO, AMC, and Nightly 10-Q sweeps.
        Runs as soon as corporate earnings drop:
        1. Generates Flash preliminary review (SUE, Gap %, immediate playbook).
        2. Logs thesis drift and updates the two-stage lifecycle state machine.
        3. If in nightly session, audits 10-Q filings.
        4. Keeps latest_report.html synchronized.
        """
        now_est = datetime.datetime.now(TZ_EST)
        if session == "AUTO":
            t = now_est.time()
            if t < datetime.time(9, 30):
                session = "BMO"
            elif datetime.time(16, 0) <= t < datetime.time(20, 0):
                session = "AMC"
            else:
                session = "NIGHTLY"

        logger.info(f"Starting automated Hands-Off Earnings processing (Session: {session})...")
        cal_data = earnings_cal.get_earnings_dashboard()
        target_cal_items = []
        if session == "BMO":
            target_cal_items = cal_data.get("today_bmo", [])
        elif session == "AMC":
            target_cal_items = cal_data.get("today_amc", [])
        else:
            # Nightly: check yesterday_amc, today_bmo, today_amc
            target_cal_items = (
                cal_data.get("yesterday_amc", [])
                + cal_data.get("today_bmo", [])
                + cal_data.get("today_amc", [])
            )

        port_data = self.port_mgr.load_portfolio()
        from sources.earnings_intelligence import KNOWN_ETFS
        port_equities = {
            p.get("symbol", "").upper().strip()
            for p in port_data.get("positions", [])
            if p.get("symbol")
            and p.get("symbol") not in KNOWN_ETFS
            and "-" not in p.get("symbol")
            and not p.get("symbol").startswith("$")
            and p.get("symbol") != "SPAXX**"
        }

        # Target set: Portfolio reporting today + top EP movers
        to_process = set()
        for item in target_cal_items:
            sym = item.get("ticker", "").upper().strip()
            if sym and sym in port_equities:
                to_process.add(sym)

        # Include any high-momentum EP movers
        for item in target_cal_items:
            sym = item.get("ticker", "").upper().strip()
            if sym and abs(item.get("pct_change", 0.0)) >= 4.0:
                to_process.add(sym)

        processed_results = []
        for sym in sorted(to_process):
            logger.info(f"Hands-Off Engine: Processing earnings release for {sym}...")
            try:
                res, was_cached = earnings_intel.get_or_run_earnings_review(sym, force_refresh=True)
                processed_results.append({
                    "ticker": sym,
                    "score": res.get("composite_quality_score"),
                    "thesis_impact": res.get("thesis_label"),
                    "filing_stage": res.get("filing_stage_label"),
                    "playbook": (res.get("trade_desk_playbook") or {}).get("active_playbook"),
                    "dossier": res.get("dossier_path"),
                })
            except Exception as e:
                logger.error(f"Error processing {sym} in hands-off run: {e}")

        # If Nightly, also run 10-Q filing upgrade sweep
        sec_audit_stats = {}
        if session == "NIGHTLY":
            sec_audit_stats = self.check_sec_10q_filing_updates(rebuild_ui=False)

        # Automatically rebuild UI dashboard if new reports were processed or upgraded
        needs_ui_rebuild = bool(processed_results or sec_audit_stats.get("upgraded"))
        if needs_ui_rebuild and rebuild_ui:
            try:
                from scripts.rebuild_report_fast import rebuild_report_fast
                logger.info("Hands-off trigger: Regenerating latest_report.html dashboard...")
                rebuild_report_fast()
            except Exception as e_ui:
                logger.error(f"Failed rebuilding report HTML: {e_ui}")

        return {
            "session": session,
            "timestamp": now_est.strftime("%Y-%m-%d %H:%M:%S ET"),
            "processed_count": len(processed_results),
            "processed_tickers": [p["ticker"] for p in processed_results],
            "details": processed_results,
            "sec_10q_upgrades": sec_audit_stats.get("upgraded", []),
            "ui_rebuilt": needs_ui_rebuild,
        }

    def run_daemon(self, interval_seconds: int = 300, max_cycles: Optional[int] = None):
        """
        Background Daemon Loop.
        Monitors time of day and calendar triggers:
        - 08:00 AM EST: BMO Releases check
        - 04:15 PM EST: AMC Releases check
        - 09:00 PM EST: Nightly 10-Q SEC filing audit sweep
        """
        import time
        logger.info(f"Starting Hands-Off Earnings Intelligence Daemon (Polling every {interval_seconds}s)...")
        cycles = 0
        last_bmo_date = None
        last_amc_date = None
        last_nightly_date = None

        while True:
            cycles += 1
            now_est = datetime.datetime.now(TZ_EST)
            today = now_est.date()
            t = now_est.time()

            try:
                # 08:00 - 09:15 EST: Morning BMO Window
                if datetime.time(8, 0) <= t < datetime.time(9, 30) and last_bmo_date != today:
                    logger.info(f"Triggering Morning BMO Earnings Check for {today}...")
                    self.check_and_process_daily_earnings(session="BMO", rebuild_ui=True)
                    last_bmo_date = today

                # 16:15 - 18:00 EST: After-Hours AMC Window
                elif datetime.time(16, 15) <= t < datetime.time(20, 0) and last_amc_date != today:
                    logger.info(f"Triggering After-Hours AMC Earnings Check for {today}...")
                    self.check_and_process_daily_earnings(session="AMC", rebuild_ui=True)
                    last_amc_date = today

                # 21:00 - 23:00 EST: Nightly 10-Q / 10-K SEC Filing Audit Window
                elif datetime.time(21, 0) <= t < datetime.time(23, 59) and last_nightly_date != today:
                    logger.info(f"Triggering Nightly SEC 10-Q/10-K Audit Sweep for {today}...")
                    self.check_sec_10q_filing_updates(rebuild_ui=True)
                    last_nightly_date = today

            except Exception as e:
                logger.error(f"Error in hands-off daemon cycle {cycles}: {e}", exc_info=True)

            if max_cycles and cycles >= max_cycles:
                logger.info(f"Daemon reached max cycles ({max_cycles}). Exiting.")
                break

            time.sleep(interval_seconds)


# Global singleton instance
earnings_scheduler = EarningsScheduler()
