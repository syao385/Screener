"""State Manager: SQLite-backed multi-day state persistence for Episodic Pivots, daily bars, and streaks."""

import os
import sqlite3
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from config import DATA_DIR, TZ_EST

logger = logging.getLogger("state_manager")

DB_PATH = DATA_DIR / "screener_state.db"

class StateManager:
    """Manages SQLite database for multi-day EP tracking, daily price action, and consecutive streaks."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get SQLite connection with row factory."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> bool:
        """Initialize database schema if not exists."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                
                # 1. Episodic Pivots lifecycle table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodic_pivots (
                    ticker TEXT PRIMARY KEY,
                    ep_date TEXT NOT NULL,
                    day_count INTEGER NOT NULL DEFAULT 1,
                    day1_open REAL,
                    day1_high REAL,
                    day1_low REAL,
                    day1_close REAL,
                    day1_vwap REAL,
                    day1_volume REAL,
                    day1_gap_pct REAL,
                    catalyst_type TEXT,
                    catalyst_headline TEXT,
                    catalyst_stars REAL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    last_seen_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)

                # 2. Daily price bar history (rolling 30 days)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_bars (
                    ticker TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    vwap REAL,
                    pct_change REAL,
                    is_green INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (ticker, trade_date)
                );
                """)

                # 3. Rolling consecutive streaks
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS streaks (
                    ticker TEXT PRIMARY KEY,
                    streak_direction TEXT NOT NULL, -- 'UP' or 'DOWN'
                    streak_count INTEGER NOT NULL DEFAULT 0,
                    last_trade_date TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)

                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error initializing SQLite state database: {e}")
            return False

    def register_or_update_ep(
        self,
        ticker: str,
        ep_date: str,
        day1_open: float,
        day1_high: float,
        day1_low: float,
        day1_close: float,
        day1_vwap: float,
        day1_volume: float,
        day1_gap_pct: float,
        catalyst_type: str,
        catalyst_headline: str,
        catalyst_stars: float,
    ) -> bool:
        """Register a new Day 1 EP or update existing EP lifecycle."""
        clean_sym = ticker.upper().strip()
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ep_date, day_count, is_active FROM episodic_pivots WHERE ticker = ?", (clean_sym,))
                row = cursor.fetchone()

                now_ts = datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S")

                if row is None:
                    # New Day 1 EP
                    cursor.execute("""
                    INSERT INTO episodic_pivots (
                        ticker, ep_date, day_count, day1_open, day1_high, day1_low, day1_close,
                        day1_vwap, day1_volume, day1_gap_pct, catalyst_type, catalyst_headline,
                        catalyst_stars, is_active, last_seen_date, updated_at
                    ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    """, (
                        clean_sym, ep_date, day1_open, day1_high, day1_low, day1_close,
                        day1_vwap, day1_volume, day1_gap_pct, catalyst_type, catalyst_headline,
                        catalyst_stars, ep_date, now_ts
                    ))
                else:
                    orig_ep_date = row["ep_date"]
                    # Calculate date distance to avoid resetting an active multi-day EP cycle
                    try:
                        d1 = datetime.datetime.strptime(orig_ep_date, "%Y-%m-%d").date()
                        d2 = datetime.datetime.strptime(ep_date, "%Y-%m-%d").date()
                        days_diff = (d2 - d1).days
                    except Exception:
                        days_diff = 100

                    # Only reset to Day 1 if the previous EP was > 10 days ago (a new quarterly earnings cycle)
                    if days_diff > 10:
                        cursor.execute("""
                        UPDATE episodic_pivots SET
                            ep_date = ?,
                            day_count = 1,
                            day1_open = ?,
                            day1_high = ?,
                            day1_low = ?,
                            day1_close = ?,
                            day1_vwap = ?,
                            day1_volume = ?,
                            day1_gap_pct = ?,
                            catalyst_type = ?,
                            catalyst_headline = ?,
                            catalyst_stars = ?,
                            is_active = 1,
                            last_seen_date = ?,
                            updated_at = ?
                        WHERE ticker = ?
                        """, (
                            ep_date, day1_open, day1_high, day1_low, day1_close,
                            day1_vwap, day1_volume, day1_gap_pct, catalyst_type, catalyst_headline,
                            catalyst_stars, ep_date, now_ts, clean_sym
                        ))
                    else:
                        # Same EP cycle (Days 2 to 5): do NOT overwrite ep_date or day_count with Day 1!
                        cursor.execute("""
                        UPDATE episodic_pivots SET
                            last_seen_date = ?,
                            updated_at = ?
                        WHERE ticker = ?
                        """, (ep_date, now_ts, clean_sym))

                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error registering EP for {ticker}: {e}")
            return False

    def advance_ep_day_counts(self, current_date_str: str) -> None:
        """Advance day count for active EPs if date has progressed."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ticker, ep_date, day_count, last_seen_date FROM episodic_pivots WHERE is_active = 1")
                rows = cursor.fetchall()
                for r in rows:
                    sym = r["ticker"]
                    ep_date = r["ep_date"]
                    day_cnt = r["day_count"]

                    if current_date_str > ep_date:
                        try:
                            d1 = datetime.datetime.strptime(ep_date, "%Y-%m-%d").date()
                            d2 = datetime.datetime.strptime(current_date_str, "%Y-%m-%d").date()
                            calendar_days = (d2 - d1).days
                            new_cnt = max(2, calendar_days + 1)
                        except Exception:
                            new_cnt = day_cnt + 1

                        # If past 7 calendar/trading days, deactivate EP lifecycle
                        is_active = 1 if new_cnt <= 7 else 0
                        cursor.execute("""
                        UPDATE episodic_pivots SET
                            day_count = ?,
                            is_active = ?,
                            last_seen_date = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE ticker = ?
                        """, (new_cnt, is_active, current_date_str, sym))
                conn.commit()
        except Exception as e:
            logger.error(f"Error advancing EP day counts: {e}")

    def get_active_eps(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all active EP records keyed by ticker."""
        active_eps = {}
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT ticker, ep_date, day_count, day1_open, day1_high, day1_low, day1_close,
                       day1_vwap, day1_volume, day1_gap_pct, catalyst_type, catalyst_headline,
                       catalyst_stars, is_active
                FROM episodic_pivots
                WHERE is_active = 1
                """)
                for r in cursor.fetchall():
                    active_eps[r["ticker"]] = dict(r)
        except Exception as e:
            logger.error(f"Error fetching active EPs: {e}")
        return active_eps

    def record_daily_bar(
        self,
        ticker: str,
        trade_date: str,
        open_p: float,
        high_p: float,
        low_p: float,
        close_p: float,
        volume: float,
        vwap: float = 0.0,
        pct_change: float = 0.0
    ) -> None:
        """Record or update daily price bar and update streak state."""
        clean_sym = ticker.upper().strip()
        is_green = 1 if pct_change > 0 or (open_p > 0 and close_p >= open_p) else 0
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO daily_bars (ticker, trade_date, open, high, low, close, volume, vwap, pct_change, is_green)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker, trade_date) DO UPDATE SET
                    open = excluded.open,
                    high = excluded.high,
                    low = excluded.low,
                    close = excluded.close,
                    volume = excluded.volume,
                    vwap = excluded.vwap,
                    pct_change = excluded.pct_change,
                    is_green = excluded.is_green
                """, (clean_sym, trade_date, open_p, high_p, low_p, close_p, volume, vwap, pct_change, is_green))

                # Update streak table
                cursor.execute("SELECT streak_direction, streak_count, last_trade_date FROM streaks WHERE ticker = ?", (clean_sym,))
                streak_row = cursor.fetchone()

                current_dir = "UP" if is_green == 1 else "DOWN"

                if streak_row is None:
                    cursor.execute("""
                    INSERT INTO streaks (ticker, streak_direction, streak_count, last_trade_date)
                    VALUES (?, ?, 1, ?)
                    """, (clean_sym, current_dir, trade_date))
                else:
                    prev_dir = streak_row["streak_direction"]
                    prev_count = streak_row["streak_count"]
                    last_date = streak_row["last_trade_date"]

                    if trade_date != last_date:
                        if current_dir == prev_dir:
                            new_count = prev_count + 1
                        else:
                            new_count = 1
                        cursor.execute("""
                        UPDATE streaks SET
                            streak_direction = ?,
                            streak_count = ?,
                            last_trade_date = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE ticker = ?
                        """, (current_dir, new_count, trade_date, clean_sym))

                conn.commit()
        except Exception as e:
            logger.error(f"Error recording daily bar for {ticker}: {e}")

    def get_streak_info(self, ticker: str) -> Dict[str, Any]:
        """Fetch current consecutive streak info for a ticker."""
        clean_sym = ticker.upper().strip()
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT streak_direction, streak_count, last_trade_date FROM streaks WHERE ticker = ?", (clean_sym,))
                row = cursor.fetchone()
                if row:
                    return {
                        "direction": row["streak_direction"],
                        "count": row["streak_count"],
                        "last_date": row["last_trade_date"]
                    }
        except Exception as e:
            logger.error(f"Error getting streak for {ticker}: {e}")
        return {"direction": "NEUTRAL", "count": 0, "last_date": ""}

    def get_recent_bars(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent daily bars for pattern calculation (e.g. 5-day range, VCP swings)."""
        clean_sym = ticker.upper().strip()
        bars = []
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT trade_date, open, high, low, close, volume, vwap, pct_change, is_green
                FROM daily_bars
                WHERE ticker = ?
                ORDER BY trade_date DESC
                LIMIT ?
                """, (clean_sym, limit))
                for r in cursor.fetchall():
                    bars.append(dict(r))
        except Exception as e:
            logger.error(f"Error getting bars for {ticker}: {e}")
        return bars

    def backfill_historical_eps(self, tickers: List[str], lookback_days: int = 5) -> int:
        """Scan historical daily bars over past lookback_days to seed historical EP Day 1s into SQLite database."""
        logger.info(f"Seeding historical Episodic Pivots across {len(tickers)} tickers (Past {lookback_days} trading days)...")
        inserted = 0
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import yfinance as yf

        def _check_ticker(ticker: str):
            clean = ticker.split(":")[-1].upper().strip()
            try:
                stock = yf.Ticker(clean)
                df = stock.history(period="20d", interval="1d")
                if df.empty or len(df) < 7:
                    return None
                candidates = []
                for i in range(max(1, len(df) - lookback_days - 1), len(df) - 1):
                    row = df.iloc[i]
                    prev_row = df.iloc[i - 1]
                    adv = df["Volume"].iloc[max(0, i - 10):i].mean()
                    if adv <= 0:
                        continue
                    gap = ((row["Open"] - prev_row["Close"]) / prev_row["Close"]) * 100.0
                    run = ((row["Close"] - row["Open"]) / row["Open"]) * 100.0
                    rvol = row["Volume"] / adv
                    
                    if (gap >= 7.0 or run >= 4.0) and rvol >= 1.35 and row["Close"] >= prev_row["Close"]:
                        dt_str = df.index[i].strftime("%Y-%m-%d")
                        days_elapsed = (len(df) - 1) - i + 1
                        vwap_est = (row["High"] + row["Low"] + row["Close"]) / 3.0
                        candidates.append({
                            "ticker": clean,
                            "ep_date": dt_str,
                            "day_count": days_elapsed,
                            "day1_open": float(row["Open"]),
                            "day1_high": float(row["High"]),
                            "day1_low": float(row["Low"]),
                            "day1_close": float(row["Close"]),
                            "day1_vwap": float(vwap_est),
                            "day1_volume": float(row["Volume"]),
                            "day1_gap_pct": float(gap),
                        })
                if candidates:
                    return candidates[-1]
            except Exception:
                pass
            return None

        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_sym = {executor.submit(_check_ticker, t): t for t in tickers}
            for future in as_completed(future_to_sym):
                try:
                    res = future.result()
                    if res:
                        sym = res["ticker"]
                        with self._get_conn() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                            INSERT INTO episodic_pivots (
                                ticker, ep_date, day_count, day1_open, day1_high, day1_low, day1_close,
                                day1_vwap, day1_volume, day1_gap_pct, catalyst_type, catalyst_headline,
                                catalyst_stars, is_active, last_seen_date, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
                            ON CONFLICT(ticker) DO UPDATE SET
                                ep_date = excluded.ep_date,
                                day_count = excluded.day_count,
                                day1_open = excluded.day1_open,
                                day1_high = excluded.day1_high,
                                day1_low = excluded.day1_low,
                                day1_close = excluded.day1_close,
                                day1_vwap = excluded.day1_vwap,
                                day1_volume = excluded.day1_volume,
                                day1_gap_pct = excluded.day1_gap_pct,
                                catalyst_type = excluded.catalyst_type,
                                catalyst_headline = excluded.catalyst_headline,
                                catalyst_stars = excluded.catalyst_stars,
                                is_active = 1,
                                last_seen_date = excluded.last_seen_date,
                                updated_at = CURRENT_TIMESTAMP
                            """, (
                                sym, res["ep_date"], res["day_count"], res["day1_open"], res["day1_high"],
                                res["day1_low"], res["day1_close"], res["day1_vwap"], res["day1_volume"],
                                res["day1_gap_pct"], "Momentum Breakout", f"{sym} Multi-Day Expansion", 3.5, res["ep_date"]
                            ))
                            conn.commit()
                        inserted += 1
                except Exception as e:
                    logger.debug(f"Error saving backfilled EP: {e}")

        logger.info(f"Successfully seeded {inserted} historical EPs into SQLite database.")
        return inserted

state_mgr = StateManager()
