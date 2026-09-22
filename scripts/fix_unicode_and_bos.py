# -*- coding: utf-8 -*-
"""Fix Unicode stars/emoji in pattern_detector.py and setup_scorer.py, and implement TradingView PivotHigh(5,5) BOS."""

import re

# 1. Update setup_scorer.py
scorer_path = r"c:\Users\jfan\Documents\Screener\sources\setup_scorer.py"
with open(scorer_path, "r", encoding="utf-8") as f:
    scorer_text = f.read()

# Fix stars_visual in setup_scorer.py
scorer_text = re.sub(
    r'stars_visual\s*=\s*"[^"]*"\s*\*\s*num_stars\s*\+\s*"[^"]*"\s*\*\s*\(5\s*-\s*num_stars\)',
    'stars_visual = "?" * num_stars + "?" * (5 - num_stars)',
    scorer_text
)
scorer_text = scorer_text.replace('"?????"', '"?????"')
scorer_text = scorer_text.replace("??", "?")
scorer_text = scorer_text.replace("??", "?")

with open(scorer_path, "w", encoding="utf-8") as f:
    f.write(scorer_text)
print("Updated setup_scorer.py!")

# 2. Update pattern_detector.py
pat_path = r"c:\Users\jfan\Documents\Screener\sources\pattern_detector.py"
with open(pat_path, "r", encoding="utf-8") as f:
    pat_text = f.read()

# Fix all badge labels in pattern_detector.py
badge_replacements = {
    'badge_label = "?? High Tight Flag"': 'badge_label = "?? High Tight Flag"',
    'badge_label = "?? EP Day 1"': 'badge_label = "?? EP Day 1"',
    'badge_label = "?? EP Day 2 VWAP"': 'badge_label = "?? EP Day 2 VWAP"',
    'badge_label = "?? EP Day 3 Breakout"': 'badge_label = "?? EP Day 3 Breakout"',
    'badge_label = "? Base Breakout"': 'badge_label = "? Base Breakout"',
    'badge_label = "?? Minervini VCP" if is_vcp_breakout else "?? VCP Cheat"': 'badge_label = "?? Minervini VCP" if is_vcp_breakout else "?? VCP Cheat"',
    'badge_label = "?? Stage 2 Pullback"': 'badge_label = "?? Stage 2 Pullback"',
    'badge_label = "?? Selling Climax"': 'badge_label = "?? Selling Climax"',
    'badge_label = "?? Buying Climax"': 'badge_label = "?? Buying Climax"',
    'badge_label = "? Structure Break"': 'badge_label = "? Structure BOS"',
    'badge_label = "?? Structure Breakdown"': 'badge_label = "?? Structure Breakdown"',
    'badge_label = "?? Intraday Velocity"': 'badge_label = "?? Intraday Velocity"',
    'badge_label = "?? Momentum Runner"': 'badge_label = "? Momentum Runner"',
    'badge_label = "?? Setup"': 'badge_label = "? Setup"',
    'badge_label = "? Momentum"': 'badge_label = "? Momentum"',
}

for k, v in badge_replacements.items():
    pat_text = pat_text.replace(k, v)

# Add TradingView ta.pivothigh(5, 5) function to PatternDetector class
tv_pivot_helper = """
    @staticmethod
    def calculate_tradingview_pivots(df, length: int = 5):
        """Calculate TradingView Pine Script ta.pivothigh(high, 5, 5) and ta.pivotlow(low, 5, 5).
        A Pivot High requires High[i] > High[i-length...i-1] AND High[i] > High[i+1...i+length].
        """
        if df is None or len(df) < (length * 2 + 1):
            return None, None
        
        highs = df['High'].values if 'High' in df.columns else df['high'].values
        lows = df['Low'].values if 'Low' in df.columns else df['low'].values
        
        last_pivot_high = None
        last_pivot_low = None
        
        n = len(highs)
        # Search from most recent confirmed bar backward
        for i in range(n - length - 1, length - 1, -1):
            curr_h = highs[i]
            is_pivot_h = True
            for l in range(1, length + 1):
                if highs[i - l] >= curr_h or highs[i + l] >= curr_h:
                    is_pivot_h = False
                    break
            if is_pivot_h and last_pivot_high is None:
                last_pivot_high = float(curr_h)
            
            curr_l = lows[i]
            is_pivot_l = True
            for l in range(1, length + 1):
                if lows[i - l] <= curr_l or lows[i + l] <= curr_l:
                    is_pivot_l = False
                    break
            if is_pivot_l and last_pivot_low is None:
                last_pivot_low = float(curr_l)
            
            if last_pivot_high is not None and last_pivot_low is not None:
                break
                
        return last_pivot_high, last_pivot_low
"""

if "calculate_tradingview_pivots" not in pat_text:
    pat_text = pat_text.replace("class PatternDetector:", "class PatternDetector:\n" + tv_pivot_helper)

# Refine Structure BOS detection logic to require true swing breakout
old_bos_logic = """        # Pattern 6: Market Structure BOS - Arch D
        is_structure_breakup = False
        is_structure_breakdown = False
        if week_high > 0 and price > week_high and rvol >= 1.35 and is_above_vwap and not is_exhausted:
            is_structure_breakup = True
            patterns_matched.append("STRUCTURE_BREAKUP")
            preset_tags.append("STRUCTURE_BOS")

        if (week_low > 0 and price < week_low and rvol >= 1.35) or (sma50_num > 0 and price < sma50_num and yesterday_high >= sma50_num and rvol >= 1.35):
            is_structure_breakdown = True
            patterns_matched.append("STRUCTURE_BREAKDOWN")
            preset_tags.append("STRUCTURE_BOS")"""

new_bos_logic = """        # Pattern 6: Market Structure BOS (Break of Structure / Change of Character) - TradingView ta.pivothigh(5,5)
        is_structure_breakup = False
        is_structure_breakdown = False
        
        # Determine verified swing structure pivot high/low
        # If history_df is passed, use exact Pine Script ta.pivothigh(5,5); else use multi-day swing anchor
        tv_swing_high, tv_swing_low = None, None
        if history_df is not None:
            tv_swing_high, tv_swing_low = PatternDetector.calculate_tradingview_pivots(history_df, length=5)
        
        # Valid Swing High Pivot to break:
        # Must be a true established swing high (higher than 5-day week_high or verified pivot), not today's own candle
        swing_ref_high = tv_swing_high if (tv_swing_high and tv_swing_high > 0) else week_high
        swing_ref_low = tv_swing_low if (tv_swing_low and tv_swing_low > 0) else week_low

        # Bullish BOS: Price breaks above established Swing High on elevated volume & closes near highs
        if swing_ref_high > 0 and price > (swing_ref_high * 1.002) and rvol >= 1.40 and close_location_pct >= 65.0 and is_above_vwap and not is_exhausted:
            is_structure_breakup = True
            patterns_matched.append("STRUCTURE_BREAKUP")
            preset_tags.append("STRUCTURE_BOS")

        # Bearish BOS: Price breaks below established Swing Low on volume
        if swing_ref_low > 0 and price < (swing_ref_low * 0.998) and rvol >= 1.40 and close_location_pct <= 35.0:
            is_structure_breakdown = True
            patterns_matched.append("STRUCTURE_BREAKDOWN")
            preset_tags.append("STRUCTURE_BOS")"""

if old_bos_logic in pat_text:
    pat_text = pat_text.replace(old_bos_logic, new_bos_logic)

with open(pat_path, "w", encoding="utf-8") as f:
    f.write(pat_text)

print("Updated pattern_detector.py with TradingView ta.pivothigh(5,5) logic and clean badges!")
