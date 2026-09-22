"""Unit tests for Phase 5 Stress Testing and Tail-Risk Engine."""

import unittest
from sources.stress_testing_engine import stress_testing_engine, SECTOR_CRISIS_SHOCKS

class TestPhase5StressTesting(unittest.TestCase):

    def setUp(self):
        self.portfolio_data = {
            "account_name": "Traditional IRA",
            "account_number": "264695485",
            "total_nav": 336870.83,
            "cash_balance": 113406.87,
            "equity_value": 223463.96,
            "positions": [
                {"symbol": "NVDA", "quantity": 100, "last_price": 210.0, "current_value": 21000.0, "sector": "Technology"},
                {"symbol": "AAPL", "quantity": 120, "last_price": 240.0, "current_value": 28800.0, "sector": "Technology"},
                {"symbol": "XOM", "quantity": 150, "last_price": 120.0, "current_value": 18000.0, "sector": "Energy"},
                {"symbol": "JNJ", "quantity": 100, "last_price": 160.0, "current_value": 16000.0, "sector": "Healthcare"},
            ]
        }

    def test_parametric_and_historical_var(self):
        metrics = stress_testing_engine.compute_portfolio_risk_metrics(self.portfolio_data, vix_level=17.5)
        self.assertIn("var_95_1d_dollar", metrics)
        self.assertIn("var_99_1d_dollar", metrics)
        self.assertIn("cvar_95_1d_dollar", metrics)
        self.assertIn("cvar_99_1d_dollar", metrics)
        self.assertGreater(metrics["var_95_1d_dollar"], 0.0)
        self.assertGreater(metrics["cvar_95_1d_dollar"], metrics["var_95_1d_dollar"])
        self.assertGreater(metrics["var_99_1d_dollar"], metrics["var_95_1d_dollar"])

    def test_monte_carlo_forward_simulation(self):
        mc = stress_testing_engine.run_monte_carlo_simulation(self.portfolio_data, num_paths=500)
        self.assertEqual(mc["num_paths"], 500)
        self.assertIn("30D", mc["horizon_stats"])
        self.assertIn("60D", mc["horizon_stats"])
        self.assertIn("90D", mc["horizon_stats"])
        s30 = mc["horizon_stats"]["30D"]
        self.assertGreater(s30["p95_best_case"], s30["p5_worst_case"])
        self.assertGreater(s30["expected_median_nav"], 0.0)

    def test_historical_crisis_replays(self):
        replays = stress_testing_engine.replay_crisis_scenarios(self.portfolio_data)
        self.assertEqual(len(replays), len(SECTOR_CRISIS_SHOCKS))
        for r in replays:
            self.assertIn("portfolio_shock_pct", r)
            self.assertIn("projected_loss_dollar", r)
            self.assertIn("projected_nav", r)
            self.assertLessEqual(r["projected_nav"], self.portfolio_data["total_nav"])

if __name__ == "__main__":
    unittest.main()
