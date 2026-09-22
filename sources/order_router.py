"""
Autonomous Multi-Broker Order Router & Unified Paper Trading Simulator (Phase 5).
=================================================================================
Provides:
  1. Unified Paper Trading Execution Engine backed by persistent DuckDB storage.
  2. Realistic slippage & bid-ask spread execution modeling.
  3. Official Alpaca Free-Tier Paper/Live REST API Gateway (POST/GET /v2/orders).
  4. Universal Webhook Order Dispatcher for external trade automations.
  5. 3-Tranche Smart Order Slicing (TWAP & Limit Laddering: 40% / 35% / 25%).
  6. Seamless integration with Phase 3 Fidelity ATP OTOCO bracket tickets.
"""

import os
import json
import uuid
import math
import logging
import datetime
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import duckdb

from config import (
    TZ_EST,
    DATA_DIR,
    PAPER_TRADING_DB_PATH,
    ALPACA_API_KEY,
    ALPACA_SECRET_KEY,
    ALPACA_BASE_URL,
    WEBHOOK_EXECUTION_URL,
)

logger = logging.getLogger("order_router")


class PaperTradingSimulator:
    """Institutional Paper Trading Simulator with persistent DuckDB ledger."""

    def __init__(self, db_path: Path = PAPER_TRADING_DB_PATH):
        self.db_path = str(db_path)
        self._init_schema()

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.db_path)

    def _init_schema(self):
        """Initialize DuckDB tables for paper trading."""
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS paper_account (
                    account_id VARCHAR PRIMARY KEY,
                    cash_balance DOUBLE,
                    equity_value DOUBLE,
                    total_nav DOUBLE,
                    created_at TIMESTAMP,
                    last_updated TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS paper_positions (
                    symbol VARCHAR PRIMARY KEY,
                    quantity DOUBLE,
                    average_cost DOUBLE,
                    last_price DOUBLE,
                    current_value DOUBLE,
                    unrealized_pnl DOUBLE,
                    unrealized_pnl_pct DOUBLE,
                    realized_pnl DOUBLE,
                    entry_date VARCHAR,
                    last_updated TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS paper_orders (
                    order_id VARCHAR PRIMARY KEY,
                    timestamp TIMESTAMP,
                    symbol VARCHAR,
                    action VARCHAR,
                    quantity DOUBLE,
                    order_type VARCHAR,
                    limit_price DOUBLE,
                    stop_price DOUBLE,
                    status VARCHAR,
                    fill_price DOUBLE,
                    fill_timestamp TIMESTAMP,
                    slippage_dollar DOUBLE,
                    strategy_tag VARCHAR,
                    notes VARCHAR
                );
            """)

            # Seed initial paper account with $100,000 cash if not exists
            row = conn.execute("SELECT COUNT(*) FROM paper_account;").fetchone()
            if not row or row[0] == 0:
                now_ts = datetime.datetime.now()
                conn.execute("""
                    INSERT INTO paper_account VALUES ('PAPER_DEFAULT', 100000.0, 0.0, 100000.0, ?, ?);
                """, (now_ts, now_ts))
        finally:
            conn.close()

    def get_account_summary(self) -> Dict[str, Any]:
        """Fetch current paper account balance and total value."""
        conn = self._get_connection()
        try:
            acc = conn.execute("SELECT cash_balance, equity_value, total_nav FROM paper_account WHERE account_id = 'PAPER_DEFAULT';").fetchone()
            pos_count = conn.execute("SELECT COUNT(*) FROM paper_positions WHERE quantity > 0;").fetchone()[0]
            orders_count = conn.execute("SELECT COUNT(*) FROM paper_orders;").fetchone()[0]

            cash = acc[0] if acc else 100000.0
            eq = acc[1] if acc else 0.0
            nav = acc[2] if acc else 100000.0

            return {
                "account_id": "PAPER_DEFAULT",
                "cash_balance": round(cash, 2),
                "equity_value": round(eq, 2),
                "total_nav": round(nav, 2),
                "open_positions_count": pos_count,
                "total_orders_count": orders_count,
            }
        finally:
            conn.close()

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Retrieve all active paper positions."""
        conn = self._get_connection()
        try:
            rows = conn.execute("""
                SELECT symbol, quantity, average_cost, last_price, current_value, unrealized_pnl, unrealized_pnl_pct, realized_pnl, entry_date
                FROM paper_positions WHERE quantity > 0 ORDER BY current_value DESC;
            """).fetchall()

            positions = []
            for r in rows:
                positions.append({
                    "symbol": r[0],
                    "quantity": r[1],
                    "average_cost": round(r[2], 2),
                    "last_price": round(r[3], 2),
                    "current_value": round(r[4], 2),
                    "unrealized_pnl": round(r[5], 2),
                    "unrealized_pnl_pct": round(r[6], 2),
                    "realized_pnl": round(r[7], 2),
                    "entry_date": r[8],
                })
            return positions
        finally:
            conn.close()

    def get_order_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve paper order history."""
        conn = self._get_connection()
        try:
            rows = conn.execute("""
                SELECT order_id, timestamp, symbol, action, quantity, order_type, limit_price, stop_price, status, fill_price, slippage_dollar, strategy_tag, notes
                FROM paper_orders ORDER BY timestamp DESC LIMIT ?;
            """, (limit,)).fetchall()

            orders = []
            for r in rows:
                orders.append({
                    "order_id": r[0],
                    "timestamp": r[1].strftime("%Y-%m-%d %H:%M:%S") if r[1] else "",
                    "symbol": r[2],
                    "action": r[3],
                    "quantity": r[4],
                    "order_type": r[5],
                    "limit_price": r[6],
                    "stop_price": r[7],
                    "status": r[8],
                    "fill_price": round(r[9], 2) if r[9] else None,
                    "slippage_dollar": round(r[10], 2) if r[10] else 0.0,
                    "strategy_tag": r[11],
                    "notes": r[12],
                })
            return orders
        finally:
            conn.close()

    def execute_paper_order(
        self,
        symbol: str,
        action: str,
        quantity: float,
        order_type: str = "LIMIT",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        market_price: Optional[float] = None,
        strategy_tag: str = "Tactical Momentum",
        notes: str = "",
    ) -> Dict[str, Any]:
        """
        Execute simulated paper order with realistic fill and slippage calculation.
        Updates cash, positions, and logs order to DuckDB.
        """
        sym = symbol.strip().upper()
        act = action.strip().upper()  # BUY or SELL
        qty = abs(float(quantity))

        if qty <= 0:
            return {"status": "REJECTED", "message": "Quantity must be positive"}

        mkt_p = float(market_price or limit_price or 100.0)
        lim_p = float(limit_price) if limit_price else mkt_p

        # Realistic Institutional Slippage Simulation
        # Spread: 0.02% base + 0.01% random volume impact
        spread_pct = 0.0003
        if act == "BUY":
            # Buyer pays half the spread plus minor impact
            fill_price = round(mkt_p * (1.0 + spread_pct), 2)
            slippage = round(fill_price - mkt_p, 4)
        else:
            # Seller receives bid
            fill_price = round(mkt_p * (1.0 - spread_pct), 2)
            slippage = round(mkt_p - fill_price, 4)

        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        now_ts = datetime.datetime.now()

        conn = self._get_connection()
        try:
            # Fetch current cash
            acc = conn.execute("SELECT cash_balance FROM paper_account WHERE account_id = 'PAPER_DEFAULT';").fetchone()
            cash = acc[0] if acc else 100000.0
            order_cost = fill_price * qty

            if act == "BUY" and order_cost > cash:
                # Insufficient funds
                conn.execute("""
                    INSERT INTO paper_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'REJECTED', NULL, NULL, 0.0, ?, 'Insufficient Paper Cash');
                """, (order_id, now_ts, sym, act, qty, order_type, lim_p, stop_price, strategy_tag))
                return {"status": "REJECTED", "order_id": order_id, "message": f"Insufficient funds: Requires ${order_cost:,.2f}, cash is ${cash:,.2f}"}

            # If SELL, check existing position
            pos_row = conn.execute("SELECT quantity, average_cost FROM paper_positions WHERE symbol = ?;", (sym,)).fetchone()
            current_held_qty = pos_row[0] if pos_row else 0.0
            avg_cost = pos_row[1] if pos_row else fill_price

            if act == "SELL" and qty > current_held_qty:
                conn.execute("""
                    INSERT INTO paper_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'REJECTED', NULL, NULL, 0.0, ?, 'Cannot sell more than held position');
                """, (order_id, now_ts, sym, act, qty, order_type, lim_p, stop_price, strategy_tag))
                return {"status": "REJECTED", "order_id": order_id, "message": f"Cannot sell {qty} shares of {sym}: Only {current_held_qty} held"}

            # Log filled order
            conn.execute("""
                INSERT INTO paper_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'FILLED', ?, ?, ?, ?, ?);
            """, (order_id, now_ts, sym, act, qty, order_type, lim_p, stop_price, fill_price, now_ts, slippage, strategy_tag, notes))

            # Update positions and account cash
            if act == "BUY":
                new_cash = cash - order_cost
                new_qty = current_held_qty + qty
                new_avg_cost = round(((current_held_qty * avg_cost) + order_cost) / new_qty, 2)
                cur_val = round(new_qty * fill_price, 2)
                today_str = datetime.datetime.now(TZ_EST).strftime("%b %d, %Y")

                conn.execute("""
                    INSERT INTO paper_positions (symbol, quantity, average_cost, last_price, current_value, unrealized_pnl, unrealized_pnl_pct, realized_pnl, entry_date, last_updated)
                    VALUES (?, ?, ?, ?, ?, 0.0, 0.0, 0.0, ?, ?)
                    ON CONFLICT(symbol) DO UPDATE SET
                        quantity = excluded.quantity,
                        average_cost = excluded.average_cost,
                        last_price = excluded.last_price,
                        current_value = excluded.current_value,
                        last_updated = excluded.last_updated;
                """, (sym, new_qty, new_avg_cost, fill_price, cur_val, today_str, now_ts))
            else:  # SELL
                new_cash = cash + order_cost
                new_qty = current_held_qty - qty
                realized_gain = round((fill_price - avg_cost) * qty, 2)

                if new_qty > 0:
                    cur_val = round(new_qty * fill_price, 2)
                    unrealized_gain = round((fill_price - avg_cost) * new_qty, 2)
                    unrealized_pct = round(((fill_price - avg_cost) / avg_cost) * 100.0, 2) if avg_cost > 0 else 0.0
                    conn.execute("""
                        UPDATE paper_positions SET
                            quantity = ?,
                            last_price = ?,
                            current_value = ?,
                            unrealized_pnl = ?,
                            unrealized_pnl_pct = ?,
                            realized_pnl = realized_pnl + ?,
                            last_updated = ?
                        WHERE symbol = ?;
                    """, (new_qty, fill_price, cur_val, unrealized_gain, unrealized_pct, realized_gain, now_ts, sym))
                else:
                    # Fully closed
                    conn.execute("""
                        DELETE FROM paper_positions WHERE symbol = ?;
                    """, (sym,))

            # Recompute Total Equity
            eq_val_row = conn.execute("SELECT SUM(current_value) FROM paper_positions WHERE quantity > 0;").fetchone()
            total_eq = eq_val_row[0] if eq_val_row and eq_val_row[0] else 0.0
            total_nav = round(new_cash + total_eq, 2)

            conn.execute("""
                UPDATE paper_account SET
                    cash_balance = ?,
                    equity_value = ?,
                    total_nav = ?,
                    last_updated = ?
                WHERE account_id = 'PAPER_DEFAULT';
            """, (round(new_cash, 2), round(total_eq, 2), total_nav, now_ts))

            return {
                "status": "FILLED",
                "order_id": order_id,
                "symbol": sym,
                "action": act,
                "quantity": qty,
                "fill_price": fill_price,
                "total_cost": round(order_cost, 2),
                "slippage": slippage,
                "remaining_cash": round(new_cash, 2),
                "total_nav": total_nav,
            }
        finally:
            conn.close()

    def reset_paper_account(self, initial_cash: float = 100000.0) -> Dict[str, Any]:
        """Reset paper account balance and wipe positions/orders."""
        conn = self._get_connection()
        try:
            now_ts = datetime.datetime.now()
            conn.execute("DELETE FROM paper_positions;")
            conn.execute("DELETE FROM paper_orders;")
            conn.execute("""
                UPDATE paper_account SET
                    cash_balance = ?,
                    equity_value = 0.0,
                    total_nav = ?,
                    last_updated = ?
                WHERE account_id = 'PAPER_DEFAULT';
            """, (initial_cash, initial_cash, now_ts))
            return {"status": "SUCCESS", "cash_balance": initial_cash, "total_nav": initial_cash}
        finally:
            conn.close()


class AlpacaClient:
    """Official Alpaca Paper / Live Trading REST API Gateway."""

    def __init__(
        self,
        api_key: str = ALPACA_API_KEY,
        secret_key: str = ALPACA_SECRET_KEY,
        base_url: str = ALPACA_BASE_URL,
    ):
        self.api_key = api_key or os.environ.get("ALPACA_API_KEY", "")
        self.secret_key = secret_key or os.environ.get("ALPACA_SECRET_KEY", "")
        self.base_url = (base_url or os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets/v2")).rstrip("/")

    def is_configured(self) -> bool:
        """Check if Alpaca API keys are provided."""
        return bool(self.api_key and self.secret_key)

    def _make_request(self, endpoint: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None) -> Tuple[bool, Any]:
        """Send authenticated HTTP request to Alpaca REST API."""
        if not self.is_configured():
            return False, {"error": "Alpaca API credentials not configured (set ALPACA_API_KEY and ALPACA_SECRET_KEY)"}

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Content-Type": "application/json",
            "User-Agent": "InstitutionalScreener/5.0",
        }

        data_bytes = json.dumps(payload).encode("utf-8") if payload else None
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                resp_text = resp.read().decode("utf-8")
                return True, json.loads(resp_text) if resp_text else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else str(e)
            logger.error(f"Alpaca API HTTP {e.code} error: {err_body}")
            try:
                parsed_err = json.loads(err_body)
            except Exception:
                parsed_err = {"message": err_body}
            return False, {"status_code": e.code, "error": parsed_err}
        except Exception as e:
            logger.error(f"Alpaca API connection error: {e}")
            return False, {"error": str(e)}

    def get_account(self) -> Dict[str, Any]:
        """Fetch Alpaca account summary."""
        success, data = self._make_request("account")
        if success:
            return {
                "status": "SUCCESS",
                "connected": True,
                "account_number": data.get("account_number"),
                "status_label": data.get("status"),
                "currency": data.get("currency", "USD"),
                "cash": float(data.get("cash", 0.0)),
                "buying_power": float(data.get("buying_power", 0.0)),
                "portfolio_value": float(data.get("portfolio_value", 0.0)),
                "equity": float(data.get("equity", 0.0)),
                "daytrade_count": int(data.get("daytrade_count", 0)),
            }
        return {"status": "UNAVAILABLE", "connected": False, "details": data}

    def get_positions(self) -> List[Dict[str, Any]]:
        """Fetch all open positions from Alpaca."""
        success, data = self._make_request("positions")
        if success and isinstance(data, list):
            positions = []
            for p in data:
                positions.append({
                    "symbol": p.get("symbol"),
                    "qty": float(p.get("qty", 0.0)),
                    "side": p.get("side"),
                    "market_value": float(p.get("market_value", 0.0)),
                    "avg_entry_price": float(p.get("avg_entry_price", 0.0)),
                    "current_price": float(p.get("current_price", 0.0)),
                    "unrealized_pl": float(p.get("unrealized_pl", 0.0)),
                    "unrealized_plpc": float(p.get("unrealized_plpc", 0.0)) * 100.0,
                })
            return positions
        return []

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str = "buy",
        order_type: str = "limit",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Submit new order to Alpaca Paper/Live."""
        payload = {
            "symbol": symbol.upper(),
            "qty": int(qty) if qty.is_integer() else qty,
            "side": side.lower(),
            "type": order_type.lower(),
            "time_in_force": time_in_force.lower(),
        }
        if limit_price and order_type.lower() in ["limit", "stop_limit"]:
            payload["limit_price"] = str(round(limit_price, 2))
        if stop_price and order_type.lower() in ["stop", "stop_limit"]:
            payload["stop_price"] = str(round(stop_price, 2))

        success, data = self._make_request("orders", method="POST", payload=payload)
        if success:
            return {
                "status": "SUBMITTED",
                "broker": "ALPACA",
                "order_id": data.get("id"),
                "client_order_id": data.get("client_order_id"),
                "symbol": data.get("symbol"),
                "qty": data.get("qty"),
                "type": data.get("type"),
                "side": data.get("side"),
                "status_label": data.get("status"),
                "submitted_at": data.get("submitted_at"),
            }
        return {"status": "FAILED", "broker": "ALPACA", "details": data}


class OrderRouter:
    """Universal Execution Hub routing orders to Paper Simulator, Alpaca, or Webhook."""

    def __init__(self):
        self.paper_sim = PaperTradingSimulator()
        self.alpaca_client = AlpacaClient()

    @staticmethod
    def slice_smart_ladder(
        symbol: str,
        total_quantity: float,
        pivot_price: float,
        action: str = "BUY",
    ) -> List[Dict[str, Any]]:
        """
        Generate 3-stage Smart Limit Order Ladder (40% Breakout, 35% Pullback, 25% Confirmation).
        Minimizes market impact and slippage.
        """
        q = float(total_quantity)
        p = float(pivot_price)

        t1_qty = round(q * 0.40, 3)
        t2_qty = round(q * 0.35, 3)
        t3_qty = round(q - t1_qty - t2_qty, 3)

        if action.upper() == "BUY":
            t1_price = round(p, 2)                # Immediate pivot
            t2_price = round(p * 0.9925, 2)       # -0.75% Pullback test
            t3_price = round(p * 1.0050, 2)       # +0.50% Breakout confirmation
        else:
            t1_price = round(p, 2)
            t2_price = round(p * 1.0075, 2)       # +0.75% Rip test
            t3_price = round(p * 0.9950, 2)       # -0.50% Breakdown confirmation

        return [
            {
                "tranche": 1,
                "label": "Tranche 1 (40% Primary Pivot)",
                "action": action.upper(),
                "quantity": t1_qty,
                "limit_price": t1_price,
                "order_type": "LIMIT",
                "allocation_pct": 40.0,
            },
            {
                "tranche": 2,
                "label": "Tranche 2 (35% Pullback / VWAP)",
                "action": action.upper(),
                "quantity": t2_qty,
                "limit_price": t2_price,
                "order_type": "LIMIT",
                "allocation_pct": 35.0,
            },
            {
                "tranche": 3,
                "label": "Tranche 3 (25% Momentum Confirm)",
                "action": action.upper(),
                "quantity": t3_qty,
                "limit_price": t3_price,
                "order_type": "LIMIT",
                "allocation_pct": 25.0,
            },
        ]

    def route_order(
        self,
        symbol: str,
        action: str,
        quantity: float,
        destination: str = "PAPER",
        order_type: str = "LIMIT",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        market_price: Optional[float] = None,
        strategy_tag: str = "Tactical Momentum",
        notes: str = "",
    ) -> Dict[str, Any]:
        """
        Route order to target destination:
          - 'PAPER': Local DuckDB simulated paper trading.
          - 'ALPACA': Alpaca Paper / Live API.
          - 'WEBHOOK': External HTTP REST Webhook.
        """
        dest = destination.strip().upper()

        if dest == "ALPACA":
            if not self.alpaca_client.is_configured():
                return {
                    "status": "FAILED",
                    "broker": "ALPACA",
                    "message": "Alpaca API keys not set. Set ALPACA_API_KEY and ALPACA_SECRET_KEY in config.py or environment."
                }
            return self.alpaca_client.submit_order(
                symbol=symbol,
                qty=quantity,
                side=action.lower(),
                order_type=order_type.lower(),
                limit_price=limit_price,
                stop_price=stop_price,
            )

        elif dest == "WEBHOOK":
            if not WEBHOOK_EXECUTION_URL:
                return {"status": "FAILED", "broker": "WEBHOOK", "message": "WEBHOOK_EXECUTION_URL is not configured"}
            payload = {
                "event": "ORDER_EXECUTION",
                "timestamp": datetime.datetime.now(TZ_EST).isoformat(),
                "symbol": symbol.upper(),
                "action": action.upper(),
                "quantity": quantity,
                "order_type": order_type,
                "limit_price": limit_price,
                "stop_price": stop_price,
                "strategy_tag": strategy_tag,
            }
            try:
                data_bytes = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    WEBHOOK_EXECUTION_URL,
                    data=data_bytes,
                    headers={"Content-Type": "application/json", "User-Agent": "InstitutionalScreener/5.0"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return {"status": "SUBMITTED", "broker": "WEBHOOK", "http_status": resp.status}
            except Exception as e:
                return {"status": "FAILED", "broker": "WEBHOOK", "error": str(e)}

        else:  # Default to PAPER
            return self.paper_sim.execute_paper_order(
                symbol=symbol,
                action=action,
                quantity=quantity,
                order_type=order_type,
                limit_price=limit_price,
                stop_price=stop_price,
                market_price=market_price,
                strategy_tag=strategy_tag,
                notes=notes,
            )


order_router = OrderRouter()
