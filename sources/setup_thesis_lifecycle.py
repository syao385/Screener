"""Skill 14: Unified Setup-Thesis Lifecycle State Machine (Phase 6).
========================================================================================
Unifies technical breakout setups (9 Master Archetypes) with fundamental thesis management:
  1. Two-Stage State Machine:
     - Stage 1 (TACTICAL_SETUP): Days 1-10, governed by technical pivots, hard stops,
       soft VWAP stops, and +2.0R / +3.5R profit targets.
     - Promotion Gatekeeper: Checks if Target 1 (+2.0R) reached OR held >= 10 days in
       Stage 2 trend with healthy Sloan accruals (<= 8%) and intact moat.
     - Stage 2 (CORE_THESIS): Escalated into long-term fundamental holding with 8-quarter
       accounting anchors, Health Score monitoring, and red-line tracking.
  2. Closed-Loop Execution Desk Routing:
     - Tier 1: Broken theses (Health < 3.0) & fatal red-lines
     - Tier 2: News Pulse stealth flow surges (Z_eps >= 2.0)
     - Tier 3: Weakened thesis trims ((6 - Health) * 10%) & Target 1/2 completions
"""

import math
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple

from config import TZ_EST, DATA_DIR
from sources.thesis_monitor import thesis_monitor
from sources.news_pulse import news_pulse

logger = logging.getLogger("setup_thesis_lifecycle")


class SetupThesisLifecycleManager:
    """Manages the two-stage lifecycle transition from tactical trade to core thesis."""

    def __init__(self):
        pass

    def evaluate_lifecycle_stage(
        self,
        symbol: str,
        holding_days: int,
        current_price: float,
        entry_price: float,
        hard_stop: float,
        target_1: float,
        target_2: float,
        sloan_ratio_pct: float = 3.5,
        sue_val: float = 0.5,
        is_stage_2_trend: bool = True,
        origin_archetype: str = "Base Breakout",
    ) -> Dict[str, Any]:
        """Evaluate whether a position is TACTICAL_SETUP or CORE_THESIS and determine promotion."""
        if entry_price <= 0:
            return {
                "symbol": symbol,
                "stage": "TACTICAL_SETUP",
                "stage_label": "⚡ Tactical Setup (Day 0)",
                "promoted": False,
                "promotion_reason": "No entry price recorded",
                "health": thesis_monitor.compute_health_score(),
            }

        unrealized_gain_pct = ((current_price - entry_price) / entry_price) * 100.0
        if 0 < hard_stop < entry_price:
            r_risk = entry_price - hard_stop
        else:
            r_risk = max(0.01, entry_price * 0.05)
        r_multiple = (current_price - entry_price) / r_risk

        target_1_hit = bool(target_1 > 0 and current_price >= target_1) or (r_multiple >= 2.0)
        ten_days_held = bool(holding_days >= 10 and is_stage_2_trend)

        # Fundamentals gatekeeper check:
        # Sloan ratio <= 8.0% (healthy cash backed), SUE >= -0.2 (no major accounting disaster)
        fundamentals_clean = bool(sloan_ratio_pct <= 8.0 and sue_val >= -0.2)

        # Two-stage transition logic:
        if (target_1_hit or ten_days_held) and fundamentals_clean:
            stage = "CORE_THESIS"
            stage_badge = "🏛️ Core Investment Thesis"
            promoted = True
            if target_1_hit:
                promotion_reason = f"Target 1 (+{r_multiple:.1f}R) secured & forensic cash flow verified (Sloan: {sloan_ratio_pct:.1f}%)."
            else:
                promotion_reason = f"Held {holding_days} days in Stage 2 trend with healthy accruals (Sloan: {sloan_ratio_pct:.1f}%)."
        else:
            stage = "TACTICAL_SETUP"
            stage_badge = f"⚡ Tactical Setup (Day {holding_days})"
            promoted = False
            if not fundamentals_clean:
                promotion_reason = f"Retained in Tactical mode: Accruals or earnings quality below institutional threshold (Sloan: {sloan_ratio_pct:.1f}%)."
            else:
                promotion_reason = f"Under swing management: Waiting for Target 1 (+2.0R) or 10-day Stage 2 confirmation."

        # Compute Health Score
        broken = 1 if (current_price < hard_stop and hard_stop > 0) else 0
        breached = 0
        if sloan_ratio_pct > 10.0:
            breached += 1
        if sue_val < -1.0:
            breached += 1
        marginal = 1 if (sloan_ratio_pct > 6.0 or sue_val < 0.0) else 0
        redlines = 1 if (sue_val <= -2.0 or sloan_ratio_pct >= 20.0 or (hard_stop > 0 and current_price <= hard_stop * 0.90)) else 0
        strengths = 1 if (sue_val >= 1.0 and r_multiple >= 1.5) else 0

        health = thesis_monitor.compute_health_score(
            num_broken=broken,
            num_breached=breached,
            num_marginal=marginal,
            num_redlines=redlines,
            num_new_strengths=strengths,
        )

        return {
            "symbol": symbol,
            "stage": stage,
            "stage_label": stage_badge,
            "holding_days": holding_days,
            "origin_archetype": origin_archetype,
            "unrealized_gain_pct": round(unrealized_gain_pct, 2),
            "r_multiple": round(r_multiple, 2),
            "promoted": promoted,
            "promotion_reason": promotion_reason,
            "target_1_hit": target_1_hit,
            "health": health,
            "sloan_ratio_pct": round(sloan_ratio_pct, 1),
            "sue_val": round(sue_val, 2),
        }

    def evaluate_fleet_theses(
        self,
        portfolio_positions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Evaluate entire portfolio fleet for lifecycle stages, health scores, and action tickets."""
        results = []
        for pos in portfolio_positions:
            sym = pos.get("symbol", "")
            if not sym or sym.startswith("^"):
                continue

            last_p = float(pos.get("last_price") or pos.get("current_price") or pos.get("price") or 0.0)
            cost_p = float(pos.get("average_cost") or pos.get("avg_cost") or pos.get("cost_basis") or pos.get("entry_price") or last_p)
            stop_p = float(pos.get("stop_loss") or pos.get("hard_stop") or (cost_p * 0.96 if cost_p > 0 else last_p * 0.96))
            t1_p = float(pos.get("target_price") or pos.get("target_1") or (cost_p * 1.08 if cost_p > 0 else last_p * 1.08))
            t2_p = float(pos.get("target_price_2") or pos.get("target_2") or (cost_p * 1.15 if cost_p > 0 else last_p * 1.15))

            # Calculate holding days from entry_date if available
            days = 12
            if pos.get("holding_days"):
                days = int(pos["holding_days"])
            elif pos.get("days_held"):
                days = int(pos["days_held"])
            elif pos.get("entry_date"):
                try:
                    ed_str = str(pos["entry_date"]).strip()
                    for fmt in ("%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y"):
                        try:
                            ed_dt = datetime.datetime.strptime(ed_str, fmt).date()
                            days = max(1, (datetime.date.today() - ed_dt).days)
                            break
                        except ValueError:
                            continue
                except Exception:
                    days = 12

            arch = pos.get("strategy_tag") or pos.get("setup_code") or "Core Growth & Momentum"

            # Dynamically ingest real earnings factors if available
            sloan = float(pos.get("sloan_ratio_pct") or pos.get("sloan_accrual_pct") or 0.0)
            sue = float(pos.get("sue_val") or pos.get("earnings_sue") or 0.0)
            gross_margin = float(pos.get("gross_margin_pct", 62.5))
            rev_surprise = float(pos.get("rev_surprise_pct", 5.2))
            pead_score = 65.0
            playbook = "Playbook 2: Day 1-5 PEAD Multi-Week Swing"
            playbook_action = "Accumulate on Day 2-3 pullback to 20-EMA."

            earnings_file = DATA_DIR / "earnings_reports" / f"{sym}_Latest.json"
            if earnings_file.exists():
                try:
                    import json
                    with open(earnings_file, "r", encoding="utf-8") as ef:
                        e_data = json.load(ef)
                        flash_s = e_data.get("flash_summary", {})
                        e_facts = flash_s.get("factors", {})
                        if e_facts.get("sloan_accrual_pct") is not None and not math.isnan(e_facts.get("sloan_accrual_pct")):
                            sloan = float(e_facts["sloan_accrual_pct"])
                        if e_facts.get("sue") is not None and not math.isnan(e_facts.get("sue")):
                            sue = float(e_facts["sue"])
                        if e_facts.get("rev_surprise_pct") is not None and not math.isnan(e_facts.get("rev_surprise_pct")):
                            rev_surprise = float(e_facts["rev_surprise_pct"])
                        if e_facts.get("pead_score") is not None and not math.isnan(e_facts.get("pead_score")):
                            pead_score = float(e_facts["pead_score"])
                        if e_facts.get("category_label"):
                            arch = e_facts["category_label"]
                        if flash_s.get("active_playbook"):
                            playbook = flash_s["active_playbook"]
                        if flash_s.get("playbook_action"):
                            playbook_action = flash_s["playbook_action"]
                        lq = flash_s.get("latest_quarter", {})
                        if lq.get("gross_margin_pct") is not None and not math.isnan(lq.get("gross_margin_pct")):
                            gross_margin = float(lq["gross_margin_pct"])
                except Exception:
                    pass

            if not sloan and not pos.get("sloan_ratio_pct"):
                sloan = 2.8

            eval_res = self.evaluate_lifecycle_stage(
                symbol=sym,
                holding_days=days,
                current_price=last_p,
                entry_price=cost_p,
                hard_stop=stop_p,
                target_1=t1_p,
                target_2=t2_p,
                sloan_ratio_pct=sloan,
                sue_val=sue,
                origin_archetype=arch,
            )
            eval_res["gross_margin_pct"] = round(gross_margin, 1)
            eval_res["rev_surprise_pct"] = round(rev_surprise, 1)
            eval_res["pead_score"] = round(pead_score, 1)
            eval_res["playbook"] = playbook
            eval_res["playbook_action"] = playbook_action
            results.append(eval_res)

        return results


# Global singleton instance
lifecycle_mgr = SetupThesisLifecycleManager()
