import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sources.portfolio_manager import portfolio_mgr

p = portfolio_mgr.enrich_live_metrics()
print("=== LIVE PORTFOLIO ENRICHMENT TEST ===")
print(f"Total NAV: ${p.get('total_nav'):,.2f}")
print(f"Equity Value: ${p.get('equity_value'):,.2f}")
print(f"Cash Balance (SPAXX): ${p.get('cash_balance'):,.2f} ({p.get('cash_weight_pct')}%)")
print(f"Today P&L: ${p.get('total_day_pnl_dollar'):+,.2f} ({p.get('total_day_pnl_pct'):+.2f}% Account | {p.get('equity_day_pnl_pct'):+.2f}% Equity)")
print(f"Unrealized Total: ${p.get('total_unrealized_pnl_dollar'):+,.2f} ({p.get('total_unrealized_pnl_pct'):+.2f}%)")

print("\n--- FIRST 10 POSITIONS (LIVE PRICES & PNL) ---")
for x in p.get('positions', [])[:10]:
    print(f"  {x['symbol']:<6} | Qty: {x['quantity']:>7.2f} | Live Price: ${x['last_price']:>8.2f} | Cur Value: ${x['current_value']:>10.2f} | Day PnL: ${x['today_pnl_dollar']:>+9.2f} ({x['today_pnl_pct']:>+6.2f}%) | Tot PnL: ${x['total_pnl_dollar']:>+9.2f} ({x['total_pnl_pct']:>+6.2f}%)")
