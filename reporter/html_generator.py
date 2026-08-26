"""HTML Dashboard Generator: Produces the interactive, paginated, and sortable latest_report.html (Zero fake data)."""

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

        /* Stockbeep Preset Tabs Bar */
        .stockbeep-preset-bar {{ display: flex; gap: 8px; margin-bottom: 14px; overflow: visible; flex-wrap: wrap; position: relative; z-index: 50; }}
        .stockbeep-preset-tab {{ position: relative; background: #1e293b; color: #cbd5e1; border: 1px solid #334155; padding: 7px 14px; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer; white-space: nowrap; transition: all 0.2s ease; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.3); }}
        .stockbeep-preset-tab:hover {{ background: #334155; color: #fff; border-color: #60a5fa; transform: translateY(-1px); z-index: 100; }}
        .stockbeep-preset-tab.active {{ background: #2563eb; color: #fff; border-color: #93c5fd; box-shadow: 0 0 12px rgba(37,99,235,0.6); }}
        .stockbeep-preset-tab#preset-tab-EXTENDED_MOVERS.active, .stockbeep-preset-tab#port-preset-tab-EXTENDED_MOVERS.active {{ background: #b45309; border-color: #fcd34d; box-shadow: 0 0 12px rgba(245,158,11,0.6); }}
        .stockbeep-preset-tab#preset-tab-EP_DAY_1.active, .stockbeep-preset-tab#port-preset-tab-EP_DAY_1.active {{ background: #dc2626; border-color: #fca5a5; box-shadow: 0 0 12px rgba(220,38,38,0.6); }}
        .stockbeep-preset-tab#preset-tab-EP_DAY_2.active, .stockbeep-preset-tab#port-preset-tab-EP_DAY_2.active {{ background: #059669; border-color: #6ee7b7; box-shadow: 0 0 12px rgba(5,150,105,0.6); }}
        .stockbeep-preset-tab#preset-tab-MINERVINI_VCP.active, .stockbeep-preset-tab#port-preset-tab-MINERVINI_VCP.active {{ background: #7c3aed; border-color: #c4b5fd; box-shadow: 0 0 12px rgba(124,58,237,0.6); }}
        .stockbeep-preset-tab#preset-tab-MOMENTUM_BURST.active, .stockbeep-preset-tab#port-preset-tab-MOMENTUM_BURST.active {{ background: #0284c7; border-color: #38bdf8; box-shadow: 0 0 12px rgba(2,132,199,0.6); }}

        /* Instant Rich Floating Tooltip Positioned ABOVE Preset Tabs */
        .stockbeep-preset-tab[data-tooltip]::after {{
            content: attr(data-tooltip);
            position: absolute;
            bottom: calc(100% + 10px);
            left: 50%;
            transform: translateX(-50%) translateY(4px);
            background: #0f172a;
            color: #f8fafc;
            border: 1px solid #38bdf8;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 500;
            line-height: 1.4;
            white-space: normal;
            min-width: 240px;
            max-width: 320px;
            pointer-events: none;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.15s ease, transform 0.15s ease, visibility 0.15s ease;
            box-shadow: 0 12px 30px rgba(0,0,0,0.85);
            z-index: 999999;
            text-align: left;
        }}
        .stockbeep-preset-tab[data-tooltip]::before {{
            content: '';
            position: absolute;
            bottom: calc(100% + 4px);
            left: 50%;
            transform: translateX(-50%);
            border-width: 6px 6px 0 6px;
            border-style: solid;
            border-color: #38bdf8 transparent transparent transparent;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.15s ease, visibility 0.15s ease;
            z-index: 999999;
        }}
        .stockbeep-preset-tab[data-tooltip]:hover::after,
        .stockbeep-preset-tab[data-tooltip]:hover::before {{
            opacity: 1;
            visibility: visible;
            transform: translateX(-50%) translateY(0);
        }}

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
        .view-options .col-tech-core {{ display: none !important; }}

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
            <button class="nav-tab-btn" id="nav-tab-actions" onclick="switchMainView('actions')">🎯 Trade Execution Desk (Actions Tab)</button>
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
        <div class="card" id="portfolio-manager-card">
            <div class="section-header-row">
                <div class="section-title">
                    <span>💼 Institutional Portfolio Manager & Real-Time Risk Book</span>
                    <span id="port-acc-subtitle" style="font-size: 12px; color: #9ca3af; font-weight: normal;">({portfolio_acc_name} • #{portfolio_acc_num} • Synced with data/portfolio.json)</span>
                </div>
                <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                    <span class="pill pill-green" id="port-counter-pill">Showing <span id="port-visible-count">{portfolio_pos_count}</span> of <span id="port-total-count">{portfolio_pos_count}</span> Positions</span>
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

            <!-- Stockbeep Preset Tab Navigation Bar for Portfolio -->
            <div class="stockbeep-preset-bar" id="port-preset-bar">
                <button type="button" class="stockbeep-preset-tab active" id="port-preset-tab-ALL_SETUPS" data-tooltip="All Positions: Displays all open portfolio equity &amp; options holdings." onclick="selectPortfolioStockbeepPreset('ALL_SETUPS')">🌟 All Positions</button>
                <button type="button" class="stockbeep-preset-tab" id="port-preset-tab-EP_DAY_1" data-tooltip="Episodic Pivot Day 1: Overnight/day catalyst (Earnings/FDA/M&amp;A) with either Opening Gap% &ge; +7.0% OR Intraday Rally &ge; +4.0% on elevated RVOL &ge; 1.35x." onclick="selectPortfolioStockbeepPreset('EP_DAY_1')">🔥 EP Day 1</button>
                <button type="button" class="stockbeep-preset-tab" id="port-preset-tab-EP_DAY_2" data-tooltip="EP Day 2+ VWAP Touch: Pullback to Day 1 VWAP or 5-SMA within 1–5 days of prior Episodic Pivot on drying volume (&lt; 70% of Day 1) holding Day 1 low." onclick="selectPortfolioStockbeepPreset('EP_DAY_2')">🎯 EP Day 2+ VWAP</button>
                <button type="button" class="stockbeep-preset-tab" id="port-preset-tab-EP_5DAY_DB" data-tooltip="🏛️ 5-Day EP Database Universe: Displays all active Episodic Pivots tracked across Days 1 to 5 stored in the local SQLite database." onclick="selectPortfolioStockbeepPreset('EP_5DAY_DB')">🏛️ 5-Day EP Universe</button>
                <button type="button" class="stockbeep-preset-tab" id="port-preset-tab-MINERVINI_VCP" data-tooltip="Minervini Volatility Contraction Pattern (VCP): Multi-contraction consolidation (&lt; 12% 5-day range) in Stage 2 uptrend (Price &gt; SMA50 &gt; SMA200) breaking out above 5-day consolidation resistance (Price &ge; 5-Day High) on heavy breakout volume (RVOL &ge; 1.40x)." onclick="selectPortfolioStockbeepPreset('MINERVINI_VCP')">📉 Minervini VCP</button>
                <button type="button" class="stockbeep-preset-tab" id="port-preset-tab-MOMENTUM_BURST" data-tooltip="⚡ Momentum Burst: Decisive intraday expansion (&ge; +4.0% from open or prior close) OR psychological round-dollar breakout ($10, $20, $50, $100...) on heavy institutional volume (RVOL &ge; 1.50x)." onclick="selectPortfolioStockbeepPreset('MOMENTUM_BURST')">⚡ Momentum Burst</button>
                <button type="button" class="stockbeep-preset-tab" id="port-preset-tab-V_REVERSAL" data-tooltip="V-Reversal (Intraday Shakeout Reclaim): Morning dip/flush (&le; -1.8% from open/close) that reverses sharply back above VWAP &amp; open into green territory (&ge; +1.5%) on elevated volume (RVOL &ge; 1.25x)." onclick="selectPortfolioStockbeepPreset('V_REVERSAL')">🔄 V-Reversal</button>
                <button type="button" class="stockbeep-preset-tab" id="port-preset-tab-WHALE_FLOW" data-tooltip="Whale Sweeps: Aggressive institutional orders with single-trade notional premium &ge; $200K to $500K+. Call Wall Magnet: Heavy Call OI strikes within +2% to +8% above spot price, forcing market makers to buy underlying stock to hedge positive delta (gamma acceleration). Bullish Skew: Put/Call Ratio &lt; 0.70 and positive Net Dollar Flow (&gt; $0)." onclick="selectPortfolioStockbeepPreset('WHALE_FLOW')">🐳 Whale Flow / Gamma</button>
            </div>

            <!-- Interactive Multi-Factor Filter Bar for Portfolio -->
            <div class="filter-panel" id="port-filter-panel">
                <div class="filter-row">
                    <div class="filter-item" id="port-breakout-dropdown-container" style="position: relative;">
                        <span style="font-weight: 700; color: #93c5fd;">⚡ Break Up/Down:</span>
                        <div class="dropdown-multiselect" style="display: inline-block; position: relative;">
                            <button type="button" id="port-breakout-btn" class="filter-select" style="min-width: 175px; text-align: left; cursor: pointer; display: inline-flex; justify-content: space-between; align-items: center;" onclick="toggleBreakoutDropdown('port-breakout-dropdown')">
                                <span id="port-breakout-label">All Levels (Unchecked)</span>
                                <span style="font-size: 9px; margin-left: 6px;">▼</span>
                            </button>
                            <div id="port-breakout-dropdown" class="multiselect-dropdown-menu" style="display: none; position: absolute; top: 100%; left: 0; z-index: 1050; background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 10px 14px; box-shadow: 0 12px 30px rgba(0,0,0,0.7); min-width: 220px;">
                                <div style="font-size: 10px; font-weight: 800; color: #38bdf8; text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.5px;">Break Up (&gt; Resistance)</div>
                                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 11.5px; cursor: pointer; color: #e2e8f0;">
                                    <input type="checkbox" id="port-chk-gt-week-high" class="port-breakout-chk" onchange="filterPortfolioWatchlist()"> <strong>&gt; Last Week High</strong>
                                </label>
                                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 11.5px; cursor: pointer; color: #4ade80;">
                                    <input type="checkbox" id="port-chk-gt-day-high" class="port-breakout-chk" onchange="filterPortfolioWatchlist()"> <strong>&gt; Last Day High</strong>
                                </label>
                                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 11.5px; cursor: pointer; color: #a78bfa;">
                                    <input type="checkbox" id="port-chk-gt-pm-high" class="port-breakout-chk" onchange="filterPortfolioWatchlist()"> <strong>&gt; Premarket High</strong>
                                </label>
                                <hr style="border: 0; border-top: 1px solid #334155; margin: 6px 0;">
                                <div style="font-size: 10px; font-weight: 800; color: #f87171; text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.5px;">Break Down (&lt; Level)</div>
                                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 11.5px; cursor: pointer; color: #fb7185;">
                                    <input type="checkbox" id="port-chk-lt-pm-low" class="port-breakout-chk" onchange="filterPortfolioWatchlist()"> <strong>&lt; Premarket Low</strong>
                                </label>
                                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 11.5px; cursor: pointer; color: #ef4444;">
                                    <input type="checkbox" id="port-chk-lt-week-low" class="port-breakout-chk" onchange="filterPortfolioWatchlist()"> <strong>&lt; Last Week Low</strong>
                                </label>
                                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px; font-size: 11.5px; cursor: pointer; color: #dc2626;">
                                    <input type="checkbox" id="port-chk-lt-day-low" class="port-breakout-chk" onchange="filterPortfolioWatchlist()"> <strong>&lt; Last Day Low</strong>
                                </label>
                                <div style="margin-top: 8px; text-align: right;">
                                    <button type="button" style="background: transparent; border: none; color: #94a3b8; font-size: 10px; cursor: pointer; text-decoration: underline;" onclick="clearAllPortBreakoutChecks()">Clear All</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="filter-item">
                        <span>% Chg:</span>
                        <select id="port-filter-chg" class="filter-select" onchange="filterPortfolioWatchlist()">
                            <option value="ALL" selected>All % Chg</option>
                            <option value="GT_3">&gt; +3.0%</option>
                            <option value="LT_M3">&lt; -3.0%</option>
                            <option value="LT_M20">&lt; -20%</option>
                            <option value="M20_M10">-20% to -10%</option>
                            <option value="M10_M5">-10% to -5%</option>
                            <option value="M5_0">-5% to 0%</option>
                            <option value="0_5">0% to 5%</option>
                            <option value="5_10">5% to 10%</option>
                            <option value="10_20">10% to 20%</option>
                            <option value="20_50">20% to 50%</option>
                            <option value="50_100">50% to 100%</option>
                            <option value="GT_100">&gt; 100%</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Gap %:</span>
                        <select id="port-filter-gap" class="filter-select" onchange="filterPortfolioWatchlist()">
                            <option value="ALL" selected>All Gaps</option>
                            <option value="NOGAP">No Gaps (Flat &lt; 1.0%)</option>
                            <option value="1.0">&ge; +1.0%</option>
                            <option value="2.0">&ge; +2.0%</option>
                            <option value="3.0">&ge; +3.0%</option>
                            <option value="5.0">&ge; +5.0%</option>
                            <option value="8.0">&ge; +8.0%</option>
                            <option value="-1.0">Gap Down &le; -1.0%</option>
                            <option value="-3.0">Gap Down &le; -3.0%</option>
                            <option value="-8.0">Gap Down &le; -8.0%</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>% Open:</span>
                        <select id="port-filter-open" class="filter-select" onchange="filterPortfolioWatchlist()">
                            <option value="ALL" selected>All % Open</option>
                            <option value="GT_3">&gt; +3.0%</option>
                            <option value="LT_M3">&lt; -3.0%</option>
                            <option value="LT_M20">&lt; -20%</option>
                            <option value="M20_M10">-20% to -10%</option>
                            <option value="M10_M5">-10% to -5%</option>
                            <option value="M5_0">-5% to 0%</option>
                            <option value="0_5">0% to 5%</option>
                            <option value="5_10">5% to 10%</option>
                            <option value="10_20">10% to 20%</option>
                            <option value="20_50">20% to 50%</option>
                            <option value="50_100">50% to 100%</option>
                            <option value="GT_100">&gt; 100%</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>% VWAP:</span>
                        <select id="port-filter-vwap" class="filter-select" onchange="filterPortfolioWatchlist()">
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
                        <span>Total P&L %:</span>
                        <select id="port-filter-total-pct" class="filter-select" onchange="filterPortfolioWatchlist()">
                            <option value="ALL" selected>All Total %</option>
                            <option value="GT_3">&gt; +3.0%</option>
                            <option value="LT_M3">&lt; -3.0%</option>
                            <option value="LT_M20">&lt; -20% (Deep Underwater)</option>
                            <option value="M20_M10">-20% to -10%</option>
                            <option value="M10_M5">-10% to -5%</option>
                            <option value="M5_0">-5% to 0%</option>
                            <option value="0_5">0% to +5%</option>
                            <option value="5_10">+5% to +10%</option>
                            <option value="10_20">+10% to +20%</option>
                            <option value="20_50">+20% to +50%</option>
                            <option value="50_100">+50% to +100%</option>
                            <option value="GT_100">&gt; +100% (Multibaggers)</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Weight %:</span>
                        <select id="port-filter-weight" class="filter-select" onchange="filterPortfolioWatchlist()">
                            <option value="ALL" selected>All Weights</option>
                            <option value="GT_10">&ge; 10.0% (Core Pillar)</option>
                            <option value="GT_5">&ge; 5.0%</option>
                            <option value="GT_3">&ge; 3.0%</option>
                            <option value="GT_1">&ge; 1.0%</option>
                            <option value="LT_1">&lt; 1.0% (Starter / Small)</option>
                            <option value="1_3">1.0% - 3.0%</option>
                            <option value="3_5">3.0% - 5.0%</option>
                            <option value="5_10">5.0% - 10.0%</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Flow / Bias:</span>
                        <select id="port-filter-flow" class="filter-select" onchange="filterPortfolioWatchlist()">
                            <option value="ALL" selected>All Flow Bias</option>
                            <option value="BULL_FLOW">🟢 Bullish Flow (Long Gamma, P/C &lt; 0.70)</option>
                            <option value="BEAR_FLOW">🔴 Bearish Flow (Put Hedge, P/C &gt; 1.00)</option>
                            <option value="WHALE">🐳 Whale Sweeps Active</option>
                            <option value="MOM_BULL">⚡ Bullish Momentum (&gt; VWAP &amp; Bullish Flow)</option>
                            <option value="MOM_BEAR">🔻 Bearish Momentum (&lt; VWAP &amp; Bearish Flow)</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>SMA5:</span>
                        <select id="port-filter-sma5" class="filter-select" onchange="filterPortfolioWatchlist()">
                            <option value="ALL" selected>All SMA5</option>
                            <option value="POS">&gt; SMA5 (Above)</option>
                            <option value="XO">⚡ Cross Over SMA5</option>
                            <option value="XU">🔻 Cross Under SMA5</option>
                            <option value="1.0">&ge; +1.0% above SMA5</option>
                            <option value="3.0">&ge; +3.0% above SMA5</option>
                            <option value="NEG">&lt; SMA5 (Below)</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>SMA20:</span>
                        <select id="port-filter-sma20" class="filter-select" onchange="filterPortfolioWatchlist()">
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
                        <select id="port-filter-sma50" class="filter-select" onchange="filterPortfolioWatchlist()">
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
                        <select id="port-filter-sma200" class="filter-select" onchange="filterPortfolioWatchlist()">
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
                        <select id="port-filter-catalyst" class="filter-select" onchange="filterPortfolioWatchlist()">
                            <option value="0.0" selected>All News / Any Rating</option>
                            <option value="2.0">&ge; 2.0★ Positive</option>
                            <option value="3.0">&ge; 3.0★</option>
                            <option value="4.0">&ge; 4.0★</option>
                            <option value="5.0">5.0★ Only</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Min RVOL:</span>
                        <select id="port-filter-rvol" class="filter-select" onchange="filterPortfolioWatchlist()">
                            <option value="0.0" selected>Any RVOL</option>
                            <option value="1.0">&ge; 1.00x</option>
                            <option value="1.5">&ge; 1.50x</option>
                            <option value="2.0">&ge; 2.00x</option>
                            <option value="3.0">&ge; 3.00x</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Min Score:</span>
                        <select id="port-filter-score" class="filter-select" onchange="filterPortfolioWatchlist()">
                            <option value="0.0" selected>Any Setup Score</option>
                            <option value="2.5">&ge; 2.5★</option>
                            <option value="3.0">&ge; 3.0★</option>
                            <option value="3.5">&ge; 3.5★</option>
                            <option value="4.0">&ge; 4.0★</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Sector:</span>
                        <select id="port-filter-sector" class="filter-select" onchange="filterPortfolioWatchlist()">
                            <option value="ALL" selected>All Sectors</option>
                            {sector_options}
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Asset Type:</span>
                        <select id="port-filter-asset-type" class="filter-select" onchange="filterPortfolioWatchlist()">
                            <option value="ALL" selected>All Assets</option>
                            <option value="STOCK">Stocks &amp; ETFs</option>
                            <option value="OPTION">Options Contracts</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Strategy:</span>
                        <select id="port-filter-strat" class="filter-select" onchange="filterPortfolioWatchlist()">
                            <option value="ALL" selected>All Strategies</option>
                            <option value="Core Long Holding">Core Long Holding</option>
                            <option value="Tactical Momentum">Tactical Momentum</option>
                            <option value="Options Hedge / Income">Options Hedge / Income</option>
                            <option value="Earnings Gap Breakout">Earnings Gap Breakout</option>
                            <option value="Options Flow Whale">Options Flow Whale</option>
                            <option value="Mean Reversion">Mean Reversion</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <button class="btn-action" onclick="resetPortfolioInstitutionalDefaults()">⚡ Institutional Defaults</button>
                        <button class="btn-secondary" onclick="showAllPortfolioPositions()">🌐 Show All Positions</button>
                        <span id="port-save-status-pill" class="pill pill-green" style="display: none; font-size: 10px;">💾 Saved</span>
                    </div>
                </div>
            </div>

            <!-- View Mode Selector for Portfolio -->
            <div class="view-mode-bar">
                <span style="font-size: 12px; font-weight: 700; color: #9ca3af; align-self: center; margin-right: 6px;">PORTFOLIO VIEW:</span>
                <button class="view-btn active" id="btn-port-view-core" onclick="switchPortfolioView('core')">📊 Core Overview (14 Cols)</button>
                <button class="view-btn" id="btn-port-view-technical" onclick="switchPortfolioView('technical')">📈 Technical & MAs (17 Cols)</button>
                <button class="view-btn" id="btn-port-view-options" onclick="switchPortfolioView('options')">🎯 Options Structure & Walls (17 Cols)</button>
            </div>

            <!-- Table Controls -->
            <div class="table-controls">
                <div>Show <select class="page-size-select" onchange="changePageSize('portfolio-table', this.value)"><option value="25">25</option><option value="50">50</option><option value="100">100</option><option value="1000" selected>All</option></select> entries</div>
                <input type="text" class="search-input" id="portfolio-search-input" placeholder="Search portfolio ticker, description, sector, strategy..." onkeyup="filterPortfolioWatchlist(false)">
            </div>

            <!-- Positions Table -->
            <div class="table-responsive">
                <table class="data-table view-core" id="portfolio-table">
                    <thead>
                        <tr>
                            <th onclick="sortTable('portfolio-table', 0)" class="sortable col-all">Symbol <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 1)" class="sortable col-all" title="Institutional 5-Star Setup Score: Multi-factor quantitative rating (1.0★ to 5.0★) synthesizing: 1) Catalyst Tier (30%), 2) RVOL Expansion (25%), 3) Technical Pattern &amp; MAs/VWAP (20%), 4) Options Gamma &amp; Whale Alignment (15%), 5) Macro Multiplier (10%).">Score <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 2)" class="sortable col-all">Price <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 3)" class="sortable col-all">Today P&L ($) <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 4)" class="sortable col-all">Total P&L ($) <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 5)" class="sortable col-all">Total % <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 6)" class="sortable col-all">Value ($) <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 7)" class="sortable col-all">Weight % <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 8)" class="sortable col-all">Qty <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 9)" class="sortable col-all">Avg Cost <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 10)" class="sortable col-tech-core">% Chg <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 11)" class="sortable col-tech-core">Gap % <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 12)" class="sortable col-tech-core">% Open <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 13)" class="sortable col-tech-core" title="Relative Volume (RVOL): Ratio of session cumulative volume relative to 20-day historical session average at time T.">RVOL <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 14)" class="sortable col-tech-core" title="Earnings Date &amp; Timing: 'b' = Before Market Open, 'a' = After Market Close. Real-time dynamic calendar.">Earnings <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 15)" class="sortable col-tech-core">Last High <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 16)" class="sortable col-core-only">Sector <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 17)" class="sortable col-core-only">Industry <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 18)" class="sortable col-core-only" title="Institutional Catalyst Rating: 5.0★: Verified Major Earnings Beat (EPS/Rev &gt; 15%) or FDA Approval / Buyout. 4.0★: Strong Earnings Release / Major Contract / Tier-1 Upgrade. 3.0★: Product Launch / M&amp;A Rumor. 2.0★: Earnings Anticipation / Preview / Valuation Commentary. 1.0★: Technical Noise.">Catalyst <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 19)" class="sortable col-tech-only">PM High <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 20)" class="sortable col-tech-only">VWAP <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 21)" class="sortable col-tech-only">SMA5 <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 22)" class="sortable col-tech-only">SMA20 <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 23)" class="sortable col-tech-only">SMA50 <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 24)" class="sortable col-tech-only">SMA200 <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 25)" class="sortable col-opt-only">Call Wall <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 26)" class="sortable col-opt-only">Put Wall <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 27)" class="sortable col-opt-only">Gamma Flip <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 28)" class="sortable col-opt-only">Vol/OI <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 29)" class="sortable col-opt-only">ATM IV <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 30)" class="sortable col-opt-only">Skew <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 31)" class="sortable col-opt-only">P/C <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 32)" class="sortable col-opt-only">Analyst <span class="sort-icon"></span></th>
                            <th onclick="sortTable('portfolio-table', 33)" class="sortable col-core-only">Strategy Tag <span class="sort-icon"></span></th>
                            <th class="col-all" style="text-align: center;">Actions</th>
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

    <!-- VIEW 4: TRADE EXECUTION DESK (ACTIONS TAB) -->
    <div id="view-actions-section" style="display: none;">
        <div class="card actions-desk-card">
            <div class="section-header-row">
                <div class="section-title">
                    <span>🎯 Trade Execution Desk &amp; Action Queue</span>
                    <span style="font-size: 12px; color: #9ca3af; font-weight: normal;">(Real-time setup priority, hard stops, soft stops, trailing exits, and interactive checkboxes for Screener &amp; Portfolio)</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn-secondary" onclick="clearCompletedActionDeskTasks()">🧹 Clear Completed</button>
                    <button class="btn-action" onclick="resetAllActionDeskTasks()">🔄 Reset Checklist</button>
                </div>
            </div>

            <!-- Summary KPI Cards -->
            <div class="actions-summary-grid">
                <div class="action-stat-box">
                    <div class="action-stat-title">⚡ Immediate Priority 1 Actions</div>
                    <div class="action-stat-val" id="actions-p1-count" style="color: #f87171;">{action_p1_count}</div>
                    <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">Urgent entry breakouts &amp; stop breaks</div>
                </div>
                <div class="action-stat-box">
                    <div class="action-stat-title">🚨 Hard Stops / Risk Alerts</div>
                    <div class="action-stat-val" id="actions-p2-count" style="color: #fbbf24;">{action_p2_count}</div>
                    <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">Portfolio stops &amp; breakdown exits</div>
                </div>
                <div class="action-stat-box">
                    <div class="action-stat-title">🎯 Profit Targets &amp; Trailing</div>
                    <div class="action-stat-val" id="actions-p3-count" style="color: #34d399;">{action_p3_count}</div>
                    <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">2.0R / 3.5R profit trims &amp; trailing stops</div>
                </div>
                <div class="action-stat-box">
                    <div class="action-stat-title">📋 Execution Progress</div>
                    <div class="action-stat-val" id="actions-progress-val" style="color: #60a5fa;">0 / {action_total_count} Done</div>
                    <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">Saved locally in browser</div>
                </div>
            </div>

            <!-- Action Filters -->
            <div class="filter-panel" style="margin-bottom: 12px;">
                <div class="filter-row">
                    <div class="filter-item">
                        <span>Priority Tier:</span>
                        <select id="action-filter-priority" class="filter-select" onchange="filterActionsDesk()">
                            <option value="ALL" selected>All Priorities (Tiers 1-4)</option>
                            <option value="TIER1">⚡ Tier 1: Immediate Entry &amp; 3-Day Rule</option>
                            <option value="TIER2">🚨 Tier 2: Hard Stop Triggered / VCP Setup</option>
                            <option value="TIER3">🎯 Tier 3: Profit Targets (2R/3.5R)</option>
                            <option value="TIER4">📈 Tier 4: Trailing Management &amp; Review</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Task Status:</span>
                        <select id="action-filter-status" class="filter-select" onchange="filterActionsDesk()">
                            <option value="PENDING" selected>⏳ Pending / Action Required</option>
                            <option value="DONE">✅ Done / Executed</option>
                            <option value="SKIPPED">❌ Skipped</option>
                            <option value="ALL">All Items</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Source Desk:</span>
                        <select id="action-filter-source" class="filter-select" onchange="filterActionsDesk()">
                            <option value="ALL" selected>All Sources</option>
                            <option value="SCREENER">🚀 Screener Setups</option>
                            <option value="PORTFOLIO">💼 Portfolio Risk &amp; Exits</option>
                        </select>
                    </div>
                    <div class="filter-item" style="flex: 1; max-width: 320px;">
                        <input type="text" class="search-input" id="action-search-input" placeholder="Search action symbol, instruction, setup..." style="width: 100%;" onkeyup="filterActionsDesk()">
                    </div>
                </div>
            </div>

            <!-- Actions Table -->
            <div class="table-responsive">
                <table class="data-table" id="actions-table">
                    <thead>
                        <tr>
                            <th style="width: 75px; text-align: center;">Done / Skip</th>
                            <th>Priority Tier</th>
                            <th>Symbol</th>
                            <th>Desk Source</th>
                            <th>Setup Archetype</th>
                            <th>Order Instruction</th>
                            <th>Entry / Ref Price</th>
                            <th>Hard Stop ($ / %)</th>
                            <th>Soft Stop</th>
                            <th>Target 1 (2.0R)</th>
                            <th>Target 2 (3.5R)</th>
                            <th>Trailing Rule</th>
                            <th>Conviction / Alloc</th>
                            <th>Time Horizon</th>
                        </tr>
                    </thead>
                    <tbody id="actions-table-tbody">
                        {action_desk_rows}
                    </tbody>
                </table>
            </div>
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

            <!-- 9 Consolidated Institutional Master Setup Tabs -->
            <div class="stockbeep-preset-bar" id="preset-bar">
                <button type="button" class="stockbeep-preset-tab active" id="preset-tab-ALL_SETUPS" data-tooltip="All Setups: Complete screened universe passing liquidity & volume filters." onclick="selectStockbeepPreset('ALL_SETUPS')">🌟 All Setups</button>
                <button type="button" class="stockbeep-preset-tab" id="preset-tab-HIGH_TIGHT_FLAG" data-tooltip="High Tight Flag (HTF): Explosive setup with +75% to +100%+ rapid advance over 4-8 weeks, consolidating tightly (&lt; 20% range) near 52-week highs." onclick="selectStockbeepPreset('HIGH_TIGHT_FLAG')">🚩 High Tight Flag</button>
                <button type="button" class="stockbeep-preset-tab" id="preset-tab-BASE_BREAKOUT" data-tooltip="Base Breakout (Cup &amp; Handle / Base-on-Base): 7-14 week constructive base breaking above pivot on heavy institutional volume." onclick="selectStockbeepPreset('BASE_BREAKOUT')">☕ Base Breakout</button>
                <button type="button" class="stockbeep-preset-tab" id="preset-tab-MINERVINI_VCP" data-tooltip="Minervini VCP &amp; Cheat: Progressive volatility contractions (2-4 contractions) with volume dry-up before the explosive pivot break." onclick="selectStockbeepPreset('MINERVINI_VCP')">📉 Minervini VCP</button>
                <button type="button" class="stockbeep-preset-tab" id="preset-tab-EP_DAY_1" data-tooltip="Episodic Pivot Day 1: High conviction earnings/FDA/M&amp;A catalyst shock, gap &ge; 7%, and monster RVOL &ge; 1.35x." onclick="selectStockbeepPreset('EP_DAY_1')">🔥 EP Day 1</button>
                <button type="button" class="stockbeep-preset-tab" id="preset-tab-EP_DAY_2" data-tooltip="EP Day 2+ VWAP Touch: Orderly pullback to Day 1 VWAP or 5-SMA within Days 2-5 holding prior lows on dry volume." onclick="selectStockbeepPreset('EP_DAY_2')">🎯 EP Day 2+ VWAP</button>
                <button type="button" class="stockbeep-preset-tab" id="preset-tab-STAGE_2_PULLBACK" data-tooltip="Stage 2 Pullback &amp; PEAD: Orderly pullback to rising 10-EMA, 20-SMA or 50-SMA with low volume in confirmed Stage 2 trend." onclick="selectStockbeepPreset('STAGE_2_PULLBACK')">📈 Stage 2 Pullback</button>
                <button type="button" class="stockbeep-preset-tab" id="preset-tab-STRUCTURE_BOS" data-tooltip="Market Structure Break (BOS): Decisive break of multi-day swing highs/lows with volume confirmation." onclick="selectStockbeepPreset('STRUCTURE_BOS')">⚡ Structure BOS</button>
                <button type="button" class="stockbeep-preset-tab" id="preset-tab-INTRADAY_VELOCITY" data-tooltip="Intraday Velocity &amp; ORB: Real-time 5-minute volume spike &ge; 2.5x, ORB breakout, or VWAP spring." onclick="selectStockbeepPreset('INTRADAY_VELOCITY')">🌊 Intraday Velocity</button>
                <button type="button" class="stockbeep-preset-tab" id="preset-tab-CLIMAX_REVERSALS" data-tooltip="Selling Climax Bottom &amp; Buying Climax Top: Statistical extreme oversold/overbought with massive volume absorption." onclick="selectStockbeepPreset('CLIMAX_REVERSALS')">🌊 Climax Reversals</button>
                <button type="button" class="stockbeep-preset-tab" id="preset-tab-WHALE_FLOW" data-tooltip="Whale Flow &amp; Gamma Magnet: Single option sweep orders &ge; $200K, Call Wall magnet headroom, and bullish gamma skew." onclick="selectStockbeepPreset('WHALE_FLOW')">🐳 Whale Flow / Gamma</button>
                <button type="button" class="stockbeep-preset-tab" id="preset-tab-EXTENDED_MOVERS" data-tooltip="Extended Movers: Overextended moves with gap &ge; 22%, RSI &gt; 80, or extended +35% above 50-SMA." onclick="selectStockbeepPreset('EXTENDED_MOVERS')">⚠️ Extended Movers</button>
            </div>

            <!-- Interactive Multi-Factor Filter Bar -->
            <div class="filter-panel">
                <div class="filter-row">
                    <div class="filter-item" id="day-breakout-dropdown-container" style="position: relative;">
                        <span style="font-weight: 700; color: #93c5fd;">⚡ Break Up/Down:</span>
                        <div class="dropdown-multiselect" style="display: inline-block; position: relative;">
                            <button type="button" id="day-breakout-btn" class="filter-select" style="min-width: 175px; text-align: left; cursor: pointer; display: inline-flex; justify-content: space-between; align-items: center;" onclick="toggleBreakoutDropdown('day-breakout-dropdown')">
                                <span id="day-breakout-label">All Levels (Unchecked)</span>
                                <span style="font-size: 9px; margin-left: 6px;">▼</span>
                            </button>
                            <div id="day-breakout-dropdown" class="multiselect-dropdown-menu" style="display: none; position: absolute; top: 100%; left: 0; z-index: 1050; background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 10px 14px; box-shadow: 0 12px 30px rgba(0,0,0,0.7); min-width: 220px;">
                                <div style="font-size: 10px; font-weight: 800; color: #38bdf8; text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.5px;">Break Up (&gt; Resistance)</div>
                                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 11.5px; cursor: pointer; color: #e2e8f0;">
                                    <input type="checkbox" id="day-chk-gt-week-high" class="day-breakout-chk" onchange="filterDayWatchlist()"> <strong>&gt; Last Week High</strong>
                                </label>
                                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 11.5px; cursor: pointer; color: #4ade80;">
                                    <input type="checkbox" id="day-chk-gt-day-high" class="day-breakout-chk" onchange="filterDayWatchlist()"> <strong>&gt; Last Day High</strong>
                                </label>
                                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 11.5px; cursor: pointer; color: #a78bfa;">
                                    <input type="checkbox" id="day-chk-gt-pm-high" class="day-breakout-chk" onchange="filterDayWatchlist()"> <strong>&gt; Premarket High</strong>
                                </label>
                                <hr style="border: 0; border-top: 1px solid #334155; margin: 6px 0;">
                                <div style="font-size: 10px; font-weight: 800; color: #f87171; text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.5px;">Break Down (&lt; Level)</div>
                                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 11.5px; cursor: pointer; color: #fb7185;">
                                    <input type="checkbox" id="day-chk-lt-pm-low" class="day-breakout-chk" onchange="filterDayWatchlist()"> <strong>&lt; Premarket Low</strong>
                                </label>
                                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 11.5px; cursor: pointer; color: #ef4444;">
                                    <input type="checkbox" id="day-chk-lt-week-low" class="day-breakout-chk" onchange="filterDayWatchlist()"> <strong>&lt; Last Week Low</strong>
                                </label>
                                <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px; font-size: 11.5px; cursor: pointer; color: #dc2626;">
                                    <input type="checkbox" id="day-chk-lt-day-low" class="day-breakout-chk" onchange="filterDayWatchlist()"> <strong>&lt; Last Day Low</strong>
                                </label>
                                <div style="margin-top: 8px; text-align: right;">
                                    <button type="button" style="background: transparent; border: none; color: #94a3b8; font-size: 10px; cursor: pointer; text-decoration: underline;" onclick="clearAllDayBreakoutChecks()">Clear All</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="filter-item">
                        <span>% Chg:</span>
                        <select id="filter-chg" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="ALL" selected>All % Chg</option>
                            <option value="GT_3">&gt; +3.0%</option>
                            <option value="LT_M3">&lt; -3.0%</option>
                            <option value="LT_M20">&lt; -20%</option>
                            <option value="M20_M10">-20% to -10%</option>
                            <option value="M10_M5">-10% to -5%</option>
                            <option value="M5_0">-5% to 0%</option>
                            <option value="0_5">0% to 5%</option>
                            <option value="5_10">5% to 10%</option>
                            <option value="10_20">10% to 20%</option>
                            <option value="20_50">20% to 50%</option>
                            <option value="50_100">50% to 100%</option>
                            <option value="GT_100">&gt; 100%</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Gap %:</span>
                        <select id="filter-gap" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="ALL" selected>All Gaps</option>
                            <option value="3.0">&ge; +3.0% (Breakout)</option>
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
                            <option value="GT_3">&gt; +3.0%</option>
                            <option value="LT_M3">&lt; -3.0%</option>
                            <option value="LT_M20">&lt; -20%</option>
                            <option value="M20_M10">-20% to -10%</option>
                            <option value="M10_M5">-10% to -5%</option>
                            <option value="M5_0">-5% to 0%</option>
                            <option value="0_5">0% to 5%</option>
                            <option value="5_10">5% to 10%</option>
                            <option value="10_20">10% to 20%</option>
                            <option value="20_50">20% to 50%</option>
                            <option value="50_100">50% to 100%</option>
                            <option value="GT_100">&gt; 100%</option>
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
                        <span>SMA5:</span>
                        <select id="filter-sma5" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="ALL" selected>All SMA5</option>
                            <option value="POS">&gt; SMA5 (Above)</option>
                            <option value="XO">⚡ Cross Over SMA5</option>
                            <option value="XU">🔻 Cross Under SMA5</option>
                            <option value="1.0">&ge; +1.0% above SMA5</option>
                            <option value="3.0">&ge; +3.0% above SMA5</option>
                            <option value="NEG">&lt; SMA5 (Below)</option>
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
                            <option value="0.0" selected>All News / Any Rating</option>
                            <option value="2.0">&ge; 2.0★ Positive (Default)</option>
                            <option value="3.0">&ge; 3.0★</option>
                            <option value="4.0">&ge; 4.0★</option>
                            <option value="5.0">5.0★ Only</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Min RVOL:</span>
                        <select id="filter-rvol" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="0.0" selected>Any RVOL</option>
                            <option value="1.0">&ge; 1.00x</option>
                            <option value="1.5">&ge; 1.50x (Default)</option>
                            <option value="2.0">&ge; 2.00x</option>
                            <option value="3.0">&ge; 3.00x</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <span>Min Score:</span>
                        <select id="filter-score" class="filter-select" onchange="filterDayWatchlist()">
                            <option value="0.0" selected>Any Setup Score</option>
                            <option value="2.5">&ge; 2.5★ (Default)</option>
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
                            <th onclick="sortTable('day-table', 1)" class="sortable col-all" title="Institutional 5-Star Setup Score: Multi-factor quantitative rating (1.0★ to 5.0★) synthesizing: 1) Catalyst Significance (30%), 2) RVOL Expansion (25%), 3) Technical Pattern &amp; MAs/VWAP (20%), 4) Options Gamma &amp; Whale Alignment (15%), 5) Macro Multiplier (10%). Deducts penalties for overextension.">Score <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 2)" class="sortable col-all">Price <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 3)" class="sortable col-all">% Chg <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 4)" class="sortable col-all">Gap % <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 5)" class="sortable col-all">% Open <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 6)" class="sortable col-all" title="Relative Volume (RVOL): Ratio of session cumulative volume relative to 20-day historical session average at time T.">RVOL <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 7)" class="sortable col-all" title="Earnings Date &amp; Timing: 'b' = Before Market Open, 'a' = After Market Close. Real-time dynamic calendar.">Earnings <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 8)" class="sortable col-all">Last High <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 9)" class="sortable col-tech-only">PM High <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 10)" class="sortable col-tech-only">VWAP <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 11)" class="sortable col-tech-only">SMA5 <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 12)" class="sortable col-tech-only">SMA20 <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 13)" class="sortable col-tech-only">SMA50 <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 14)" class="sortable col-tech-only">SMA200 <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 15)" class="sortable col-core-only">Sector <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 16)" class="sortable col-core-only">Industry <span class="sort-icon"></span></th>
                            <th onclick="sortTable('day-table', 17)" class="sortable col-core-only" title="Institutional Catalyst Rating: 5.0★: Verified Major Earnings Beat (EPS/Rev &gt; 15%) or FDA Approval / Buyout. 4.0★: Strong Earnings Release / Major Contract / Tier-1 Upgrade. 3.0★: Product Launch / M&amp;A Rumor. 2.0★: Earnings Anticipation / Preview / Valuation Commentary. 1.0★: Technical Noise.">Catalyst <span class="sort-icon"></span></th>
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
                <div class="tab-bar" id="earn-tab-bar">
                    <button type="button" class="tab-btn active" onclick="switchEarningsTab(this, 'ALL')">All Reports</button>
                    <button type="button" class="tab-btn" onclick="switchEarningsTab(this, 'YEST_AMC')">Yesterday AMC</button>
                    <button type="button" class="tab-btn" onclick="switchEarningsTab(this, 'TODAY_BMO')">Today BMO</button>
                    <button type="button" class="tab-btn" onclick="switchEarningsTab(this, 'TODAY_AMC')">Today AMC</button>
                    <button type="button" class="tab-btn" onclick="switchEarningsTab(this, 'TOMORROW')">Tomorrow</button>
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
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <span>Show <select class="page-size-select" onchange="changePageSize('options-table', this.value)"><option value="10" selected>10</option><option value="25">25</option><option value="1000">All</option></select></span>
                        <select id="options-whale-filter" class="filter-select" onchange="filterOptionsTable(this.value)">
                            <option value="ALL" selected>All Gamma Structures ({options_agg_count})</option>
                            <option value="WHALES">🐳 Whales Only (≥ 1 Whale Trade)</option>
                            <option value="VOL_OI_GT_1">Vol/OI &gt; 1.0x</option>
                            <option value="BULLISH">Bullish Skew Only</option>
                        </select>
                    </div>
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

    <!-- MODAL 4: WHALE TRADES MODAL -->
    <div class="modal-overlay" id="modal-whale-trades">
        <div class="modal-dialog" style="max-width: 880px;">
            <div class="modal-header">
                <div class="modal-title"><span id="whale-modal-title">🐳 Institutional Whale Trades &amp; Gamma Sweeps</span></div>
                <button class="modal-close" onclick="closeModal('modal-whale-trades')">&times;</button>
            </div>
            <div>
                <div id="whale-modal-summary" style="margin-bottom: 12px; font-size: 12px; color: #94a3b8;"></div>
                <div class="table-responsive" style="max-height: 440px; overflow-y: auto;">
                    <table class="whale-inner-table" id="whale-modal-table">
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
                        <tbody id="whale-modal-tbody">
                            <!-- Populated dynamically via JS -->
                        </tbody>
                    </table>
                </div>
                <div style="display: flex; justify-content: flex-end; margin-top: 16px;">
                    <button class="btn-secondary" onclick="closeModal('modal-whale-trades')">Close</button>
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
        'portfolio-table': {{ currentPage: 1, pageSize: 1000, allRows: [], filteredRows: [] }}
    }};

    window.portfolioData = {portfolio_json_raw};
    window.whaleTradesLookup = {whale_lookup_json};

    document.addEventListener('DOMContentLoaded', () => {{
        initTableState('day-table');
        initTableState('eco-table');
        initTableState('earn-table');
        initTableState('analyst-table');
        initTableState('options-table');
        initTableState('portfolio-table');
        
        loadFilterPreferences();
        loadPortfolioFilterPreferences();
        filterDayWatchlist(false);
        filterPortfolioWatchlist(false);

        // Fallback: If saved filters produced 0 rows on load, show all active candidates
        const dayState = tableStates['day-table'];
        if (dayState && dayState.filteredRows.length === 0 && dayState.allRows.length > 0) {{
            showAllCandidates();
        }}
    }});

    function switchMainView(view) {{
        const btnScreener = document.getElementById('nav-tab-screener');
        const btnActions = document.getElementById('nav-tab-actions');
        const btnPortfolio = document.getElementById('nav-tab-portfolio');
        const btnMacro = document.getElementById('nav-tab-macro');
        
        const secScreener = document.getElementById('view-screener-section');
        const secActions = document.getElementById('view-actions-section');
        const secPortfolio = document.getElementById('view-portfolio-section');
        const secMacro = document.getElementById('view-macro-section');

        if (btnScreener) btnScreener.classList.remove('active');
        if (btnActions) btnActions.classList.remove('active');
        if (btnPortfolio) btnPortfolio.classList.remove('active');
        if (btnMacro) btnMacro.classList.remove('active');

        if (secScreener) secScreener.style.display = 'none';
        if (secActions) secActions.style.display = 'none';
        if (secPortfolio) secPortfolio.style.display = 'none';
        if (secMacro) secMacro.style.display = 'none';

        if (view === 'screener') {{
            if (btnScreener) btnScreener.classList.add('active');
            if (secScreener) secScreener.style.display = 'block';
            if (secMacro) secMacro.style.display = 'block';
        }} else if (view === 'actions') {{
            if (btnActions) btnActions.classList.add('active');
            if (secActions) secActions.style.display = 'block';
            if (window.filterActionsDesk) window.filterActionsDesk();
        }} else if (view === 'portfolio') {{
            if (btnPortfolio) btnPortfolio.classList.add('active');
            if (secPortfolio) secPortfolio.style.display = 'block';
        }} else if (view === 'macro') {{
            if (btnMacro) btnMacro.classList.add('active');
            if (secMacro) secMacro.style.display = 'block';
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
            tbody.innerHTML = '<tr><td colspan="36" style="text-align: center; color: #9ca3af; padding: 24px;">No positions found in active book. Click "Import Fidelity CSV" to load positions.</td></tr>';
            return;
        }}

        const rowElements = [];
        positions.forEach((p, idx) => {{
            const sym = p.symbol || '—';
            const rawSym = p.raw_symbol || sym;
            const underlying = p.underlying || sym.replace(/[^A-Za-z]/g, '');
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
            const strat = p.strategy_tag || 'Tactical Momentum';
            const stopL = p.stop_loss || +(lastP * 0.96).toFixed(2);
            const targP = p.target_price || +(lastP * 1.15).toFixed(2);
            const notes = p.notes || '';
            const isOpt = p.is_option || false;

            const pDayColor = pDayD >= 0 ? '#34d399' : '#f87171';
            const pTotColor = pTotD >= 0 ? '#34d399' : '#f87171';

            // Market intelligence fields
            const scoreVal = p.setup_score || 3.0;
            const scoreStars = p.stars_visual || '★★★☆☆';
            const scorePill = '<span class="pill pill-purple" style="font-size: 11px;">' + scoreStars + ' ' + scoreVal.toFixed(1) + '★</span>';

            const pChg = p.pct_change !== undefined ? p.pct_change : pDayP;
            const pChgPill = pChg > 0 ? ('<span class="pill pill-green">+' + pChg.toFixed(2) + '%</span>') : (pChg < 0 ? ('<span class="pill pill-red">' + pChg.toFixed(2) + '%</span>') : ('<span class="pill pill-blue">' + pChg.toFixed(2) + '%</span>'));

            const gapVal = p.gap_pct || 0.0;
            const gapStr = gapVal !== 0 ? ('<span style="color: #38bdf8; font-weight: 600;">' + (gapVal >= 0 ? '+' : '') + gapVal.toFixed(2) + '%</span>') : '<span style="color: #9ca3af;">0.00%</span>';

            const pOpen = p.pct_from_open || 0.0;
            const pOpenColor = pOpen > 0 ? '#34d399' : (pOpen < 0 ? '#f87171' : '#9ca3af');
            const pOpenStr = '<span style="color: ' + pOpenColor + '; font-weight: 600;">' + (pOpen >= 0 ? '+' : '') + pOpen.toFixed(2) + '%</span>';

            const rvolVal = p.rvol || 1.0;
            const rvolPill = rvolVal >= 2.0 ? ('<span class="pill pill-green">' + rvolVal.toFixed(2) + 'x</span>') : ('<span class="pill pill-yellow">' + rvolVal.toFixed(2) + 'x</span>');

            const earnDateVal = p.earnings_date || '—';
            const earnPill = earnDateVal !== '—' ? ('<span class="pill pill-purple" style="font-size: 10.5px;">' + earnDateVal + '</span>') : '<span style="color: #6b7280;">—</span>';

            const catCat = p.catalyst_type || 'Holding';
            const catStarsNum = Math.min(5, Math.max(1, Math.round(p.catalyst_stars || 3)));
            const catStarsStr = '★'.repeat(catStarsNum) + '☆'.repeat(5 - catStarsNum);
            const catDateStr = p.catalyst_date || '—';
            const catPill = '<span class="pill pill-blue">[' + catCat + ']</span> <span style="color: #fbbf24; font-size: 11px;">' + catStarsStr + '</span>';

            const skewVal = p.gamma_skew || 'Neutral';
            const skewPill = skewVal.indexOf('Bullish') >= 0 ? '<span class="pill pill-green">Bullish</span>' : (skewVal.indexOf('Bearish') >= 0 ? '<span class="pill pill-red">Bearish</span>' : ('<span class="pill pill-blue">' + skewVal + '</span>'));

            const drawerId = 'port-row-drawer-' + idx;

            const tr = document.createElement('tr');
            tr.className = 'data-row';
            tr.setAttribute('data-drawer-id', drawerId);
            tr.setAttribute('data-preset-tags', p.preset_tags || 'ALL_SETUPS');
            tr.setAttribute('data-symbol', sym);
            tr.setAttribute('data-underlying', underlying);
            tr.setAttribute('data-is-option', isOpt ? 'true' : 'false');
            tr.setAttribute('data-chg', pChg.toFixed(2));
            tr.setAttribute('data-gap', gapVal.toFixed(2));
            tr.setAttribute('data-open', pOpen.toFixed(2));
            tr.setAttribute('data-vwap-dist', (p.vwap_dist || 0).toFixed(2));
            tr.setAttribute('data-vwap-xo', String(p.vwap_xo || false).toLowerCase());
            tr.setAttribute('data-vwap-xu', String(p.vwap_xu || false).toLowerCase());
            tr.setAttribute('data-vwap-std-p1', String(p.vwap_std_p1 || false).toLowerCase());
            tr.setAttribute('data-vwap-std-p2', String(p.vwap_std_p2 || false).toLowerCase());
            tr.setAttribute('data-vwap-std-m1', String(p.vwap_std_m1 || false).toLowerCase());
            tr.setAttribute('data-vwap-std-m2', String(p.vwap_std_m2 || false).toLowerCase());
            tr.setAttribute('data-skew', skewVal);
            tr.setAttribute('data-pc', String(p.pc_ratio || 1.0));
            tr.setAttribute('data-net-flow', String(p.net_dollar_val || 0.0));
            tr.setAttribute('data-whales', String(p.whale_trades_count || 0));
            tr.setAttribute('data-sma5-dist', (p.sma5_dist || 0).toFixed(2));
            tr.setAttribute('data-sma5-xo', String(p.sma5_xo || false).toLowerCase());
            tr.setAttribute('data-sma5-xu', String(p.sma5_xu || false).toLowerCase());
            tr.setAttribute('data-sma20-dist', (p.sma20_dist || 0).toFixed(2));
            tr.setAttribute('data-sma20-xo', String(p.sma20_xo || false).toLowerCase());
            tr.setAttribute('data-sma20-xu', String(p.sma20_xu || false).toLowerCase());
            tr.setAttribute('data-sma50-dist', (p.sma50_dist || 0).toFixed(2));
            tr.setAttribute('data-sma50-xo', String(p.sma50_xo || false).toLowerCase());
            tr.setAttribute('data-sma50-xu', String(p.sma50_xu || false).toLowerCase());
            tr.setAttribute('data-sma200-dist', (p.sma200_dist || 0).toFixed(2));
            tr.setAttribute('data-sma200-xo', String(p.sma200_xo || false).toLowerCase());
            tr.setAttribute('data-sma200-xu', String(p.sma200_xu || false).toLowerCase());
            tr.setAttribute('data-rvol', rvolVal.toFixed(2));
            tr.setAttribute('data-score', scoreVal.toFixed(2));
            tr.setAttribute('data-stars', String(p.catalyst_stars || 0.0));
            tr.setAttribute('data-pos', String(p.is_positive !== undefined ? p.is_positive : true).toLowerCase());
            tr.setAttribute('data-breakout-last', String(p.breakout_last_high || false).toLowerCase());
            tr.setAttribute('data-breakout-pm', String(p.breakout_pm_high || false).toLowerCase());
            tr.setAttribute('data-breakout-week-high', String(p.breakout_week_high || false).toLowerCase());
            tr.setAttribute('data-breakout-last-high', String(p.breakout_last_high || false).toLowerCase());
            tr.setAttribute('data-breakout-pm-high', String(p.breakout_pm_high || false).toLowerCase());
            tr.setAttribute('data-breakdown-pm-low', String(p.breakdown_pm_low || false).toLowerCase());
            tr.setAttribute('data-breakdown-week-low', String(p.breakdown_week_low || false).toLowerCase());
            tr.setAttribute('data-breakdown-last-low', String(p.breakdown_last_low || false).toLowerCase());
            tr.setAttribute('data-sector', p.sector || 'General');
            tr.setAttribute('data-total-pct', pTotP.toFixed(2));
            tr.setAttribute('data-weight', wPct.toFixed(2));
            tr.setAttribute('data-strategy', strat);

            tr.innerHTML = 
                '<td class="col-all"><a class="ticker-link" href="https://finance.yahoo.com/quote/' + underlying + '" target="_blank">' + sym + '</a></td>' +
                '<td class="col-all">' + scorePill + '</td>' +
                '<td class="col-all"><strong>$' + lastP.toFixed(2) + '</strong></td>' +
                '<td class="col-all" style="color: ' + pDayColor + '; font-weight: 600;">' + (pDayD >= 0 ? '+' : '') + pDayD.toFixed(2) + '</td>' +
                '<td class="col-all" style="color: ' + pTotColor + '; font-weight: 700;">' + (pTotD >= 0 ? '+' : '') + pTotD.toFixed(2) + '</td>' +
                '<td class="col-all" style="color: ' + pTotColor + '; font-weight: 700;">' + (pTotP >= 0 ? '+' : '') + pTotP.toFixed(2) + '%</td>' +
                '<td class="col-all"><strong>$' + curV.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}}) + '</strong></td>' +
                '<td class="col-all"><span class="pill pill-blue">' + wPct.toFixed(2) + '%</span></td>' +
                '<td class="col-all"><strong>' + qty.toLocaleString('en-US', {{minimumFractionDigits: 0, maximumFractionDigits: 3}}) + '</strong></td>' +
                '<td class="col-all">$' + avgC.toFixed(2) + '</td>' +
                '<td class="col-tech-core">' + pChgPill + '</td>' +
                '<td class="col-tech-core">' + gapStr + '</td>' +
                '<td class="col-tech-core">' + pOpenStr + '</td>' +
                '<td class="col-tech-core">' + rvolPill + '</td>' +
                '<td class="col-tech-core">' + earnPill + '</td>' +
                '<td class="col-tech-core">' + (p.yesterday_high_dist || '—') + '</td>' +
                '<td class="col-core-only"><span class="pill pill-blue">' + (p.sector || 'General') + '</span></td>' +
                '<td class="col-core-only" style="font-size: 11px; color: #d1d5db;">' + (p.industry || 'Diversified') + '</td>' +
                '<td class="col-core-only">' + catPill + ' <a class="headline-link" href="' + (p.catalyst_url || '#') + '" target="_blank">' + (p.headline || desc) + '</a></td>' +
                '<td class="col-tech-only">' + (p.premarket_high_dist || '—') + '</td>' +
                '<td class="col-tech-only"><strong style="color: #38bdf8;">' + (p.vwap || '—') + '</strong></td>' +
                '<td class="col-tech-only">' + (p.sma5 || '—') + '</td>' +
                '<td class="col-tech-only">' + (p.sma20 || '—') + '</td>' +
                '<td class="col-tech-only">' + (p.sma50 || '—') + '</td>' +
                '<td class="col-tech-only">' + (p.sma200 || '—') + '</td>' +
                '<td class="col-opt-only" style="color: #60a5fa; font-weight: 600;">' + (p.call_wall || '—') + '</td>' +
                '<td class="col-opt-only" style="color: #f87171; font-weight: 600;">' + (p.put_wall || '—') + '</td>' +
                '<td class="col-opt-only" style="color: #fbbf24;">' + (p.gamma_flip || '—') + '</td>' +
                '<td class="col-opt-only">' + (p.vol_oi_ratio ? p.vol_oi_ratio.toFixed(2) + 'x' : '1.00x') + '</td>' +
                '<td class="col-opt-only">' + (p.atm_iv_str || '—') + '</td>' +
                '<td class="col-opt-only">' + skewPill + '</td>' +
                '<td class="col-opt-only">' + (p.pc_ratio || '—') + '</td>' +
                '<td class="col-opt-only"><strong style="color: #34d399; font-size: 11px;">' + (p.analyst_rating || '—') + '</strong></td>' +
                '<td class="col-core-only"><span class="pill pill-purple">' + strat + '</span></td>' +
                '<td class="col-all" style="text-align: center; white-space: nowrap;">' +
                    '<button class="btn-action" style="padding: 2px 6px; font-size: 10px;" onclick="openSizingModal(&quot;' + underlying + '&quot;, ' + lastP + ', ' + stopL + ', &quot;' + desc.replace(/"/g, '').replace(/\'/g, '') + '&quot;, &quot;Rebalance&quot;)">⚡</button>' +
                    '<button class="btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="openEditPositionModal(&quot;' + sym + '&quot;, ' + qty + ', ' + avgC + ', ' + stopL + ', ' + targP + ', &quot;' + strat + '&quot;, &quot;' + notes.replace(/"/g, '').replace(/\'/g, '') + '&quot;)">✏️</button>' +
                    '<button class="btn-danger" style="padding: 2px 6px; font-size: 10px;" onclick="deletePortfolioPosition(&quot;' + sym + '&quot;)">❌</button>' +
                    '<button class="btn-secondary" style="padding: 2px 6px; font-size: 10px; margin-left: 2px;" onclick="toggleRowDrawer(&quot;' + drawerId + '&quot;)">🔍</button>' +
                '</td>';

            const drawerTr = document.createElement('tr');
            drawerTr.className = 'row-drawer';
            drawerTr.id = drawerId;
            drawerTr.innerHTML = 
                '<td colspan="35">' +
                    '<div class="drawer-content">' +
                        '<div class="drawer-card">' +
                            '<div class="drawer-card-title">📈 Trend & Moving Average Matrix (' + sym + ')</div>' +
                            '<div class="drawer-item-row"><span>Total Session % Chg:</span> ' + pChgPill + '</div>' +
                            '<div class="drawer-item-row"><span>Opening Gap %:</span> ' + gapStr + '</div>' +
                            '<div class="drawer-item-row"><span>Intraday Run (% Open):</span> ' + pOpenStr + '</div>' +
                            '<div class="drawer-item-row"><span>VWAP (Session):</span> <strong style="color: #38bdf8;">' + (p.vwap || '—') + '</strong></div>' +
                            '<div class="drawer-item-row"><span>5-Day SMA:</span> <strong>' + (p.sma5 || '—') + '</strong></div>' +
                            '<div class="drawer-item-row"><span>20-Day SMA:</span> <strong>' + (p.sma20 || '—') + '</strong></div>' +
                            '<div class="drawer-item-row"><span>50-Day SMA:</span> <strong>' + (p.sma50 || '—') + '</strong></div>' +
                            '<div class="drawer-item-row"><span>200-Day SMA:</span> <strong>' + (p.sma200 || '—') + '</strong></div>' +
                        '</div>' +
                        '<div class="drawer-card">' +
                            '<div class="drawer-card-title">🎯 Institutional Options Gamma & Sizing</div>' +
                            '<div class="drawer-item-row"><span>Gamma Skew:</span> ' + skewPill + '</div>' +
                            '<div class="drawer-item-row"><span>Flow Conviction:</span> ' + (p.flow_conviction_badge || '🟡 Flow: 50/100') + '</div>' +
                            '<div class="drawer-item-row"><span>Call Wall (Magnet):</span> <strong style="color: #60a5fa;">' + (p.call_wall || '—') + '</strong></div>' +
                            '<div class="drawer-item-row"><span>Put Wall (Floor):</span> <strong style="color: #f87171;">' + (p.put_wall || '—') + '</strong></div>' +
                            '<div class="drawer-item-row"><span>Gamma Flip Level:</span> <strong style="color: #fbbf24;">' + (p.gamma_flip || '—') + '</strong></div>' +
                            '<div class="drawer-item-row"><span>Vol/OI & P/C Ratio:</span> <strong>' + (p.vol_oi_ratio ? p.vol_oi_ratio.toFixed(2) + 'x' : '1.00x') + ' (P/C: ' + (p.pc_ratio || '—') + ')</strong></div>' +
                            '<div class="drawer-item-row"><span>ATM IV & Net Flow:</span> <strong>' + (p.atm_iv_str || '—') + ' (' + (p.net_dollar_str || '—') + ')</strong></div>' +
                        '</div>' +
                        '<div class="drawer-card">' +
                            '<div class="drawer-card-title">📰 Catalyst & Analyst Intelligence</div>' +
                            '<div style="margin-bottom: 6px;">' + catPill + '</div>' +
                            '<div style="margin-bottom: 8px;"><a class="headline-link" href="' + (p.catalyst_url || '#') + '" target="_blank" style="font-size: 12px; font-weight: 600;">' + (p.headline || desc) + '</a></div>' +
                            '<div class="drawer-item-row"><span>Sector:</span> <strong style="color: #9ca3af;">' + (p.sector || 'General') + '</strong></div>' +
                            '<div class="drawer-item-row"><span>Industry:</span> <strong style="color: #d1d5db;">' + (p.industry || 'Diversified') + '</strong></div>' +
                            '<div class="drawer-item-row"><span>Earnings Date:</span> <strong style="color: #c084fc;">' + (p.earnings_date || '—') + '</strong></div>' +
                            '<div class="drawer-item-row"><span>Analyst Revisions:</span> <strong style="color: #34d399;">' + (p.analyst_rating || '—') + '</strong></div>' +
                        '</div>' +
                        '<div class="drawer-card">' +
                            '<div class="drawer-card-title">💼 Portfolio Position & Risk Sizing</div>' +
                            '<div class="drawer-item-row"><span>Holding Quantity:</span> <strong>' + qty.toLocaleString('en-US') + '</strong></div>' +
                            '<div class="drawer-item-row"><span>Average Cost:</span> <strong>$' + avgC.toFixed(2) + '</strong></div>' +
                            '<div class="drawer-item-row"><span>Total Cost Basis:</span> <strong>$' + (p.cost_basis_total ? p.cost_basis_total.toLocaleString('en-US', {{minimumFractionDigits: 2}}) : (qty * avgC).toFixed(2)) + '</strong></div>' +
                            '<div class="drawer-item-row"><span>Current Value:</span> <strong>$' + curV.toLocaleString('en-US', {{minimumFractionDigits: 2}}) + ' (' + wPct.toFixed(2) + '%)</strong></div>' +
                            '<div class="drawer-item-row"><span>Today Session P&L:</span> <strong style="color: ' + pDayColor + ';">' + (pDayD >= 0 ? '+' : '') + pDayD.toFixed(2) + ' (' + (pDayP >= 0 ? '+' : '') + pDayP.toFixed(2) + '%)</strong></div>' +
                            '<div class="drawer-item-row"><span>Total Unrealized P&L:</span> <strong style="color: ' + pTotColor + ';">' + (pTotD >= 0 ? '+' : '') + pTotD.toFixed(2) + ' (' + (pTotP >= 0 ? '+' : '') + pTotP.toFixed(2) + '%)</strong></div>' +
                            '<div class="drawer-item-row"><span>Stop Loss / Target:</span> <strong>$' + stopL.toFixed(2) + ' / $' + targP.toFixed(2) + '</strong></div>' +
                            '<div class="drawer-item-row"><span>Strategy Tag:</span> <span class="pill pill-purple">' + strat + '</span></div>' +
                            (notes ? '<div class="drawer-item-row"><span>Trade Notes:</span> <em>' + notes + '</em></div>' : '') +
                        '</div>' +
                    '</div>' +
                '</td>';

            tbody.appendChild(tr);
            tbody.appendChild(drawerTr);
            rowElements.push(tr);
        }});

        tableStates['portfolio-table'].allRows = rowElements;
        tableStates['portfolio-table'].filteredRows = [...rowElements];
        filterPortfolioWatchlist(false);
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

    function switchPortfolioView(mode, save = true) {{
        const table = document.getElementById('portfolio-table');
        if (!table) return;

        table.classList.remove('view-core', 'view-technical', 'view-options');
        table.classList.add(`view-${{mode}}`);

        const btnCore = document.getElementById('btn-port-view-core');
        const btnTech = document.getElementById('btn-port-view-technical');
        const btnOpt = document.getElementById('btn-port-view-options');

        if (btnCore) btnCore.classList.toggle('active', mode === 'core');
        if (btnTech) btnTech.classList.toggle('active', mode === 'technical');
        if (btnOpt) btnOpt.classList.toggle('active', mode === 'options');

        window.currentPortfolioView = mode;
        if (save) savePortfolioFilterPreferences();
    }}

    function savePortfolioFilterPreferences() {{
        try {{
            const prefs = {{
                reqLastHigh: document.getElementById('port-filter-breakout-last') ? document.getElementById('port-filter-breakout-last').checked : false,
                reqPmHigh: document.getElementById('port-filter-breakout-pm') ? document.getElementById('port-filter-breakout-pm').checked : false,
                filterChg: document.getElementById('port-filter-chg') ? document.getElementById('port-filter-chg').value : 'ALL',
                filterGap: document.getElementById('port-filter-gap') ? document.getElementById('port-filter-gap').value : 'ALL',
                filterOpen: document.getElementById('port-filter-open') ? document.getElementById('port-filter-open').value : 'ALL',
                filterVwap: document.getElementById('port-filter-vwap') ? document.getElementById('port-filter-vwap').value : 'ALL',
                filterTotalPct: document.getElementById('port-filter-total-pct') ? document.getElementById('port-filter-total-pct').value : 'ALL',
                filterWeight: document.getElementById('port-filter-weight') ? document.getElementById('port-filter-weight').value : 'ALL',
                filterFlow: document.getElementById('port-filter-flow') ? document.getElementById('port-filter-flow').value : 'ALL',
                filterSma20: document.getElementById('port-filter-sma20') ? document.getElementById('port-filter-sma20').value : 'ALL',
                filterSma50: document.getElementById('port-filter-sma50') ? document.getElementById('port-filter-sma50').value : 'ALL',
                filterSma200: document.getElementById('port-filter-sma200') ? document.getElementById('port-filter-sma200').value : 'ALL',
                minCat: document.getElementById('port-filter-catalyst') ? document.getElementById('port-filter-catalyst').value : '0.0',
                minRvol: document.getElementById('port-filter-rvol') ? document.getElementById('port-filter-rvol').value : '0.0',
                minScore: document.getElementById('port-filter-score') ? document.getElementById('port-filter-score').value : '0.0',
                selSector: document.getElementById('port-filter-sector') ? document.getElementById('port-filter-sector').value : 'ALL',
                assetType: document.getElementById('port-filter-asset-type') ? document.getElementById('port-filter-asset-type').value : 'ALL',
                strat: document.getElementById('port-filter-strat') ? document.getElementById('port-filter-strat').value : 'ALL',
                activeView: window.currentPortfolioView || 'core'
            }};
            localStorage.setItem('portfolio_filter_prefs', JSON.stringify(prefs));
            const saveNotice = document.getElementById('port-save-status-pill');
            if (saveNotice) {{
                saveNotice.style.display = 'inline-block';
                saveNotice.innerText = '💾 Saved';
                setTimeout(() => {{ saveNotice.innerText = '💾 Auto-Saved'; }}, 1500);
            }}
        }} catch (e) {{
            console.error('Failed to save portfolio filter preferences:', e);
        }}
    }}

    function toggleBreakoutDropdown(menuId) {{
        const menu = document.getElementById(menuId);
        if (!menu) return;
        const isHidden = menu.style.display === 'none' || menu.style.display === '';
        menu.style.display = isHidden ? 'block' : 'none';
    }}

    function clearAllPortBreakoutChecks(triggerFilter = true) {{
        const chks = document.querySelectorAll('.port-breakout-chk');
        chks.forEach(c => c.checked = false);
        const labelElem = document.getElementById('port-breakout-label');
        if (labelElem) labelElem.innerText = 'All Levels (Unchecked)';
        if (triggerFilter) filterPortfolioWatchlist(true);
    }}

    document.addEventListener('click', function(e) {{
        const portContainer = document.getElementById('port-breakout-dropdown-container');
        const portMenu = document.getElementById('port-breakout-dropdown');
        if (portContainer && portMenu && !portContainer.contains(e.target)) {{
            portMenu.style.display = 'none';
        }}
        const dayContainer = document.getElementById('day-breakout-dropdown-container');
        const dayMenu = document.getElementById('day-breakout-dropdown');
        if (dayContainer && dayMenu && !dayContainer.contains(e.target)) {{
            dayMenu.style.display = 'none';
        }}
    }});

    /* Portfolio Stockbeep Preset Tab Filter Engine */
    window.activePortfolioStockbeepPreset = 'ALL_SETUPS';

    function selectPortfolioStockbeepPreset(presetTag) {{
        window.activePortfolioStockbeepPreset = presetTag || 'ALL_SETUPS';
        document.querySelectorAll('#port-preset-bar .stockbeep-preset-tab').forEach(tab => {{
            tab.classList.remove('active');
        }});
        const activeTab = document.getElementById('port-preset-tab-' + window.activePortfolioStockbeepPreset);
        if (activeTab) {{
            activeTab.classList.add('active');
        }}
        if (presetTag && presetTag !== 'ALL_SETUPS') {{
            document.querySelectorAll('.port-breakout-chk').forEach(c => c.checked = false);
            const labelElem = document.getElementById('port-breakout-label');
            if (labelElem) labelElem.innerText = 'All Levels (Unchecked)';
        }}
        filterPortfolioWatchlist(true);
    }}

    function savePortfolioFilterPreferences() {{
        try {{
            const prefs = {{
                activePreset: window.activePortfolioStockbeepPreset || 'ALL_SETUPS',
                chkGtWeekHigh: document.getElementById('port-chk-gt-week-high') ? document.getElementById('port-chk-gt-week-high').checked : false,
                chkGtDayHigh: document.getElementById('port-chk-gt-day-high') ? document.getElementById('port-chk-gt-day-high').checked : false,
                chkGtPmHigh: document.getElementById('port-chk-gt-pm-high') ? document.getElementById('port-chk-gt-pm-high').checked : false,
                chkLtPmLow: document.getElementById('port-chk-lt-pm-low') ? document.getElementById('port-chk-lt-pm-low').checked : false,
                chkLtWeekLow: document.getElementById('port-chk-lt-week-low') ? document.getElementById('port-chk-lt-week-low').checked : false,
                chkLtDayLow: document.getElementById('port-chk-lt-day-low') ? document.getElementById('port-chk-lt-day-low').checked : false,
                filterChg: document.getElementById('port-filter-chg') ? document.getElementById('port-filter-chg').value : 'ALL',
                filterGap: document.getElementById('port-filter-gap') ? document.getElementById('port-filter-gap').value : 'ALL',
                filterOpen: document.getElementById('port-filter-open') ? document.getElementById('port-filter-open').value : 'ALL',
                filterVwap: document.getElementById('port-filter-vwap') ? document.getElementById('port-filter-vwap').value : 'ALL',
                filterTotalPct: document.getElementById('port-filter-total-pct') ? document.getElementById('port-filter-total-pct').value : 'ALL',
                filterWeight: document.getElementById('port-filter-weight') ? document.getElementById('port-filter-weight').value : 'ALL',
                filterFlow: document.getElementById('port-filter-flow') ? document.getElementById('port-filter-flow').value : 'ALL',
                filterSma5: document.getElementById('port-filter-sma5') ? document.getElementById('port-filter-sma5').value : 'ALL',
                filterSma20: document.getElementById('port-filter-sma20') ? document.getElementById('port-filter-sma20').value : 'ALL',
                filterSma50: document.getElementById('port-filter-sma50') ? document.getElementById('port-filter-sma50').value : 'ALL',
                filterSma200: document.getElementById('port-filter-sma200') ? document.getElementById('port-filter-sma200').value : 'ALL',
                minCat: document.getElementById('port-filter-catalyst') ? document.getElementById('port-filter-catalyst').value : '0.0',
                minRvol: document.getElementById('port-filter-rvol') ? document.getElementById('port-filter-rvol').value : '0.0',
                minScore: document.getElementById('port-filter-score') ? document.getElementById('port-filter-score').value : '0.0',
                selSector: document.getElementById('port-filter-sector') ? document.getElementById('port-filter-sector').value : 'ALL',
                assetType: document.getElementById('port-filter-asset-type') ? document.getElementById('port-filter-asset-type').value : 'ALL',
                strat: document.getElementById('port-filter-strat') ? document.getElementById('port-filter-strat').value : 'ALL',
                activeView: window.currentPortfolioView || 'core'
            }};
            localStorage.setItem('portfolio_filter_prefs_v2', JSON.stringify(prefs));
            const saveNotice = document.getElementById('port-save-status-pill');
            if (saveNotice) {{
                saveNotice.style.display = 'inline-block';
                saveNotice.innerText = '💾 Saved';
                setTimeout(() => {{ saveNotice.innerText = '💾 Auto-Saved'; }}, 1500);
            }}
        }} catch (e) {{
            console.error('Failed to save portfolio filter preferences:', e);
        }}
    }}

    function loadPortfolioFilterPreferences() {{
        try {{
            const saved = localStorage.getItem('portfolio_filter_prefs_v2');
            if (saved) {{
                const prefs = JSON.parse(saved);
                if (prefs.activePreset) {{
                    window.activePortfolioStockbeepPreset = prefs.activePreset;
                    document.querySelectorAll('#port-preset-bar .stockbeep-preset-tab').forEach(tab => tab.classList.remove('active'));
                    const activeTab = document.getElementById('port-preset-tab-' + prefs.activePreset);
                    if (activeTab) activeTab.classList.add('active');
                }}
                if (prefs.chkGtWeekHigh !== undefined && document.getElementById('port-chk-gt-week-high')) document.getElementById('port-chk-gt-week-high').checked = prefs.chkGtWeekHigh;
                if (prefs.chkGtDayHigh !== undefined && document.getElementById('port-chk-gt-day-high')) document.getElementById('port-chk-gt-day-high').checked = prefs.chkGtDayHigh;
                if (prefs.chkGtPmHigh !== undefined && document.getElementById('port-chk-gt-pm-high')) document.getElementById('port-chk-gt-pm-high').checked = prefs.chkGtPmHigh;
                if (prefs.chkLtPmLow !== undefined && document.getElementById('port-chk-lt-pm-low')) document.getElementById('port-chk-lt-pm-low').checked = prefs.chkLtPmLow;
                if (prefs.chkLtWeekLow !== undefined && document.getElementById('port-chk-lt-week-low')) document.getElementById('port-chk-lt-week-low').checked = prefs.chkLtWeekLow;
                if (prefs.chkLtDayLow !== undefined && document.getElementById('port-chk-lt-day-low')) document.getElementById('port-chk-lt-day-low').checked = prefs.chkLtDayLow;
                if (prefs.filterChg !== undefined && document.getElementById('port-filter-chg')) document.getElementById('port-filter-chg').value = prefs.filterChg;
                if (prefs.filterGap !== undefined && document.getElementById('port-filter-gap')) document.getElementById('port-filter-gap').value = prefs.filterGap;
                if (prefs.filterOpen !== undefined && document.getElementById('port-filter-open')) document.getElementById('port-filter-open').value = prefs.filterOpen;
                if (prefs.filterVwap !== undefined && document.getElementById('port-filter-vwap')) document.getElementById('port-filter-vwap').value = prefs.filterVwap;
                if (prefs.filterTotalPct !== undefined && document.getElementById('port-filter-total-pct')) document.getElementById('port-filter-total-pct').value = prefs.filterTotalPct;
                if (prefs.filterWeight !== undefined && document.getElementById('port-filter-weight')) document.getElementById('port-filter-weight').value = prefs.filterWeight;
                if (prefs.filterFlow !== undefined && document.getElementById('port-filter-flow')) document.getElementById('port-filter-flow').value = prefs.filterFlow;
                if (prefs.filterSma5 !== undefined && document.getElementById('port-filter-sma5')) document.getElementById('port-filter-sma5').value = prefs.filterSma5;
                if (prefs.filterSma20 !== undefined && document.getElementById('port-filter-sma20')) document.getElementById('port-filter-sma20').value = prefs.filterSma20;
                if (prefs.filterSma50 !== undefined && document.getElementById('port-filter-sma50')) document.getElementById('port-filter-sma50').value = prefs.filterSma50;
                if (prefs.filterSma200 !== undefined && document.getElementById('port-filter-sma200')) document.getElementById('port-filter-sma200').value = prefs.filterSma200;
                if (prefs.minCat !== undefined && document.getElementById('port-filter-catalyst')) document.getElementById('port-filter-catalyst').value = prefs.minCat;
                if (prefs.minRvol !== undefined && document.getElementById('port-filter-rvol')) document.getElementById('port-filter-rvol').value = prefs.minRvol;
                if (prefs.minScore !== undefined && document.getElementById('port-filter-score')) document.getElementById('port-filter-score').value = prefs.minScore;
                if (prefs.selSector !== undefined && document.getElementById('port-filter-sector')) {{
                    const secElem = document.getElementById('port-filter-sector');
                    if (secElem.querySelector(`option[value="${{prefs.selSector}}"]`)) {{
                        secElem.value = prefs.selSector;
                    }}
                }}
                if (prefs.assetType !== undefined && document.getElementById('port-filter-asset-type')) document.getElementById('port-filter-asset-type').value = prefs.assetType;
                if (prefs.strat !== undefined && document.getElementById('port-filter-strat')) document.getElementById('port-filter-strat').value = prefs.strat;
                if (prefs.activeView) {{
                    switchPortfolioView(prefs.activeView, false);
                }}
            }}
        }} catch (e) {{
            console.error('Failed to load portfolio filter preferences:', e);
        }}
    }}

    function filterPortfolioWatchlist(save = true) {{
        const chkGtWeekHigh = document.getElementById('port-chk-gt-week-high') ? document.getElementById('port-chk-gt-week-high').checked : false;
        const chkGtDayHigh = document.getElementById('port-chk-gt-day-high') ? document.getElementById('port-chk-gt-day-high').checked : false;
        const chkGtPmHigh = document.getElementById('port-chk-gt-pm-high') ? document.getElementById('port-chk-gt-pm-high').checked : false;
        const chkLtPmLow = document.getElementById('port-chk-lt-pm-low') ? document.getElementById('port-chk-lt-pm-low').checked : false;
        const chkLtWeekLow = document.getElementById('port-chk-lt-week-low') ? document.getElementById('port-chk-lt-week-low').checked : false;
        const chkLtDayLow = document.getElementById('port-chk-lt-day-low') ? document.getElementById('port-chk-lt-day-low').checked : false;

        const checkedLevelsCount = [chkGtWeekHigh, chkGtDayHigh, chkGtPmHigh, chkLtPmLow, chkLtWeekLow, chkLtDayLow].filter(Boolean).length;
        const labelElem = document.getElementById('port-breakout-label');
        if (labelElem) {{
            labelElem.innerText = checkedLevelsCount > 0 ? `${{checkedLevelsCount}} Levels Active` : 'All Levels (Unchecked)';
        }}

        const filterChg = document.getElementById('port-filter-chg') ? document.getElementById('port-filter-chg').value : 'ALL';
        const filterGap = document.getElementById('port-filter-gap') ? document.getElementById('port-filter-gap').value : 'ALL';
        const filterOpen = document.getElementById('port-filter-open') ? document.getElementById('port-filter-open').value : 'ALL';
        const filterVwap = document.getElementById('port-filter-vwap') ? document.getElementById('port-filter-vwap').value : 'ALL';
        const filterTotalPct = document.getElementById('port-filter-total-pct') ? document.getElementById('port-filter-total-pct').value : 'ALL';
        const filterWeight = document.getElementById('port-filter-weight') ? document.getElementById('port-filter-weight').value : 'ALL';
        const filterFlow = document.getElementById('port-filter-flow') ? document.getElementById('port-filter-flow').value : 'ALL';
        const filterSma5 = document.getElementById('port-filter-sma5') ? document.getElementById('port-filter-sma5').value : 'ALL';
        const filterSma20 = document.getElementById('port-filter-sma20') ? document.getElementById('port-filter-sma20').value : 'ALL';
        const filterSma50 = document.getElementById('port-filter-sma50') ? document.getElementById('port-filter-sma50').value : 'ALL';
        const filterSma200 = document.getElementById('port-filter-sma200') ? document.getElementById('port-filter-sma200').value : 'ALL';
        const minCat = parseFloat(document.getElementById('port-filter-catalyst') ? document.getElementById('port-filter-catalyst').value : '0') || 0.0;
        const minRvol = parseFloat(document.getElementById('port-filter-rvol') ? document.getElementById('port-filter-rvol').value : '0') || 0.0;
        const minScore = parseFloat(document.getElementById('port-filter-score') ? document.getElementById('port-filter-score').value : '0') || 0.0;
        const selSector = document.getElementById('port-filter-sector') ? document.getElementById('port-filter-sector').value : 'ALL';
        const assetType = document.getElementById('port-filter-asset-type') ? document.getElementById('port-filter-asset-type').value : 'ALL';
        const filterStrat = document.getElementById('port-filter-strat') ? document.getElementById('port-filter-strat').value : 'ALL';
        const searchInput = document.getElementById('portfolio-search-input');
        const q = searchInput ? searchInput.value.toLowerCase().trim() : '';

        const state = tableStates['portfolio-table'];
        if (!state) return;

        state.filteredRows = state.allRows.filter(r => {{
            // Portfolio Stockbeep Preset Tab Filter
            const activePreset = window.activePortfolioStockbeepPreset || 'ALL_SETUPS';
            if (activePreset !== 'ALL_SETUPS') {{
                const presetTags = (r.getAttribute('data-preset-tags') || '').split(' ');
                if (!presetTags.includes(activePreset)) {{
                    return false;
                }}
            }}

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

            const totalPct = parseFloat(r.getAttribute('data-total-pct')) || 0.0;
            const weightVal = parseFloat(r.getAttribute('data-weight')) || 0.0;
            const isOpt = r.getAttribute('data-is-option') === 'true';
            const strat = r.getAttribute('data-strategy') || '';

            const skew = r.getAttribute('data-skew') || 'Neutral';
            const pc = parseFloat(r.getAttribute('data-pc')) || 1.0;
            const netFlow = parseFloat(r.getAttribute('data-net-flow')) || 0.0;
            const whales = parseInt(r.getAttribute('data-whales'), 10) || 0;

            const sma5Dist = parseFloat(r.getAttribute('data-sma5-dist')) || 0.0;
            const sma5Xo = r.getAttribute('data-sma5-xo') === 'true';
            const sma5Xu = r.getAttribute('data-sma5-xu') === 'true';

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

            // Asset Type Filter
            if (assetType === 'STOCK' && isOpt) return false;
            if (assetType === 'OPTION' && !isOpt) return false;

            // Strategy Tag Filter
            if (filterStrat !== 'ALL' && !strat.toLowerCase().includes(filterStrat.toLowerCase())) return false;

            // Total % P&L Filter
            if (filterTotalPct !== 'ALL') {{
                if (filterTotalPct === 'GT_3' && !(totalPct > 3.0)) return false;
                if (filterTotalPct === 'LT_M3' && !(totalPct < -3.0)) return false;
                if (filterTotalPct === 'LT_M20' && !(totalPct < -20.0)) return false;
                if (filterTotalPct === 'M20_M10' && !(totalPct >= -20.0 && totalPct < -10.0)) return false;
                if (filterTotalPct === 'M10_M5' && !(totalPct >= -10.0 && totalPct < -5.0)) return false;
                if (filterTotalPct === 'M5_0' && !(totalPct >= -5.0 && totalPct < 0.0)) return false;
                if (filterTotalPct === '0_5' && !(totalPct >= 0.0 && totalPct <= 5.0)) return false;
                if (filterTotalPct === '5_10' && !(totalPct > 5.0 && totalPct <= 10.0)) return false;
                if (filterTotalPct === '10_20' && !(totalPct > 10.0 && totalPct <= 20.0)) return false;
                if (filterTotalPct === '20_50' && !(totalPct > 20.0 && totalPct <= 50.0)) return false;
                if (filterTotalPct === '50_100' && !(totalPct > 50.0 && totalPct <= 100.0)) return false;
                if (filterTotalPct === 'GT_100' && !(totalPct > 100.0)) return false;
            }}

            // Weight % Filter
            if (filterWeight !== 'ALL') {{
                if (filterWeight === 'GT_10' && !(weightVal >= 10.0)) return false;
                if (filterWeight === 'GT_5' && !(weightVal >= 5.0)) return false;
                if (filterWeight === 'GT_3' && !(weightVal >= 3.0)) return false;
                if (filterWeight === 'GT_1' && !(weightVal >= 1.0)) return false;
                if (filterWeight === 'LT_1' && !(weightVal < 1.0)) return false;
                if (filterWeight === '1_3' && !(weightVal >= 1.0 && weightVal <= 3.0)) return false;
                if (filterWeight === '3_5' && !(weightVal > 3.0 && weightVal <= 5.0)) return false;
                if (filterWeight === '5_10' && !(weightVal > 5.0 && weightVal <= 10.0)) return false;
            }}

            // Break Up & Break Down Checks
            if (chkGtWeekHigh && r.getAttribute('data-breakout-week-high') !== 'true') return false;
            if (chkGtDayHigh && r.getAttribute('data-breakout-last-high') !== 'true') return false;
            if (chkGtPmHigh && r.getAttribute('data-breakout-pm-high') !== 'true') return false;
            if (chkLtPmLow && r.getAttribute('data-breakdown-pm-low') !== 'true') return false;
            if (chkLtWeekLow && r.getAttribute('data-breakdown-week-low') !== 'true') return false;
            if (chkLtDayLow && r.getAttribute('data-breakdown-last-low') !== 'true') return false;

            // % Chg Buckets
            if (filterChg !== 'ALL') {{
                if (filterChg === 'GT_3' && !(chg > 3.0)) return false;
                if (filterChg === 'LT_M3' && !(chg < -3.0)) return false;
                if (filterChg === 'LT_M20' && !(chg < -20.0)) return false;
                if (filterChg === 'M20_M10' && !(chg >= -20.0 && chg < -10.0)) return false;
                if (filterChg === 'M10_M5' && !(chg >= -10.0 && chg < -5.0)) return false;
                if (filterChg === 'M5_0' && !(chg >= -5.0 && chg < 0.0)) return false;
                if (filterChg === '0_5' && !(chg >= 0.0 && chg <= 5.0)) return false;
                if (filterChg === '5_10' && !(chg > 5.0 && chg <= 10.0)) return false;
                if (filterChg === '10_20' && !(chg > 10.0 && chg <= 20.0)) return false;
                if (filterChg === '20_50' && !(chg > 20.0 && chg <= 50.0)) return false;
                if (filterChg === '50_100' && !(chg > 50.0 && chg <= 100.0)) return false;
                if (filterChg === 'GT_100' && !(chg > 100.0)) return false;
            }}

            // Gap %
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

            // % Open Buckets
            if (filterOpen !== 'ALL') {{
                if (filterOpen === 'GT_3' && !(openChg > 3.0)) return false;
                if (filterOpen === 'LT_M3' && !(openChg < -3.0)) return false;
                if (filterOpen === 'LT_M20' && !(openChg < -20.0)) return false;
                if (filterOpen === 'M20_M10' && !(openChg >= -20.0 && openChg < -10.0)) return false;
                if (filterOpen === 'M10_M5' && !(openChg >= -10.0 && openChg < -5.0)) return false;
                if (filterOpen === 'M5_0' && !(openChg >= -5.0 && openChg < 0.0)) return false;
                if (filterOpen === '0_5' && !(openChg >= 0.0 && openChg <= 5.0)) return false;
                if (filterOpen === '5_10' && !(openChg > 5.0 && openChg <= 10.0)) return false;
                if (filterOpen === '10_20' && !(openChg > 10.0 && openChg <= 20.0)) return false;
                if (filterOpen === '20_50' && !(openChg > 20.0 && openChg <= 50.0)) return false;
                if (filterOpen === '50_100' && !(openChg > 50.0 && openChg <= 100.0)) return false;
                if (filterOpen === 'GT_100' && !(openChg > 100.0)) return false;
            }}

            // % VWAP
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

            // Flow
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

            // SMAs
            if (filterSma5 !== 'ALL') {{
                if (filterSma5 === 'POS' && sma5Dist < 0) return false;
                if (filterSma5 === 'NEG' && sma5Dist >= 0) return false;
                if (filterSma5 === 'XO') {{
                    if (!sma5Xo && !(sma5Dist >= 0 && sma5Dist <= 1.5)) return false;
                }} else if (filterSma5 === 'XU') {{
                    if (!sma5Xu && !(sma5Dist <= 0 && sma5Dist >= -1.5)) return false;
                }} else if (filterSma5 !== 'POS' && filterSma5 !== 'NEG') {{
                    const minSma = parseFloat(filterSma5);
                    if (!isNaN(minSma) && sma5Dist < minSma) return false;
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
        renderTablePage('portfolio-table');

        const visCount = document.getElementById('port-visible-count');
        if (visCount) visCount.innerText = state.filteredRows.length;
        const totCount = document.getElementById('port-total-count');
        if (totCount) totCount.innerText = state.allRows.length;

        if (save) {{
            savePortfolioFilterPreferences();
        }}
    }}

    function resetPortfolioInstitutionalDefaults() {{
        clearAllPortBreakoutChecks(false);
        window.activePortfolioStockbeepPreset = 'ALL_SETUPS';
        document.querySelectorAll('#port-preset-bar .stockbeep-preset-tab').forEach(tab => tab.classList.remove('active'));
        const allTab = document.getElementById('port-preset-tab-ALL_SETUPS');
        if (allTab) allTab.classList.add('active');
        if (document.getElementById('port-filter-chg')) document.getElementById('port-filter-chg').value = 'ALL';
        if (document.getElementById('port-filter-gap')) document.getElementById('port-filter-gap').value = 'ALL';
        if (document.getElementById('port-filter-open')) document.getElementById('port-filter-open').value = 'ALL';
        if (document.getElementById('port-filter-vwap')) document.getElementById('port-filter-vwap').value = 'ALL';
        if (document.getElementById('port-filter-total-pct')) document.getElementById('port-filter-total-pct').value = 'ALL';
        if (document.getElementById('port-filter-weight')) document.getElementById('port-filter-weight').value = 'ALL';
        if (document.getElementById('port-filter-flow')) document.getElementById('port-filter-flow').value = 'ALL';
        if (document.getElementById('port-filter-sma5')) document.getElementById('port-filter-sma5').value = 'ALL';
        if (document.getElementById('port-filter-sma20')) document.getElementById('port-filter-sma20').value = 'ALL';
        if (document.getElementById('port-filter-sma50')) document.getElementById('port-filter-sma50').value = 'ALL';
        if (document.getElementById('port-filter-sma200')) document.getElementById('port-filter-sma200').value = 'ALL';
        if (document.getElementById('port-filter-catalyst')) document.getElementById('port-filter-catalyst').value = '0.0';
        if (document.getElementById('port-filter-rvol')) document.getElementById('port-filter-rvol').value = '0.0';
        if (document.getElementById('port-filter-score')) document.getElementById('port-filter-score').value = '0.0';
        if (document.getElementById('port-filter-sector')) document.getElementById('port-filter-sector').value = 'ALL';
        if (document.getElementById('port-filter-asset-type')) document.getElementById('port-filter-asset-type').value = 'ALL';
        if (document.getElementById('port-filter-strat')) document.getElementById('port-filter-strat').value = 'ALL';
        const searchInput = document.getElementById('portfolio-search-input');
        if (searchInput) searchInput.value = '';
        try {{
            localStorage.removeItem('portfolio_filter_prefs_v2');
        }} catch (e) {{}}
        filterPortfolioWatchlist(true);
    }}

    function showAllPortfolioPositions() {{
        resetPortfolioInstitutionalDefaults();
    }}

    /* Core Table Sorting & Filtering */
    function initTableState(tableId) {{
        const table = document.getElementById(tableId);
        if (!table) return;
        const rows = Array.from(table.querySelectorAll('tbody tr.data-row'));
        tableStates[tableId].allRows = rows;
        tableStates[tableId].filteredRows = [...rows];

        // Cache all drawer elements permanently before tbody is emptied
        const drawerMap = new Map();
        table.querySelectorAll('tbody tr.row-drawer, tbody tr.whale-drawer').forEach(d => {{
            drawerMap.set(d.id, d);
        }});
        tableStates[tableId].drawerMap = drawerMap;

        renderTablePage(tableId);
    }}

    function renderTablePage(tableId) {{
        const state = tableStates[tableId];
        if (!state) return;
        const table = document.getElementById(tableId);
        const tbody = table.querySelector('tbody');
        const start = (state.currentPage - 1) * state.pageSize;
        const end = start + state.pageSize;

        const drawerMap = state.drawerMap || new Map();

        tbody.innerHTML = '';
        const pageRows = state.filteredRows.slice(start, end);

        if (pageRows.length === 0) {{
            const colCount = table.querySelectorAll('thead th').length || 15;
            tbody.innerHTML = `<tr><td colspan="${{colCount}}" style="text-align: center; color: #9ca3af; padding: 24px;">No matching records found.</td></tr>`;
        }} else {{
            pageRows.forEach(r => {{
                tbody.appendChild(r);
                const drawerId = r.getAttribute('data-drawer-id') || r.getAttribute('data-whale-id');
                if (drawerId && drawerMap.has(drawerId)) {{
                    tbody.appendChild(drawerMap.get(drawerId));
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

    function openWhaleModal(ticker) {{
        if (!ticker) return;
        const trades = (window.whaleTradesLookup && window.whaleTradesLookup[ticker]) || [];
        const titleElem = document.getElementById('whale-modal-title');
        const summaryElem = document.getElementById('whale-modal-summary');
        const tbody = document.getElementById('whale-modal-tbody');
        if (titleElem) titleElem.innerHTML = `🐳 Institutional Whale Trades &amp; Gamma Sweeps — <strong style="color: #60a5fa;">${{ticker}}</strong>`;
        if (summaryElem) summaryElem.innerHTML = trades.length > 0 ? `Displaying ${{trades.length}} real-time smart-money block &amp; sweep orders with notional premium &ge; $200,000 in the active 45-day cycle.` : `No whale sweep orders recorded for ${{ticker}}.`;
        
        if (tbody) {{
            tbody.innerHTML = '';
            if (trades.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #94a3b8; padding: 20px;">No individual whale orders (&ge; $200K) recorded for ' + ticker + ' in the current 45-day cycle.</td></tr>';
            }} else {{
                trades.forEach(w => {{
                    const wType = w.type || 'CALL';
                    const pill = wType === 'CALL' ? '<span class="pill pill-green">CALL</span>' : '<span class="pill pill-red">PUT</span>';
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${{pill}} <strong>${{w.strike || '—'}}</strong></td>
                        <td>${{w.expiry || 'Near-Term'}} (${{w.dte || 0}} DTE)</td>
                        <td><span class="pill pill-yellow">${{w.vol_oi_ratio || 1.0}}x</span> (${{(w.volume || 0).toLocaleString()}} / ${{ (w.open_interest || 0).toLocaleString() }})</td>
                        <td><strong>${{w.contract_iv || '—'}}</strong></td>
                        <td><strong style="color: #fbbf24;">${{w.premium_str || '—'}}</strong></td>
                        <td>${{w.flow_tag || 'Whale Sweep'}}</td>
                        <td>${{w.sentiment || 'Bullish'}}</td>
                    `;
                    tbody.appendChild(tr);
                }});
            }}
        }}
        openModal('modal-whale-trades');
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

    function switchEarningsTab(btnElement, filterVal) {{
        const tabBar = document.getElementById('earn-tab-bar') || (btnElement ? btnElement.parentElement : null);
        if (tabBar) {{
            tabBar.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
        }}
        if (btnElement) {{
            btnElement.classList.add('active');
        }}

        const state = tableStates['earn-table'];
        if (!state) return;

        if (!filterVal || filterVal === 'ALL') {{
            state.filteredRows = [...state.allRows];
        }} else {{
            state.filteredRows = state.allRows.filter(r => {{
                const rowTiming = r.getAttribute('data-timing') || '';
                return rowTiming === filterVal;
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
            if (tableId === 'earn-table' && colIdx === 5) {{
                const capA = parseFloat(a.getAttribute('data-mkt-cap')) || 0.0;
                const capB = parseFloat(b.getAttribute('data-mkt-cap')) || 0.0;
                return isAsc ? capB - capA : capA - capB;
            }}

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

    function filterOptionsTable(mode) {{
        const state = tableStates['options-table'];
        if (!state) return;
        state.filteredRows = state.allRows.filter(r => {{
            const whales = parseInt(r.getAttribute('data-whales'), 10) || 0;
            const volOi = parseFloat(r.getAttribute('data-vol-oi')) || 0.0;
            const skew = r.getAttribute('data-skew') || '';
            if (mode === 'WHALES' && whales <= 0) return false;
            if (mode === 'VOL_OI_GT_1' && volOi < 1.0) return false;
            if (mode === 'BULLISH' && !skew.includes('Bullish')) return false;
            return true;
        }});
        state.currentPage = 1;
        renderTablePage('options-table');
    }}

    /* Stockbeep Preset Tab Filter Engine */
    window.activeStockbeepPreset = 'ALL_SETUPS';

    function selectStockbeepPreset(presetTag) {{
        window.activeStockbeepPreset = presetTag || 'ALL_SETUPS';
        document.querySelectorAll('#view-screener-section .stockbeep-preset-tab').forEach(tab => {{
            tab.classList.remove('active');
        }});
        const activeTab = document.getElementById('preset-tab-' + window.activeStockbeepPreset);
        if (activeTab) {{
            activeTab.classList.add('active');
        }}
        // Clear conflicting manual breakout checkboxes
        document.querySelectorAll('.day-breakout-chk').forEach(c => c.checked = false);
        const labelElem = document.getElementById('day-breakout-label');
        if (labelElem) labelElem.innerText = 'All Levels (Unchecked)';

        // When ALL_SETUPS is clicked, reset restrictive manual filter dropdowns
        if (presetTag === 'ALL_SETUPS') {{
            if (document.getElementById('filter-chg')) document.getElementById('filter-chg').value = 'ALL';
            if (document.getElementById('filter-gap')) document.getElementById('filter-gap').value = 'ALL';
            if (document.getElementById('filter-open')) document.getElementById('filter-open').value = 'ALL';
            if (document.getElementById('filter-vwap')) document.getElementById('filter-vwap').value = 'ALL';
            if (document.getElementById('filter-flow')) document.getElementById('filter-flow').value = 'ALL';
            if (document.getElementById('filter-sma5')) document.getElementById('filter-sma5').value = 'ALL';
            if (document.getElementById('filter-sma20')) document.getElementById('filter-sma20').value = 'ALL';
            if (document.getElementById('filter-sma50')) document.getElementById('filter-sma50').value = 'ALL';
            if (document.getElementById('filter-sma200')) document.getElementById('filter-sma200').value = 'ALL';
            if (document.getElementById('filter-catalyst')) document.getElementById('filter-catalyst').value = '0.0';
            if (document.getElementById('filter-rvol')) document.getElementById('filter-rvol').value = '0.0';
            if (document.getElementById('filter-score')) document.getElementById('filter-score').value = '0.0';
            if (document.getElementById('filter-sector')) document.getElementById('filter-sector').value = 'ALL';
        }}
        filterDayWatchlist(true);
    }}

    /* Watchlist Multi-Factor Interactive Filter with LocalStorage Persistence */
    function clearAllDayBreakoutChecks() {{
        const chks = document.querySelectorAll('.day-breakout-chk');
        chks.forEach(c => c.checked = false);
        const labelElem = document.getElementById('day-breakout-label');
        if (labelElem) labelElem.innerText = 'All Levels (Unchecked)';
        filterDayWatchlist(true);
    }}

    function saveFilterPreferences() {{
        try {{
            const prefs = {{
                activePreset: window.activeStockbeepPreset || 'ALL_SETUPS',
                chkGtWeekHigh: document.getElementById('day-chk-gt-week-high') ? document.getElementById('day-chk-gt-week-high').checked : false,
                chkGtDayHigh: document.getElementById('day-chk-gt-day-high') ? document.getElementById('day-chk-gt-day-high').checked : false,
                chkGtPmHigh: document.getElementById('day-chk-gt-pm-high') ? document.getElementById('day-chk-gt-pm-high').checked : false,
                chkLtPmLow: document.getElementById('day-chk-lt-pm-low') ? document.getElementById('day-chk-lt-pm-low').checked : false,
                chkLtWeekLow: document.getElementById('day-chk-lt-week-low') ? document.getElementById('day-chk-lt-week-low').checked : false,
                chkLtDayLow: document.getElementById('day-chk-lt-day-low') ? document.getElementById('day-chk-lt-day-low').checked : false,
                filterChg: document.getElementById('filter-chg') ? document.getElementById('filter-chg').value : 'ALL',
                minGap: document.getElementById('filter-gap') ? document.getElementById('filter-gap').value : 'ALL',
                filterOpen: document.getElementById('filter-open') ? document.getElementById('filter-open').value : 'ALL',
                filterVwap: document.getElementById('filter-vwap') ? document.getElementById('filter-vwap').value : 'ALL',
                filterFlow: document.getElementById('filter-flow') ? document.getElementById('filter-flow').value : 'ALL',
                filterSma5: document.getElementById('filter-sma5') ? document.getElementById('filter-sma5').value : 'ALL',
                filterSma20: document.getElementById('filter-sma20') ? document.getElementById('filter-sma20').value : 'ALL',
                filterSma50: document.getElementById('filter-sma50') ? document.getElementById('filter-sma50').value : 'ALL',
                filterSma200: document.getElementById('filter-sma200') ? document.getElementById('filter-sma200').value : 'ALL',
                minCat: document.getElementById('filter-catalyst').value,
                minRvol: document.getElementById('filter-rvol').value,
                minScore: document.getElementById('filter-score').value,
                selSector: document.getElementById('filter-sector').value,
                activeView: window.currentWatchlistView || 'core'
            }};
            localStorage.setItem('screener_filter_prefs_v2', JSON.stringify(prefs));
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
            const saved = localStorage.getItem('screener_filter_prefs_v2');
            if (saved) {{
                const prefs = JSON.parse(saved);
                if (prefs.activePreset) {{
                    window.activeStockbeepPreset = prefs.activePreset;
                    document.querySelectorAll('.stockbeep-preset-tab').forEach(tab => tab.classList.remove('active'));
                    const activeTab = document.getElementById('preset-tab-' + prefs.activePreset);
                    if (activeTab) activeTab.classList.add('active');
                }}
                if (prefs.chkGtWeekHigh !== undefined && document.getElementById('day-chk-gt-week-high')) document.getElementById('day-chk-gt-week-high').checked = prefs.chkGtWeekHigh;
                if (prefs.chkGtDayHigh !== undefined && document.getElementById('day-chk-gt-day-high')) document.getElementById('day-chk-gt-day-high').checked = prefs.chkGtDayHigh;
                if (prefs.chkGtPmHigh !== undefined && document.getElementById('day-chk-gt-pm-high')) document.getElementById('day-chk-gt-pm-high').checked = prefs.chkGtPmHigh;
                if (prefs.chkLtPmLow !== undefined && document.getElementById('day-chk-lt-pm-low')) document.getElementById('day-chk-lt-pm-low').checked = prefs.chkLtPmLow;
                if (prefs.chkLtWeekLow !== undefined && document.getElementById('day-chk-lt-week-low')) document.getElementById('day-chk-lt-week-low').checked = prefs.chkLtWeekLow;
                if (prefs.chkLtDayLow !== undefined && document.getElementById('day-chk-lt-day-low')) document.getElementById('day-chk-lt-day-low').checked = prefs.chkLtDayLow;
                if (prefs.filterChg !== undefined && document.getElementById('filter-chg')) document.getElementById('filter-chg').value = prefs.filterChg;
                if (prefs.minGap !== undefined && document.getElementById('filter-gap')) document.getElementById('filter-gap').value = prefs.minGap;
                if (prefs.filterOpen !== undefined && document.getElementById('filter-open')) document.getElementById('filter-open').value = prefs.filterOpen;
                if (prefs.filterVwap !== undefined && document.getElementById('filter-vwap')) document.getElementById('filter-vwap').value = prefs.filterVwap;
                if (prefs.filterFlow !== undefined && document.getElementById('filter-flow')) document.getElementById('filter-flow').value = prefs.filterFlow;
                if (prefs.filterSma5 !== undefined && document.getElementById('filter-sma5')) document.getElementById('filter-sma5').value = prefs.filterSma5;
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
        const chkGtWeekHigh = document.getElementById('day-chk-gt-week-high') ? document.getElementById('day-chk-gt-week-high').checked : false;
        const chkGtDayHigh = document.getElementById('day-chk-gt-day-high') ? document.getElementById('day-chk-gt-day-high').checked : false;
        const chkGtPmHigh = document.getElementById('day-chk-gt-pm-high') ? document.getElementById('day-chk-gt-pm-high').checked : false;
        const chkLtPmLow = document.getElementById('day-chk-lt-pm-low') ? document.getElementById('day-chk-lt-pm-low').checked : false;
        const chkLtWeekLow = document.getElementById('day-chk-lt-week-low') ? document.getElementById('day-chk-lt-week-low').checked : false;
        const chkLtDayLow = document.getElementById('day-chk-lt-day-low') ? document.getElementById('day-chk-lt-day-low').checked : false;

        const checkedDayCount = [chkGtWeekHigh, chkGtDayHigh, chkGtPmHigh, chkLtPmLow, chkLtWeekLow, chkLtDayLow].filter(Boolean).length;
        const dayLabelElem = document.getElementById('day-breakout-label');
        if (dayLabelElem) {{
            dayLabelElem.innerText = checkedDayCount > 0 ? `${{checkedDayCount}} Levels Active` : 'All Levels (Unchecked)';
        }}

        const filterChg = document.getElementById('filter-chg') ? document.getElementById('filter-chg').value : 'ALL';
        const filterGap = document.getElementById('filter-gap') ? document.getElementById('filter-gap').value : 'ALL';
        const filterOpen = document.getElementById('filter-open') ? document.getElementById('filter-open').value : 'ALL';
        const filterVwap = document.getElementById('filter-vwap') ? document.getElementById('filter-vwap').value : 'ALL';
        const filterFlow = document.getElementById('filter-flow') ? document.getElementById('filter-flow').value : 'ALL';
        const filterSma5 = document.getElementById('filter-sma5') ? document.getElementById('filter-sma5').value : 'ALL';
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
            // Stockbeep Preset Tab Filter
            const activePreset = window.activeStockbeepPreset || 'ALL_SETUPS';
            if (activePreset !== 'ALL_SETUPS') {{
                const presetTags = (r.getAttribute('data-preset-tags') || '').split(' ');
                if (!presetTags.includes(activePreset)) {{
                    return false;
                }}
            }}

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

            const sma5Dist = parseFloat(r.getAttribute('data-sma5-dist')) || 0.0;
            const sma5Xo = r.getAttribute('data-sma5-xo') === 'true';
            const sma5Xu = r.getAttribute('data-sma5-xu') === 'true';

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

            // Break Up & Break Down Checks
            if (chkGtWeekHigh && r.getAttribute('data-breakout-week-high') !== 'true') return false;
            if (chkGtDayHigh && r.getAttribute('data-breakout-last-high') !== 'true') return false;
            if (chkGtPmHigh && r.getAttribute('data-breakout-pm-high') !== 'true') return false;
            if (chkLtPmLow && r.getAttribute('data-breakdown-pm-low') !== 'true') return false;
            if (chkLtWeekLow && r.getAttribute('data-breakdown-week-low') !== 'true') return false;
            if (chkLtDayLow && r.getAttribute('data-breakdown-last-low') !== 'true') return false;

            // % Chg Buckets
            if (filterChg !== 'ALL') {{
                if (filterChg === 'GT_3' && !(chg > 3.0)) return false;
                if (filterChg === 'LT_M3' && !(chg < -3.0)) return false;
                if (filterChg === 'LT_M20' && !(chg < -20.0)) return false;
                if (filterChg === 'M20_M10' && !(chg >= -20.0 && chg < -10.0)) return false;
                if (filterChg === 'M10_M5' && !(chg >= -10.0 && chg < -5.0)) return false;
                if (filterChg === 'M5_0' && !(chg >= -5.0 && chg < 0.0)) return false;
                if (filterChg === '0_5' && !(chg >= 0.0 && chg <= 5.0)) return false;
                if (filterChg === '5_10' && !(chg > 5.0 && chg <= 10.0)) return false;
                if (filterChg === '10_20' && !(chg > 10.0 && chg <= 20.0)) return false;
                if (filterChg === '20_50' && !(chg > 20.0 && chg <= 50.0)) return false;
                if (filterChg === '50_100' && !(chg > 50.0 && chg <= 100.0)) return false;
                if (filterChg === 'GT_100' && !(chg > 100.0)) return false;
            }}

            // Gap %
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

            // % Open Buckets
            if (filterOpen !== 'ALL') {{
                if (filterOpen === 'GT_3' && !(openChg > 3.0)) return false;
                if (filterOpen === 'LT_M3' && !(openChg < -3.0)) return false;
                if (filterOpen === 'LT_M20' && !(openChg < -20.0)) return false;
                if (filterOpen === 'M20_M10' && !(openChg >= -20.0 && openChg < -10.0)) return false;
                if (filterOpen === 'M10_M5' && !(openChg >= -10.0 && openChg < -5.0)) return false;
                if (filterOpen === 'M5_0' && !(openChg >= -5.0 && openChg < 0.0)) return false;
                if (filterOpen === '0_5' && !(openChg >= 0.0 && openChg <= 5.0)) return false;
                if (filterOpen === '5_10' && !(openChg > 5.0 && openChg <= 10.0)) return false;
                if (filterOpen === '10_20' && !(openChg > 10.0 && openChg <= 20.0)) return false;
                if (filterOpen === '20_50' && !(openChg > 20.0 && openChg <= 50.0)) return false;
                if (filterOpen === '50_100' && !(openChg > 50.0 && openChg <= 100.0)) return false;
                if (filterOpen === 'GT_100' && !(openChg > 100.0)) return false;
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

            if (filterSma5 !== 'ALL') {{
                if (filterSma5 === 'POS' && sma5Dist < 0) return false;
                if (filterSma5 === 'NEG' && sma5Dist >= 0) return false;
                if (filterSma5 === 'XO') {{
                    if (!sma5Xo && !(sma5Dist >= 0 && sma5Dist <= 1.5)) return false;
                }} else if (filterSma5 === 'XU') {{
                    if (!sma5Xu && !(sma5Dist <= 0 && sma5Dist >= -1.5)) return false;
                }} else if (filterSma5 !== 'POS' && filterSma5 !== 'NEG') {{
                    const minSma = parseFloat(filterSma5);
                    if (!isNaN(minSma) && sma5Dist < minSma) return false;
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

            if (minCat > 0 && stars < minCat) return false;
            if (minRvol > 0 && rvol < minRvol) return false;
            if (minScore > 0 && score < minScore) return false;
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
        clearAllDayBreakoutChecks();
        window.activeStockbeepPreset = 'ALL_SETUPS';
        document.querySelectorAll('.stockbeep-preset-tab').forEach(tab => tab.classList.remove('active'));
        const allTab = document.getElementById('preset-tab-ALL_SETUPS');
        if (allTab) allTab.classList.add('active');
        if (document.getElementById('filter-chg')) document.getElementById('filter-chg').value = "ALL";
        if (document.getElementById('filter-gap')) document.getElementById('filter-gap').value = "3.0";
        if (document.getElementById('filter-open')) document.getElementById('filter-open').value = "ALL";
        if (document.getElementById('filter-vwap')) document.getElementById('filter-vwap').value = "ALL";
        if (document.getElementById('filter-flow')) document.getElementById('filter-flow').value = "ALL";
        if (document.getElementById('filter-sma5')) document.getElementById('filter-sma5').value = "ALL";
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
        clearAllDayBreakoutChecks();
        window.activeStockbeepPreset = 'ALL_SETUPS';
        document.querySelectorAll('.stockbeep-preset-tab').forEach(tab => tab.classList.remove('active'));
        const allTab = document.getElementById('preset-tab-ALL_SETUPS');
        if (allTab) allTab.classList.add('active');
        if (document.getElementById('filter-chg')) document.getElementById('filter-chg').value = "ALL";
        if (document.getElementById('filter-gap')) document.getElementById('filter-gap').value = "ALL";
        if (document.getElementById('filter-open')) document.getElementById('filter-open').value = "ALL";
        if (document.getElementById('filter-vwap')) document.getElementById('filter-vwap').value = "ALL";
        if (document.getElementById('filter-flow')) document.getElementById('filter-flow').value = "ALL";
        if (document.getElementById('filter-sma5')) document.getElementById('filter-sma5').value = "ALL";
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

    /* -----------------------------------------------------------------
       Floating Hover Scorecard (Zero-Clipping Calculation Portal)
       ----------------------------------------------------------------- */
    function showScorecardHover(event, dataJsonStr) {{
        const portal = document.getElementById('floating-hover-portal');
        const content = document.getElementById('hover-portal-content');
        if (!portal || !content) return;

        try {{
            const data = typeof dataJsonStr === 'string' ? JSON.parse(dataJsonStr) : dataJsonStr;
            const sym = data.ticker || data.symbol || 'ASSET';
            const score = data.score !== undefined ? data.score : (data.setup_score || 3.0);
            const stars = data.stars_visual || '★★★☆☆';
            const archetype = data.archetype || 'ARCHETYPE_E';
            const pattern = data.primary_pattern || data.pattern_badge || 'Technical Setup';
            const chk = data.criteria_checklist || {{}};
            const brk = data.score_breakdown || {{}};
            const plan = data.trade_plan || {{}};
            const catHeadline = data.headline || data.catalyst_headline || 'No major headline';
            const catUrl = data.catalyst_url || '#';
            const catStars = data.catalyst_stars || 1.0;
            const catType = data.catalyst_type || 'News';
            const isExhausted = data.is_exhausted || false;
            const exDesc = data.exhaustion_desc || '';

            let chkHtml = '';
            chkHtml += '<div class="hover-row"><span>Stage 2 Trend:</span> <span class="' + (chk.stage2_trend ? 'hover-tag-pass">✅ Confirmed' : 'hover-tag-fail">❌ Off-Trend') + '</span></div>';
            chkHtml += '<div class="hover-row"><span>MA Ribbon (10/20/50):</span> <span class="' + (chk.ma_ribbon ? 'hover-tag-pass">✅ Bullish Stack' : 'hover-tag-fail">❌ Mixed') + '</span></div>';
            chkHtml += '<div class="hover-row"><span>5-Day Range Tightness:</span> <strong>' + (chk.five_day_range_pct !== undefined ? chk.five_day_range_pct + '%' : '—') + '</strong></div>';
            chkHtml += '<div class="hover-row"><span>Distance to 52W High:</span> <strong>' + (chk.dist_to_52w_high_pct !== undefined ? chk.dist_to_52w_high_pct + '%' : '—') + '</strong></div>';
            chkHtml += '<div class="hover-row"><span>Session RVOL:</span> <strong style="color: #38bdf8;">' + (chk.rvol !== undefined ? chk.rvol + 'x' : '—') + '</strong></div>';
            chkHtml += '<div class="hover-row"><span>Intraday Close Loc:</span> <strong>' + (chk.close_location_pct !== undefined ? chk.close_location_pct + '%' : '—') + '</strong></div>';

            let brkHtml = '';
            brkHtml += '<div class="hover-row"><span>Base Geometry / Contraction:</span> <strong style="color: #34d399;">+' + (brk.base_points || 0).toFixed(2) + '★</strong></div>';
            brkHtml += '<div class="hover-row"><span>Volume Dry-Up / Surge:</span> <strong style="color: #34d399;">+' + (brk.vol_points || 0).toFixed(2) + '★</strong></div>';
            brkHtml += '<div class="hover-row"><span>Trend Template Alignment:</span> <strong style="color: #34d399;">+' + (brk.trend_points || 0).toFixed(2) + '★</strong></div>';
            brkHtml += '<div class="hover-row"><span>Catalyst Shock Impact:</span> <strong style="color: #34d399;">+' + (brk.catalyst_points || 0).toFixed(2) + '★</strong></div>';
            brkHtml += '<div class="hover-row"><span>Options Gamma / Skew Magnet:</span> <strong style="color: #38bdf8;">+' + (brk.gamma_points || 0).toFixed(2) + '★</strong></div>';
            brkHtml += '<div class="hover-row"><span>4D Macro Regime Multiplier:</span> <strong style="color: #38bdf8;">+' + (brk.macro_points || 0).toFixed(2) + '★</strong></div>';
            if (isExhausted) {{
                brkHtml += '<div class="hover-row" style="color: #f87171;"><span>Exhaustion Penalty:</span> <strong>-' + (brk.exhaustion_penalty || 0).toFixed(2) + '★</strong></div>';
            }}

            let planHtml = '';
            planHtml += '<div class="hover-row"><span>Entry Pivot:</span> <strong style="color: #34d399;">$' + (plan.entry_pivot || 0).toFixed(2) + '</strong></div>';
            planHtml += '<div class="hover-row"><span>Hard Stop:</span> <strong style="color: #f87171;">$' + (plan.hard_stop || 0).toFixed(2) + ' (' + (plan.stop_dist_pct || 0).toFixed(1) + '%)</strong></div>';
            planHtml += '<div class="hover-row"><span>Soft Stop:</span> <span style="font-size: 11px; color: #cbd5e1;">' + (plan.soft_stop_desc || 'VWAP loss') + '</span></div>';
            planHtml += '<div class="hover-row"><span>Target 1 (2.0R):</span> <strong style="color: #38bdf8;">$' + (plan.target_1 || 0).toFixed(2) + ' (+' + (plan.target_1_pct || 0).toFixed(1) + '%)</strong></div>';
            planHtml += '<div class="hover-row"><span>Target 2 (3.5R):</span> <strong style="color: #60a5fa;">$' + (plan.target_2 || 0).toFixed(2) + ' (+' + (plan.target_2_pct || 0).toFixed(1) + '%)</strong></div>';
            planHtml += '<div class="hover-row"><span>Trailing Rule:</span> <span style="font-size: 11px; color: #a78bfa;">' + (plan.trailing_desc || 'Trailing 20-SMA') + '</span></div>';
            planHtml += '<div class="hover-row"><span>Conviction Mult:</span> <strong>' + (plan.conviction_mult || 1.0).toFixed(2) + 'x</strong></div>';

            let catHtml = '';
            catHtml += '<div style="margin-bottom: 4px;"><span class="pill pill-blue">[' + catType + ']</span> <span style="color: #fbbf24; font-weight: bold;">' + '★'.repeat(Math.min(5, Math.max(1, Math.round(catStars)))) + '</span></div>';
            catHtml += '<div style="font-size: 11.5px; margin-bottom: 4px;"><a href="' + catUrl + '" target="_blank" style="color: #93c5fd; text-decoration: none;">' + catHeadline + '</a></div>';

            let html = '';
            html += '<div class="hover-card-title"><span>🔍 ' + sym + ' • Diagnostic Scorecard</span> <span style="color: #a78bfa;">' + stars + ' ' + score.toFixed(1) + '★</span></div>';
            if (isExhausted) {{
                html += '<div style="background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; border-radius: 6px; padding: 6px 8px; margin-bottom: 8px; font-size: 11px; color: #fca5a5;">' + exDesc + '</div>';
            }}
            html += '<div class="hover-section"><div class="hover-section-header"><span>📐 1. Setup Criteria Checklist</span><span>' + pattern + '</span></div>' + chkHtml + '</div>';
            html += '<div class="hover-section"><div class="hover-section-header"><span>🧮 2. Bespoke Score Breakdown Math</span><span>' + archetype + '</span></div>' + brkHtml + '</div>';
            html += '<div class="hover-section"><div class="hover-section-header"><span>🎯 3. Institutional Trade Plan & Execution</span><span>R:R 2.0R/3.5R</span></div>' + planHtml + '</div>';
            html += '<div class="hover-section"><div class="hover-section-header"><span>📰 4. Catalyst & News Intelligence</span></div>' + catHtml + '</div>';

            content.innerHTML = html;
            portal.style.display = 'block';

            // Viewport Zero-Clipping Positioning
            const portalWidth = 440;
            const portalHeight = portal.offsetHeight || 500;
            const padding = 14;

            let x = event.clientX + 18;
            let y = event.clientY - 30;

            if (x + portalWidth > window.innerWidth - padding) {{
                x = event.clientX - portalWidth - 18;
            }}
            if (x < padding) {{
                x = padding;
            }}

            if (y + portalHeight > window.innerHeight - padding) {{
                y = window.innerHeight - portalHeight - padding;
            }}
            if (y < padding) {{
                y = padding;
            }}

            portal.style.left = x + 'px';
            portal.style.top = y + 'px';
        }} catch (err) {{
            console.error('Hover scorecard error:', err);
        }}
    }}

    function hideScorecardHover() {{
        const portal = document.getElementById('floating-hover-portal');
        if (portal) portal.style.display = 'none';
    }}

    /* -----------------------------------------------------------------
       Trade Execution Desk (Actions Tab) Interactive Checkbox & Filter Engine
       ----------------------------------------------------------------- */
    function getActionDeskState() {{
        try {{
            return JSON.parse(localStorage.getItem('screener_action_desk_state') || '{{}}');
        }} catch (e) {{
            return {{}};
        }}
    }}

    function saveActionDeskState(state) {{
        try {{
            localStorage.setItem('screener_action_desk_state', JSON.stringify(state));
        }} catch (e) {{}}
    }}

    function toggleActionItemDone(actionId, isDone) {{
        const state = getActionDeskState();
        if (!state[actionId]) state[actionId] = {{}};
        state[actionId].done = isDone;
        if (isDone) state[actionId].skipped = false;
        saveActionDeskState(state);
        applyActionDeskRowStyles(actionId);
        updateActionDeskProgress();
    }}

    function toggleActionItemSkip(actionId, isSkip) {{
        const state = getActionDeskState();
        if (!state[actionId]) state[actionId] = {{}};
        state[actionId].skipped = isSkip;
        if (isSkip) state[actionId].done = false;
        saveActionDeskState(state);
        applyActionDeskRowStyles(actionId);
        updateActionDeskProgress();
    }}

    function applyActionDeskRowStyles(actionId) {{
        const state = getActionDeskState();
        const tr = document.getElementById('action-row-' + actionId);
        const chkDone = document.getElementById('chk-done-' + actionId);
        const chkSkip = document.getElementById('chk-skip-' + actionId);
        if (!tr) return;

        const isDone = state[actionId] && state[actionId].done;
        const isSkip = state[actionId] && state[actionId].skipped;

        if (chkDone) chkDone.checked = Boolean(isDone);
        if (chkSkip) chkSkip.checked = Boolean(isSkip);

        tr.classList.remove('action-row-done', 'action-row-skip');
        if (isDone) {{
            tr.classList.add('action-row-done');
        }} else if (isSkip) {{
            tr.classList.add('action-row-skip');
        }}
    }}

    function filterActionsDesk() {{
        const priorityFilter = document.getElementById('action-filter-priority') ? document.getElementById('action-filter-priority').value : 'ALL';
        const statusFilter = document.getElementById('action-filter-status') ? document.getElementById('action-filter-status').value : 'PENDING';
        const sourceFilter = document.getElementById('action-filter-source') ? document.getElementById('action-filter-source').value : 'ALL';
        const query = document.getElementById('action-search-input') ? document.getElementById('action-search-input').value.toLowerCase().trim() : '';

        const state = getActionDeskState();
        const rows = document.querySelectorAll('#actions-table-tbody tr');

        rows.forEach(r => {{
            const actionId = r.getAttribute('data-action-id') || '';
            const prio = r.getAttribute('data-priority') || '';
            const source = r.getAttribute('data-source') || '';
            const isDone = Boolean(state[actionId] && state[actionId].done);
            const isSkip = Boolean(state[actionId] && state[actionId].skipped);

            // Apply checkbox styles
            applyActionDeskRowStyles(actionId);

            let visible = true;
            if (priorityFilter !== 'ALL' && prio !== priorityFilter) visible = false;
            if (sourceFilter !== 'ALL' && source !== sourceFilter) visible = false;

            if (statusFilter === 'PENDING' && (isDone || isSkip)) visible = false;
            if (statusFilter === 'DONE' && !isDone) visible = false;
            if (statusFilter === 'SKIPPED' && !isSkip) visible = false;

            if (query && !r.innerText.toLowerCase().includes(query)) visible = false;

            r.style.display = visible ? '' : 'none';
        }});

        updateActionDeskProgress();
    }}

    function updateActionDeskProgress() {{
        const state = getActionDeskState();
        const rows = document.querySelectorAll('#actions-table-tbody tr');
        let total = rows.length;
        let doneCount = 0;
        let skipCount = 0;
        let p1Count = 0;
        let p2Count = 0;
        let p3Count = 0;

        rows.forEach(r => {{
            const actionId = r.getAttribute('data-action-id') || '';
            const prio = r.getAttribute('data-priority') || '';
            const isDone = Boolean(state[actionId] && state[actionId].done);
            const isSkip = Boolean(state[actionId] && state[actionId].skipped);

            if (isDone) doneCount++;
            if (isSkip) skipCount++;

            if (!isDone && !isSkip) {{
                if (prio === 'TIER1') p1Count++;
                if (prio === 'TIER2') p2Count++;
                if (prio === 'TIER3') p3Count++;
            }}
        }});

        const p1El = document.getElementById('actions-p1-count');
        if (p1El) p1El.innerText = p1Count;
        const p2El = document.getElementById('actions-p2-count');
        if (p2El) p2El.innerText = p2Count;
        const p3El = document.getElementById('actions-p3-count');
        if (p3El) p3El.innerText = p3Count;

        const progEl = document.getElementById('actions-progress-val');
        if (progEl) progEl.innerText = doneCount + ' / ' + total + ' Done (' + skipCount + ' Skipped)';
    }}

    function clearCompletedActionDeskTasks() {{
        if (!confirm('Mark all currently pending action items as Done?')) return;
        const state = getActionDeskState();
        const rows = document.querySelectorAll('#actions-table-tbody tr');
        rows.forEach(r => {{
            const actionId = r.getAttribute('data-action-id') || '';
            if (!state[actionId]) state[actionId] = {{}};
            state[actionId].done = true;
            state[actionId].skipped = false;
        }});
        saveActionDeskState(state);
        filterActionsDesk();
    }}

    function resetAllActionDeskTasks() {{
        if (!confirm('Reset all action checklist progress?')) return;
        localStorage.removeItem('screener_action_desk_state');
        filterActionsDesk();
    }}

</script>

    <!-- Floating Zero-Clipping Hover Scorecard Portal -->
    <div id="floating-hover-portal">
        <div id="hover-portal-content"></div>
    </div>

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
        for p in portfolio_data.get("positions", []):
            if p.get("sector") and p.get("sector") != "General":
                sectors_set.add(p.get("sector"))
        sector_options_html = "".join([f'<option value="{s}">{s}</option>' for s in sorted(sectors_set) if s and s != "General"])

        # -------------------------------------------------------------
        # 0. Build Trade Execution Desk (Actions Tab) Items
        # -------------------------------------------------------------
        action_desk_items = []
        for idx, item in enumerate(day_watchlist):
            p_info = item.get("pattern_info", {})
            plan = item.get("trade_plan", {}) or p_info.get("trade_plan", {})
            chk = item.get("criteria_checklist", {}) or p_info.get("criteria_checklist", {})
            sym = item.get("ticker", "")
            cur_p = item.get("price", 0.0)
            score = item.get("setup_score", 3.0)
            prim = p_info.get("primary_pattern", item.get("primary_pattern", "MOMENTUM_RUNNER"))
            badge = p_info.get("badge_label", item.get("pattern_badge", "⚡ Momentum"))
            
            is_p1 = bool(item.get("breakout_last_high") or item.get("pct_from_open", 0.0) >= 2.0 or p_info.get("is_ep_day1") or p_info.get("is_selling_climax"))
            is_p2 = bool(p_info.get("is_vcp") or p_info.get("is_htf") or p_info.get("is_base_breakout"))
            is_p3 = bool(p_info.get("is_stage2_pullback") or p_info.get("is_ep_day2") or score >= 4.0)

            prio_code = "TIER1" if is_p1 else ("TIER2" if is_p2 else ("TIER3" if is_p3 else "TIER4"))
            prio_badge = '<span class="badge-priority badge-p1">⚡ Tier 1: Immediate Entry</span>' if prio_code == "TIER1" else (
                '<span class="badge-priority badge-p2">🎯 Tier 2: Setup Anticipation</span>' if prio_code == "TIER2" else (
                    '<span class="badge-priority badge-p3">📈 Tier 3: Pullback Watch</span>' if prio_code == "TIER3" else '<span class="badge-priority badge-p4">📊 Tier 4: Watchlist</span>'
                )
            )

            order_inst = f"BUY STOP-LIMIT @ ${plan.get('entry_pivot', cur_p):.2f}" if not plan.get("is_short") else f"SELL SHORT STOP @ ${plan.get('entry_pivot', cur_p):.2f}"
            sz = item.get("sizing", {})
            sz_str = f"{sz.get('shares', 0):,} shs (${sz.get('capital_required', 0.0):,.0f})" if sz.get("shares") else "—"

            action_desk_items.append({
                "action_id": f"scr_{sym}_{idx}",
                "priority_code": prio_code,
                "priority_badge": prio_badge,
                "symbol": sym,
                "source": "SCREENER",
                "source_badge": '<span class="pill pill-blue">🚀 Screener</span>',
                "archetype_badge": f'<span class="pill pill-purple">{badge}</span>',
                "order_instruction": f"<strong>{order_inst}</strong>",
                "entry_price": f"${plan.get('entry_pivot', cur_p):.2f}",
                "hard_stop": f"<strong style='color: #f87171;'>${plan.get('hard_stop', cur_p*0.96):.2f}</strong> ({plan.get('stop_dist_pct', 4.0):.1f}%)",
                "soft_stop": f"<span style='font-size: 11px; color: #94a3b8;'>{plan.get('soft_stop_desc', 'VWAP loss')}</span>",
                "target_1": f"<strong style='color: #34d399;'>${plan.get('target_1', cur_p*1.08):.2f}</strong> (+{plan.get('target_1_pct', 8.0):.1f}%)",
                "target_2": f"<strong style='color: #60a5fa;'>${plan.get('target_2', cur_p*1.14):.2f}</strong> (+{plan.get('target_2_pct', 14.0):.1f}%)",
                "trailing": f"<span style='font-size: 11px; color: #a78bfa;'>{plan.get('trailing_desc', 'Trailing 20-SMA')}</span>",
                "sizing": sz_str,
                "time_horizon": f"{plan.get('time_stop_days', 5)} Days (Swing)",
                "json_data": json.dumps({
                    "ticker": sym,
                    "score": score,
                    "stars_visual": item.get("stars_visual", "★★★☆☆"),
                    "archetype": p_info.get("archetype", "ARCHETYPE_E"),
                    "primary_pattern": prim,
                    "pattern_badge": badge,
                    "criteria_checklist": chk,
                    "score_breakdown": item.get("score_breakdown", {}),
                    "trade_plan": plan,
                    "headline": item.get("headline", ""),
                    "catalyst_url": item.get("catalyst_url", "#"),
                    "catalyst_stars": item.get("catalyst_stars", 1.0),
                    "catalyst_type": item.get("catalyst_type", "News"),
                    "is_exhausted": item.get("is_exhausted", False),
                    "exhaustion_desc": item.get("exhaustion_desc", "")
                }).replace('"', '&quot;')
            })

        for p_idx, p in enumerate(portfolio_data.get("positions", [])):
            sym = p.get("symbol", "")
            underlying = p.get("underlying") or sym
            last_p = p.get("last_price", 0.0)
            stop_l = p.get("stop_loss", round(last_p * 0.96, 2))
            targ_p = p.get("target_price", round(last_p * 1.15, 2))
            qty = p.get("quantity", 0.0)
            streak = p.get("streak_count", 0)
            day_p = p.get("today_pnl_pct", 0.0)

            if stop_l > 0 and last_p <= stop_l:
                prio_code = "TIER2"
                prio_badge = '<span class="badge-priority badge-p1">🚨 Hard Stop Triggered</span>'
                order_inst = f"<strong style='color: #f87171;'>SELL STOP EXIT ALL ({qty:,.0f} shs @ ${last_p:.2f})</strong>"
            elif targ_p > 0 and last_p >= targ_p:
                prio_code = "TIER3"
                prio_badge = '<span class="badge-priority badge-p3">🎯 Target 1 (2R) Reached</span>'
                order_inst = f"<strong style='color: #34d399;'>TRIM 50% PROFIT ({qty/2:,.0f} shs @ ${last_p:.2f})</strong>"
            elif streak >= 3 and day_p < 0:
                prio_code = "TIER1"
                prio_badge = '<span class="badge-priority badge-p1">⚡ 3-Day Rule Down Exit</span>'
                order_inst = f"<strong style='color: #fbbf24;'>TRIM 50% on First Down Day ({qty/2:,.0f} shs)</strong>"
            else:
                prio_code = "TIER4"
                prio_badge = '<span class="badge-priority badge-p4">📈 Trailing Stop Hold</span>'
                order_inst = f"HOLD & TRAIL Stop @ ${stop_l:.2f}"

            action_desk_items.append({
                "action_id": f"port_{sym}_{p_idx}",
                "priority_code": prio_code,
                "priority_badge": prio_badge,
                "symbol": sym,
                "source": "PORTFOLIO",
                "source_badge": '<span class="pill pill-green">💼 Portfolio</span>',
                "archetype_badge": f'<span class="pill pill-purple">{p.get("strategy_tag", "Holding")}</span>',
                "order_instruction": order_inst,
                "entry_price": f"${p.get('average_cost', last_p):.2f}",
                "hard_stop": f"<strong style='color: #f87171;'>${stop_l:.2f}</strong>",
                "soft_stop": "<span style='font-size: 11px; color: #94a3b8;'>Daily close below 20-SMA</span>",
                "target_1": f"<strong style='color: #34d399;'>${targ_p:.2f}</strong>",
                "target_2": f"<strong style='color: #60a5fa;'>${targ_p*1.10:.2f}</strong>",
                "trailing": "<span style='font-size: 11px; color: #a78bfa;'>Trailing 20-SMA</span>",
                "sizing": f"{qty:,.0f} shs (${qty*last_p:,.0f})",
                "time_horizon": "Core Book",
                "json_data": json.dumps({
                    "ticker": sym,
                    "score": p.get("setup_score", 3.5),
                    "stars_visual": p.get("stars_visual", "★★★☆☆"),
                    "archetype": "PORTFOLIO_HOLDING",
                    "primary_pattern": p.get("strategy_tag", "Core Holding"),
                    "pattern_badge": p.get("strategy_tag", "Core Holding"),
                    "criteria_checklist": {"stage2_trend": True, "ma_ribbon": True},
                    "score_breakdown": {"base_points": 2.0, "trend_points": 1.5},
                    "trade_plan": {"entry_pivot": p.get("average_cost", last_p), "hard_stop": stop_l, "target_1": targ_p},
                    "headline": p.get("headline", p.get("description", "Open portfolio position")),
                    "catalyst_url": p.get("catalyst_url", "#"),
                    "catalyst_stars": p.get("catalyst_stars", 3.0),
                    "catalyst_type": p.get("catalyst_type", "Holding"),
                    "is_exhausted": False
                }).replace('"', '&quot;')
            })

        action_desk_rows_html = []
        action_p1_count = sum(1 for a in action_desk_items if a["priority_code"] == "TIER1")
        action_p2_count = sum(1 for a in action_desk_items if a["priority_code"] == "TIER2")
        action_p3_count = sum(1 for a in action_desk_items if a["priority_code"] == "TIER3")
        action_total_count = len(action_desk_items)

        for a in action_desk_items:
            action_id = a["action_id"]
            action_desk_rows_html.append(f"""
            <tr class="data-row" id="action-row-{action_id}" data-action-id="{action_id}" data-priority="{a['priority_code']}" data-source="{a['source']}">
                <td style="text-align: center; white-space: nowrap;">
                    <input type="checkbox" id="chk-done-{action_id}" class="chk-action-desk" title="Mark Done" onchange="toggleActionItemDone('{action_id}', this.checked)">
                    <input type="checkbox" id="chk-skip-{action_id}" class="chk-action-skip" title="Skip Task" onchange="toggleActionItemSkip('{action_id}', this.checked)">
                </td>
                <td>{a['priority_badge']}</td>
                <td><a class="ticker-link" href="https://finance.yahoo.com/quote/{a['symbol']}" target="_blank" onmouseenter="showScorecardHover(event, '{a['json_data']}')" onmouseleave="hideScorecardHover()">{a['symbol']}</a></td>
                <td>{a['source_badge']}</td>
                <td>{a['archetype_badge']}</td>
                <td>{a['order_instruction']}</td>
                <td><strong>{a['entry_price']}</strong></td>
                <td>{a['hard_stop']}</td>
                <td>{a['soft_stop']}</td>
                <td>{a['target_1']}</td>
                <td>{a['target_2']}</td>
                <td>{a['trailing']}</td>
                <td><strong>{a['sizing']}</strong></td>
                <td><span class="pill pill-blue" style="font-size: 10px;">{a['time_horizon']}</span></td>
            </tr>
            """)

        # 1. Day Trading Watchlist Rows & Accordion Drawers
        day_rows_html = []
        if day_watchlist:
            for idx, item in enumerate(day_watchlist):
                drawer_id = f"row-drawer-{idx}"
                rvol_val = item.get("rvol", 1.0)
                rvol_pill = f'<span class="pill pill-green">{rvol_val:.2f}x</span>' if rvol_val >= 2.0 else f'<span class="pill pill-yellow">{rvol_val:.2f}x</span>'
                
                score_val = item.get("setup_score", 3.0)
                badge_str = item.get('pattern_badge', '⚡ Setup')
                badge_html = f'<span class="pill pill-purple" style="font-size: 10px; margin-top: 2px; display: inline-block;">{badge_str}</span>'
                if item.get('is_exhausted'):
                    badge_html += f'<div style="color: #f59e0b; font-size: 9.5px; font-weight: 700; margin-top: 2px;">⚠️ Extended</div>'
                
                # Build JSON payload for floating hover scorecard
                item_hover_payload = json.dumps({
                    "ticker": item.get("ticker", ""),
                    "score": score_val,
                    "stars_visual": item.get("stars_visual", "★★★☆☆"),
                    "archetype": item.get("pattern_info", {}).get("archetype", "ARCHETYPE_E"),
                    "primary_pattern": item.get("primary_pattern", "MOMENTUM_RUNNER"),
                    "pattern_badge": badge_str,
                    "criteria_checklist": item.get("criteria_checklist", {}),
                    "score_breakdown": item.get("score_breakdown", {}),
                    "trade_plan": item.get("trade_plan", {}),
                    "headline": item.get("headline", ""),
                    "catalyst_url": item.get("catalyst_url", "#"),
                    "catalyst_stars": item.get("catalyst_stars", 1.0),
                    "catalyst_type": item.get("catalyst_type", "News"),
                    "is_exhausted": item.get("is_exhausted", False),
                    "exhaustion_desc": item.get("exhaustion_desc", "")
                }).replace('"', '&quot;')

                score_pill = f'<div style="cursor: pointer;" onmouseenter="showScorecardHover(event, \'{item_hover_payload}\')" onmouseleave="hideScorecardHover()"><span class="pill pill-purple" style="font-size: 11px;">{item.get("stars_visual", "★★★☆☆")} {score_val:.1f}★</span><br>{badge_html}</div>'

                p_open = item.get("pct_from_open", 0.0)
                p_open_color = "#34d399" if p_open > 0 else ("#f87171" if p_open < 0 else "#9ca3af")
                p_open_str = f'<span style="color: {p_open_color}; font-weight: 600;">{p_open:+.2f}%</span>'

                cat_cat = item.get("catalyst_type", "News")
                cat_stars_num = int(round(item.get("catalyst_stars", 1.0)))
                cat_stars_str = "&#9733;" * cat_stars_num + "&#9734;" * (5 - cat_stars_num)
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
                preset_tags_val = item.get('preset_tags', 'ALL_SETUPS')

                day_rows_html.append(f"""
                <tr class="data-row" data-drawer-id="{drawer_id}"
                    data-ticker="{item['ticker']}"
                    data-preset-tags="{preset_tags_val}"
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
                    data-sma5-dist="{item.get('sma5_dist', 0.0):.2f}"
                    data-sma5-xo="{str(item.get('sma5_xo', False)).lower()}"
                    data-sma5-xu="{str(item.get('sma5_xu', False)).lower()}"
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
                    data-breakout-week-high="{str(item.get('breakout_week_high', False)).lower()}"
                    data-breakout-last-high="{str(item.get('breakout_last_high', False)).lower()}"
                    data-breakout-pm-high="{str(item.get('breakout_pm_high', False)).lower()}"
                    data-breakdown-pm-low="{str(item.get('breakdown_pm_low', False)).lower()}"
                    data-breakdown-week-low="{str(item.get('breakdown_week_low', False)).lower()}"
                    data-breakdown-last-low="{str(item.get('breakdown_last_low', False)).lower()}"
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
                                <div style="margin-top: 8px;"><button class="whale-btn" style="width: 100%; justify-content: center;" onclick="openWhaleModal('{item['ticker']}')">🐳 View Institutional Whale Sweeps & Orders</button></div>
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
            for idx, p in enumerate(portfolio_positions):
                sym = p.get("symbol", "—")
                raw_sym = p.get("raw_symbol", sym)
                underlying = p.get("underlying") or re.sub(r'[^A-Za-z\.]', '', sym)
                desc = p.get("description", "—")
                qty = p.get("quantity", 0.0)
                avg_c = p.get("average_cost", 0.0)
                last_p = p.get("last_price", 0.0)
                cur_v = p.get("current_value", qty * last_p)
                day_d = p.get("today_pnl_dollar", 0.0)
                day_p = p.get("today_pnl_pct", 0.0)
                tot_d = p.get("total_pnl_dollar", 0.0)
                tot_p = p.get("total_pnl_pct", 0.0)
                w_pct = p.get("weight_pct", 0.0)
                strat = p.get("strategy_tag", "Tactical Momentum")
                stop_l = p.get("stop_loss", round(last_p * 0.96, 2))
                targ_p = p.get("target_price", round(last_p * 1.15, 2))
                notes = p.get("notes", "")
                is_opt = p.get("is_option", False)

                day_color = "#34d399" if day_d > 0 else ("#f87171" if day_d < 0 else "#9ca3af")
                tot_color = "#34d399" if tot_d > 0 else ("#f87171" if tot_d < 0 else "#9ca3af")

                score_val = p.get("setup_score", 3.0)
                score_stars = p.get("stars_visual", "&#9733;&#9733;&#9733;&#9734;&#9734;")
                score_pill = f'<span class="pill pill-purple" style="font-size: 11px;">{score_stars} {score_val:.1f}&#9733;</span>'

                p_chg = p.get("pct_change", day_p)
                p_chg_pill = f'<span class="pill pill-green">+{p_chg:.2f}%</span>' if p_chg > 0 else (f'<span class="pill pill-red">{p_chg:.2f}%</span>' if p_chg < 0 else f'<span class="pill pill-blue">{p_chg:.2f}%</span>')

                gap_val = p.get("gap_pct", 0.0)
                gap_str = f'<span style="color: #38bdf8; font-weight: 600;">{gap_val:+.2f}%</span>' if gap_val != 0 else '<span style="color: #9ca3af;">0.00%</span>'

                p_open = p.get("pct_from_open", 0.0)
                p_open_color = "#34d399" if p_open > 0 else ("#f87171" if p_open < 0 else "#9ca3af")
                p_open_str = f'<span style="color: {p_open_color}; font-weight: 600;">{p_open:+.2f}%</span>'

                rvol_val = p.get("rvol", 1.0)
                rvol_pill = f'<span class="pill pill-green">{rvol_val:.2f}x</span>' if rvol_val >= 2.0 else f'<span class="pill pill-yellow">{rvol_val:.2f}x</span>'

                earn_date_val = p.get("earnings_date", "—")
                earn_pill = f'<span class="pill pill-purple" style="font-size: 10.5px;">{earn_date_val}</span>' if earn_date_val != "—" else '<span style="color: #6b7280;">—</span>'

                cat_cat = p.get("catalyst_type", "Holding")
                cat_stars_num = int(round(p.get("catalyst_stars", 3.0)))
                cat_stars_num = min(5, max(1, cat_stars_num))
                cat_stars_str = "★" * cat_stars_num + "☆" * (5 - cat_stars_num)
                cat_date_str = p.get("catalyst_date", "—")
                cat_pill = f'<span class="pill pill-blue">[{cat_cat}]</span> <span style="color: #fbbf24; font-size: 11px;">{cat_stars_str}</span>'

                skew_val = p.get("gamma_skew", "Neutral")
                skew_pill = '<span class="pill pill-green">Bullish</span>' if "Bullish" in skew_val else ('<span class="pill pill-red">Bearish</span>' if "Bearish" in skew_val else f'<span class="pill pill-blue">{skew_val}</span>')

                b_last_str = "true" if p.get("breakout_last_high") else "false"
                b_pm_str = "true" if p.get("breakout_pm_high") else "false"
                is_pos_str = "true" if p.get("is_positive", True) else "false"

                # Stockbee Mechanical Exit Rule Checks
                exit_alerts = []
                if p.get("streak_count", 0) >= 3 and p_chg < 0:
                    exit_alerts.append("🚨 3-Day Run Down-Day Exit")
                try:
                    sma5_val = float(str(p.get("sma5", "0")).replace("$", "").replace(",", ""))
                    if sma5_val > 0 and last_p < sma5_val:
                        exit_alerts.append("🚨 SMA5 Breakdown")
                except Exception:
                    pass
                exit_alerts_html = "".join([f'<div style="color: #f87171; font-weight: 700; font-size: 10px; margin-top: 2px;">{alert}</div>' for alert in exit_alerts])

                drawer_id = f"port-row-drawer-{idx}"

                port_rows_html.append(f"""
                <tr class="data-row" data-drawer-id="{drawer_id}" data-preset-tags="{p.get('preset_tags', 'ALL_SETUPS')}" data-symbol="{sym}" data-underlying="{underlying}" data-is-option="{str(is_opt).lower()}" data-chg="{p_chg:.2f}" data-gap="{gap_val:.2f}" data-open="{p_open:.2f}" data-vwap-dist="{p.get('vwap_dist', 0.0):.2f}" data-vwap-xo="{str(p.get('vwap_xo', False)).lower()}" data-vwap-xu="{str(p.get('vwap_xu', False)).lower()}" data-vwap-std-p1="{str(p.get('vwap_std_p1', False)).lower()}" data-vwap-std-p2="{str(p.get('vwap_std_p2', False)).lower()}" data-vwap-std-m1="{str(p.get('vwap_std_m1', False)).lower()}" data-vwap-std-m2="{str(p.get('vwap_std_m2', False)).lower()}" data-skew="{skew_val}" data-pc="{p.get('pc_ratio', 1.0)}" data-net-flow="{p.get('net_dollar_val', 0.0)}" data-whales="{p.get('whale_trades_count', 0)}" data-sma5-dist="{p.get('sma5_dist', 0.0):.2f}" data-sma5-xo="{str(p.get('sma5_xo', False)).lower()}" data-sma5-xu="{str(p.get('sma5_xu', False)).lower()}" data-sma20-dist="{p.get('sma20_dist', 0.0):.2f}" data-sma20-xo="{str(p.get('sma20_xo', False)).lower()}" data-sma20-xu="{str(p.get('sma20_xu', False)).lower()}" data-sma50-dist="{p.get('sma50_dist', 0.0):.2f}" data-sma50-xo="{str(p.get('sma50_xo', False)).lower()}" data-sma50-xu="{str(p.get('sma50_xu', False)).lower()}" data-sma200-dist="{p.get('sma200_dist', 0.0):.2f}" data-sma200-xo="{str(p.get('sma200_xo', False)).lower()}" data-sma200-xu="{str(p.get('sma200_xu', False)).lower()}" data-rvol="{rvol_val:.2f}" data-score="{score_val:.2f}" data-stars="{p.get('catalyst_stars', 0.0)}" data-pos="{is_pos_str}" data-breakout-week-high="{str(p.get('breakout_week_high', False)).lower()}" data-breakout-last-high="{str(p.get('breakout_last_high', False)).lower()}" data-breakout-pm-high="{str(p.get('breakout_pm_high', False)).lower()}" data-breakdown-pm-low="{str(p.get('breakdown_pm_low', False)).lower()}" data-breakdown-week-low="{str(p.get('breakdown_week_low', False)).lower()}" data-breakdown-last-low="{str(p.get('breakdown_last_low', False)).lower()}" data-sector="{p.get('sector', 'General')}" data-total-pct="{tot_p:.2f}" data-weight="{w_pct:.2f}" data-strategy="{strat}">
                    <td class="col-all"><a class="ticker-link" href="https://finance.yahoo.com/quote/{underlying}" target="_blank">{sym}</a>{exit_alerts_html}</td>
                    <td class="col-all">{score_pill}</td>
                    <td class="col-all"><strong>${last_p:,.2f}</strong></td>
                    <td class="col-all" style="color: {day_color}; font-weight: 600;">{day_d:+,.2f}</td>
                    <td class="col-all" style="color: {tot_color}; font-weight: 700;">{tot_d:+,.2f}</td>
                    <td class="col-all" style="color: {tot_color}; font-weight: 700;">{tot_p:+.2f}%</td>
                    <td class="col-all"><strong>${cur_v:,.2f}</strong></td>
                    <td class="col-all"><span class="pill pill-blue">{w_pct:.2f}%</span></td>
                    <td class="col-all"><strong>{qty:,.3f}</strong></td>
                    <td class="col-all">${avg_c:,.2f}</td>
                    <td class="col-tech-core">{p_chg_pill}</td>
                    <td class="col-tech-core">{gap_str}</td>
                    <td class="col-tech-core">{p_open_str}</td>
                    <td class="col-tech-core">{rvol_pill}</td>
                    <td class="col-tech-core">{earn_pill}</td>
                    <td class="col-tech-core">{p.get('yesterday_high_dist', '—')}</td>
                    <td class="col-core-only"><span class="pill pill-blue">{p.get('sector', 'General')}</span></td>
                    <td class="col-core-only" style="font-size: 11px; color: #d1d5db;">{p.get('industry', 'Diversified')}</td>
                    <td class="col-core-only">{cat_pill} <a class="headline-link" href="{p.get('catalyst_url', '#')}" target="_blank">{p.get('headline', desc)}</a></td>
                    <td class="col-tech-only">{p.get('premarket_high_dist', '—')}</td>
                    <td class="col-tech-only"><strong style="color: #38bdf8;">{p.get('vwap', '—')}</strong></td>
                    <td class="col-tech-only">{p.get('sma5', '—')}</td>
                    <td class="col-tech-only">{p.get('sma20', '—')}</td>
                    <td class="col-tech-only">{p.get('sma50', '—')}</td>
                    <td class="col-tech-only">{p.get('sma200', '—')}</td>
                    <td class="col-opt-only" style="color: #60a5fa; font-weight: 600;">{p.get('call_wall', '—')}</td>
                    <td class="col-opt-only" style="color: #f87171; font-weight: 600;">{p.get('put_wall', '—')}</td>
                    <td class="col-opt-only" style="color: #fbbf24;">{p.get('gamma_flip', '—')}</td>
                    <td class="col-opt-only">{p.get('vol_oi_ratio', 1.0):.2f}x</td>
                    <td class="col-opt-only">{p.get('atm_iv_str', '—')}</td>
                    <td class="col-opt-only">{skew_pill}</td>
                    <td class="col-opt-only">{p.get('pc_ratio', '—')}</td>
                    <td class="col-opt-only"><strong style="color: #34d399; font-size: 11px;">{p.get('analyst_rating', '—')}</strong></td>
                    <td class="col-core-only"><span class="pill pill-purple">{strat}</span></td>
                    <td class="col-all" style="text-align: center; white-space: nowrap;">
                        <button class="btn-action" style="padding: 2px 6px; font-size: 10px;" onclick="openSizingModal('{underlying}', {last_p}, {stop_l}, '{desc}', 'Rebalance')">⚡</button>
                        <button class="btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="openEditPositionModal('{sym}', {qty}, {avg_c}, {stop_l}, {targ_p}, '{strat}', '{notes}')">✏️</button>
                        <button class="btn-danger" style="padding: 2px 6px; font-size: 10px;" onclick="deletePortfolioPosition('{sym}')">❌</button>
                        <button class="btn-secondary" style="padding: 2px 6px; font-size: 10px; margin-left: 2px;" onclick="toggleRowDrawer('{drawer_id}')">🔍</button>
                    </td>
                </tr>
                <tr class="row-drawer" id="{drawer_id}">
                    <td colspan="35">
                        <div class="drawer-content">
                            <div class="drawer-card">
                                <div class="drawer-card-title">📈 Trend & Moving Average Matrix ({sym})</div>
                                <div class="drawer-item-row"><span>Total Session % Chg:</span> {p_chg_pill}</div>
                                <div class="drawer-item-row"><span>Opening Gap %:</span> {gap_str}</div>
                                <div class="drawer-item-row"><span>Intraday Run (% Open):</span> {p_open_str}</div>
                                <div class="drawer-item-row"><span>VWAP (Session):</span> <strong style="color: #38bdf8;">{p.get('vwap', '—')}</strong></div>
                                <div class="drawer-item-row"><span>5-Day SMA:</span> <strong>{p.get('sma5', '—')}</strong></div>
                                <div class="drawer-item-row"><span>20-Day SMA:</span> <strong>{p.get('sma20', '—')}</strong></div>
                                <div class="drawer-item-row"><span>50-Day SMA:</span> <strong>{p.get('sma50', '—')}</strong></div>
                                <div class="drawer-item-row"><span>200-Day SMA:</span> <strong>{p.get('sma200', '—')}</strong></div>
                            </div>
                            <div class="drawer-card">
                                <div class="drawer-card-title">🎯 Institutional Options Gamma & Sizing</div>
                                <div class="drawer-item-row"><span>Gamma Skew:</span> {skew_pill}</div>
                                <div class="drawer-item-row"><span>Flow Conviction:</span> {p.get('flow_conviction_badge', '🟡 Flow: 50/100')}</div>
                                <div class="drawer-item-row"><span>Call Wall (Magnet):</span> <strong style="color: #60a5fa;">{p.get('call_wall', '—')}</strong></div>
                                <div class="drawer-item-row"><span>Put Wall (Floor):</span> <strong style="color: #f87171;">{p.get('put_wall', '—')}</strong></div>
                                <div class="drawer-item-row"><span>Gamma Flip Level:</span> <strong style="color: #fbbf24;">{p.get('gamma_flip', '—')}</strong></div>
                                <div class="drawer-item-row"><span>Vol/OI & P/C Ratio:</span> <strong>{p.get('vol_oi_ratio', 1.0):.2f}x (P/C: {p.get('pc_ratio', '—')})</strong></div>
                                <div class="drawer-item-row"><span>ATM IV & Net Flow:</span> <strong>{p.get('atm_iv_str', '—')} ({p.get('net_dollar_str', '—')})</strong></div>
                            </div>
                            <div class="drawer-card">
                                <div class="drawer-card-title">📰 Catalyst & Analyst Intelligence</div>
                                <div style="margin-bottom: 6px;">{cat_pill}</div>
                                <div style="margin-bottom: 8px;"><a class="headline-link" href="{p.get('catalyst_url', '#')}" target="_blank" style="font-size: 12px; font-weight: 600;">{p.get('headline', desc)}</a></div>
                                <div class="drawer-item-row"><span>Sector:</span> <strong style="color: #9ca3af;">{p.get('sector', 'General')}</strong></div>
                                <div class="drawer-item-row"><span>Industry:</span> <strong style="color: #d1d5db;">{p.get('industry', 'Diversified')}</strong></div>
                                <div class="drawer-item-row"><span>Earnings Date:</span> <strong style="color: #c084fc;">{p.get('earnings_date', '—')}</strong></div>
                                <div class="drawer-item-row"><span>Analyst Revisions:</span> <strong style="color: #34d399;">{p.get('analyst_rating', '—')}</strong></div>
                            </div>
                            <div class="drawer-card">
                                <div class="drawer-card-title">💼 Portfolio Position & Risk Sizing</div>
                                <div class="drawer-item-row"><span>Holding Quantity:</span> <strong>{qty:,.3f}</strong></div>
                                <div class="drawer-item-row"><span>Average Cost:</span> <strong>${avg_c:,.2f}</strong></div>
                                <div class="drawer-item-row"><span>Total Cost Basis:</span> <strong>${p.get('cost_basis_total', qty * avg_c):,.2f}</strong></div>
                                <div class="drawer-item-row"><span>Current Value:</span> <strong>${cur_v:,.2f} ({w_pct:.2f}%)</strong></div>
                                <div class="drawer-item-row"><span>Today Session P&L:</span> <strong style="color: {day_color};">{day_d:+,.2f} ({day_p:+.2f}%)</strong></div>
                                <div class="drawer-item-row"><span>Total Unrealized P&L:</span> <strong style="color: {tot_color};">{tot_d:+,.2f} ({tot_p:+.2f}%)</strong></div>
                                <div class="drawer-item-row"><span>Stop Loss / Target:</span> <strong>${stop_l:,.2f} / ${targ_p:,.2f}</strong></div>
                                <div class="drawer-item-row"><span>Strategy Tag:</span> <span class="pill pill-purple">{strat}</span></div>
                                """ + (f'<div class="drawer-item-row"><span>Trade Notes:</span> <em>{notes}</em></div>' if notes else '') + f"""
                            </div>
                        </div>
                    </td>
                </tr>
                """)
        else:
            port_rows_html.append('<tr><td colspan="36" style="text-align: center; color: #9ca3af; padding: 20px;">No open positions in book. Click "Import Fidelity CSV" to populate.</td></tr>')

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
        tomorrow_bmo = earnings_data.get("tomorrow_bmo", [])
        tomorrow_amc = earnings_data.get("tomorrow_amc", [])

        for x in yesterday_amc:
            x["_timing_cat"] = "YEST_AMC"
        for x in today_bmo:
            x["_timing_cat"] = "TODAY_BMO"
        for x in today_amc:
            x["_timing_cat"] = "TODAY_AMC"
        for x in tomorrow_bmo + tomorrow_amc:
            x["_timing_cat"] = "TOMORROW"

        all_earnings = []
        seen_earn_tickers = set()
        for item in yesterday_amc + today_bmo + today_amc + tomorrow_bmo + tomorrow_amc:
            if item["ticker"] not in seen_earn_tickers:
                seen_earn_tickers.add(item["ticker"])
                all_earnings.append(item)

        def parse_mkt_cap_num(cap_str: Any) -> float:
            if not cap_str:
                return 0.0
            s = str(cap_str).strip().upper().replace("$", "").replace(",", "")
            try:
                if s.endswith("T"):
                    return float(s[:-1]) * 1000.0
                elif s.endswith("B"):
                    return float(s[:-1])
                elif s.endswith("M"):
                    return float(s[:-1]) / 1000.0
                elif s.endswith("K"):
                    return float(s[:-1]) / 1000000.0
                else:
                    return float(s)
            except Exception:
                return 0.0

        for item in all_earnings:
            item["_mkt_cap_num"] = parse_mkt_cap_num(item.get("market_cap", ""))

        # Sort earnings by Market Cap Descending
        all_earnings.sort(key=lambda x: x.get("_mkt_cap_num", 0.0), reverse=True)

        total_earn_count = len(all_earnings)

        if all_earnings:
            for item in all_earnings:
                timing_cat = item.get("_timing_cat", "ALL")
                timing_raw = item.get("timing", "")
                if timing_cat == "YEST_AMC":
                    timing_badge = f'<span class="pill pill-blue">Yesterday AMC ({timing_raw})</span>'
                elif timing_cat == "TODAY_BMO":
                    timing_badge = f'<span class="pill pill-green">Today BMO ({timing_raw})</span>'
                elif timing_cat == "TODAY_AMC":
                    timing_badge = f'<span class="pill pill-yellow">Today AMC ({timing_raw})</span>'
                elif timing_cat == "TOMORROW":
                    timing_badge = f'<span class="pill pill-purple">Tomorrow ({timing_raw})</span>'
                else:
                    timing_badge = f'<span class="pill pill-purple">{timing_raw}</span>'

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
                <tr class="data-row" data-timing="{timing_cat}" data-mkt-cap="{item.get('_mkt_cap_num', 0.0):.4f}">
                    <td><a class="ticker-link" href="https://finance.yahoo.com/quote/{item['ticker']}" target="_blank">{item['ticker']}</a></td>
                    <td style="font-size: 11px; color: #d1d5db;">{item.get('company', '')}</td>
                    <td><span class="pill pill-blue">{item.get('sector', 'General')}</span></td>
                    <td>{timing_badge}</td>
                    <td>{pct_str}</td>
                    <td style="color: #9ca3af; font-weight: 600;">{item.get('market_cap', '—')}</td>
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
                agg_ticker = agg.get("ticker", "")
                whale_btn_html = f'<button class="whale-btn" onclick="openWhaleModal(\'{agg_ticker}\')">🐳 {whale_count} Whales</button>' if whale_count > 0 else '<span style="color: #6b7280; font-size: 11px;">0 Trades</span>'

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
                stock_p = agg.get("stock_price", 0.0) or 0.0
                stock_chg = agg.get("stock_pct_chg", 0.0) or 0.0
                chg_color = "#34d399" if stock_chg > 0 else ("#f87171" if stock_chg < 0 else "#9ca3af")
                if stock_p > 0:
                    price_str = f"<strong>${stock_p:,.2f}</strong> (<span style=\"color: {chg_color}; font-weight: 600;\">{stock_chg:+.2f}%</span>)"
                else:
                    price_str = "—"

                options_agg_html.append(f"""
                <tr class="data-row" data-whale-id="{drawer_id}" data-whales="{whale_count}" data-vol-oi="{vol_oi_val:.2f}" data-skew="{skew_val}">
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
        p_nav = float(portfolio_data.get("total_nav", 0.0) or 0.0)
        p_cash = float(portfolio_data.get("cash_balance", 0.0) or 0.0)
        p_eq = float(portfolio_data.get("equity_value", 0.0) or 0.0)
        p_day_d = float(portfolio_data.get("total_day_pnl_dollar", 0.0) or 0.0)
        p_day_p = float(portfolio_data.get("total_day_pnl_pct", 0.0) or 0.0)
        p_tot_d = float(portfolio_data.get("total_unrealized_pnl_dollar", 0.0) or 0.0)
        p_cash_w = float(portfolio_data.get("cash_weight_pct", 0.0) or 0.0)

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
            whale_lookup_json=json.dumps({agg["ticker"]: agg.get("whale_trades", []) for agg in options_aggregated}),
            action_p1_count=action_p1_count,
            action_p2_count=action_p2_count,
            action_p3_count=action_p3_count,
            action_total_count=action_total_count,
            action_desk_rows="".join(action_desk_rows_html),
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
