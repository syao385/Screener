import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sources.sector_flow_engine import sector_flow_engine

res = sector_flow_engine.get_sector_flow_matrix(force_refresh=True)
print("=== SECTOR FLOW ENGINE TEST ===")
print("Timestamp:", res.get("timestamp_str"))
spy = res.get("benchmark_spy", {})
print(f"SPY 1W: {spy.get('perf_1w')}% | 1M: {spy.get('perf_1m')}%")
print("\n--- 11 GICS SECTOR RANKINGS ---")
for s in res.get("sectors", []):
    print(f"{s['ticker']:<5} | {s['sector_name']:<22} | Price: ${s['price']:<7.2f} | 1W: {s['perf_1w']:>+6.2f}% | 1M: {s['perf_1m']:>+6.2f}% | RS 1W: {s['rs_1w']:>+5.2f}% | Flow Score: {s['flow_score']:>4.1f} | {s['badge']}")

print("\nTop Inflows:", res.get("top_inflows"))
print("Top Outflows:", res.get("top_outflows"))

print("\n--- SUB-INDUSTRY DRILLDOWN ---")
for parent_sec, subs in res.get("sub_industries", {}).items():
    print(f"Parent Sector: {parent_sec}")
    for sub in subs:
        print(f"  {sub['ticker']:<5} ({sub['sub_industry_name']:<30}) | Price: ${sub['price']:<7.2f} | 1W: {sub['perf_1w']:>+6.2f}% | Flow Score: {sub['flow_score']:>4.1f}")

# Test stock matching helper
print("\n--- STOCK MATCHING TEST ---")
for test_stock in [("NVDA", "Information Technology", "Semiconductors"), ("JPM", "Financials", "Major Banks"), ("XOM", "Energy", "Oil & Gas")]:
    is_hot, rationale, mult = sector_flow_engine.is_stock_in_hot_sector(test_stock[1], test_stock[2], res)
    print(f"{test_stock[0]} ({test_stock[1]}): Hot={is_hot} | Mult={mult}x | Rationale={rationale}")
