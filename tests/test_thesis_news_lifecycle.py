"""Unit tests for Phase 6 Institutional Quantitative Integration:
- NewsPulseEngine: 2-factor beta residualization, multi-factor news signal, stealth flow detection
- ThesisMonitorEngine: Formulaic thesis health score, ATR volatility stop, quantitative drift
- SetupThesisLifecycleManager: Two-stage setup-to-thesis transition state machine
- PortfolioMonitorEngine & Waterfall: Action desk routing for Broken, Stealth, and Weakened theses
- ThesisLake: DuckDB analytical lake & SQLite schema synchronization
"""

import unittest
from sources.news_pulse import news_pulse, NewsPulseEngine
from sources.thesis_monitor import thesis_monitor, ThesisMonitorEngine
from sources.setup_thesis_lifecycle import lifecycle_mgr, SetupThesisLifecycleManager
from sources.thesis_lake import thesis_lake
from sources.portfolio_monitor_engine import PortfolioMonitorEngine


class TestThesisNewsLifecycle(unittest.TestCase):

    def setUp(self):
        self.news_engine = NewsPulseEngine()
        self.thesis_engine = ThesisMonitorEngine()
        self.lifecycle = SetupThesisLifecycleManager()

    # =========================================================================
    # 1. News Pulse & Residual Returns
    # =========================================================================

    def test_residual_return_calculation(self):
        # R_i = +5.0%, R_mkt = +1.0%, R_sec = +1.5%
        # Beta_spy = 1.2, Beta_sec = 0.8
        # Expected systematic = (1.2 * 0.01) + (0.8 * 0.015) = 0.012 + 0.012 = 0.024 (+2.4%)
        # Residual = 0.05 - 0.024 = 0.026 (+2.6%)
        res = self.news_engine.calculate_residual_return(
            stock_return=0.05,
            market_return=0.01,
            sector_return=0.015,
            beta_spy=1.2,
            beta_sector=0.8,
        )
        self.assertAlmostEqual(res["residual_return"], 0.026, places=4)
        self.assertGreater(res["residual_zscore"], 1.4)
        self.assertAlmostEqual(res["market_component"], 0.012, places=4)
        self.assertAlmostEqual(res["sector_component"], 0.012, places=4)

    def test_signal_score_formula(self):
        # Score = 0.4*R + 0.3*N + 0.2*A + 0.1*S
        # R=80, N=70, Authority="SEC_EDGAR" (100), Sentiment=0.8 (rescaled to 80.0)
        # 0.4*80 = 32.0, 0.3*70 = 21.0, 0.2*100 = 20.0, 0.1*80 = 8.0 -> Sum = 81.0
        score_data = self.news_engine.compute_signal_score(
            relevance=80.0,
            novelty=70.0,
            authority_or_source="SEC_EDGAR",
            sentiment=0.8,
        )
        self.assertAlmostEqual(score_data["composite_score"], 81.0, places=1)
        self.assertEqual(score_data["authority"], 100.0)

    def test_stealth_flow_detection(self):
        # Residual return +5.5% with quiet news (no catalyst text) -> Z >= 2.0 and Signal <= 50
        eval_res = self.news_engine.evaluate_portfolio_position(
            symbol="XYZ",
            price_change_pct=5.5,
            rvol=2.5,
            catalyst_text="",
            catalyst_source="",
        )
        self.assertTrue(eval_res["is_stealth"])
        self.assertGreaterEqual(eval_res["residuals"]["residual_zscore"], 2.0)
        self.assertLess(eval_res["signal"]["composite_score"], 50.0)

    def test_earnings_divergence(self):
        # Stock drops -6.5% despite blowout SUE (+2.5) and beat confirmation
        div = self.news_engine.evaluate_earnings_divergence(
            symbol="TECH1",
            pead_classification="TRIPLE_BULL_BEAT",
            sue=2.5,
            post_earnings_return_pct=-6.5,
        )
        self.assertEqual(div["scenario"], "PEAD_OVERREACTION_OPPORTUNITY")
        self.assertEqual(div["action"], "STAGE2_PULLBACK_CANDIDATE")
        self.assertIn("overreaction", div["label"].lower())

    # =========================================================================
    # 2. Thesis Health & Stop Calibration
    # =========================================================================

    def test_health_score_intact(self):
        # Zero broken, zero breached, one strength
        h = self.thesis_engine.compute_health_score(
            num_broken=0,
            num_breached=0,
            num_marginal=0,
            num_redlines=0,
            num_new_strengths=1,
        )
        self.assertEqual(h["health_score"], 10.0)
        self.assertEqual(h["category"], "STRONG")
        self.assertEqual(h["action"], "ADD_ELIGIBLE")

        # 1 marginal (-0.5) -> 9.5 (STRONG), 2 marginal (-1.0) -> 9.0 (STRONG), 3 marginal (-1.5) -> 8.5 (INTACT)
        h_intact = self.thesis_engine.compute_health_score(
            num_broken=0,
            num_breached=0,
            num_marginal=3,
            num_redlines=0,
            num_new_strengths=0,
        )
        self.assertEqual(h_intact["health_score"], 8.5)
        self.assertEqual(h_intact["category"], "INTACT")
        self.assertEqual(h_intact["action"], "HOLD")

    def test_health_score_damaged_and_broken(self):
        # 1 Broken (-3.0), 2 Breached (-3.0), 1 Marginal (-0.5) -> 10 - 6.5 = 3.5 (DAMAGED)
        h_damaged = self.thesis_engine.compute_health_score(
            num_broken=1,
            num_breached=2,
            num_marginal=1,
            num_redlines=0,
            num_new_strengths=0,
        )
        self.assertEqual(h_damaged["health_score"], 3.5)
        self.assertEqual(h_damaged["category"], "DAMAGED")
        self.assertIn("REDUCE", h_damaged["action"])

        # Critical redline (-2.0) + 2 broken (-6.0) + 1 breached (-1.5) -> 10 - 9.5 = 0.5 (CRITICAL_REDLINE)
        h_broken = self.thesis_engine.compute_health_score(
            num_broken=2,
            num_breached=1,
            num_marginal=0,
            num_redlines=1,
            num_new_strengths=0,
        )
        self.assertEqual(h_broken["health_score"], 0.5)
        self.assertEqual(h_broken["category"], "CRITICAL_REDLINE")
        self.assertEqual(h_broken["action"], "SELL_ALL")

    def test_dynamic_volatility_stop_iv_scaling(self):
        # Normal IV Rank (30%):
        stop_normal = self.thesis_engine.compute_dynamic_volatility_stop(
            current_price=100.0,
            highest_price_seen=105.0,
            atr14=4.0,
            iv_rank_pct=30.0,
        )
        # High IV Rank (90%): stop distance expands to avoid noise flush
        stop_high_iv = self.thesis_engine.compute_dynamic_volatility_stop(
            current_price=100.0,
            highest_price_seen=105.0,
            atr14=4.0,
            iv_rank_pct=90.0,
        )
        self.assertLess(stop_normal["stop_price"], 105.0)
        self.assertLess(stop_high_iv["stop_price"], stop_normal["stop_price"])
        self.assertGreater(stop_high_iv["stop_distance"], stop_normal["stop_distance"])

    # =========================================================================
    # 3. Two-Stage Setup-to-Thesis State Machine
    # =========================================================================

    def test_tactical_setup_promotion_on_target_1(self):
        # Target 1 hit (+2.1R) with clean Sloan accruals (3.5%)
        eval_res = self.lifecycle.evaluate_lifecycle_stage(
            symbol="NVDA",
            holding_days=5,
            current_price=122.0,
            entry_price=100.0,
            hard_stop=90.0,      # R = 10.0, gain = 22.0 -> +2.2R
            target_1=120.0,
            target_2=135.0,
            sloan_ratio_pct=3.5,
            sue_val=1.8,
        )
        self.assertEqual(eval_res["stage"], "CORE_THESIS")
        self.assertTrue(eval_res["promoted"])
        self.assertIn("Target 1", eval_res["promotion_reason"])

    def test_tactical_setup_retention_on_aggressive_accruals(self):
        # Target 1 hit, but Sloan accrual is +12% (aggressive/low quality earnings)
        eval_res = self.lifecycle.evaluate_lifecycle_stage(
            symbol="SPEC1",
            holding_days=6,
            current_price=125.0,
            entry_price=100.0,
            hard_stop=90.0,
            target_1=120.0,
            target_2=135.0,
            sloan_ratio_pct=12.5,
            sue_val=1.5,
        )
        self.assertEqual(eval_res["stage"], "TACTICAL_SETUP")
        self.assertFalse(eval_res["promoted"])
        self.assertIn("Accruals", eval_res["promotion_reason"])

    # =========================================================================
    # 4. Portfolio Monitor Waterfall Integration
    # =========================================================================

    def test_waterfall_broken_thesis_tier1_routing(self):
        port_monitor = PortfolioMonitorEngine()
        portfolio_data = {
            "positions": [
                {
                    "symbol": "FAIL1",
                    "shares": 100,
                    "current_price": 45.0,
                    "avg_cost": 55.0,
                    "hard_stop": 50.0,     # Stop breached (-10%)
                    "strategy_tag": "Breakout",
                    "sloan_ratio_pct": 14.0, # High accrual breach
                    "sue_val": -2.0,       # SUE disaster
                    "holding_days": 15,
                }
            ]
        }
        actions = port_monitor.sync_and_evaluate(portfolio_data["positions"], day_watchlist=[])
        broken_actions = [a for a in actions if a["priority_code"] == "TIER1" and "Broken Thesis" in a["priority_badge"]]
        self.assertGreaterEqual(len(broken_actions), 1)
        self.assertEqual(broken_actions[0]["priority_weight"], 105)
        self.assertIn("SELL ALL LIQUIDATE", broken_actions[0]["order_instruction"])

    # =========================================================================
    # 5. DuckDB & SQLite Lake Persistence
    # =========================================================================

    def test_thesis_lake_records_and_retrieval(self):
        # 1. Record a mock news event
        event_data = {
            "symbol": "TEST_TICKER",
            "trigger_type": "PORTFOLIO_MOVER",
            "residuals": {
                "stock_return": 0.045,
                "market_component": 0.005,
                "sector_component": 0.005,
                "residual_return": 0.035,
                "residual_zscore": 2.45,
            },
            "signal": {
                "composite_score": 25.0,
                "authority": 50.0,
                "novelty": 40.0,
            },
            "attribution": {
                "event_name": "Unexplained volume surge",
                "source": "PRICE_ACTION",
                "attribution_weight": 0.15,
                "is_stealth": True,
            }
        }
        ok_news = thesis_lake.record_news_event(event_data)
        self.assertTrue(ok_news)

        recent = thesis_lake.get_recent_news_events(limit=5)
        self.assertGreaterEqual(len(recent), 1)

        # 2. Record drift event
        ok_drift = thesis_lake.record_drift_event({
            "symbol": "TEST_TICKER",
            "prior_health_score": 9.5,
            "new_health_score": 8.0,
            "broken_assumptions": 0,
            "breached_assumptions": 1,
            "redlines_triggered": 0,
            "quantitative_drift_score": 1.5,
            "action_recommended": "HOLD_POSITION",
        })
        self.assertTrue(ok_drift)

        drift_hist = thesis_lake.get_drift_history(symbol="TEST_TICKER", limit=5)
        self.assertGreaterEqual(len(drift_hist), 1)
        self.assertEqual(drift_hist[0]["symbol"], "TEST_TICKER")


if __name__ == "__main__":
    unittest.main()
