import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
from sources.portfolio_manager import portfolio_mgr
from reporter.html_generator import html_generator

def rebuild_report_fast() -> str:
    """Build report using cached portfolio and zero unnecessary network calls."""
    portfolio_data = portfolio_mgr.load_portfolio()
    html_path = html_generator.generate_report(
        macro_data={"composite_score": 62, "regime_label": "BULLISH_EXPANSION", "composite_multiplier": 1.0, "top_factors": [], "bottom_factors": []},
        day_watchlist=[],
        economic_events=[],
        earnings_data={},
        analyst_actions=[],
        options_aggregated=[],
        session_label="REGULAR_HOURS",
        portfolio_data=portfolio_data,
        earnings_summary={"reports": []},
        earnings_radar=[],
        sector_flow_data={}
    )
    return str(html_path)

if __name__ == "__main__":
    path = rebuild_report_fast()
    print("Rebuilt report at:", path)
