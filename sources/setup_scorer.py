"""Setup Scorer 2.0: Bespoke 1? to 5? Institutional Scoring with 5 Archetype Quant Engines."""

from typing import Dict, Any, Optional

class SetupScorer:
    """
    Calculates bespoke setup quality index from 1.0 to 5.0 stars across 5 dedicated quant engines:
    1. Base & Contraction Engine (HTF, Cup & Handle, VCP, Base-on-Base)
    2. Catalyst & Momentum Shock Engine (EP 1-3)
    3. Trend Pullback Engine (Stage 2 Pullback, PEAD, EP2 VWAP)
    4. Market Structure & Intraday Velocity Engine (Structure BOS, Stockbeep 5m Spike, ORB)
    5. Climax Reversal Engine (Selling Climax Bottom, Buying Climax Top)
    """

    @staticmethod
    def calculate_score(
        catalyst_stars: float,
        rvol: float,
        gap_pct: float,
        price: float,
        yesterday_high: float,
        premarket_high: float,
        gamma_skew: str,
        call_wall: Any,
        pc_ratio: Any,
        macro_regime: str = "Neutral",
        pattern_info: Optional[Dict[str, Any]] = None,
        sentiment_score: Optional[float] = None,
        signal_score: Optional[float] = None,
        source_authority: Optional[float] = None,
    ) -> Dict[str, Any]:
        if not pattern_info:
            pattern_info = {}

        # Extract or default News Pulse / Sentiment components
        if sentiment_score is None:
            sentiment_score = float(pattern_info.get("sentiment_score", 0.5))
        if signal_score is None:
            signal_score = float(pattern_info.get("signal_score", 65.0))
        if source_authority is None:
            source_authority = float(pattern_info.get("source_authority", 70.0))

        # Blended institutional catalyst rating (1.0 - 5.0):
        # 50% Pattern Stars + 30% (Signal Score / 20) + 20% Directional Sentiment (0-5)
        sent_dir_pts = (max(-1.0, min(1.0, sentiment_score)) + 1.0) * 2.5
        blended_cat_rating = (
            0.50 * float(catalyst_stars) +
            0.30 * (float(signal_score) / 20.0) +
            0.20 * sent_dir_pts
        )
        effective_cat_stars = max(1.0, min(5.0, blended_cat_rating))

        prim_pattern = pattern_info.get("primary_pattern", "TECHNICAL_SETUP")
        archetype = pattern_info.get("archetype", "ARCHETYPE_E")
        checklist = pattern_info.get("criteria_checklist", {})
        trade_plan = pattern_info.get("trade_plan", {})
        is_exhausted = pattern_info.get("is_exhausted", False)
        exhaustion_penalty = pattern_info.get("exhaustion_penalty", 0.0)

        # Options Gamma Common Points (up to +0.75★)
        gamma_pts = 0.0
        has_bullish_gamma = False
        if "Bullish" in str(gamma_skew):
            gamma_pts += 0.40
            has_bullish_gamma = True
        elif "Neutral" in str(gamma_skew):

            gamma_pts += 0.20

        cw_above_price = False
        try:
            cw_clean = str(call_wall).split("(")[0].replace("$", "").replace(",", "").strip()
            cw_num = float(cw_clean)
            if cw_num > price:
                gamma_pts += 0.20
                cw_above_price = True
        except Exception:
            pass

        try:
            pc_num = float(str(pc_ratio).strip())
            if pc_num < 0.70:
                gamma_pts += 0.15
        except Exception:
            pass
        gamma_pts = min(0.75, gamma_pts)

        # 4D Macro Regime Common Points (up to +0.75?)
        macro_pts = 0.45
        if "Risk-On" in str(macro_regime):
            macro_pts = 0.75
        elif "Risk-Off" in str(macro_regime):
            macro_pts = 0.15

        # -------------------------------------------------------------
        # 1. Dispatch to Bespoke Archetype Scoring Engines
        # -------------------------------------------------------------
        base_points = 0.0
        vol_points = 0.0
        trend_points = 0.0
        catalyst_pts = 0.0

        if archetype == "ARCHETYPE_A":
            # Archetype A: Base & Contraction (VCP, Cup & Handle, Base-on-Base)
            # Evaluates Base Geometry, Stage 2 Trend, Volume Dry-Up (Low RVOL is positive!), Runway
            trend_points += 1.00 if checklist.get("stage2_trend") else 0.40
            if checklist.get("ma_ribbon"):
                trend_points += 0.25

            # Base Geometry (5-day range tightness)
            rng = checklist.get("five_day_range_pct", 15.0)
            if rng <= 6.5:
                base_points += 1.25
            elif rng <= 10.0:
                base_points += 1.00
            elif rng <= 14.0:
                base_points += 0.75
            else:
                base_points += 0.40

            # Volume Dry-Up Scoring (Low RVOL is scored positively!)
            if rvol <= 0.85:
                vol_points += 0.85
            elif rvol <= 1.15:
                vol_points += 0.65
            elif rvol >= 1.40 and (price >= yesterday_high or price >= premarket_high):
                vol_points += 0.85  # Breakout volume expansion
            else:
                vol_points += 0.35

            # Overhead Runway to 52w high
            dist_52w = checklist.get("dist_to_52w_high_pct", 20.0)
            if dist_52w <= 8.0:
                base_points += 0.50
            elif dist_52w <= 15.0:
                base_points += 0.35

            catalyst_pts = min(0.50, (effective_cat_stars / 5.0) * 0.50)

        elif archetype == "ARCHETYPE_B":
            # Archetype B: Momentum & Catalyst Shocks (EP Day 1, EP Day 3, High Tight Flag)
            # Evaluates Tier-1 Catalyst surprise, RVOL Surge, Prior Runup, Gap Retention
            if prim_pattern == "HIGH_TIGHT_FLAG":
                base_points += 1.40
                trend_points += 1.00 if checklist.get("stage2_trend") else 0.50
                vol_points += 0.85 if rvol >= 1.50 else 0.50
                catalyst_pts = min(0.60, (effective_cat_stars / 5.0) * 0.60)
            else:  # EP Day 1 / Day 3
                cat_mult = 1.20 if checklist.get("has_catalyst") else 0.60
                catalyst_pts = min(1.35, (effective_cat_stars / 5.0) * 1.35 * cat_mult)
                
                # RVOL Surge (Massive institutional commitment)
                if rvol >= 3.0:
                    vol_points += 1.00
                elif rvol >= 2.0:
                    vol_points += 0.80
                elif rvol >= 1.35:
                    vol_points += 0.60
                else:
                    vol_points += 0.25

                # Price Retention (Holding above open & VWAP)
                if checklist.get("is_above_vwap") and checklist.get("close_location_pct", 0) >= 60.0:
                    trend_points += 0.90
                else:
                    trend_points += 0.40
                base_points += 0.50

        elif archetype == "ARCHETYPE_C":
            # Archetype C: Trend Pullbacks (Stage 2 Pullback, EP Day 2 VWAP, PEAD)
            # Evaluates Trend Ribbon, Orderly Volume Decline (< 75% avg), MA/VWAP support hold
            trend_points += 1.10 if checklist.get("stage2_trend") and checklist.get("ma_ribbon") else 0.60
            
            # Support hold
            if checklist.get("is_above_vwap"):
                trend_points += 0.40

            # Orderly Volume Contraction (Low RVOL is positive!)
            if rvol <= 0.80:
                vol_points += 0.95
            elif rvol <= 1.10:
                vol_points += 0.70
            else:
                vol_points += 0.35

            base_points += 0.80
            catalyst_pts = min(0.60, (effective_cat_stars / 5.0) * 0.60)

        elif archetype == "ARCHETYPE_D":
            # Archetype D: Market Structure BOS (Breakup & Breakdown)
            # Evaluates Clarity of Swing Break, Breakout Volume, Distance to Liquidity
            base_points += 1.00
            trend_points += 0.80
            if rvol >= 2.0:
                vol_points += 0.90
            elif rvol >= 1.35:
                vol_points += 0.70
            else:
                vol_points += 0.30
            catalyst_pts = min(0.50, (effective_cat_stars / 5.0) * 0.50)

        elif archetype == "ARCHETYPE_G":
            # Archetype G: Climax Reversals (Selling Climax Bottom & Buying Climax Top)
            # Evaluates Statistical Overextension, Climax RVOL Absorption (>= 2.0x), Hammer/Pin Bar
            base_points += 1.20
            # Climax RVOL Absorption
            if rvol >= 3.0:
                vol_points += 1.10
            elif rvol >= 2.0:
                vol_points += 0.85
            else:
                vol_points += 0.50

            # Reversal Price Action & VWAP Reclaim
            if prim_pattern == "SELLING_CLIMAX_BOTTOM":
                if checklist.get("is_above_vwap") and checklist.get("close_location_pct", 0) >= 60.0:
                    trend_points += 1.10
                else:
                    trend_points += 0.50
            else:  # Buying Climax Top
                if not checklist.get("is_above_vwap") and checklist.get("close_location_pct", 100) <= 40.0:
                    trend_points += 1.10
                else:
                    trend_points += 0.50

            catalyst_pts = min(0.30, (effective_cat_stars / 5.0) * 0.30)

        else:
            # Archetype E: Intraday Velocity & ORB / Momentum Runner
            if rvol >= 2.5:
                vol_points += 0.90
            elif rvol >= 1.5:
                vol_points += 0.60
            else:
                vol_points += 0.30

            if yesterday_high > 0 and price > yesterday_high:
                trend_points += 0.40
            if premarket_high > 0 and price >= premarket_high:
                trend_points += 0.30
            if gap_pct >= 4.0:
                trend_points += 0.30
            base_points += 0.70
            catalyst_pts = min(0.60, (effective_cat_stars / 5.0) * 0.60)


        # -------------------------------------------------------------
        # 2. Composite Score Summation & Deductions
        # -------------------------------------------------------------
        raw_score = base_points + vol_points + trend_points + catalyst_pts + gamma_pts + macro_pts

        # Apply Quantitative Exhaustion Penalty
        if is_exhausted:
            raw_score -= exhaustion_penalty

        # Clamp between 1.0 and 5.0
        final_score = round(max(1.0, min(5.0, raw_score)), 1)
        num_stars = int(round(final_score))
        stars_visual = "&#9733;" * num_stars + "&#9734;" * (5 - num_stars)

        score_breakdown = {
            "base_points": round(base_points, 2),
            "vol_points": round(vol_points, 2),
            "trend_points": round(trend_points, 2),
            "catalyst_points": round(catalyst_pts, 2),
            "gamma_points": round(gamma_pts, 2),
            "macro_points": round(macro_pts, 2),
            "exhaustion_penalty": round(exhaustion_penalty, 2) if is_exhausted else 0.0,
            "blended_catalyst_rating": round(effective_cat_stars, 2),
            "sentiment_score": round(float(sentiment_score), 2),
            "signal_score": round(float(signal_score), 1),
            "scoring_archetype": archetype,
            "final_score": final_score
        }

        return {
            "score": final_score,
            "stars_visual": stars_visual,
            "display_str": f"{stars_visual} {final_score:.1f}&#9733;",
            "has_bullish_gamma": has_bullish_gamma,
            "cw_above_price": cw_above_price,
            "score_breakdown": score_breakdown,
            "trade_plan": trade_plan,
            "criteria_checklist": checklist
        }

    @staticmethod
    def calculate_position_size(
        portfolio_nav: float,
        price: float,
        stop_loss: float,
        available_cash: float = 0.0,
        target_cash_allocation: float = 0.0,
        risk_pct: float = 0.75,
        max_alloc_pct: float = 10.0,
        macro_multiplier: float = 0.95,
        flow_factor: float = 1.00,
        pattern_multiplier: float = 1.00,
        has_gamma_alignment: bool = True,
        is_exhausted: bool = False
    ) -> Dict[str, Any]:
        """
        Computes Practical Position Sizing for New Buy Setups:
        Allocation = min(ATR-based Risk Capital, (Total Available Cash - Target Cash Allocation) * 10%, Max NAV Cap).
        """
        if price <= 0 or portfolio_nav <= 0:
            return {"shares": 0, "capital_required": 0.0, "risk_dollar": 0.0, "display_str": "0 shs ($0)"}

        # 1. Available Free Cash Sizing Limit
        target_cash_buffer = target_cash_allocation if target_cash_allocation > 0 else (portfolio_nav * 0.10)
        free_cash = max(0.0, available_cash - target_cash_buffer) if available_cash > 0 else 0.0
        cash_alloc_cap = free_cash * 0.10  # 10% of free cash above target reserve buffer

        # 2. ATR Risk Based Sizing
        risk_budget_dollar = portfolio_nav * (risk_pct / 100.0)
        raw_stop_dist = abs(price - stop_loss) if stop_loss > 0 else (price * 0.04)
        stop_dist_dollar = max(price * 0.015, raw_stop_dist)
        stop_dist_pct = (stop_dist_dollar / price) * 100.0

        base_shares = risk_budget_dollar / stop_dist_dollar
        combined_mult = macro_multiplier * flow_factor * pattern_multiplier

        if not has_gamma_alignment and combined_mult > 1.0:
            combined_mult = 1.00

        if is_exhausted:
            combined_mult *= 0.50

        effective_mult = max(0.35, min(1.45, combined_mult))
        atr_shares = int(base_shares * effective_mult)
        atr_capital = atr_shares * price

        # 3. Maximum NAV Allocation Cap (e.g. 10% of NAV)
        nav_max_capital = portfolio_nav * (max_alloc_pct / 100.0)

        # 4. Practical Allocation Selection
        if available_cash > 0:
            if free_cash <= 0:
                final_shares = 0
                final_capital = 0.0
                sizing_desc = "⚠️ Cash Buffer Limit (0 Free Cash)"
            else:
                practical_capital = min(atr_capital, cash_alloc_cap, nav_max_capital)
                final_shares = int(practical_capital / price)
                final_capital = round(final_shares * price, 2)
                sizing_desc = "Cash-Gated (10% Free Cash)" if cash_alloc_cap < atr_capital else "ATR Risk Parity"
        else:
            practical_capital = min(atr_capital, nav_max_capital)
            final_shares = max(1, int(practical_capital / price)) if practical_capital >= price else 0
            final_capital = round(final_shares * price, 2)
            sizing_desc = "ATR Risk Parity"

        actual_risk_dollar = round(final_shares * stop_dist_dollar, 2)
        weight_pct = round((final_capital / portfolio_nav * 100.0), 2) if portfolio_nav > 0 else 0.0

        formula_breakdown = f"Base: {int(base_shares):,} shs × Regime ({macro_multiplier:.2f}x) × Flow ({flow_factor:.2f}x) = {final_shares:,} shs (${final_capital:,.0f} | ${actual_risk_dollar:,.0f} Risk)"

        return {
            "base_shares": int(base_shares),
            "shares": final_shares,
            "capital_required": final_capital,
            "capital_required_str": f"${final_capital:,.0f}",
            "risk_dollar": actual_risk_dollar,
            "risk_dollar_str": f"${actual_risk_dollar:,.2f}",
            "stop_loss": round(stop_loss, 2) if stop_loss > 0 else round(price * 0.96, 2),
            "stop_dist_pct": round(stop_dist_pct, 2),
            "weight_pct": weight_pct,
            "free_cash": round(free_cash, 2),
            "cash_alloc_cap": round(cash_alloc_cap, 2),
            "sizing_desc": sizing_desc,
            "display_str": f"{final_shares:,} shs (${final_capital:,.0f})" if final_shares > 0 else f"0 shs ($0) - {sizing_desc}",
            "formula_breakdown": formula_breakdown,
            "macro_multiplier": macro_multiplier,
            "flow_factor": flow_factor,
            "pattern_multiplier": pattern_multiplier,
            "effective_mult": round(effective_mult, 2),
        }

setup_scorer = SetupScorer()
