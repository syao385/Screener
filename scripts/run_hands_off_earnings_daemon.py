"""
Hands-Off Earnings Intelligence & Longitudinal Thesis Drift Daemon.
===================================================================
Orchestrates automated two-step earnings lifecycle processing:
1. Phase A (Flash / Press Release): Immediate SUE, price reaction, and preliminary review.
2. Phase B (Audited SEC 10-Q/10-K): Full balance sheet, forensic accruals, and DuckDB drift tracking.
3. Automatically triggers UI rebuild (latest_report.html) when new reports are processed.

Usage:
  python scripts/run_hands_off_earnings_daemon.py --session AUTO
  python scripts/run_hands_off_earnings_daemon.py --session BMO
  python scripts/run_hands_off_earnings_daemon.py --session AMC
  python scripts/run_hands_off_earnings_daemon.py --audit-10q
  python scripts/run_hands_off_earnings_daemon.py --daemon --interval 300
"""

import sys
import argparse
import logging
from pathlib import Path

# Set up project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sources.earnings_scheduler import earnings_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("hands_off_earnings")

def main():
    parser = argparse.ArgumentParser(description="Hands-Off Institutional Earnings Intelligence & Thesis Drift Daemon")
    parser.add_argument("--session", choices=["AUTO", "BMO", "AMC", "NIGHTLY"], default="AUTO", help="Target earnings session")
    parser.add_argument("--audit-10q", action="store_true", help="Run immediate SEC 10-Q/10-K filing upgrade audit")
    parser.add_argument("--daemon", action="store_true", help="Run continuously as background daemon")
    parser.add_argument("--interval", type=int, default=300, help="Daemon poll interval in seconds (default: 300s)")
    parser.add_argument("--no-ui", action="store_true", help="Skip automatic latest_report.html rebuild")

    args = parser.parse_args()
    rebuild_ui = not args.no_ui

    if args.daemon:
        logger.info(f"Launching Hands-Off Earnings Daemon (Interval: {args.interval}s, Rebuild UI: {rebuild_ui})...")
        earnings_scheduler.run_daemon(interval_seconds=args.interval)
    elif args.audit_10q:
        logger.info("Executing on-demand SEC 10-Q/10-K audit across portfolio...")
        stats = earnings_scheduler.check_sec_10q_filing_updates(rebuild_ui=rebuild_ui)
        print(f"SEC 10-Q Audit Complete. Upgraded: {len(stats.get('upgraded', []))}, Unchanged: {stats.get('unchanged_count', 0)}")
    else:
        logger.info(f"Executing one-shot earnings check for session: {args.session}...")
        res = earnings_scheduler.check_and_process_daily_earnings(session=args.session, rebuild_ui=rebuild_ui)
        print(f"[{res['session']}] Processed {res['processed_count']} earnings releases. UI Rebuilt: {res['ui_rebuilt']}")
        if res.get("details"):
            for item in res["details"]:
                print(f" -> {item['ticker']}: Score={item['score']}, Stage={item['filing_stage']}, Playbook={item['playbook']}")

if __name__ == "__main__":
    main()
