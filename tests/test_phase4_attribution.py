"""Unit test suite for Phase 4: Attribution Lake, Brinson-Fachler Factor Attribution & Auto-Tuning."""

import unittest
import math
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import DATA_DIR, TUNING_MIN_CLAMP, TUNING_MAX_CLAMP
from sources.attribution_lake import attribution_lake
from sources.attribution_engine import attribution_engine, BENCHMARK_SECTOR_WEIGHTS
from sources.parameter_tuner import parameter_tuner


class TestPhase4AttributionAndTuning(unittest.TestCase):
    """Test suite for Phase 4 analytical modules."""

    def test_01_attribution_lake_schema_and_baseline_synthesis(self):
        """Test DuckDB schema creation and baseline synthesis from portfolio holdings."""
        count = attribution_lake.synthesize_baseline_holdings()
        self.assertGreaterEqual(count, 70, "Expected at least 70 baseline holdings synthesized.")
        
        ledger = attribution_lake.get_trade_ledger(limit=10)
        self.assertGreater(len(ledger), 0, "Trade ledger should return entries.")
        self.assertTrue(ledger[0]["is_baseline_synthesis"], "Baseline trades should have is_baseline_synthesis=True.")

    def test_02_forward_fills_toggle_and_manual_override(self):
        """Test forward incremental fills default to OFF, toggleable, and support manual override."""
        # 1. Verify default or current state
        initial_state = attribution_lake.is_forward_fills_enabled()
        
        # Test toggling OFF
        attribution_lake.set_forward_fills_enabled(False)
        self.assertFalse(attribution_lake.is_forward_fills_enabled())

        # When OFF, normal forward fill is skipped
        skip_fill = attribution_lake.record_forward_fill("AUTO_TEST", "BUY", 10, 100.0, manual_override=False)
        self.assertIsNone(skip_fill, "Should skip forward fill when disabled.")

        # Manual override proceeds even when OFF
        override_fill = attribution_lake.manual_override_fill("OVR_TEST", "BUY", 15, 120.0)
        self.assertIsNotNone(override_fill, "Manual override should log trade even when forward fills are disabled.")
        self.assertTrue(override_fill.startswith("FILL_OVR_TEST"))

        # Clean up test trade
        conn = attribution_lake.get_connection(read_only=False)
        conn.execute("DELETE FROM trade_ledger WHERE symbol = 'OVR_TEST'")
        conn.commit()

        # Restore initial state
        attribution_lake.set_forward_fills_enabled(initial_state)

    def test_03_brinson_fachler_mathematical_identity(self):
        """Test that Brinson-Fachler active return matches Allocation + Selection + Interaction."""
        bf = attribution_engine.calculate_brinson_fachler_attribution()
        
        alloc = bf["allocation_effect_pct"]
        select = bf["selection_effect_pct"]
        inter = bf["interaction_effect_pct"]
        total_active = bf["total_active_return_pct"]

        sum_components = round(alloc + select + inter, 2)
        self.assertAlmostEqual(
            sum_components,
            total_active,
            places=1,
            msg=f"Brinson-Fachler identity failed: {sum_components} != {total_active}"
        )
        self.assertEqual(len(bf["sector_breakdown"]), len(BENCHMARK_SECTOR_WEIGHTS))

    def test_04_risk_adjusted_metrics(self):
        """Test Sharpe, Sortino, Information Ratio, and Max Drawdown calculations."""
        metrics = attribution_engine.calculate_risk_adjusted_metrics()
        
        self.assertIn("sharpe_ratio", metrics)
        self.assertIn("sortino_ratio", metrics)
        self.assertIn("information_ratio", metrics)
        self.assertIn("max_drawdown_pct", metrics)
        self.assertIn("calmar_ratio", metrics)

        # Sharpe should be positive in a profitable portfolio
        self.assertGreater(metrics["sharpe_ratio"], 0.0)
        self.assertGreater(metrics["sortino_ratio"], 0.0)
        self.assertGreaterEqual(metrics["max_drawdown_pct"], 0.0)

    def test_05_parameter_tuner_hard_clamps(self):
        """Test automatic bounded tuning strictly enforces [0.50x, 1.35x] safety clamps."""
        # Test low clamp
        val_low, status_low = parameter_tuner.clamp(0.20)
        self.assertEqual(val_low, TUNING_MIN_CLAMP)
        self.assertEqual(status_low, "CLAMPED_LOWER")

        # Test high clamp
        val_high, status_high = parameter_tuner.clamp(1.85)
        self.assertEqual(val_high, TUNING_MAX_CLAMP)
        self.assertEqual(status_high, "CLAMPED_UPPER")

        # Test within bounds
        val_norm, status_norm = parameter_tuner.clamp(1.15)
        self.assertEqual(val_norm, 1.15)
        self.assertEqual(status_norm, "OPTIMAL_BOUNDED")

    def test_06_calibration_run_and_archetype_multipliers(self):
        """Test full parameter calibration run across all 9 Master Setups."""
        tuning_rep = parameter_tuner.run_calibration(market_vix=16.5)
        
        setups = tuning_rep["calibrated_setups"]
        self.assertEqual(len(setups), 9, "Should calibrate all 9 Master Setup Archetypes.")

        for name, data in setups.items():
            mult = data["calibrated_multiplier"]
            self.assertGreaterEqual(mult, TUNING_MIN_CLAMP, f"{name} below min clamp")
            self.assertLessEqual(mult, TUNING_MAX_CLAMP, f"{name} above max clamp")

        # Stop loss calibration check
        stops = tuning_rep["calibrated_stops"]
        self.assertEqual(stops["clamped_multiplier"], 2.0)  # VIX 16.5 -> 2.0x ATR


if __name__ == "__main__":
    unittest.main()
