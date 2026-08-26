"""Setup Scorer: Computes Institutional 1★ to 5★ Setup Score based on Catalyst, RVOL, Technicals, Gamma, Macro, and Stockbee/Minervini Patterns."""

from typing import Dict, Any, Optional

class SetupScorer:
    """Calculates statistical setup quality index from 1.0 to 5.0 stars with Gamma Gating and Exhaustion penalties."""

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
        pattern_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        score = 0.0

        # 1. Catalyst component (up to 1.5 stars)
        score += min(1.5, max(0.0, (catalyst_stars / 5.0) * 1.5))

        # 2. RVOL component (up to 1.0 stars)
        if rvol >= 3.0:
            score += 1.0
        elif rvol >= 2.0:
            score += 0.75
        elif rvol >= 1.5:
            score += 0.5
        else:
            score += 0.2

        # 3. Technical Breakout component (up to 1.0 stars)
        tech_pts = 0.0
        if yesterday_high > 0 and price > yesterday_high:
            tech_pts += 0.4
        if premarket_high > 0 and price >= premarket_high:
            tech_pts += 0.3
        if gap_pct >= 8.0:
            tech_pts += 0.3
        elif gap_pct >= 4.0:
            tech_pts += 0.2
        elif gap_pct >= 3.0:
            tech_pts += 0.1
        score += min(1.0, tech_pts)

        # 4. Options Gamma Structure & Conviction (up to 0.75 stars)
        gamma_pts = 0.0
        has_bullish_gamma = False
        if "Bullish" in str(gamma_skew):
            gamma_pts += 0.4
            has_bullish_gamma = True
        elif "Neutral" in str(gamma_skew):
            gamma_pts += 0.2

        cw_above_price = False
        try:
            cw_clean = str(call_wall).split("(")[0].replace("$", "").replace(",", "").strip()
            cw_num = float(cw_clean)
            if cw_num > price:
                gamma_pts += 0.2
                cw_above_price = True
        except Exception:
            pass

        try:
            pc_num = float(str(pc_ratio).strip())
            if pc_num < 0.7:
                gamma_pts += 0.15
        except Exception:
            pass
        score += min(0.75, gamma_pts)

        # 5. Macro Regime (up to 0.75 stars)
        if "Risk-On" in str(macro_regime):
            score += 0.75
        elif "Risk-Off" in str(macro_regime):
            score += 0.15
        else:
            score += 0.45

        # 6. Pattern Quality Modifier (Stockbee & Minervini)
        if pattern_info:
            prim_pattern = pattern_info.get("primary_pattern", "")
            if prim_pattern in ("EP_DAY_1", "EP_DAY_2_VWAP"):
                score += 0.5
            elif prim_pattern in ("MINERVINI_VCP", "BURST_4PCT", "DOLLAR_BREAKOUT"):
                score += 0.3

            # Apply quantitative exhaustion penalty
            if pattern_info.get("is_exhausted"):
                pen = pattern_info.get("exhaustion_penalty", 0.5)
                score -= pen

        # Clamp between 1.0 and 5.0
        final_score = round(max(1.0, min(5.0, score)), 1)
        num_stars = int(round(final_score))
        stars_visual = "★" * num_stars + "☆" * (5 - num_stars)

        return {
            "score": final_score,
            "stars_visual": stars_visual,
            "display_str": f"{stars_visual} {final_score:.1f}★",
            "has_bullish_gamma": has_bullish_gamma,
            "cw_above_price": cw_above_price,
        }

    @staticmethod
    def calculate_position_size(
        portfolio_nav: float,
        risk_pct: float,
        price: float,
        stop_loss: float,
        macro_multiplier: float = 0.95,
        flow_factor: float = 1.00,
        max_alloc_pct: float = 10.0,
        pattern_multiplier: float = 1.00,
        has_gamma_alignment: bool = True,
        is_exhausted: bool = False
    ) -> Dict[str, Any]:
        """
        Computes Championship ATR-Parity position sizing in exact shares and dollars,
        gated by Options Gamma alignment and Exhaustion limits.
        """
        if price <= 0 or portfolio_nav <= 0:
            return {"shares": 0, "capital_required": 0.0, "risk_dollar": 0.0}

        # Dollar risk budget
        risk_budget_dollar = portfolio_nav * (risk_pct / 100.0)

        # Stop loss distance (minimum 1.5% to avoid division by near-zero)
        raw_stop_dist = abs(price - stop_loss) if stop_loss > 0 else (price * 0.04)
        stop_dist_dollar = max(price * 0.015, raw_stop_dist)
        stop_dist_pct = (stop_dist_dollar / price) * 100.0

        # Base shares from risk budget
        base_shares = risk_budget_dollar / stop_dist_dollar

        # Effective multiplier combining Macro, Options Flow, Pattern Quality, and Gamma Gating
        combined_mult = macro_multiplier * flow_factor * pattern_multiplier

        # Gamma Gating: If Gamma is NOT aligned (e.g. trading straight into Put Wall or Bearish Skew),
        # cap maximum multiplier to 1.0x (cannot receive 1.25x-1.50x super-size)
        if not has_gamma_alignment and combined_mult > 1.0:
            combined_mult = 1.00

        # Exhaustion restriction: cut position size by 50% if setup is flagged as extended/exhausted
        if is_exhausted:
            combined_mult *= 0.50

        effective_mult = max(0.35, min(1.40, combined_mult))
        scaled_shares = int(base_shares * effective_mult)

        # Cap by maximum position allocation (e.g. 10% NAV)
        max_capital = portfolio_nav * (max_alloc_pct / 100.0)
        max_shares = int(max_capital / price)
        final_shares = max(1, min(scaled_shares, max_shares)) if scaled_shares > 0 else 0

        capital_required = round(final_shares * price, 2)
        actual_risk_dollar = round(final_shares * stop_dist_dollar, 2)
        weight_pct = round((capital_required / portfolio_nav * 100.0), 2)

        return {
            "shares": final_shares,
            "capital_required": capital_required,
            "capital_required_str": f"${capital_required:,.2f}",
            "risk_dollar": actual_risk_dollar,
            "risk_dollar_str": f"${actual_risk_dollar:,.2f}",
            "stop_loss": round(stop_loss, 2) if stop_loss > 0 else round(price * 0.96, 2),
            "stop_dist_pct": round(stop_dist_pct, 2),
            "weight_pct": weight_pct,
            "macro_multiplier": macro_multiplier,
            "flow_factor": flow_factor,
            "pattern_multiplier": pattern_multiplier,
            "effective_mult": round(effective_mult, 2),
        }

setup_scorer = SetupScorer()
