import sys, os
sys.path.insert(0, os.path.abspath("."))
from sources.portfolio_manager import portfolio_mgr

csv_path = r"C:\Users\jfan\.gemini\antigravity\brain\a0b05868-9505-4d97-8c5e-24cedd38800d\.user_uploaded\media_1787589598541.csv"
res = portfolio_mgr.parse_fidelity_csv(csv_path, save_to_disk=True)
print(f"Successfully re-imported {len(res['positions'])} positions into data/portfolio.json!")
print(f"Total NAV: ${res['total_nav']:,.2f}")
print(f"Cash Balance (SPAXX): ${res['cash_balance']:,.2f}")
print(f"Equity Value: ${res['equity_value']:,.2f}")
