"""
Autonomous Intraday Drawdown Circuit Breakers & Capital Preservation Governor (Phase 5).
========================================================================================
Enforces institutional multi-tiered capital preservation:
  - LEVEL 0 (NORMAL): Drawdown > -1.0%. Standard operations.
  - LEVEL 1 (WARNING): Drawdown <= -1.0%. Ratchet stops to 1.5x ATR, cap conviction to <= 0.85x.
  - LEVEL 2 (DERISK): Drawdown <= -2.0%. Clamp risk multiplier to 0.50x, flag Tier 3 trims.
  - LEVEL 3 (KILL-SWITCH): Drawdown <= -3.0%. Halt all automated buying, lock cash, emergency alert.
Also monitors:
  - VIX Term Structure Inversion (VIX / VXV > 1.00 backwardation).
  - Index Gamma Flip Breaches (SPY / QQQ spot below dealer gamma flip).
"""

import os
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from config import (
    TZ_EST,
    CIRCUIT_BREAKER_LEVEL1_PCT,
    CIRCUIT_BREAKER_LEVEL2_PCT,
    CIRCUIT_BREAKER_LEVEL3_PCT,
    CIRCUIT_BREAKER_STATE_FILE,
)
from sources.alert_dispatcher import alert_dispatcher

logger = logging.getLogger("risk_circuit_breakers")


class CircuitBreakerState:
    NORMAL = "NORMAL"
    WARNING = "WARNING"          # Level 1 (-1.0%)
    DERISK = "DERISK"            # Level 2 (-2.0%)
    KILL_SWITCH = "KILL_SWITCH"  # Level 3 (-3.0%)


class RiskCircuitBreakerGovernor:
    """Institutional High-Water Mark & Volatility Shock Circuit Breaker Governor."""

    def __init__(self, state_file: Path = CIRCUIT_BREAKER_STATE_FILE):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.level1_pct = CIRCUIT_BREAKER_LEVEL1_PCT
        self.level2_pct = CIRCUIT_BREAKER_LEVEL2_PCT
        self.level3_pct = CIRCUIT_BREAKER_LEVEL3_PCT
        self._ensure_state_file()

    def _ensure_state_file(self):
        """Initialize circuit breaker state persistence if missing."""
        if not self.state_file.exists():
            today_str = datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d")
            initial_state = {
                "session_date": today_str,
                "high_water_mark_nav": 336870.83,
                "current_nav": 336870.83,
                "intraday_drawdown_pct": 0.0,
                "max_drawdown_pct": 0.0,
                "circuit_breaker_level": CircuitBreakerState.NORMAL,
                "last_alert_level": CircuitBreakerState.NORMAL,
                "last_updated": datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET"),
                "vix_backwardation": False,
                "vix_ratio": 0.92,
                "gamma_flip_breach": False,
                "manual_override": False,
                "history": []
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(initial_state, f, indent=2)

    def load_state(self) -> Dict[str, Any]:
        """Load active circuit breaker state from disk."""
        self._ensure_state_file()
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            
            # Auto-reset high-water mark if new calendar day
            today_str = datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d")
            if state.get("session_date") != today_str:
                state["session_date"] = today_str
                state["high_water_mark_nav"] = state.get("current_nav", 336870.83)
                state["intraday_drawdown_pct"] = 0.0
                state["max_drawdown_pct"] = 0.0
                state["circuit_breaker_level"] = CircuitBreakerState.NORMAL
                state["last_alert_level"] = CircuitBreakerState.NORMAL
                self.save_state(state)

            return state
        except Exception as e:
            logger.error(f"Error loading circuit breaker state: {e}")
            return {
                "session_date": datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d"),
                "high_water_mark_nav": 336870.83,
                "current_nav": 336870.83,
                "intraday_drawdown_pct": 0.0,
                "circuit_breaker_level": CircuitBreakerState.NORMAL,
            }

    def save_state(self, state: Dict[str, Any]) -> bool:
        """Persist circuit breaker state to disk."""
        try:
            state["last_updated"] = datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET")
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving circuit breaker state: {e}")
            return False

    def evaluate_intraday_nav(
        self,
        current_nav: float,
        vix_spot: float = 16.5,
        vix_3m: float = 17.8,
        spy_price: float = 590.0,
        spy_gamma_flip: float = 585.0,
        dispatch_alerts: bool = True,
    ) -> Dict[str, Any]:
        """
        Evaluate real-time NAV against high-water mark and check circuit breaker conditions.
        Updates state and dispatches multi-channel alerts if thresholds are breached.
        """
        state = self.load_state()
        if state.get("manual_override", False):
            state["current_nav"] = current_nav
            self.save_state(state)
            return state

        hwm = float(state.get("high_water_mark_nav") or current_nav)
        
        # Ratchet up High-Water Mark if current NAV achieves new session high
        if current_nav > hwm:
            hwm = current_nav
            state["high_water_mark_nav"] = round(hwm, 2)

        drawdown_pct = ((current_nav - hwm) / hwm * 100.0) if hwm > 0 else 0.0
        drawdown_pct = round(drawdown_pct, 2)
        state["current_nav"] = round(current_nav, 2)
        state["intraday_drawdown_pct"] = drawdown_pct

        max_dd = min(float(state.get("max_drawdown_pct") or 0.0), drawdown_pct)
        state["max_drawdown_pct"] = round(max_dd, 2)

        # Volatility & Gamma checks
        vix_ratio = round(vix_spot / max(0.1, vix_3m), 2)
        vix_backwardation = vix_ratio > 1.00
        gamma_breach = (spy_price > 0 and spy_gamma_flip > 0 and spy_price < spy_gamma_flip)

        state["vix_ratio"] = vix_ratio
        state["vix_backwardation"] = vix_backwardation
        state["gamma_flip_breach"] = gamma_breach

        # Determine Circuit Breaker Level
        prev_level = state.get("circuit_breaker_level", CircuitBreakerState.NORMAL)
        new_level = CircuitBreakerState.NORMAL

        if drawdown_pct <= self.level3_pct:
            new_level = CircuitBreakerState.KILL_SWITCH
        elif drawdown_pct <= self.level2_pct:
            new_level = CircuitBreakerState.DERISK
        elif drawdown_pct <= self.level1_pct:
            new_level = CircuitBreakerState.WARNING

        state["circuit_breaker_level"] = new_level

        # Dispatch alerts if level escalated
        last_alert = state.get("last_alert_level", CircuitBreakerState.NORMAL)
        if dispatch_alerts and new_level != last_alert:
            self._dispatch_breaker_alert(new_level, drawdown_pct, current_nav, hwm)
            state["last_alert_level"] = new_level

        self.save_state(state)
        return state

    def _dispatch_breaker_alert(
        self,
        level: str,
        drawdown_pct: float,
        current_nav: float,
        hwm: float,
    ):
        """Dispatch graduated multi-channel alert on breaker escalation."""
        loss_dollar = hwm - current_nav
        if level == CircuitBreakerState.WARNING:
            msg = f"⚠️ [CIRCUIT BREAKER: LEVEL 1 WARNING]\nIntraday Drawdown: {drawdown_pct:.2f}% (-${loss_dollar:,.2f})\nAction: ATR stops ratcheted to 1.5x. Setup conviction constrained to <= 0.85x."
            alert_dispatcher.dispatch(
                title="Level 1 Drawdown Warning",
                body=f"Portfolio down {drawdown_pct:.2f}% (-${loss_dollar:,.2f}). Sizing constrained.",
                priority="HIGH",
                sound_freq=750,
                duration_ms=400,
            )
        elif level == CircuitBreakerState.DERISK:
            msg = f"🟠 [CIRCUIT BREAKER: LEVEL 2 DE-RISK]\nIntraday Drawdown: {drawdown_pct:.2f}% (-${loss_dollar:,.2f})\nAction: Global risk multiplier clamped to 0.50x. Tier 3 positions flagged for 50% defensive trim."
            alert_dispatcher.dispatch(
                title="Level 2 Tactical De-Risk",
                body=f"Portfolio down {drawdown_pct:.2f}%. Multiplier clamped to 0.50x.",
                priority="URGENT",
                sound_freq=1000,
                duration_ms=700,
            )
        elif level == CircuitBreakerState.KILL_SWITCH:
            msg = f"🛑 [CIRCUIT BREAKER: LEVEL 3 EMERGENCY KILL-SWITCH]\nIntraday Drawdown: {drawdown_pct:.2f}% (-${loss_dollar:,.2f})\nAction: ALL automated buying halted. Liquid cash buffer locked. Desk in capital preservation mode."
            alert_dispatcher.dispatch(
                title="Level 3 KILL-SWITCH ENGAGED",
                body=f"EMERGENCY: Portfolio down {drawdown_pct:.2f}% (-${loss_dollar:,.2f}). Trading halted.",
                priority="CRITICAL",
                sound_freq=1500,
                duration_ms=1200,
            )

    def reset_circuit_breaker(self, new_nav: Optional[float] = None) -> Dict[str, Any]:
        """Manually reset circuit breaker and align High-Water Mark with current NAV."""
        state = self.load_state()
        if new_nav is not None:
            state["current_nav"] = round(new_nav, 2)
            state["high_water_mark_nav"] = round(new_nav, 2)
        else:
            state["high_water_mark_nav"] = state.get("current_nav", 336870.83)

        state["intraday_drawdown_pct"] = 0.0
        state["circuit_breaker_level"] = CircuitBreakerState.NORMAL
        state["last_alert_level"] = CircuitBreakerState.NORMAL
        state["manual_override"] = False
        self.save_state(state)
        logger.info(f"Circuit Breaker reset successfully. High-Water Mark: ${state['high_water_mark_nav']:,.2f}")
        return state

    def set_manual_override(self, override: bool) -> Dict[str, Any]:
        """Toggle manual override to bypass automatic circuit breaker enforcement."""
        state = self.load_state()
        state["manual_override"] = override
        self.save_state(state)
        return state


circuit_breaker_governor = RiskCircuitBreakerGovernor()
