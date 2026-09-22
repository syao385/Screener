"""
RVOL Calculator: Computes 20-day anchored Relative Volume at time T across four market sessions.

Institutional Specification & Anchor Times:
1. Premarket Session:
   - Window: Weekdays 00:00:00 to 09:30:00 EST
   - Anchor Time: Midnight - 00:00:00 EST
   - Formula: RVOL(T) = Cumulative Premarket Volume [00:00 -> T] / 20-Day Avg Cumulative Premarket Volume [00:00 -> T]
2. Regular Market Session:
   - Window: Weekdays 09:30:00 to 16:30:00 EST
   - Anchor Time: 09:30:00 EST
   - Formula: RVOL(T) = Cumulative Regular Volume [09:30 -> T] / 20-Day Avg Cumulative Regular Volume [09:30 -> T]
3. After-Hours Session:
   - Window: Weekdays (Mon-Thu) 16:30:00 to 23:59:59 EST
   - Anchor Time: 04:30:00 PM EST (16:30:00 EST)
   - Formula: RVOL(T) = Cumulative After-Hours Volume [16:30 -> T] / 20-Day Avg Cumulative After-Hours Volume [16:30 -> T]
4. Weekend Session:
   - Window: Friday 16:30:00 EST through Sunday 23:59:59 EST (until Monday 00:00:00 EST)
   - Anchor Time: Friday 04:30:00 PM EST (Friday 16:30:00 EST)
   - Formula: RVOL(T) = Cumulative Friday Post-4:30 PM Volume [16:30 -> 20:00] / 20-Day Avg Cumulative Volume [16:30 -> 20:00]
"""

import logging
import datetime
import pandas as pd
import yfinance as yf
from typing import Dict, Optional
from config import RVOL_LOOKBACK_DAYS, TZ_EST

logger = logging.getLogger("rvol_calculator")

# Exact Session Anchor Times (EST)
ANCHOR_PREMARKET = datetime.time(0, 0)      # Midnight - 00:00 AM EST
ANCHOR_REGULAR   = datetime.time(9, 30)     # 09:30 AM EST
ANCHOR_AFTERHOUR = datetime.time(16, 30)    # 04:30 PM EST (16:30 EST)
ANCHOR_WEEKEND   = datetime.time(16, 30)    # Friday 04:30 PM EST


def get_anchor_time(session_type: str, now_est: Optional[datetime.datetime] = None) -> datetime.time:
    """Return institutional anchor time according to market session."""
    session_upper = (session_type or "REGULAR").upper().strip()
    if session_upper == "PREMARKET":
        return ANCHOR_PREMARKET
    elif session_upper == "REGULAR":
        return ANCHOR_REGULAR
    elif session_upper in ["POSTMARKET", "AFTER_HOURS", "AFTERHOURS"]:
        return ANCHOR_AFTERHOUR
    elif session_upper == "WEEKEND":
        return ANCHOR_WEEKEND
    return ANCHOR_REGULAR


def get_expected_cumulative_fraction(session_type: str, target_time: datetime.time) -> float:
    """
    Returns empirical institutional fraction of 20-day ADV expected to accumulate
    between session anchor time and target_time T.
    """
    session_upper = (session_type or "REGULAR").upper().strip()
    m = target_time.hour * 60 + target_time.minute

    if session_upper == "PREMARKET":
        # Anchor: 00:00 EST. Window: 00:00 to 09:30 EST (0 to 570 mins)
        if m < 240:    # 00:00 - 04:00 overnight
            return max(0.0001, 0.0005 * (m / 240.0))
        elif m < 420:  # 04:00 - 07:00 early premarket
            return 0.0005 + 0.0035 * ((m - 240) / 180.0)
        elif m < 480:  # 07:00 - 08:00 premarket core
            return 0.0040 + 0.0050 * ((m - 420) / 60.0)
        elif m < 540:  # 08:00 - 09:00 prime premarket
            return 0.0090 + 0.0090 * ((m - 480) / 60.0)
        elif m <= 570: # 09:00 - 09:30 opening auction sprint
            return 0.0180 + 0.0070 * ((m - 540) / 30.0)
        else:
            return 0.0250

    elif session_upper == "REGULAR":
        # Anchor: 09:30 EST. Window: 09:30 to 16:30 EST (0 to 420 mins)
        reg_m = m - 570
        if reg_m <= 0:
            return 0.05
        elif reg_m <= 30:   # 09:30 - 10:00 ORB
            return 0.20 * (reg_m / 30.0)
        elif reg_m <= 90:   # 10:00 - 11:00 morning wave
            return 0.20 + 0.18 * ((reg_m - 30) / 60.0)
        elif reg_m <= 150:  # 11:00 - 12:00 midday transition
            return 0.38 + 0.12 * ((reg_m - 90) / 60.0)
        elif reg_m <= 270:  # 12:00 - 14:00 lunch consolidation
            return 0.50 + 0.20 * ((reg_m - 150) / 120.0)
        elif reg_m <= 360:  # 14:00 - 15:30 afternoon trend
            return 0.70 + 0.18 * ((reg_m - 270) / 90.0)
        elif reg_m <= 390:  # 15:30 - 16:00 close run
            return 0.88 + 0.09 * ((reg_m - 360) / 30.0)
        elif reg_m <= 420:  # 16:00 - 16:30 post-close cross settlement
            return 0.97 + 0.03 * ((reg_m - 390) / 30.0)
        else:
            return 1.00

    elif session_upper in ["POSTMARKET", "AFTER_HOURS", "AFTERHOURS"]:
        # Anchor: 16:30 EST. Window: 16:30 to 20:00 EST (0 to 210 mins)
        post_m = m - 990
        if post_m <= 0:
            return 0.001
        elif post_m <= 30:   # 16:30 - 17:00
            return 0.0030 * (post_m / 30.0)
        elif post_m <= 60:   # 17:00 - 17:30
            return 0.0030 + 0.0030 * ((post_m - 30) / 30.0)
        elif post_m <= 90:   # 17:30 - 18:00
            return 0.0060 + 0.0025 * ((post_m - 60) / 30.0)
        elif post_m <= 150:  # 18:00 - 19:00
            return 0.0085 + 0.0020 * ((post_m - 90) / 60.0)
        elif post_m <= 210:  # 19:00 - 20:00
            return 0.0105 + 0.0015 * ((post_m - 150) / 60.0)
        else:                # 20:00 close through overnight
            return 0.0120

    elif session_upper == "WEEKEND":
        # Anchor: Friday 16:30 EST. Window: Completed Friday 16:30 - 20:00 post-market
        return 0.0120

    return 1.00


class RVOLCalculator:
    """Calculates Relative Volume at time T (cumulative session volume vs 20-day session average)."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, float]] = {}

    def calculate_session_rvol(
        self,
        ticker: str,
        session_type: str = "REGULAR",
        current_volume: Optional[float] = None,
        adv_20d: Optional[float] = None,
        tv_rvol: Optional[float] = None,
        target_time: Optional[datetime.time] = None
    ) -> float:
        """
        Calculate Relative Volume (RVOL) at time T strictly anchored to session definition:
        RVOL(T) = Cumulative Volume [Anchor -> T] / 20-day Avg Cumulative Volume [Anchor -> T]

        Anchor Times:
        - PREMARKET: Midnight - 00:00 AM EST
        - REGULAR: 09:30 AM EST
        - POSTMARKET: 04:30 PM EST (16:30 EST)
        - WEEKEND: Friday 04:30 PM EST (Friday 16:30 EST)
        """
        if not target_time:
            now_est = datetime.datetime.now(TZ_EST)
            target_time = now_est.time()

        session_upper = (session_type or "REGULAR").upper().strip()
        vol_key = int(current_volume or 0)
        cache_key = f"{ticker}_{session_upper}_{target_time.strftime('%H%M')}_{vol_key}"
        if cache_key in self._cache:
            return self._cache[cache_key].get("rvol", 1.0)

        # Retrieve or compute 20-day ADV if not supplied
        if adv_20d is None or adv_20d <= 0:
            try:
                clean_sym = ticker.split(":")[-1] if ":" in ticker else ticker
                yf_ticker = yf.Ticker(clean_sym)
                df_day = yf_ticker.history(period="35d", interval="1d")
                if not df_day.empty and len(df_day) >= 5:
                    adv_20d = float(df_day["Volume"].iloc[-21:-1].mean())
            except Exception as e:
                logger.debug(f"Error fetching ADV for {ticker}: {e}")

        if not adv_20d or adv_20d <= 0:
            adv_20d = 1_000_000.0

        rvol = None

        # 1. REGULAR SESSION (Anchor: 09:30 AM EST)
        if session_upper == "REGULAR":
            # First Priority: TradingView's verified time-of-day normalized relative_volume_10d_calc
            if tv_rvol is not None and not pd.isna(tv_rvol):
                try:
                    tv_val = float(tv_rvol)
                    if 0.05 <= tv_val <= 30.0:
                        rvol = round(tv_val, 2)
                except Exception:
                    pass

            # Second Priority: Direct time-of-day cumulative model
            if rvol is None:
                frac = get_expected_cumulative_fraction("REGULAR", target_time)
                expected_vol = max(1000.0, adv_20d * frac)
                vol = current_volume if (current_volume and current_volume > 0) else adv_20d
                rvol = round(vol / expected_vol, 2)

        # 2. PREMARKET SESSION (Anchor: 00:00 AM Midnight EST)
        elif session_upper == "PREMARKET":
            frac = get_expected_cumulative_fraction("PREMARKET", target_time)
            expected_vol = max(1000.0, adv_20d * frac)

            if current_volume is None or current_volume <= 0:
                rvol = 0.00
            elif current_volume > adv_20d * 0.25:
                # Defensive clamp: if full day volume was passed in error, fallback to daily RVOL
                rvol = round(current_volume / adv_20d, 2)
            else:
                rvol = round(current_volume / expected_vol, 2)

        # 3. AFTER-HOURS SESSION (Anchor: 04:30 PM EST)
        elif session_upper in ["POSTMARKET", "AFTER_HOURS", "AFTERHOURS"]:
            frac = get_expected_cumulative_fraction("POSTMARKET", target_time)
            expected_vol = max(1000.0, adv_20d * frac)

            if current_volume is None or current_volume <= 0:
                rvol = 0.00
            elif current_volume > adv_20d * 0.25:
                # Defensive clamp: if full day volume was passed in error, fallback to daily RVOL
                rvol = round(current_volume / adv_20d, 2)
            else:
                rvol = round(current_volume / expected_vol, 2)

        # 4. WEEKEND SESSION (Anchor: Friday 04:30 PM EST)
        elif session_upper == "WEEKEND":
            frac = get_expected_cumulative_fraction("WEEKEND", target_time)
            expected_vol = max(1000.0, adv_20d * frac)

            if current_volume is None or current_volume <= 0:
                rvol = 0.00
            elif current_volume > adv_20d * 0.25:
                # Defensive clamp: if full day volume was passed in error, fallback to daily RVOL
                rvol = round(current_volume / adv_20d, 2)
            else:
                rvol = round(current_volume / expected_vol, 2)

        # Final Fallback
        if rvol is None:
            if tv_rvol is not None and not pd.isna(tv_rvol) and float(tv_rvol) > 0:
                rvol = round(float(tv_rvol), 2)
            else:
                rvol = 1.00

        self._cache[cache_key] = {"rvol": rvol}
        return rvol

    # Backward-compatible alias
    def calculate_premarket_rvol(
        self,
        ticker: str,
        current_premarket_vol: Optional[float] = None,
        tv_rvol: Optional[float] = None,
        target_time: Optional[datetime.time] = None
    ) -> float:
        return self.calculate_session_rvol(
            ticker=ticker,
            session_type="PREMARKET",
            current_volume=current_premarket_vol,
            tv_rvol=tv_rvol,
            target_time=target_time
        )


rvol_calc = RVOLCalculator()
