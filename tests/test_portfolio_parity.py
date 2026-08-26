"""Automated unit and integration test suite for Portfolio Manager feature parity."""

import unittest
import os
import json
from pathlib import Path

from sources.portfolio_manager import portfolio_mgr, extract_underlying_ticker
from reporter.html_generator import html_generator

class TestPortfolioManagerParity(unittest.TestCase):

    def test_extract_underlying_ticker(self):
        """Test extraction of underlying ticker from stock and option symbols."""
        cases = [
            ("NVDA", "NVDA"),
            ("AAPL", "AAPL"),
            ("-NVDA260828C210", "NVDA"),
            ("-AAPL240920P220", "AAPL"),
            ("TSLA250117C250", "TSLA"),
            ("SPY241220C550", "SPY"),
            ("BRK.B", "BRK.B"),
            ("-MSFT260116C400", "MSFT"),
        ]
        for raw, expected in cases:
            res = extract_underlying_ticker(raw)
            self.assertEqual(res, expected, f"Expected {expected} for {raw}, got {res}")
        print("[PASS] extract_underlying_ticker test passed.")

    def test_enrich_live_metrics(self):
        """Test portfolio live metrics enrichment with market lookup data."""
        sample_portfolio = {
            "account_name": "Test Account",
            "account_number": "Z12345678",
            "total_nav": 100000.0,
            "cash_balance": 20000.0,
            "positions": [
                {
                    "symbol": "NVDA",
                    "quantity": 100.0,
                    "average_cost": 120.0,
                    "last_price": 130.0,
                    "current_value": 13000.0,
                    "is_option": False,
                    "strategy_tag": "Core Long Holding"
                },
                {
                    "symbol": "-NVDA260828C210",
                    "quantity": 2.0,
                    "average_cost": 5.0,
                    "last_price": 7.0,
                    "current_value": 1400.0,
                    "is_option": True,
                    "strategy_tag": "Options Hedge / Income"
                }
            ]
        }
        market_lookup = {
            "NVDA": {
                "ticker": "NVDA",
                "price": 130.0,
                "pct_change": 4.5,
                "gap_pct": 2.1,
                "pct_from_open": 2.35,
                "vwap": "$128.50",
                "vwap_dist": 1.17,
                "sma20": "$125.00",
                "sma20_dist": 4.0,
                "sma50": "$120.00",
                "sma50_dist": 8.33,
                "sma200": "$110.00",
                "sma200_dist": 18.18,
                "call_wall": "$135.00",
                "put_wall": "$120.00",
                "gamma_flip": "$127.50",
                "gamma_skew": "Bullish Gamma",
                "pc_ratio": "0.55",
                "vol_oi_ratio": 2.5,
                "atm_iv_str": "45.0%",
                "setup_score": 4.5,
                "stars_visual": "★★★★☆",
                "catalyst_stars": 4.0,
                "is_positive": True,
                "breakout_last_high": True,
                "breakout_pm_high": True,
                "sector": "Technology",
                "industry": "Semiconductors",
                "headline": "NVDA Next-Gen Blackwell chips shipping in volume",
                "analyst_rating": "Strong Buy (Top Pick)"
            }
        }
        enriched = portfolio_mgr.enrich_live_metrics(sample_portfolio, market_lookup)
        positions = enriched.get("positions", [])
        self.assertEqual(len(positions), 2)
        
        # Verify NVDA stock position
        nvda_pos = positions[0]
        self.assertEqual(nvda_pos["underlying"], "NVDA")
        self.assertEqual(nvda_pos["sector"], "Technology")
        self.assertEqual(nvda_pos["call_wall"], "$135.00")
        self.assertEqual(nvda_pos["put_wall"], "$120.00")
        self.assertEqual(nvda_pos["gamma_skew"], "Bullish Gamma")
        self.assertTrue(nvda_pos["breakout_last_high"])
        # Total calculated NAV = equity (13000 + 1400) + cash (20000) = 34400
        # NVDA weight = 13000 / 34400 = ~37.79%
        self.assertAlmostEqual(nvda_pos["weight_pct"], 37.8, places=1)
        self.assertAlmostEqual(nvda_pos["total_pnl_pct"], ((130.0 - 120.0) / 120.0) * 100, places=1)

        # Verify NVDA option position inherits underlying intelligence
        nvda_opt = positions[1]
        self.assertEqual(nvda_opt["underlying"], "NVDA")
        self.assertEqual(nvda_opt["sector"], "Technology")
        self.assertEqual(nvda_opt["call_wall"], "$135.00")
        self.assertTrue(nvda_opt["is_option"])
        print("[PASS] enrich_live_metrics test passed.")

    def test_html_generator_portfolio_parity(self):
        """Test HTML generator produces all portfolio tabs, filters, headers, and drawers."""
        macro_data = {
            "composite_regime": "Structural Bull (Aggressive)",
            "composite_multiplier": 1.0,
            "b_riley_state": "RISK_ON",
            "vix": {"value": 14.5, "chg": -0.5, "pct_chg": -3.3},
            "fed_funds": {"rate": "5.33%"},
            "tnx": {"value": 3.85, "chg": -0.02, "pct_chg": -0.5},
            "wti": {"value": 74.5, "chg": 0.5, "pct_chg": 0.7},
            "brent": {"value": 78.2, "chg": 0.4, "pct_chg": 0.5},
            "futures": {
                "es": {"value": 5600.0, "chg": 25.0, "pct_chg": 0.45},
                "nq": {"value": 19800.0, "chg": 128.0, "pct_chg": 0.65},
                "gold": {"value": 2510.0, "chg": 12.0, "pct_chg": 0.5},
                "btc": {"value": 64200.0, "chg": 1200.0, "pct_chg": 1.9}
            },
            "breadth": {"advancing_pct": 68.0, "declining_pct": 32.0, "nh_pct": 72.0, "nl_pct": 28.0, "pct_above_sma50": 65.0, "pct_above_sma200": 70.0},
            "portfolio_matrix": {"equity_allocation": 85, "gold_target": 5, "btc_target": 5, "cash_target": 5, "tech_cap": 35}
        }
        sample_portfolio = {
            "account_name": "Primary Trading",
            "account_number": "Z87654321",
            "total_nav": 250000.0,
            "cash_balance": 50000.0,
            "positions": [
                {
                    "symbol": "AAPL",
                    "underlying": "AAPL",
                    "description": "Apple Inc Common Stock",
                    "quantity": 200.0,
                    "average_cost": 210.0,
                    "last_price": 225.0,
                    "current_value": 45000.0,
                    "today_pnl_dollar": 1200.0,
                    "today_pnl_pct": 2.74,
                    "total_pnl_dollar": 3000.0,
                    "total_pnl_pct": 7.14,
                    "weight_pct": 18.0,
                    "strategy_tag": "Core Long Holding",
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "is_option": False,
                    "setup_score": 4.2,
                    "stars_visual": "★★★★☆",
                    "pct_change": 2.74,
                    "gap_pct": 1.2,
                    "pct_from_open": 1.54,
                    "vwap": "$223.50",
                    "vwap_dist": 0.67,
                    "sma20": "$218.00",
                    "sma50": "$212.00",
                    "sma200": "$195.00",
                    "call_wall": "$230.00",
                    "put_wall": "$215.00",
                    "gamma_flip": "$220.00",
                    "vol_oi_ratio": 2.1,
                    "atm_iv_str": "24.5%",
                    "gamma_skew": "Bullish Skew",
                    "pc_ratio": "0.62",
                    "analyst_rating": "Buy (Top Pick)",
                    "headline": "Apple Intelligence expanding globally",
                    "breakout_last_high": True,
                    "breakout_pm_high": False
                }
            ]
        }

        report_path = html_generator.generate_report(
            macro_data=macro_data,
            day_watchlist=[],
            economic_events=[],
            earnings_data={},
            analyst_actions=[],
            options_aggregated=[],
            portfolio_data=sample_portfolio
        )

        with open(report_path, "r", encoding="utf-8") as f:
            html = f.read()

        # 1. Check Portfolio View Mode tabs exist
        self.assertIn('id="btn-port-view-core"', html)
        self.assertIn('id="btn-port-view-technical"', html)
        self.assertIn('id="btn-port-view-options"', html)
        self.assertIn('switchPortfolioView(\'core\')', html)
        self.assertIn('switchPortfolioView(\'technical\')', html)
        self.assertIn('switchPortfolioView(\'options\')', html)

        # 2. Check Multi-Factor Filters & Break Up / Down Multi-Select exist
        self.assertIn('id="port-breakout-btn"', html)
        self.assertIn('id="port-chk-gt-week-high"', html)
        self.assertIn('id="port-chk-gt-day-high"', html)
        self.assertIn('id="port-chk-gt-pm-high"', html)
        self.assertIn('id="port-chk-lt-pm-low"', html)
        self.assertIn('id="port-chk-lt-week-low"', html)
        self.assertIn('id="port-chk-lt-day-low"', html)
        self.assertIn('id="port-filter-chg"', html)
        self.assertIn('id="port-filter-gap"', html)
        self.assertIn('id="port-filter-open"', html)
        self.assertIn('id="port-filter-vwap"', html)
        self.assertIn('id="port-filter-total-pct"', html)
        self.assertIn('id="port-filter-weight"', html)
        self.assertIn('id="port-filter-flow"', html)
        self.assertIn('id="port-filter-sma20"', html)
        self.assertIn('id="port-filter-sma50"', html)
        self.assertIn('id="port-filter-sma200"', html)
        self.assertIn('id="port-filter-catalyst"', html)
        self.assertIn('id="port-filter-rvol"', html)
        self.assertIn('id="port-filter-score"', html)
        self.assertIn('id="port-filter-sector"', html)
        self.assertIn('id="port-filter-asset-type"', html)
        self.assertIn('id="port-filter-strat"', html)

        # 2b. Check Watchlist Break Up / Down Multi-Select
        self.assertIn('id="day-breakout-btn"', html)
        self.assertIn('id="day-chk-gt-week-high"', html)
        self.assertIn('id="day-chk-gt-day-high"', html)
        self.assertIn('id="day-chk-gt-pm-high"', html)
        self.assertIn('id="day-chk-lt-pm-low"', html)
        self.assertIn('id="day-chk-lt-week-low"', html)
        self.assertIn('id="day-chk-lt-day-low"', html)

        # 3. Check Total% and Weight% filter bucket values
        self.assertIn('value="GT_3"', html)
        self.assertIn('value="LT_M3"', html)
        self.assertIn('value="LT_M20"', html)
        self.assertIn('value="M20_M10"', html)
        self.assertIn('value="M10_M5"', html)
        self.assertIn('value="M5_0"', html)
        self.assertIn('value="0_5"', html)
        self.assertIn('value="5_10"', html)
        self.assertIn('value="10_20"', html)
        self.assertIn('value="20_50"', html)
        self.assertIn('value="50_100"', html)
        self.assertIn('value="GT_100"', html)
        self.assertIn('value="GT_10"', html)
        self.assertIn('value="GT_5"', html)
        self.assertIn('value="GT_1"', html)
        self.assertIn('value="LT_1"', html)

        # 4. Check Table Headers and Visibility classes
        self.assertIn('col-all', html)
        self.assertIn('col-tech-core', html)
        self.assertIn('col-core-only', html)
        self.assertIn('col-tech-only', html)
        self.assertIn('col-opt-only', html)

        # 5. Check Portfolio row and 4-card matrix drawer
        self.assertIn('data-drawer-id="port-row-drawer-0"', html)
        self.assertIn('id="port-row-drawer-0"', html)
        self.assertIn('📈 Trend & Moving Average Matrix (AAPL)', html)
        self.assertIn('🎯 Institutional Options Gamma & Sizing', html)
        self.assertIn('📰 Catalyst & Analyst Intelligence', html)
        self.assertIn('💼 Portfolio Position & Risk Sizing', html)

        # 6. Check JavaScript Functions
        self.assertIn('function renderPortfolioDOM()', html)
        self.assertIn('function filterPortfolioWatchlist(', html)
        self.assertIn('function switchPortfolioView(', html)
        self.assertIn('function savePortfolioFilterPreferences()', html)
        self.assertIn('function loadPortfolioFilterPreferences()', html)
        self.assertIn('function resetPortfolioInstitutionalDefaults()', html)
        self.assertIn('function showAllPortfolioPositions()', html)

        print("[PASS] HTML generator portfolio parity test passed.")

if __name__ == "__main__":
    unittest.main()
