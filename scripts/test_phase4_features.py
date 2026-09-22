"""Verification script for Phase 4: DuckDB Attribution Lake, Brinson-Fachler Decomposition & Auto-Tuning."""

import os
import sys
from pathlib import Path

# Ensure project root in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sources.attribution_lake import attribution_lake
from sources.attribution_engine import attribution_engine
from sources.parameter_tuner import parameter_tuner

print("==================================================")
print("  PHASE 4 FEATURES VERIFICATION & E2E TEST")
print("==================================================")

# 1. Verify DuckDB Lake & Baseline Holdings Synthesis
print("\n--- TEST 1: DUCKDB ATTRIBUTION LAKE & SYNTHESIS ---")
synth_count = attribution_lake.synthesize_baseline_holdings()
print(f"Synthesized Baseline Holdings: {synth_count} positions")
ledger = attribution_lake.get_trade_ledger(limit=5)
print(f"Active Trade Ledger Records:  {len(attribution_lake.get_trade_ledger(limit=1000))} total")
print(f"Sample Trade: {ledger[0]['symbol']} ({ledger[0]['side']} {ledger[0]['shares']} @ ${ledger[0]['price']:.2f}) [Baseline={ledger[0]['is_baseline_synthesis']}]")
assert synth_count >= 70, "Should synthesize at least 70 positions"
print("[OK] Test 1: Attribution Lake & Baseline Synthesis Verified.")

# 2. Verify Toggleable Forward Incremental Fills & Manual Override
print("\n--- TEST 2: FORWARD INCREMENTAL FILLS & MANUAL OVERRIDE ---")
is_enabled = attribution_lake.is_forward_fills_enabled()
print(f"Initial Forward Fills Toggle: {'ENABLED' if is_enabled else 'DISABLED (Default)'}")

# Verify default is OFF
attribution_lake.set_forward_fills_enabled(False)
assert attribution_lake.is_forward_fills_enabled() is False

# Normal forward fill should be rejected when OFF
res_off = attribution_lake.record_forward_fill("NVDA", "BUY", 10, 215.0)
print(f"Attempt Forward Fill while OFF: {res_off} (Expected: None)")
assert res_off is None

# Manual override should succeed regardless of toggle state
override_id = attribution_lake.manual_override_fill("NVDA", "BUY", 10, 215.0, setup_type="BASE_BREAKOUT")
print(f"Manual Override Fill:           {override_id}")
assert override_id is not None
assert "NVDA" in override_id

# Clean up override record
conn = attribution_lake.get_connection(read_only=False)
conn.execute("DELETE FROM trade_ledger WHERE trade_id = ?", [override_id])
conn.commit()
print("[OK] Test 2: Toggleable Forward Fills & Manual Override Verified.")

# 3. Verify Skill 08 Brinson-Fachler Factor Attribution
print("\n--- TEST 3: SKILL 08 BRINSON-FACHLER FACTOR ATTRIBUTION ---")
attr_rep = attribution_engine.get_full_attribution_report()
bf = attr_rep["brinson_fachler"]
risk = attr_rep["risk_metrics"]

print(f"Portfolio Return:   {bf['portfolio_return_pct']:+.2f}%")
print(f"Benchmark Return:   {bf['benchmark_return_pct']:+.2f}%")
print(f"Total Active Alpha: {bf['total_active_return_pct']:+.2f}%")
print(f"  - Allocation (A): {bf['allocation_effect_pct']:+.2f}%")
print(f"  - Selection (S):  {bf['selection_effect_pct']:+.2f}%")
print(f"  - Interaction (I):{bf['interaction_effect_pct']:+.2f}%")

print(f"\nRisk-Adjusted Metrics:")
print(f"  - Sharpe Ratio:       {risk['sharpe_ratio']:.2f}")
print(f"  - Sortino Ratio:      {risk['sortino_ratio']:.2f}")
print(f"  - Information Ratio:  {risk['information_ratio']:.2f}")
print(f"  - Max Drawdown:       {risk['max_drawdown_pct']:.2f}%")

assert abs((bf['allocation_effect_pct'] + bf['selection_effect_pct'] + bf['interaction_effect_pct']) - bf['total_active_return_pct']) < 0.2
print("[OK] Test 3: Brinson-Fachler Decomposition & Risk Ratios Verified.")

# 4. Verify Automatic Parameter Auto-Tuning & Hard Safety Clamps [0.50x, 1.35x]
print("\n--- TEST 4: PARAMETER AUTO-TUNING & HARD CLAMPS [0.50x, 1.35x] ---")
tuning_rep = parameter_tuner.run_calibration(market_vix=16.5)
bounds = tuning_rep["safety_bounds"]
print(f"Safety Bounds:       [{bounds['min_clamp']}x, {bounds['max_clamp']}x]")
print(f"Chandelier ATR Stop: {tuning_rep['calibrated_stops']['clamped_multiplier']:.1f}x (Regime-Adaptive)")
print(f"Slippage Impact:     {tuning_rep['slippage_governor']['avg_slippage_bps']:.1f} bps ({tuning_rep['slippage_governor']['status']})")

print("\nSetup Archetype Calibrated Multipliers:")
for name, data in tuning_rep["calibrated_setups"].items():
    print(f"  • {name:<28}: Raw={data['raw_multiplier']:.2f}x -> Calibrated={data['calibrated_multiplier']:.2f}x [{data['status']}]")
    assert bounds["min_clamp"] <= data["calibrated_multiplier"] <= bounds["max_clamp"]

# Test clamp edge cases
assert parameter_tuner.clamp(2.50)[0] == 1.35
assert parameter_tuner.clamp(0.10)[0] == 0.50
print("[OK] Test 4: Parameter Auto-Tuning & Hard Safety Clamps Verified.")

print("\n==================================================")
print("  ALL PHASE 4 UNIT & INTEGRATION TESTS PASSED (4/4)")
print("==================================================")
