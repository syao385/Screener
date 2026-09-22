"""Quantitative Continuous Parameter Auto-Tuning Engine (Phase 4).
Applies automatic bounded tuning with hard safety clamps [0.50x, 1.35x]
for setup conviction multipliers and regime-adaptive trailing stops.
"""

import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from config import (
    CALIBRATED_PARAMS_FILE,
    TUNING_MIN_CLAMP,
    TUNING_MAX_CLAMP,
    TZ_EST,
)
from sources.attribution_lake import attribution_lake
from sources.attribution_engine import attribution_engine

logger = logging.getLogger("parameter_tuner")


class ParameterTuner:
    """Institutional Feedback Calibration & Parameter Tuning Engine."""

    def __init__(
        self,
        min_clamp: float = TUNING_MIN_CLAMP,  # 0.50x
        max_clamp: float = TUNING_MAX_CLAMP,  # 1.35x
        cache_path: Path = CALIBRATED_PARAMS_FILE,
    ):
        self.min_clamp = min_clamp
        self.max_clamp = max_clamp
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_or_initialize()

    def _load_or_initialize(self):
        """Load cached parameters or initialize baseline parameters."""
        if not self.cache_path.exists():
            self.run_calibration()

    def clamp(self, value: float) -> Tuple[float, str]:
        """Enforce strict hard safety bounds [0.50x, 1.35x]."""
        if value < self.min_clamp:
            return self.min_clamp, "CLAMPED_LOWER"
        elif value > self.max_clamp:
            return self.max_clamp, "CLAMPED_UPPER"
        else:
            return round(value, 3), "OPTIMAL_BOUNDED"

    def run_calibration(self, market_vix: float = 16.5) -> Dict[str, Any]:
        """Execute full automatic calibration across setup archetypes, trailing stops & slippage."""
        archetype_perf = attribution_engine.evaluate_setup_archetypes()
        now_str = datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET")

        calibrated_setups = {}
        conn = None
        try:
            conn = attribution_lake.get_connection(read_only=False)
        except Exception as e:
            logger.debug(f"DuckDB connection notice: {e}")

        # 1. Bounded Setup Conviction Multiplier Tuning
        for a in archetype_perf:
            name = a["setup_name"]
            win_rate = a["win_rate_pct"]
            expectancy = a["expectancy_r"]

            # Mathematical calibration formula:
            # Baseline is 1.0x. Adds 0.35x per 1.0 unit of expectancy above 0.5R, or reduces for poor expectancy.
            raw_multiplier = 1.0 + 0.35 * (expectancy - 0.50)
            clamped_val, status = self.clamp(raw_multiplier)

            param_key = f"CONVICTION_{name.replace(' ', '_').upper()}"
            calibrated_setups[name] = {
                "raw_multiplier": round(raw_multiplier, 3),
                "calibrated_multiplier": clamped_val,
                "status": status,
                "min_clamp": self.min_clamp,
                "max_clamp": self.max_clamp,
                "win_rate_pct": win_rate,
                "expectancy_r": expectancy,
            }

            if conn:
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO tuning_state (
                            parameter_key, parameter_value, clamped_value, min_clamp, max_clamp,
                            last_calibrated, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, [
                        param_key,
                        round(raw_multiplier, 3),
                        clamped_val,
                        self.min_clamp,
                        self.max_clamp,
                        now_str,
                        status,
                    ])
                except Exception as e:
                    logger.debug(f"Error updating tuning_state in DuckDB: {e}")

        # 2. Regime-Adaptive Chandelier Stop Multiplier
        # Low vol (VIX < 14) -> 1.8x; Normal (14-22) -> 2.0x; High vol (VIX > 22) -> 2.4x
        if market_vix < 14.0:
            raw_stop_mult = 1.80
        elif market_vix <= 22.0:
            raw_stop_mult = 2.00
        else:
            raw_stop_mult = 2.40

        clamped_stop_mult = max(1.50, min(2.50, raw_stop_mult))
        calibrated_stops = {
            "parameter_key": "CHANDELIER_ATR_MULTIPLIER",
            "vix_reference": market_vix,
            "raw_multiplier": raw_stop_mult,
            "clamped_multiplier": clamped_stop_mult,
            "status": "REGIME_ADAPTIVE",
        }

        # 3. Slippage Governor
        trade_ledger = attribution_lake.get_trade_ledger(limit=100)
        slippages = [float(t.get("slippage_bps", 0.0)) for t in trade_ledger if t.get("slippage_bps")]
        avg_slippage = (sum(slippages) / len(slippages)) if slippages else 3.2
        slippage_status = "NORMAL_IMPACT" if avg_slippage < 25.0 else "HIGH_SLIPPAGE_WARNING"

        tuning_payload = {
            "last_calibrated": now_str,
            "safety_bounds": {
                "min_clamp": self.min_clamp,
                "max_clamp": self.max_clamp,
            },
            "calibrated_setups": calibrated_setups,
            "calibrated_stops": calibrated_stops,
            "slippage_governor": {
                "avg_slippage_bps": round(avg_slippage, 1),
                "status": slippage_status,
            },
        }

        if conn:
            try:
                conn.commit()
            except Exception:
                pass
            conn.close()

        # Persist to disk cache
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(tuning_payload, f, indent=2)
            logger.info(f"Auto-tuning completed and saved. Safety clamps [{self.min_clamp}x, {self.max_clamp}x] verified.")
        except Exception as e:
            logger.error(f"Failed to persist calibrated parameters: {e}")

        return tuning_payload

    def get_calibrated_multiplier(self, setup_name: str) -> float:
        """Fetch the calibrated conviction multiplier for a given setup archetype."""
        try:
            if self.cache_path.exists():
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    setups = data.get("calibrated_setups", {})
                    for k, v in setups.items():
                        if k.lower() in setup_name.lower() or setup_name.lower() in k.lower():
                            return float(v.get("calibrated_multiplier", 1.0))
        except Exception:
            pass
        return 1.0

    def get_tuning_report(self) -> Dict[str, Any]:
        """Retrieve current auto-tuning state."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return self.run_calibration()


parameter_tuner = ParameterTuner()
