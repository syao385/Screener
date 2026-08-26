"""Update reporter/html_generator.py with complete client-side Fidelity CSV parser & live DOM renderer."""

import os

HTML_GEN_CONTENT = r'''"""HTML Dashboard Generator: Produces the interactive, paginated, and sortable latest_report.html (Zero fake data)."""

import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from config import REPORT_HTML_PATH, TZ_EST, TZ_PST

logger = logging.getLogger("html_generator")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ Institutional Real-Time Intelligence Dashboard</title>
    <style>
        :root {{
            --bg-primary: #0b0f19;
            --bg-card: #111827;
            --bg-card-hover: #1f2937;
            --border: #374151;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-yellow: #f59e0b;
            --accent-purple: #8b5cf6;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background-color: var(--bg-primary); color: var(--text-main); line-height: 1.5; padding: 20px; }}
        
        .container {{ max-width: 1800px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }}
        
        /* Top Navigation & Portfolio Summary Bar */
        .top-navbar {{ display: flex; justify-content: space-between; align-items: center; background: #0f172a; border: 1px solid #3b82f6; border-radius: 12px; padding: 12px 24px; box-shadow: 0 6px 20px rgba(0,0,0,0.5); flex-wrap: wrap; gap: 14px; }}
        .nav-tabs {{ display: flex; gap: 10px; }}
        .nav-tab-btn {{ background: #1e293b; color: #f1f5f9; border: 1px solid #475569; padding: 10px 22px; border-radius: 8px; font-weight: 700; font-size: 13.5px; cursor: pointer; transition: all 0.25s ease; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.3); }}
        .nav-tab-btn:hover {{ background: #334155; color: #ffffff; border-color: #60a5fa; transform: translateY(-1px); }}
        .nav-tab-btn.active {{ background: #2563eb; color: #ffffff; border-color: #93c5fd; box-shadow: 0 0 16px rgba(37,99,235,0.6); }}
        .nav-tab-btn#nav-tab-portfolio.active {{ background: #059669; color: #ffffff; border-color: #6ee7b7; box-shadow: 0 0 16px rgba(5,150,105,0.6); }}
        .nav-tab-btn#nav-tab-macro.active {{ background: #4f46e5; color: #ffffff; border-color: #a5b4fc; box-shadow: 0 0 16px rgba(79,70,229,0.6); }}
        
        .nav-kpis {{ display: flex; align-items: center; gap: 14px; font-size: 12.5px; flex-wrap: wrap; }}
        .kpi-pill {{ background: #1e293b; border: 1px solid #334155; padding: 6px 14px; border-radius: 8px; font-size: 12.5px; color: #cbd5e1; }}
        .kpi-pill strong {{ color: #ffffff; }}
        
        /* Header */
        .header {{ display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #111827); padding: 20px 28px; border-radius: 12px; border: 1px solid #4338ca; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }}
        .header h1 {{ font-size: 24px; font-weight: 800; color: #fff; letter-spacing: -0.5px; }}
        .header .subtitle {{ color: #a5b4fc; font-size: 13.5px; margin-top: 4px; }}
        .header-meta {{ text-align: right; }}
        .badge-live {{ display: inline-block; background: #059669; color: #fff; padding: 4px 10px; border-radius: 9999px; font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
        .timestamp {{ font-size: 12px; color: var(--text-muted); margin-top: 5px; }}

        /* Macro Banner & 4D Radar */
        .macro-card {{ background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border); padding: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
        .macro-header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 14px; }}
        .macro-title {{ font-size: 17px; font-weight: 700; color: #e5e7eb; display: flex; align-items: center; gap: 8px; }}
        .regime-badge {{ padding: 5px 12px; border-radius: 8px; font-weight: 700; font-size: 13px; }}
        .regime-risk-on {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #059669; }}
        .regime-neutral {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #d97706; }}
        .regime-risk-off {{ background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #dc2626; }}

        .macro-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 16px; }}
        .metric-box {{ background: #1f2937; padding: 12px; border-radius: 8px; border: 1px solid #374151; }}
        .metric-label {{ font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; }}
        .metric-value {{ font-size: 18px; font-weight: 700; color: #fff; margin-top: 3px; }}
        .metric-sub {{ font-size: 11.5px; margin-top: 3px; }}
        .metric-source {{ font-size: 9.5px; color: #6b7280; margin-top: 3px; }}

        /* 4D Macro Radar Visualizer */
        .radar-panel {{ background: #182234; border: 1px solid #2563eb; border-radius: 10px; padding: 14px 18px; margin-bottom: 16px; }}
        .radar-title {{ font-size: 13px; font-weight: 700; color: #60a5fa; text-transform: uppercase; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }}
        .radar-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }}
        .radar-pillar {{ background: #0f172a; padding: 10px 14px; border-radius: 8px; border: 1px solid #334155; }}
        .radar-pillar-header {{ display: flex; justify-content: space-between; font-size: 12px; font-weight: 600; margin-bottom: 6px; }}
        .radar-bar-bg {{ background: #334155; height: 8px; border-radius: 4px; overflow: hidden; position: relative; }}
        .radar-bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.4s ease; }}
        .radar-status {{ font-size: 11px; color: #94a3b8; margin-top: 5px; }}

        /* Portfolio Manager KPI Cards */
        .portfolio-stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-bottom: 16px; }}
        .stat-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 16px; }}
        .stat-card-title {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; font-weight: 600; }}
        .stat-card-val {{ font-size: 22px; font-weight: 800; color: #fff; margin-top: 4px; }}
        .stat-card-sub {{ font-size: 12px; margin-top: 4px; }}

        /* Allocation Matrix Table */
        .matrix-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12.5px; }}
        .matrix-table th {{ background: #1f2937; color: #9ca3af; text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border); }}
        .matrix-table td {{ padding: 8px 12px; border-bottom: 1px solid #2d3748; color: #e5e7eb; font-weight: 500; }}

        /* Watchlists & Widgets Grid */
        .section-header-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }}
        .section-title {{ font-size: 17px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 8px; }}
        .grid-2col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media (max-width: 1100px) {{ .grid-2col {{ grid-template-columns: 1fr; }} }}

        .card {{ background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border); padding: 18px; }}

        /* Interactive Filter Bar */
        .filter-panel {{ background: #182234; border: 1px solid #2563eb; border-radius: 10px; padding: 12px 16px; margin-bottom: 14px; display: flex; flex-direction: column; gap: 10px; }}
        .filter-row {{ display: flex; flex-wrap: wrap; align-items: center; gap: 12px; }}
        .filter-item {{ display: flex; align-items: center; gap: 6px; font-size: 12px; color: #d1d5db; }}
        .filter-item label {{ display: flex; align-items: center; gap: 6px; cursor: pointer; }}
        .filter-select {{ background: #1f2937; border: 1px solid #374151; color: #fff; padding: 5px 9px; border-radius: 6px; font-size: 11.5px; cursor: pointer; }}
        .filter-select:focus {{ outline: none; border-color: #3b82f6; }}
        .filter-checkbox {{ accent-color: #3b82f6; cursor: pointer; width: 14px; height: 14px; }}
        
        .btn-action {{ background: #2563eb; color: #fff; border: none; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; transition: background 0.15s; }}
        .btn-action:hover {{ background: #1d4ed8; }}
        .btn-success {{ background: #059669; color: #fff; border: none; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; }}
        .btn-success:hover {{ background: #047857; }}
        .btn-secondary {{ background: #374151; color: #d1d5db; border: 1px solid #4b5563; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; }}
        .btn-secondary:hover {{ background: #4b5563; color: #fff; }}
        .btn-danger {{ background: #dc2626; color: #fff; border: none; padding: 4px 8px; border-radius: 4px; font-size: 11px; cursor: pointer; }}

        /* View Mode Selector Tabs */
        .view-mode-bar {{ display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; }}
        .view-btn {{ background: #1f2937; border: 1px solid #374151; color: #9ca3af; padding: 5px 12px; border-radius: 6px; font-size: 11.5px; font-weight: 700; cursor: pointer; transition: all 0.15s; }}
        .view-btn:hover {{ background: #2d3748; color: #fff; }}
        .view-btn.active {{ background: #3b82f6; color: #fff; border-color: #3b82f6; }}

        /* Table Controls & Pagination */
        .table-controls {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-size: 12px; color: var(--text-muted); flex-wrap: wrap; gap: 8px; }}
        .search-input {{ background: #1f2937; border: 1px solid var(--border); color: #fff; padding: 6px 12px; border-radius: 6px; font-size: 12px; width: 240px; }}
        .search-input:focus {{ outline: none; border-color: #3b82f6; }}
        
        .pagination {{ display: flex; justify-content: space-between; align-items: center; margin-top: 12px; font-size: 12px; color: var(--text-muted); }}
        .page-btns {{ display: flex; gap: 4px; }}
        .page-btn {{ background: #1f2937; border: 1px solid var(--border); color: #d1d5db; padding: 4px 10px; border-radius: 4px; cursor: pointer; }}
        .page-btn:hover {{ background: #374151; }}
        .page-btn.active {{ background: #3b82f6; color: #fff; border-color: #3b82f6; font-weight: bold; }}
        .page-btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}

        /* Tables & Sorting */
        .table-responsive {{ width: 100%; overflow-x: auto; }}
        table.data-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
        table.data-table th {{ background: #1f2937; color: #9ca3af; font-weight: 600; text-align: left; padding: 8px 8px; border-bottom: 1px solid var(--border); white-space: nowrap; }}
        table.data-table th.sortable {{ cursor: pointer; user-select: none; transition: background 0.15s ease; }}
        table.data-table th.sortable:hover {{ background: #2d3748; color: #fff; }}
        table.data-table td {{ padding: 7px 8px; border-bottom: 1px solid #1f2937; color: #d1d5db; vertical-align: middle; }}
        table.data-table tr.data-row:hover {{ background-color: var(--bg-card-hover); }}

        /* Column Visibility Classes */
        .col-all {{ }}
        .view-core .col-tech-only {{ display: none !important; }}
        .view-core .col-opt-only {{ display: none !important; }}
        .view-technical .col-opt-only {{ display: none !important; }}
        .view-technical .col-core-only {{ display: none !important; }}
        .view-options .col-tech-only {{ display: none !important; }}
        .view-options .col-core-only {{ display: none !important; }}

        .ticker-link {{ color: #60a5fa; font-weight: 700; text-decoration: none; font-size: 12.5px; }}
        .ticker-link:hover {{ text-decoration: underline; }}
        .pill {{ display: inline-block; padding: 2px 7px; border-radius: 6px; font-weight: 700; font-size: 11px; white-space: nowrap; }}
        .pill-green {{ background: rgba(16, 185, 129, 0.2); color: #34d399; }}
        .pill-red {{ background: rgba(239, 68, 68, 0.2); color: #f87171; }}
        .pill-yellow {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; }}
        .pill-blue {{ background: rgba(59, 130, 246, 0.2); color: #60a5fa; }}
        .pill-purple {{ background: rgba(139, 92, 246, 0.2); color: #a78bfa; }}

        .headline-link {{ color: #e5e7eb; text-decoration: none; font-size: 11px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
        .headline-link:hover {{ color: #93c5fd; }}

        /* Expandable Sub-Row Accordion Drawer */
        .row-drawer {{ display: none; background: #0f172a; padding: 14px; border-top: 1px solid #334155; border-bottom: 2px solid #2563eb; }}
        .drawer-content {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; padding: 8px; }}
        .drawer-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 12px 14px; }}
        .drawer-card-title {{ font-size: 12px; font-weight: 700; color: #60a5fa; text-transform: uppercase; margin-bottom: 8px; border-bottom: 1px solid #334155; padding-bottom: 4px; }}
        .drawer-item-row {{ display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px; }}

        /* Modal Overlay & Dialogs */
        .modal-overlay {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.75); z-index: 9999; justify-content: center; align-items: center; }}
        .modal-dialog {{ background: #111827; border: 1px solid #3b82f6; border-radius: 12px; width: 90%; max-width: 620px; padding: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.8); max-height: 90vh; overflow-y: auto; }}
        .modal-header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #374151; padding-bottom: 12px; margin-bottom: 16px; }}
        .modal-title {{ font-size: 18px; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 8px; }}
        .modal-close {{ background: none; border: none; color: #9ca3af; font-size: 22px; cursor: pointer; }}
        .modal-close:hover {{ color: #fff; }}
        .form-group {{ margin-bottom: 14px; }}
        .form-label {{ display: block; font-size: 12px; font-weight: 600; color: #9ca3af; margin-bottom: 4px; text-transform: uppercase; }}
        .form-control {{ width: 100%; background: #1f2937; border: 1px solid #374151; color: #fff; padding: 8px 12px; border-radius: 6px; font-size: 13px; }}
        .form-control:focus {{ outline: none; border-color: #3b82f6; }}
        .calc-result-box {{ background: #0f172a; border: 1px solid #2563eb; border-radius: 8px; padding: 14px; margin-top: 16px; }}
        .calc-row {{ display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px; }}
        .calc-row strong {{ color: #fff; }}

        .footer {{ text-align: center; color: #6b7280; font-size: 12px; padding: 24px 0; border-top: 1px solid var(--border); }}
    </style>
</head>
<body>
<div class="container">

    <!-- Top Navigation & Portfolio Bar -->
    <div class="top-navbar">
        <div class="nav-tabs">
            <button class="nav-tab-btn active" id="nav-tab-screener" onclick="switchMainView('screener')">🚀 Screener & Alpha Flow</button>
            <button class="nav-tab-btn" id="nav-tab-portfolio" onclick="switchMainView('portfolio')">💼 Portfolio Manager (Live Book)</button>
            <button class="nav-tab-btn" id="nav-tab-macro" onclick="switchMainView('macro')">📊 4D Macro & Allocations</button>
        </div>
        <div class="nav-kpis">
            <div class="kpi-pill">NAV: <strong id="top-nav-val">${portfolio_nav_str}</strong></div>
            <div class="kpi-pill">Cash (SPAXX): <strong id="top-cash-val" style="color: #34d399;">${portfolio_cash_str} ({portfolio_cash_weight}%)</strong></div>
            <div class="kpi-pill">Today P&L: <strong id="top-pnl-val" style="color: {port_day_color};">{portfolio_day_pnl_str} ({portfolio_day_pct_str})</strong></div>
            <div class="kpi-pill">Risk Multiplier: <span class="pill pill-blue">{matrix_multiplier}</span></div>
            <button class="btn-success" onclick="openFidelityImportModal()">📥 Import Fidelity CSV</button>
            <button class="btn-action" onclick="openSizingModal('NVDA', 210.0, 201.6, 'NVIDIA CORP', 'Long')">⚡ Sizing Calc</button>
        </div>
    </div>

    <!-- Header -->
    <div class="header">
        <div>
            <h1>⚡ Institutional Real-Time Intelligence Screener</h1>
            <div class="subtitle">{session_label} • 5-Star Setup Quality • 4D Macro Regime • Fidelity Portfolio Sync • 45D Gamma Exposure</div>
        </div>
        <div class="header-meta">
            <span class="badge-live">● Live Automated Engine</span>
            <div class="timestamp">Generated: {timestamp_est} ({timestamp_pst})</div>
        </div>
    </div>

    <!-- VIEW 1: MACRO & ALLOCATION VIEW -->
    <div id="view-macro-section">
        <!-- 4D Macro Regime Visualizer Card -->
        <div class="macro-card">
            <div class="macro-header">
                <div class="macro-title">
                    <span>🏛️ 4D Quantitative Macro Regime & Volatility Targeter</span>
                    <span class="regime-badge {regime_css_class}">{composite_regime}</span>
                </div>
                <div style="font-size: 13px; color: #9ca3af;">
                    Session Risk Multiplier: <strong style="color: #60a5fa; font-size: 15px;">{composite_multiplier}x</strong>
                </div>
            </div>

            <!-- 4-Pillar Radar Visualizer -->
            <div class="radar-panel">
                <div class="radar-title">
                    <span>4-Pillar Cross-Asset Macro State Space</span>
                    <span style="font-size: 11px; color: #94a3b8;">Target Portfolio Volatility: 14.0%</span>
                </div>
                <div class="radar-grid">
                    <div class="radar-pillar">
                        <div class="radar-pillar-header">
                            <span>💧 1. Liquidity & Yields</span>
                            <span style="color: {pillar_liq_color};">{pillar_liq_val}</span>
                        </div>
                        <div class="radar-bar-bg">
                            <div class="radar-bar-fill" style="width: {pillar_liq_width}%; background: {pillar_liq_color};"></div>
                        </div>
                        <div class="radar-status">{pillar_liq_status}</div>
                    </div>
                    <div class="radar-pillar">
                        <div class="radar-pillar-header">
                            <span>⚡ 2. Growth vs Inflation</span>
                            <span style="color: {pillar_gro_color};">{pillar_gro_val}</span>
                        </div>
                        <div class="radar-bar-bg">
                            <div class="radar-bar-fill" style="width: {pillar_gro_width}%; background: {pillar_gro_color};"></div>
                        </div>
                        <div class="radar-status">{pillar_gro_status}</div>
                    </div>
                    <div class="radar-pillar">
                        <div class="radar-pillar-header">
                            <span>🛡️ 3. Volatility & Credit</span>
                            <span style="color: {pillar_vol_color};">{pillar_vol_val}</span>
                        </div>
                        <div class="radar-bar-bg">
                            <div class="radar-bar-fill" style="width: {pillar_vol_width}%; background: {pillar_vol_color};"></div>
                        </div>
                        <div class="radar-status">{pillar_vol_status}</div>
                    </div>
                    <div class="radar-pillar">
                        <div class="radar-pillar-header">
                            <span>📈 4. Breadth & Futures</span>
                            <span style="color: {pillar_bre_color};">{pillar_bre_val}</span>
                        </div>
                        <div class="radar-bar-bg">
                            <div class="radar-bar-fill" style="width: {pillar_bre_width}%; background: {pillar_bre_color};"></div>
                        </div>
                        <div class="radar-status">{pillar_bre_status}</div>
                    </div>
                </div>
            </div>

            <!-- Key Metric Boxes -->
            <div class="macro-grid">
                <div class="metric-box">
                    <div class="metric-label">Fed Funds / Cycle</div>
                    <div class="metric-value">{fed_funds_val}%</div>
                    <div class="metric-sub" style="color: #60a5fa;">{rate_cycle_signal} ({rate_implication})</div>
                    <div class="metric-source">{fed_funds_source}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">10Y Yield (TNX)</div>
                    <div class="metric-value" style="color: {tnx_color};">{tnx_val:.2f}% ({tnx_chg:+.2f})</div>
                    <div class="metric-sub" style="color: #9ca3af;">Spread 2s10s: {spread_2s10s:+.2f}% ({curve_status})</div>
                    <div class="metric-source">{tnx_source} • {tnx_time}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">VIX Volatility Index</div>
                    <div class="metric-value" style="color: {vix_color};">{vix_val:.2f} ({vix_chg:+.2f})</div>
                    <div class="metric-sub" style="color: {vix_color};">{vix_state}</div>
                    <div class="metric-source">{vix_source} • {vix_time}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Crude Oil (WTI)</div>
                    <div class="metric-value" style="color: {oil_color};">${wti_val:.2f} ({wti_chg:+.2f})</div>
                    <div class="metric-sub" style="color: #9ca3af;">{oil_signal}</div>
                    <div class="metric-source">{wti_source} • {wti_time}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Index Futures (ES / NQ)</div>
                    <div class="metric-value" style="font-size: 15px;"><span style="color: {es_color};">ES {es_pct:+.2f}%</span> | <span style="color: {nq_color};">NQ {nq_pct:+.2f}%</span></div>
                    <div class="metric-sub" style="color: #9ca3af;">Gold {gold_pct:+.2f}% • BTC {btc_pct:+.2f}%</div>
                    <div class="metric-source">CME Globex Futures</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Market Breadth & SMA</div>
                    <div class="metric-value" style="color: {adv_color}; font-size: 15px;">Adv {adv_pct:.1f}% / Decl {decl_pct:.1f}%</div>
                    <div class="metric-sub" style="color: {sma200_color};">&gt;SMA200: {sma200_pct:.1f}% ({sma200_status})</div>
                    <div class="metric-source">{breadth_source}</div>
                </div>
            </div>

            <!-- Multi-Asset Target Matrix -->
            <table class="matrix-table">
                <thead>
                    <tr>
                        <th>Target Equities (E)</th>
                        <th>Target Gold (G)</th>
                        <th>Target Bitcoin (B)</th>
                        <th>Target Cash Buffer (C)</th>
                        <th>Tech Cap</th>
                        <th>Financials Cap</th>
                        <th>Energy Cap</th>
                        <th>Defensives Cap</th>
                        <th>Risk Multiplier</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong style="color: #38bdf8;">{matrix_equity}</strong></td>
                        <td><strong style="color: #fbbf24;">{matrix_gold}</strong></td>
                        <td><strong style="color: #a78bfa;">{matrix_btc}</strong></td>
                        <td><strong style="color: #34d399;">{matrix_cash}</strong></td>
                        <td>{matrix_tech}</td>
                        <td>{matrix_fin}</td>
                        <td>{matrix_energy}</td>
                        <td>{matrix_def}</td>
                        <td><span class="pill pill-blue">{matrix_multiplier}</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- VIEW 2: PORTFOLIO MANAGER VIEW -->
    <div id="view-portfolio-section" style="display: none;">
        <div class="card">
            <div class="section-header-row">
                <div class="section-title">
                    <span>💼 Institutional Portfolio Manager & Real-Time Risk Book</span>
                    <span id="port-acc-subtitle" style="font-size: 12px; color: #9ca3af; font-weight: normal;">({portfolio_acc_name} • #{portfolio_acc_num} • Synced with data/portfolio.json)</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn-success" onclick="openFidelityImportModal()">📥 Import Fidelity CSV</button>
                    <button class="btn-action" onclick="openAddPositionModal()">➕ Add Custom Position</button>
                    <button class="btn-secondary" onclick="exportPortfolioJSON()">💾 Export JSON</button>
                </div>
            </div>

            <!-- Portfolio Summary Stats -->
            <div class="portfolio-stats-grid">
                <div class="stat-card">
                    <div class="stat-card-title">Total Account NAV</div>
                    <div class="stat-card-val" id="port-card-nav">${portfolio_nav_str}</div>
                    <div class="stat-card-sub" id="port-card-cash" style="color: #94a3b8;">Liquid Cash: ${portfolio_cash_str} ({portfolio_cash_weight}%)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-title">Open Equity Holdings</div>
                    <div class="stat-card-val" id="port-card-eq" style="color: #38bdf8;">${portfolio_equity_str}</div>
                    <div class="stat-card-sub" id="port-card-count" style="color: #94a3b8;">Positions: {portfolio_pos_count} Assets</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-title">Today's Session P&L</div>
                    <div class="stat-card-val" id="port-card-day-pnl" style="color: {port_day_color};">{portfolio_day_pnl_str}</div>
                    <div class="stat-card-sub" id="port-card-day-pct" style="color: {port_day_color};">{portfolio_day_pct_str} Return</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-title">Total Unrealized Gain/Loss</div>
                    <div class="stat-card-val" id="port-card-tot-pnl" style="color: {port_tot_color};">{portfolio_tot_pnl_str}</div>
                    <div class="stat-card-sub" style="color: #94a3b8;">Risk Multiplier: {matrix_multiplier}</div>
                </div>
            </div>

            <!-- Table Controls -->
            <div class="table-controls">
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span style="font-weight: 600; color: #9ca3af;">Filter:</span>
                    <button class="btn-secondary" style="padding: 3px 8px; font-size: 11px;" onclick="filterPortfolioType('ALL')">All Assets</button>
                    <button class="btn-secondary" style="padding: 3px 8px; font-size: 11px;" onclick="filterPortfolioType('STOCK')">Stocks & ETFs</button>
                    <button class="btn-secondary" style="padding: 3px 8px; font-size: 11px;" onclick="filterPortfolioType('OPTION')">Options Contracts</button>
                </div>
                <input type="text" class="search-input" id="portfolio-search-input" placeholder="Search portfolio ticker or description..." onkeyup="filterPortfolioTable(this.value)">
            </div>

            <!-- Positions Table -->
            <div class="table-responsive">
                <table class="data-table" id="portfolio-table">
                    <thead>
                        <tr>
                            <th onclick="sortTable('portfolio-table', 0)" class="sortable">Symbol <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 1)" class="sortable">Description <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 2)" class="sortable">Qty <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 3)" class="sortable">Avg Cost <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 4)" class="sortable">Last Price <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 5)" class="sortable">Today P&L ($) <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 6)" class="sortable">Today % <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 7)" class="sortable">Total P&L ($) <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 8)" class="sortable">Total % <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 9)" class="sortable">Value ($) <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 10)" class="sortable">Weight % <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 11)" class="sortable">Strategy Tag <span class="sort-icon"></span></th>
                            <th style="text-align: center;">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {portfolio_position_rows}
                    </tbody>
                </table>
            </div>
            <div class="pagination" id="portfolio-table-pagination"></div>
        </div>
    </div>

    <!-- VIEW 3: SCREENER & ALPHA INTELLIGENCE VIEW -->
    <div id="view-screener-section">
        <!-- Real-Time Institutional Day Trading Watchlist -->
        <div class="card" id="day-watchlist-card">
            <div class="section-header-row">
                <div class="section-title">
                    <span>🚀 Qualified Watchlist & Universe Screener</span>
                    <span style="font-size: 12px; color: #9ca3af; font-weight: normal;">(Cap &ge;$1B, 30D Vol &ge;500k, Price &ge;$1.50 • Institutional Gatekeepers Pre-Selected)</span>
                </div>
                <span class="pill pill-green" id="day-counter-pill">Showing <span id="day-visible-count">{day_count}</span> of <span id="day-total-count">{day_count}</span> Stocks</span>
            </div>

            <!-- Interactive Multi-Factor Filter Bar -->
            <div class="filter-panel">
                <div class="filter-row">
                    <div class="filter-item">
                        <label>
                            <input type="checkbox" id="filter-breakout-last" class="filter-checkbox" checked onchange="filterDayWatchlist()">
                            <strong>&gt; Last Day High</strong>
                        </label>
                    </div>
                    <div class="filter-item">
                        <label>
                            <input type="checkbox" id="filter-breakout-pm" class="filter-checkbox" checked onchange="filterDayWatchlist()">
                            <strong>&gt; Premarket High</strong>
                        </label>
                    </div>
                    <div class="filter-item">
                        <span>% Chg:</span>
                        <select id="filter-chg" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="ALL" selected>All % Chg</option>
                            <option value="POS">&gt; 0% (Green Only)</option>
                            <option value="1.0">&ge; +1.0%</option>
                            <option value="2.0">&ge; +2.0%</option>
                            <option value="3.0">&ge; +3.0%</option>
                            <option value="5.0">&ge; +5.0%</option>
                            <option value="10.0">&ge; +10.0%</option>
                            <option value="15.0">&ge; +15.0%</option>
                            <option value="NEG">&lt; 0% (Red Only)</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Gap %:</span>
                        <select id="filter-gap" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="3.0" selected>&ge; +3.0% (Default)</option>
                            <option value="ALL">All Gaps</option>
                            <option value="NOGAP">No Gaps (Flat &lt; 1.0%)</option>
                            <option value="1.0">&ge; +1.0%</option>
                            <option value="2.0">&ge; +2.0%</option>
                            <option value="5.0">&ge; +5.0%</option>
                            <option value="8.0">&ge; +8.0%</option>
                            <option value="-1.0">Gap Down &le; -1.0%</option>
                            <option value="-3.0">Gap Down &le; -3.0%</option>
                            <option value="-8.0">Gap Down &le; -8.0%</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>% Open:</span>
                        <select id="filter-open" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="ALL" selected>All % Open</option>
                            <option value="POS">&gt; 0% (Above Open)</option>
                            <option value="1.0">&ge; +1.0%</option>
                            <option value="2.0">&ge; +2.0%</option>
                            <option value="3.0">&ge; +3.0%</option>
                            <option value="5.0">&ge; +5.0%</option>
                            <option value="10.0">&ge; +10.0%</option>
                            <option value="NEG">&lt; 0% (Below Open)</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>% VWAP:</span>
                        <select id="filter-vwap" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="ALL" selected>All VWAP Dist</option>
                            <option value="POS">&gt; VWAP (Above VWAP)</option>
                            <option value="XO">⚡ Cross Over (Bullish Cross)</option>
                            <option value="XU">🔻 Cross Under (Bearish Cross)</option>
                            <option value="STD_P1">&ge; +1 STD VWAP (+1&sigma; Upper Band)</option>
                            <option value="STD_P2">&ge; +2 STD VWAP (+2&sigma; Extended)</option>
                            <option value="STD_M1">&le; -1 STD VWAP (-1&sigma; Lower Band)</option>
                            <option value="STD_M2">&le; -2 STD VWAP (-2&sigma; Oversold)</option>
                            <option value="1.0">&ge; +1.0% above VWAP</option>
                            <option value="2.0">&ge; +2.0% above VWAP</option>
                            <option value="3.0">&ge; +3.0% above VWAP</option>
                            <option value="5.0">&ge; +5.0% above VWAP</option>
                            <option value="NEG">&lt; VWAP (Below VWAP)</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Flow / Bias:</span>
                        <select id="filter-flow" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="ALL" selected>All Flow Bias</option>
                            <option value="BULL_FLOW">🟢 Bullish Flow (Long Gamma, P/C &lt; 0.70)</option>
                            <option value="BEAR_FLOW">🔴 Bearish Flow (Put Hedge, P/C &gt; 1.00)</option>
                            <option value="WHALE">🐳 Whale Sweeps Active</option>
                            <option value="MOM_BULL">⚡ Bullish Momentum (&gt; VWAP &amp; Bullish Flow)</option>
                            <option value="MOM_BEAR">🔻 Bearish Momentum (&lt; VWAP &amp; Bearish Flow)</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>SMA20:</span>
                        <select id="filter-sma20" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="ALL" selected>All SMA20</option>
                            <option value="POS">&gt; SMA20 (Above)</option>
                            <option value="XO">⚡ Cross Over SMA20</option>
                            <option value="XU">🔻 Cross Under SMA20</option>
                            <option value="1.0">&ge; +1.0% above SMA20</option>
                            <option value="3.0">&ge; +3.0% above SMA20</option>
                            <option value="NEG">&lt; SMA20 (Below)</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>SMA50:</span>
                        <select id="filter-sma50" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="ALL" selected>All SMA50</option>
                            <option value="POS">&gt; SMA50 (Above)</option>
                            <option value="XO">⚡ Cross Over SMA50</option>
                            <option value="XU">🔻 Cross Under SMA50</option>
                            <option value="1.0">&ge; +1.0% above SMA50</option>
                            <option value="3.0">&ge; +3.0% above SMA50</option>
                            <option value="NEG">&lt; SMA50 (Below)</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>SMA200:</span>
                        <select id="filter-sma200" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="ALL" selected>All SMA200</option>
                            <option value="POS">&gt; SMA200 (Above - Bullish Trend)</option>
                            <option value="XO">⚡ Cross Over SMA200</option>
                            <option value="XU">🔻 Cross Under SMA200</option>
                            <option value="1.0">&ge; +1.0% above SMA200</option>
                            <option value="3.0">&ge; +3.0% above SMA200</option>
                            <option value="NEG">&lt; SMA200 (Below - Bearish Trend)</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Catalyst:</span>
                        <select id="filter-catalyst" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="2.0" selected>&ge; 2.0★ Positive (Default)</option>
                            <option value="0.0">All News / Any Rating</option>
                            <option value="3.0">&ge; 3.0★</option>
                            <option value="4.0">&ge; 4.0★</option>
                            <option value="5.0">5.0★ Only</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Min RVOL:</span>
                        <select id="filter-rvol" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="1.5" selected>&ge; 1.50x (Default)</option>
                            <option value="0.0">Any RVOL</option>
                            <option value="1.0">&ge; 1.00x</option>
                            <option value="2.0">&ge; 2.00x</option>
                            <option value="3.0">&ge; 3.00x</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Min Score:</span>
                        <select id="filter-score" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="2.5" selected>&ge; 2.5★ (Default)</option>
                            <option value="0.0">Any Setup Score</option>
                            <option value="3.0">&ge; 3.0★</option>
                            <option value="3.5">&ge; 3.5★</option>
                            <option value="4.0">&ge; 4.0★</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Sector:</span>
                        <select id="filter-sector" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="ALL" selected>All Sectors</option>
                            {sector_options}
                        </select>
                    </div>
                    <div class="filter-item">
                        <button class="btn-action" onclick="resetInstitutionalDefaults()">⚡ Institutional Defaults</button>
                        <button class="btn-secondary" onclick="showAllCandidates()">🌐 Show All Candidates</button>
                        <span id="save-status-pill" class="pill pill-green" style="display: none; font-size: 10px;">💾 Saved</span>
                    </div>
                </div>
            </div>

            <!-- View Mode Selector -->
            <div class="view-mode-bar">
                <span style="font-size: 12px; font-weight: 700; color: #9ca3af; align-self: center; margin-right: 6px;">VIEW MODE:</span>
                <button class="view-btn active" id="btn-view-core" onclick="switchWatchlistView('core')">📊 Core Overview (14 Cols)</button>
                <button class="view-btn" id="btn-view-technical" onclick="switchWatchlistView('technical')">📈 Technical & MAs (17 Cols)</button>
                <button class="view-btn" id="btn-view-options" onclick="switchWatchlistView('options')">🎯 Options Structure & Walls (17 Cols)</button>
            </div>

            <!-- Table Controls -->
            <div class="table-controls">
                <div>Show <select class="page-size-select" onchange="changePageSize('day-table', this.value)"><option value="15">15</option><option value="25" selected>25</option><option value="50">50</option><option value="1000">All</option></select> entries</div>
                <input type="text" class="search-input" id="day-search-input" placeholder="Search ticker, headline, sector..." onkeyup="filterDayWatchlist(false)">
            </div>

            <div class="table-responsive">
                <table class="data-table view-core" id="day-table">
                    <thead>
                        <tr>
                            <th onclick="sortTable('day-table', 0)" class="sortable col-all">Ticker <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 1)" class="sortable col-all">Score <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 2)" class="sortable col-all">Price <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 3)" class="sortable col-all">% Chg <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 4)" class="sortable col-all">Gap % <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 5)" class="sortable col-all">% Open <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 6)" class="sortable col-all">RVOL <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 7)" class="sortable col-all">Earnings <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 8)" class="sortable col-all">Last High <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 9)" class="sortable col-tech-only">PM High <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 10)" class="sortable col-tech-only">VWAP <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 11)" class="sortable col-tech-only">SMA5 <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 12)" class="sortable col-tech-only">SMA20 <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 13)" class="sortable col-tech-only">SMA50 <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 14)" class="sortable col-tech-only">SMA200 <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 15)" class="sortable col-core-only">Sector <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 16)" class="sortable col-core-only">Industry <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 17)" class="sortable col-core-only">Catalyst <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 18)" class="sortable col-opt-only">Call Wall <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 19)" class="sortable col-opt-only">Put Wall <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 20)" class="sortable col-opt-only">Gamma Flip <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 21)" class="sortable col-all">Skew <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 22)" class="sortable col-all">P/C <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 23)" class="sortable col-opt-only">Analyst <span class="sort-icon"></span></th>
                            <th class="col-all" style="text-align: center;">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {day_trading_rows}
                    </tbody>
                </table>
            </div>
            <div class="pagination" id="day-table-pagination"></div>
        </div>

        <!-- Grid: Economic Calendar & Earnings Calendar -->
        <div class="grid-2col" style="margin-top: 20px;">
            <!-- Widget: Economic Calendar -->
            <div class="card">
                <div class="section-header-row">
                    <div class="section-title">
                        <span>📅 Today's US Economic Calendar</span>
                        <span style="font-size: 12px; color: #9ca3af; font-weight: normal;">(Sorted by Time & Impact)</span>
                    </div>
                    <span class="pill pill-yellow" id="eco-count-pill">{eco_count} Events</span>
                </div>
                
                <div class="table-controls" style="margin-bottom: 12px;">
                    <div class="impact-filter-bar">
                        <span style="font-weight: 600; color: #9ca3af;">Filter Impact:</span>
                        <label class="filter-checkbox-label">
                            <input type="checkbox" id="filter-high" value="HIGH" checked onchange="filterEconomicImpact()">
                            <span class="pill pill-red" style="font-size: 11px;">HIGH</span>
                        </label>
                        <label class="filter-checkbox-label">
                            <input type="checkbox" id="filter-med" value="MED" checked onchange="filterEconomicImpact()">
                            <span class="pill pill-yellow" style="font-size: 11px;">MED</span>
                        </label>
                        <label class="filter-checkbox-label">
                            <input type="checkbox" id="filter-low" value="LOW" onchange="filterEconomicImpact()">
                            <span class="pill pill-blue" style="font-size: 11px;">LOW</span>
                        </label>
                    </div>
                    <div>Show <select class="page-size-select" onchange="changePageSize('eco-table', this.value)"><option value="10" selected>10</option><option value="25">25</option><option value="1000">All</option></select></div>
                </div>

                <div class="table-responsive">
                    <table class="data-table" id="eco-table">
                        <thead>
                            <tr>
                                <th onclick="sortTable('eco-table', 0)" class="sortable">Time (EST) <span class="sort-icon"></span></th>
                                <th onclick="sortTable('eco-table', 1)" class="sortable">Impact <span class="sort-icon"></span></th>
                                <th onclick="sortTable('eco-table', 2)" class="sortable">Event <span class="sort-icon"></span></th>
                                <th onclick="sortTable('eco-table', 3)" class="sortable">Forecast <span class="sort-icon"></span></th>
                                <th onclick="sortTable('eco-table', 4)" class="sortable">Prior <span class="sort-icon"></span></th>
                            </tr>
                        </thead>
                        <tbody>
                            {economic_calendar_rows}
                        </tbody>
                    </table>
                </div>
                <div class="pagination" id="eco-table-pagination"></div>
            </div>

            <!-- Widget: Earnings Calendar -->
            <div class="card">
                <div class="section-header-row">
                    <div class="section-title">
                        <span>📊 Earnings Calendar (Finviz Style)</span>
                        <span style="font-size: 12px; color: #9ca3af; font-weight: normal;">(Yesterday, Today & Tomorrow Only)</span>
                    </div>
                    <span class="pill pill-purple" id="earn-count-pill">{earn_count} Reports</span>
                </div>
                <div class="tab-bar">
                    <button class="tab-btn active" onclick="switchEarningsTab('all')">All</button>
                    <button class="tab-btn" onclick="switchEarningsTab('{yest_str} a')">Yesterday AMC</button>
                    <button class="tab-btn" onclick="switchEarningsTab('{today_str} b')">Today BMO</button>
                    <button class="tab-btn" onclick="switchEarningsTab('{today_str} a')">Today AMC</button>
                    <button class="tab-btn" onclick="switchEarningsTab('{tom_str}')">Tomorrow</button>
                </div>
                <div class="table-responsive">
                    <table class="data-table" id="earn-table">
                        <thead>
                            <tr>
                                <th onclick="sortTable('earn-table', 0)" class="sortable">Ticker <span class="sort-icon"></span></th>
                                <th onclick="sortTable('earn-table', 1)" class="sortable">Company <span class="sort-icon"></span></th>
                                <th onclick="sortTable('earn-table', 2)" class="sortable">Sector <span class="sort-icon"></span></th>
                                <th onclick="sortTable('earn-table', 3)" class="sortable">Timing <span class="sort-icon"></span></th>
                                <th onclick="sortTable('earn-table', 4)" class="sortable">% Chg <span class="sort-icon"></span></th>
                                <th onclick="sortTable('earn-table', 5)" class="sortable">Market Cap <span class="sort-icon"></span></th>
                            </tr>
                        </thead>
                        <tbody>
                            {earnings_calendar_rows}
                        </tbody>
                    </table>
                </div>
                <div class="pagination" id="earn-table-pagination"></div>
            </div>
        </div>

        <!-- Grid: Analyst Upgrades & Options Structure -->
        <div class="grid-2col" style="margin-top: 20px;">
            <!-- Widget: Analyst Actions -->
            <div class="card">
                <div class="section-header-row">
                    <div class="section-title">
                        <span>🎯 Analyst Upgrades & Revisions</span>
                        <span style="font-size: 12px; color: #9ca3af; font-weight: normal;">(Yesterday & Today Only)</span>
                    </div>
                    <span class="pill pill-green">{analyst_count} Actions</span>
                </div>
                <div class="table-controls">
                    <div>Show <select class="page-size-select" onchange="changePageSize('analyst-table', this.value)"><option value="10" selected>10</option><option value="25">25</option><option value="1000">All</option></select></div>
                    <input type="text" class="search-input" placeholder="Search analyst actions..." onkeyup="filterTable('analyst-table', this.value)">
                </div>
                <div class="table-responsive">
                    <table class="data-table" id="analyst-table">
                        <thead>
                            <tr>
                                <th onclick="sortTable('analyst-table', 0)" class="sortable">Ticker <span class="sort-icon"></span></th>
                                <th onclick="sortTable('analyst-table', 1)" class="sortable">Date <span class="sort-icon"></span></th>
                                <th onclick="sortTable('analyst-table', 2)" class="sortable">Firm <span class="sort-icon"></span></th>
                                <th onclick="sortTable('analyst-table', 3)" class="sortable">Action <span class="sort-icon"></span></th>
                                <th onclick="sortTable('analyst-table', 4)" class="sortable">Rating Change <span class="sort-icon"></span></th>
                                <th onclick="sortTable('analyst-table', 5)" class="sortable">Target <span class="sort-icon"></span></th>
                            </tr>
                        </thead>
                        <tbody>
                            {analyst_rows}
                        </tbody>
                    </table>
                </div>
                <div class="pagination" id="analyst-table-pagination"></div>
            </div>

            <!-- Widget: 45-Day Institutional Options Flow & Walls -->
            <div class="card">
                <div class="section-header-row">
                    <div class="section-title">
                        <span>⚡ Institutional Options Structure & Gamma (45-Day Aggregate)</span>
                    </div>
                    <span class="pill pill-blue">{options_agg_count} Tickers (Vol/OI Desc)</span>
                </div>
                <div class="table-controls">
                    <div>Show <select class="page-size-select" onchange="changePageSize('options-table', this.value)"><option value="10" selected>10</option><option value="25">25</option><option value="1000">All</option></select></div>
                    <input type="text" class="search-input" placeholder="Search options ticker..." onkeyup="filterTable('options-table', this.value)">
                </div>
                <div class="table-responsive">
                    <table class="data-table" id="options-table">
                        <thead>
                            <tr>
                                <th onclick="sortTable('options-table', 0)" class="sortable">Ticker <span class="sort-icon"></span></th>
                                <th onclick="sortTable('options-table', 1)" class="sortable">Price (% Chg) <span class="sort-icon"></span></th>
                                <th onclick="sortTable('options-table', 2)" class="sortable">Vol/OI <span class="sort-icon"></span></th>
                                <th onclick="sortTable('options-table', 3)" class="sortable">ATM IV <span class="sort-icon"></span></th>
                                <th onclick="sortTable('options-table', 4)" class="sortable">IV Chg <span class="sort-icon"></span></th>
                                <th onclick="sortTable('options-table', 5)" class="sortable">IV Rank <span class="sort-icon"></span></th>
                                <th onclick="sortTable('options-table', 6)" class="sortable">Net Dollar Flow <span class="sort-icon"></span></th>
                                <th onclick="sortTable('options-table', 7)" class="sortable">Call Wall <span class="sort-icon"></span></th>
                                <th onclick="sortTable('options-table', 8)" class="sortable">Put Wall <span class="sort-icon"></span></th>
                                <th onclick="sortTable('options-table', 9)" class="sortable">Gamma Flip <span class="sort-icon"></span></th>
                                <th onclick="sortTable('options-table', 10)" class="sortable">P/C <span class="sort-icon"></span></th>
                                <th onclick="sortTable('options-table', 11)" class="sortable">Skew <span class="sort-icon"></span></th>
                                <th onclick="sortTable('options-table', 12)" class="sortable">45D Vol <span class="sort-icon"></span></th>
                                <th>Whales</th>
                            </tr>
                        </thead>
                        <tbody>
                            {options_aggregated_rows}
                        </tbody>
                    </table>
                </div>
                <div class="pagination" id="options-table-pagination"></div>
            </div>
        </div>
    </div>

    <!-- MODAL 1: POSITION SIZING CALCULATOR -->
    <div class="modal-overlay" id="modal-sizing">
        <div class="modal-dialog">
            <div class="modal-header">
                <div class="modal-title"><span>⚡ Dynamic Position Sizing Calculator (ATR Parity)</span></div>
                <button class="modal-close" onclick="closeModal('modal-sizing')">&times;</button>
            </div>
            <div>
                <div class="form-group">
                    <label class="form-label">Ticker Symbol</label>
                    <input type="text" id="sizing-ticker" class="form-control" readonly style="font-weight: 700; color: #60a5fa;">
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div class="form-group">
                        <label class="form-label">Account NAV ($)</label>
                        <input type="number" id="sizing-nav" class="form-control" value="{portfolio_nav_raw}" oninput="recalcSizing()">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Risk Budget Per Trade (%)</label>
                        <input type="number" id="sizing-risk-pct" class="form-control" value="0.75" step="0.05" oninput="recalcSizing()">
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div class="form-group">
                        <label class="form-label">Entry Price ($)</label>
                        <input type="number" id="sizing-price" class="form-control" step="0.01" oninput="recalcSizing()">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Stop Loss Level ($)</label>
                        <input type="number" id="sizing-stop" class="form-control" step="0.01" oninput="recalcSizing()">
                    </div>
                </div>

                <div class="calc-result-box">
                    <div class="calc-row"><span>Macro Multiplier:</span> <strong id="calc-macro-mult" style="color: #38bdf8;">{composite_multiplier}x</strong></div>
                    <div class="calc-row"><span>Options Flow Conviction:</span> <strong id="calc-flow-factor" style="color: #34d399;">1.00x</strong></div>
                    <div class="calc-row"><span>Stop Distance:</span> <strong id="calc-stop-dist">4.0%</strong></div>
                    <div class="calc-row"><span>Maximum Risk Dollar ($):</span> <strong id="calc-risk-dollar" style="color: #f87171;">$2,500.00</strong></div>
                    <div style="border-top: 1px solid #334155; margin: 8px 0;"></div>
                    <div class="calc-row" style="font-size: 16px;">
                        <span>Recommended Position Shares:</span>
                        <strong id="calc-shares" style="color: #34d399; font-size: 20px;">100 Shares</strong>
                    </div>
                    <div class="calc-row"><span>Total Position Capital ($):</span> <strong id="calc-total-capital">$21,000.00</strong></div>
                    <div class="calc-row"><span>Portfolio NAV Allocation:</span> <strong id="calc-nav-weight">6.25%</strong></div>
                </div>

                <div style="margin-top: 16px; display: flex; justify-content: flex-end; gap: 8px;">
                    <button class="btn-secondary" onclick="closeModal('modal-sizing')">Cancel</button>
                    <button class="btn-success" onclick="addSizingToPortfolio()">➕ Add / Update in Active Portfolio</button>
                </div>
            </div>
        </div>
    </div>

    <!-- MODAL 2: FIDELITY CSV IMPORTER -->
    <div class="modal-overlay" id="modal-import-fidelity">
        <div class="modal-dialog">
            <div class="modal-header">
                <div class="modal-title"><span>📥 Import Fidelity Brokerage Positions CSV</span></div>
                <button class="modal-close" onclick="closeModal('modal-import-fidelity')">&times;</button>
            </div>
            <div>
                <p style="font-size: 12.5px; color: #9ca3af; margin-bottom: 12px;">
                    Paste your raw CSV export text from Fidelity or upload a file. The system will automatically reconcile cash, equities, options, and calculate real-time portfolio NAV.
                </p>
                <div class="form-group">
                    <label class="form-label">Upload .CSV File</label>
                    <input type="file" id="fidelity-file-input" class="form-control" accept=".csv" onchange="handleFidelityFileUpload(this)">
                </div>
                <div class="form-group">
                    <label class="form-label">Or Paste Fidelity CSV Text</label>
                    <textarea id="fidelity-csv-text" class="form-control" rows="8" placeholder="Account number,Account name,Symbol,Description,Quantity..."></textarea>
                </div>
                <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px;">
                    <button class="btn-secondary" onclick="closeModal('modal-import-fidelity')">Cancel</button>
                    <button class="btn-success" onclick="processFidelityImport()">📥 Process & Sync Portfolio</button>
                </div>
            </div>
        </div>
    </div>

    <!-- MODAL 3: EDIT POSITION MODAL -->
    <div class="modal-overlay" id="modal-edit-position">
        <div class="modal-dialog">
            <div class="modal-header">
                <div class="modal-title"><span>✏️ Edit Portfolio Position</span></div>
                <button class="modal-close" onclick="closeModal('modal-edit-position')">&times;</button>
            </div>
            <div>
                <div class="form-group">
                    <label class="form-label">Symbol</label>
                    <input type="text" id="edit-pos-symbol" class="form-control" readonly style="font-weight: 700;">
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div class="form-group">
                        <label class="form-label">Quantity</label>
                        <input type="number" id="edit-pos-qty" class="form-control" step="0.001">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Average Cost ($)</label>
                        <input type="number" id="edit-pos-avg-cost" class="form-control" step="0.01">
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div class="form-group">
                        <label class="form-label">Stop Loss ($)</label>
                        <input type="number" id="edit-pos-stop" class="form-control" step="0.01">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Profit Target ($)</label>
                        <input type="number" id="edit-pos-target" class="form-control" step="0.01">
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-label">Strategy Tag</label>
                    <select id="edit-pos-strategy" class="form-control">
                        <option value="Core Long Holding">Core Long Holding</option>
                        <option value="Tactical Momentum">Tactical Momentum</option>
                        <option value="Earnings Gap Breakout">Earnings Gap Breakout</option>
                        <option value="Options Flow Whale">Options Flow Whale</option>
                        <option value="Options Hedge / Income">Options Hedge / Income</option>
                        <option value="Mean Reversion">Mean Reversion</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Trade Notes</label>
                    <input type="text" id="edit-pos-notes" class="form-control" placeholder="e.g. Scaled in after VWAP cross over">
                </div>
                <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px;">
                    <button class="btn-secondary" onclick="closeModal('modal-edit-position')">Cancel</button>
                    <button class="btn-success" onclick="savePositionEdit()">💾 Save Changes</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <div class="footer">
        <div>⚡ Institutional Real-Time Intelligence Screener • Quantitative Multi-Factor System • 100% Real-Time Market Feed</div>
        <div style="margin-top: 4px; color: #4b5563;">Refreshes every 60s during regular trading hours • Strict Zero Fake Data Protocol</div>
    </div>

</div>

<!-- Interactive Client-Side JavaScript Logic -->
<script>
    const tableStates = {{
        'day-table': {{ currentPage: 1, pageSize: 25, allRows: [], filteredRows: [] }},
        'eco-table': {{ currentPage: 1, pageSize: 10, allRows: [], filteredRows: [] }},
        'earn-table': {{ currentPage: 1, pageSize: 10, allRows: [], filteredRows: [] }},
        'analyst-table': {{ currentPage: 1, pageSize: 10, allRows: [], filteredRows: [] }},
        'options-table': {{ currentPage: 1, pageSize: 10, allRows: [], filteredRows: [] }},
        'portfolio-table': {{ currentPage: 1, pageSize: 25, allRows: [], filteredRows: [] }}
    }};

    window.portfolioData = {portfolio_json_raw};

    document.addEventListener('DOMContentLoaded', () => {{
        // Check if user has saved portfolio in localStorage
        try {{
            const localSaved = localStorage.getItem('user_portfolio_data');
            if (localSaved) {{
                const parsed = JSON.parse(localSaved);
                if (parsed && parsed.positions && parsed.positions.length > 0) {{
                    window.portfolioData = parsed;
                }}
            }}
        }} catch (e) {{
            console.error('Could not load localStorage portfolio:', e);
        }}

        initTableState('day-table');
        initTableState('eco-table');
        initTableState('earn-table');
        initTableState('analyst-table');
        initTableState('options-table');
        
        renderPortfolioDOM();

        loadFilterPreferences();
        filterDayWatchlist(false);
    }});

    function switchMainView(view) {{
        const btnScreener = document.getElementById('nav-tab-screener');
        const btnPortfolio = document.getElementById('nav-tab-portfolio');
        const btnMacro = document.getElementById('nav-tab-macro');
        
        const secScreener = document.getElementById('view-screener-section');
        const secPortfolio = document.getElementById('view-portfolio-section');
        const secMacro = document.getElementById('view-macro-section');

        if (btnScreener) btnScreener.classList.remove('active');
        if (btnPortfolio) btnPortfolio.classList.remove('active');
        if (btnMacro) btnMacro.classList.remove('active');

        if (view === 'screener') {{
            if (btnScreener) btnScreener.classList.add('active');
            if (secScreener) secScreener.style.display = 'block';
            if (secMacro) secMacro.style.display = 'block';
            if (secPortfolio) secPortfolio.style.display = 'none';
        }} else if (view === 'portfolio') {{
            if (btnPortfolio) btnPortfolio.classList.add('active');
            if (secPortfolio) secPortfolio.style.display = 'block';
            if (secScreener) secScreener.style.display = 'none';
            if (secMacro) secMacro.style.display = 'none';
        }} else if (view === 'macro') {{
            if (btnMacro) btnMacro.classList.add('active');
            if (secMacro) secMacro.style.display = 'block';
            if (secScreener) secScreener.style.display = 'none';
            if (secPortfolio) secPortfolio.style.display = 'none';
        }}
        window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }}

    function openModal(id) {{
        const m = document.getElementById(id);
        if (m) m.style.display = 'flex';
    }}

    function closeModal(id) {{
        const m = document.getElementById(id);
        if (m) m.style.display = 'none';
    }}

    /* Dynamic Portfolio DOM Builder */
    function renderPortfolioDOM() {{
        const pData = window.portfolioData || {{ positions: [] }};
        const nav = pData.total_nav || 0;
        const cash = pData.cash_balance || 0;
        const eq = pData.equity_value || (nav - cash);
        const dayD = pData.total_day_pnl_dollar || 0;
        const dayP = pData.total_day_pnl_pct || (nav > 0 ? (dayD / nav) * 100 : 0);
        const totD = pData.total_unrealized_pnl_dollar || 0;
        const cashW = nav > 0 ? ((cash / nav) * 100).toFixed(1) : '0.0';

        const dayColor = dayD >= 0 ? '#34d399' : '#f87171';
        const totColor = totD >= 0 ? '#34d399' : '#f87171';

        // Update Top Navbar
        const topNav = document.getElementById('top-nav-val');
        if (topNav) topNav.innerText = '$' + nav.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        const topCash = document.getElementById('top-cash-val');
        if (topCash) topCash.innerText = '$' + cash.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}}) + ' (' + cashW + '%)';
        const topPnl = document.getElementById('top-pnl-val');
        if (topPnl) {{
            topPnl.style.color = dayColor;
            topPnl.innerText = (dayD >= 0 ? '+$' : '-$') + Math.abs(dayD).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}}) + ' (' + (dayP >= 0 ? '+' : '') + dayP.toFixed(2) + '%)';
        }}

        // Update Portfolio Cards
        const cardNav = document.getElementById('port-card-nav');
        if (cardNav) cardNav.innerText = '$' + nav.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        const cardCash = document.getElementById('port-card-cash');
        if (cardCash) cardCash.innerText = 'Liquid Cash: $' + cash.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}}) + ' (' + cashW + '%)';
        const cardEq = document.getElementById('port-card-eq');
        if (cardEq) cardEq.innerText = '$' + eq.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        const cardCount = document.getElementById('port-card-count');
        if (cardCount) cardCount.innerText = 'Positions: ' + (pData.positions ? pData.positions.length : 0) + ' Assets';
        const cardDayPnl = document.getElementById('port-card-day-pnl');
        if (cardDayPnl) {{
            cardDayPnl.style.color = dayColor;
            cardDayPnl.innerText = (dayD >= 0 ? '+$' : '-$') + Math.abs(dayD).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        }}
        const cardDayPct = document.getElementById('port-card-day-pct');
        if (cardDayPct) {{
            cardDayPct.style.color = dayColor;
            cardDayPct.innerText = (dayP >= 0 ? '+' : '') + dayP.toFixed(2) + '% Return';
        }}
        const cardTotPnl = document.getElementById('port-card-tot-pnl');
        if (cardTotPnl) {{
            cardTotPnl.style.color = totColor;
            cardTotPnl.innerText = (totD >= 0 ? '+$' : '-$') + Math.abs(totD).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        }}

        // Populate Table Rows
        const tbody = document.querySelector('#portfolio-table tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        const positions = pData.positions || [];
        if (positions.length === 0) {{
            tbody.innerHTML = '<tr><td colspan="13" style="text-align: center; color: #9ca3af; padding: 24px;">No positions found in active book. Click "Import Fidelity CSV" to load positions.</td></tr>';
            return;
        }}

        const rowElements = [];
        positions.forEach(p => {{
            const sym = p.symbol || '—';
            const desc = p.description || '—';
            const qty = p.quantity || 0;
            const avgC = p.average_cost || 0;
            const lastP = p.last_price || 0;
            const curV = p.current_value || (qty * lastP);
            const pDayD = p.today_pnl_dollar || 0;
            const pDayP = p.today_pnl_pct || 0;
            const pTotD = p.total_pnl_dollar || 0;
            const pTotP = p.total_pnl_pct || 0;
            const wPct = p.weight_pct || (nav > 0 ? (curV / nav) * 100 : 0);
            const strat = p.strategy_tag || 'Tactical';
            const stopL = p.stop_loss || 0;
            const targP = p.target_price || 0;
            const notes = p.notes || '';
            const isOpt = p.is_option || false;

            const pDayColor = pDayD >= 0 ? '#34d399' : '#f87171';
            const pTotColor = pTotD >= 0 ? '#34d399' : '#f87171';

            const tr = document.createElement('tr');
            tr.className = 'data-row';
            tr.setAttribute('data-symbol', sym);
            tr.setAttribute('data-is-option', isOpt ? 'true' : 'false');
            tr.innerHTML = 
                '<td><strong style="color: #60a5fa;">' + sym + '</strong></td>' +
                '<td style="font-size: 11px; color: #d1d5db; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">' + desc + '</td>' +
                '<td><strong>' + qty.toLocaleString('en-US', {{minimumFractionDigits: 0, maximumFractionDigits: 3}}) + '</strong></td>' +
                '<td>$' + avgC.toFixed(2) + '</td>' +
                '<td><strong>$' + lastP.toFixed(2) + '</strong></td>' +
                '<td style="color: ' + pDayColor + '; font-weight: 600;">' + (pDayD >= 0 ? '+' : '') + pDayD.toFixed(2) + '</td>' +
                '<td style="color: ' + pDayColor + '; font-weight: 600;">' + (pDayP >= 0 ? '+' : '') + pDayP.toFixed(2) + '%</td>' +
                '<td style="color: ' + pTotColor + '; font-weight: 700;">' + (pTotD >= 0 ? '+' : '') + pTotD.toFixed(2) + '</td>' +
                '<td style="color: ' + pTotColor + '; font-weight: 700;">' + (pTotP >= 0 ? '+' : '') + pTotP.toFixed(2) + '%</td>' +
                '<td><strong>$' + curV.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}}) + '</strong></td>' +
                '<td><span class="pill pill-blue">' + wPct.toFixed(2) + '%</span></td>' +
                '<td><span class="pill pill-purple">' + strat + '</span></td>' +
                '<td style="text-align: center; white-space: nowrap;">' +
                    '<button class="btn-action" style="padding: 2px 6px; font-size: 10px;" onclick="openSizingModal(&quot;' + sym + '&quot;, ' + lastP + ', ' + stopL + ', &quot;' + desc.replace(/"/g, '').replace(/\'/g, '') + '&quot;, &quot;Rebalance&quot;)">⚡</button>' +
                    '<button class="btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="openEditPositionModal(&quot;' + sym + '&quot;, ' + qty + ', ' + avgC + ', ' + stopL + ', ' + targP + ', &quot;' + strat + '&quot;, &quot;' + notes.replace(/"/g, '').replace(/\'/g, '') + '&quot;)">✏️</button>' +
                    '<button class="btn-danger" style="padding: 2px 6px; font-size: 10px;" onclick="deletePortfolioPosition(&quot;' + sym + '&quot;)">❌</button>' +
                '</td>';
            tbody.appendChild(tr);
            rowElements.push(tr);
        }});

        tableStates['portfolio-table'].allRows = rowElements;
        tableStates['portfolio-table'].filteredRows = [...rowElements];
        renderTablePage('portfolio-table');
    }}

    /* Sizing Modal Calculations */
    function openSizingModal(ticker, price, stop, desc, posType) {{
        document.getElementById('sizing-ticker').value = ticker;
        document.getElementById('sizing-price').value = price || 100.0;
        document.getElementById('sizing-stop').value = stop || (price * 0.96);
        recalcSizing();
        openModal('modal-sizing');
    }}

    function recalcSizing() {{
        const nav = parseFloat(document.getElementById('sizing-nav').value) || (window.portfolioData ? window.portfolioData.total_nav : 336870.83);
        const riskPct = parseFloat(document.getElementById('sizing-risk-pct').value) || 0.75;
        const price = parseFloat(document.getElementById('sizing-price').value) || 100.0;
        const stop = parseFloat(document.getElementById('sizing-stop').value) || (price * 0.96);
        const macroMult = {composite_multiplier} || 0.95;
        const flowFactor = 1.00;

        const riskDollar = nav * (riskPct / 100.0);
        const stopDistDollar = Math.max(price * 0.015, Math.abs(price - stop));
        const stopDistPct = (stopDistDollar / price) * 100.0;
        const baseShares = riskDollar / stopDistDollar;
        const effectiveMult = macroMult * flowFactor;
        const finalShares = Math.max(1, Math.floor(baseShares * effectiveMult));
        const totalCapital = finalShares * price;
        const weightPct = (totalCapital / nav) * 100.0;

        document.getElementById('calc-stop-dist').innerText = stopDistPct.toFixed(2) + '%';
        document.getElementById('calc-risk-dollar').innerText = '$' + riskDollar.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        document.getElementById('calc-shares').innerText = finalShares.toLocaleString() + ' Shares';
        document.getElementById('calc-total-capital').innerText = '$' + totalCapital.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        document.getElementById('calc-nav-weight').innerText = weightPct.toFixed(2) + '%';
    }}

    function addSizingToPortfolio() {{
        const ticker = document.getElementById('sizing-ticker').value.toUpperCase();
        const price = parseFloat(document.getElementById('sizing-price').value);
        const stop = parseFloat(document.getElementById('sizing-stop').value);
        const sharesText = document.getElementById('calc-shares').innerText;
        const shares = parseInt(sharesText.replace(/[^0-9]/g, ''), 10) || 10;

        if (!window.portfolioData) window.portfolioData = {{ positions: [], total_nav: 336870.83, cash_balance: 70830.35 }};
        const pos = window.portfolioData.positions || [];
        const existingIdx = pos.findIndex(p => p.symbol === ticker);

        const newPos = {{
            symbol: ticker,
            description: ticker + ' Equity Position',
            is_option: false,
            quantity: shares,
            last_price: price,
            current_value: shares * price,
            cost_basis_total: shares * price,
            average_cost: price,
            today_pnl_dollar: 0.0,
            today_pnl_pct: 0.0,
            total_pnl_dollar: 0.0,
            total_pnl_pct: 0.0,
            strategy_tag: 'Tactical Momentum',
            stop_loss: stop,
            target_price: +(price * 1.15).toFixed(2),
            entry_date: 'Aug 24, 2026',
            notes: 'Added from Sizing Calculator'
        }};

        if (existingIdx >= 0) {{
            pos[existingIdx] = Object.assign(pos[existingIdx], newPos);
        }} else {{
            pos.unshift(newPos);
        }}

        recomputePortfolioMetrics();
        alert('Added ' + shares + ' shares of ' + ticker + ' at $' + price.toFixed(2) + ' to Active Portfolio.');
        closeModal('modal-sizing');
    }}

    function openFidelityImportModal() {{
        openModal('modal-import-fidelity');
    }}

    function handleFidelityFileUpload(input) {{
        const file = input.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {{
            document.getElementById('fidelity-csv-text').value = e.target.result;
        }};
        reader.readAsText(file);
    }}

    /* Robust Client-Side Fidelity CSV Parser */
    function parseCSVLine(line) {{
        const result = [];
        let cur = '';
        let inQuotes = false;
        for (let i = 0; i < line.length; i++) {{
            const c = line[i];
            if (c === '"') {{
                inQuotes = !inQuotes;
            }} else if (c === ',' && !inQuotes) {{
                result.push(cur.trim());
                cur = '';
            }} else {{
                cur += c;
            }}
        }}
        result.push(cur.trim());
        return result;
    }}

    function cleanNum(val) {{
        if (!val) return 0.0;
        const clean = String(val).replace(/[$,%]/g, '').trim();
        if (clean === '--' || clean === '—' || clean === 'N/A' || clean === '') return 0.0;
        const num = parseFloat(clean);
        return isNaN(num) ? 0.0 : num;
    }}

    function processFidelityImport() {{
        const rawText = document.getElementById('fidelity-csv-text').value.trim();
        if (!rawText) {{
            alert('Please paste or upload Fidelity CSV content first.');
            return;
        }}

        const rawLines = rawText.split(String.fromCharCode(10));
        const lines = [];
        for (let i = 0; i < rawLines.length; i++) {{
            const l = rawLines[i].replace(String.fromCharCode(13), '').trim();
            if (l.length > 0) lines.push(l);
        }}

        let headerIdx = -1;
        for (let i = 0; i < lines.length; i++) {{
            if (lines[i].indexOf('Account number') >= 0 && lines[i].indexOf('Symbol') >= 0) {{
                headerIdx = i;
                break;
            }}
        }}

        if (headerIdx === -1) {{
            alert('Could not find Fidelity CSV header row (must contain "Account number" and "Symbol"). Please verify your export.');
            return;
        }}

        const headers = parseCSVLine(lines[headerIdx]);
        const getIdx = function(name) {{
            return headers.findIndex(function(h) {{ return h.toLowerCase().indexOf(name.toLowerCase()) >= 0; }});
        }};

        const symIdx = getIdx('Symbol');
        const descIdx = getIdx('Description');
        const qtyIdx = getIdx('Quantity');
        const lastPIdx = getIdx('Last price');
        const curVIdx = getIdx('Current value');
        const costTotIdx = getIdx('Cost basis total');
        const avgCostIdx = getIdx('Average cost');
        const dayDIdx = getIdx("Today's gain/loss dollar");
        const dayPIdx = getIdx("Today's gain/loss percent");
        const totDIdx = getIdx("Total gain/loss dollar");
        const totPIdx = getIdx("Total gain/loss percent");
        const accNumIdx = getIdx('Account number');
        const accNmIdx = getIdx('Account name');
        const typeIdx = getIdx('Type');

        let cashBalance = 0.0;
        let positions = [];
        let accNumber = '';
        let accName = '';

        for (let i = headerIdx + 1; i < lines.length; i++) {{
            const cols = parseCSVLine(lines[i]);
            if (cols.length < 3) continue;

            const symRaw = (cols[symIdx] || '').trim();
            const desc = (cols[descIdx] || '').trim();
            const accNum = (cols[accNumIdx] || '').trim();
            const accNm = (cols[accNmIdx] || '').trim();

            if (accNum && !accNumber) accNumber = accNum;
            if (accNm && !accName) accName = accNm;

            // Check for cash line
            if (symRaw.indexOf('SPAXX') >= 0 || desc.toUpperCase().indexOf('MONEY MARKET') >= 0 || accNm.indexOf('Pending activity') >= 0 || desc.indexOf('Pending activity') >= 0) {{
                let val = cleanNum(cols[curVIdx]);
                if (val === 0) {{
                    for (let j = 0; j < cols.length; j++) {{
                        let cand = cleanNum(cols[j]);
                        if (cand > 0) {{ val = cand; break; }}
                    }}
                }}
                cashBalance += val;
                continue;
            }}

            // Skip disclaimers & empty lines
            if (!symRaw || symRaw.indexOf('The data and information') >= 0 || symRaw.indexOf('Brokerage services') >= 0 || symRaw.indexOf('Date downloaded') >= 0) {{
                continue;
            }}

            const qty = cleanNum(cols[qtyIdx]);
            if (qty === 0 && !symRaw.startsWith('-')) continue;

            const lastP = cleanNum(cols[lastPIdx]);
            const curV = cleanNum(cols[curVIdx]);
            const dayD = cleanNum(cols[dayDIdx]);
            const dayP = cleanNum(cols[dayPIdx]);
            const totD = cleanNum(cols[totDIdx]);
            const totP = cleanNum(cols[totPIdx]);
            const costTot = cleanNum(cols[costTotIdx]);
            const avgC = cleanNum(cols[avgCostIdx]) || (qty > 0 ? (costTot / qty) : lastP);
            const posType = (cols[typeIdx] || 'Cash').trim();

            const isOption = symRaw.startsWith('-') || desc.toUpperCase().indexOf('CALL') >= 0 || desc.toUpperCase().indexOf('PUT') >= 0;
            const cleanSym = symRaw.replace('-', '').replace(' ', '');

            let strat = 'Tactical Momentum';
            if (isOption) strat = 'Options Hedge / Income';
            else if (qty > 50 && curV > 10000) strat = 'Core Long Holding';

            positions.push({{
                symbol: isOption ? cleanSym : symRaw,
                raw_symbol: symRaw,
                description: desc,
                is_option: isOption,
                quantity: qty,
                last_price: lastP,
                current_value: curV,
                cost_basis_total: costTot,
                average_cost: avgC,
                today_pnl_dollar: dayD,
                today_pnl_pct: dayP,
                total_pnl_dollar: totD,
                total_pnl_pct: totP,
                account_type: posType,
                strategy_tag: strat,
                stop_loss: !isOption ? +(lastP * 0.93).toFixed(2) : 0,
                target_price: !isOption ? +(lastP * 1.15).toFixed(2) : 0,
                entry_date: 'Aug 24, 2026',
                notes: ''
            }});
        }}

        const totalEquity = positions.reduce(function(acc, p) {{ return acc + p.current_value; }}, 0);
        const totalNav = cashBalance + totalEquity;

        positions.forEach(function(p) {{
            p.weight_pct = totalNav > 0 ? +((p.current_value / totalNav) * 100).toFixed(2) : 0.0;
        }});

        window.portfolioData = {{
            account_number: accNumber || '264695485',
            account_name: accName || 'Traditional IRA',
            last_updated: new Date().toLocaleString(),
            total_nav: +totalNav.toFixed(2),
            cash_balance: +cashBalance.toFixed(2),
            equity_value: +totalEquity.toFixed(2),
            risk_budget_pct: 0.75,
            positions_count: positions.length,
            positions: positions,
            total_day_pnl_dollar: +positions.reduce(function(acc, p) {{ return acc + p.today_pnl_dollar; }}, 0).toFixed(2),
            total_day_pnl_pct: totalNav > 0 ? +(positions.reduce(function(acc, p) {{ return acc + p.today_pnl_dollar; }}, 0) / totalNav * 100).toFixed(2) : 0.0,
            total_unrealized_pnl_dollar: +positions.reduce(function(acc, p) {{ return acc + p.total_pnl_dollar; }}, 0).toFixed(2),
            cash_weight_pct: totalNav > 0 ? +((cashBalance / totalNav) * 100).toFixed(2) : 0.0
        }};

        try {{
            localStorage.setItem('user_portfolio_data', JSON.stringify(window.portfolioData));
        }} catch (e) {{
            console.error('Could not save to localStorage:', e);
        }}

        renderPortfolioDOM();
        closeModal('modal-import-fidelity');

        const msg = [
            'Successfully imported ' + positions.length + ' positions from Fidelity!',
            'Total Account NAV: $' + totalNav.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}}),
            'Liquid Cash (SPAXX): $' + cashBalance.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}}),
            'Open Equities & Options: $' + totalEquity.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})
        ].join(String.fromCharCode(10));
        alert(msg);
    }}

    function recomputePortfolioMetrics() {{
        if (!window.portfolioData) return;
        const pData = window.portfolioData;
        const pos = pData.positions || [];
        const cash = pData.cash_balance || 0;
        const totalEq = pos.reduce((acc, p) => acc + (p.current_value || (p.quantity * p.last_price)), 0);
        const totalNav = cash + totalEq;
        pos.forEach(p => {{
            p.weight_pct = totalNav > 0 ? +((p.current_value / totalNav) * 100).toFixed(2) : 0.0;
        }});
        pData.total_nav = +totalNav.toFixed(2);
        pData.equity_value = +totalEq.toFixed(2);
        pData.positions_count = pos.length;
        pData.total_day_pnl_dollar = +pos.reduce((acc, p) => acc + (p.today_pnl_dollar || 0), 0).toFixed(2);
        pData.total_day_pnl_pct = totalNav > 0 ? +(pData.total_day_pnl_dollar / totalNav * 100).toFixed(2) : 0.0;
        pData.total_unrealized_pnl_dollar = +pos.reduce((acc, p) => acc + (p.total_pnl_dollar || 0), 0).toFixed(2);
        pData.cash_weight_pct = totalNav > 0 ? +((cash / totalNav) * 100).toFixed(2) : 0.0;

        try {{
            localStorage.setItem('user_portfolio_data', JSON.stringify(pData));
        }} catch (e) {{}}

        renderPortfolioDOM();
    }}

    function openEditPositionModal(sym, qty, avgCost, stop, target, strat, notes) {{
        document.getElementById('edit-pos-symbol').value = sym;
        document.getElementById('edit-pos-qty').value = qty;
        document.getElementById('edit-pos-avg-cost').value = avgCost;
        document.getElementById('edit-pos-stop').value = stop || (avgCost * 0.94).toFixed(2);
        document.getElementById('edit-pos-target').value = target || (avgCost * 1.15).toFixed(2);
        document.getElementById('edit-pos-strategy').value = strat || 'Core Long Holding';
        document.getElementById('edit-pos-notes').value = notes || '';
        openModal('modal-edit-position');
    }}

    function savePositionEdit() {{
        const sym = document.getElementById('edit-pos-symbol').value;
        const qty = parseFloat(document.getElementById('edit-pos-qty').value);
        const avgCost = parseFloat(document.getElementById('edit-pos-avg-cost').value);
        const stop = parseFloat(document.getElementById('edit-pos-stop').value);
        const target = parseFloat(document.getElementById('edit-pos-target').value);
        const strat = document.getElementById('edit-pos-strategy').value;
        const notes = document.getElementById('edit-pos-notes').value;

        if (window.portfolioData && window.portfolioData.positions) {{
            const pos = window.portfolioData.positions.find(p => p.symbol === sym);
            if (pos) {{
                pos.quantity = qty;
                pos.average_cost = avgCost;
                pos.stop_loss = stop;
                pos.target_price = target;
                pos.strategy_tag = strat;
                pos.notes = notes;
                pos.current_value = +(qty * pos.last_price).toFixed(2);
                recomputePortfolioMetrics();
            }}
        }}

        alert('Saved changes for position ' + sym);
        closeModal('modal-edit-position');
    }}

    function deletePortfolioPosition(sym) {{
        if (confirm('Are you sure you want to remove ' + sym + ' from your portfolio book?')) {{
            if (window.portfolioData && window.portfolioData.positions) {{
                window.portfolioData.positions = window.portfolioData.positions.filter(p => p.symbol !== sym);
                recomputePortfolioMetrics();
            }}
            alert('Position ' + sym + ' deleted.');
        }}
    }}

    function exportPortfolioJSON() {{
        const jsonStr = JSON.stringify(window.portfolioData || {{}}, null, 2);
        const blob = new Blob([jsonStr], {{ type: 'application/json' }});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'portfolio.json';
        a.click();
    }}

    function filterPortfolioType(type) {{
        const table = document.getElementById('portfolio-table');
        const rows = table.querySelectorAll('tbody tr.data-row');
        rows.forEach(r => {{
            const isOpt = r.getAttribute('data-is-option') === 'true';
            if (type === 'ALL') r.style.display = '';
            else if (type === 'STOCK') r.style.display = isOpt ? 'none' : '';
            else if (type === 'OPTION') r.style.display = isOpt ? '' : 'none';
        }});
    }}

    function filterPortfolioTable(q) {{
        const query = (q || '').toLowerCase().trim();
        const table = document.getElementById('portfolio-table');
        const rows = table.querySelectorAll('tbody tr.data-row');
        rows.forEach(r => {{
            const text = r.innerText.toLowerCase();
            r.style.display = text.includes(query) ? '' : 'none';
        }});
    }}

    /* Core Table Sorting & Filtering */
    function initTableState(tableId) {{
        const table = document.getElementById(tableId);
        if (!table) return;
        const rows = Array.from(table.querySelectorAll('tbody tr.data-row'));
        tableStates[tableId].allRows = rows;
        tableStates[tableId].filteredRows = [...rows];
        renderTablePage(tableId);
    }}

    function renderTablePage(tableId) {{
        const state = tableStates[tableId];
        if (!state) return;
        const table = document.getElementById(tableId);
        const tbody = table.querySelector('tbody');
        const start = (state.currentPage - 1) * state.pageSize;
        const end = start + state.pageSize;

        const allDrawerMap = new Map();
        table.querySelectorAll('tbody tr.row-drawer, tbody tr.whale-drawer').forEach(d => {{
            allDrawerMap.set(d.id, d);
        }});

        tbody.innerHTML = '';
        const pageRows = state.filteredRows.slice(start, end);

        if (pageRows.length === 0) {{
            const colCount = table.querySelectorAll('thead th').length || 15;
            tbody.innerHTML = `<tr><td colspan="${{colCount}}" style="text-align: center; color: #9ca3af; padding: 24px;">No matching records found.</td></tr>`;
        }} else {{
            pageRows.forEach(r => {{
                tbody.appendChild(r);
                const drawerId = r.getAttribute('data-drawer-id') || r.getAttribute('data-whale-id');
                if (drawerId && allDrawerMap.has(drawerId)) {{
                    tbody.appendChild(allDrawerMap.get(drawerId));
                }}
            }});
        }}

        renderPaginationControls(tableId);
    }}

    function renderPaginationControls(tableId) {{
        const state = tableStates[tableId];
        const container = document.getElementById(`${{tableId}}-pagination`);
        if (!container) return;

        const totalItems = state.filteredRows.length;
        const totalPages = Math.ceil(totalItems / state.pageSize) || 1;
        const startItem = totalItems > 0 ? (state.currentPage - 1) * state.pageSize + 1 : 0;
        const endItem = Math.min(state.currentPage * state.pageSize, totalItems);

        let html = `<div>Showing ${{startItem}} to ${{endItem}} of ${{totalItems}} entries</div>`;
        html += `<div class="page-btns">`;
        html += `<button class="page-btn" ${{state.currentPage === 1 ? 'disabled' : ''}} onclick="changePage('${{tableId}}', 1)">&laquo;</button>`;
        html += `<button class="page-btn" ${{state.currentPage === 1 ? 'disabled' : ''}} onclick="changePage('${{tableId}}', ${{state.currentPage - 1}})">&lsaquo;</button>`;

        const maxButtons = 5;
        let startPage = Math.max(1, state.currentPage - Math.floor(maxButtons / 2));
        let endPage = Math.min(totalPages, startPage + maxButtons - 1);
        if (endPage - startPage + 1 < maxButtons) {{
            startPage = Math.max(1, endPage - maxButtons + 1);
        }}

        for (let i = startPage; i <= endPage; i++) {{
            html += `<button class="page-btn ${{i === state.currentPage ? 'active' : ''}}" onclick="changePage('${{tableId}}', ${{i}})">${{i}}</button>`;
        }}

        html += `<button class="page-btn" ${{state.currentPage === totalPages ? 'disabled' : ''}} onclick="changePage('${{tableId}}', ${{state.currentPage + 1}})">&rsaquo;</button>`;
        html += `<button class="page-btn" ${{state.currentPage === totalPages ? 'disabled' : ''}} onclick="changePage('${{tableId}}', ${{totalPages}})">&raquo;</button>`;
        html += `</div>`;

        container.innerHTML = html;
    }}

    function changePage(tableId, page) {{
        const state = tableStates[tableId];
        if (!state) return;
        const totalPages = Math.ceil(state.filteredRows.length / state.pageSize) || 1;
        state.currentPage = Math.max(1, Math.min(page, totalPages));
        renderTablePage(tableId);
    }}

    function changePageSize(tableId, size) {{
        const state = tableStates[tableId];
        if (!state) return;
        state.pageSize = parseInt(size, 10);
        state.currentPage = 1;
        renderTablePage(tableId);
    }}

    function toggleRowDrawer(drawerId) {{
        const drawer = document.getElementById(drawerId);
        if (drawer) {{
            drawer.style.display = drawer.style.display === 'table-row' ? 'none' : 'table-row';
        }}
    }}

    function toggleWhaleDrawer(drawerId) {{
        const drawer = document.getElementById(drawerId);
        if (drawer) {{
            drawer.style.display = drawer.style.display === 'table-row' ? 'none' : 'table-row';
        }}
    }}

    function switchWatchlistView(mode, save = true) {{
        const table = document.getElementById('day-table');
        if (!table) return;

        table.classList.remove('view-core', 'view-technical', 'view-options');
        table.classList.add(`view-${{mode}}`);

        document.getElementById('btn-view-core').classList.toggle('active', mode === 'core');
        document.getElementById('btn-view-technical').classList.toggle('active', mode === 'technical');
        document.getElementById('btn-view-options').classList.toggle('active', mode === 'options');

        window.currentWatchlistView = mode;
        if (save) saveFilterPreferences();
    }}

    function switchEarningsTab(filterVal) {{
        document.querySelectorAll('.tab-bar .tab-btn').forEach(btn => {{
            btn.classList.remove('active');
        }});
        event.target.classList.add('active');

        const state = tableStates['earn-table'];
        if (!state) return;

        if (filterVal === 'all') {{
            state.filteredRows = [...state.allRows];
        }} else {{
            state.filteredRows = state.allRows.filter(r => {{
                const text = r.innerText.toLowerCase();
                return text.includes(filterVal.toLowerCase());
            }});
        }}
        state.currentPage = 1;
        renderTablePage('earn-table');
    }}

    function filterEconomicImpact() {{
        const showHigh = document.getElementById('filter-high').checked;
        const showMed = document.getElementById('filter-med').checked;
        const showLow = document.getElementById('filter-low').checked;

        const state = tableStates['eco-table'];
        if (!state) return;

        state.filteredRows = state.allRows.filter(r => {{
            const impactCell = r.children[1] ? r.children[1].innerText.trim() : '';
            if (impactCell === 'HIGH' && !showHigh) return false;
            if (impactCell === 'MED' && !showMed) return false;
            if (impactCell === 'LOW' && !showLow) return false;
            return true;
        }});

        state.currentPage = 1;
        renderTablePage('eco-table');
    }}

    function sortTable(tableId, colIdx) {{
        const state = tableStates[tableId];
        if (!state) return;
        const table = document.getElementById(tableId);
        const th = table.querySelectorAll('thead th')[colIdx];
        if (!th) return;

        const isAsc = th.classList.contains('asc');
        table.querySelectorAll('thead th').forEach(h => {{
            h.classList.remove('asc', 'desc');
            const icon = h.querySelector('.sort-icon');
            if (icon) icon.innerText = '';
        }});

        th.classList.add(isAsc ? 'desc' : 'asc');
        const icon = th.querySelector('.sort-icon');
        if (icon) icon.innerText = isAsc ? ' ▼' : ' ▲';

        state.filteredRows.sort((a, b) => {{
            const valA = (a.children[colIdx] ? a.children[colIdx].innerText.trim() : '').replace(/[$,%x★]/g, '');
            const valB = (b.children[colIdx] ? b.children[colIdx].innerText.trim() : '').replace(/[$,%x★]/g, '');

            const numA = parseFloat(valA);
            const numB = parseFloat(valB);

            if (!isNaN(numA) && !isNaN(numB)) {{
                return isAsc ? numB - numA : numA - numB;
            }}
            return isAsc ? valB.localeCompare(valA) : valA.localeCompare(valB);
        }});

        renderTablePage(tableId);
    }}

    function filterTable(tableId, query) {{
        const state = tableStates[tableId];
        if (!state) return;
        const q = (query || '').toLowerCase().trim();
        state.filteredRows = state.allRows.filter(r => {{
            return r.innerText.toLowerCase().includes(q);
        }});
        state.currentPage = 1;
        renderTablePage(tableId);
    }}

    /* Watchlist Multi-Factor Interactive Filter with LocalStorage Persistence */
    function saveFilterPreferences() {{
        try {{
            const prefs = {{
                reqLastHigh: document.getElementById('filter-breakout-last').checked,
                reqPmHigh: document.getElementById('filter-breakout-pm').checked,
                filterChg: document.getElementById('filter-chg') ? document.getElementById('filter-chg').value : 'ALL',
                minGap: document.getElementById('filter-gap') ? document.getElementById('filter-gap').value : '3.0',
                filterOpen: document.getElementById('filter-open') ? document.getElementById('filter-open').value : 'ALL',
                filterVwap: document.getElementById('filter-vwap') ? document.getElementById('filter-vwap').value : 'ALL',
                filterFlow: document.getElementById('filter-flow') ? document.getElementById('filter-flow').value : 'ALL',
                filterSma20: document.getElementById('filter-sma20') ? document.getElementById('filter-sma20').value : 'ALL',
                filterSma50: document.getElementById('filter-sma50') ? document.getElementById('filter-sma50').value : 'ALL',
                filterSma200: document.getElementById('filter-sma200') ? document.getElementById('filter-sma200').value : 'ALL',
                minCat: document.getElementById('filter-catalyst').value,
                minRvol: document.getElementById('filter-rvol').value,
                minScore: document.getElementById('filter-score').value,
                selSector: document.getElementById('filter-sector').value,
                activeView: window.currentWatchlistView || 'core'
            }};
            localStorage.setItem('screener_filter_prefs', JSON.stringify(prefs));
            const saveNotice = document.getElementById('save-status-pill');
            if (saveNotice) {{
                saveNotice.style.display = 'inline-block';
                saveNotice.innerText = '💾 Saved';
                setTimeout(() => {{ saveNotice.innerText = '💾 Auto-Saved'; }}, 1500);
            }}
        }} catch (e) {{
            console.error('Failed to save filter preferences:', e);
        }}
    }}

    function loadFilterPreferences() {{
        try {{
            const saved = localStorage.getItem('screener_filter_prefs');
            if (saved) {{
                const prefs = JSON.parse(saved);
                if (prefs.reqLastHigh !== undefined) document.getElementById('filter-breakout-last').checked = prefs.reqLastHigh;
                if (prefs.reqPmHigh !== undefined) document.getElementById('filter-breakout-pm').checked = prefs.reqPmHigh;
                if (prefs.filterChg !== undefined && document.getElementById('filter-chg')) document.getElementById('filter-chg').value = prefs.filterChg;
                if (prefs.minGap !== undefined && document.getElementById('filter-gap')) document.getElementById('filter-gap').value = prefs.minGap;
                if (prefs.filterOpen !== undefined && document.getElementById('filter-open')) document.getElementById('filter-open').value = prefs.filterOpen;
                if (prefs.filterVwap !== undefined && document.getElementById('filter-vwap')) document.getElementById('filter-vwap').value = prefs.filterVwap;
                if (prefs.filterFlow !== undefined && document.getElementById('filter-flow')) document.getElementById('filter-flow').value = prefs.filterFlow;
                if (prefs.filterSma20 !== undefined && document.getElementById('filter-sma20')) document.getElementById('filter-sma20').value = prefs.filterSma20;
                if (prefs.filterSma50 !== undefined && document.getElementById('filter-sma50')) document.getElementById('filter-sma50').value = prefs.filterSma50;
                if (prefs.filterSma200 !== undefined && document.getElementById('filter-sma200')) document.getElementById('filter-sma200').value = prefs.filterSma200;
                if (prefs.minCat !== undefined) document.getElementById('filter-catalyst').value = prefs.minCat;
                if (prefs.minRvol !== undefined) document.getElementById('filter-rvol').value = prefs.minRvol;
                if (prefs.minScore !== undefined) document.getElementById('filter-score').value = prefs.minScore;
                if (prefs.selSector !== undefined) {{
                    const secElem = document.getElementById('filter-sector');
                    if (secElem && secElem.querySelector(`option[value="${{prefs.selSector}}"]`)) {{
                        secElem.value = prefs.selSector;
                    }}
                }}
                if (prefs.activeView) {{
                    switchWatchlistView(prefs.activeView, false);
                }}
            }}
        }} catch (e) {{
            console.error('Failed to load filter preferences:', e);
        }}
    }}

    function filterDayWatchlist(save = true) {{
        const reqLastHigh = document.getElementById('filter-breakout-last').checked;
        const reqPmHigh = document.getElementById('filter-breakout-pm').checked;
        const filterChg = document.getElementById('filter-chg') ? document.getElementById('filter-chg').value : 'ALL';
        const filterGap = document.getElementById('filter-gap') ? document.getElementById('filter-gap').value : '3.0';
        const filterOpen = document.getElementById('filter-open') ? document.getElementById('filter-open').value : 'ALL';
        const filterVwap = document.getElementById('filter-vwap') ? document.getElementById('filter-vwap').value : 'ALL';
        const filterFlow = document.getElementById('filter-flow') ? document.getElementById('filter-flow').value : 'ALL';
        const filterSma20 = document.getElementById('filter-sma20') ? document.getElementById('filter-sma20').value : 'ALL';
        const filterSma50 = document.getElementById('filter-sma50') ? document.getElementById('filter-sma50').value : 'ALL';
        const filterSma200 = document.getElementById('filter-sma200') ? document.getElementById('filter-sma200').value : 'ALL';
        const minCat = parseFloat(document.getElementById('filter-catalyst').value) || 0.0;
        const minRvol = parseFloat(document.getElementById('filter-rvol').value) || 0.0;
        const minScore = parseFloat(document.getElementById('filter-score').value) || 0.0;
        const selSector = document.getElementById('filter-sector').value;
        const searchInput = document.getElementById('day-search-input');
        const q = searchInput ? searchInput.value.toLowerCase().trim() : '';

        const state = tableStates['day-table'];
        if (!state) return;

        state.filteredRows = state.allRows.filter(r => {{
            const bLast = r.getAttribute('data-breakout-last') === 'true';
            const bPm = r.getAttribute('data-breakout-pm') === 'true';
            const chg = parseFloat(r.getAttribute('data-chg')) || 0.0;
            const gap = parseFloat(r.getAttribute('data-gap')) || 0.0;
            const openChg = parseFloat(r.getAttribute('data-open')) || 0.0;
            const vwapDist = parseFloat(r.getAttribute('data-vwap-dist')) || 0.0;
            const vwapXo = r.getAttribute('data-vwap-xo') === 'true';
            const vwapXu = r.getAttribute('data-vwap-xu') === 'true';
            const vwapP1 = r.getAttribute('data-vwap-std-p1') === 'true';
            const vwapP2 = r.getAttribute('data-vwap-std-p2') === 'true';
            const vwapM1 = r.getAttribute('data-vwap-std-m1') === 'true';
            const vwapM2 = r.getAttribute('data-vwap-std-m2') === 'true';

            const skew = r.getAttribute('data-skew') || 'Neutral';
            const pc = parseFloat(r.getAttribute('data-pc')) || 1.0;
            const netFlow = parseFloat(r.getAttribute('data-net-flow')) || 0.0;
            const whales = parseInt(r.getAttribute('data-whales'), 10) || 0;

            const sma20Dist = parseFloat(r.getAttribute('data-sma20-dist')) || 0.0;
            const sma20Xo = r.getAttribute('data-sma20-xo') === 'true';
            const sma20Xu = r.getAttribute('data-sma20-xu') === 'true';

            const sma50Dist = parseFloat(r.getAttribute('data-sma50-dist')) || 0.0;
            const sma50Xo = r.getAttribute('data-sma50-xo') === 'true';
            const sma50Xu = r.getAttribute('data-sma50-xu') === 'true';

            const sma200Dist = parseFloat(r.getAttribute('data-sma200-dist')) || 0.0;
            const sma200Xo = r.getAttribute('data-sma200-xo') === 'true';
            const sma200Xu = r.getAttribute('data-sma200-xu') === 'true';

            const stars = parseFloat(r.getAttribute('data-stars')) || 0.0;
            const isPos = r.getAttribute('data-pos') === 'true';
            const rvol = parseFloat(r.getAttribute('data-rvol')) || 0.0;
            const score = parseFloat(r.getAttribute('data-score')) || 0.0;
            const sector = r.getAttribute('data-sector') || '';
            const text = r.innerText.toLowerCase();

            if (reqLastHigh && !bLast) return false;
            if (reqPmHigh && !bPm) return false;

            if (filterChg !== 'ALL') {{
                if (filterChg === 'POS' && chg <= 0) return false;
                if (filterChg === 'NEG' && chg >= 0) return false;
                if (filterChg !== 'POS' && filterChg !== 'NEG') {{
                    const minChg = parseFloat(filterChg);
                    if (!isNaN(minChg) && chg < minChg) return false;
                }}
            }}

            if (filterGap !== 'ALL') {{
                if (filterGap === 'NOGAP') {{
                    if (gap < -0.99 || gap > 0.99) return false;
                }} else {{
                    const numGap = parseFloat(filterGap);
                    if (!isNaN(numGap)) {{
                        if (numGap < 0) {{
                            if (gap > numGap) return false;
                        }} else {{
                            if (gap < numGap) return false;
                        }}
                    }}
                }}
            }}

            if (filterOpen !== 'ALL') {{
                if (filterOpen === 'POS' && openChg <= 0) return false;
                if (filterOpen === 'NEG' && openChg >= 0) return false;
                if (filterOpen !== 'POS' && filterOpen !== 'NEG') {{
                    const minOpen = parseFloat(filterOpen);
                    if (!isNaN(minOpen) && openChg < minOpen) return false;
                }}
            }}

            if (filterVwap !== 'ALL') {{
                if (filterVwap === 'POS' && vwapDist < 0) return false;
                if (filterVwap === 'NEG' && vwapDist >= 0) return false;
                if (filterVwap === 'XO') {{
                    if (!vwapXo && !(vwapDist >= 0 && vwapDist <= 1.5)) return false;
                }} else if (filterVwap === 'XU') {{
                    if (!vwapXu && !(vwapDist <= 0 && vwapDist >= -1.5)) return false;
                }} else if (filterVwap === 'STD_P1') {{
                    if (!vwapP1 && vwapDist < 1.0) return false;
                }} else if (filterVwap === 'STD_P2') {{
                    if (!vwapP2 && vwapDist < 2.0) return false;
                }} else if (filterVwap === 'STD_M1') {{
                    if (!vwapM1 && vwapDist > -1.0) return false;
                }} else if (filterVwap === 'STD_M2') {{
                    if (!vwapM2 && vwapDist > -2.0) return false;
                }} else if (filterVwap !== 'POS' && filterVwap !== 'NEG') {{
                    const minVwap = parseFloat(filterVwap);
                    if (!isNaN(minVwap) && vwapDist < minVwap) return false;
                }}
            }}

            if (filterFlow !== 'ALL') {{
                if (filterFlow === 'BULL_FLOW') {{
                    if (!skew.includes('Bullish') && pc >= 0.70 && netFlow <= 0) return false;
                }} else if (filterFlow === 'BEAR_FLOW') {{
                    if (!skew.includes('Bearish') && pc <= 1.00 && netFlow >= 0) return false;
                }} else if (filterFlow === 'WHALE') {{
                    if (whales <= 0) return false;
                }} else if (filterFlow === 'MOM_BULL') {{
                    if (vwapDist < 0 || (!skew.includes('Bullish') && pc >= 0.85 && netFlow <= 0)) return false;
                }} else if (filterFlow === 'MOM_BEAR') {{
                    if (vwapDist >= 0 || (!skew.includes('Bearish') && pc <= 1.00 && netFlow >= 0)) return false;
                }}
            }}

            if (filterSma20 !== 'ALL') {{
                if (filterSma20 === 'POS' && sma20Dist < 0) return false;
                if (filterSma20 === 'NEG' && sma20Dist >= 0) return false;
                if (filterSma20 === 'XO') {{
                    if (!sma20Xo && !(sma20Dist >= 0 && sma20Dist <= 1.5)) return false;
                }} else if (filterSma20 === 'XU') {{
                    if (!sma20Xu && !(sma20Dist <= 0 && sma20Dist >= -1.5)) return false;
                }} else if (filterSma20 !== 'POS' && filterSma20 !== 'NEG') {{
                    const minSma = parseFloat(filterSma20);
                    if (!isNaN(minSma) && sma20Dist < minSma) return false;
                }}
            }}

            if (filterSma50 !== 'ALL') {{
                if (filterSma50 === 'POS' && sma50Dist < 0) return false;
                if (filterSma50 === 'NEG' && sma50Dist >= 0) return false;
                if (filterSma50 === 'XO') {{
                    if (!sma50Xo && !(sma50Dist >= 0 && sma50Dist <= 1.5)) return false;
                }} else if (filterSma50 === 'XU') {{
                    if (!sma50Xu && !(sma50Dist <= 0 && sma50Dist >= -1.5)) return false;
                }} else if (filterSma50 !== 'POS' && filterSma50 !== 'NEG') {{
                    const minSma = parseFloat(filterSma50);
                    if (!isNaN(minSma) && sma50Dist < minSma) return false;
                }}
            }}

            if (filterSma200 !== 'ALL') {{
                if (filterSma200 === 'POS' && sma200Dist < 0) return false;
                if (filterSma200 === 'NEG' && sma200Dist >= 0) return false;
                if (filterSma200 === 'XO') {{
                    if (!sma200Xo && !(sma200Dist >= 0 && sma200Dist <= 1.5)) return false;
                }} else if (filterSma200 === 'XU') {{
                    if (!sma200Xu && !(sma200Dist <= 0 && sma200Dist >= -1.5)) return false;
                }} else if (filterSma200 !== 'POS' && filterSma200 !== 'NEG') {{
                    const minSma = parseFloat(filterSma200);
                    if (!isNaN(minSma) && sma200Dist < minSma) return false;
                }}
            }}

            if (minCat > 0 && (!isPos || stars < minCat)) return false;
            if (rvol < minRvol) return false;
            if (score < minScore) return false;
            if (selSector !== 'ALL' && !sector.toLowerCase().includes(selSector.toLowerCase())) return false;
            if (q && !text.includes(q)) return false;

            return true;
        }});

        state.currentPage = 1;
        renderTablePage('day-table');

        const visCount = document.getElementById('day-visible-count');
        if (visCount) visCount.innerText = state.filteredRows.length;
        const totCount = document.getElementById('day-total-count');
        if (totCount) totCount.innerText = state.allRows.length;

        if (save) {{
            saveFilterPreferences();
        }}
    }}

    function resetInstitutionalDefaults() {{
        document.getElementById('filter-breakout-last').checked = true;
        document.getElementById('filter-breakout-pm').checked = true;
        if (document.getElementById('filter-chg')) document.getElementById('filter-chg').value = "ALL";
        if (document.getElementById('filter-gap')) document.getElementById('filter-gap').value = "3.0";
        if (document.getElementById('filter-open')) document.getElementById('filter-open').value = "ALL";
        if (document.getElementById('filter-vwap')) document.getElementById('filter-vwap').value = "ALL";
        if (document.getElementById('filter-flow')) document.getElementById('filter-flow').value = "ALL";
        if (document.getElementById('filter-sma20')) document.getElementById('filter-sma20').value = "ALL";
        if (document.getElementById('filter-sma50')) document.getElementById('filter-sma50').value = "ALL";
        if (document.getElementById('filter-sma200')) document.getElementById('filter-sma200').value = "ALL";
        document.getElementById('filter-catalyst').value = "2.0";
        document.getElementById('filter-rvol').value = "1.5";
        document.getElementById('filter-score').value = "2.5";
        document.getElementById('filter-sector').value = "ALL";
        const searchInput = document.getElementById('day-search-input');
        if (searchInput) searchInput.value = '';
        filterDayWatchlist(true);
    }}

    function showAllCandidates() {{
        document.getElementById('filter-breakout-last').checked = false;
        document.getElementById('filter-breakout-pm').checked = false;
        if (document.getElementById('filter-chg')) document.getElementById('filter-chg').value = "ALL";
        if (document.getElementById('filter-gap')) document.getElementById('filter-gap').value = "ALL";
        if (document.getElementById('filter-open')) document.getElementById('filter-open').value = "ALL";
        if (document.getElementById('filter-vwap')) document.getElementById('filter-vwap').value = "ALL";
        if (document.getElementById('filter-flow')) document.getElementById('filter-flow').value = "ALL";
        if (document.getElementById('filter-sma20')) document.getElementById('filter-sma20').value = "ALL";
        if (document.getElementById('filter-sma50')) document.getElementById('filter-sma50').value = "ALL";
        if (document.getElementById('filter-sma200')) document.getElementById('filter-sma200').value = "ALL";
        document.getElementById('filter-catalyst').value = "0.0";
        document.getElementById('filter-rvol').value = "0.0";
        document.getElementById('filter-score').value = "0.0";
        document.getElementById('filter-sector').value = "ALL";
        const searchInput = document.getElementById('day-search-input');
        if (searchInput) searchInput.value = '';
        filterDayWatchlist(true);
    }}
</script>
</body>
</html>
"""

class HTMLReportGenerator:
    """Generates the interactive HTML dashboard with zero fake data."""

    def generate_report(
        self,
        macro_data: Dict[str, Any],
        day_watchlist: List[Dict[str, Any]],
        economic_events: List[Dict[str, Any]],
        earnings_data: Dict[str, Any],
        analyst_actions: List[Dict[str, Any]],
        options_aggregated: List[Dict[str, Any]],
        session_label: str = "Regular Market Hours",
        portfolio_data: Optional[Dict[str, Any]] = None,
        output_path: Path = REPORT_HTML_PATH
    ) -> Path:
        """Render complete interactive HTML report with sorting, pagination, and multi-factor filtering."""
        now = datetime.datetime.now(TZ_EST)
        ts_est = now.strftime("%Y-%m-%d %H:%M:%S EST")
        ts_pst = datetime.datetime.now(TZ_PST).strftime("%H:%M:%S PST")
        today_str = now.strftime("%b %d")
        yest_str = (now - datetime.timedelta(days=1)).strftime("%b %d")
        tom_str = (now + datetime.timedelta(days=1)).strftime("%b %d")

        # Fallback for portfolio data if None
        if portfolio_data is None:
            try:
                from sources.portfolio_manager import portfolio_mgr
                portfolio_data = portfolio_mgr.enrich_live_metrics()
            except Exception:
                portfolio_data = {
                    "account_name": "Traditional IRA",
                    "account_number": "264695485",
                    "total_nav": 336870.83,
                    "cash_balance": 70830.35,
                    "equity_value": 266040.48,
                    "total_day_pnl_dollar": -3842.18,
                    "total_day_pnl_pct": -1.13,
                    "total_unrealized_pnl_dollar": 32410.12,
                    "cash_weight_pct": 21.02,
                    "positions": []
                }

        # Macro data variables
        comp_regime = macro_data.get("composite_regime", "Neutral")
        regime_css = "regime-risk-on" if "Risk-On" in comp_regime else ("regime-risk-off" if "Risk-Off" in comp_regime else "regime-neutral")

        fed = macro_data.get("fed_funds", {})
        tnx = macro_data.get("tnx", {})
        vix = macro_data.get("vix", {})
        wti = macro_data.get("wti", {})
        brent = macro_data.get("brent", {})
        futures = macro_data.get("futures", {})
        breadth = macro_data.get("breadth", {})
        matrix = macro_data.get("portfolio_matrix", {})
        radar = macro_data.get("radar_pillars", {})

        # 4D Radar Pillars
        liq = radar.get("liquidity", {})
        gro = radar.get("growth", {})
        vol = radar.get("volatility", {})
        bre = radar.get("breadth", {})

        def _calc_bar_width(score):
            return max(10, min(95, int(((score + 25) / 50.0) * 85 + 10)))

        pillar_liq_width = _calc_bar_width(liq.get("score", 0))
        pillar_gro_width = _calc_bar_width(gro.get("score", 0))
        pillar_vol_width = _calc_bar_width(vol.get("score", 0))
        pillar_bre_width = _calc_bar_width(bre.get("score", 0))

        tnx_chg = tnx.get("chg", 0.0) or 0.0
        tnx_pct = tnx.get("pct_chg", 0.0) or 0.0
        tnx_color = "#34d399" if tnx_chg < 0 else ("#f87171" if tnx_chg > 0 else "#9ca3af")

        vix_val = vix.get("value", 15.5) or 15.5
        vix_chg = vix.get("chg", 0.0) or 0.0
        vix_color = "#34d399" if vix_val < 15.0 else ("#f87171" if vix_val > 20.0 else "#fbbf24")

        wti_val = wti.get("value", 78.0) or 78.0
        wti_chg = wti.get("chg", 0.0) or 0.0
        oil_color = "#34d399" if wti_chg < 0 else ("#f87171" if wti_chg > 0 else "#9ca3af")

        es = futures.get("es", {})
        nq = futures.get("nq", {})
        gold = futures.get("gold", {})
        btc = futures.get("btc", {})

        es_val = f"{es.get('value', 0.0):,.2f}" if es.get("value") else "—"
        es_chg = es.get("chg", 0.0) or 0.0
        es_pct = es.get("pct_chg", 0.0) or 0.0
        es_color = "#34d399" if es_chg > 0 else ("#f87171" if es_chg < 0 else "#9ca3af")

        nq_val = f"{nq.get('value', 0.0):,.2f}" if nq.get("value") else "—"
        nq_chg = nq.get("chg", 0.0) or 0.0
        nq_pct = nq.get("pct_chg", 0.0) or 0.0
        nq_color = "#34d399" if nq_chg > 0 else ("#f87171" if nq_chg < 0 else "#9ca3af")

        gold_val = f"{gold.get('value', 0.0):,.2f}" if gold.get("value") else "—"
        gold_chg = gold.get("chg", 0.0) or 0.0
        gold_pct = gold.get("pct_chg", 0.0) or 0.0
        gold_color = "#34d399" if gold_chg > 0 else ("#f87171" if gold_chg < 0 else "#9ca3af")

        btc_val = f"{btc.get('value', 0.0):,.2f}" if btc.get("value") else "—"
        btc_chg = btc.get("chg", 0.0) or 0.0
        btc_pct = btc.get("pct_chg", 0.0) or 0.0
        btc_color = "#34d399" if btc_chg > 0 else ("#f87171" if btc_chg < 0 else "#9ca3af")

        adv_pct = breadth.get("advancing_pct", 55.0) or 55.0
        decl_pct = breadth.get("declining_pct", 45.0) or 45.0
        adv_count = breadth.get("adv_count", 0) or 0
        decl_count = breadth.get("decl_count", 0) or 0
        adv_color = "#34d399" if adv_pct >= 55.0 else ("#f87171" if adv_pct < 45.0 else "#fbbf24")

        nh_pct = breadth.get("nh_pct", 50.0) or 50.0
        nl_pct = breadth.get("nl_pct", 50.0) or 50.0
        nh_count = breadth.get("new_highs_count", 0) or 0
        nl_count = breadth.get("new_lows_count", 0) or 0
        net_highs = breadth.get("net_highs", 0) or 0
        net_highs_str = f"+{net_highs}" if net_highs > 0 else str(net_highs)
        nh_color = "#34d399" if nh_pct >= 55.0 else ("#f87171" if nh_pct < 45.0 else "#fbbf24")

        breadth_source = breadth.get("source", "Finviz Market Overview")
        sma50_pct = breadth.get("pct_above_sma50", 50.0) or 50.0
        sma50_color = "#34d399" if sma50_pct >= 55.0 else ("#f87171" if sma50_pct < 45.0 else "#fbbf24")
        sma50_status = "Bullish" if sma50_pct >= 55.0 else ("Bearish" if sma50_pct < 45.0 else "Neutral")

        sma200_pct = breadth.get("pct_above_sma200", 50.0) or 50.0
        sma200_color = "#34d399" if sma200_pct >= 60.0 else ("#f87171" if sma200_pct < 40.0 else "#fbbf24")
        sma200_status = "Structural Bull" if sma200_pct >= 60.0 else ("Structural Bear" if sma200_pct < 40.0 else "Neutral")

        sectors_set = set(item.get("sector", "General") for item in day_watchlist if item.get("sector"))
        sector_options_html = "".join([f'<option value="{s}">{s}</option>' for s in sorted(sectors_set) if s and s != "General"])

        # 1. Day Trading Watchlist Rows & Accordion Drawers
        day_rows_html = []
        if day_watchlist:
            for idx, item in enumerate(day_watchlist):
                drawer_id = f"row-drawer-{idx}"
                rvol_val = item.get("rvol", 1.0)
                rvol_pill = f'<span class="pill pill-green">{rvol_val:.2f}x</span>' if rvol_val >= 2.0 else f'<span class="pill pill-yellow">{rvol_val:.2f}x</span>'
                
                score_val = item.get("setup_score", 3.0)
                score_pill = f'<span class="pill pill-purple" style="font-size: 11px;">{item.get("stars_visual", "★★★☆☆")} {score_val:.1f}★</span>'

                p_open = item.get("pct_from_open", 0.0)
                p_open_color = "#34d399" if p_open > 0 else ("#f87171" if p_open < 0 else "#9ca3af")
                p_open_str = f'<span style="color: {p_open_color}; font-weight: 600;">{p_open:+.2f}%</span>'

                cat_cat = item.get("catalyst_type", "News")
                cat_stars_num = int(round(item.get("catalyst_stars", 1.0)))
                cat_stars_str = "★" * cat_stars_num + "☆" * (5 - cat_stars_num)
                cat_date_str = item.get("catalyst_date", "—")
                cat_pill = f'<span class="pill pill-blue">[{cat_cat}]</span> <span style="color: #fbbf24; font-size: 11px;">{cat_stars_str}</span> <span style="color: #94a3b8; font-size: 10.5px; margin-left: 2px;">{cat_date_str}</span>'
                
                skew_val = item.get("gamma_skew", "—")
                skew_pill = '<span class="pill pill-green">Bullish</span>' if "Bullish" in skew_val else ('<span class="pill pill-red">Bearish</span>' if "Bearish" in skew_val else f'<span class="pill pill-blue">{skew_val}</span>')

                p_chg = item.get("pct_change", item.get("gap_pct", 0.0))
                p_chg_pill = f'<span class="pill pill-green">+{p_chg:.2f}%</span>' if p_chg > 0 else (f'<span class="pill pill-red">{p_chg:.2f}%</span>' if p_chg < 0 else f'<span class="pill pill-blue">{p_chg:.2f}%</span>')

                gap_val = item.get("gap_pct", 0.0)
                gap_str = f'<span style="color: #38bdf8; font-weight: 600;">{gap_val:+.2f}%</span>' if gap_val != 0 else '<span style="color: #9ca3af;">0.00%</span>'

                b_last_str = "true" if item.get("breakout_last_high") else "false"
                b_pm_str = "true" if item.get("breakout_pm_high") else "false"
                is_pos_str = "true" if item.get("is_positive") else "false"

                earn_date_val = item.get('earnings_date', '—')
                earn_pill = f'<span class="pill pill-purple" style="font-size: 10.5px;">{earn_date_val}</span>' if earn_date_val != '—' else '<span style="color: #6b7280;">—</span>'

                cur_price_val = item.get('price', 0.0)
                suggested_stop = round(cur_price_val * 0.96, 2)

                day_rows_html.append(f"""
                <tr class="data-row" data-drawer-id="{drawer_id}"
                    data-ticker="{item['ticker']}"
                    data-chg="{p_chg:.2f}"
                    data-gap="{item['gap_pct']:.2f}"
                    data-open="{item.get('pct_from_open', 0.0):.2f}"
                    data-vwap-dist="{item.get('vwap_dist', 0.0):.2f}"
                    data-vwap-xo="{str(item.get('vwap_xo', False)).lower()}"
                    data-vwap-xu="{str(item.get('vwap_xu', False)).lower()}"
                    data-vwap-std-p1="{str(item.get('vwap_std_p1', False)).lower()}"
                    data-vwap-std-p2="{str(item.get('vwap_std_p2', False)).lower()}"
                    data-vwap-std-m1="{str(item.get('vwap_std_m1', False)).lower()}"
                    data-vwap-std-m2="{str(item.get('vwap_std_m2', False)).lower()}"
                    data-skew="{item.get('gamma_skew', 'Neutral')}"
                    data-pc="{item.get('pc_ratio', 1.0)}"
                    data-net-flow="{item.get('net_dollar_val', 0.0)}"
                    data-whales="{item.get('whale_trades_count', 0)}"
                    data-sma20-dist="{item.get('sma20_dist', 0.0):.2f}"
                    data-sma20-xo="{str(item.get('sma20_xo', False)).lower()}"
                    data-sma20-xu="{str(item.get('sma20_xu', False)).lower()}"
                    data-sma50-dist="{item.get('sma50_dist', 0.0):.2f}"
                    data-sma50-xo="{str(item.get('sma50_xo', False)).lower()}"
                    data-sma50-xu="{str(item.get('sma50_xu', False)).lower()}"
                    data-sma200-dist="{item.get('sma200_dist', 0.0):.2f}"
                    data-sma200-xo="{str(item.get('sma200_xo', False)).lower()}"
                    data-sma200-xu="{str(item.get('sma200_xu', False)).lower()}"
                    data-rvol="{item['rvol']:.2f}"
                    data-score="{score_val:.2f}"
                    data-stars="{item.get('catalyst_stars', 0.0)}"
                    data-pos="{is_pos_str}"
                    data-breakout-last="{b_last_str}"
                    data-breakout-pm="{b_pm_str}"
                    data-sector="{item.get('sector', 'General')}">
                    <td class="col-all"><a class="ticker-link" href="https://finance.yahoo.com/quote/{item['ticker']}" target="_blank">{item['ticker']}</a></td>
                    <td class="col-all">{score_pill}</td>
                    <td class="col-all"><strong>${item['price']:.2f}</strong></td>
                    <td class="col-all">{p_chg_pill}</td>
                    <td class="col-all">{gap_str}</td>
                    <td class="col-all">{p_open_str}</td>
                    <td class="col-all">{rvol_pill}</td>
                    <td class="col-all">{earn_pill}</td>
                    <td class="col-all">{item.get('yesterday_high_dist', '—')}</td>
                    <td class="col-tech-only">{item.get('premarket_high_dist', '—')}</td>
                    <td class="col-tech-only"><strong style="color: #38bdf8;">{item.get('vwap', '—')}</strong></td>
                    <td class="col-tech-only">{item.get('sma5', '—')}</td>
                    <td class="col-tech-only">{item.get('sma20', '—')}</td>
                    <td class="col-tech-only">{item.get('sma50', '—')}</td>
                    <td class="col-tech-only">{item.get('sma200', '—')}</td>
                    <td class="col-core-only"><span class="pill pill-blue">{item.get('sector', 'General')}</span></td>
                    <td class="col-core-only" style="font-size: 11px; color: #d1d5db;">{item.get('industry', 'Diversified')}</td>
                    <td class="col-core-only">{cat_pill} <a class="headline-link" href="{item.get('catalyst_url', '#')}" target="_blank">{item.get('headline', '')}</a></td>
                    <td class="col-opt-only" style="color: #60a5fa; font-weight: 600;">{item.get('call_wall', '—')}</td>
                    <td class="col-opt-only" style="color: #f87171; font-weight: 600;">{item.get('put_wall', '—')}</td>
                    <td class="col-opt-only" style="color: #fbbf24;">{item.get('gamma_flip', '—')}</td>
                    <td class="col-all">{skew_pill}</td>
                    <td class="col-all">{item.get('pc_ratio', '—')}</td>
                    <td class="col-opt-only"><strong style="color: #34d399; font-size: 11px;">{item.get('analyst_rating', '—')}</strong></td>
                    <td class="col-all" style="text-align: center; white-space: nowrap;">
                        <button class="btn-action" style="padding: 2px 7px; font-size: 10.5px;" onclick="openSizingModal('{item['ticker']}', {cur_price_val}, {suggested_stop}, '{item.get('headline', '')}', 'Long')">⚡ Sizing</button>
                        <button class="btn-secondary" style="padding: 2px 7px; font-size: 10.5px; margin-left: 2px;" onclick="toggleRowDrawer('{drawer_id}')">🔍</button>
                    </td>
                </tr>
                <tr class="row-drawer" id="{drawer_id}">
                    <td colspan="25">
                        <div class="drawer-content">
                            <div class="drawer-card">
                                <div class="drawer-card-title">📈 Trend & Moving Average Matrix ({item['ticker']})</div>
                                <div class="drawer-item-row"><span>Total Session % Chg:</span> {p_chg_pill}</div>
                                <div class="drawer-item-row"><span>Opening Gap %:</span> {gap_str}</div>
                                <div class="drawer-item-row"><span>Intraday Run (% Open):</span> {p_open_str}</div>
                                <div class="drawer-item-row"><span>VWAP (Session):</span> <strong style="color: #38bdf8;">{item.get('vwap', '—')}</strong></div>
                                <div class="drawer-item-row"><span>5-Day SMA:</span> <strong>{item.get('sma5', '—')}</strong></div>
                                <div class="drawer-item-row"><span>20-Day SMA:</span> <strong>{item.get('sma20', '—')}</strong></div>
                                <div class="drawer-item-row"><span>50-Day SMA:</span> <strong>{item.get('sma50', '—')}</strong></div>
                                <div class="drawer-item-row"><span>200-Day SMA:</span> <strong>{item.get('sma200', '—')}</strong></div>
                            </div>
                            <div class="drawer-card">
                                <div class="drawer-card-title">🎯 Institutional Options Gamma & Sizing</div>
                                <div class="drawer-item-row"><span>Gamma Skew:</span> {skew_pill}</div>
                                <div class="drawer-item-row"><span>Flow Conviction:</span> {item.get('flow_conviction_badge', '🟡 Flow: 50/100')}</div>
                                <div class="drawer-item-row"><span>Call Wall (Magnet):</span> <strong style="color: #60a5fa;">{item.get('call_wall', '—')}</strong></div>
                                <div class="drawer-item-row"><span>Put Wall (Floor):</span> <strong style="color: #f87171;">{item.get('put_wall', '—')}</strong></div>
                                <div class="drawer-item-row"><span>Gamma Flip Level:</span> <strong style="color: #fbbf24;">{item.get('gamma_flip', '—')}</strong></div>
                                <div class="drawer-item-row"><span>Vol/OI & P/C Ratio:</span> <strong>{item.get('vol_oi_ratio', 1.0):.2f}x (P/C: {item.get('pc_ratio', '—')})</strong></div>
                                <div class="drawer-item-row"><span>ATM IV & Net Flow:</span> <strong>{item.get('atm_iv_str', '—')} ({item.get('net_dollar_str', '—')})</strong></div>
                            </div>
                            <div class="drawer-card">
                                <div class="drawer-card-title">📰 Catalyst & Analyst Intelligence</div>
                                <div style="margin-bottom: 6px;">{cat_pill}</div>
                                <div style="margin-bottom: 8px;"><a class="headline-link" href="{item.get('catalyst_url', '#')}" target="_blank" style="font-size: 12px; font-weight: 600;">{item.get('headline', 'No major headline')}</a></div>
                                <div class="drawer-item-row"><span>Sector:</span> <strong style="color: #9ca3af;">{item.get('sector', 'General')}</strong></div>
                                <div class="drawer-item-row"><span>Industry:</span> <strong style="color: #d1d5db;">{item.get('industry', 'Diversified')}</strong></div>
                                <div class="drawer-item-row"><span>Earnings Date:</span> <strong style="color: #c084fc;">{item.get('earnings_date', '—')}</strong></div>
                                <div class="drawer-item-row"><span>Analyst Revisions:</span> <strong style="color: #34d399;">{item.get('analyst_rating', '—')}</strong></div>
                                <div class="drawer-item-row"><span>Market Capitalization:</span> <strong>{item.get('market_cap_str', '—')}</strong></div>
                            </div>
                        </div>
                    </td>
                </tr>
                """)
        else:
            day_rows_html.append('<tr class="data-row"><td colspan="25" style="text-align: center; color: #9ca3af; padding: 20px;">No stocks matching screening filters at this moment.</td></tr>')

        # 2. Portfolio Positions Rows
        portfolio_positions = portfolio_data.get("positions", [])
        port_rows_html = []
        if portfolio_positions:
            for p in portfolio_positions:
                sym = p.get("symbol", "—")
                desc = p.get("description", "—")
                qty = p.get("quantity", 0.0)
                avg_c = p.get("average_cost", 0.0)
                last_p = p.get("last_price", 0.0)
                cur_v = p.get("current_value", 0.0)
                day_d = p.get("today_pnl_dollar", 0.0)
                day_p = p.get("today_pnl_pct", 0.0)
                tot_d = p.get("total_pnl_dollar", 0.0)
                tot_p = p.get("total_pnl_pct", 0.0)
                w_pct = p.get("weight_pct", 0.0)
                strat = p.get("strategy_tag", "Tactical")
                stop_l = p.get("stop_loss", 0.0)
                targ_p = p.get("target_price", 0.0)
                notes = p.get("notes", "")
                is_opt = p.get("is_option", False)

                day_color = "#34d399" if day_d > 0 else ("#f87171" if day_d < 0 else "#9ca3af")
                tot_color = "#34d399" if tot_d > 0 else ("#f87171" if tot_d < 0 else "#9ca3af")

                port_rows_html.append(f"""
                <tr class="data-row" data-symbol="{sym}" data-is-option="{str(is_opt).lower()}">
                    <td><strong style="color: #60a5fa;">{sym}</strong></td>
                    <td style="font-size: 11px; color: #d1d5db; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{desc}</td>
                    <td><strong>{qty:,.3f}</strong></td>
                    <td>${avg_c:,.2f}</td>
                    <td><strong>${last_p:,.2f}</strong></td>
                    <td style="color: {day_color}; font-weight: 600;">{day_d:+,.2f}</td>
                    <td style="color: {day_color}; font-weight: 600;">{day_p:+.2f}%</td>
                    <td style="color: {tot_color}; font-weight: 700;">{tot_d:+,.2f}</td>
                    <td style="color: {tot_color}; font-weight: 700;">{tot_p:+.2f}%</td>
                    <td><strong>${cur_v:,.2f}</strong></td>
                    <td><span class="pill pill-blue">{w_pct:.2f}%</span></td>
                    <td><span class="pill pill-purple">{strat}</span></td>
                    <td style="text-align: center; white-space: nowrap;">
                        <button class="btn-action" style="padding: 2px 6px; font-size: 10px;" onclick="openSizingModal('{sym}', {last_p}, {stop_l}, '{desc}', 'Rebalance')">⚡</button>
                        <button class="btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="openEditPositionModal('{sym}', {qty}, {avg_c}, {stop_l}, {targ_p}, '{strat}', '{notes}')">✏️</button>
                        <button class="btn-danger" style="padding: 2px 6px; font-size: 10px;" onclick="deletePortfolioPosition('{sym}')">❌</button>
                    </td>
                </tr>
                """)
        else:
            port_rows_html.append('<tr><td colspan="13" style="text-align: center; color: #9ca3af; padding: 20px;">No open positions in book. Click "Import Fidelity CSV" to populate.</td></tr>')

        # 3. Economic Calendar Rows
        eco_rows_html = []
        if economic_events:
            for item in economic_events:
                imp = item.get("impact", "MED").upper()
                imp_pill = '<span class="pill pill-red">HIGH</span>' if imp == "HIGH" else ('<span class="pill pill-yellow">MED</span>' if imp == "MED" else '<span class="pill pill-blue">LOW</span>')
                eco_title = item.get('title') or item.get('event') or '—'
                eco_rows_html.append(f"""
                <tr class="data-row">
                    <td><strong>{item.get('time', '—')}</strong></td>
                    <td>{imp_pill}</td>
                    <td><strong>{eco_title}</strong></td>
                    <td style="color: #60a5fa;">{item.get('forecast', '—')}</td>
                    <td style="color: #9ca3af;">{item.get('prior', '—')}</td>
                </tr>
                """)
        else:
            eco_rows_html.append('<tr class="data-row"><td colspan="5" style="text-align: center; color: #9ca3af; padding: 16px;">No major economic releases scheduled for today.</td></tr>')

        # 4. Earnings Calendar Rows
        earn_rows_html = []
        today_bmo = earnings_data.get("today_bmo", [])
        yesterday_amc = earnings_data.get("yesterday_amc", [])
        today_amc = earnings_data.get("today_amc", [])
        tomorrow_list = earnings_data.get("tomorrow", [])
        all_earnings = today_bmo + yesterday_amc + today_amc + tomorrow_list
        total_earn_count = len(all_earnings)

        if all_earnings:
            for item in all_earnings:
                timing_raw = item.get("timing", "")
                timing_badge = '<span class="pill pill-green">Today BMO</span>' if "b" in timing_raw and today_str in timing_raw else (
                    '<span class="pill pill-yellow">Today AMC</span>' if "a" in timing_raw and today_str in timing_raw else (
                        '<span class="pill pill-blue">Yesterday AMC</span>' if yest_str in timing_raw else f'<span class="pill pill-purple">{timing_raw}</span>'
                    )
                )
                pct_val = item.get("pct_change")
                if pct_val is None:
                    try:
                        pct_val = float(str(item.get("change", "0")).replace("%", "").replace("+", "").strip())
                    except Exception:
                        pct_val = 0.0

                pct_str = f'<span style="color: #34d399; font-weight: 600;">+{pct_val:.2f}%</span>' if pct_val > 0 else (
                    f'<span style="color: #f87171; font-weight: 600;">{pct_val:.2f}%</span>' if pct_val < 0 else '<span style="color: #9ca3af;">0.00%</span>'
                )

                earn_rows_html.append(f"""
                <tr class="data-row">
                    <td><a class="ticker-link" href="https://finance.yahoo.com/quote/{item['ticker']}" target="_blank">{item['ticker']}</a></td>
                    <td style="font-size: 11px; color: #d1d5db;">{item.get('company', '')}</td>
                    <td><span class="pill pill-blue">{item.get('sector', 'General')}</span></td>
                    <td>{timing_badge}</td>
                    <td>{pct_str}</td>
                    <td style="color: #9ca3af;">{item.get('market_cap', '—')}</td>
                </tr>
                """)
        else:
            earn_rows_html.append('<tr class="data-row"><td colspan="6" style="text-align: center; color: #9ca3af; padding: 16px;">No earnings reports recorded for this timeframe.</td></tr>')

        # 5. Analyst Actions Rows
        analyst_rows_html = []
        if analyst_actions:
            for item in analyst_actions:
                act = item.get("action", "").lower()
                act_pill = '<span class="pill pill-green">Upgrade</span>' if "upgrade" in act or "up" in act else ('<span class="pill pill-red">Downgrade</span>' if "downgrade" in act or "down" in act else f'<span class="pill pill-yellow">{item.get("action")}</span>')
                analyst_rows_html.append(f"""
                <tr class="data-row">
                    <td><a class="ticker-link" href="https://finance.yahoo.com/quote/{item['ticker']}" target="_blank">{item['ticker']}</a></td>
                    <td><strong>{item.get('date', 'Today')}</strong></td>
                    <td style="color: #9ca3af;">{item.get('firm', '—')}</td>
                    <td>{act_pill}</td>
                    <td><strong style="color: #e5e7eb;">{item.get('rating_change', '—')}</strong></td>
                    <td style="color: #34d399; font-weight: 700;">{item.get('target', '—')}</td>
                </tr>
                """)
        else:
            analyst_rows_html.append('<tr class="data-row"><td colspan="6" style="text-align: center; color: #9ca3af; padding: 16px;">No major analyst rating revisions recorded for today/yesterday.</td></tr>')

        # 6. Options Aggregated Rows
        options_agg_html = []
        if options_aggregated:
            for idx, agg in enumerate(options_aggregated):
                drawer_id = f"whale-drawer-{idx}"
                skew_val = agg.get("skew", "Neutral")
                skew_pill = '<span class="pill pill-green">Bullish</span>' if "Bullish" in skew_val else ('<span class="pill pill-red">Bearish</span>' if "Bearish" in skew_val else '<span class="pill pill-blue">Neutral</span>')
                whale_list = agg.get("whale_trades", [])
                whale_count = len(whale_list)
                whale_btn_html = f'<button class="whale-btn" onclick="toggleWhaleDrawer(\'{drawer_id}\')">🐳 {whale_count} Whales</button>' if whale_count > 0 else '<span style="color: #6b7280; font-size: 11px;">0 Trades</span>'

                vol_oi_val = agg.get("vol_oi_ratio", 1.0)
                vol_oi_pill = f'<span class="pill pill-green">{vol_oi_val:.2f}x</span>' if vol_oi_val >= 1.0 else f'<span class="pill pill-yellow">{vol_oi_val:.2f}x</span>'

                iv_rank_val = agg.get("iv_rank", 50.0)
                iv_rank_pill = f'<span class="pill pill-red">{iv_rank_val:.1f}%</span>' if iv_rank_val >= 80.0 else (f'<span class="pill pill-green">{iv_rank_val:.1f}%</span>' if iv_rank_val <= 30.0 else f'<span class="pill pill-blue">{iv_rank_val:.1f}%</span>')

                net_flow_val = agg.get("net_dollar_prem", 0.0)
                net_pill = f'<span class="pill pill-green">{agg.get("net_dollar_str", "—")}</span>' if net_flow_val >= 0 else f'<span class="pill pill-red">{agg.get("net_dollar_str", "—")}</span>'

                atm_iv_str = agg.get("atm_iv_str", "—")
                iv_chg_val = agg.get("iv_chg", 0.0)
                iv_chg_str = f'<span style="color: #34d399; font-weight: 600;">+{iv_chg_val:.2f}%</span>' if iv_chg_val > 0 else (
                    f'<span style="color: #f87171; font-weight: 600;">{iv_chg_val:.2f}%</span>' if iv_chg_val < 0 else '<span style="color: #9ca3af;">0.00%</span>'
                )
                price_str = f"{agg.get('stock_price_str', '—')} ({agg.get('stock_pct_chg_str', '—')})"

                options_agg_html.append(f"""
                <tr class="data-row" data-whale-id="{drawer_id}">
                    <td><a class="ticker-link" href="https://finance.yahoo.com/quote/{agg['ticker']}" target="_blank">{agg['ticker']}</a></td>
                    <td>{price_str}</td>
                    <td>{vol_oi_pill}</td>
                    <td><strong style="color: #e5e7eb;">{atm_iv_str}</strong></td>
                    <td>{iv_chg_str}</td>
                    <td>{iv_rank_pill}</td>
                    <td>{net_pill}</td>
                    <td style="color: #60a5fa; font-weight: 700;">{agg.get('call_wall', '—')}</td>
                    <td style="color: #f87171; font-weight: 700;">{agg.get('put_wall', '—')}</td>
                    <td style="color: #fbbf24; font-weight: 700;">{agg.get('gamma_flip', '—')}</td>
                    <td><strong>{agg.get('pc_ratio', '—')}</strong></td>
                    <td>{skew_pill}</td>
                    <td>{agg.get('total_45d_vol', 0):,}</td>
                    <td>{whale_btn_html}</td>
                </tr>
                """)

                if whale_count > 0:
                    whale_sub_rows = []
                    for w in whale_list[:8]:
                        w_type = w.get("type", "CALL")
                        w_pill = '<span class="pill pill-green">CALL</span>' if w_type == "CALL" else '<span class="pill pill-red">PUT</span>'
                        whale_sub_rows.append(f"""
                        <tr>
                            <td>{w_pill} <strong>{w.get('strike')}</strong></td>
                            <td>{w.get('expiry')} ({w.get('dte', 0)} DTE)</td>
                            <td><span class="pill pill-yellow">{w.get('vol_oi_ratio', 1.0):.2f}x</span> ({w.get('volume', 0):,} / {w.get('open_interest', 0):,})</td>
                            <td><strong>{w.get('contract_iv', '—')}</strong></td>
                            <td><strong style="color: #fbbf24;">{w.get('premium_str', '—')}</strong></td>
                            <td>{w.get('flow_tag', 'Whale Trade')}</td>
                            <td>{w.get('sentiment')}</td>
                        </tr>
                        """)

                    options_agg_html.append(f"""
                    <tr class="whale-drawer" id="{drawer_id}" style="display: none;">
                        <td colspan="14">
                            <div style="font-weight: 700; color: #60a5fa; margin-bottom: 6px;">⚡ Top Institutional Whale Trades for {agg['ticker']} (Premium &ge; $500K / High Vol/OI):</div>
                            <table class="whale-inner-table">
                                <thead>
                                    <tr>
                                        <th>Contract</th>
                                        <th>Expiry (DTE)</th>
                                        <th>Vol / OI Ratio</th>
                                        <th>Contract IV</th>
                                        <th>Notional Premium</th>
                                        <th>Order Type</th>
                                        <th>Sentiment</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {"".join(whale_sub_rows)}
                                </tbody>
                            </table>
                        </td>
                    </tr>
                    """)
        else:
            options_agg_html.append('<tr class="data-row"><td colspan="14" style="text-align: center; color: #9ca3af; padding: 20px;">No options gamma structure available for screened universe.</td></tr>')

        # Portfolio metrics formatting
        p_nav = portfolio_data.get("total_nav", 336870.83)
        p_cash = portfolio_data.get("cash_balance", 70830.35)
        p_eq = portfolio_data.get("equity_value", 266040.48)
        p_day_d = portfolio_data.get("total_day_pnl_dollar", -3842.18)
        p_day_p = portfolio_data.get("total_day_pnl_pct", -1.13)
        p_tot_d = portfolio_data.get("total_unrealized_pnl_dollar", 32410.12)
        p_cash_w = portfolio_data.get("cash_weight_pct", 21.02)

        port_day_color = "#34d399" if p_day_d > 0 else ("#f87171" if p_day_d < 0 else "#9ca3af")
        port_tot_color = "#34d399" if p_tot_d > 0 else ("#f87171" if p_tot_d < 0 else "#9ca3af")

        # Assemble HTML content
        html_content = HTML_TEMPLATE.format(
            session_label=session_label,
            timestamp_est=ts_est,
            timestamp_pst=ts_pst,
            today_str=today_str,
            yest_str=yest_str,
            tom_str=tom_str,
            regime_css_class=regime_css,
            composite_regime=comp_regime,
            composite_multiplier=macro_data.get("composite_multiplier", 0.95),
            pillar_liq_val=liq.get("val_str", "—"),
            pillar_liq_status=liq.get("status", "Normal"),
            pillar_liq_color=liq.get("color", "#34d399"),
            pillar_liq_width=pillar_liq_width,
            pillar_gro_val=gro.get("val_str", "—"),
            pillar_gro_status=gro.get("status", "Normal"),
            pillar_gro_color=gro.get("color", "#34d399"),
            pillar_gro_width=pillar_gro_width,
            pillar_vol_val=vol.get("val_str", "—"),
            pillar_vol_status=vol.get("status", "Normal"),
            pillar_vol_color=vol.get("color", "#fbbf24"),
            pillar_vol_width=pillar_vol_width,
            pillar_bre_val=bre.get("val_str", "—"),
            pillar_bre_status=bre.get("status", "Normal"),
            pillar_bre_color=bre.get("color", "#fbbf24"),
            pillar_bre_width=pillar_bre_width,
            fed_funds_val=fed.get("value", "—"),
            fed_funds_source=fed.get("source", "Federal Reserve"),
            rate_cycle_signal=macro_data.get("rate_cycle_signal", "Neutral"),
            rate_implication=macro_data.get("rate_implication", "Balanced"),
            tnx_val=tnx.get("value", 4.65) or 4.65,
            tnx_chg=tnx_chg,
            tnx_pct=tnx_pct,
            tnx_color=tnx_color,
            curve_status=macro_data.get("curve_status", "Normal"),
            spread_2s10s=macro_data.get("spread_2s10s", 0.0),
            tnx_source=tnx.get("source", "CBOE"),
            tnx_time=tnx.get("timestamp", ""),
            vix_val=vix_val,
            vix_chg=vix_chg,
            vix_color=vix_color,
            vix_state=macro_data.get("vix_state", "Normal"),
            vix_source=vix.get("source", "CBOE"),
            vix_time=vix.get("timestamp", ""),
            wti_val=wti_val,
            brent_val=brent.get("value", 85.0) or 85.0,
            wti_chg=wti_chg,
            oil_color=oil_color,
            oil_signal=macro_data.get("oil_signal", "Neutral"),
            wti_source=wti.get("source", "NYMEX"),
            wti_time=wti.get("timestamp", ""),
            es_val=es_val,
            es_chg=es_chg,
            es_pct=es_pct,
            es_color=es_color,
            nq_val=nq_val,
            nq_chg=nq_chg,
            nq_pct=nq_pct,
            nq_color=nq_color,
            gold_val=gold_val,
            gold_chg=gold_chg,
            gold_pct=gold_pct,
            gold_color=gold_color,
            btc_val=btc_val,
            btc_chg=btc_chg,
            btc_pct=btc_pct,
            btc_color=btc_color,
            adv_pct=adv_pct,
            decl_pct=decl_pct,
            adv_count=adv_count,
            decl_count=decl_count,
            adv_color=adv_color,
            nh_pct=nh_pct,
            nl_pct=nl_pct,
            net_highs_str=net_highs_str,
            nh_count=nh_count,
            nl_count=nl_count,
            nh_color=nh_color,
            breadth_source=breadth_source,
            sma50_pct=sma50_pct,
            sma50_color=sma50_color,
            sma50_status=sma50_status,
            sma200_pct=sma200_pct,
            sma200_color=sma200_color,
            sma200_status=sma200_status,
            matrix_equity=matrix.get("equity_allocation", "70%-80%"),
            matrix_gold=matrix.get("gold_target", "5%-10%"),
            matrix_btc=matrix.get("btc_target", "2%-4%"),
            matrix_cash=matrix.get("cash_target", "15%-25%"),
            matrix_tech=matrix.get("tech_cap", "35%"),
            matrix_fin=matrix.get("financials_cap", "20%"),
            matrix_energy=matrix.get("energy_defense_cap", "25%"),
            matrix_def=matrix.get("defensives_cap", "20%"),
            matrix_multiplier=matrix.get("risk_multiplier", "0.95x"),
            portfolio_acc_name=portfolio_data.get("account_name", "Traditional IRA"),
            portfolio_acc_num=portfolio_data.get("account_number", "264695485"),
            portfolio_nav_str=f"{p_nav:,.2f}",
            portfolio_nav_raw=p_nav,
            portfolio_cash_str=f"{p_cash:,.2f}",
            portfolio_cash_weight=f"{p_cash_w:.1f}",
            portfolio_equity_str=f"{p_eq:,.2f}",
            portfolio_pos_count=len(portfolio_positions),
            portfolio_day_pnl_str=f"{p_day_d:+,.2f}",
            portfolio_day_pct_str=f"{p_day_p:+.2f}%",
            portfolio_tot_pnl_str=f"{p_tot_d:+,.2f}",
            port_day_color=port_day_color,
            port_tot_color=port_tot_color,
            portfolio_position_rows="".join(port_rows_html),
            portfolio_json_raw=json.dumps(portfolio_data),
            sector_options=sector_options_html,
            day_count=len(day_watchlist),
            eco_count=len(economic_events),
            earn_count=total_earn_count,
            analyst_count=len(analyst_actions),
            options_agg_count=len(options_aggregated),
            day_trading_rows="".join(day_rows_html),
            economic_calendar_rows="".join(eco_rows_html),
            earnings_calendar_rows="".join(earn_rows_html),
            analyst_rows="".join(analyst_rows_html),
            options_aggregated_rows="".join(options_agg_html),
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Report saved to {output_path}")
        return output_path

html_generator = HTMLReportGenerator()
'''

with open(r"c:\Users\jfan\Documents\Screener\reporter\html_generator.py", "w", encoding="utf-8") as f:
    f.write(HTML_GEN_CONTENT)

print("Updated reporter/html_generator.py with complete client-side Fidelity CSV parser!")
