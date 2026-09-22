"""Test script for Phase 2 Portfolio Optimizer & Stop Loss Manager."""

import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sources.portfolio_optimizer import portfolio_optimizer
from sources.stop_loss_manager import stop_loss_manager

print("==================================================")
print("  PHASE 2 ENGINES VERIFICATION & UNIT TEST")
print("==================================================")

# 1. Test Order Plan Calculation (New Screener Setup)
print("\n--- TEST 1: 3-WAY MINIMUM POSITION SIZING (NVDA) ---")
order_plan = portfolio_optimizer.calculate_order_plan(
    ticker="NVDA",
    entry_price=219.62,
    stop_price=210.00,
    setup_type="BASE_BREAKOUT",
    setup_quality_mult=1.0,
    stock_sector="Information Technology",
    stock_industry="Semiconductors",
)

print(f"Ticker: {order_plan['ticker']} | Entry: ${order_plan['entry_price']} | Stop: ${order_plan['stop_price']} ({order_plan['stop_distance_pct']}%)")
print(f"Conviction Tier: {order_plan['tier_name']} (Cap: {order_plan['tier_cap_pct']}%)")
print(f"Portfolio NAV: ${order_plan['portfolio_nav']:,.2f} | Unencumbered Cash: ${order_plan['unencumbered_cash']:,.2f}")
print(f"Shares Risk: {order_plan['shares_risk_calculated']} | Shares Tier Cap: {order_plan['shares_tier_cap_allowed']} | Shares Cash: {order_plan['shares_cash_available']}")
print(f"FINAL ALLOCATED SHARES: {order_plan['final_shares']} shares (${order_plan['order_dollar_value']:,.2f})")
print(f"Binding Constraint: {order_plan['binding_constraint']}")
print(f"Risk $ Committed: ${order_plan['actual_dollar_risk']:,.2f} ({order_plan['actual_risk_pct_of_nav']}% of NAV)")
print(f"Target 1 (+1.0R Breakeven Lock): ${order_plan['target_1_breakeven_lock']}")
print(f"Target 2 (+2.5R Profit Trim): ${order_plan['target_2_profit_trim']}")

# 2. Test Portfolio Allocation Audit
print("\n--- TEST 2: PORTFOLIO ALLOCATION AUDIT ---")
audit = portfolio_optimizer.audit_portfolio_allocations()
print(f"Tier 1 Aggregate: {audit['tier_1_weight_pct']}% (Cap: {audit['tier_1_cap_pct']}%)")
print(f"Tier 2 Aggregate: {audit['tier_2_weight_pct']}% (Cap: {audit['tier_2_cap_pct']}%)")
print(f"Tier 3 Aggregate: {audit['tier_3_weight_pct']}%")
print(f"Overweight Positions: {len(audit['overweight_positions'])}")
for o in audit['overweight_positions']:
    print(f"  🚨 {o['symbol']}: Weight {o['weight_pct']}% > Cap {o['tier_cap_pct']}% | Trim {o['recommended_trim_shares']} shares (${o['excess_dollars']:,.2f})")

# 3. Test Adaptive Stop Loss Manager
print("\n--- TEST 3: MULTI-TIER ADAPTIVE STOP LOSS AUDIT ---")
stop_audits = stop_loss_manager.audit_all_portfolio_stops()
print(f"Audited {len(stop_audits)} positions:")
for s in stop_audits[:8]:
    print(f"  {s['symbol']:<6} | Cur: ${s['current_price']:>7.2f} | Stop: ${s['active_stop_price']:>7.2f} ({s['stop_distance_pct']:>+5.1f}%) | {s['risk_status']} | {s['action_plan']}")
