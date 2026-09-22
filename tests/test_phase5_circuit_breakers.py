"""Unit tests for Phase 5 Circuit Breakers and Capital Preservation Governor."""

import unittest
from sources.risk_circuit_breakers import circuit_breaker_governor, CircuitBreakerState

class TestPhase5CircuitBreakers(unittest.TestCase):

    def setUp(self):
        circuit_breaker_governor.reset_circuit_breaker(new_nav=336870.83)

    def test_normal_state_evaluation(self):
        res = circuit_breaker_governor.evaluate_intraday_nav(current_nav=336870.83, dispatch_alerts=False)
        self.assertEqual(res["circuit_breaker_level"], CircuitBreakerState.NORMAL)
        self.assertEqual(res["intraday_drawdown_pct"], 0.0)

    def test_level1_warning_transition(self):
        # -1.2% drawdown
        res = circuit_breaker_governor.evaluate_intraday_nav(current_nav=336870.83 * 0.988, dispatch_alerts=False)
        self.assertEqual(res["circuit_breaker_level"], CircuitBreakerState.WARNING)

    def test_level2_derisk_transition(self):
        # -2.2% drawdown
        res = circuit_breaker_governor.evaluate_intraday_nav(current_nav=336870.83 * 0.978, dispatch_alerts=False)
        self.assertEqual(res["circuit_breaker_level"], CircuitBreakerState.DERISK)

    def test_level3_kill_switch_transition(self):
        # -3.5% drawdown
        res = circuit_breaker_governor.evaluate_intraday_nav(current_nav=336870.83 * 0.965, dispatch_alerts=False)
        self.assertEqual(res["circuit_breaker_level"], CircuitBreakerState.KILL_SWITCH)

    def test_reset_functionality(self):
        circuit_breaker_governor.evaluate_intraday_nav(current_nav=336870.83 * 0.965, dispatch_alerts=False)
        state_after_reset = circuit_breaker_governor.reset_circuit_breaker(new_nav=336870.83)
        self.assertEqual(state_after_reset["circuit_breaker_level"], CircuitBreakerState.NORMAL)
        self.assertEqual(state_after_reset["intraday_drawdown_pct"], 0.0)

if __name__ == "__main__":
    unittest.main()
