"""Portfolio Manager module: Ingests Fidelity brokerage exports, manages live open positions,
calculates real-time P&L/weights, and syncs seamlessly with data/portfolio.json."""

import os
import io
import csv
import json
import logging
import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
from config import TZ_EST

logger = logging.getLogger("portfolio_manager")

PORTFOLIO_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "portfolio.json")

import re

def extract_underlying_ticker(symbol: str) -> str:
    """Extract base equity ticker from stock or option symbol (e.g. -NVDA260828C210 -> NVDA, BRK.B -> BRK.B)."""
    if not symbol:
        return ""
    s = str(symbol).strip().lstrip("-").strip()
    occ_match = re.match(r"^([A-Za-z\.]+?)\d{6}[CPcp]\d+", s)
    if occ_match:
        return occ_match.group(1).upper()
    return s.upper()

class PortfolioManager:
    """Institutional Portfolio Manager with Fidelity Brokerage Ingestion & Live Analytics."""

    def __init__(self, json_path: str = PORTFOLIO_JSON_PATH):
        self.json_path = json_path
        self._ensure_storage()

    def _ensure_storage(self):
        """Ensure data directory and portfolio.json exist."""
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
        if not os.path.exists(self.json_path):
            initial_data = {
                "account_name": "Traditional IRA",
                "account_number": "264695485",
                "last_updated": datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET"),
                "total_nav": 338000.0,
                "cash_balance": 71830.35,
                "risk_budget_pct": 0.75,
                "positions": []
            }
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2)

    def load_portfolio(self) -> Dict[str, Any]:
        """Load portfolio state from JSON file."""
        self._ensure_storage()
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading portfolio JSON: {e}")
            return {"account_name": "My Account", "cash_balance": 50000.0, "positions": []}

    def save_portfolio(self, data: Dict[str, Any]) -> bool:
        """Save portfolio state to JSON file."""
        try:
            data["last_updated"] = datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET")
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving portfolio JSON: {e}")
            return False

    @staticmethod
    def _clean_num(val: Any) -> float:
        """Convert string numbers with $, %, commas, +, - to float."""
        if val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip().replace("$", "").replace("%", "").replace(",", "").replace("+", "")
        if not s or s == "--" or s == "—" or s == "N/A":
            return 0.0
        try:
            return float(s)
        except ValueError:
            return 0.0

    def parse_fidelity_csv(self, csv_content_or_path: str, save_to_disk: bool = True) -> Dict[str, Any]:
        """
        Parse Fidelity CSV export content and return structured portfolio.
        Handles cash rows (SPAXX**, Pending activity), stock/ETF rows, and option contracts.
        """
        raw_text = csv_content_or_path
        if os.path.exists(csv_content_or_path):
            with open(csv_content_or_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        header_idx = -1
        for idx, line in enumerate(lines):
            if "Account number" in line and "Symbol" in line:
                header_idx = idx
                break

        if header_idx == -1:
            logger.error("Could not find Fidelity CSV header row.")
            return {"error": "Invalid Fidelity CSV format: Missing header row"}

        csv_data = "\n".join(lines[header_idx:])
        reader = csv.DictReader(io.StringIO(csv_data))

        account_number = ""
        account_name = ""
        cash_balance = 0.0
        positions = []

        for row in reader:
            if not row:
                continue
            sym_raw = (row.get("Symbol") or "").strip()
            desc = (row.get("Description") or "").strip()
            acc_num = (row.get("Account number") or "").strip()
            acc_nm = (row.get("Account name") or "").strip()

            if acc_num and not account_number:
                account_number = acc_num
            if acc_nm and not account_name:
                account_name = acc_nm

            # Check for Money Market / Cash
            if "SPAXX" in sym_raw or "MONEY MARKET" in desc.upper() or "Pending activity" in acc_nm or "Pending activity" in desc:
                val = self._clean_num(row.get("Current value", 0.0))
                if val == 0.0:
                    for k, v in row.items():
                        if k not in ["Account number", "Account name", "Symbol", "Description", "Type"]:
                            cand = self._clean_num(v)
                            if cand > 0:
                                val = cand
                                break
                cash_balance += val
                continue

            # Check if this row is a disclaimer / footer
            if not sym_raw or "The data and information" in sym_raw or "Brokerage services" in sym_raw or "Date downloaded" in sym_raw:
                continue

            qty = self._clean_num(row.get("Quantity", 0.0))
            if qty == 0.0 and not sym_raw.startswith("-"):
                continue

            last_price = self._clean_num(row.get("Last price", 0.0))
            cur_value = self._clean_num(row.get("Current value", 0.0))
            day_gain_d = self._clean_num(row.get("Today's gain/loss dollar", 0.0))
            day_gain_p = self._clean_num(row.get("Today's gain/loss percent", 0.0))
            tot_gain_d = self._clean_num(row.get("Total gain/loss dollar", 0.0))
            tot_gain_p = self._clean_num(row.get("Total gain/loss percent", 0.0))
            cost_basis_tot = self._clean_num(row.get("Cost basis total", 0.0))
            avg_cost = self._clean_num(row.get("Average cost basis", 0.0))
            pos_type = (row.get("Type") or "Cash").strip()

            # Classify Asset Class: Option vs Stock/ETF
            clean_sym = sym_raw.replace(" ", "").replace("-", "")
            is_option = sym_raw.startswith("-") or "CALL" in desc.upper() or "PUT" in desc.upper()
            underlying = extract_underlying_ticker(sym_raw)

            # Assign default strategy tag
            if is_option:
                strategy_tag = "Options Hedge / Income"
            elif qty > 50 and cur_value > 10000:
                strategy_tag = "Core Long Holding"
            else:
                strategy_tag = "Tactical Momentum"

            positions.append({
                "symbol": clean_sym if is_option else sym_raw,
                "raw_symbol": sym_raw,
                "underlying": underlying,
                "description": desc,
                "is_option": is_option,
                "quantity": qty,
                "last_price": last_price,
                "current_value": cur_value,
                "cost_basis_total": cost_basis_tot,
                "average_cost": avg_cost if avg_cost > 0 else (cost_basis_tot / qty if qty > 0 else last_price),
                "today_pnl_dollar": day_gain_d,
                "today_pnl_pct": day_gain_p,
                "total_pnl_dollar": tot_gain_d,
                "total_pnl_pct": tot_gain_p,
                "account_type": pos_type,
                "strategy_tag": strategy_tag,
                "stop_loss": round(last_price * 0.93, 2) if not is_option else 0.0,
                "target_price": round(last_price * 1.15, 2) if not is_option else 0.0,
                "entry_date": datetime.datetime.now(TZ_EST).strftime("%b %d, %Y"),
                "notes": "",
            })

        # Calculate Total Portfolio Value
        equity_val = sum(p["current_value"] for p in positions)
        total_nav = equity_val + cash_balance

        portfolio_data = {
            "account_number": account_number or "264695485",
            "account_name": account_name or "Traditional IRA",
            "last_updated": datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET"),
            "total_nav": round(total_nav, 2),
            "cash_balance": round(cash_balance, 2),
            "equity_value": round(equity_val, 2),
            "risk_budget_pct": 0.75,
            "positions_count": len(positions),
            "positions": positions
        }

        # Save to disk
        if save_to_disk:
            self.save_portfolio(portfolio_data)
        logger.info(f"Parsed Fidelity CSV: {len(positions)} positions, NAV: ${total_nav:,.2f}, Cash: ${cash_balance:,.2f}")
        return portfolio_data

    def enrich_live_metrics(
        self,
        portfolio_data: Optional[Dict[str, Any]] = None,
        market_lookup: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Enrich portfolio positions with live real-time metrics (dynamic weights, day P&L,
        technicals, MA distances, options gamma walls, analyst ratings, and setup scores).
        """
        if portfolio_data is None:
            portfolio_data = self.load_portfolio()

        positions = portfolio_data.get("positions", [])
        if not positions:
            return portfolio_data

        total_equity_val = 0.0
        tot_day_pnl = 0.0
        tot_unrealized_pnl = 0.0
        mkt_map = market_lookup or {}

        for p in positions:
            sym = p.get("symbol", "")
            raw_sym = p.get("raw_symbol", sym)
            underlying = p.get("underlying") or extract_underlying_ticker(raw_sym)
            p["underlying"] = underlying
            is_opt = p.get("is_option", False)

            qty = float(p.get("quantity", 0.0) or 0.0)
            avg_cost = float(p.get("average_cost", 0.0) or 0.0)
            cost_tot = float(p.get("cost_basis_total", 0.0) or 0.0)
            if cost_tot <= 0 and qty > 0 and avg_cost > 0:
                cost_tot = qty * avg_cost
            p["cost_basis_total"] = round(cost_tot, 2)

            # Check if live market data is available for underlying or sym
            mkt_info = mkt_map.get(underlying) or mkt_map.get(sym) or {}
            live_price = float(mkt_info.get("price", 0.0) or 0.0)

            # Update live price for equities / ETFs
            if not is_opt and live_price > 0:
                cur_price = live_price
                p["last_price"] = round(cur_price, 2)
            else:
                cur_price = float(p.get("last_price", 0.0) or 0.0)

            # Update current holding market value
            if not is_opt:
                cur_val = qty * cur_price
            else:
                cur_val = float(p.get("current_value", 0.0) or 0.0)
            p["current_value"] = round(cur_val, 2)
            total_equity_val += cur_val

            # Total Unrealized Gain / Loss
            if cost_tot > 0 and not is_opt:
                tot_pnl_d = cur_val - cost_tot
                tot_pnl_p = (tot_pnl_d / cost_tot) * 100.0
            else:
                tot_pnl_d = float(p.get("total_pnl_dollar", 0.0) or 0.0)
                tot_pnl_p = float(p.get("total_pnl_pct", 0.0) or 0.0)

            p["total_pnl_dollar"] = round(tot_pnl_d, 2)
            p["total_pnl_pct"] = round(tot_pnl_p, 2)

            # Today's Session P&L
            if not is_opt and live_price > 0:
                pct_chg = float(mkt_info.get("pct_change", 0.0) or 0.0)
                prev_close = float(mkt_info.get("prev_close", 0.0) or 0.0)
                if prev_close <= 0 and pct_chg != -100:
                    prev_close = cur_price / (1.0 + pct_chg / 100.0)
                if prev_close > 0:
                    day_pnl_d = qty * (cur_price - prev_close)
                else:
                    day_pnl_d = cur_val * (pct_chg / 100.0)
                day_pnl_p = pct_chg
            else:
                day_pnl_d = float(p.get("today_pnl_dollar", 0.0) or 0.0)
                day_pnl_p = float(p.get("today_pnl_pct", 0.0) or 0.0)

            p["today_pnl_dollar"] = round(day_pnl_d, 2)
            p["today_pnl_pct"] = round(day_pnl_p, 2)

            tot_day_pnl += p["today_pnl_dollar"]
            tot_unrealized_pnl += p["total_pnl_dollar"]

            # Attach Live Market Technicals / Screener Attributes from Market Lookup
            p["pct_change"] = mkt_info.get("pct_change", p.get("today_pnl_pct", 0.0))
            p["gap_pct"] = mkt_info.get("gap_pct", 0.0)
            p["pct_from_open"] = mkt_info.get("pct_from_open", 0.0)
            p["rvol"] = mkt_info.get("rvol", 1.0)
            p["setup_score"] = mkt_info.get("setup_score", 3.0)
            p["setup_score_display"] = mkt_info.get("setup_score_display", "3.0★")
            p["stars_visual"] = mkt_info.get("stars_visual", "★★★☆☆")
            p["sector"] = mkt_info.get("sector", "General")
            p["industry"] = mkt_info.get("industry", "Diversified")
            p["earnings_date"] = mkt_info.get("earnings_date", "—")
            p["yesterday_high_dist"] = mkt_info.get("yesterday_high_dist", "—")
            p["premarket_high_dist"] = mkt_info.get("premarket_high_dist", "—")
            p["vwap"] = mkt_info.get("vwap", "—")
            p["vwap_num"] = mkt_info.get("vwap_num", 0.0)
            p["vwap_dist"] = mkt_info.get("vwap_dist", 0.0)
            p["vwap_xo"] = mkt_info.get("vwap_xo", False)
            p["vwap_xu"] = mkt_info.get("vwap_xu", False)
            p["vwap_std_p1"] = mkt_info.get("vwap_std_p1", False)
            p["vwap_std_p2"] = mkt_info.get("vwap_std_p2", False)
            p["vwap_std_m1"] = mkt_info.get("vwap_std_m1", False)
            p["vwap_std_m2"] = mkt_info.get("vwap_std_m2", False)
            p["sma5"] = mkt_info.get("sma5", "—")
            p["sma20"] = mkt_info.get("sma20", "—")
            p["sma20_dist"] = mkt_info.get("sma20_dist", 0.0)
            p["sma20_xo"] = mkt_info.get("sma20_xo", False)
            p["sma20_xu"] = mkt_info.get("sma20_xu", False)
            p["sma50"] = mkt_info.get("sma50", "—")
            p["sma50_dist"] = mkt_info.get("sma50_dist", 0.0)
            p["sma50_xo"] = mkt_info.get("sma50_xo", False)
            p["sma50_xu"] = mkt_info.get("sma50_xu", False)
            p["sma200"] = mkt_info.get("sma200", "—")
            p["sma200_dist"] = mkt_info.get("sma200_dist", 0.0)
            p["sma200_xo"] = mkt_info.get("sma200_xo", False)
            p["sma200_xu"] = mkt_info.get("sma200_xu", False)
            p["catalyst_type"] = mkt_info.get("catalyst_type", "Portfolio Holding")
            p["catalyst_stars"] = mkt_info.get("catalyst_stars", 3.0)
            p["catalyst_date"] = mkt_info.get("catalyst_date", "—")
            p["headline"] = mkt_info.get("headline", p.get("description", ""))
            p["catalyst_url"] = mkt_info.get("catalyst_url", "#")
            p["is_positive"] = mkt_info.get("is_positive", True)
            p["breakout_last_high"] = mkt_info.get("breakout_last_high", False)
            p["breakout_pm_high"] = mkt_info.get("breakout_pm_high", False)
            p["breakout_week_high"] = mkt_info.get("breakout_week_high", False)
            p["breakdown_pm_low"] = mkt_info.get("breakdown_pm_low", False)
            p["breakdown_week_low"] = mkt_info.get("breakdown_week_low", False)
            p["breakdown_last_low"] = mkt_info.get("breakdown_last_low", False)
            p["call_wall"] = mkt_info.get("call_wall", "—")
            p["put_wall"] = mkt_info.get("put_wall", "—")
            p["gamma_flip"] = mkt_info.get("gamma_flip", "—")
            p["gamma_skew"] = mkt_info.get("gamma_skew", "Neutral")
            p["pc_ratio"] = mkt_info.get("pc_ratio", "—")
            p["vol_oi_ratio"] = mkt_info.get("vol_oi_ratio", 1.0)
            p["atm_iv_str"] = mkt_info.get("atm_iv_str", "—")
            p["net_dollar_str"] = mkt_info.get("net_dollar_str", "—")
            p["net_dollar_val"] = mkt_info.get("net_dollar_val", 0.0)
            p["whale_trades_count"] = mkt_info.get("whale_trades_count", 0)
            p["flow_conviction_badge"] = mkt_info.get("flow_conviction_badge", "🟡 Flow: 50/100")
            p["analyst_rating"] = mkt_info.get("analyst_rating", "—")
            p["market_cap_str"] = mkt_info.get("market_cap_str", "—")

            # Guaranteed Options Gamma fallback if not in market_lookup
            if (p["call_wall"] == "—" or p["gamma_flip"] == "—") and underlying:
                from sources.options_flow import options_scanner
                g_data = options_scanner.compute_45d_ticker_gamma(underlying)
                if g_data:
                    cur_p = p.get("last_price", 0.0)
                    def _fmt_lvl(lvl, cur):
                        if not lvl or lvl == "—":
                            return "—"
                        try:
                            val = float(str(lvl).replace("$", "").replace(",", "").strip())
                            if cur > 0 and val > 0:
                                diff = ((val - cur) / cur) * 100.0
                                return f"${val:.2f} ({diff:+.1f}%)"
                            return f"${val:.2f}"
                        except Exception:
                            return str(lvl)

                    p["call_wall"] = _fmt_lvl(g_data.get("call_wall"), cur_p)
                    p["put_wall"] = _fmt_lvl(g_data.get("put_wall"), cur_p)
                    p["gamma_flip"] = _fmt_lvl(g_data.get("gamma_flip"), cur_p)
                    p["gamma_skew"] = g_data.get("skew", "Neutral")
                    p["pc_ratio"] = str(g_data.get("pc_ratio", "1.00"))
                    p["vol_oi_ratio"] = g_data.get("vol_oi_ratio", 1.0)
                    p["atm_iv_str"] = g_data.get("atm_iv_str", "—")
                    p["net_dollar_str"] = g_data.get("net_dollar_str", "—")
                    p["net_dollar_val"] = g_data.get("net_dollar_val", 0.0)
                    p["whale_trades_count"] = g_data.get("whale_count", 0)
                    p["flow_conviction_badge"] = g_data.get("flow_conviction_badge", "🟡 Flow: 50/100")

        # Recalculate weights and live aggregate portfolio metrics
        cash_balance = float(portfolio_data.get("cash_balance", 0.0) or 0.0)
        total_nav = cash_balance + total_equity_val
        portfolio_data["total_nav"] = round(total_nav, 2)
        portfolio_data["cash_balance"] = round(cash_balance, 2)
        portfolio_data["equity_value"] = round(total_equity_val, 2)
        portfolio_data["total_day_pnl_dollar"] = round(tot_day_pnl, 2)
        prev_equity = total_equity_val - tot_day_pnl
        portfolio_data["total_day_pnl_pct"] = round((tot_day_pnl / (total_nav - tot_day_pnl) * 100.0) if (total_nav - tot_day_pnl) > 0 else 0.0, 2)
        portfolio_data["total_unrealized_pnl_dollar"] = round(tot_unrealized_pnl, 2)
        portfolio_data["cash_weight_pct"] = round((cash_balance / total_nav * 100.0) if total_nav > 0 else 0.0, 2)

        for p in positions:
            p["weight_pct"] = round((p["current_value"] / total_nav * 100.0) if total_nav > 0 else 0.0, 2)

        return portfolio_data

    def add_or_update_position(self, pos: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new position or update an existing position."""
        data = self.load_portfolio()
        sym = pos.get("symbol", "").upper().strip()
        if not sym:
            return data

        existing = next((p for p in data["positions"] if p.get("symbol", "").upper() == sym), None)
        if existing:
            existing.update(pos)
        else:
            if "entry_date" not in pos:
                pos["entry_date"] = datetime.datetime.now(TZ_EST).strftime("%b %d, %Y")
            data["positions"].append(pos)

        enriched = self.enrich_live_metrics(data)
        self.save_portfolio(enriched)
        return enriched

    def delete_position(self, symbol: str) -> Dict[str, Any]:
        """Remove a position by symbol."""
        data = self.load_portfolio()
        clean = symbol.upper().strip()
        data["positions"] = [p for p in data["positions"] if p.get("symbol", "").upper() != clean and p.get("raw_symbol", "").upper() != clean]
        enriched = self.enrich_live_metrics(data)
        self.save_portfolio(enriched)
        return enriched

portfolio_mgr = PortfolioManager()

