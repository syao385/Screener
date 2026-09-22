"""Order Execution Desk & Fidelity ATP Ticket Engine (Phase 3).
Converts quantitative setups, stop breaches, and rebalance trims into
broker-ready execution tickets formatted specifically for:
  1. Fidelity Active Trader Pro (ATP) Multi-Leg Bracket (OTOCO) Entry
  2. Fidelity.com Web Fast Order Entry
  3. 1-Click Clipboard Instant Paste Strings
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from config import DATA_DIR, ORDER_DESK_FILE, TZ_EST

logger = logging.getLogger("order_execution_desk")


class OrderExecutionDesk:
    """Institutional Order Desk generating Fidelity-tailored trade execution tickets."""

    def __init__(self, storage_path: Path = ORDER_DESK_FILE):
        self.storage_path = Path(storage_path)
        self.default_account = "Traditional IRA"
        self.default_account_num = "264695485"
        self._ensure_storage()

    def _ensure_storage(self):
        """Ensure storage directory and JSON file exist."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            initial_data = {
                "last_updated": datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET"),
                "active_orders": [],
                "execution_history": []
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2)

    def load_orders(self) -> Dict[str, Any]:
        """Load current order desk state."""
        self._ensure_storage()
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load order desk JSON: {e}")
            return {"active_orders": [], "execution_history": []}

    def save_orders(self, data: Dict[str, Any]) -> bool:
        """Persist order desk state."""
        try:
            data["last_updated"] = datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET")
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save order desk JSON: {e}")
            return False

    def create_fidelity_bracket_ticket(
        self,
        ticker: str,
        action: str,  # BUY or SELL
        shares: int,
        entry_price: float,
        stop_price: float,
        target_1: float,
        target_2: float,
        setup_type: str = "BREAKOUT",
        conviction_tier: str = "Tier 2",
        urgency: str = "TIER_1_IMMEDIATE",
        account_name: str = "Traditional IRA",
        account_num: str = "264695485",
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive, broker-ready order ticket formatted for Fidelity Active Trader Pro (ATP).
        """
        order_id = f"ORD-{datetime.datetime.now(TZ_EST).strftime('%Y%m%d')}-{ticker}-{action}-{shares}"
        ts = datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET")

        # 1. Concise 1-Click Clipboard String (for rapid entry or note-taking)
        clipboard_str = (
            f"{action} {shares} {ticker} @ LIMIT ${entry_price:.2f} | "
            f"STOP ${stop_price:.2f} | T1 ${target_1:.2f} | TIF: DAY | ACC: {account_name}"
        )

        # 2. Fidelity.com Web Formatted Copy Block
        fidelity_web_text = (
            f"Account: {account_name} ({account_num})\n"
            f"Action: {action}\n"
            f"Symbol: {ticker}\n"
            f"Quantity: {shares}\n"
            f"Order Type: Limit\n"
            f"Limit Price: ${entry_price:.2f}\n"
            f"Time in Force: Day"
        )

        # 3. Fidelity Active Trader Pro (ATP) Multi-Leg OTOCO Bracket Ticket
        fidelity_atp_bracket_text = (
            f"═══════════════════════════════════════════════════════\n"
            f"  FIDELITY ACTIVE TRADER PRO (ATP) — OTOCO BRACKET TICKET\n"
            f"═══════════════════════════════════════════════════════\n"
            f"Account:        {account_name} ({account_num})\n"
            f"Strategy:       {setup_type} ({conviction_tier})\n"
            f"Order Class:    One-Triggers-OCO (OTOCO)\n"
            f"───────────────────────────────────────────────────────\n"
            f"▶ [PRIMARY ORDER - ENTRY]:\n"
            f"   Action:        {action}\n"
            f"   Symbol:        {ticker}\n"
            f"   Quantity:      {shares} shares\n"
            f"   Order Type:    LIMIT\n"
            f"   Limit Price:   ${entry_price:.2f}\n"
            f"   Time in Force: DAY\n"
            f"───────────────────────────────────────────────────────\n"
            f"▶ [TRIGGERED EXIT 1 - PROFIT TARGET (1.0R Breakeven Lock)]:\n"
            f"   Action:        SELL\n"
            f"   Quantity:      {shares} shares\n"
            f"   Order Type:    LIMIT\n"
            f"   Limit Price:   ${target_1:.2f} (Lock breakeven at entry)\n"
            f"   Time in Force: GTC (Good 'Til Canceled)\n"
            f"───────────────────────────────────────────────────────\n"
            f"▶ [TRIGGERED EXIT 2 - PROTECTIVE HARD STOP]:\n"
            f"   Action:        SELL\n"
            f"   Quantity:      {shares} shares\n"
            f"   Order Type:    STOP LOSS\n"
            f"   Stop Price:    ${stop_price:.2f}\n"
            f"   Time in Force: GTC\n"
            f"───────────────────────────────────────────────────────\n"
            f"▶ [PROFIT TRIM 2.5R TARGET]: ${target_2:.2f}\n"
            f"═══════════════════════════════════════════════════════"
        )

        ticket = {
            "order_id": order_id,
            "timestamp": ts,
            "ticker": ticker,
            "action": action,
            "order_type": "OTOCO_BRACKET" if action == "BUY" else "STOP_LOSS",
            "shares": int(shares),
            "entry_price": float(entry_price),
            "stop_price": float(stop_price),
            "target_1": float(target_1),
            "target_2": float(target_2),
            "conviction_tier": conviction_tier,
            "setup_type": setup_type,
            "urgency": urgency,
            "account_name": account_name,
            "account_num": account_num,
            "status": "STAGED",
            "clipboard_str": clipboard_str,
            "fidelity_web_text": fidelity_web_text,
            "fidelity_atp_bracket_text": fidelity_atp_bracket_text,
        }
        return ticket

    def create_fidelity_exit_ticket(
        self,
        ticker: str,
        shares: int,
        current_price: float,
        stop_price: float,
        reason: str = "Protective Stop Breached",
        urgency: str = "TIER_1_IMMEDIATE",
        account_name: str = "Traditional IRA",
        account_num: str = "264695485",
    ) -> Dict[str, Any]:
        """Generate an immediate exit order ticket for stop loss breach."""
        order_id = f"ORD-{datetime.datetime.now(TZ_EST).strftime('%Y%m%d')}-{ticker}-EXIT-{shares}"
        ts = datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET")

        clipboard_str = (
            f"SELL {shares} {ticker} @ MARKET | REASON: {reason} | ACC: {account_name}"
        )

        fidelity_web_text = (
            f"Account: {account_name} ({account_num})\n"
            f"Action: SELL\n"
            f"Symbol: {ticker}\n"
            f"Quantity: {shares}\n"
            f"Order Type: Market (or Limit ${current_price * 0.99:.2f})\n"
            f"Time in Force: Day"
        )

        fidelity_atp_bracket_text = (
            f"═══════════════════════════════════════════════════════\n"
            f"  FIDELITY ATP — EMERGENCY EXIT ORDER TICKET\n"
            f"═══════════════════════════════════════════════════════\n"
            f"Account:        {account_name} ({account_num})\n"
            f"Action:         SELL (COMPLETE EXIT)\n"
            f"Symbol:         {ticker}\n"
            f"Quantity:       {shares} shares\n"
            f"Order Type:     MARKET\n"
            f"Time in Force:  DAY\n"
            f"Trigger Reason: {reason} (Stop: ${stop_price:.2f} vs Cur: ${current_price:.2f})\n"
            f"═══════════════════════════════════════════════════════"
        )

        return {
            "order_id": order_id,
            "timestamp": ts,
            "ticker": ticker,
            "action": "SELL",
            "order_type": "MARKET_EXIT",
            "shares": int(shares),
            "entry_price": float(current_price),
            "stop_price": float(stop_price),
            "target_1": 0.0,
            "target_2": 0.0,
            "conviction_tier": "Risk Exit",
            "setup_type": "STOP_EXIT",
            "urgency": urgency,
            "account_name": account_name,
            "account_num": account_num,
            "status": "STAGED",
            "clipboard_str": clipboard_str,
            "fidelity_web_text": fidelity_web_text,
            "fidelity_atp_bracket_text": fidelity_atp_bracket_text,
        }

    def create_fidelity_trim_ticket(
        self,
        ticker: str,
        trim_shares: int,
        current_price: float,
        reason: str = "Sector Invalidation Trim (50%)",
        account_name: str = "Traditional IRA",
        account_num: str = "264695485",
    ) -> Dict[str, Any]:
        """Generate a position trim ticket for overweight or invalidation."""
        order_id = f"ORD-{datetime.datetime.now(TZ_EST).strftime('%Y%m%d')}-{ticker}-TRIM-{trim_shares}"
        ts = datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET")

        clipboard_str = (
            f"SELL {trim_shares} {ticker} @ LIMIT ${current_price:.2f} | REASON: {reason} | ACC: {account_name}"
        )

        fidelity_web_text = (
            f"Account: {account_name} ({account_num})\n"
            f"Action: SELL\n"
            f"Symbol: {ticker}\n"
            f"Quantity: {trim_shares}\n"
            f"Order Type: Limit\n"
            f"Limit Price: ${current_price:.2f}\n"
            f"Time in Force: Day"
        )

        fidelity_atp_bracket_text = (
            f"═══════════════════════════════════════════════════════\n"
            f"  FIDELITY ATP — POSITION TRIM TICKET\n"
            f"═══════════════════════════════════════════════════════\n"
            f"Account:        {account_name} ({account_num})\n"
            f"Action:         SELL (PARTIAL TRIM)\n"
            f"Symbol:         {ticker}\n"
            f"Quantity:       {trim_shares} shares\n"
            f"Order Type:     LIMIT\n"
            f"Limit Price:    ${current_price:.2f}\n"
            f"Time in Force:  DAY\n"
            f"Trigger Reason: {reason}\n"
            f"═══════════════════════════════════════════════════════"
        )

        return {
            "order_id": order_id,
            "timestamp": ts,
            "ticker": ticker,
            "action": "SELL",
            "order_type": "LIMIT_TRIM",
            "shares": int(trim_shares),
            "entry_price": float(current_price),
            "stop_price": 0.0,
            "target_1": 0.0,
            "target_2": 0.0,
            "conviction_tier": "Rebalance Trim",
            "setup_type": "TRIM",
            "urgency": "TIER_2_CONDITIONAL",
            "account_name": account_name,
            "account_num": account_num,
            "status": "STAGED",
            "clipboard_str": clipboard_str,
            "fidelity_web_text": fidelity_web_text,
            "fidelity_atp_bracket_text": fidelity_atp_bracket_text,
        }

    def create_thesis_action_ticket(
        self,
        ticker: str,
        action: str,  # SELL or TRIM
        shares: int,
        current_price: float,
        health_score: float,
        reason: str,
        urgency: str = "TIER_1_IMMEDIATE"
    ) -> Dict[str, Any]:
        """Create a dedicated thesis health action ticket."""
        if action.upper() == "SELL":
            return self.create_fidelity_exit_ticket(
                ticker=ticker,
                shares=shares,
                current_price=current_price,
                stop_price=current_price,
                reason=f"Broken Thesis (Health: {health_score:.1f}/10) - {reason}",
                urgency=urgency,
            )
        else:
            return self.create_fidelity_trim_ticket(
                ticker=ticker,
                trim_shares=shares,
                current_price=current_price,
                reason=f"Weakened Thesis (Health: {health_score:.1f}/10) - {reason}",
            )

    def sync_from_screener(
        self,
        candidate_setups: List[Dict[str, Any]],
        portfolio_audit: Optional[Dict[str, Any]] = None,
        stop_audits: Optional[List[Dict[str, Any]]] = None,
        portfolio_data: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Synchronize active tickets from live screener results, stop breaches, and rebalance audits.
        Preserves user 'FILLED' or 'SKIPPED' statuses.
        """
        data = self.load_orders()
        existing_map = {o["order_id"]: o for o in data.get("active_orders", [])}
        new_active_orders = []

        # 1. Process Stop Breaches (Immediate Exits)
        if stop_audits:
            for s in stop_audits:
                sym = s.get("symbol")
                cur_p = float(s.get("current_price", 0.0))
                stop_p = float(s.get("active_stop_price", 0.0))
                shares = int(s.get("shares", 0))
                status = s.get("risk_status", "")

                if "HARD STOP TRIGGERED" in status and shares > 0:
                    ticket = self.create_fidelity_exit_ticket(
                        ticker=sym,
                        shares=shares,
                        current_price=cur_p,
                        stop_price=stop_p,
                        reason=f"Hard Stop Breached at ${stop_p:.2f}",
                        urgency="TIER_1_IMMEDIATE"
                    )
                    oid = ticket["order_id"]
                    if oid in existing_map:
                        ticket["status"] = existing_map[oid].get("status", "STAGED")
                    new_active_orders.append(ticket)

                elif "SECTOR INVALIDATION" in status and shares > 0:
                    trim_qty = max(1, shares // 2)
                    ticket = self.create_fidelity_trim_ticket(
                        ticker=sym,
                        trim_shares=trim_qty,
                        current_price=cur_p,
                        reason=f"Sector Flow Invalidation (Pre-emptive 50% Trim)",
                    )
                    oid = ticket["order_id"]
                    if oid in existing_map:
                        ticket["status"] = existing_map[oid].get("status", "STAGED")
                    new_active_orders.append(ticket)

        # 2. Process Overweight Portfolio Rebalance Trims
        if portfolio_audit and "overweight_positions" in portfolio_audit:
            for o in portfolio_audit["overweight_positions"]:
                sym = o.get("symbol")
                trim_sh = int(o.get("recommended_trim_shares", 0))
                cur_p = float(o.get("current_price", 0.0))
                if trim_sh > 0:
                    ticket = self.create_fidelity_trim_ticket(
                        ticker=sym,
                        trim_shares=trim_sh,
                        current_price=cur_p,
                        reason=f"Concentration Cap Breach ({o.get('weight_pct')}% > {o.get('tier_cap_pct')}%)",
                    )
                    oid = ticket["order_id"]
                    if oid in existing_map:
                        ticket["status"] = existing_map[oid].get("status", "STAGED")
                    new_active_orders.append(ticket)

        # 3. Process High-Conviction Screener Buy Candidates (Top 5 Setups)
        if candidate_setups:
            try:
                from sources.portfolio_optimizer import portfolio_optimizer
                for cand in candidate_setups[:5]:
                    sym = cand.get("ticker", cand.get("symbol", "")).upper()
                    cur_p = float(cand.get("price", cand.get("close", 0.0)) or 0.0)
                    score = float(cand.get("score", 0.0) or 0.0)
                    setup_type = cand.get("pattern", "BASE_BREAKOUT")

                    if cur_p > 0 and score >= 3.5:
                        plan = portfolio_optimizer.calculate_order_plan(
                            ticker=sym,
                            entry_price=cur_p,
                            setup_type=setup_type,
                            setup_quality_mult=min(1.2, score / 4.0),
                            stock_sector=cand.get("sector", "General"),
                            stock_industry=cand.get("industry", "Diversified"),
                        )
                        final_sh = plan.get("final_shares", 0)
                        if final_sh > 0:
                            ticket = self.create_fidelity_bracket_ticket(
                                ticker=sym,
                                action="BUY",
                                shares=final_sh,
                                entry_price=plan["entry_price"],
                                stop_price=plan["stop_price"],
                                target_1=plan["target_1_breakeven_lock"],
                                target_2=plan["target_2_profit_trim"],
                                setup_type=setup_type,
                                conviction_tier=plan["tier_name"],
                                urgency="TIER_1_IMMEDIATE" if score >= 4.2 else "TIER_2_CONDITIONAL",
                            )
                            oid = ticket["order_id"]
                            if oid in existing_map:
                                ticket["status"] = existing_map[oid].get("status", "STAGED")
                            new_active_orders.append(ticket)
            except Exception as e:
                logger.error(f"Error sizing screener buy orders: {e}")

        # Save merged orders
        data["active_orders"] = new_active_orders
        self.save_orders(data)
        return new_active_orders

    def update_order_status(self, order_id: str, new_status: str) -> bool:
        """Mark order as FILLED, SKIPPED, CANCELLED, or STAGED."""
        data = self.load_orders()
        updated = False
        for o in data.get("active_orders", []):
            if o.get("order_id") == order_id:
                o["status"] = new_status.upper()
                o["updated_at"] = datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET")
                updated = True
                break

        if updated:
            self.save_orders(data)
        return updated


# Global singleton instance
order_desk = OrderExecutionDesk()
