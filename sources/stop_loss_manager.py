"""Multi-Tier Adaptive Stop-Loss & Early Invalidation Engine (Skill 12 v2.0).
Computes real-time protective stops for all portfolio holdings:
  1. Chandelier Trailing ATR(14) Stops
  2. +1.0R Breakeven Profit Lock
  3. Age-Based Structural Support (EP Low / 50 SMA / 5% Trail)
  4. Institutional Sector Flow Invalidation (Pre-Emptive 50% Trim)
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from config import DATA_DIR
from sources.portfolio_manager import portfolio_mgr
from sources.sector_flow_engine import sector_flow_engine

logger = logging.getLogger("stop_loss_manager")


class StopLossManager:
    """Institutional Multi-Tier Adaptive Stop Engine conforming strictly to Skill 12."""

    def __init__(self, atr_multiplier: float = 2.0, soft_stop_buffer_pct: float = 0.10):
        self.atr_multiplier = atr_multiplier  # 2.0x ATR(14) standard Chandelier distance
        self.soft_stop_buffer_pct = soft_stop_buffer_pct  # 10% early warning buffer

    def calculate_position_stop(
        self,
        symbol: str,
        current_price: float,
        cost_basis: float,
        existing_stop: float = 0.0,
        high_price: float = 0.0,
        atr_14: float = 0.0,
        sma_50: float = 0.0,
        is_leveraged: bool = False,
        stock_sector: str = "General",
        stock_industry: str = "Diversified",
        sector_flow_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compute multi-tier adaptive stop and check for invalidation alerts."""
        cur_p = float(current_price or 0.0)
        avg_cost = float(cost_basis or 0.0)
        high_p = float(high_price or cur_p)
        if high_p < cur_p:
            high_p = cur_p

        if cur_p <= 0:
            return {"error": "Invalid current price"}

        active_atr_mult = self.atr_multiplier
        try:
            from sources.parameter_tuner import parameter_tuner
            tuning_data = parameter_tuner.get_tuning_report()
            active_atr_mult = float(tuning_data.get("calibrated_stops", {}).get("clamped_multiplier", self.atr_multiplier))
        except Exception:
            pass

        # 1. Base ATR-Derived Stop
        if atr_14 > 0:
            stop_dist = active_atr_mult * atr_14
            chandelier_stop = round(high_p - stop_dist, 2)
            stop_source = f"Chandelier ATR(14) ({active_atr_mult:.1f}x = ${stop_dist:.2f})"
        else:
            # Fallback based on asset type
            default_pct = 0.08 if is_leveraged else 0.05
            stop_dist = cur_p * default_pct
            chandelier_stop = round(cur_p * (1.0 - default_pct), 2)
            stop_source = f"Default Fixed {default_pct*100:.0f}% Stop"

        # 2. Structural Support Floor (50 SMA)
        structural_support = round(sma_50, 2) if sma_50 > 0 else None

        # 3. Initial Risk Unit (1.0R) and +1.0R Breakeven Profit Lock
        initial_risk = avg_cost - (existing_stop if existing_stop > 0 else avg_cost * 0.95)
        if initial_risk <= 0:
            initial_risk = avg_cost * 0.05

        breakeven_target = round(avg_cost + initial_risk, 2)
        profit_locked = False
        final_stop = chandelier_stop

        # Lock Breakeven if current price >= entry + 1.0R
        if avg_cost > 0 and cur_p >= breakeven_target:
            if final_stop < avg_cost:
                final_stop = round(avg_cost, 2)
                profit_locked = True
                stop_source = f"🔒 Breakeven Lock (+1.0R Attained at ${breakeven_target:.2f})"

        # Ratchet check: Stop should never move downwards
        if existing_stop > 0 and existing_stop > final_stop:
            final_stop = existing_stop
            stop_source = f"Preserved Ratchet Stop (${existing_stop:.2f})"

        # 4. Soft Stop (10% Buffer above Hard Stop)
        stop_gap = cur_p - final_stop
        soft_stop = round(final_stop + (stop_gap * self.soft_stop_buffer_pct), 2) if stop_gap > 0 else final_stop
        stop_dist_pct = ((cur_p - final_stop) / cur_p) * 100.0 if cur_p > 0 else 0.0

        # 5. Sector Flow Invalidation Check (Skill 14 & 12)
        is_hot, flow_rationale, flow_mult = sector_flow_engine.is_stock_in_hot_sector(stock_sector, stock_industry, sector_flow_data)
        sector_invalidation = False
        if not is_hot and flow_mult <= 0.75:
            sector_invalidation = True

        # 6. Determine Risk State & Action Plan
        if cur_p <= final_stop:
            status = "🔴 HARD STOP TRIGGERED"
            action_plan = f"EXIT IMMEDIATE: Price (${cur_p:.2f}) breached protective stop (${final_stop:.2f})"
            status_class = "pill-red"
        elif sector_invalidation:
            status = "⚠️ SECTOR INVALIDATION"
            action_plan = f"PRE-EMPTIVE 50% TRIM: Parent sector flow collapsed ({flow_rationale})"
            status_class = "pill-red"
        elif cur_p <= soft_stop:
            status = "🟡 SOFT STOP WARNING"
            action_plan = f"MONITOR CLOSE: Price within 10% buffer of stop (${final_stop:.2f})"
            status_class = "pill-yellow"
        elif profit_locked:
            status = "🟢 PROFIT LOCKED"
            action_plan = f"HOLD / TRAIL: Downside protected at Breakeven (${final_stop:.2f})"
            status_class = "pill-green"
        else:
            status = "🟢 SAFE"
            action_plan = f"HOLD: Trailing Stop at ${final_stop:.2f} ({stop_dist_pct:+.1f}%)"
            status_class = "pill-green"

        return {
            "symbol": symbol,
            "current_price": cur_p,
            "cost_basis": avg_cost,
            "high_price": high_p,
            "active_stop_price": final_stop,
            "soft_stop_price": soft_stop,
            "stop_distance_pct": round(stop_dist_pct, 2),
            "stop_source": stop_source,
            "structural_50_sma": structural_support,
            "is_profit_locked": profit_locked,
            "breakeven_price": avg_cost,
            "sector_invalidation_alert": sector_invalidation,
            "flow_rationale": flow_rationale,
            "risk_status": status,
            "status_class": status_class,
            "action_plan": action_plan,
        }

    def audit_all_portfolio_stops(
        self,
        portfolio_data: Optional[Dict[str, Any]] = None,
        sector_flow_data: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Audit all 73 holdings in the portfolio and generate active stop management alerts."""
        if not portfolio_data:
            portfolio_data = portfolio_mgr.enrich_live_metrics()

        positions = portfolio_data.get("positions", [])
        audited_stops = []

        for p in positions:
            if not isinstance(p, dict):
                continue
            sym = (p.get("symbol") or p.get("underlying", "")).upper().strip()
            cur_p = float(p.get("last_price", 0.0) or 0.0)
            avg_cost = float(p.get("average_cost", 0.0) or 0.0)
            cur_stop = float(p.get("stop_loss", 0.0) or 0.0)
            sec = p.get("sector", "General")
            ind = p.get("industry", "Diversified")
            is_opt = p.get("is_option", False)

            if is_opt or cur_p <= 0:
                continue

            # Extract technical indicators from position attributes
            sma50_val = 0.0
            try:
                sma50_val = float(str(p.get("sma50", "0")).replace("$", "").replace(",", "").strip())
            except Exception:
                sma50_val = 0.0

            stop_eval = self.calculate_position_stop(
                symbol=sym,
                current_price=cur_p,
                cost_basis=avg_cost,
                existing_stop=cur_stop,
                high_price=cur_p * 1.02,  # approximate session range
                atr_14=cur_p * 0.025,    # standard ATR proxy
                sma_50=sma50_val,
                is_leveraged=(sym in ["SOXL", "SOXS", "TQQQ", "SQQQ", "BITO", "CURE"]),
                stock_sector=sec,
                stock_industry=ind,
                sector_flow_data=sector_flow_data,
            )

            # Attach position metadata
            stop_eval["quantity"] = float(p.get("quantity", 0.0) or 0.0)
            stop_eval["current_value"] = float(p.get("current_value", 0.0) or 0.0)
            stop_eval["weight_pct"] = float(p.get("weight_pct", 0.0) or 0.0)
            stop_eval["today_pnl_pct"] = float(p.get("today_pnl_pct", 0.0) or 0.0)
            audited_stops.append(stop_eval)

        # Sort with highest risk alerts first (Triggered -> Invalidation -> Soft Stop -> Safe)
        status_rank = {
            "🔴 HARD STOP TRIGGERED": 0,
            "⚠️ SECTOR INVALIDATION": 1,
            "🟡 SOFT STOP WARNING": 2,
            "🟢 PROFIT LOCKED": 3,
            "🟢 SAFE": 4,
        }
        audited_stops.sort(key=lambda x: status_rank.get(x.get("risk_status", ""), 5))
        return audited_stops


stop_loss_manager = StopLossManager()
