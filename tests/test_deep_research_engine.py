"""Automated Unit Test Suite for Institutional Deep Research Engine (Skill 04)."""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sources.deep_research_engine import deep_research_engine, DeepResearchEngine
from sources.thesis_lake import thesis_lake


class TestDeepResearchEngine(unittest.TestCase):
    """Test suite for 4-Master dialectics, forensics, reverse DCF, and persistence."""

    def setUp(self):
        self.engine = deep_research_engine

    def test_01_piotroski_f_score(self):
        """Verify Piotroski 9-point fundamental strength scoring."""
        # Clean compounder mock quarters
        quarters = [
            {
                "period": "2026-Q2",
                "net_income": 10e9,
                "ocf": 14e9,
                "total_assets": 50e9,
                "total_debt": 5e9,
                "current_ratio": 2.5,
                "shares_outstanding": 10e9,
                "revenue": 30e9,
                "gross_profit": 20e9,
            },
            {
                "period": "2026-Q1",
                "net_income": 9e9,
                "ocf": 12e9,
                "total_assets": 48e9,
                "total_debt": 5e9,
                "current_ratio": 2.4,
                "shares_outstanding": 10e9,
                "revenue": 28e9,
                "gross_profit": 18e9,
            },
            {"period": "2025-Q4"},
            {"period": "2025-Q3"},
            {
                "period": "2025-Q2",
                "net_income": 7e9,
                "ocf": 9e9,
                "total_assets": 45e9,
                "total_debt": 6e9,
                "current_ratio": 2.1,
                "shares_outstanding": 10.2e9,
                "revenue": 22e9,
                "gross_profit": 13e9,
            },
        ]
        res = self.engine.calculate_piotroski_f_score(quarters)
        self.assertGreaterEqual(res["score"], 8)
        self.assertIn("Elite Compounder", res["rating"])
        self.assertTrue(res["signals"]["cfo_greater_than_ni"])
        self.assertTrue(res["signals"]["increasing_roa"])

    def test_02_beneish_m_score_clean_vs_manipulator(self):
        """Verify Beneish M-score cleanly flags manipulation risk above -1.78."""
        # Case A: Normal clean company
        clean_quarters = [
            {
                "revenue": 10e9,
                "receivables": 1.2e9,
                "gross_profit": 5e9,
                "total_assets": 20e9,
                "depreciation": 800e6,
                "sga": 1.5e9,
                "total_debt": 2e9,
                "net_income": 2e9,
                "ocf": 2.5e9,
            },
            {
                "revenue": 9.5e9,
                "receivables": 1.1e9,
                "gross_profit": 4.7e9,
                "total_assets": 19e9,
                "depreciation": 780e6,
                "sga": 1.45e9,
                "total_debt": 2.1e9,
                "net_income": 1.8e9,
                "ocf": 2.2e9,
            },
        ]
        res_clean = self.engine.calculate_beneish_m_score(clean_quarters)
        self.assertFalse(res_clean["is_manipulator_risk"])
        self.assertLessEqual(res_clean["m_score"], -1.78)
        self.assertIn("Clean", res_clean["verdict"])

        # Case B: Aggressive accounting (Huge receivables spike, gross margin decay, massive accruals)
        dirty_quarters = [
            {
                "revenue": 15e9,
                "receivables": 6.0e9,  # DSRI spikes massively
                "gross_profit": 4.0e9, # Margin collapse
                "total_assets": 25e9,
                "depreciation": 200e6,
                "sga": 1.0e9,
                "total_debt": 10e9,
                "net_income": 5.0e9,
                "ocf": -2.0e9,          # Terrible cash flow vs net income -> large TATA
            },
            {
                "revenue": 10e9,
                "receivables": 1.2e9,
                "gross_profit": 6.0e9,
                "total_assets": 20e9,
                "depreciation": 800e6,
                "sga": 1.5e9,
                "total_debt": 2e9,
                "net_income": 2.0e9,
                "ocf": 2.5e9,
            },
        ]
        res_dirty = self.engine.calculate_beneish_m_score(dirty_quarters)
        self.assertTrue(res_dirty["is_manipulator_risk"])
        self.assertGreater(res_dirty["m_score"], -1.78)
        self.assertIn("Manipulation Risk Flagged", res_dirty["verdict"])

    def test_03_reverse_dcf_inversion(self):
        """Verify Reverse DCF solver determines implied annual FCF growth."""
        res = self.engine.calculate_reverse_dcf(
            current_market_cap=1000e9,
            ttm_fcf=40e9,
            discount_rate=0.09,
            terminal_exit_multiple=18.0
        )
        self.assertGreater(res["implied_terminal_growth_pct"], 0.0)
        self.assertGreater(res["bull_fair_value"], res["base_fair_value"])
        self.assertGreater(res["base_fair_value"], res["bear_fair_value"])

    def test_04_four_master_dialectic_and_sizing(self):
        """Verify 4-master consensus weighting and sizing multiplier."""
        quarters = [{
            "revenue": 50e9,
            "gross_profit": 35e9,  # 70% GM
            "net_income": 25e9,
            "ocf": 28e9,          # Sloan clean
            "fcf": 26e9,
            "total_assets": 80e9,
            "total_debt": 10e9,
            "cash": 30e9,
            "shares_outstanding": 24e9,
        }]
        profile = {"sector": "Technology", "company_name": "Test Tech"}
        synth = self.engine.synthesize_four_masters(
            ticker="TEST",
            quarters=quarters,
            market_cap=2000e9,
            current_price=100.0,
            profile=profile
        )
        self.assertGreaterEqual(synth["composite_stars"], 3.5)
        self.assertFalse(synth["hard_veto"])
        self.assertGreater(synth["sizing_multiplier"], 0.0)

    def test_05_munger_hard_veto_enforcement(self):
        """Verify Munger Hard Veto triggers on high Sloan accrual distortion (>8%)."""
        quarters = [{
            "revenue": 50e9,
            "gross_profit": 20e9,
            "net_income": 30e9,
            "ocf": 5e9,           # NI - OCF = 25B on 100B assets = 25% > 8%
            "fcf": 4e9,
            "total_assets": 100e9,
            "total_debt": 50e9,
            "cash": 5e9,
            "shares_outstanding": 10e9,
        }]
        profile = {"sector": "Industrials", "company_name": "Test Bad Accruals"}
        synth = self.engine.synthesize_four_masters(
            ticker="BAD",
            quarters=quarters,
            market_cap=500e9,
            current_price=50.0,
            profile=profile
        )
        self.assertTrue(synth["hard_veto"])
        self.assertEqual(synth["sizing_multiplier"], 0.0)
        self.assertIn("HARD VETO", synth["verdict"])

    def test_06_sample_audit_gate_pass_and_reject(self):
        """Verify 15% random sample audit passes matching data and rejects drifted data."""
        # 1. Matching data
        pass_data = {
            "market_cap": 100e9,
            "primary_market_cap": 100.5e9,  # 0.5% delta <= 5%
            "ttm_revenue": 20e9,
            "primary_revenue": 20.2e9,
            "ttm_net_income": 5e9,
            "primary_net_income": 5.0e9,
            "ttm_fcf": 4.5e9,
            "primary_fcf": 4.5e9,
            "sloan_accrual": 2.5,
            "primary_sloan": 2.5,
            "current_price": 50.0,
            "primary_price": 50.0,
        }
        res_pass = self.engine.audit_dossier_data(pass_data)
        self.assertTrue(res_pass["all_passed"])
        self.assertIn("【准出】", res_pass["verdict"])

        # 2. Corrupted data (huge drift)
        fail_data = {
            "market_cap": 100e9,
            "primary_market_cap": 150e9,  # 50% drift
            "ttm_revenue": 20e9,
            "primary_revenue": 40e9,    # 100% drift
            "ttm_net_income": 5e9,
            "primary_net_income": 10e9,
            "ttm_fcf": 4e9,
            "primary_fcf": 8e9,
            "sloan_accrual": 2.0,
            "primary_sloan": 8.0,
            "current_price": 50.0,
            "primary_price": 100.0,
        }
        res_fail = self.engine.audit_dossier_data(fail_data)
        self.assertFalse(res_fail["all_passed"])
        self.assertIn("【打回】", res_fail["verdict"])

    def test_07_duckdb_thesis_persistence_and_retrieval(self):
        """Verify deep research thesis persistence and retrieval in DuckDB."""
        test_thesis = {
            "symbol": "TSTDEEP",
            "composite_score": 85.0,
            "composite_stars": 4.3,
            "verdict": "🟢 HIGH-CONVICTION BUY",
            "sizing_multiplier": 1.0,
            "duan_stars": 4.5,
            "buffett_stars": 4.2,
            "munger_stars": 4.0,
            "lilu_stars": 4.5,
            "divergence_alert": False,
            "hard_veto_triggered": False,
            "sloan_accrual": 2.1,
            "fcf_conversion": 110.0,
            "piotroski_f_score": 8,
            "beneish_m_score": -2.55,
            "implied_terminal_growth": 14.5,
            "fair_value_base": 120.0,
            "entry_target_price": 102.0,
            "invalidation_stop_price": 83.5,
            "dossier_path": "reports/deep_research/TSTDEEP_dossier_test.md",
        }
        success = thesis_lake.record_deep_research_thesis(test_thesis)
        self.assertTrue(success)

        retrieved = thesis_lake.get_deep_research_thesis("TSTDEEP")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["symbol"], "TSTDEEP")
        self.assertEqual(retrieved["composite_stars"], 4.3)
        self.assertEqual(retrieved["piotroski_f_score"], 8)
        self.assertEqual(retrieved["sizing_multiplier"], 1.0)


if __name__ == "__main__":
    unittest.main()
