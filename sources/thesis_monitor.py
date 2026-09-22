"""Skill 08: Investment Thesis Monitor, Quantitative Drift & Dynamic Stop Engine (Phase 6).
========================================================================================
Tracks lifecycle validity of institutional investment theses:
  1. Composite Health Score (0 - 10):
       H = 10.0 - (3.0 * Broken) - (1.5 * Breached) - (0.5 * Marginal) - (2.0 * Redlines) + (0.5 * NewStrengths)
  2. Formulaic Risk-Budgeted Sizing Rule:
       If H < 6.0: Sell Size (%) = (6.0 - H) * 10%
       If H < 3.0 or Fatal Red-Line: Sell 100% at next open
  3. Dynamic Volatility-Adjusted Stops with Sector & IV Rank Scaling:
       Stop Distance = 2.0 * ATR(14) * (1 + Sector_Factor) * (1 + 0.5 * IVR_30d)
  4. Quantitative and Semantic Drift Classification:
       NO_DRIFT (<10), MILD_DRIFT (10-25), MODERATE_DRIFT (25-50), SIGNIFICANT_DRIFT (>50)
"""

import math
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple

from config import TZ_EST

logger = logging.getLogger("thesis_monitor")

# Sector Volatility Factors (normalized relative to SPY)
SECTOR_VOL_FACTORS = {
    "Technology": 0.25,
    "Financials": 0.15,
    "Healthcare": 0.10,
    "Consumer Discretionary": 0.20,
    "Communication Services": 0.18,
    "Industrials": 0.12,
    "Consumer Staples": 0.05,
    "Energy": 0.30,
    "Utilities": 0.08,
    "Real Estate": 0.15,
    "Materials": 0.20,
}


class ThesisMonitorEngine:
    """Quantitative Thesis Lifecycle and Drift Monitoring Engine."""

    def __init__(self):
        pass

    def compute_health_score(
        self,
        num_broken: int = 0,
        num_breached: int = 0,
        num_marginal: int = 0,
        num_redlines: int = 0,
        num_new_strengths: int = 0,
    ) -> Dict[str, Any]:
        """Compute exact Composite Health Score (0.0 - 10.0) and action recommendation.
        
        Formula:
          Score = 10.0 - (3.0 * BROKEN) - (1.5 * BREACHED) - (0.5 * MARGINAL) - (2.0 * REDLINES) + (0.5 * STRENGTHS)
        """
        deductions = (3.0 * num_broken) + (1.5 * num_breached) + (0.5 * num_marginal) + (2.0 * num_redlines)
        bonuses = 0.5 * num_new_strengths
        raw_score = 10.0 - deductions + bonuses
        clamped_score = max(0.0, min(10.0, round(raw_score, 1)))

        # Sizing / Trim formula
        if clamped_score < 3.0 or num_redlines > 0:
            category = "BROKEN" if num_redlines == 0 else "CRITICAL_REDLINE"
            action = "SELL_ALL"
            trim_pct = 100.0
            order_priority = "TIER1"
            badge_color = "#ef4444"
            desc = "Thesis damaged or fatal red-line triggered. Liquidate position at next market open."
        elif clamped_score < 5.0:
            category = "DAMAGED"
            action = "REDUCE_50"
            trim_pct = 50.0
            order_priority = "TIER2"
            badge_color = "#f97316"
            desc = "Thesis severely weakened. Reduce position 50% and raise emergency surveillance."
        elif clamped_score < 6.0:
            category = "WEAKENED"
            action = "TRIM_FORMULA"
            # Linear trim rule: (6.0 - Score) * 10%
            trim_pct = round((6.0 - clamped_score) * 10.0, 1)
            order_priority = "TIER3"
            badge_color = "#eab308"
            desc = f"Margin of safety eroded. Proportional trim of {trim_pct:.1f}% recommended."
        elif clamped_score < 9.0:
            category = "INTACT"
            action = "HOLD"
            trim_pct = 0.0
            order_priority = "TIER4"
            badge_color = "#10b981"
            desc = "Core investment thesis intact. Maintain standard trailing stop rules."
        else:
            category = "STRONG"
            action = "ADD_ELIGIBLE"
            trim_pct = 0.0
            order_priority = "TIER4"
            badge_color = "#34d399"
            desc = "Moat widening and financials confirming thesis. Eligible for position add on pullbacks."

        return {
            "health_score": clamped_score,
            "category": category,
            "action": action,
            "trim_pct": trim_pct,
            "order_priority": order_priority,
            "badge_color": badge_color,
            "description": desc,
            "breakdown": {
                "broken": num_broken,
                "breached": num_breached,
                "marginal": num_marginal,
                "redlines": num_redlines,
                "strengths": num_new_strengths,
            },
        }

    def compute_dynamic_volatility_stop(
        self,
        current_price: float,
        highest_price_seen: float,
        atr14: float,
        sector: str = "Technology",
        iv_rank_pct: float = 30.0,
        current_gain_pct: float = 0.0,
    ) -> Dict[str, Any]:
        """Compute regime-adaptive dynamic stop price and ratchet levels.
        
        Formula:
          Stop Distance = Base_Mult * ATR(14) * (1 + Sector_Factor) * (1 + 0.5 * (IVR / 100))
        """
        if current_price <= 0 or atr14 <= 0:
            return {"stop_price": round(current_price * 0.95, 2), "stop_distance": 0.0, "status": "DEFAULT"}

        # Base multiplier ratchets tighter as unrealized profits expand
        if current_gain_pct >= 50.0:
            base_mult = 0.75
        elif current_gain_pct >= 30.0:
            base_mult = 1.0
        elif current_gain_pct >= 15.0:
            base_mult = 1.5
        else:
            base_mult = 2.0

        sec_factor = SECTOR_VOL_FACTORS.get(sector, 0.15)
        ivr_factor = max(0.0, min(1.0, iv_rank_pct / 100.0))

        # Dynamic stop distance
        stop_dist = base_mult * atr14 * (1.0 + sec_factor) * (1.0 + (0.5 * ivr_factor))
        peak_anchor = max(current_price, highest_price_seen)
        stop_price = round(max(0.01, peak_anchor - stop_dist), 2)

        is_breached = bool(current_price <= stop_price)
        dist_to_stop_pct = round(((current_price - stop_price) / current_price) * 100.0, 2)

        return {
            "current_price": current_price,
            "highest_seen": peak_anchor,
            "atr14": round(atr14, 2),
            "base_multiplier": base_mult,
            "sector_factor": sec_factor,
            "iv_rank_pct": iv_rank_pct,
            "stop_distance": round(stop_dist, 2),
            "stop_price": stop_price,
            "dist_to_stop_pct": dist_to_stop_pct,
            "is_breached": is_breached,
        }

    def compute_quantitative_drift(
        self,
        baseline_assumptions: Dict[str, float],
        current_data: Dict[str, float],
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Compute quantitative multi-metric parameter drift score (0 - 100).
        
        Formula:
          Drift_Score = Sum(|new - old| / old * weight) * 100
        """
        if not baseline_assumptions or not current_data:
            return {"drift_score": 0.0, "classification": "NO_DRIFT", "deltas": {}}

        total_weight = 0.0
        weighted_drift = 0.0
        deltas = {}

        for metric, old_val in baseline_assumptions.items():
            if old_val == 0 or metric not in current_data:
                continue
            new_val = current_data[metric]
            delta_pct = ((new_val - old_val) / abs(old_val)) * 100.0
            w = weights.get(metric, 1.0) if weights else 1.0

            deltas[metric] = {
                "baseline": old_val,
                "current": new_val,
                "delta_pct": round(delta_pct, 2),
                "weight": w,
            }

            # Only negative deviations count as adverse thesis drift for growth/margins
            adverse_deviation = max(0.0, -delta_pct) if "margin" in metric.lower() or "growth" in metric.lower() else abs(delta_pct)
            weighted_drift += (adverse_deviation / 100.0) * w
            total_weight += w

        drift_score = round((weighted_drift / total_weight) * 100.0, 1) if total_weight > 0 else 0.0

        if drift_score < 10.0:
            classification = "NO_DRIFT"
            label = "🟢 No Drift (Assumptions Intact)"
        elif drift_score < 25.0:
            classification = "MILD_DRIFT"
            label = "🟡 Mild Drift (Monitor Next Quarter)"
        elif drift_score < 50.0:
            classification = "MODERATE_DRIFT"
            label = "🟠 Moderate Drift (Review Required)"
        else:
            classification = "SIGNIFICANT_DRIFT"
            label = "🔴 Significant Drift (Thesis Changed)"

        return {
            "drift_score": drift_score,
            "classification": classification,
            "label": label,
            "deltas": deltas,
        }


# Global singleton instance
thesis_monitor = ThesisMonitorEngine()
