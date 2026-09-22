"""Unit tests for Phase 5 Order Router and Paper Execution Engine."""

import unittest
from sources.order_router import order_router, PaperTradingSimulator

class TestPhase5OrderRouter(unittest.TestCase):

    def setUp(self):
        self.sim = PaperTradingSimulator()
        self.sim.reset_paper_account(initial_cash=100000.0)

    def test_account_initialization(self):
        summary = self.sim.get_account_summary()
        self.assertEqual(summary["cash_balance"], 100000.0)
        self.assertEqual(summary["equity_value"], 0.0)
        self.assertEqual(summary["total_nav"], 100000.0)

    def test_buy_execution_and_positions(self):
        res = self.sim.execute_paper_order(
            symbol="NVDA",
            action="BUY",
            quantity=50,
            order_type="LIMIT",
            limit_price=200.0,
            market_price=200.0,
            strategy_tag="Minervini VCP",
        )
        self.assertEqual(res["status"], "FILLED")
        self.assertEqual(res["symbol"], "NVDA")
        self.assertEqual(res["quantity"], 50)
        self.assertLess(res["remaining_cash"], 100000.0)

        positions = self.sim.get_open_positions()
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]["symbol"], "NVDA")
        self.assertEqual(positions[0]["quantity"], 50)

    def test_sell_execution_and_pnl(self):
        # Buy 50 shares at 200
        self.sim.execute_paper_order("AAPL", "BUY", 50, "LIMIT", 200.0, market_price=200.0)
        # Sell 20 shares at 210
        sell_res = self.sim.execute_paper_order("AAPL", "SELL", 20, "LIMIT", 210.0, market_price=210.0)
        self.assertEqual(sell_res["status"], "FILLED")

        positions = self.sim.get_open_positions()
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]["symbol"], "AAPL")
        self.assertEqual(positions[0]["quantity"], 30)

    def test_smart_limit_order_slicing(self):
        tranches = order_router.slice_smart_ladder(
            symbol="MSFT",
            total_quantity=100,
            pivot_price=420.0,
            action="BUY"
        )
        self.assertEqual(len(tranches), 3)
        self.assertEqual(tranches[0]["quantity"] + tranches[1]["quantity"] + tranches[2]["quantity"], 100)
        self.assertLess(tranches[1]["limit_price"], tranches[0]["limit_price"])

if __name__ == "__main__":
    unittest.main()
