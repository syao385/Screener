"""Institutional & Championship Pattern Recognition Engine 2.0 (9 Master Setups)."""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger("pattern_detector")

ROUND_DOLLAR_LEVELS = [
    10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 60.0, 75.0, 100.0,
    125.0, 150.0, 175.0, 200.0, 250.0, 300.0, 400.0, 500.0, 750.0, 1000.0
]

class PatternDetector:
    """
    Classifies market setups across 9 Consolidated Master Institutional Archetypes:
    1. High Tight Flag (HTF)
    2. Base Breakout (Cup & Handle / Base-on-Base)
    3. Minervini VCP (Breakout & Anticipation / Cheat)
    4. Episodic Pivot Lifecycle (Day 1, Day 2 VWAP, Day 3 Breakout)
    5. Stage 2 Pullback & Continuation (10EMA/20SMA/PEAD)
    6. Market Structure BOS (Breakup & Breakdown)
    7. Intraday Velocity & ORB (Stockbeep 5m Spike, ORB, VWAP Reclaim)
    8. Climax Reversals (Selling Climax Bottom & Buying Climax Top)
    9. Whale Options Flow & Gamma Magnet
    """

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
        intraday_high: float = 0.0,
        intraday_low: float = 0.0,
    ) -> Dict[str, Any]:
        patterns_matched = []
        preset_tags = ["ALL_SETUPS"]
        
        cur_high = max(price, yesterday_high, week_high, intraday_high)
        cur_low = min(filter(lambda x: x > 0, [price, yesterday_low, week_low, intraday_low])) if any([price, yesterday_low, week_low, intraday_low]) else price * 0.95
        
        # 0. Exhaustion & Anti-Chase Evaluation
        is_exhausted = False
        exhaustion_flag = "CLEAN"
        exhaustion_desc = ""
        exhaustion_penalty = 0.0

        if gap_pct >= 40.0:
            is_exhausted = True
            exhaustion_flag = "PARABOLIC_TRAP"
            exhaustion_desc = f"Parabolic Gap (+{gap_pct:.1f}%) - High fade risk, wait for Day 2"
            exhaustion_penalty = 1.5
        elif gap_pct >= 22.0:
            is_exhausted = True
            exhaustion_flag = "OVEREXTENDED"
            exhaustion_desc = f"Overextended Gap (+{gap_pct:.1f}%) - Trim 50% or wait for Day 2 VWAP"
            exhaustion_penalty = 0.75
        elif rsi_val > 80.0:
            is_exhausted = True
            exhaustion_flag = "OVERBOUGHT_RSI"
            exhaustion_desc = f"Daily RSI Overbought ({rsi_val:.1f}) - Mean reversion risk"
            exhaustion_penalty = 0.5
        elif sma50_num > 0 and (price - sma50_num) / sma50_num > 0.35:
            is_exhausted = True
            exhaustion_flag = "EXTENDED_FROM_50SMA"
            dist_50 = ((price - sma50_num) / sma50_num) * 100.0
            exhaustion_desc = f"Extended +{dist_50:.1f}% above 50-SMA - Wait for base"
            exhaustion_penalty = 0.5
        elif gap_pct >= 10.0 and rvol < 0.6:
            is_exhausted = True
            exhaustion_flag = "LOW_VOL_TRAP"
            exhaustion_desc = f"Low-Volume Gap ({rvol:.2f}x RVOL) - High manipulation fade risk"
            exhaustion_penalty = 1.0

        if is_exhausted:
            preset_tags.append("EXTENDED_MOVERS")

        stage2_trend = bool(sma50_num > 0 and sma200_num > 0 and price > sma50_num and sma50_num > sma200_num)
        ma_ribbon = bool(sma20_num > 0 and sma50_num > 0 and price >= sma20_num and sma20_num >= sma50_num)
        
        five_day_range_pct = 999.0
        if week_high > 0 and week_low > 0:
            five_day_range_pct = ((week_high - week_low) / week_low) * 100.0

        dist_to_52w_high_pct = 0.0
        if price_52w_high > 0:
            dist_to_52w_high_pct = ((price_52w_high - price) / price) * 100.0

        dist_from_52w_low_pct = 0.0
        if price_52w_low > 0:
            dist_from_52w_low_pct = ((price - price_52w_low) / price_52w_low) * 100.0

        is_above_vwap = bool(vwap_num > 0 and price >= vwap_num)
        dist_to_vwap_pct = ((price - vwap_num) / vwap_num * 100.0) if vwap_num > 0 else 0.0

        day_range = max(0.01, cur_high - cur_low)
        close_location_pct = ((price - cur_low) / day_range) * 100.0

        # Pattern 1: High Tight Flag (HTF) - Arch B
        is_htf = False
        if dist_from_52w_low_pct >= 75.0 and five_day_range_pct <= 22.0 and dist_to_52w_high_pct <= 12.0 and stage2_trend:
            if price >= (week_high * 0.99) and (rvol >= 1.35 or volume >= avg_vol_30d):
                is_htf = True
                patterns_matched.append("HIGH_TIGHT_FLAG")
                preset_tags.append("HIGH_TIGHT_FLAG")

        # Pattern 2: Base Breakout (C&H / Base-on-Base) - Arch A
        is_base_breakout = False
        is_cup_and_handle = False
        is_base_on_base = False
        if stage2_trend and dist_from_52w_low_pct >= 30.0 and dist_to_52w_high_pct <= 18.0:
            if five_day_range_pct <= 14.0 and price >= (week_high * 0.995) and rvol >= 1.30:
                is_base_breakout = True
                is_cup_and_handle = True
                patterns_matched.append("BASE_BREAKOUT")
                preset_tags.append("BASE_BREAKOUT")
            elif five_day_range_pct <= 10.0 and sma20_num > 0 and (price - sma20_num) / sma20_num <= 0.06 and rvol >= 1.25 and price >= yesterday_high:
                is_base_breakout = True
                is_base_on_base = True
                patterns_matched.append("BASE_BREAKOUT")
                preset_tags.append("BASE_BREAKOUT")

        # Pattern 3: Minervini VCP (Breakout & Cheat) - Arch A
        is_vcp = False
        is_vcp_breakout = False
        is_vcp_cheat = False
        vcp_points = 0
        if sma50_num > 0 and price > sma50_num: vcp_points += 1
        if sma200_num > 0 and price > sma200_num: vcp_points += 1
        if sma50_num > 0 and sma200_num > 0 and sma50_num > sma200_num: vcp_points += 1
        if dist_to_52w_high_pct <= 25.0: vcp_points += 1
        if dist_from_52w_low_pct >= 30.0: vcp_points += 1
        if sma20_num > 0 and sma50_num > 0 and sma20_num >= sma50_num: vcp_points += 1
        if five_day_range_pct <= 12.0: vcp_points += 1
        if rvol <= 1.15 or volume <= avg_vol_30d: vcp_points += 1

        if vcp_points >= 5 and five_day_range_pct <= 12.0 and price >= week_high and rvol >= 1.35:
            is_vcp = True
            is_vcp_breakout = True
            patterns_matched.append("MINERVINI_VCP")
            preset_tags.append("MINERVINI_VCP")
        elif vcp_points >= 5 and five_day_range_pct <= 6.5 and rvol <= 1.05 and price >= sma20_num and week_high > 0 and abs(price - week_high) / week_high <= 0.04:
            is_vcp = True
            is_vcp_cheat = True
            patterns_matched.append("MINERVINI_VCP")
            patterns_matched.append("VCP_CHEAT")
            preset_tags.append("MINERVINI_VCP")

        # Pattern 4: Episodic Pivot (EP 1-5 Lifecycle) - Arch B/C
        # Strict EP Rule: Must be a BULLISH catalyst shock (Gap >= +5% or Surge >= +4%, pct_change > 0, RVOL >= 1.35x)
        is_ep_day1 = False
        is_ep_day2 = False
        is_ep_day3 = False
        has_ep_catalyst = (catalyst_stars >= 3.0 and is_positive_catalyst) or any(
            t in catalyst_type.lower() for t in ["earnings", "fda", "m&a", "contract", "buyout", "guidance"]
        )
        is_bullish_momentum = (pct_change > 0) and ((gap_pct >= 5.0) or (pct_from_open >= 4.0) or (pct_change >= 4.0 and gap_pct >= 0.0))

        if active_ep_record:
            day1_gap = float(active_ep_record.get("day1_gap_pct", 0.0) or 0.0)
            ep_day_count = active_ep_record.get("day_count", 1)
            
            # An EP record is only valid if Day 1 was a positive shock
            if day1_gap >= 0:
                preset_tags.append("EP_5DAY_DB")
                if ep_day_count == 1:
                    if is_bullish_momentum and rvol >= 1.35 and has_ep_catalyst:
                        is_ep_day1 = True
                        patterns_matched.append("EP_DAY_1")
                        preset_tags.append("EP_DAY_1")
                elif 2 <= ep_day_count <= 5:
                    day1_vwap = float(active_ep_record.get("day1_vwap", 0.0) or 0.0)
                    day1_low = float(active_ep_record.get("day1_low", 0.0) or 0.0)
                    day1_high = float(active_ep_record.get("day1_high", 0.0) or 0.0)
                    day1_vol = float(active_ep_record.get("day1_volume", 0.0) or avg_vol_30d)

                    vwap_target = day1_vwap if day1_vwap > 0 else sma5_num
                    dist_to_vwap = (abs(price - vwap_target) / vwap_target) if vwap_target > 0 else 1.0
                    holds_low = (price >= day1_low * 0.985) if day1_low > 0 else True
                    vol_dryup = (volume < (day1_vol * 0.85)) if (day1_vol > 0 and volume > 0) else True

                    # If price broke below Day 1 low, EP setup is invalidated
                    if holds_low:
                        if day1_high > 0 and price >= (day1_high * 0.995) and rvol >= 1.20:
                            is_ep_day3 = True
                            patterns_matched.append("EP_DAY_3_BREAKOUT")
                            preset_tags.append("EP_DAY_2")
                        elif dist_to_vwap <= 0.045:
                            is_ep_day2 = True
                            patterns_matched.append("EP_DAY_2_VWAP")
                            preset_tags.append("EP_DAY_2")
                        else:
                            is_ep_day2 = True
                            patterns_matched.append("EP_DAY_2_VWAP")
                            preset_tags.append("EP_DAY_2")
        else:
            # Fresh Day 1 EP Shock evaluation
            if is_bullish_momentum and rvol >= 1.35 and has_ep_catalyst:
                is_ep_day1 = True
                patterns_matched.append("EP_DAY_1")
                preset_tags.append("EP_DAY_1")
                preset_tags.append("EP_5DAY_DB")

        # Pattern 5: Stage 2 Pullback - Arch C
        is_stage2_pullback = False
        is_pead_drift = False
        if stage2_trend and ma_ribbon:
            dist_20 = (abs(price - sma20_num) / sma20_num) if sma20_num > 0 else 1.0
            dist_50 = (abs(price - sma50_num) / sma50_num) if sma50_num > 0 else 1.0
            if (dist_20 <= 0.025 or dist_50 <= 0.025) and rvol <= 1.10 and price >= yesterday_low:
                is_stage2_pullback = True
                patterns_matched.append("STAGE_2_PULLBACK")
                preset_tags.append("STAGE_2_PULLBACK")
            elif has_ep_catalyst and price > sma20_num and dist_20 <= 0.04 and rvol <= 1.15:
                is_stage2_pullback = True
                is_pead_drift = True
                patterns_matched.append("STAGE_2_PULLBACK")
                preset_tags.append("STAGE_2_PULLBACK")

        # Pattern 6: Market Structure BOS (Break of Structure / Change of Character)
        is_structure_breakup = False
        is_structure_breakdown = False
        
        # Valid Swing High/Low: Must be a true multi-day swing structure level, not today's own candle
        # Requires breaking above 5-day week_high by at least +0.2% with high volume AND close in top 35% of day range
        if week_high > 0 and price > (week_high * 1.002) and rvol >= 1.45 and close_location_pct >= 65.0 and is_above_vwap and not is_exhausted:
            is_structure_breakup = True
            patterns_matched.append("STRUCTURE_BREAKUP")
            preset_tags.append("STRUCTURE_BOS")

        if (week_low > 0 and price < (week_low * 0.998) and rvol >= 1.45 and close_location_pct <= 35.0) or (sma50_num > 0 and price < sma50_num and yesterday_high >= sma50_num and rvol >= 1.40):
            is_structure_breakdown = True
            patterns_matched.append("STRUCTURE_BREAKDOWN")
            preset_tags.append("STRUCTURE_BOS")

        # Pattern 7: Intraday Velocity & ORB - Arch E
        is_intraday_velocity = False
        if rvol >= 2.20 and pct_change >= 2.5 and is_above_vwap:
            is_intraday_velocity = True
        if premarket_high > 0 and price >= premarket_high and pct_from_open >= 1.5 and rvol >= 1.40:
            is_intraday_velocity = True
        if (five_day_range_pct <= 10.0 or pct_from_open >= 4.0) and pct_change >= 4.0 and rvol >= 1.45:
            is_intraday_velocity = True
        for lvl in ROUND_DOLLAR_LEVELS:
            if abs(price - lvl) / lvl <= 0.015 and price >= lvl and (yesterday_high < lvl or open_price < lvl) and rvol >= 1.45:
                is_intraday_velocity = True
                break
        if premarket_low > 0 and premarket_change <= -1.8 and pct_change >= 1.5 and is_above_vwap and rvol >= 1.25:
            is_intraday_velocity = True

        if is_intraday_velocity:
            patterns_matched.append("INTRADAY_VELOCITY")
            preset_tags.append("INTRADAY_VELOCITY")

        # Pattern 8: Climax Reversals (Selling Climax Bottom & Buying Climax Top) - Arch G
        is_selling_climax = False
        is_buying_climax = False
        is_deep_oversold = bool(rsi_val <= 32.0 or (sma20_num > 0 and (price - sma20_num) / sma20_num <= -0.15))
        if is_deep_oversold and rvol >= 1.80 and (close_location_pct >= 60.0 or pct_from_open >= 2.0) and is_above_vwap:
            is_selling_climax = True
            patterns_matched.append("SELLING_CLIMAX_BOTTOM")
            preset_tags.append("CLIMAX_REVERSALS")

        is_deep_overbought = bool(rsi_val >= 72.0 or (sma20_num > 0 and (price - sma20_num) / sma20_num >= 0.18))
        if is_deep_overbought and rvol >= 1.80 and close_location_pct <= 40.0 and (not is_above_vwap or pct_from_open <= -1.5):
            is_buying_climax = True
            patterns_matched.append("BUYING_CLIMAX_TOP")
            preset_tags.append("CLIMAX_REVERSALS")

        # Primary Pattern Resolution
        primary_pattern = "MOMENTUM_RUNNER"
        badge_label = "⚡ Momentum"
        archetype = "ARCHETYPE_E"

        if is_htf:
            primary_pattern = "HIGH_TIGHT_FLAG"
            badge_label = "🚩 High Tight Flag"
            archetype = "ARCHETYPE_B"
        elif is_ep_day1:
            primary_pattern = "EP_DAY_1"
            badge_label = "🔥 EP Day 1"
            archetype = "ARCHETYPE_B"
        elif is_ep_day2:
            primary_pattern = "EP_DAY_2_VWAP"
            badge_label = "🎯 EP Day 2 VWAP"
            archetype = "ARCHETYPE_C"
        elif is_ep_day3:
            primary_pattern = "EP_DAY_3_BREAKOUT"
            badge_label = "🔥 EP Day 3 Breakout"
            archetype = "ARCHETYPE_B"
        elif is_base_breakout:
            primary_pattern = "BASE_BREAKOUT"
            badge_label = "☕ Base Breakout"
            archetype = "ARCHETYPE_A"
        elif is_vcp:
            primary_pattern = "MINERVINI_VCP"
            badge_label = "📉 Minervini VCP" if is_vcp_breakout else "📉 VCP Cheat"
            archetype = "ARCHETYPE_A"
        elif is_stage2_pullback:
            primary_pattern = "STAGE_2_PULLBACK"
            badge_label = "📈 Stage 2 Pullback"
            archetype = "ARCHETYPE_C"
        elif is_selling_climax:
            primary_pattern = "SELLING_CLIMAX_BOTTOM"
            badge_label = "🌊 Selling Climax"
            archetype = "ARCHETYPE_G"
        elif is_buying_climax:
            primary_pattern = "BUYING_CLIMAX_TOP"
            badge_label = "🌊 Buying Climax"
            archetype = "ARCHETYPE_G"
        elif is_structure_breakup:
            primary_pattern = "STRUCTURE_BREAKUP"
            badge_label = "⚡ Structure BOS"
            archetype = "ARCHETYPE_D"
        elif is_structure_breakdown:
            primary_pattern = "STRUCTURE_BREAKDOWN"
            badge_label = "🔻 Structure Breakdown"
            archetype = "ARCHETYPE_D"
        elif is_intraday_velocity:
            primary_pattern = "INTRADAY_VELOCITY"
            badge_label = "🌊 Intraday Velocity"
            archetype = "ARCHETYPE_E"
        elif pct_change >= 3.0 and rvol >= 1.5:
            primary_pattern = "MOMENTUM_RUNNER"
            badge_label = "⚡ Momentum Runner"
            archetype = "ARCHETYPE_E"
        else:
            primary_pattern = "TECHNICAL_SETUP"
            badge_label = "⚡ Setup"
            archetype = "ARCHETYPE_E"

        trade_plan = PatternDetector._build_trade_plan(
            pattern=primary_pattern,
            price=price,
            open_price=open_price,
            yesterday_high=yesterday_high,
            yesterday_low=yesterday_low,
            week_high=week_high,
            week_low=week_low,
            vwap_num=vwap_num,
            sma5_num=sma5_num,
            sma20_num=sma20_num,
            sma50_num=sma50_num,
            gap_pct=gap_pct
        )

        criteria_checklist = {
            "stage2_trend": stage2_trend,
            "ma_ribbon": ma_ribbon,
            "five_day_range_pct": round(five_day_range_pct, 1) if five_day_range_pct < 900 else 0.0,
            "dist_to_52w_high_pct": round(dist_to_52w_high_pct, 1),
            "dist_from_52w_low_pct": round(dist_from_52w_low_pct, 1),
            "rvol": round(rvol, 2),
            "is_above_vwap": is_above_vwap,
            "close_location_pct": round(close_location_pct, 1),
            "has_catalyst": has_ep_catalyst,
            "catalyst_stars": catalyst_stars,
            "catalyst_type": catalyst_type,
            "is_exhausted": is_exhausted,
            "exhaustion_flag": exhaustion_flag,
            "exhaustion_desc": exhaustion_desc,
        }

        return {
            "primary_pattern": primary_pattern,
            "badge_label": badge_label,
            "archetype": archetype,
            "patterns_matched": patterns_matched,
            "preset_tags": preset_tags,
            "is_exhausted": is_exhausted,
            "exhaustion_flag": exhaustion_flag,
            "exhaustion_desc": exhaustion_desc,
            "exhaustion_penalty": exhaustion_penalty,
            "is_ep_day1": is_ep_day1,
            "is_ep_day2": is_ep_day2,
            "is_vcp": is_vcp,
            "is_htf": is_htf,
            "is_base_breakout": is_base_breakout,
            "is_stage2_pullback": is_stage2_pullback,
            "is_selling_climax": is_selling_climax,
            "is_buying_climax": is_buying_climax,
            "is_structure_breakup": is_structure_breakup,
            "is_structure_breakdown": is_structure_breakdown,
            "is_intraday_velocity": is_intraday_velocity,
            "trade_plan": trade_plan,
            "criteria_checklist": criteria_checklist,
            "five_day_range_pct": round(five_day_range_pct, 1) if five_day_range_pct < 900 else 0.0,
            "vcp_points": vcp_points,
        }

    @staticmethod
    def _build_trade_plan(
        pattern: str,
        price: float,
        open_price: float,
        yesterday_high: float,
        yesterday_low: float,
        week_high: float,
        week_low: float,
        vwap_num: float,
        sma5_num: float,
        sma20_num: float,
        sma50_num: float,
        gap_pct: float
    ) -> Dict[str, Any]:
        entry_pivot = price
        hard_stop = price * 0.95
        soft_stop_desc = "Loss of session VWAP for 15m"
        time_stop_days = 5
        trailing_desc = "Trailing 20-SMA"
        conviction_mult = 1.00
        is_short = False

        if pattern == "HIGH_TIGHT_FLAG":
            entry_pivot = max(price, week_high)
            hard_stop = week_low if week_low > 0 else (price * 0.94)
            soft_stop_desc = "Daily close below 10-EMA"
            time_stop_days = 4
            trailing_desc = "Trailing 10-EMA"
            conviction_mult = 1.35
        elif pattern == "BASE_BREAKOUT":
            entry_pivot = max(price, week_high)
            hard_stop = (yesterday_low if yesterday_low > 0 else price * 0.94)
            soft_stop_desc = "Daily close below 20-SMA"
            time_stop_days = 7
            trailing_desc = "Trailing 20-SMA"
            conviction_mult = 1.25
        elif pattern == "MINERVINI_VCP":
            entry_pivot = max(price, week_high)
            hard_stop = (week_low if week_low > 0 else price * 0.95)
            soft_stop_desc = "Daily close below 20-SMA"
            time_stop_days = 5
            trailing_desc = "Trailing 20-SMA"
            conviction_mult = 1.25
        elif pattern == "EP_DAY_1":
            entry_pivot = price
            hard_stop = open_price if open_price > 0 else (price * 0.93)
            soft_stop_desc = "Loss of Intraday VWAP"
            time_stop_days = 5
            trailing_desc = "Trailing 10-EMA"
            conviction_mult = 1.35
        elif pattern == "EP_DAY_2_VWAP":
            entry_pivot = price
            hard_stop = yesterday_low if yesterday_low > 0 else (price * 0.95)
            soft_stop_desc = "Daily close below 5-SMA"
            time_stop_days = 5
            trailing_desc = "Trailing 10-EMA"
            conviction_mult = 1.25
        elif pattern == "STAGE_2_PULLBACK":
            entry_pivot = price
            hard_stop = yesterday_low if yesterday_low > 0 else (sma20_num * 0.98 if sma20_num > 0 else price * 0.95)
            soft_stop_desc = "Daily close below 20-SMA"
            time_stop_days = 5
            trailing_desc = "Trailing 20-SMA"
            conviction_mult = 1.20
        elif pattern == "SELLING_CLIMAX_BOTTOM":
            entry_pivot = price
            hard_stop = yesterday_low if yesterday_low > 0 else (price * 0.93)
            soft_stop_desc = "Loss of Intraday VWAP"
            time_stop_days = 5
            trailing_desc = "Trailing 5-EMA / VWAP"
            conviction_mult = 1.25
        elif pattern in ("BUYING_CLIMAX_TOP", "STRUCTURE_BREAKDOWN"):
            is_short = True
            entry_pivot = price
            hard_stop = max(yesterday_high, week_high) if max(yesterday_high, week_high) > 0 else (price * 1.05)
            soft_stop_desc = "Reclaim of Intraday VWAP"
            time_stop_days = 5
            trailing_desc = "Trailing 10-EMA / VWAP"
            conviction_mult = 1.15
        elif pattern == "STRUCTURE_BREAKUP":
            entry_pivot = max(price, week_high)
            hard_stop = yesterday_low if yesterday_low > 0 else (price * 0.95)
            soft_stop_desc = "Loss of broken resistance level"
            time_stop_days = 5
            trailing_desc = "Trailing 20-SMA"
            conviction_mult = 1.10
        elif pattern == "INTRADAY_VELOCITY":
            entry_pivot = price
            hard_stop = (vwap_num * 0.985 if vwap_num > 0 else price * 0.97)
            soft_stop_desc = "Loss of session VWAP"
            time_stop_days = 1
            trailing_desc = "Trailing Intraday VWAP"
            conviction_mult = 1.00

        if is_short:
            stop_dist = max(price * 0.015, hard_stop - price)
            stop_dist_pct = (stop_dist / price) * 100.0
            target_1 = round(price - (stop_dist * 2.0), 2)
            target_2 = round(price - (stop_dist * 3.5), 2)
        else:
            stop_dist = max(price * 0.015, price - hard_stop)
            stop_dist_pct = (stop_dist / price) * 100.0
            target_1 = round(price + (stop_dist * 2.0), 2)
            target_2 = round(price + (stop_dist * 3.5), 2)

        t1_pct = abs((target_1 - price) / price * 100.0)
        t2_pct = abs((target_2 - price) / price * 100.0)

        return {
            "is_short": is_short,
            "entry_pivot": round(entry_pivot, 2),
            "hard_stop": round(hard_stop, 2),
            "stop_dist_dollar": round(stop_dist, 2),
            "stop_dist_pct": round(stop_dist_pct, 2),
            "soft_stop_desc": soft_stop_desc,
            "time_stop_days": time_stop_days,
            "target_1": target_1,
            "target_1_pct": round(t1_pct, 1),
            "target_2": target_2,
            "target_2_pct": round(t2_pct, 1),
            "trailing_desc": trailing_desc,
            "conviction_mult": conviction_mult,
            "reward_risk_ratio": "2.0R / 3.5R"
        }

pattern_detector = PatternDetector()
