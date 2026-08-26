"""RVOL Calculator: Computes 20-day Relative Volume at time T for Premarket, Regular Hours, and After-Hours."""

import logging
import datetime
import pandas as pd
import yfinance as yf
from typing import Dict, Optional
from config import RVOL_LOOKBACK_DAYS, TZ_EST

logger = logging.getLogger("rvol_calculator")

class RVOLCalculator:
    """Calculates Relative Volume at time T (cumulative session volume vs 20-day session average)."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, float]] = {}

    def calculate_session_rvol(
        self,
        ticker: str,
        session_type: str = "PREMARKET",
        current_volume: Optional[float] = None,
        tv_rvol: Optional[float] = None,
        target_time: Optional[datetime.time] = None
    ) -> float:
        """
        Calculate RVOL at time T anchored by market session.
        - PREMARKET: 04:00 to target_time (or 09:30)
        - REGULAR: 09:30 to target_time
        - POSTMARKET: 16:00 to target_time (or 20:00)
        """
        if not target_time:
            now_est = datetime.datetime.now(TZ_EST)
            target_time = now_est.time()

        cache_key = f"{ticker}_{session_type}_{target_time.strftime('%H%M')}"
        if cache_key in self._cache:
            return self._cache[cache_key].get("rvol", 1.0)

        rvol = None

        # Determine start time anchor based on session
        if session_type == "REGULAR":
            # If after 16:00 EST or target_time >= 16:00, use full-day volume vs 20d ADV
            if target_time.hour >= 16 or target_time.hour < 9 or (target_time.hour == 9 and target_time.minute < 30):
                # Market is closed or post-market: full session volume vs 20d average daily volume
                try:
                    clean_sym = ticker.split(":")[-1] if ":" in ticker else ticker
                    yf_ticker = yf.Ticker(clean_sym)
                    df_day = yf_ticker.history(period="35d", interval="1d")
                    if not df_day.empty and len(df_day) >= 5:
                        adv_20d = df_day["Volume"].iloc[-21:-1].mean()
                        last_vol = current_volume if (current_volume and current_volume > 0) else df_day["Volume"].iloc[-1]
                        if adv_20d > 0 and last_vol > 0:
                            rvol = round(last_vol / adv_20d, 2)
                except Exception as e:
                    logger.debug(f"Daily RVOL calc error on {ticker}: {e}")
            else:
                # Intraday regular market hours (09:30 to T)
                if tv_rvol is not None and not pd.isna(tv_rvol) and tv_rvol > 0:
                    rvol = round(float(tv_rvol), 2)
                else:
                    try:
                        clean_sym = ticker.split(":")[-1] if ":" in ticker else ticker
                        yf_ticker = yf.Ticker(clean_sym)
                        df = yf_ticker.history(period="30d", interval="5m", prepost=False)
                        if not df.empty and "Volume" in df.columns:
                            if df.index.tz is None:
                                df.index = df.index.tz_localize("UTC").tz_convert(TZ_EST)
                            else:
                                df.index = df.index.tz_convert(TZ_EST)
                            end_str = f"{min(target_time.hour, 16):02d}:{target_time.minute:02d}"
                            df_window = df.between_time("09:30", end_str)
                            if not df_window.empty:
                                daily_vols = df_window.groupby(df_window.index.date)["Volume"].sum()
                                if len(daily_vols) >= 2:
                                    today_vol = daily_vols.iloc[-1]
                                    hist_vols = daily_vols.iloc[-(RVOL_LOOKBACK_DAYS + 1):-1]
                                    active_hist = hist_vols[hist_vols > 0]
                                    if not active_hist.empty and active_hist.mean() > 0:
                                        rvol = round(today_vol / active_hist.mean(), 2)
                    except Exception as e:
                        logger.debug(f"Intraday regular RVOL error on {ticker}: {e}")
        elif session_type == "POSTMARKET":
            # Post-market after-hours session (16:00 to 20:00 EST)
            # Calculates cumulative after-hours volume (16:00 to T) relative to 20-day historical after-hours volume (16:00 to T)
            try:
                clean_sym = ticker.split(":")[-1] if ":" in ticker else ticker
                yf_ticker = yf.Ticker(clean_sym)
                df = yf_ticker.history(period="30d", interval="5m", prepost=True)
                if not df.empty and "Volume" in df.columns:
                    if df.index.tz is None:
                        df.index = df.index.tz_localize("UTC").tz_convert(TZ_EST)
                    else:
                        df.index = df.index.tz_convert(TZ_EST)
                    end_str = f"{min(target_time.hour, 20):02d}:{target_time.minute if target_time.hour < 20 else 0:02d}"
                    df_window = df.between_time("16:00", end_str)
                    if not df_window.empty:
                        daily_vols = df_window.groupby(df_window.index.date)["Volume"].sum()
                        if len(daily_vols) >= 2:
                            today_vol = daily_vols.iloc[-1]
                            if current_volume is not None and current_volume > 0:
                                today_vol = max(today_vol, current_volume)
                            hist_vols = daily_vols.iloc[-(RVOL_LOOKBACK_DAYS + 1):-1]
                            active_hist = hist_vols[hist_vols > 0]
                            if not active_hist.empty and active_hist.mean() > 0:
                                rvol = round(today_vol / active_hist.mean(), 2)
            except Exception as e:
                logger.debug(f"Postmarket intraday RVOL error on {ticker}: {e}")

            # Fallback if historical post-market 5m data is thin: compare postmarket volume to 2% of 20d ADV
            if rvol is None or rvol == 0:
                try:
                    df_day = yf_ticker.history(period="35d", interval="1d")
                    if not df_day.empty and len(df_day) >= 5:
                        adv_20d = df_day["Volume"].iloc[-21:-1].mean()
                        expected_pm_vol = max(5000.0, adv_20d * 0.02)
                        post_vol = current_volume if (current_volume and current_volume > 0) else 0.0
                        if post_vol > 0:
                            rvol = round(post_vol / expected_pm_vol, 2)
                except Exception:
                    pass
        else: # PREMARKET (04:00 to 09:30)
            try:
                clean_sym = ticker.split(":")[-1] if ":" in ticker else ticker
                yf_ticker = yf.Ticker(clean_sym)
                df = yf_ticker.history(period="30d", interval="5m", prepost=True)
                if not df.empty and "Volume" in df.columns:
                    if df.index.tz is None:
                        df.index = df.index.tz_localize("UTC").tz_convert(TZ_EST)
                    else:
                        df.index = df.index.tz_convert(TZ_EST)
                    end_str = f"{min(target_time.hour, 9):02d}:{target_time.minute if target_time.hour < 9 else 30:02d}"
                    df_window = df.between_time("04:00", end_str)
                    if not df_window.empty:
                        daily_vols = df_window.groupby(df_window.index.date)["Volume"].sum()
                        if len(daily_vols) >= 2:
                            today_vol = daily_vols.iloc[-1]
                            if current_volume is not None and current_volume > 0:
                                today_vol = max(today_vol, current_volume)
                            hist_vols = daily_vols.iloc[-(RVOL_LOOKBACK_DAYS + 1):-1]
                            active_hist = hist_vols[hist_vols > 0]
                            if not active_hist.empty and active_hist.mean() > 0:
                                rvol = round(today_vol / active_hist.mean(), 2)
            except Exception as e:
                logger.debug(f"Premarket RVOL error on {ticker}: {e}")

        # Fallback to tv_rvol or 1.0
        if rvol is None or rvol == 0:
            if tv_rvol is not None and not pd.isna(tv_rvol) and tv_rvol > 0:
                rvol = round(float(tv_rvol), 2)
            else:
                rvol = 1.0

        self._cache[cache_key] = {"rvol": rvol}
        return rvol

    # Backward-compatible alias
    def calculate_premarket_rvol(self, ticker: str, current_premarket_vol: Optional[float] = None, tv_rvol: Optional[float] = None, target_time: Optional[datetime.time] = None) -> float:
        return self.calculate_session_rvol(ticker, session_type="PREMARKET", current_volume=current_premarket_vol, tv_rvol=tv_rvol, target_time=target_time)

rvol_calc = RVOLCalculator()
