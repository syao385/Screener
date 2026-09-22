"""
Batch runner to execute and verify earnings-review skill for all 45 portfolio equities.
Saves both JSON and Markdown Dossiers to reports/earnings_review/.
Evaluates cached data vs fundamental changes.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sources.earnings_intelligence import earnings_intel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("batch_earnings_review")

PORTFOLIO_TICKERS = [
    'AAPL', 'AGNC', 'AMAT', 'AMD', 'APLD', 'ARM', 'ASML', 'AXP', 'BBDC', 'BE',
    'COST', 'DELL', 'FLEX', 'GEV', 'GLW', 'GOOGL', 'HOOD', 'HPE', 'INTC', 'IONQ',
    'LITE', 'META', 'MRVL', 'MSFT', 'MU', 'MXL', 'MYRG', 'NBIS', 'NVDA', 'PANW',
    'PLTR', 'SIG', 'SKHY', 'SNDK', 'STRL', 'TSEM', 'TSM', 'TTMI', 'TXN', 'VIAV',
    'VRT', 'VSH', 'VTR', 'WDC', 'ZIM'
]

def run_batch():
    results = []
    logger.info(f"Starting batch earnings review for {len(PORTFOLIO_TICKERS)} equities...")

    for idx, ticker in enumerate(PORTFOLIO_TICKERS, 1):
        logger.info(f"[{idx}/{len(PORTFOLIO_TICKERS)}] Processing {ticker}...")
        try:
            res, was_cached = earnings_intel.get_or_run_earnings_review(ticker)
            flash = res.get("flash_summary") or {}
            lq = flash.get("latest_quarter") or {}
            score = res.get("composite_quality_score")
            stars = res.get("total_master_stars")
            thesis = res.get("thesis_impact") or flash.get("thesis_impact")
            label = res.get("thesis_label") or flash.get("thesis_label")
            dossier_path = res.get("dossier_path")

            item = {
                "ticker": ticker,
                "period": lq.get("period", "N/A"),
                "fiscal_quarter": flash.get("fiscal_quarter", "N/A"),
                "composite_quality_score": score,
                "total_master_stars": stars,
                "thesis_impact": thesis,
                "thesis_label": label,
                "was_cached": was_cached,
                "dossier_path": dossier_path,
                "status": "SUCCESS"
            }
            results.append(item)
            logger.info(
                f" -> {ticker} ({lq.get('period', 'N/A')}): Score={score}, Stars={stars}★, "
                f"Impact={label}, Cached={was_cached}"
            )
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}", exc_info=True)
            results.append({
                "ticker": ticker,
                "status": "ERROR",
                "error": str(e)
            })

    # Save summary report
    summary_path = earnings_intel.markdown_reports_dir / "batch_portfolio_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Batch processing completed. Summary saved to {summary_path}")
    return results

if __name__ == "__main__":
    run_batch()
