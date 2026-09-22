"""Automated Test Suite for Financial Rigor & Multi-Source Cross-Validation Engine."""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sources.financial_rigor import financial_rigor, FinancialRigorEngine, to_decimal
from sources.defeatbeta_client import fundamental_engine
from sources.earnings_intelligence import earnings_intel


class TestFinancialRigorEngine(unittest.TestCase):
    """Test suite for exact financial calculations and multi-tier reconciliation."""

    def test_01_sloan_accrual_calculation(self):
        """Verify Richard Sloan accrual anomaly calculation."""
        # Case A: High quality cash earnings (OCF > NI)
        ratio, quality = financial_rigor.calculate_sloan_accrual(
            net_income=500e6, ocf=800e6, total_assets=10e9
        )
        self.assertAlmostEqual(ratio, -3.0, places=2)
        self.assertIn("Clean Cash-Backed", quality)

        # Case B: High accrual distortion (NI >> OCF)
        ratio_b, quality_b = financial_rigor.calculate_sloan_accrual(
            net_income=1.2e9, ocf=200e6, total_assets=10e9
        )
        self.assertAlmostEqual(ratio_b, 10.0, places=2)
        self.assertIn("High Accrual Distortion", quality_b)

    def test_02_fcf_conversion(self):
        """Verify FCF conversion rate calculation."""
        conv, verdict = financial_rigor.calculate_fcf_conversion(fcf=900e6, net_income=1e9)
        self.assertEqual(conv, 90.0)
        self.assertIn("Strong Conversion", verdict)

        conv_super, verdict_super = financial_rigor.calculate_fcf_conversion(fcf=1.5e9, net_income=1e9)
        self.assertEqual(conv_super, 150.0)
        self.assertIn(">100% Cash-Backed", verdict_super)

    def test_03_cross_source_discrepancy_audit(self):
        """Verify cross-source deviation tolerance checking."""
        # 1. Close alignment (within 2%)
        res1 = financial_rigor.audit_cross_source_discrepancy("Revenue", 100.0, 101.5)
        self.assertEqual(res1["status"], "✅ VERIFIED_HIGH_CONFIDENCE")

        # 2. Moderate deviation (between 2% and 5%)
        res2 = financial_rigor.audit_cross_source_discrepancy("Revenue", 100.0, 104.0)
        self.assertEqual(res2["status"], "⚠️ ACCEPTABLE_DELTA")

        # 3. High discrepancy (> 5%) -> Primary SEC precedence rule
        res3 = financial_rigor.audit_cross_source_discrepancy("Revenue", 100.0, 125.0)
        self.assertEqual(res3["status"], "❌ DISCREPANCY_FLAGGED")
        self.assertEqual(res3["chosen_value"], 100.0)

    def test_04_nvda_primary_sec_reconciliation(self):
        """Verify NVDA's true SEC 10-Q filing profile and cash flow metrics."""
        prof = fundamental_engine.get_historical_profile("NVDA", fetch_remote=True)
        self.assertTrue(len(prof.get("quarters", [])) > 0)
        q0 = prof["quarters"][0]
        self.assertGreater(q0["revenue"], 70e9)
        self.assertGreater(q0["ocf"], 20e9)

        flash = earnings_intel.analyze_flash_earnings("NVDA", fetch_remote=True)
        self.assertIn("STRENGTHENED", flash.get("thesis_label", ""))
        self.assertEqual(flash.get("factors", {}).get("classification"), "TRIPLE_BULL_BEAT")

    def test_05_smtc_live_quarter_synchronization(self):
        """Verify SMTC's newly reported Q2 quarter synchronization."""
        prof = fundamental_engine.get_historical_profile("SMTC", fetch_remote=True)
        self.assertTrue(len(prof.get("quarters", [])) > 0)
        q0 = prof["quarters"][0]
        # Should be ~$341.9M matching TradingView/SEC release
        self.assertAlmostEqual(q0["revenue"] / 1e6, 341.9, delta=5.0)
        self.assertTrue(abs(q0["eps"] - 1.59) < 0.1 or abs(q0["eps"] - 0.71) < 0.1)


if __name__ == "__main__":
    unittest.main()
