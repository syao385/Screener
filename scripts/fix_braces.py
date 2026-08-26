import re

with open("reporter/html_generator.py", "r", encoding="utf-8") as f:
    code = f.read()

# Check HTML_TEMPLATE
template_match = re.search(r'HTML_TEMPLATE\s*=\s*"""(.*?)"""\s*class HTMLReportGenerator', code, re.DOTALL)
if not template_match:
    print("Could not find HTML_TEMPLATE")
    exit(1)

template_str = template_match.group(1)

# Valid keys
valid_keys = [
    "session_label", "timestamp_est", "timestamp_pst", "today_str", "yest_str", "tom_str",
    "regime_css_class", "composite_regime", "composite_multiplier",
    "pillar_liq_val", "pillar_liq_status", "pillar_liq_color", "pillar_liq_width",
    "pillar_gro_val", "pillar_gro_status", "pillar_gro_color", "pillar_gro_width",
    "pillar_vol_val", "pillar_vol_status", "pillar_vol_color", "pillar_vol_width",
    "pillar_bre_val", "pillar_bre_status", "pillar_bre_color", "pillar_bre_width",
    "fed_funds_val", "fed_funds_source", "rate_cycle_signal", "rate_implication",
    "tnx_val", "tnx_chg", "tnx_pct", "tnx_color", "curve_status", "spread_2s10s",
    "tnx_source", "tnx_time", "vix_val", "vix_chg", "vix_color", "vix_state",
    "vix_source", "vix_time", "wti_val", "brent_val", "wti_chg", "oil_color",
    "oil_signal", "wti_source", "wti_time", "es_val", "es_chg", "es_pct", "es_color",
    "nq_val", "nq_chg", "nq_pct", "nq_color", "gold_val", "gold_chg", "gold_pct",
    "gold_color", "btc_val", "btc_chg", "btc_pct", "btc_color", "adv_pct", "decl_pct",
    "adv_count", "decl_count", "adv_color", "nh_pct", "nl_pct", "net_highs_str",
    "nh_count", "nl_count", "nh_color", "breadth_source", "sma50_pct", "sma50_color",
    "sma50_status", "sma200_pct", "sma200_color", "sma200_status", "matrix_equity",
    "matrix_gold", "matrix_btc", "matrix_cash", "matrix_tech", "matrix_fin",
    "matrix_energy", "matrix_def", "matrix_multiplier", "portfolio_acc_name",
    "portfolio_acc_num", "portfolio_nav_str", "portfolio_nav_raw", "portfolio_cash_str",
    "portfolio_cash_weight", "portfolio_equity_str", "portfolio_pos_count",
    "portfolio_day_pnl_str", "portfolio_day_pct_str", "portfolio_tot_pnl_str",
    "port_day_color", "port_tot_color", "portfolio_position_rows", "portfolio_json_raw",
    "sector_options", "day_count", "eco_count", "earn_count", "analyst_count",
    "options_agg_count", "day_trading_rows", "economic_calendar_rows",
    "earnings_calendar_rows", "analyst_rows", "options_aggregated_rows"
]

# Find placeholders in template_str
placeholders = re.findall(r'\{([^{}]+)\}', template_str)
bad_keys = []
for p in placeholders:
    # check format specifiers like {tnx_val:.2f}
    k = p.split(':')[0].strip()
    if k not in valid_keys:
        bad_keys.append(p)

print(f"Found {len(bad_keys)} single-brace tokens that are not valid keys: {bad_keys[:20]}")
