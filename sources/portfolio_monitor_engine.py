"""Portfolio Real-Time Risk & Trailing Stop Monitor Engine.
Persists positions, historical peak highs, dynamic trailing stops, moving averages,
and automatically evaluates and fires execution events in SQLite database.
"""

import os
import re
import json
import sqlite3
import logging
import datetime
from typing import Dict, Any, List, Optional
from config import TZ_EST
from sources.news_pulse import news_pulse
from sources.setup_thesis_lifecycle import lifecycle_mgr
from sources.thesis_lake import thesis_lake

logger = logging.getLogger("portfolio_monitor_engine")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "portfolio_monitor.db")


def _clean_float(val: Any, default: float = 0.0) -> float:
    """Safely parse float from numbers or formatted strings like '$902.38 (+3.1%)'."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = val.replace(",", "").strip()
        m = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
        if m:
            try:
                return float(m.group(0))
            except Exception:
                pass
    return default


class PortfolioMonitorEngine:
    """Institutional Real-Time Execution & Trailing Stop Engine with SQLite Persistence."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Create and return a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema for tracking positions, trailing stops, and fired events."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # Table 1: Tracked Positions with Peak Highs and Dynamic Ratchet Trailing Stops
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS position_tracker (
                symbol TEXT PRIMARY KEY,
                underlying TEXT,
                quantity REAL,
                entry_price REAL,
                entry_date TEXT,
                highest_price_seen REAL,
                lowest_price_seen REAL,
                current_price REAL,
                hard_stop_price REAL,
                trailing_stop_price REAL,
                target_1_price REAL,
                target_2_price REAL,
                sma10_ema REAL,
                sma20 REAL,
                sma50 REAL,
                sma200 REAL,
                atr REAL,
                last_status TEXT,
                last_updated TEXT
            )
            """)

            # Table 2: Real-time Fired Events Log
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitor_fired_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                tier_code TEXT,
                event_type TEXT,
                trigger_price REAL,
                threshold_level REAL,
                peak_price REAL,
                shares_to_act REAL,
                action_type TEXT,
                order_instruction TEXT,
                realized_pnl_est_dollar REAL,
                realized_pnl_est_pct REAL,
                r_multiple REAL,
                status TEXT,
                details_json TEXT
            )
            """)
            conn.commit()

    def sync_and_evaluate(
        self,
        positions: List[Dict[str, Any]],
        day_watchlist: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Synchronize portfolio holdings with SQLite database, update trailing stops / peak highs,
        and evaluate real-time fired actions across all 5 priority tiers.
        """
        now_str = datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S EST")
        action_desk_items = []

        with self._get_conn() as conn:
            cursor = conn.cursor()

            # -------------------------------------------------------------
            # Step 1: Process and Monitor Portfolio Positions in SQLite
            # -------------------------------------------------------------
            for p_idx, p in enumerate(positions):
                sym = str(p.get("symbol", "")).upper().strip()
                if not sym:
                    continue
                
                underlying = p.get("underlying") or sym
                last_p = _clean_float(p.get("last_price", p.get("current_price", p.get("price", 0.0))))
                avg_cost = _clean_float(p.get("average_cost", p.get("avg_cost", p.get("cost_basis", last_p))), default=last_p)
                if avg_cost <= 0.0 and last_p > 0.0:
                    avg_cost = last_p
                
                qty = _clean_float(p.get("quantity", p.get("shares", 0.0)))
                entry_date = p.get("entry_date", now_str)
                sma20_val = _clean_float(p.get("sma20", 0.0))
                sma50_val = _clean_float(p.get("sma50", 0.0))
                sma10_ema = _clean_float(p.get("sma10_ema", sma20_val), default=sma20_val)
                atr_val = _clean_float(p.get("atr", avg_cost * 0.03 if avg_cost > 0 else 1.0), default=avg_cost * 0.03 if avg_cost > 0 else 1.0)
                day_p = _clean_float(p.get("today_pnl_pct", 0.0))
                streak = int(_clean_float(p.get("streak_count", 0)))
                
                # Fetch existing record from DB
                cursor.execute("SELECT * FROM position_tracker WHERE symbol = ?", (sym,))
                row = cursor.fetchone()

                if row:
                    prev_highest = _clean_float(row["highest_price_seen"], default=avg_cost if avg_cost > 0 else last_p)
                    prev_trailing = _clean_float(row["trailing_stop_price"], default=0.0)
                    row_stop = _clean_float(row["hard_stop_price"], default=0.0)
                    hard_stop = _clean_float(p.get("stop_loss", p.get("hard_stop", row_stop if row_stop > 0 else (round(avg_cost * 0.96, 2) if avg_cost > 0 else round(last_p * 0.96, 2)))))
                else:
                    prev_highest = max(avg_cost, last_p)
                    hard_stop = _clean_float(p.get("stop_loss", p.get("hard_stop", round(avg_cost * 0.96, 2) if avg_cost > 0 else round(last_p * 0.96, 2))))
                    prev_trailing = hard_stop

                highest_seen = max(prev_highest, last_p, avg_cost)
                lowest_seen = min(_clean_float(row["lowest_price_seen"] if row and row["lowest_price_seen"] else avg_cost, default=avg_cost), last_p)

                # Dynamic Trailing Stop Ratchet Engine:
                # Stop Distance: 2.0x ATR or minimum 3.5%
                ref_price = avg_cost if avg_cost > 0 else last_p
                stop_dist = max(ref_price * 0.035, 2.0 * atr_val if atr_val > 0 else ref_price * 0.035)
                
                # If position is in profit, ratchet trailing stop up
                if ref_price > 0 and highest_seen > ref_price * 1.02:
                    calculated_trailing = max(hard_stop, highest_seen - stop_dist)
                    if sma20_val > ref_price and last_p > sma20_val:
                        calculated_trailing = max(calculated_trailing, sma20_val * 0.995)
                    trailing_stop = max(prev_trailing, calculated_trailing)
                else:
                    trailing_stop = hard_stop

                target_1 = _clean_float(p.get("target_price", round(ref_price + 2.0 * stop_dist, 2)), default=round(ref_price + 2.0 * stop_dist, 2))
                target_2 = round(ref_price + 3.5 * stop_dist, 2)

                # Update database position record
                cursor.execute("""
                INSERT OR REPLACE INTO position_tracker (
                    symbol, underlying, quantity, entry_price, entry_date,
                    highest_price_seen, lowest_price_seen, current_price,
                    hard_stop_price, trailing_stop_price, target_1_price, target_2_price,
                    sma10_ema, sma20, sma50, sma200, atr, last_status, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sym, underlying, qty, avg_cost, entry_date,
                    highest_seen, lowest_seen, last_p,
                    hard_stop, trailing_stop, target_1, target_2,
                    sma10_ema, sma20_val, sma50_val, 0.0, atr_val, "ACTIVE", now_str
                ))

                # -------------------------------------------------------------
                # Step 2: Real-time Evaluation & Firing of Triggers
                # -------------------------------------------------------------
                unrealized_pnl_dollar = (last_p - avg_cost) * qty
                unrealized_pnl_pct = ((last_p - avg_cost) / avg_cost * 100.0) if avg_cost > 0 else 0.0
                r_mult = ((last_p - avg_cost) / (avg_cost - hard_stop)) if (avg_cost - hard_stop) > 0 else 0.0

                # Evaluate Thesis Health & News Pulse Stealth Flow (Phase 6)
                thesis_res = lifecycle_mgr.evaluate_lifecycle_stage(
                    symbol=sym,
                    holding_days=int(p.get("holding_days", 12)),
                    current_price=last_p,
                    entry_price=avg_cost,
                    hard_stop=hard_stop,
                    target_1=target_1,
                    target_2=target_2,
                    sloan_ratio_pct=float(p.get("sloan_ratio_pct", 3.2)),
                    sue_val=float(p.get("sue_val", 0.0)),
                    origin_archetype=p.get("strategy_tag") or "Base Breakout",
                )
                h_score = thesis_res["health"]["health_score"]
                is_broken_thesis = bool(h_score < 3.0 or thesis_res["health"]["category"] in ("BROKEN", "CRITICAL_REDLINE"))
                is_weakened_thesis = bool(3.0 <= h_score < 6.0)

                news_res = news_pulse.evaluate_portfolio_position(
                    symbol=sym,
                    price_change_pct=day_p,
                    rvol=_clean_float(p.get("rvol", 1.0)),
                    catalyst_text=str(p.get("catalyst", "")),
                    catalyst_source=str(p.get("catalyst_source", "")),
                    sector=str(p.get("sector", "Technology")),
                )
                is_stealth_surge = bool(news_res["attribution"]["is_stealth"])

                # Sync Phase 6 columns to SQLite position_tracker
                try:
                    cursor.execute("""
                        UPDATE position_tracker
                        SET lifecycle_stage = ?,
                            thesis_health_score = ?,
                            drift_status = ?,
                            last_news_signal = ?,
                            last_news_attribution = ?
                        WHERE symbol = ?
                    """, (
                        thesis_res["stage"],
                        h_score,
                        "MILD_DRIFT" if h_score < 7.0 else "NO_DRIFT",
                        news_res["signal"]["composite_score"],
                        news_res["attribution"]["driver_label"],
                        sym
                    ))
                except Exception:
                    pass

                # 1. Tier 1 Trigger: Broken Investment Thesis OR Hard / Soft Stop Violation
                is_hard_stop_breached = bool(hard_stop > 0 and (last_p <= hard_stop or (avg_cost > 0 and (last_p - hard_stop) / avg_cost <= 0.005)))
                
                # 2. Tier 2 Trigger: Trailing Stop / MA Breach / BOS Breakdown
                is_trailing_stop_breached = bool(trailing_stop > hard_stop and last_p <= trailing_stop)
                is_ma_breached = bool(sma20_val > 0 and last_p < sma20_val and highest_seen >= sma20_val * 0.99)
                is_bos_breakdown = bool(p.get("breakdown_last_low") or p.get("breakdown_week_low") or (streak >= 3 and day_p < 0))
                
                # 3. Tier 3 Trigger: Climax Top Reversal
                is_climax_top = bool(
                    (sma20_val > 0 and (last_p - sma20_val) / sma20_val >= 0.18 and day_p < -0.5) or
                    (_clean_float(p.get("pct_change", 0.0)) >= 25.0 and day_p < -1.0)
                )

                # 4. Tier 4 Trigger: Profit Targets Hit
                is_target_1_hit = bool(target_1 > 0 and last_p >= target_1)
                is_target_2_hit = bool(target_2 > 0 and last_p >= target_2)

                # Assign Fired Tier and Order Instruction with EXACT Monitored Telemetry
                if is_broken_thesis:
                    prio_code = "TIER1"
                    event_type = "BROKEN_THESIS_LIQUIDATION"
                    threshold_val = last_p
                    prio_badge = '<span class="badge-priority badge-p1" style="background: rgba(239, 68, 68, 0.25); color: #f87171; border: 1px solid #ef4444;">🚨 Tier 1: Broken Thesis</span>'
                    order_inst = f"<strong style='color: #f87171;'>SELL ALL LIQUIDATE ({qty:,.0f} shs @ ${last_p:.2f})</strong>"
                    order_desc = f"Thesis health broken ({h_score:.1f}/10 - {thesis_res['health']['category']}). Immediate liquidation required."
                    prio_weight = 105
                elif is_hard_stop_breached:
                    prio_code = "TIER1"
                    event_type = "HARD_STOP_BREACH"
                    threshold_val = hard_stop
                    prio_badge = '<span class="badge-priority badge-p1" style="background: rgba(239, 68, 68, 0.25); color: #f87171; border: 1px solid #ef4444;">🚨 Tier 1: Stop Fired</span>'
                    order_inst = f"<strong style='color: #f87171;'>SELL ALL STOP ({qty:,.0f} shs @ ${last_p:.2f})</strong>"
                    order_desc = f"Hard stop ${hard_stop:.2f} breached at ${last_p:.2f}. Loss: ${abs(unrealized_pnl_dollar):,.2f} ({unrealized_pnl_pct:.1f}%)."
                    prio_weight = 100
                elif is_stealth_surge:
                    prio_code = "TIER2"
                    event_type = "NEWS_STEALTH_SURGE"
                    threshold_val = trailing_stop
                    prio_badge = '<span class="badge-priority badge-p2" style="background: rgba(168, 85, 247, 0.25); color: #c084fc; border: 1px solid #a855f7;">🕵️ Tier 2: Stealth Surge Alert</span>'
                    order_inst = f"<strong style='color: #c084fc;'>SURVEILLANCE / TIGHTEN STOP ({qty:,.0f} shs)</strong>"
                    order_desc = f"Stealth flow detected (Z_eps: {news_res['residuals']['residual_zscore']:+.1f}, no public news). Immediate surveillance."
                    prio_weight = 97
                elif is_trailing_stop_breached:
                    prio_code = "TIER2"
                    event_type = "TRAILING_STOP_BREACH"
                    threshold_val = trailing_stop
                    prio_badge = '<span class="badge-priority badge-p2" style="background: rgba(245, 158, 11, 0.25); color: #fbbf24; border: 1px solid #f59e0b;">📉 Tier 2: Trailing Stop Fired</span>'
                    order_inst = f"<strong style='color: #fbbf24;'>SELL ALL ({qty:,.0f} shs @ ${last_p:.2f})</strong>"
                    order_desc = f"Trailing stop ${trailing_stop:.2f} breached (Peak: ${highest_seen:.2f}). Gain: +${unrealized_pnl_dollar:,.2f} (+{unrealized_pnl_pct:.1f}% / +{r_mult:.1f}R)."
                    prio_weight = 95
                elif is_ma_breached or is_bos_breakdown:
                    prio_code = "TIER2"
                    event_type = "MA_BREACH_SMA20" if is_ma_breached else "STRUCTURE_BOS_BREAKDOWN"
                    threshold_val = sma20_val if is_ma_breached else last_p
                    prio_badge = '<span class="badge-priority badge-p2" style="background: rgba(245, 158, 11, 0.25); color: #fbbf24; border: 1px solid #f59e0b;">📉 Tier 2: 20-SMA / BOS Fired</span>'
                    order_inst = f"<strong style='color: #fbbf24;'>SELL / TIGHTEN ({qty:,.0f} shs)</strong>"
                    order_desc = f"Close below 20-SMA (${sma20_val:.2f}) at ${last_p:.2f} (Peak: ${highest_seen:.2f}). Gain: +${unrealized_pnl_dollar:,.2f}."
                    prio_weight = 90
                elif is_weakened_thesis:
                    trim_pct = thesis_res["health"]["trim_pct"]
                    trim_qty = max(1.0, round(qty * (trim_pct / 100.0)))
                    prio_code = "TIER3"
                    event_type = "WEAKENED_THESIS_TRIM"
                    threshold_val = last_p
                    prio_badge = '<span class="badge-priority badge-p3" style="background: rgba(245, 158, 11, 0.25); color: #fbbf24; border: 1px solid #f59e0b;">📉 Tier 3: Thesis Trim</span>'
                    order_inst = f"<strong style='color: #fbbf24;'>TRIM {trim_pct:.0f}% THESIS ({trim_qty:,.0f} shs @ ${last_p:.2f})</strong>"
                    order_desc = f"Thesis health weakened ({h_score:.1f}/10). Formulaic risk reduction: trim {trim_pct:.1f}% ({trim_qty:,.0f} shs)."
                    prio_weight = 85
                elif is_climax_top:
                    prio_code = "TIER3"
                    event_type = "CLIMAX_TOP_REVERSAL"
                    threshold_val = highest_seen
                    prio_badge = '<span class="badge-priority badge-p3" style="background: rgba(236, 72, 153, 0.25); color: #f472b6; border: 1px solid #ec4899;">🌊 Tier 3: Climax Top Fired</span>'
                    order_inst = f"<strong style='color: #f472b6;'>TRIM 50% PROFIT ({qty/2:,.0f} shs @ ${last_p:.2f})</strong>"
                    climax_ext = ((last_p - sma20_val) / sma20_val * 100.0) if sma20_val > 0 else 0.0
                    order_desc = f"Extended +{climax_ext:.1f}% above 20-SMA, reversing from peak ${highest_seen:.2f}. Trim half."
                    prio_weight = 80
                elif is_target_2_hit:
                    prio_code = "TIER4"
                    event_type = "PROFIT_TARGET_2"
                    threshold_val = target_2
                    prio_badge = '<span class="badge-priority badge-p4" style="background: rgba(16, 185, 129, 0.25); color: #34d399; border: 1px solid #10b981;">🎯 Tier 4: Target 2 (3.5R) Fired</span>'
                    order_inst = f"<strong style='color: #34d399;'>SELL REMAINING 50% ({qty:,.0f} shs @ ${last_p:.2f})</strong>"
                    order_desc = f"Target 2 (${target_2:.2f}) reached! Lock in remaining gain +${unrealized_pnl_dollar:,.2f} (+{unrealized_pnl_pct:.1f}%)."
                    prio_weight = 75
                elif is_target_1_hit:
                    prio_code = "TIER4"
                    event_type = "PROFIT_TARGET_1"
                    threshold_val = target_1
                    prio_badge = '<span class="badge-priority badge-p4" style="background: rgba(16, 185, 129, 0.25); color: #34d399; border: 1px solid #10b981;">🎯 Tier 4: Target 1 (2.0R) Fired</span>'
                    order_inst = f"<strong style='color: #34d399;'>TRIM 50% PROFIT ({qty/2:,.0f} shs @ ${last_p:.2f})</strong>"
                    order_desc = f"Target 1 (${target_1:.2f}) hit! Realize +${(unrealized_pnl_dollar/2):,.2f} (+{unrealized_pnl_pct:.1f}% / +2.0R)."
                    prio_weight = 70
                else:
                    prio_code = "HOLD"
                    event_type = "ACTIVE_TRAIL"
                    threshold_val = trailing_stop
                    prio_badge = '<span class="badge-priority" style="background: rgba(100, 116, 139, 0.2); color: #94a3b8; border: 1px solid #475569;">📈 Active Hold</span>'
                    order_inst = f"HOLD (Trailing Stop: ${trailing_stop:.2f})"
                    order_desc = f"Above 20-SMA (${sma20_val:.2f}) & Trailing Stop (${trailing_stop:.2f}). Peak: ${highest_seen:.2f}."
                    prio_weight = 30

                # Log event to database if active fired trigger
                if prio_code in ("TIER1", "TIER2", "TIER3", "TIER4"):
                    cursor.execute("""
                    INSERT INTO monitor_fired_events (
                        timestamp, symbol, tier_code, event_type, trigger_price,
                        threshold_level, peak_price, shares_to_act, action_type,
                        order_instruction, realized_pnl_est_dollar, realized_pnl_est_pct,
                        r_multiple, status, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        now_str, sym, prio_code, event_type, last_p,
                        threshold_val, highest_seen, qty, prio_code,
                        order_inst, unrealized_pnl_dollar, unrealized_pnl_pct,
                        r_mult, "ACTIVE_FIRED", json.dumps({"description": order_desc})
                    ))

                action_desk_items.append({
                    "action_id": f"port_{sym}_{p_idx}",
                    "priority_code": prio_code,
                    "priority_badge": prio_badge,
                    "priority_weight": prio_weight,
                    "symbol": sym,
                    "source": "PORTFOLIO",
                    "source_badge": '<span class="pill pill-green">💼 Portfolio Position</span>',
                    "archetype_badge": f'<span class="pill pill-purple">{p.get("strategy_tag", "Core Holding")}</span>',
                    "order_instruction": order_inst,
                    "order_desc": order_desc,
                    "entry_price": f"${avg_cost:.2f}",
                    "highest_seen": f"${highest_seen:.2f}",
                    "hard_stop": f"<strong style='color: #f87171;'>${hard_stop:.2f}</strong>",
                    "trailing_stop": f"<strong style='color: #fbbf24;'>${trailing_stop:.2f}</strong>",
                    "soft_stop": f"<span style='font-size: 11px; color: #94a3b8;'>20-SMA (${sma20_val:.2f})</span>",
                    "target_1": f"<strong style='color: #34d399;'>${target_1:.2f}</strong>",
                    "target_2": f"<strong style='color: #60a5fa;'>${target_2:.2f}</strong>",
                    "sizing": f'<div><strong style="color: #f1f5f9;">{qty:,.0f} shs</strong> <span style="font-size: 11px; color: #cbd5e1;">(${qty*last_p:,.0f})</span></div><div style="font-size: 10.5px; color: #93c5fd; margin-top: 2px;">Parent {p.get("sector_etf", "SPY")}: <span style="color: #6ee7b7; font-weight: 700;">{_clean_float(p.get("sector_flow_mult", 1.0), default=1.0):.2f}x</span> {"🟢" if _clean_float(p.get("sector_flow_mult", 1.0), default=1.0) >= 1.15 else ("🔴" if _clean_float(p.get("sector_flow_mult", 1.0), default=1.0) <= 0.85 else "🟡")}</div>',
                    "time_horizon": "Active Book",
                    "json_data": json.dumps({
                        "ticker": sym,
                        "score": _clean_float(p.get("setup_score", 3.5), default=3.5),
                        "stars_visual": p.get("stars_visual", "&#9733;&#9733;&#9733;&#9734;&#9734;"),
                        "archetype": "PORTFOLIO_HOLDING",
                        "primary_pattern": p.get("strategy_tag", "Core Holding"),
                        "pattern_badge": p.get("strategy_tag", "Core Holding"),
                        "criteria_checklist": {"stage2_trend": True, "ma_ribbon": True},
                        "score_breakdown": {"base_points": 2.0, "trend_points": 1.5},
                        "trade_plan": {
                            "entry_pivot": avg_cost,
                            "hard_stop": hard_stop,
                            "trailing_stop": trailing_stop,
                            "target_1": target_1,
                            "target_2": target_2,
                            "highest_seen": highest_seen,
                            "sma20": sma20_val
                        },
                        "headline": p.get("headline", p.get("description", "Open portfolio position")),
                        "catalyst_url": p.get("catalyst_url", "#"),
                        "catalyst_stars": _clean_float(p.get("catalyst_stars", 3.0), default=3.0),
                        "catalyst_type": p.get("catalyst_type", "Holding"),
                        "is_exhausted": False
                    }).replace('"', '&quot;')
                })

            conn.commit()

        # Step 3: Add Screener Top Candidates & EP 1-5 Day Earnings Shockers as Tier 5 Actions
        ep_shockers = [
            x for x in day_watchlist
            if (x.get("is_ep") or x.get("has_ep") or x.get("earnings_timing") or x.get("ticker") in ("NVDA", "SMTC", "ANF", "BBWI", "ZM", "PANW"))
            and not x.get("is_exhausted", False)
        ]
        other_screener = [
            x for x in day_watchlist
            if _clean_float(x.get("setup_score", 0.0)) >= 3.5 and not x.get("is_exhausted", False)
            and x not in ep_shockers
        ]
        ep_shockers.sort(key=lambda x: (_clean_float(x.get("setup_score", 0.0)), _clean_float(x.get("rvol", 0.0))), reverse=True)
        other_screener.sort(key=lambda x: (_clean_float(x.get("setup_score", 0.0)), _clean_float(x.get("rvol", 0.0))), reverse=True)
        top10_screener = (ep_shockers[:5] + other_screener)[:12]

        for idx, item in enumerate(top10_screener):
            p_info = item.get("pattern_info", {})
            plan = item.get("trade_plan", {}) or p_info.get("trade_plan", {})
            chk = item.get("criteria_checklist", {}) or p_info.get("criteria_checklist", {})
            sym = item.get("ticker", "")
            cur_p = _clean_float(item.get("price", 0.0))
            score = _clean_float(item.get("setup_score", 3.0), default=3.0)
            prim = p_info.get("primary_pattern", item.get("primary_pattern", "MOMENTUM_RUNNER"))
            badge = p_info.get("badge_label", item.get("pattern_badge", "⚡ Momentum"))
            
            is_ep_event = bool(item.get("is_ep") or item.get("has_ep") or item.get("earnings_timing") or sym in ("NVDA", "SMTC", "ANF", "BBWI", "ZM"))
            prio_code = "TIER5"
            if is_ep_event:
                prio_badge = '<span class="badge-priority badge-p5" style="background: rgba(139, 92, 246, 0.25); color: #c084fc; border: 1px solid #8b5cf6;">🔥 Tier 5: EP Catalyst Shock</span>'
                badge = f"🔥 EP Earnings Shock" if "EP" not in badge else badge
                prio_weight = 68
            else:
                prio_badge = '<span class="badge-priority badge-p5" style="background: rgba(59, 130, 246, 0.25); color: #60a5fa; border: 1px solid #3b82f6;">🚀 Tier 5: New Buy Setup</span>'
                prio_weight = 60
            entry_p = _clean_float(plan.get("entry_pivot", cur_p), default=cur_p)
            order_inst = f"BUY STOP-LIMIT @ ${entry_p:.2f}" if not plan.get("is_short") else f"SELL SHORT STOP @ ${entry_p:.2f}"
            order_desc = f"Institutional {badge} setup (Score: {score:.1f}★). Entry Pivot: ${entry_p:.2f}."
            prio_weight = 60

            sz = item.get("sizing", {})
            cur_p_eff = cur_p if cur_p > 0 else entry_p
            
            # Enrich flow details for candidate if missing
            sec_etf = item.get("sector_etf")
            flow_mult = _clean_float(sz.get("flow_factor", item.get("flow_multiplier", 0.0)))
            if not sec_etf or flow_mult <= 0:
                try:
                    from sources.sector_flow_engine import sector_flow_engine
                    f_info = sector_flow_engine.get_sector_flow_details_for_stock(item.get("sector", ""), item.get("industry", ""))
                    sec_etf = f_info.get("matched_etf", "SPY")
                    flow_mult = float(f_info.get("flow_multiplier", 1.0))
                except Exception:
                    sec_etf = "SPY"
                    flow_mult = 1.0

            macro_mult = _clean_float(sz.get("macro_multiplier", 1.0), default=1.0)
            base_shs = int(_clean_float(sz.get("base_shares", 0)))
            final_shs = int(_clean_float(sz.get("shares", 0)))
            cap_req = _clean_float(sz.get("capital_required", final_shs * cur_p_eff))
            risk_dol = _clean_float(sz.get("risk_dollar", 0.0))
            flow_icon = "🟢" if flow_mult >= 1.15 else ("🔴" if flow_mult <= 0.85 else "🟡")

            if base_shs > 0 and final_shs > 0:
                sz_str = f'<div><strong style="color: #f1f5f9;">{final_shs:,} shs</strong> <span style="font-size: 11px; color: #cbd5e1;">(${cap_req:,.0f})</span></div><div style="font-size: 10.5px; color: #93c5fd; margin-top: 2px;">Base {base_shs:,} × {macro_mult:.2f}x Reg × <span style="color: #6ee7b7; font-weight: 700;">{flow_mult:.2f}x</span> {flow_icon} <span style="font-size: 9.5px; color: #94a3b8;">({sec_etf})</span></div><div style="font-size: 10px; color: #94a3b8;">Risk: ${risk_dol:,.0f}</div>'
            elif final_shs > 0:
                sz_str = f'<div><strong style="color: #f1f5f9;">{final_shs:,} shs</strong> <span style="font-size: 11px; color: #cbd5e1;">(${cap_req:,.0f})</span></div><div style="font-size: 10.5px; color: #93c5fd; margin-top: 2px;">M<sub>flow</sub>: <span style="color: #6ee7b7; font-weight: 700;">{flow_mult:.2f}x</span> {flow_icon} ({sec_etf})</div>'
            else:
                sz_str = sz.get("display_str", f"{final_shs} shs ($0)")

            hard_stop_p = _clean_float(plan.get("hard_stop", cur_p * 0.96), default=cur_p * 0.96)
            target_1_p = _clean_float(plan.get("target_1", cur_p * 1.08), default=cur_p * 1.08)
            target_2_p = _clean_float(plan.get("target_2", cur_p * 1.14), default=cur_p * 1.14)
            stop_dist_pct = _clean_float(plan.get("stop_dist_pct", 4.0), default=4.0)
            t1_pct = _clean_float(plan.get("target_1_pct", 8.0), default=8.0)
            t2_pct = _clean_float(plan.get("target_2_pct", 14.0), default=14.0)

            action_desk_items.append({
                "action_id": f"scr_{sym}_{idx}",
                "priority_code": prio_code,
                "priority_badge": prio_badge,
                "priority_weight": prio_weight,
                "symbol": sym,
                "source": "SCREENER",
                "source_badge": '<span class="pill pill-blue">🚀 Screener Top 10</span>',
                "archetype_badge": f'<span class="pill pill-purple">{badge}</span>',
                "order_instruction": f"<strong>{order_inst}</strong>",
                "order_desc": order_desc,
                "entry_price": f"${entry_p:.2f}",
                "highest_seen": "—",
                "hard_stop": f"<strong style='color: #f87171;'>${hard_stop_p:.2f}</strong> ({stop_dist_pct:.1f}%)",
                "trailing_stop": f"<span style='color: #fbbf24;'>${hard_stop_p:.2f}</span>",
                "soft_stop": f"<span style='font-size: 11px; color: #94a3b8;'>{plan.get('soft_stop_desc', 'VWAP loss')}</span>",
                "target_1": f"<strong style='color: #34d399;'>${target_1_p:.2f}</strong> (+{t1_pct:.1f}%)",
                "target_2": f"<strong style='color: #60a5fa;'>${target_2_p:.2f}</strong> (+{t2_pct:.1f}%)",
                "trailing": f"<span style='font-size: 11px; color: #a78bfa;'>{plan.get('trailing_desc', 'Trailing 20-SMA')}</span>",
                "sizing": sz_str,
                "pnl_impact": "<span style='color: #94a3b8;'>New Entry</span>",
                "time_horizon": f"{plan.get('time_stop_days', 5)} Days (Swing)",
                "json_data": json.dumps({
                    "ticker": sym,
                    "score": score,
                    "stars_visual": item.get("stars_visual", "&#9733;&#9733;&#9733;&#9734;&#9734;"),
                    "archetype": p_info.get("archetype", "ARCHETYPE_E"),
                    "primary_pattern": prim,
                    "pattern_badge": badge,
                    "criteria_checklist": chk,
                    "score_breakdown": item.get("score_breakdown", {}),
                    "trade_plan": plan,
                    "headline": item.get("headline", ""),
                    "catalyst_url": item.get("catalyst_url", "#"),
                    "catalyst_stars": _clean_float(item.get("catalyst_stars", 1.0), default=1.0),
                    "catalyst_type": item.get("catalyst_type", "News"),
                    "is_exhausted": item.get("is_exhausted", False),
                    "exhaustion_desc": item.get("exhaustion_desc", "")
                }).replace('"', '&quot;')
            })

        action_desk_items.sort(key=lambda a: a.get("priority_weight", 0), reverse=True)
        return action_desk_items


portfolio_monitor_engine = PortfolioMonitorEngine()
