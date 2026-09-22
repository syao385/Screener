"""Thesis Lake & Analytical Schemas for Phase 6 (Skills 13, 08, 14).
===================================================================
Manages DuckDB persistence in data/attribution_lake.duckdb and SQLite sync
in data/portfolio_monitor.db:
  - Table: news_pulse_events (Residual attribution, signal score, stealth flag)
  - Table: thesis_contracts (Tactical vs Core, entry, stops, 8Q anchors)
  - Table: thesis_drift_history (Quarterly Health Score delta & drift metrics)
"""

import os
import json
import sqlite3
import logging
import datetime
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional

import duckdb
from config import ATTRIBUTION_DB_PATH, DATA_DIR, TZ_EST

logger = logging.getLogger("thesis_lake")
SQLITE_MONITOR_DB = DATA_DIR / "portfolio_monitor.db"


class ThesisLake:
    """Analytical storage and real-time synchronization engine for Theses & News."""

    def __init__(self, db_path: Path = ATTRIBUTION_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = None
        self.initialize_schema()
        self.sync_sqlite_columns()

    def get_connection(self, read_only: bool = False):
        """Acquire thread-safe DuckDB connection with fallback."""
        with self._lock:
            if self._conn is None:
                try:
                    self._conn = duckdb.connect(str(self.db_path), read_only=read_only)
                except Exception as e:
                    if not read_only:
                        logger.warning(f"DuckDB locked, falling back to read_only=True: {e}")
                        try:
                            self._conn = duckdb.connect(str(self.db_path), read_only=True)
                        except Exception:
                            self._conn = duckdb.connect(":memory:")
                    else:
                        try:
                            self._conn = duckdb.connect(str(self.db_path), read_only=True)
                        except Exception:
                            self._conn = duckdb.connect(":memory:")
            return self._conn

    def close(self):
        with self._lock:
            if self._conn is not None:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None

    def initialize_schema(self):
        """Initialize Phase 6 analytical schemas in DuckDB."""
        try:
            conn = self.get_connection(read_only=False)
            # 1. News Pulse Events
            conn.execute("""
                CREATE TABLE IF NOT EXISTS news_pulse_events (
                    event_id VARCHAR PRIMARY KEY,
                    symbol VARCHAR NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    trigger_type VARCHAR,
                    return_1d DOUBLE,
                    market_beta_return DOUBLE,
                    sector_beta_return DOUBLE,
                    residual_return DOUBLE,
                    residual_zscore DOUBLE,
                    composite_signal_score DOUBLE,
                    primary_headline VARCHAR,
                    primary_source VARCHAR,
                    authority_score DOUBLE,
                    novelty_score DOUBLE,
                    attribution_weight DOUBLE,
                    is_stealth BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Master Thesis Contracts
            conn.execute("""
                CREATE TABLE IF NOT EXISTS thesis_contracts (
                    thesis_id VARCHAR PRIMARY KEY,
                    symbol VARCHAR NOT NULL,
                    promotion_stage VARCHAR NOT NULL,
                    established_date DATE NOT NULL,
                    origin_archetype VARCHAR NOT NULL,
                    entry_price DOUBLE NOT NULL,
                    current_shares DOUBLE NOT NULL,
                    target_1_price DOUBLE,
                    target_2_price DOUBLE,
                    hard_stop_price DOUBLE,
                    dynamic_stop_price DOUBLE,
                    trailing_rule VARCHAR,
                    moat_description VARCHAR,
                    sloan_accrual_baseline DOUBLE,
                    fcf_conversion_baseline DOUBLE,
                    health_score DOUBLE DEFAULT 10.0,
                    status VARCHAR DEFAULT 'ACTIVE',
                    last_review_date DATE
                );
            """)

            # 3. Fleet-Wide Thesis Quarterly Drift History
            conn.execute("""
                CREATE TABLE IF NOT EXISTS thesis_drift_history (
                    drift_id VARCHAR PRIMARY KEY,
                    thesis_id VARCHAR,
                    symbol VARCHAR NOT NULL,
                    review_date DATE NOT NULL,
                    prior_health_score DOUBLE,
                    new_health_score DOUBLE,
                    broken_assumptions INTEGER,
                    breached_assumptions INTEGER,
                    redlines_triggered INTEGER,
                    quantitative_drift_score DOUBLE,
                    semantic_similarity DOUBLE,
                    action_recommended VARCHAR,
                    action_executed VARCHAR,
                    filing_quarter VARCHAR
                );
            """)

            # 4. Daily Sentiment Snapshots (Multi-Source Horizon Delta Tracking)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_sentiment_snapshots (
                    snapshot_id VARCHAR PRIMARY KEY,
                    symbol VARCHAR NOT NULL,
                    snapshot_date DATE NOT NULL,
                    composite_sentiment DOUBLE,
                    sec_sentiment DOUBLE,
                    media_sentiment DOUBLE,
                    social_sentiment DOUBLE,
                    delta_sentiment_7d DOUBLE,
                    divergence_regime VARCHAR,
                    price_change_7d DOUBLE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- 5. Institutional Deep Research Theses (Phase 7 / Skill 04)
                CREATE TABLE IF NOT EXISTS deep_research_theses (
                    research_id VARCHAR PRIMARY KEY,
                    symbol VARCHAR NOT NULL,
                    research_date DATE NOT NULL,
                    composite_score DOUBLE NOT NULL,
                    composite_stars DOUBLE NOT NULL,
                    verdict VARCHAR NOT NULL,
                    sizing_multiplier DOUBLE NOT NULL,
                    duan_stars DOUBLE,
                    buffett_stars DOUBLE,
                    munger_stars DOUBLE,
                    lilu_stars DOUBLE,
                    divergence_alert BOOLEAN,
                    hard_veto_triggered BOOLEAN,
                    sloan_accrual DOUBLE,
                    fcf_conversion DOUBLE,
                    piotroski_f_score INTEGER,
                    beneish_m_score DOUBLE,
                    implied_terminal_growth DOUBLE,
                    fair_value_base DOUBLE,
                    entry_target_price DOUBLE,
                    invalidation_stop_price DOUBLE,
                    dossier_path VARCHAR,
                    raw_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            logger.info("Initialized Phase 6 & Deep Research DuckDB schemas successfully.")
        except Exception as e:
            logger.error(f"Error initializing DuckDB thesis schema: {e}")

    def sync_sqlite_columns(self):
        """Ensure SQLite position_tracker has Phase 6 lifecycle and news columns."""
        if not SQLITE_MONITOR_DB.exists():
            return

        try:
            conn = sqlite3.connect(str(SQLITE_MONITOR_DB))
            cursor = conn.cursor()

            # Check existing columns
            cursor.execute("PRAGMA table_info(position_tracker);")
            columns = [info[1] for info in cursor.fetchall()]

            new_columns = [
                ("lifecycle_stage", "TEXT DEFAULT 'TACTICAL_SETUP'"),
                ("thesis_health_score", "REAL DEFAULT 10.0"),
                ("drift_status", "TEXT DEFAULT 'NO_DRIFT'"),
                ("last_news_signal", "REAL DEFAULT 0.0"),
                ("last_news_attribution", "TEXT DEFAULT 'NONE'"),
            ]

            for col_name, col_type in new_columns:
                if col_name not in columns:
                    cursor.execute(f"ALTER TABLE position_tracker ADD COLUMN {col_name} {col_type};")
                    logger.info(f"Added SQLite column {col_name} to position_tracker.")

            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Note on SQLite schema sync: {e}")

    def record_news_event(self, event_data: Dict[str, Any]) -> bool:
        """Insert news pulse event into DuckDB."""
        try:
            conn = self.get_connection(read_only=False)
            now_ts = datetime.datetime.now(TZ_EST)
            event_id = f"NEWS_{event_data.get('symbol', 'UNK')}_{now_ts.strftime('%Y%m%d%H%M%S%f')}"

            residuals = event_data.get("residuals", {})
            signal = event_data.get("signal", {})
            attr = event_data.get("attribution", {})

            conn.execute("""
                INSERT OR REPLACE INTO news_pulse_events (
                    event_id, symbol, timestamp, trigger_type, return_1d,
                    market_beta_return, sector_beta_return, residual_return, residual_zscore,
                    composite_signal_score, primary_headline, primary_source,
                    authority_score, novelty_score, attribution_weight, is_stealth
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                event_data.get("symbol", ""),
                now_ts,
                event_data.get("trigger_type", "PORTFOLIO_MOVER"),
                residuals.get("stock_return", 0.0),
                residuals.get("market_component", 0.0),
                residuals.get("sector_component", 0.0),
                residuals.get("residual_return", 0.0),
                residuals.get("residual_zscore", 0.0),
                signal.get("composite_score", 0.0),
                attr.get("event_name", ""),
                attr.get("source", ""),
                signal.get("authority", 70.0),
                signal.get("novelty", 80.0),
                attr.get("attribution_weight", 0.20),
                attr.get("is_stealth", False)
            ))
            return True
        except Exception as e:
            logger.error(f"Error inserting news event: {e}")
            return False

    def get_recent_news_events(self, limit: int = 15, include_tests: bool = False) -> List[Dict[str, Any]]:
        """Fetch latest news pulse events for UI rendering (excluding test fixtures unless requested)."""
        try:
            conn = self.get_connection(read_only=True)
            filter_sql = "" if include_tests else "WHERE symbol NOT LIKE 'TEST%' AND LENGTH(symbol) <= 5 AND NOT regexp_matches(symbol, '[0-9]')"
            res = conn.execute(f"""
                SELECT symbol, timestamp, trigger_type, return_1d, residual_return,
                       residual_zscore, composite_signal_score, primary_headline,
                       primary_source, attribution_weight, is_stealth
                FROM news_pulse_events
                {filter_sql}
                ORDER BY timestamp DESC
                LIMIT {limit}
            """).fetchall()
            if not res and not include_tests:
                # Fallback to all if empty
                res = conn.execute(f"""
                    SELECT symbol, timestamp, trigger_type, return_1d, residual_return,
                           residual_zscore, composite_signal_score, primary_headline,
                           primary_source, attribution_weight, is_stealth
                    FROM news_pulse_events
                    ORDER BY timestamp DESC
                    LIMIT {limit}
                """).fetchall()

            events = []
            for row in res:
                events.append({
                    "symbol": row[0],
                    "timestamp": str(row[1])[:19],
                    "trigger_type": row[2],
                    "return_1d_pct": round(row[3] * 100.0, 1),
                    "residual_return_pct": round(row[4] * 100.0, 1),
                    "residual_zscore": round(row[5], 2),
                    "signal_score": round(row[6], 1),
                    "headline": row[7],
                    "source": row[8],
                    "attribution_weight": round(row[9] * 100.0, 0),
                    "is_stealth": bool(row[10]),
                })
            return events
        except Exception as e:
            logger.error(f"Error fetching news events: {e}")
            return []

    def record_thesis_contract(self, contract: Dict[str, Any]) -> bool:
        """Upsert master thesis contract in DuckDB."""
        try:
            conn = self.get_connection(read_only=False)
            thesis_id = f"THESIS_{contract.get('symbol', 'UNK')}"
            conn.execute("""
                INSERT OR REPLACE INTO thesis_contracts (
                    thesis_id, symbol, promotion_stage, established_date, origin_archetype,
                    entry_price, current_shares, target_1_price, target_2_price,
                    hard_stop_price, dynamic_stop_price, trailing_rule, moat_description,
                    sloan_accrual_baseline, fcf_conversion_baseline, health_score,
                    status, last_review_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                thesis_id,
                contract.get("symbol", ""),
                contract.get("promotion_stage", "TACTICAL_SETUP"),
                contract.get("established_date", datetime.date.today()),
                contract.get("origin_archetype", "Stage 2 Pullback & PEAD"),
                float(contract.get("entry_price", 0.0)),
                float(contract.get("current_shares", 0.0)),
                float(contract.get("target_1_price", 0.0)),
                float(contract.get("target_2_price", 0.0)),
                float(contract.get("hard_stop_price", 0.0)),
                float(contract.get("dynamic_stop_price", 0.0)),
                contract.get("trailing_rule", "2.0 * ATR(14)"),
                contract.get("moat_description", ""),
                float(contract.get("sloan_accrual_baseline", 0.0)),
                float(contract.get("fcf_conversion_baseline", 100.0)),
                float(contract.get("health_score", 10.0)),
                contract.get("status", "ACTIVE"),
                datetime.date.today()
            ))
            return True
        except Exception as e:
            logger.error(f"Error recording thesis contract: {e}")
            return False

    def record_drift_event(self, drift_data: Dict[str, Any]) -> bool:
        """Insert thesis drift audit into DuckDB."""
        try:
            conn = self.get_connection(read_only=False)
            now_date = datetime.date.today()
            drift_id = f"DRIFT_{drift_data.get('symbol', 'UNK')}_{now_date.strftime('%Y%m%d')}"
            conn.execute("""
                INSERT OR REPLACE INTO thesis_drift_history (
                    drift_id, thesis_id, symbol, review_date, prior_health_score,
                    new_health_score, broken_assumptions, breached_assumptions,
                    redlines_triggered, quantitative_drift_score, semantic_similarity,
                    action_recommended, action_executed, filing_quarter
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                drift_id,
                f"THESIS_{drift_data.get('symbol', 'UNK')}",
                drift_data.get("symbol", ""),
                now_date,
                float(drift_data.get("prior_health_score", 10.0)),
                float(drift_data.get("new_health_score", 10.0)),
                int(drift_data.get("broken_assumptions", 0)),
                int(drift_data.get("breached_assumptions", 0)),
                int(drift_data.get("redlines_triggered", 0)),
                float(drift_data.get("quantitative_drift_score", 0.0)),
                float(drift_data.get("semantic_similarity", 1.0)),
                drift_data.get("action_recommended", "HOLD_STAGE"),
                drift_data.get("action_executed", "NONE"),
                drift_data.get("filing_quarter", "CURRENT")
            ))
            return True
        except Exception as e:
            logger.error(f"Error recording drift event: {e}")
            return False

    def get_drift_history(self, symbol: Optional[str] = None, limit: int = 15) -> List[Dict[str, Any]]:
        """Fetch drift history records for UI or diagnostic inspection."""
        try:
            conn = self.get_connection(read_only=True)
            if symbol:
                res = conn.execute(f"""
                    SELECT symbol, review_date, prior_health_score, new_health_score,
                           quantitative_drift_score, action_recommended
                    FROM thesis_drift_history
                    WHERE symbol = ?
                    ORDER BY review_date DESC
                    LIMIT {limit}
                """, (symbol,)).fetchall()
            else:
                res = conn.execute(f"""
                    SELECT symbol, review_date, prior_health_score, new_health_score,
                           quantitative_drift_score, action_recommended
                    FROM thesis_drift_history
                    ORDER BY review_date DESC
                    LIMIT {limit}
                """).fetchall()

            history = []
            for row in res:
                history.append({
                    "symbol": row[0],
                    "review_date": str(row[1]),
                    "prior_health_score": round(row[2], 1),
                    "new_health_score": round(row[3], 1),
                    "drift_score": round(row[4], 1),
                    "action_recommended": row[5]
                })
            return history
        except Exception as e:
            logger.error(f"Error fetching drift history: {e}")
            return []

    def record_sentiment_snapshot(self, snapshot_data: Dict[str, Any]) -> bool:
        """Insert or replace daily sentiment snapshot for a symbol."""
        try:
            conn = self.get_connection(read_only=False)
            now_date = datetime.datetime.now(TZ_EST).date()
            symbol = snapshot_data.get("symbol", "UNK")
            snapshot_id = f"SENT_{symbol}_{now_date.strftime('%Y%m%d')}"

            conn.execute("""
                INSERT OR REPLACE INTO daily_sentiment_snapshots (
                    snapshot_id, symbol, snapshot_date, composite_sentiment,
                    sec_sentiment, media_sentiment, social_sentiment,
                    delta_sentiment_7d, divergence_regime, price_change_7d
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id,
                symbol,
                now_date,
                float(snapshot_data.get("composite_sentiment", 0.0)),
                float(snapshot_data.get("sec_sentiment", 0.0)),
                float(snapshot_data.get("media_sentiment", 0.0)),
                float(snapshot_data.get("social_sentiment", 0.0)),
                float(snapshot_data.get("delta_sentiment_7d", 0.0)),
                snapshot_data.get("divergence_regime", "NARRATIVE_STABLE"),
                float(snapshot_data.get("price_change_7d", 0.0)),
            ))
            return True
        except Exception as e:
            logger.error(f"Error recording sentiment snapshot: {e}")
            return False

    def get_sentiment_trend(self, symbol: str, days: int = 7) -> List[Dict[str, Any]]:
        """Retrieve recent sentiment snapshots for trend and divergence analysis."""
        try:
            conn = self.get_connection(read_only=True)
            res = conn.execute(f"""
                SELECT symbol, snapshot_date, composite_sentiment, sec_sentiment,
                       media_sentiment, social_sentiment, delta_sentiment_7d,
                       divergence_regime, price_change_7d
                FROM daily_sentiment_snapshots
                WHERE symbol = ?
                ORDER BY snapshot_date DESC
                LIMIT {days}
            """, (symbol,)).fetchall()

            snapshots = []
            for row in res:
                snapshots.append({
                    "symbol": row[0],
                    "date": str(row[1]),
                    "composite_sentiment": round(row[2], 2),
                    "sec_sentiment": round(row[3], 2),
                    "media_sentiment": round(row[4], 2),
                    "social_sentiment": round(row[5], 2),
                    "delta_sentiment_7d": round(row[6], 2),
                    "divergence_regime": row[7],
                    "price_change_7d": round(row[8], 2),
                })
            return snapshots
        except Exception as e:
            logger.error(f"Error fetching sentiment trend: {e}")
            return []

    def record_deep_research_thesis(self, thesis_data: Dict[str, Any]) -> bool:
        """Insert or replace institutional deep research thesis into DuckDB with JSON mirror."""
        symbol = str(thesis_data.get("symbol", "UNK")).upper().strip()
        now_date = datetime.datetime.now(TZ_EST).date()
        research_id = f"DEEP_{symbol}_{now_date.strftime('%Y%m%d')}"

        # 1. Always mirror to disk JSON store to guarantee resilience against multi-process locks
        try:
            deep_dir = DATA_DIR / "deep_research"
            deep_dir.mkdir(parents=True, exist_ok=True)
            json_file = deep_dir / f"{symbol}.json"
            enriched = dict(thesis_data)
            enriched["research_id"] = research_id
            enriched["research_date"] = str(now_date)
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(enriched, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Note on JSON mirror for deep research {symbol}: {e}")

        # 2. Persist to DuckDB lake
        try:
            conn = self.get_connection(read_only=False)
            conn.execute("""
                INSERT OR REPLACE INTO deep_research_theses (
                    research_id, symbol, research_date, composite_score,
                    composite_stars, verdict, sizing_multiplier, duan_stars,
                    buffett_stars, munger_stars, lilu_stars, divergence_alert,
                    hard_veto_triggered, sloan_accrual, fcf_conversion,
                    piotroski_f_score, beneish_m_score, implied_terminal_growth,
                    fair_value_base, entry_target_price, invalidation_stop_price,
                    dossier_path, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                research_id,
                symbol,
                now_date,
                float(thesis_data.get("composite_score", 0.0)),
                float(thesis_data.get("composite_stars", 0.0)),
                str(thesis_data.get("verdict", "NEUTRAL")),
                float(thesis_data.get("sizing_multiplier", 1.0)),
                float(thesis_data.get("duan_stars", 0.0)),
                float(thesis_data.get("buffett_stars", 0.0)),
                float(thesis_data.get("munger_stars", 0.0)),
                float(thesis_data.get("lilu_stars", 0.0)),
                bool(thesis_data.get("divergence_alert", False)),
                bool(thesis_data.get("hard_veto_triggered", False)),
                float(thesis_data.get("sloan_accrual", 0.0)),
                float(thesis_data.get("fcf_conversion", 0.0)),
                int(thesis_data.get("piotroski_f_score", 0)),
                float(thesis_data.get("beneish_m_score", 0.0)),
                float(thesis_data.get("implied_terminal_growth", 0.0)),
                float(thesis_data.get("fair_value_base", 0.0)),
                float(thesis_data.get("entry_target_price", 0.0)),
                float(thesis_data.get("invalidation_stop_price", 0.0)),
                str(thesis_data.get("dossier_path", "")),
                json.dumps(thesis_data, default=str),
            ))
            logger.info(f"Recorded Deep Research thesis for {symbol} ({research_id}) into DuckDB.")
            return True
        except Exception as e:
            logger.warning(f"DuckDB lock on deep research thesis insert (mirrored in JSON): {e}")
            return True

    def get_deep_research_thesis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Retrieve most recent deep research thesis for a symbol (DuckDB + JSON fallback)."""
        symbol = symbol.upper().strip()
        try:
            conn = self.get_connection(read_only=True)
            res = conn.execute("""
                SELECT research_id, symbol, research_date, composite_score,
                       composite_stars, verdict, sizing_multiplier, duan_stars,
                       buffett_stars, munger_stars, lilu_stars, divergence_alert,
                       hard_veto_triggered, sloan_accrual, fcf_conversion,
                       piotroski_f_score, beneish_m_score, implied_terminal_growth,
                       fair_value_base, entry_target_price, invalidation_stop_price,
                       dossier_path, raw_json
                FROM deep_research_theses
                WHERE symbol = ?
                ORDER BY research_date DESC
                LIMIT 1
            """, (symbol,)).fetchone()

            if res:
                return {
                    "research_id": res[0],
                    "symbol": res[1],
                    "research_date": str(res[2]),
                    "composite_score": res[3],
                    "composite_stars": res[4],
                    "verdict": res[5],
                    "sizing_multiplier": res[6],
                    "duan_stars": res[7],
                    "buffett_stars": res[8],
                    "munger_stars": res[9],
                    "lilu_stars": res[10],
                    "divergence_alert": bool(res[11]),
                    "hard_veto_triggered": bool(res[12]),
                    "sloan_accrual": res[13],
                    "fcf_conversion": res[14],
                    "piotroski_f_score": res[15],
                    "beneish_m_score": res[16],
                    "implied_terminal_growth": res[17],
                    "fair_value_base": res[18],
                    "entry_target_price": res[19],
                    "invalidation_stop_price": res[20],
                    "dossier_path": res[21],
                    "details": json.loads(res[22]) if res[22] else {}
                }
        except Exception as e:
            logger.warning(f"Error querying DuckDB for deep research {symbol}: {e}")

        # JSON fallback if DuckDB file was locked
        try:
            json_file = DATA_DIR / "deep_research" / f"{symbol}.json"
            if json_file.exists():
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return {
                    "research_id": data.get("research_id", f"DEEP_{symbol}"),
                    "symbol": symbol,
                    "research_date": data.get("research_date", ""),
                    "composite_score": data.get("composite_score", 0.0),
                    "composite_stars": data.get("composite_stars", 0.0),
                    "verdict": data.get("verdict", ""),
                    "sizing_multiplier": data.get("sizing_multiplier", 1.0),
                    "duan_stars": data.get("duan_stars", 0.0),
                    "buffett_stars": data.get("buffett_stars", 0.0),
                    "munger_stars": data.get("munger_stars", 0.0),
                    "lilu_stars": data.get("lilu_stars", 0.0),
                    "divergence_alert": data.get("divergence_alert", False),
                    "hard_veto_triggered": data.get("hard_veto_triggered", False),
                    "sloan_accrual": data.get("sloan_accrual", 0.0),
                    "fcf_conversion": data.get("fcf_conversion", 0.0),
                    "piotroski_f_score": data.get("piotroski_f_score", 0),
                    "beneish_m_score": data.get("beneish_m_score", 0.0),
                    "implied_terminal_growth": data.get("implied_terminal_growth", 0.0),
                    "fair_value_base": data.get("fair_value_base", 0.0),
                    "entry_target_price": data.get("entry_target_price", 0.0),
                    "invalidation_stop_price": data.get("invalidation_stop_price", 0.0),
                    "dossier_path": data.get("dossier_path", ""),
                    "details": data,
                }
        except Exception as e:
            logger.error(f"Error reading JSON fallback for deep research {symbol}: {e}")

        return None

    def get_latest_deep_research_theses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch latest deep research theses across the universe."""
        try:
            conn = self.get_connection(read_only=True)
            res = conn.execute(f"""
                SELECT research_id, symbol, research_date, composite_score,
                       composite_stars, verdict, sizing_multiplier,
                       divergence_alert, hard_veto_triggered, entry_target_price,
                       invalidation_stop_price, dossier_path
                FROM deep_research_theses
                ORDER BY research_date DESC
                LIMIT {limit}
            """).fetchall()

            theses = []
            for row in res:
                theses.append({
                    "research_id": row[0],
                    "symbol": row[1],
                    "research_date": str(row[2]),
                    "composite_score": row[3],
                    "composite_stars": row[4],
                    "verdict": row[5],
                    "sizing_multiplier": row[6],
                    "divergence_alert": bool(row[7]),
                    "hard_veto_triggered": bool(row[8]),
                    "entry_target_price": row[9],
                    "invalidation_stop_price": row[10],
                    "dossier_path": row[11],
                })
            return theses
        except Exception as e:
            logger.error(f"Error fetching latest deep research theses: {e}")
            return []


# Global singleton instance
thesis_lake = ThesisLake()


