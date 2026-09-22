"""Unit and integration tests for Macro Regime Assessment v3.0 per 01_macro-regime-new.md."""

import unittest
from sources.macro_regime import macro_assessor


class TestMacroRegimeV3(unittest.TestCase):

    def setUp(self):
        self.macro_data = macro_assessor.assess_macro_regime(force_refresh=True)

    def test_top_and_bottom_scores_bounds(self):
        """Verify Top and Bottom detection scores are strictly within [0, 100]."""
        top_score = self.macro_data.get("top_score")
        bot_score = self.macro_data.get("bottom_score")
        self.assertIsNotNone(top_score)
        self.assertIsNotNone(bot_score)
        self.assertGreaterEqual(top_score, 0.0)
        self.assertLessEqual(top_score, 100.0)
        self.assertGreaterEqual(bot_score, 0.0)
        self.assertLessEqual(bot_score, 100.0)

        turning_points = self.macro_data.get("turning_points", {})
        self.assertIn("verdict", turning_points)
        self.assertIn("confidence", turning_points)
        self.assertIn("action", turning_points)
        self.assertIn("sub_scores", turning_points)
        self.assertIn("top", turning_points["sub_scores"])
        self.assertIn("bottom", turning_points["sub_scores"])

    def test_market_internals_composite_bounds(self):
        """Verify Market Internals composite score is strictly within [1.0, 5.0]."""
        breadth = self.macro_data.get("breadth", {})
        internals_score = breadth.get("composite_internals_score")
        self.assertIsNotNone(internals_score)
        self.assertGreaterEqual(internals_score, 1.0)
        self.assertLessEqual(internals_score, 5.0)

        self.assertIn("tick_close", breadth)
        self.assertIn("add_net", breadth)
        self.assertIn("vold_ratio", breadth)

    def test_bayesian_scenarios_sum(self):
        """Verify 4-Quadrant Bayesian Scenario probabilities sum to 100% (+/- 0.5% tolerance for rounding)."""
        scenarios = self.macro_data.get("scenarios", {})
        self.assertIsNotNone(scenarios)

        p_gold = scenarios.get("goldilocks_pct", 0.0)
        p_refl = scenarios.get("reflation_pct", 0.0)
        p_stag = scenarios.get("stagflation_pct", 0.0)
        p_defl = scenarios.get("deflation_pct", 0.0)
        p_fail = scenarios.get("regime_failure_pct", 0.0)

        total_prob = p_gold + p_refl + p_stag + p_defl + p_fail
        self.assertAlmostEqual(total_prob, 100.0, delta=0.5)
        self.assertIn("dominant_scenario", scenarios)

    def test_debasement_and_separation_model(self):
        """Verify Debasement Hedges, BTC/Gold ratio, and MVRV Z-Score metrics."""
        debasement = self.macro_data.get("debasement", {})
        self.assertIsNotNone(debasement)
        self.assertIn("btc_gold_ratio", debasement)
        self.assertIn("crypto_fng_value", debasement)
        self.assertIn("crypto_fng_class", debasement)
        self.assertIn("mvrv_z_score", debasement)
        self.assertIn("cycle_phase", debasement)
        self.assertIn("separation_warning", debasement)

    def test_gatekeeper_quality_audit(self):
        """Verify Section 0.5 Data Completeness Gatekeeper."""
        gk = self.macro_data.get("gatekeeper", {})
        self.assertIsNotNone(gk)
        self.assertIn(gk.get("grade"), ["A", "B", "C"])
        self.assertIn(gk.get("status"), ["PASS", "WARNING", "RESTRICTED"])
        self.assertIn("action", gk)
        self.assertIn("valid_count", gk)

    def test_section8_markdown_dossier_generation(self):
        """Verify that generate_section8_markdown outputs all 9 required sections."""
        md = macro_assessor.generate_section8_markdown(self.macro_data)
        self.assertIsInstance(md, str)
        self.assertIn("## 1. Core Macro Summary", md)
        self.assertIn("## 2. Market Internals", md)
        self.assertIn("## 3. Debasement Hedge", md)
        self.assertIn("## 4. Top/Bottom Detection", md)
        self.assertIn("## 5. Scenario Probabilities", md)
        self.assertIn("## 6. Portfolio Implication Matrix", md)
        self.assertIn("## 7. Key Alerts", md)
        self.assertIn("## 8. Verdict & Action", md)
        self.assertIn("## 9. Data Quality & Gatekeeper Status", md)


if __name__ == "__main__":
    unittest.main()
