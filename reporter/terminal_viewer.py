"""Terminal Console Viewer: ASCII-safe Rich Dashboard renderer for the CLI."""

import datetime
from typing import Dict, List, Any, Optional
from tabulate import tabulate
from config import TZ_EST, TZ_PST

class TerminalViewer:
    """Renders formatted ASCII-safe tables for Windows command prompt / PowerShell."""

    def render_dashboard(
        self,
        macro_data: Dict[str, Any],
        day_watchlist: List[Dict[str, Any]],
        economic_events: List[Dict[str, Any]],
        earnings_data: Dict[str, Any],
        analyst_actions: List[Dict[str, Any]],
        options_aggregated: List[Dict[str, Any]],
        session_label: str = "Real-Time Market Session",
    ):
        now_est = datetime.datetime.now(TZ_EST)
        now_pst = datetime.datetime.now(TZ_PST)

        print("\n" + "="*95)
        print(f"  INSTITUTIONAL REAL-TIME INTELLIGENCE SCREENER [{session_label}]  ")
        print(f"  Live Ingestion: {now_est.strftime('%Y-%m-%d %I:%M:%S %p EST')} ({now_pst.strftime('%I:%M:%S %p PST')})")
        print("="*95 + "\n")

        # 1. Macro Regime Assessment
        fed = macro_data.get("fed_funds", {})
        tnx = macro_data.get("tnx", {})
        vix = macro_data.get("vix", {})
        wti = macro_data.get("wti", {})
        brent = macro_data.get("brent", {})
        matrix = macro_data.get("portfolio_matrix", {})
        futures = macro_data.get("futures", {})
        breadth = macro_data.get("breadth", {})

        es = futures.get("es", {})
        nq = futures.get("nq", {})
        gold = futures.get("gold", {})
        btc = futures.get("btc", {})

        print(f"[MACRO REGIME ASSESSMENT] -> {macro_data.get('composite_regime', 'Neutral')} (Multiplier: {macro_data.get('composite_multiplier', 1.0)}x)")
        print(f"  * Fed Funds Rate: {fed.get('value', '—')} | Cycle Signal: {macro_data.get('rate_cycle_signal', 'Neutral')}")
        print(f"  * 10Y Yield (^TNX): {tnx.get('value', '—')}% ({tnx.get('chg', 0):+.2f}) | 2s10s Curve: {macro_data.get('curve_status', 'Normal')} ({macro_data.get('spread_2s10s', 0):+.2f})")
        print(f"  * VIX: {vix.get('value', '—')} ({macro_data.get('vix_state', 'Normal')}) | Oil: WTI ${wti.get('value', '—')} / Brent ${brent.get('value', '—')}")
        print(f"  * Futures & Crypto: ES {es.get('value', '—')} ({es.get('pct_chg', 0):+.2f}%), NQ {nq.get('value', '—')} ({nq.get('pct_chg', 0):+.2f}%), Gold ${gold.get('value', '—')} ({gold.get('pct_chg', 0):+.2f}%), BTC ${btc.get('value', '—')} ({btc.get('pct_chg', 0):+.2f}%)")
        print(f"  * Market Breadth: Adv/Decl {breadth.get('advancing_pct', 50)}% / {breadth.get('declining_pct', 50)}% | High/Low: {breadth.get('nh_pct', 50)}% / {breadth.get('nl_pct', 50)}% ({breadth.get('new_highs_count', 0)} Highs vs {breadth.get('new_lows_count', 0)} Lows) | >SMA50: {breadth.get('pct_above_sma50', 50)}% | >SMA200: {breadth.get('pct_above_sma200', 50)}%")
        print(f"  * B. Riley Rule: {macro_data.get('b_riley_state', 'Neutral')} - {macro_data.get('b_riley_detail', '')}")
        print(f"  * Multi-Asset Targets: Equity {matrix.get('equity_allocation', '70-80%')}, Gold {matrix.get('gold_target', '5-10%')}, BTC {matrix.get('btc_target', '2-4%')}, Cash {matrix.get('cash_target', '15-25%')} | Tech Cap {matrix.get('tech_cap', '35%')}\n")

        # 2. Institutional Watchlist
        print(f"[QUALIFIED INSTITUTIONAL WATCHLIST] ({len(day_watchlist)} Setups Qualified)")
        day_table_data = []
        for item in day_watchlist[:20]:
            clean_hl = item["headline"].encode("ascii", "ignore").decode("ascii")
            cat_stars_num = int(round(item.get("catalyst_stars", 3.0)))
            cat_tag = f"[{item['catalyst_type']}] {'*' * cat_stars_num} {clean_hl[:20]}"
            p_chg = item.get("pct_change", item.get("gap_pct", 0.0))
            day_table_data.append([
                item["ticker"],
                f"{item.get('setup_score', 0.0):.1f}*",
                f"${item['price']:.2f}",
                f"{p_chg:+.2f}%",
                f"{item['gap_pct']:+.2f}%",
                f"{item.get('pct_from_open', 0.0):+.2f}%",
                f"{item['rvol']:.2f}x",
                item.get("earnings_date", "—"),
                item.get("yesterday_high_dist", "—"),
                item.get("sector", "General")[:12],
                item.get("industry", "Diversified")[:15],
                cat_tag,
                item.get("analyst_rating", "—")[:12],
                item.get("call_wall", "—"),
                item.get("put_wall", "—"),
                item.get("gamma_flip", "—"),
                item.get("gamma_skew", "—")[:10],
                item.get("pc_ratio", "—")
            ])
        if day_table_data:
            print(tabulate(day_table_data, headers=["Ticker", "Score", "Price", "% Chg", "Gap %", "% Open", "RVOL", "Earnings", "Last High", "Sector", "Industry", "Catalyst", "Analyst", "Call Wall", "Put Wall", "Flip", "Skew", "P/C"], tablefmt="grid"))
        else:
            print("  No tickers qualified under current market session filters.")
        print()

        # 3. Economic Calendar
        print(f"[TODAY'S US ECONOMIC CALENDAR] (Sorted by Time & Impact, {len(economic_events)} Total Events)")
        eco_table_data = []
        for ev in economic_events:
            eco_table_data.append([
                ev.get("time"),
                ev.get("impact"),
                ev.get("title")[:40],
                ev.get("forecast"),
                ev.get("prior")
            ])
        if eco_table_data:
            print(tabulate(eco_table_data, headers=["Time (EST)", "Impact", "Event Title", "Forecast", "Prior"], tablefmt="grid"))
        else:
            print("  No economic releases scheduled today.")
        print()

        # 4. Earnings Calendar Summary (Yesterday AMC, Today BMO/AMC, Tomorrow BMO/AMC)
        bmo_list = earnings_data.get("today_bmo", [])
        amc_list = earnings_data.get("yesterday_amc", [])
        today_amc_list = earnings_data.get("today_amc", [])
        tom_bmo_list = earnings_data.get("tomorrow_bmo", [])
        tom_amc_list = earnings_data.get("tomorrow_amc", [])
        
        bmo_strs = [f"{x['ticker']} ({x['timing']}, {x.get('change', '—')})" for x in bmo_list[:6]]
        amc_strs = [f"{x['ticker']} ({x['timing']}, {x.get('change', '—')})" for x in amc_list[:6]]
        tom_strs = [f"{x['ticker']} ({x['timing']}, {x.get('change', '—')})" for x in (tom_bmo_list + tom_amc_list)[:6]]

        print(f"[EARNINGS CALENDAR (YESTERDAY, TODAY & TOMORROW)]")
        print(f"  * Today BMO ({len(bmo_list)} tickers): {', '.join(bmo_strs)}...")
        print(f"  * Yesterday AMC ({len(amc_list)} tickers): {', '.join(amc_strs)}...")
        print(f"  * Today AMC ({len(today_amc_list)} tickers)")
        print(f"  * Tomorrow BMO/AMC ({len(tom_bmo_list) + len(tom_amc_list)} tickers): {', '.join(tom_strs)}...\n")

        # 5. Analyst Upgrades & Revisions (Yesterday & Today)
        print(f"[ANALYST UPGRADES & REVISIONS (YESTERDAY & TODAY)] ({len(analyst_actions)} Revisions)")
        analyst_table_data = []
        for act in analyst_actions[:15]:
            clean_firm = act.get("firm", "Wall Street").encode("ascii", "ignore").decode("ascii")
            clean_rating = act.get("rating", "-").encode("ascii", "ignore").decode("ascii")
            clean_pt = act.get("price_target", "-").encode("ascii", "ignore").decode("ascii")
            analyst_table_data.append([
                act["ticker"],
                act.get("date", "Today"),
                clean_firm[:25],
                act.get("action", "Rating"),
                clean_rating[:30],
                clean_pt
            ])
        if analyst_table_data:
            print(tabulate(analyst_table_data, headers=["Ticker", "Date", "Firm", "Action", "Rating", "Target"], tablefmt="grid"))
        else:
            print("  No analyst rating revisions recorded for yesterday or today.")
        print()

        # 6. 45-Day Aggregated Institutional Options Structure
        if options_aggregated:
            print(f"[45-DAY AGGREGATED INSTITUTIONAL OPTIONS STRUCTURE] ({len(options_aggregated)} Tickers, Default Sorted by Vol/OI DESC)")
            opt_table_data = []
            for agg in options_aggregated[:15]:
                p_val = agg.get("stock_price", 0.0) or 0.0
                p_chg_val = agg.get("stock_pct_chg", 0.0) or 0.0
                p_str = f"${p_val:.2f} ({p_chg_val:+.2f}%)" if p_val > 0 else f"{agg.get('stock_price_str', '—')} ({agg.get('stock_pct_chg_str', '—')})"
                opt_table_data.append([
                    agg["ticker"],
                    p_str,
                    f"{agg.get('vol_oi_ratio', 1.0):.2f}x",
                    agg.get("atm_iv_str", "—"),
                    agg.get("iv_chg_str", "—"),
                    agg.get("iv_rank_str", "—"),
                    agg.get("net_dollar_str", "—"),
                    agg.get("call_wall", "—"),
                    agg.get("put_wall", "—"),
                    agg.get("gamma_flip", "—"),
                    agg.get("pc_ratio", "—"),
                    agg.get("skew", "—"),
                    f"{agg.get('total_45d_vol', 0):,}",
                    f"{agg.get('whale_count', 0)} Trades"
                ])
            print(tabulate(opt_table_data, headers=["Ticker", "Price (% Chg)", "Vol/OI", "ATM IV", "IV Chg", "IV Rank", "Net Flow ($)", "Call Wall", "Put Wall", "Gamma Flip", "P/C Ratio", "Skew", "45D Volume", "Whale Trades"], tablefmt="grid"))
            print()

terminal_viewer = TerminalViewer()
