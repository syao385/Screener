"""Stockbee Momentum & Minervini VCP Pattern Recognition Engine."""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger("pattern_detector")

ROUND_DOLLAR_LEVELS = [
    10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 60.0, 75.0, 100.0,
    125.0, 150.0, 175.0, 200.0, 250.0, 300.0, 400.0, 500.0, 750.0, 1000.0
]

class PatternDetector:
    """Classifies setups according to Stockbee and Minervini quantitative frameworks."""

    @staticmethod
    def evaluate_patterns(
        ticker: str,
        price: float,
        open_price: float,
        pct_change: float,
        gap_pct: float,
        pct_from_open: float,
        rvol: float,
        volume: float,
        avg_vol_30d: float,
        premarket_change: float,
        premarket_high: float,
        premarket_low: float,
        yesterday_high: float,
        yesterday_low: float,
        week_high: float,
        week_low: float,
        vwap_num: float,
        sma5_num: float,
        sma20_num: float,
        sma50_num: float,
        sma200_num: float,
        rsi_val: float,
        price_52w_high: float,
        price_52w_low: float,
        catalyst_stars: float,
        catalyst_type: str,
        is_positive_catalyst: bool,
        active_ep_record: Optional[Dict[str, Any]] = None,
        recent_bars: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates all Stockbee & Minervini setup criteria, returns primary setup classification,
        setup tags, exhaustion warnings, and setup score modifiers.
        """
        patterns_matched = []
        primary_pattern = "MOMENTUM_RUNNER"
        badge_label = "⚡ Momentum"
        preset_tags = ["ALL_SETUPS"]

        # -------------------------------------------------------------
        # 1. Exhaustion & Anti-Chase Evaluation
        # -------------------------------------------------------------
        is_exhausted = False
        exhaustion_flag = "CLEAN"
        exhaustion_desc = ""
        exhaustion_penalty = 0.0

        # Check extreme gaps
        if gap_pct >= 40.0:
            is_exhausted = True
            exhaustion_flag = "PARABOLIC_TRAP"
            exhaustion_desc = f"⚠️ Parabolic Gap (+{gap_pct:.1f}%) — High fade risk, wait for Day 2"
            exhaustion_penalty = 1.5
        elif gap_pct >= 22.0:
            is_exhausted = True
            exhaustion_flag = "OVEREXTENDED"
            exhaustion_desc = f"⚠️ Overextended Gap (+{gap_pct:.1f}%) — Trim 50% or wait for Day 2 VWAP"
            exhaustion_penalty = 0.75
        elif rsi_val > 78.0:
            is_exhausted = True
            exhaustion_flag = "OVERBOUGHT_RSI"
            exhaustion_desc = f"⚠️ Daily RSI Overbought ({rsi_val:.1f}) — Mean reversion risk"
            exhaustion_penalty = 0.5
        elif sma50_num > 0 and (price - sma50_num) / sma50_num > 0.35:
            is_exhausted = True
            exhaustion_flag = "EXTENDED_FROM_50SMA"
            dist_50 = ((price - sma50_num) / sma50_num) * 100.0
            exhaustion_desc = f"⚠️ Extended +{dist_50:.1f}% above 50-SMA — Wait for base"
            exhaustion_penalty = 0.5
        elif gap_pct >= 10.0 and rvol < 0.6:
            is_exhausted = True
            exhaustion_flag = "LOW_VOL_TRAP"
            exhaustion_desc = f"⚠️ Low-Volume Gap ({rvol:.2f}x RVOL) — High manipulation fade risk"
            exhaustion_penalty = 1.0

        if is_exhausted:
            preset_tags.append("EXTENDED_MOVERS")

        # -------------------------------------------------------------
        # 2. Episodic Pivot (EP) Lifecycle Engine (Day 1 vs Day 2+ vs Day 3+)
        # -------------------------------------------------------------
        is_ep_day1 = False
        is_ep_day2 = False
        is_ep_day3 = False

        # Fresh Day 1 EP: (Gap >= 7.0% OR Intraday Rally pct_from_open >= 4.0% OR pct_change >= 4.0%), RVOL >= 1.35x, Catalyst >= 3.0 stars (or verified earnings/FDA/M&A)
        has_ep_catalyst = (catalyst_stars >= 3.0 and is_positive_catalyst) or any(
            t in catalyst_type.lower() for t in ["earnings", "fda", "m&a", "contract", "buyout"]
        )
        has_ep_momentum = (gap_pct >= 7.0) or (pct_from_open >= 4.0) or (pct_change >= 4.0 and gap_pct >= 0.0)

        if has_ep_momentum and rvol >= 1.35 and has_ep_catalyst:
            is_ep_day1 = True
            patterns_matched.append("EP_DAY_1")
            preset_tags.append("EP_DAY_1")
            preset_tags.append("EP_5DAY_DB")

        # Check Active Multi-Day EP from SQLite State
        if active_ep_record:
            ep_day_count = active_ep_record.get("day_count", 1)
            preset_tags.append("EP_5DAY_DB")

            # Retain EP Day 1 during after-hours/post-market if registered today
            if ep_day_count == 1 and not is_ep_day1:
                is_ep_day1 = True
                patterns_matched.append("EP_DAY_1")
                preset_tags.append("EP_DAY_1")

            day1_vwap = float(active_ep_record.get("day1_vwap", 0.0) or 0.0)
            day1_low = float(active_ep_record.get("day1_low", 0.0) or 0.0)
            day1_high = float(active_ep_record.get("day1_high", 0.0) or 0.0)
            day1_vol = float(active_ep_record.get("day1_volume", 0.0) or avg_vol_30d)

            # Rule: Day 2 to Day 5 pullback to Day 1 VWAP or 5-SMA with Volume Dry-Up
            vwap_target = day1_vwap if day1_vwap > 0 else sma5_num
            dist_to_vwap = (abs(price - vwap_target) / vwap_target) if vwap_target > 0 else 1.0
            holds_low = (price >= day1_low * 0.985) if day1_low > 0 else True
            vol_dryup = (volume < (day1_vol * 0.85)) if (day1_vol > 0 and volume > 0) else True

            if 2 <= ep_day_count <= 5:
                # 1. VWAP or 5SMA touch/bounce on volume dry-up
                if dist_to_vwap <= 0.035 and holds_low and vol_dryup:
                    is_ep_day2 = True
                    patterns_matched.append("EP_DAY_2_VWAP")
                    preset_tags.append("EP_DAY_2")
                # 2. Secondary breakout above Day 1 High on volume
                elif day1_high > 0 and price >= (day1_high * 0.995) and rvol >= 1.20:
                    is_ep_day3 = True
                    patterns_matched.append("EP_DAY_3_BREAKOUT")
                    preset_tags.append("EP_DAY_2")

        # -------------------------------------------------------------
        # 3. Minervini Volatility Contraction Pattern (VCP) & Trend Template
        # -------------------------------------------------------------
        is_vcp = False
        vcp_points = 0
        vcp_reasons = []

        # 8-Point Trend Template check
        if sma50_num > 0 and price > sma50_num:
            vcp_points += 1
        if sma200_num > 0 and price > sma200_num:
            vcp_points += 1
        if sma50_num > 0 and sma200_num > 0 and sma50_num > sma200_num:
            vcp_points += 1

        # Within 25% of 52-week high
        high_ref = price_52w_high if price_52w_high > 0 else week_high
        if high_ref > 0 and price >= (high_ref * 0.75):
            vcp_points += 1

        # Above 52-week low by >= 30%
        low_ref = price_52w_low if price_52w_low > 0 else week_low
        if low_ref > 0 and price >= (low_ref * 1.30):
            vcp_points += 1

        # Stage 2 Moving Average alignment (SMA20 > SMA50)
        if sma20_num > 0 and sma50_num > 0 and sma20_num >= sma50_num:
            vcp_points += 1

        # Range contraction (5-day high vs low range < 12%)
        five_day_range_pct = 999.0
        if week_high > 0 and week_low > 0:
            five_day_range_pct = ((week_high - week_low) / week_low) * 100.0

        if five_day_range_pct <= 12.0:
            vcp_points += 1

        # Volume dry-up during base or expanding on breakout
        if rvol <= 1.15 or volume <= avg_vol_30d:
            vcp_points += 1

        # VCP Qualifies if Trend Template + Contraction (< 12% 5-day range) and breaking out above 5-day consolidation resistance (week_high) on heavy volume (RVOL >= 1.40x)
        is_breaking_pivot = (week_high > 0 and price >= week_high)
        if vcp_points >= 5 and five_day_range_pct <= 12.0 and is_breaking_pivot and rvol >= 1.40:
            is_vcp = True
            patterns_matched.append("MINERVINI_VCP")
            preset_tags.append("MINERVINI_VCP")

        # -------------------------------------------------------------
        # 4. Non-Earnings Momentum Bursts (4% Range Expansion OR Round-Dollar Breakout)
        # -------------------------------------------------------------
        # A. 4% Range Breakout: 5-day range <= 10%, price >= +4% on RVOL >= 1.5x
        is_4pct_burst = False
        if (five_day_range_pct <= 10.0 or pct_from_open >= 4.0) and pct_change >= 4.0 and rvol >= 1.50:
            is_4pct_burst = True
            patterns_matched.append("BURST_4PCT")

        # B. Dollar Breakout: Crossing key round levels on RVOL >= 1.5x
        is_dollar_breakout = False
        for lvl in ROUND_DOLLAR_LEVELS:
            if abs(price - lvl) / lvl <= 0.015 and price >= lvl and (yesterday_high < lvl or open_price < lvl) and rvol >= 1.50:
                is_dollar_breakout = True
                patterns_matched.append("DOLLAR_BREAKOUT")
                break

        # Merged Momentum Burst
        is_momentum_burst = is_4pct_burst or is_dollar_breakout
        if is_momentum_burst:
            patterns_matched.append("MOMENTUM_BURST")
            preset_tags.append("MOMENTUM_BURST")

        # C. Pre-Market V-Reversal: Morning dip <= -1.8%, reversing >= +1.5% with RVOL >= 1.25x
        is_v_reversal = False
        if premarket_low > 0 and premarket_change <= -1.8 and pct_change >= 1.5 and rvol >= 1.25:
            is_v_reversal = True
            patterns_matched.append("V_REVERSAL")
            preset_tags.append("V_REVERSAL")

        # -------------------------------------------------------------
        # 5. Resolve Primary Pattern & UI Badge
        # -------------------------------------------------------------
        if is_ep_day1:
            primary_pattern = "EP_DAY_1"
            badge_label = "🔥 EP Day 1"
        elif is_ep_day2:
            primary_pattern = "EP_DAY_2_VWAP"
            badge_label = "🎯 EP Day 2 VWAP"
        elif is_ep_day3:
            primary_pattern = "EP_DAY_3_BREAKOUT"
            badge_label = "🚀 EP Day 3 Breakout"
        elif is_vcp:
            primary_pattern = "MINERVINI_VCP"
            badge_label = "📉 Minervini VCP"
        elif is_momentum_burst:
            primary_pattern = "MOMENTUM_BURST"
            badge_label = "⚡ Momentum Burst"
        elif is_v_reversal:
            primary_pattern = "V_REVERSAL"
            badge_label = "🔄 V-Reversal"
        elif pct_change >= 3.0 and rvol >= 1.5:
            primary_pattern = "MOMENTUM_BREAKOUT"
            badge_label = "📈 Momentum"
        else:
            primary_pattern = "TECHNICAL_SETUP"
            badge_label = "📊 Setup"

        # Stockbee Score calculation (1.0 - 10.0 scale)
        stockbee_score = 5.0
        if is_ep_day1:
            stockbee_score += 3.0
        if is_ep_day2:
            stockbee_score += 2.5
        if is_vcp:
            stockbee_score += 2.0
        if is_4pct_burst or is_dollar_breakout:
            stockbee_score += 1.5
        if rvol >= 2.5:
            stockbee_score += 1.0
        if catalyst_stars >= 4.0:
            stockbee_score += 1.0

        if is_exhausted:
            stockbee_score = max(3.0, stockbee_score - (exhaustion_penalty * 2.0))

        stockbee_score = min(10.0, max(1.0, round(stockbee_score, 1)))

        return {
            "primary_pattern": primary_pattern,
            "badge_label": badge_label,
            "patterns_matched": patterns_matched,
            "preset_tags": preset_tags,
            "is_exhausted": is_exhausted,
            "exhaustion_flag": exhaustion_flag,
            "exhaustion_desc": exhaustion_desc,
            "exhaustion_penalty": exhaustion_penalty,
            "is_ep_day1": is_ep_day1,
            "is_ep_day2": is_ep_day2,
            "is_vcp": is_vcp,
            "is_4pct_burst": is_4pct_burst,
            "is_dollar_breakout": is_dollar_breakout,
            "is_v_reversal": is_v_reversal,
            "stockbee_score": stockbee_score,
            "five_day_range_pct": round(five_day_range_pct, 1) if five_day_range_pct < 900 else 0.0,
            "vcp_points": vcp_points,
        }

pattern_detector = PatternDetector()
