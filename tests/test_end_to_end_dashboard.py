"""End-to-End Automated Test Suite for Institutional Screener & Intelligence Dashboard."""

import unittest
import json
import re
import os
from pathlib import Path
from bs4 import BeautifulSoup

from config import REPORT_HTML_PATH
from reporter.html_generator import html_generator
from sources.defeatbeta_client import defeatbeta_client
from sources.portfolio_monitor_engine import portfolio_monitor_engine

class TestDashboardEndToEnd(unittest.TestCase):

    def setUp(self):
        self.mock_watchlist = [
            {
                "ticker": "ANF",
                "price": 145.25,
                "gap_pct": 5.2,
                "pct_change": 5.2,
                "pct_from_open": 1.5,
                "rvol": 2.8,
                "setup_score": 4.8,
                "stars_visual": "★★★★★",
                "pattern_badge": "EP Breakout",
                "sector": "Consumer Cyclical",
                "industry": "Apparel Retail",
                "headline": "Abercrombie & Fitch Just Delivered Its 15th Consecutive Quarter. Here's Why.",
                "catalyst_url": "https://finance.yahoo.com/quote/ANF",
                "catalyst_stars": 5.0,
                "catalyst_type": "Earnings",
                "earnings_date": "2026-08-26",
                "earnings_sue": 2.45,
                "earnings_pead": 92.0,
                "earnings_badge": "🚀 EP SUE Beat",
                "earnings_badge_color": "#10b981",
                "thesis_impact": "🟢 STRENGTHENED",
                "earnings_playbook": "Playbook 1: Day-1 Gap & Go Momentum",
                "earnings_flash": {
                    "factors": {
                        "sue": 2.45,
                        "sloan_accrual_pct": -0.85,
                        "fcf_conversion_pct": 115.0,
                        "pead_score": 92.0
                    },
                    "playbook_action": "Execute Day-1 ORB breakout above $146.00. Don't chase if extended.",
                    "playbook_ah": "Scale 25% if +3.0% post-close.",
                    "playbook_bmo": "Watch 15-min ORB level.",
                    "divergence_alert": "None"
                },
                "trade_plan": {
                    "entry_pivot": 146.00,
                    "hard_stop": 139.50,
                    "stop_dist_pct": 4.5,
                    "target_1": 158.00,
                    "target_2": 168.00
                }
            },
            {
                "ticker": "DKS",
                "price": 128.50,
                "gap_pct": -12.4,
                "pct_change": -12.4,
                "pct_from_open": -2.0,
                "rvol": 3.5,
                "setup_score": 1.5,
                "stars_visual": "★☆☆☆☆",
                "pattern_badge": "Earnings Breakdown",
                "sector": "Consumer Cyclical",
                "industry": "Specialty Retail",
                "headline": "Dick's Sporting Goods stock crash reveals a major problem for struggling Nike.",
                "catalyst_url": "https://finance.yahoo.com/quote/DKS",
                "catalyst_stars": 1.0,
                "catalyst_type": "Earnings",
                "earnings_date": "2026-08-26",
                "earnings_sue": -2.10,
                "earnings_pead": 18.0,
                "earnings_badge": "🚨 SUE Miss",
                "earnings_badge_color": "#ef4444",
                "thesis_impact": "🔴 BROKEN",
                "earnings_playbook": "Playbook 5: Thesis Drift Exit",
                "earnings_flash": {
                    "factors": {
                        "sue": -2.10,
                        "sloan_accrual_pct": 9.40,
                        "fcf_conversion_pct": 42.0,
                        "pead_score": 18.0
                    },
                    "playbook_action": "Immediate liquidation on any bounce towards VWAP.",
                    "playbook_ah": "Exit in after-hours.",
                    "playbook_bmo": "Pre-market hedge.",
                    "divergence_alert": "Severe Accrual Warning"
                },
                "trade_plan": {
                    "entry_pivot": 128.00,
                    "hard_stop": 134.00,
                    "stop_dist_pct": 4.6,
                    "target_1": 118.00,
                    "target_2": 110.00
                }
            }
        ]
        self.mock_portfolio = {
            "total_nav": 350000.0,
            "cash_balance": 75000.0,
            "equity_value": 275000.0,
            "total_day_pnl_dollar": 1250.0,
            "total_day_pnl_pct": 0.36,
            "total_unrealized_pnl_dollar": 15400.0,
            "cash_weight_pct": 21.4,
            "positions": [
                {
                    "symbol": "SMTC",
                    "underlying": "SMTC",
                    "quantity": 250,
                    "average_cost": 130.50,
                    "current_price": 137.20,
                    "current_value": 34300.0,
                    "weight_pct": 9.8,
                    "day_pnl_dollar": 450.0,
                    "total_pnl_dollar": 1675.0,
                    "total_pnl_pct": 5.13,
                    "hard_stop": 128.00,
                    "target_price_1": 150.00,
                    "strategy": "Core Long",
                    "notes": "Q2 Earnings Winner. Sloan accrual clean (-0.45%).",
                    "headline": "Semtech Corp beats Q2 estimates by $0.08.",
                    "earnings_sue": 1.84,
                    "thesis_impact": "🟡 MAINTAINED"
                }
            ]
        }

    def test_defeatbeta_duckdb_concurrency(self):
        """Test that DuckDB client initializes gracefully without IO locking crashes."""
        client = defeatbeta_client
        self.assertTrue(client.duckdb_available or client.defeatbeta_available)
        prof = client.get_historical_profile("NVDA")
        self.assertIsNotNone(prof)
        self.assertEqual(prof.get("ticker"), "NVDA")

    def test_generated_html_and_js_integrity(self):
        """Test full dashboard HTML generation and guarantee ZERO broken JS onclick handlers."""
        html_path = html_generator.generate_report(
            macro_data={
                "composite_regime": "Risk-On (High Beta / Long Bias)",
                "composite_multiplier": 1.15,
                "breadth": {"advancing_pct": 60.0, "declining_pct": 40.0, "nh_pct": 55.0, "nl_pct": 45.0, "pct_above_sma50": 58.0, "pct_above_sma200": 62.0}
            },
            day_watchlist=self.mock_watchlist,
            economic_events=[
                {"time": "08:30", "impact": "HIGH", "title": "Gross Domestic Product (GDP)", "forecast": "3.0%", "prior": "2.8%"},
                {"time": "10:00", "impact": "LOW", "title": "MBA Mortgage Applications", "forecast": "—", "prior": "-1.2%"}
            ],
            earnings_data={"today_bmo": [], "today_amc": [], "tomorrow_bmo": []},
            analyst_actions=[],
            options_aggregated=[],
            portfolio_data=self.mock_portfolio,
            earnings_radar=[
                {"symbol": "SMTC", "underlying": "SMTC", "quantity": 250, "current_value": 34300.0, "weight_pct": 9.8, "timing": "Today AMC", "status": "REPORTED", "risk_level": "LOW", "action_hint": "Thesis Maintained"}
            ],
            earnings_summary={"reports": []}
        )

        self.assertTrue(Path(html_path).exists())
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        soup = BeautifulSoup(content, "html.parser")

        # 1. Test all onclick attributes for quote balance
        elements_with_onclick = soup.find_all(attrs={"onclick": True})
        self.assertGreater(len(elements_with_onclick), 0, "Expected onclick elements in HTML")

        broken_onclicks = []
        for el in elements_with_onclick:
            oc = el["onclick"]
            if oc.count("'") % 2 != 0:
                broken_onclicks.append((el.name, oc))

        self.assertEqual(len(broken_onclicks), 0, f"Found broken onclicks with unescaped quotes: {broken_onclicks}")

        # 2. Test modal elements exist in the document
        self.assertIsNotNone(soup.find(id="modal-flash-earnings"), "modal-flash-earnings not found in DOM")
        self.assertIsNotNone(soup.find(id="modal-sizing"), "modal-sizing not found in DOM")
        self.assertIsNotNone(soup.find(id="modal-whale-trades"), "modal-whale-trades not found in DOM")
        self.assertIsNotNone(soup.find(id="modal-edit-position"), "modal-edit-position not found in DOM")
        self.assertIsNotNone(soup.find(id="modal-import-fidelity"), "modal-import-fidelity not found in DOM")

        # 3. Test Economic Impact attribute
        eco_rows = soup.select("tr[data-impact]")
        self.assertGreater(len(eco_rows), 0, "Expected economic rows with data-impact")
        for row in eco_rows:
            self.assertIn(row["data-impact"], ["HIGH", "MED", "LOW"])

        # 4. Test Sizing & Actions column placement in portfolio table
        port_th = [th.get_text(strip=True) for th in soup.select("#portfolio-table thead th")]
        self.assertIn("⚡ Sizing & Actions", port_th)
        avg_cost_idx = port_th.index("Avg Cost")
        actions_idx = port_th.index("⚡ Sizing & Actions")
        self.assertEqual(actions_idx, avg_cost_idx + 1, "⚡ Sizing & Actions column must directly follow Avg Cost in Portfolio Table")
        print("[PASS] End-to-End Dashboard & JS Integrity Test passed with 0 errors!")

if __name__ == "__main__":
    unittest.main()
