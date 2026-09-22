"""Alpha Attribution Data Lake Storage Layer (Phase 4).
DuckDB analytical storage for:
  1. Trade Ledger (Synthesized baseline holdings + forward incremental fills)
  2. Daily Portfolio Snapshots & NAV Watermarks
  3. Benchmark Quotes & Relative Return Tracking
  4. Auto-Tuning State & Calibrated Multipliers
"""

import os
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import duckdb

from config import (
    DATA_DIR,
    ATTRIBUTION_DB_PATH,
    ENABLE_FORWARD_INCREMENTAL_FILLS,
    TUNING_MIN_CLAMP,
    TUNING_MAX_CLAMP,
    TZ_EST,
)

logger = logging.getLogger("attribution_lake")


class AttributionLake:
    """Institutional Analytical Data Lake for Alpha Attribution & Trade Logging."""

    def __init__(self, db_path: Path = ATTRIBUTION_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.forward_fills_file = DATA_DIR / "forward_fills_state.json"
        import threading
        self._lock = threading.Lock()
        self._conn = None
        self._ensure_forward_fills_state()
        self.initialize_schema()

    def _ensure_forward_fills_state(self):
        """Ensure local toggle state file exists for forward fills."""
        if not self.forward_fills_file.exists():
            state = {
                "forward_fills_enabled": ENABLE_FORWARD_INCREMENTAL_FILLS,  # default False
                "last_toggled": datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET"),
                "manual_overrides_count": 0,
            }
            try:
                with open(self.forward_fills_file, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2)
            except Exception as e:
                logger.error(f"Error initializing forward fills state: {e}")

    def is_forward_fills_enabled(self) -> bool:
        """Check if forward incremental fills are currently enabled."""
        if self.forward_fills_file.exists():
            try:
                with open(self.forward_fills_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return bool(data.get("forward_fills_enabled", False))
            except Exception:
                pass
        return ENABLE_FORWARD_INCREMENTAL_FILLS

    def set_forward_fills_enabled(self, enabled: bool) -> bool:
        """Toggle forward incremental fills on or off."""
        try:
            state = {
                "forward_fills_enabled": bool(enabled),
                "last_toggled": datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET"),
            }
            with open(self.forward_fills_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            logger.info(f"Forward incremental fills set to: {enabled}")
            return True
        except Exception as e:
            logger.error(f"Failed to set forward fills enabled: {e}")
            return False

    def get_connection(self, read_only: bool = False):
        """Acquire a resilient, thread-safe DuckDB connection with in-memory fallback if locked."""
        with self._lock:
            if self._conn is None:
                try:
                    self._conn = duckdb.connect(str(self.db_path), read_only=read_only)
                except Exception as e:
                    if not read_only:
                        logger.debug(f"DuckDB read-write locked by active PID. Trying read_only: {e}")
                        try:
                            self._conn = duckdb.connect(str(self.db_path), read_only=True)
                        except Exception as e2:
                            logger.debug(f"DuckDB read_only locked by active PID. Using in-memory fallback: {e2}")
                            self._conn = duckdb.connect(":memory:")
                    else:
                        logger.debug(f"DuckDB locked by active PID. Using in-memory fallback: {e}")
                        self._conn = duckdb.connect(":memory:")
            return self._conn

    def close(self):
        """Close connection if open."""
        with self._lock:
            if self._conn is not None:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None

    def initialize_schema(self):
        """Initialize all DuckDB analytical tables."""
        conn = None
        try:
            conn = self.get_connection(read_only=False)
            
            # 1. Trade Ledger
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_ledger (
                    trade_id VARCHAR PRIMARY KEY,
                    timestamp VARCHAR,
                    symbol VARCHAR,
                    side VARCHAR,
                    shares DOUBLE,
                    price DOUBLE,
                    cost_basis DOUBLE,
                    realized_pnl_dollar DOUBLE,
                    realized_pnl_pct DOUBLE,
                    r_multiple DOUBLE,
                    setup_type VARCHAR,
                    conviction_tier VARCHAR,
                    entry_date VARCHAR,
                    exit_date VARCHAR,
                    hold_duration_days INTEGER,
                    exit_reason VARCHAR,
                    is_baseline_synthesis BOOLEAN,
                    account_name VARCHAR,
                    slippage_bps DOUBLE,
                    manual_override BOOLEAN
                )
            """)

            # 2. Portfolio Daily Snapshots
            conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_daily_snapshots (
                    date VARCHAR PRIMARY KEY,
                    nav DOUBLE,
                    cash DOUBLE,
                    equity_value DOUBLE,
                    cash_weight DOUBLE,
                    equity_weight DOUBLE,
                    daily_return_pct DOUBLE,
                    cumulative_return_pct DOUBLE,
                    high_water_mark DOUBLE,
                    drawdown_pct DOUBLE
                )
            """)

            # 3. Benchmark Quotes
            conn.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_quotes (
                    date VARCHAR,
                    symbol VARCHAR,
                    close DOUBLE,
                    daily_return_pct DOUBLE,
                    cumulative_return_pct DOUBLE,
                    PRIMARY KEY (date, symbol)
                )
            """)

            # 4. Tuning State
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tuning_state (
                    parameter_key VARCHAR PRIMARY KEY,
                    parameter_value DOUBLE,
                    clamped_value DOUBLE,
                    min_clamp DOUBLE,
                    max_clamp DOUBLE,
                    last_calibrated VARCHAR,
                    status VARCHAR
                )
            """)

            conn.commit()
            logger.info("Attribution Lake schema initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing Attribution Lake schema: {e}")
        finally:
            pass

    def synthesize_baseline_holdings(self, portfolio_path: Optional[Path] = None, force: bool = False) -> int:
        """Synthesize baseline trades from data/portfolio.json holdings.
        
        Creates deterministic trade ledger entries for all active holdings so that
        factor attribution and historical tracking have full visibility from inception.
        """
        if portfolio_path is None:
            portfolio_path = DATA_DIR / "portfolio.json"

        if not Path(portfolio_path).exists():
            logger.warning(f"Portfolio file not found at {portfolio_path}. Skipping synthesis.")
            return 0

        conn = None
        synthesized_count = 0
        try:
            conn = self.get_connection(read_only=False)

            # Check if baseline trades already exist
            count_res = conn.execute("SELECT COUNT(*) FROM trade_ledger WHERE is_baseline_synthesis = true").fetchone()
            existing_count = count_res[0] if count_res else 0

            if existing_count > 0 and not force:
                logger.info(f"Baseline holdings already synthesized ({existing_count} records). Use force=True to re-synthesize.")
                return existing_count

            if force and existing_count > 0:
                conn.execute("DELETE FROM trade_ledger WHERE is_baseline_synthesis = true")

            with open(portfolio_path, "r", encoding="utf-8") as f:
                port_data = json.load(f)

            positions = port_data.get("positions", [])
            account_name = port_data.get("account_name", "Traditional IRA")
            now_str = datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET")

            for pos in positions:
                sym = pos.get("symbol", "").strip().upper()
                if not sym:
                    continue

                shares = float(pos.get("quantity", 0.0))
                price = float(pos.get("last_price", 0.0))
                avg_cost = float(pos.get("average_cost", price))
                cost_basis = float(pos.get("cost_basis_total", shares * avg_cost))
                pnl_dollar = float(pos.get("total_pnl_dollar", 0.0))
                pnl_pct = float(pos.get("total_pnl_pct", 0.0))
                
                # Estimate R-multiple: Risk unit = entry - stop_loss
                stop_loss = float(pos.get("stop_loss", avg_cost * 0.92))
                risk_unit = avg_cost - stop_loss if (avg_cost - stop_loss) > 0.01 else avg_cost * 0.08
                r_multiple = round((price - avg_cost) / risk_unit, 2) if risk_unit > 0 else 0.0

                strategy_tag = pos.get("strategy_tag", "Core Trend")
                entry_date = pos.get("entry_date", "2026-08-24")

                trade_id = f"BASE_{sym}_{int(shares * 100)}"

                conn.execute("""
                    INSERT OR REPLACE INTO trade_ledger (
                        trade_id, timestamp, symbol, side, shares, price, cost_basis,
                        realized_pnl_dollar, realized_pnl_pct, r_multiple, setup_type,
                        conviction_tier, entry_date, exit_date, hold_duration_days,
                        exit_reason, is_baseline_synthesis, account_name, slippage_bps,
                        manual_override
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    trade_id,
                    now_str,
                    sym,
                    "BUY",
                    shares,
                    price,
                    cost_basis,
                    pnl_dollar,
                    pnl_pct,
                    r_multiple,
                    strategy_tag,
                    "Tier 1" if pnl_pct > 30 else ("Tier 2" if pnl_pct > 0 else "Tier 3"),
                    entry_date,
                    "",
                    10,
                    "OPEN_POSITION",
                    True,
                    account_name,
                    0.0,
                    False,
                ])
                synthesized_count += 1

            conn.commit()
            logger.info(f"Successfully synthesized {synthesized_count} baseline holdings into DuckDB.")
            return synthesized_count
        except Exception as e:
            logger.error(f"Error synthesizing baseline holdings: {e}")
            return 0
        finally:
            pass

    def record_forward_fill(
        self,
        symbol: str,
        side: str,
        shares: float,
        price: float,
        setup_type: str = "BASE_BREAKOUT",
        conviction_tier: str = "Tier 2",
        stop_price: float = 0.0,
        target_price: float = 0.0,
        planned_price: float = 0.0,
        exit_reason: str = "OPEN_POSITION",
        account_name: str = "Traditional IRA",
        manual_override: bool = False,
    ) -> Optional[str]:
        """Record an incremental trade fill.
        
        Enforces user requirement:
        - Forward incremental fills can be turned on and off (default off).
        - Can be manually overridden by user even when global toggle is off.
        """
        is_enabled = self.is_forward_fills_enabled()

        if not is_enabled and not manual_override:
            logger.info(f"Forward incremental fills disabled. Skipping automatic fill for {symbol}. Set manual_override=True to force.")
            return None

        conn = None
        try:
            conn = self.get_connection(read_only=False)
            now_dt = datetime.datetime.now(TZ_EST)
            now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S ET")
            today_str = now_dt.strftime("%Y-%m-%d")

            trade_id = f"FILL_{symbol}_{now_dt.strftime('%Y%m%d_%H%M%S')}"
            cost_basis = round(shares * price, 2)

            # Slippage calculation
            slippage_bps = 0.0
            if planned_price > 0:
                slippage_pct = ((price - planned_price) / planned_price) * 100.0
                slippage_bps = round(slippage_pct * 100.0, 1)

            # R-Multiple calculation for exits or entries
            risk_unit = (price - stop_price) if (price - stop_price) > 0.01 else price * 0.08
            r_multiple = 0.0
            pnl_dollar = 0.0
            pnl_pct = 0.0

            conn.execute("""
                INSERT INTO trade_ledger (
                    trade_id, timestamp, symbol, side, shares, price, cost_basis,
                    realized_pnl_dollar, realized_pnl_pct, r_multiple, setup_type,
                    conviction_tier, entry_date, exit_date, hold_duration_days,
                    exit_reason, is_baseline_synthesis, account_name, slippage_bps,
                    manual_override
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                trade_id,
                now_str,
                symbol.upper(),
                side.upper(),
                shares,
                price,
                cost_basis,
                pnl_dollar,
                pnl_pct,
                r_multiple,
                setup_type,
                conviction_tier,
                today_str,
                today_str if side == "SELL" else "",
                0,
                exit_reason,
                False,
                account_name,
                slippage_bps,
                manual_override,
            ])
            conn.commit()
            logger.info(f"Recorded forward trade fill {trade_id} ({side} {shares} {symbol} @ ${price:.2f}) [Manual Override={manual_override}].")
            return trade_id
        except Exception as e:
            logger.error(f"Error recording forward fill: {e}")
            return None
        finally:
            pass

    def manual_override_fill(
        self,
        symbol: str,
        side: str,
        shares: float,
        price: float,
        setup_type: str = "MANUAL_OVERRIDE",
        conviction_tier: str = "Tier 2",
        stop_price: float = 0.0,
        exit_reason: str = "MANUAL_EXECUTION",
    ) -> Optional[str]:
        """User manual override fill to log a trade directly regardless of toggle state."""
        return self.record_forward_fill(
            symbol=symbol,
            side=side,
            shares=shares,
            price=price,
            setup_type=setup_type,
            conviction_tier=conviction_tier,
            stop_price=stop_price,
            exit_reason=exit_reason,
            manual_override=True,
        )

    def get_trade_ledger(self, limit: int = 200, only_forward: bool = False) -> List[Dict[str, Any]]:
        """Retrieve trade ledger entries from DuckDB."""
        conn = None
        try:
            conn = self.get_connection(read_only=True)
            query = "SELECT * FROM trade_ledger"
            if only_forward:
                query += " WHERE is_baseline_synthesis = false"
            query += " ORDER BY timestamp DESC LIMIT ?"

            res = conn.execute(query, [limit]).fetchall()
            cols = [desc[0] for desc in conn.description]

            records = []
            for row in res:
                records.append(dict(zip(cols, row)))
            return records
        except Exception as e:
            logger.error(f"Error fetching trade ledger: {e}")
            return []
        finally:
            pass

    def record_daily_snapshot(
        self,
        date_str: str,
        nav: float,
        cash: float,
        equity_value: float,
        daily_return_pct: float,
        cumulative_return_pct: float,
        high_water_mark: float,
        drawdown_pct: float,
    ) -> bool:
        """Persist daily portfolio NAV and risk metrics."""
        conn = None
        try:
            conn = self.get_connection(read_only=False)
            cash_weight = (cash / nav) * 100.0 if nav > 0 else 0.0
            equity_weight = (equity_value / nav) * 100.0 if nav > 0 else 0.0

            conn.execute("""
                INSERT OR REPLACE INTO portfolio_daily_snapshots (
                    date, nav, cash, equity_value, cash_weight, equity_weight,
                    daily_return_pct, cumulative_return_pct, high_water_mark, drawdown_pct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                date_str,
                nav,
                cash,
                equity_value,
                cash_weight,
                equity_weight,
                daily_return_pct,
                cumulative_return_pct,
                high_water_mark,
                drawdown_pct,
            ])
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error recording daily snapshot: {e}")
            return False
        finally:
            pass

    def record_benchmark_quote(
        self,
        date_str: str,
        symbol: str,
        close: float,
        daily_return_pct: float,
        cumulative_return_pct: float,
    ) -> bool:
        """Persist benchmark daily price and performance."""
        conn = None
        try:
            conn = self.get_connection(read_only=False)
            conn.execute("""
                INSERT OR REPLACE INTO benchmark_quotes (
                    date, symbol, close, daily_return_pct, cumulative_return_pct
                ) VALUES (?, ?, ?, ?, ?)
            """, [date_str, symbol.upper(), close, daily_return_pct, cumulative_return_pct])
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error recording benchmark quote: {e}")
            return False
        finally:
            pass

    def get_daily_history(self, limit: int = 90) -> List[Dict[str, Any]]:
        """Retrieve daily portfolio snapshots."""
        conn = None
        try:
            conn = self.get_connection(read_only=True)
            res = conn.execute("SELECT * FROM portfolio_daily_snapshots ORDER BY date ASC LIMIT ?", [limit]).fetchall()
            cols = [desc[0] for desc in conn.description]
            return [dict(zip(cols, row)) for row in res]
        except Exception as e:
            logger.error(f"Error fetching daily history: {e}")
            return []
        finally:
            pass


attribution_lake = AttributionLake()
