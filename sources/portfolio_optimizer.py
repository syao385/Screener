"""Closed-Loop Portfolio Sizer & Conviction Engine (Skill 07 v2.0).
Computes exact math-based share sizing enforcing the 3-Way Minimum:
  Final Shares = min(Shares_Risk, Shares_TierCap, Shares_AvailableCash)
Governs both New Screener Watchlist setups and Existing Portfolio Rebalancing.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from config import DATA_DIR
from sources.portfolio_manager import portfolio_mgr
from sources.sector_flow_engine import sector_flow_engine

logger = logging.getLogger("portfolio_optimizer")

# 3 Institutional Conviction Tiers
CONVICTION_TIERS = {
    1: {
        "tier_name": "Tier 1: Core Institutional Champions",
        "tier_code": "TIER_1",
        "description": "Deep fundamental moat; passed 4 Masters; secular macro tailwind; 5-10 yr visibility",
        "max_position_cap_pct": 10.0,  # Max 10% of portfolio NAV
        "risk_multiplier": 1.20,      # 1.2x base risk tolerance
        "aggregate_cap_pct": 35.0,    # Max 35% of portfolio in Tier 1
    },
    2: {
        "tier_name": "Tier 2: High-Growth Tactical Leaders",
        "tier_code": "TIER_2",
        "description": "Strong EPS growth (>25%), high RS (>85), verified base breakout, positive sector flow",
        "max_position_cap_pct": 5.0,  # Max 5% of portfolio NAV
        "risk_multiplier": 0.80,      # 0.8x base risk tolerance
        "aggregate_cap_pct": 60.0,    # Max 60% of portfolio in Tier 1 + 2
    },
    3: {
        "tier_name": "Tier 3: Asymmetric / Tactical / Leveraged",
        "tier_code": "TIER_3",
        "description": "Catalyst-driven, high-beta, turnaround, or leveraged ETF. Capped for capital protection",
        "max_position_cap_pct": 2.0,  # Max 2% of portfolio NAV
        "risk_multiplier": 0.50,      # 0.5x base risk tolerance
        "aggregate_cap_pct": 100.0,
    },
}

# Known Core Holding Tier Assignments
CORE_TIER_OVERRIDE = {
    "MU": 1,
    "PLTR": 1,
    "COST": 1,
    "NVDA": 2,
    "AXP": 2,
    "WDC": 2,
    "HOOD": 2,
    "MRVL": 2,
    "SMH": 2,
    "SPMO": 2,
    "COPX": 2,
    "SOXL": 3,
    "DRAM": 3,
    "FCEL": 3,
    "SILJ": 3,
    "GDXJ": 3,
    "CURE": 3,
}

LEVERAGED_TICKERS = {
    "SOXL", "SOXS", "TQQQ", "SQQQ", "UPRO", "SPXU", "NUGT", "DUST", "BITX", "CURE", "FAS", "FAZ"
}


class PortfolioOptimizer:
    """Institutional Closed-Loop Portfolio Sizing & Allocation Engine."""

    def __init__(self, base_risk_pct: float = 0.005, cash_reserve_floor_pct: float = 0.15):
        self.base_risk_pct = base_risk_pct  # Standard 0.50% account equity risk per trade
        self.cash_reserve_floor_pct = cash_reserve_floor_pct  # Preserve minimum 15% cash

    def classify_conviction_tier(
        self,
        ticker: str,
        setup_data: Optional[Dict[str, Any]] = None,
        market_cap: float = 0.0,
        manual_override_tier: Optional[int] = None,
    ) -> int:
        """
        Classify any stock or holding into Conviction Tier (1, 2, or 3).
        Priority:
          1. Explicit Manual User Override (saved in portfolio.json or UI edit)
          2. Leveraged ETF Guardrail -> Always Tier 3 (2% max cap)
          3. Core Champion Foundational Thesis (MU, PLTR, COST -> Tier 1)
          4. Quantitative Metric Classification (4-Masters Moat, EPS Growth, RS, Setup Score)
        """
        t = str(ticker).upper().strip()

        # 1. Highest Priority: Manual User Override
        if manual_override_tier in [1, 2, 3]:
            return int(manual_override_tier)

        setup = setup_data or {}
        if setup.get("conviction_tier") in [1, 2, 3, "1", "2", "3"]:
            return int(setup["conviction_tier"])

        # 2. Leveraged ETF Protection -> Tier 3
        if t in LEVERAGED_TICKERS or setup.get("is_leveraged", False):
            return 3

        # 3. Known Core Conviction Overrides
        if t in CORE_TIER_OVERRIDE:
            return CORE_TIER_OVERRIDE[t]

        # 4. Quantitative Multi-Factor Classification
        stars = float(setup.get("setup_score", setup.get("stars", setup.get("catalyst_stars", 3.0))) or 3.0)
        four_master = float(setup.get("four_masters_score", 0.0) or 0.0)
        mcap = market_cap or float(setup.get("market_cap", 0.0) or 0.0)
        eps_growth = float(setup.get("eps_growth_pct", 0.0) or 0.0)
        rs_score = float(setup.get("relative_strength", 0.0) or 0.0)

        # Tier 1: Core Institutional Champion
        # High moat score, large cap ($20B+), top quality setup (>= 4.5 stars)
        if (four_master >= 80.0 or (stars >= 4.5 and mcap >= 20.0e9)) and mcap >= 10.0e9:
            return 1
        # Tier 2: High-Growth Tactical Leader
        # Strong EPS growth (>25%), strong RS (>80), or confirmed base breakout (>= 3.5 stars)
        elif stars >= 3.5 or eps_growth >= 25.0 or rs_score >= 80.0 or mcap >= 5.0e9:
            return 2
        # Tier 3: Tactical / Asymmetric / Turnaround
        else:
            return 3

    def calculate_order_plan(
        self,
        ticker: str,
        entry_price: float,
        stop_price: float,
        setup_type: str = "BASE_BREAKOUT",
        setup_quality_mult: float = 1.0,
        portfolio_data: Optional[Dict[str, Any]] = None,
        macro_data: Optional[Dict[str, Any]] = None,
        sector_flow_data: Optional[Dict[str, Any]] = None,
        custom_tier: Optional[int] = None,
        stock_sector: str = "General",
        stock_industry: str = "Diversified",
    ) -> Dict[str, Any]:
        """
        Calculate complete executable order plan using the 3-Way Minimum Formula:
          Final Shares = min(Shares_Risk, Shares_TierCap, Shares_AvailableCash)
        """
        t = str(ticker).upper().strip()
        entry_p = float(entry_price or 0.0)
        stop_p = float(stop_price or 0.0)

        if entry_p <= 0:
            return {"error": "Invalid entry price"}

        # If stop price is invalid or >= entry, set default 2.0x ATR or 5% stop
        if stop_p <= 0 or stop_p >= entry_p:
            stop_p = round(entry_p * 0.95, 2)

        risk_per_share = entry_p - stop_p
        stop_distance_pct = (risk_per_share / entry_p) * 100.0

        # 1. Load Live Portfolio NAV and SPAXX Cash
        if not portfolio_data:
            portfolio_data = portfolio_mgr.enrich_live_metrics()

        nav = float(portfolio_data.get("total_nav", 337000.0) or 337000.0)
        cash_balance = float(portfolio_data.get("cash_balance", 70000.0) or 70000.0)

        # 2. Determine Conviction Tier
        tier_level = custom_tier if custom_tier in [1, 2, 3] else self.classify_conviction_tier(t)
        tier_info = CONVICTION_TIERS.get(tier_level, CONVICTION_TIERS[2])
        tier_mult = tier_info["risk_multiplier"]
        tier_cap_pct = tier_info["max_position_cap_pct"]
        max_tier_dollars = nav * (tier_cap_pct / 100.0)

        # Existing position value for this asset
        existing_val = 0.0
        for pos in portfolio_data.get("positions", []):
            if str(pos.get("symbol", "")).upper().strip() == t or str(pos.get("underlying", "")).upper().strip() == t:
                existing_val += float(pos.get("current_value", 0.0) or 0.0)

        # 3. Macro Multiplier
        if not macro_data:
            try:
                from sources.macro_regime import macro_assessor
                macro_data = macro_assessor.assess_macro_regime()
            except Exception:
                macro_data = {}
        macro_mult = float(macro_data.get("composite_multiplier", 1.0) or 1.0)

        # Dynamic Cash Reserve Floor based on Macro Volatility
        vix_val = float(macro_data.get("vix", {}).get("value", 15.0) or 15.0)
        cash_floor_pct = 0.25 if vix_val > 22.0 else self.cash_reserve_floor_pct
        cash_floor_reserve = nav * cash_floor_pct
        unencumbered_cash = max(0.0, cash_balance - cash_floor_reserve)

        # 4. Sector Flow Multiplier & Auto-Tuned Setup Conviction Multiplier
        is_hot, flow_rationale, flow_mult = sector_flow_engine.is_stock_in_hot_sector(stock_sector, stock_industry)
        try:
            from sources.parameter_tuner import parameter_tuner
            calibrated_mult = parameter_tuner.get_calibrated_multiplier(setup_type)
            setup_quality_mult = setup_quality_mult * calibrated_mult
        except Exception:
            pass

        # 5. Compute the 3 Constraints
        # A. Risk Budget Shares
        total_dollar_risk_budget = nav * self.base_risk_pct * tier_mult * setup_quality_mult * flow_mult * macro_mult
        shares_risk = int(total_dollar_risk_budget / risk_per_share) if risk_per_share > 0 else 0

        # B. Tier Cap Shares
        remaining_tier_capacity = max(0.0, max_tier_dollars - existing_val)
        shares_tier_cap = int(remaining_tier_capacity / entry_p)

        # C. Available Cash Buffer Shares
        shares_available_cash = int(unencumbered_cash / entry_p)

        # 6. Final Order Allocation (3-Way Minimum)
        final_shares = max(0, min(shares_risk, shares_tier_cap, shares_available_cash))

        # Determine Binding Constraint
        if final_shares == 0:
            if remaining_tier_capacity <= 0:
                binding_reason = f"Position already at Tier {tier_level} Maximum Cap ({tier_cap_pct}% of NAV)"
            elif unencumbered_cash <= entry_p:
                binding_reason = f"Cash Balance at Reserve Floor ({cash_floor_pct*100:.0f}% preserved)"
            else:
                binding_reason = "Risk per share exceeds risk budget"
        elif final_shares == shares_tier_cap:
            binding_reason = f"Tier {tier_level} Concentration Cap ({tier_cap_pct}% of NAV)"
        elif final_shares == shares_available_cash:
            binding_reason = f"Available Cash Buffer (${unencumbered_cash:,.0f} unencumbered)"
        else:
            binding_reason = f"Risk Tolerance Budget (${total_dollar_risk_budget:,.2f} Max Risk)"

        order_dollar_val = round(final_shares * entry_p, 2)
        total_pos_dollar_after = round(existing_val + order_dollar_val, 2)
        total_pos_weight_pct = round((total_pos_dollar_after / nav) * 100.0, 2)
        actual_dollar_risk = round(final_shares * risk_per_share, 2)
        actual_risk_pct = round((actual_dollar_risk / nav) * 100.0, 2)

        # Target Price Levels
        target_1_r = round(entry_p + risk_per_share, 2)        # +1.0R (Breakeven ratchet)
        target_2_r = round(entry_p + (2.5 * risk_per_share), 2)  # +2.5R (Profit trim)

        return {
            "ticker": t,
            "entry_price": entry_p,
            "stop_price": stop_p,
            "risk_per_share": round(risk_per_share, 2),
            "stop_distance_pct": round(stop_distance_pct, 2),
            "tier_level": tier_level,
            "tier_name": tier_info["tier_name"],
            "tier_cap_pct": tier_cap_pct,
            "tier_mult": tier_mult,
            "setup_type": setup_type,
            "setup_mult": setup_quality_mult,
            "flow_mult": flow_mult,
            "flow_rationale": flow_rationale,
            "macro_mult": macro_mult,
            "portfolio_nav": nav,
            "cash_balance": cash_balance,
            "cash_floor_pct": cash_floor_pct,
            "unencumbered_cash": round(unencumbered_cash, 2),
            "shares_risk_calculated": shares_risk,
            "shares_tier_cap_allowed": shares_tier_cap,
            "shares_cash_available": shares_available_cash,
            "final_shares": final_shares,
            "binding_constraint": binding_reason,
            "order_dollar_value": order_dollar_val,
            "existing_position_value": existing_val,
            "total_position_dollar_after": total_pos_dollar_after,
            "total_position_weight_pct": total_pos_weight_pct,
            "actual_dollar_risk": actual_dollar_risk,
            "actual_risk_pct_of_nav": actual_risk_pct,
            "target_1_breakeven_lock": target_1_r,
            "target_2_profit_trim": target_2_r,
        }

    def audit_portfolio_allocations(self, portfolio_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Audit existing portfolio holdings against conviction tier caps and cash floors."""
        if not portfolio_data:
            portfolio_data = portfolio_mgr.enrich_live_metrics()

        nav = float(portfolio_data.get("total_nav", 337000.0) or 337000.0)
        positions = portfolio_data.get("positions", [])

        tier_aggregates = {1: 0.0, 2: 0.0, 3: 0.0}
        overweight_positions = []
        audited_positions = []

        for p in positions:
            sym = (p.get("symbol") or p.get("underlying", "")).upper().strip()
            cur_val = float(p.get("current_value", 0.0) or 0.0)
            weight = float(p.get("weight_pct", 0.0) or 0.0)
            pos_tier_val = p.get("conviction_tier")
            try:
                pos_tier_val = int(pos_tier_val) if pos_tier_val is not None else None
            except Exception:
                pos_tier_val = None
            tier = self.classify_conviction_tier(sym, manual_override_tier=pos_tier_val)
            tier_info = CONVICTION_TIERS.get(tier, CONVICTION_TIERS[2])
            cap = tier_info["max_position_cap_pct"]

            tier_aggregates[tier] += cur_val

            is_overweight = weight > (cap * 1.05)  # 5% buffer over cap
            excess_dollars = max(0.0, cur_val - (nav * cap / 100.0))
            trim_shares = int(excess_dollars / float(p.get("last_price", 1.0) or 1.0)) if is_overweight else 0

            item = {
                "symbol": sym,
                "tier": tier,
                "current_value": cur_val,
                "weight_pct": weight,
                "tier_cap_pct": cap,
                "status": "🔴 OVERWEIGHT" if is_overweight else "🟢 IN TIER",
                "excess_dollars": round(excess_dollars, 2),
                "recommended_trim_shares": trim_shares,
            }
            audited_positions.append(item)
            if is_overweight:
                overweight_positions.append(item)

        tier_1_pct = (tier_aggregates[1] / nav) * 100.0 if nav > 0 else 0.0
        tier_2_pct = (tier_aggregates[2] / nav) * 100.0 if nav > 0 else 0.0
        tier_3_pct = (tier_aggregates[3] / nav) * 100.0 if nav > 0 else 0.0

        return {
            "portfolio_nav": nav,
            "tier_1_weight_pct": round(tier_1_pct, 2),
            "tier_2_weight_pct": round(tier_2_pct, 2),
            "tier_3_weight_pct": round(tier_3_pct, 2),
            "tier_1_cap_pct": CONVICTION_TIERS[1]["aggregate_cap_pct"],
            "tier_2_cap_pct": CONVICTION_TIERS[2]["aggregate_cap_pct"],
            "overweight_positions": overweight_positions,
            "audited_positions": audited_positions,
        }


portfolio_optimizer = PortfolioOptimizer()
