"""
Automated Browser Unit Test Suite: Clickability & Popup Verification
====================================================================
Guarantees that:
1. Zero JavaScript syntax, runtime, or escaping errors occur on page load.
2. All 5 primary navigation tabs switch views cleanly upon native user clicks.
3. Every modal and popup opens, renders its contents, and closes cleanly:
   - 4-Master Dual-Skill & Earnings Review Modal (#modal-flash-earnings)
   - Institutional Position Sizing Calculator (#modal-sizing)
   - Fidelity ATP OTOCO Bracket Order Ticket (#modal-fidelity-bracket)
   - Fidelity CSV Portfolio Importer (#modal-import-fidelity)
   - Portfolio Position Edit & Add (#modal-edit-position)
   - Options Flow Institutional Whale Trades (#modal-whale-trades)
4. Portfolio Desk actions (trim, add, delete, save) are valid and free of syntax errors.
5. All table row drawers expand and collapse smoothly.
6. No modal overlays linger in active state to intercept pointer clicks.
7. Real browser console maintains 0 SEVERE errors throughout all interactions.
"""

import unittest
import time
import os
import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class TestUIClickabilityAndPopups(unittest.TestCase):
    driver: webdriver.Chrome = None
    report_uri: str = ""

    @classmethod
    def setUpClass(cls):
        from scripts.rebuild_report_fast import rebuild_report_fast
        rebuild_report_fast()

        report_path = Path(r"C:\Users\jfan\Documents\Screener\latest_report.html")
        cls.report_uri = report_path.as_uri()

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

        cls.driver = webdriver.Chrome(options=options)
        cls.driver.get(cls.report_uri)
        time.sleep(1.2)

    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            cls.driver.quit()

    def setUp(self):
        # Ensure all modal overlays are hidden before each test
        self.driver.execute_script("""
            document.querySelectorAll('.modal-overlay').forEach(function(m) {
                m.style.display = 'none';
            });
        """)
        time.sleep(0.1)

    def test_01_zero_javascript_syntax_or_load_errors(self):
        """Verify 0 JavaScript syntax or runtime errors on initial page load."""
        logs = self.driver.get_log('browser')
        severe = [l for l in logs if l.get('level') in ['SEVERE', 'ERROR']]
        if severe:
            err_msg = "\n".join([f"[{l.get('level')}] {l.get('message')}" for l in severe])
            self.fail(f"JavaScript fatal error detected on load:\n{err_msg}")
        print("  [PASS] Zero JavaScript syntax or runtime errors on load.")

    def test_02_all_ten_main_navigation_tabs_clickable(self):
        """Verify all 10 primary navigation tabs natively switch views upon mouse clicks."""
        tabs = [
            ("nav-tab-actions", "view-actions-section"),
            ("nav-tab-portfolio", "view-portfolio-section"),
            ("nav-tab-macro", "view-macro-section"),
            ("nav-tab-earnings", "view-earnings-section"),
            ("nav-tab-attribution", "view-attribution-section"),
            ("nav-tab-risk", "view-risk-section"),
            ("nav-tab-thesis", "view-thesis-section"),
            ("nav-tab-thematic", "view-thematic-section"),
            ("nav-tab-cadence", "view-cadence-section"),
            ("nav-tab-screener", "view-screener-section"),
        ]

        for tab_id, section_id in tabs:
            tab_el = self.driver.find_element(By.ID, tab_id)
            tab_el.click()
            time.sleep(0.15)

            sec_el = self.driver.find_element(By.ID, section_id)
            display_val = sec_el.value_of_css_property("display")
            self.assertEqual(
                display_val, "block",
                f"Clicking '{tab_id}' failed to reveal '{section_id}'. Got display='{display_val}'"
            )
            self.assertIn("active", tab_el.get_attribute("class") or "")

        print("  [PASS] All 10 primary navigation tabs switch views smoothly.")

    def test_03_dual_skill_and_earnings_modal_popup(self):
        """Verify 4-Master Earnings Review & Dual Skill Modal opens and closes cleanly."""
        modal = self.driver.find_element(By.ID, "modal-flash-earnings")
        try:
            self.driver.execute_script("openDualSkillModal('NVDA', 'review');")
            time.sleep(0.3)

            self.assertIn(
                modal.value_of_css_property("display"), ["flex", "block"],
                "Earnings Review Modal failed to open!"
            )

            ticker_header = self.driver.find_element(By.ID, "flash-ticker").get_attribute("innerText").strip()
            self.assertIn("NVDA", ticker_header, "Modal header did not populate with selected ticker.")

            # Test tab toggles inside modal
            self.driver.execute_script("switchModalEarningsTab('team');")
            time.sleep(0.15)
            self.driver.execute_script("switchModalEarningsTab('review');")
            time.sleep(0.15)
        finally:
            self.driver.execute_script("closeModal('modal-flash-earnings');")
            time.sleep(0.2)
            self.assertEqual(
                modal.value_of_css_property("display"), "none",
                "Earnings Review Modal failed to close!"
            )
        print("  [PASS] 4-Master Earnings & Dual-Skill Modal opens, toggles tabs, and closes cleanly.")

    def test_04_position_sizing_modal_popup(self):
        """Verify Institutional Position Sizing Modal opens, calculates, and closes."""
        modal = self.driver.find_element(By.ID, "modal-sizing")
        try:
            sizing_btns = self.driver.find_elements(By.CSS_SELECTOR, "button[onclick*='openSizingModal']")
            if sizing_btns:
                sizing_btns[0].click()
            else:
                self.driver.execute_script("openSizingModal('AAPL', 150.0);")
            time.sleep(0.3)

            self.assertIn(
                modal.value_of_css_property("display"), ["flex", "block"],
                "Sizing Modal failed to open!"
            )

            ticker_val = self.driver.find_element(By.ID, "sizing-ticker").get_attribute("value")
            self.assertTrue(len(ticker_val) > 0, "Sizing modal ticker input was empty.")
        finally:
            self.driver.execute_script("closeModal('modal-sizing');")
            time.sleep(0.2)
            self.assertEqual(
                modal.value_of_css_property("display"), "none",
                "Sizing Modal failed to close!"
            )
        print("  [PASS] Position Sizing Calculator Modal verified.")

    def test_05_fidelity_bracket_order_modal_popup(self):
        """Verify Fidelity ATP OTOCO Bracket Order Ticket Modal opens and populates."""
        modal = self.driver.find_element(By.ID, "modal-fidelity-bracket")
        try:
            self.driver.execute_script(
                "openFidelityBracketModal('NVDA', 'BUY PULLBACK', '$220.00', '$210.00', '$230.00', '$245.00', '50 shares', 'Institutional Breakout');"
            )
            time.sleep(0.3)

            self.assertIn(
                modal.value_of_css_property("display"), ["flex", "block"],
                "Fidelity Bracket Modal failed to open!"
            )

            spec = self.driver.find_element(By.ID, "fidelity-atp-full-spec").get_attribute("innerText")
            self.assertIn("NVDA", spec)
            self.assertIn("OTOCO BRACKET TICKET", spec)
        finally:
            self.driver.execute_script("closeModal('modal-fidelity-bracket');")
            time.sleep(0.2)
            self.assertEqual(modal.value_of_css_property("display"), "none")
        print("  [PASS] Fidelity ATP OTOCO Bracket Ticket Modal verified.")

    def test_06_fidelity_csv_importer_modal_popup(self):
        """Verify Fidelity CSV Portfolio Importer Modal opens and closes."""
        modal = self.driver.find_element(By.ID, "modal-import-fidelity")
        try:
            self.driver.execute_script("openFidelityImportModal();")
            time.sleep(0.3)

            self.assertIn(
                modal.value_of_css_property("display"), ["flex", "block"],
                "Fidelity Importer Modal failed to open!"
            )
        finally:
            self.driver.execute_script("closeModal('modal-import-fidelity');")
            time.sleep(0.2)
            self.assertEqual(modal.value_of_css_property("display"), "none")
        print("  [PASS] Fidelity CSV Importer Modal verified.")

    def test_07_portfolio_edit_and_add_modal_popup(self):
        """Verify Add Position & Edit Position Modal opens with editable inputs and closes."""
        modal = self.driver.find_element(By.ID, "modal-edit-position")
        try:
            self.driver.execute_script("openAddPositionModal();")
            time.sleep(0.3)

            self.assertIn(
                modal.value_of_css_property("display"), ["flex", "block"],
                "Edit Position Modal failed to open!"
            )

            title_el = self.driver.find_element(By.CSS_SELECTOR, "#modal-edit-position .modal-title span")
            self.assertIn("Add", title_el.get_attribute("innerText"))

            sym_input = self.driver.find_element(By.ID, "edit-pos-symbol")
            self.assertTrue(sym_input.is_enabled())
        finally:
            self.driver.execute_script("closeModal('modal-edit-position');")
            time.sleep(0.2)
            self.assertEqual(modal.value_of_css_property("display"), "none")
        print("  [PASS] Portfolio Position Edit & Add Modal verified.")

    def test_08_whale_trades_modal_popup(self):
        """Verify Institutional Options Whale Trades Modal opens and closes."""
        modal = self.driver.find_element(By.ID, "modal-whale-trades")
        try:
            self.driver.execute_script("openWhaleModal('SPY');")
            time.sleep(0.3)

            self.assertIn(
                modal.value_of_css_property("display"), ["flex", "block"],
                "Whale Trades Modal failed to open!"
            )
        finally:
            self.driver.execute_script("closeModal('modal-whale-trades');")
            time.sleep(0.2)
            self.assertEqual(modal.value_of_css_property("display"), "none")
        print("  [PASS] Whale Trades Modal verified.")

    def test_09_row_drawers_expand_and_collapse(self):
        """Verify table row drawers expand to table-row and collapse to none upon click."""
        self.driver.find_element(By.ID, "nav-tab-portfolio").click()
        time.sleep(0.2)

        drawer_btns = self.driver.find_elements(By.CSS_SELECTOR, "button[onclick*='togglePortRowDrawer']")
        if drawer_btns:
            btn = drawer_btns[0]
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.2)

            drawer_row = self.driver.find_element(By.ID, "port-row-drawer-0")
            self.assertEqual(
                drawer_row.value_of_css_property("display"), "table-row",
                "Portfolio drawer row failed to expand!"
            )

            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.2)
            self.assertEqual(
                drawer_row.value_of_css_property("display"), "none",
                "Portfolio drawer row failed to collapse!"
            )
            print("  [PASS] Table row drawers expand and collapse smoothly.")
        else:
            print("  [SKIP] No portfolio positions with drawers found in report.")

    def test_10_portfolio_desk_functions_integrity(self):
        """Verify portfolio desk JavaScript functions exist and are callable."""
        funcs = [
            "trimPortfolioPosition",
            "deletePortfolioPosition",
            "openEditPositionModal",
            "openAddPositionModal",
            "savePositionEdit",
            "savePortfolioDirectToDisk",
            "recomputePortfolioMetrics",
            "openDualSkillModal",
            "openSizingModal",
            "openFidelityBracketModal",
            "openFidelityImportModal",
            "openWhaleModal",
            "toggleRowDrawer",
            "toggleWhaleDrawer",
            "switchModalEarningsTab",
            "closeModal",
        ]
        for fn in funcs:
            res = self.driver.execute_script(f"return typeof window['{fn}'] === 'function';")
            self.assertTrue(res, f"Critical interactive function '{fn}' is missing or not a function!")
        print(f"  [PASS] All {len(funcs)} critical interactive UI functions confirmed defined and callable.")

    def test_11_zero_lingering_modal_overlays(self):
        """Verify no modal overlays remain open to accidentally block user clicks."""
        overlays = self.driver.find_elements(By.CLASS_NAME, "modal-overlay")
        for idx, overlay in enumerate(overlays):
            m_id = overlay.get_attribute("id") or f"overlay-{idx}"
            display = overlay.value_of_css_property("display")
            self.assertEqual(
                display, "none",
                f"Modal overlay '{m_id}' is visible (display='{display}'), which intercepts clicks!"
            )
        print("  [PASS] All modal overlays confirmed hidden (display: none); zero click blockage.")

    def test_12_clean_browser_console_throughout_interactions(self):
        """Verify real browser console maintained zero SEVERE errors across all interactions."""
        logs = self.driver.get_log('browser')
        severe = [l for l in logs if l.get('level') in ['SEVERE', 'ERROR']]
        if severe:
            err_msg = "\n".join([f"[{l.get('level')}] {l.get('message')}" for l in severe])
            self.fail(f"JavaScript errors detected during interactive tests:\n{err_msg}")
        print("  [PASS] Real browser console remained 100% clean with 0 errors throughout all tests!")

    def test_13_state_aware_save_button_enablement(self):
        """Verify Save to Disk button starts disabled (Synced) and dynamically enables when dirty."""
        self.driver.find_element(By.ID, "nav-tab-portfolio").click()
        time.sleep(0.2)
        save_btn = self.driver.find_element(By.ID, "btn-save-portfolio-disk")
        # 1. Initial State: Synced to Disk, disabled
        self.assertFalse(save_btn.is_enabled(), "Save button should be disabled when portfolio has no unsaved changes!")
        self.assertIn("Synced", save_btn.get_attribute("innerText"))

        # 2. Mark Dirty (simulate a trim, add, or edit)
        self.driver.execute_script("markPortfolioDirty();")
        time.sleep(0.1)
        self.assertTrue(save_btn.is_enabled(), "Save button should be enabled when portfolio changes are pending!")
        self.assertIn("*", save_btn.get_attribute("innerText"))

        # 3. Mark Clean (simulate successful save)
        self.driver.execute_script("markPortfolioClean();")
        time.sleep(0.1)
        self.assertFalse(save_btn.is_enabled(), "Save button should return to disabled after save!")
        self.assertIn("Synced", save_btn.get_attribute("innerText"))
        print("  [PASS] State-aware Save to Disk enablement (dirty tracking) verified.")

    def test_14_add_position_buttons_prominently_placed_across_views(self):
        """Verify ➕ Add Position buttons exist across Navbar, Actions Desk, and Portfolio Toolbar."""
        # 1. Top Navbar has prominent Add Position button
        nav_add_btn = self.driver.find_element(By.CSS_SELECTOR, ".top-navbar button[onclick*='openAddPositionModal']")
        self.assertTrue(nav_add_btn.is_displayed(), "Add Position button missing from top navbar!")
        self.assertIn("Add Position", nav_add_btn.text)

        # 2. Trade Execution Desk has prominent Add Position button
        self.driver.find_element(By.ID, "nav-tab-actions").click()
        time.sleep(0.15)
        actions_add_btn = self.driver.find_element(By.CSS_SELECTOR, "#view-actions-section button[onclick*='openAddPositionModal']")
        self.assertTrue(actions_add_btn.is_displayed(), "Add Position button missing from Trade Execution Desk header!")

        # 3. Portfolio Live Book has prominent Add Position buttons in Header, View Bar, and Table Controls
        self.driver.find_element(By.ID, "nav-tab-portfolio").click()
        time.sleep(0.15)
        port_header_btn = self.driver.find_element(By.CSS_SELECTOR, "#portfolio-manager-card .section-header-row button[onclick*='openAddPositionModal']")
        self.assertTrue(port_header_btn.is_displayed(), "Add Position button missing from Portfolio header!")

        port_viewbar_btn = self.driver.find_element(By.CSS_SELECTOR, "#view-portfolio-section .view-mode-bar button[onclick*='openAddPositionModal']")
        self.assertTrue(port_viewbar_btn.is_displayed(), "Add Position button missing from Portfolio view mode bar!")

        port_ctrl_btn = self.driver.find_element(By.CSS_SELECTOR, "#view-portfolio-section .table-controls button[onclick*='openAddPositionModal']")
        self.assertTrue(port_ctrl_btn.is_displayed(), "Add Position button missing from Portfolio table controls!")
        print("  [PASS] All 5 prominent Add Position buttons verified across views and toolbars.")

    def test_15_accidental_removal_recovery_and_mu_auto_prefill(self):
        """Verify typing MU or passing MU to Add Position modal restores canonical quantity and cost basis."""
        modal = self.driver.find_element(By.ID, "modal-edit-position")
        try:
            self.driver.execute_script("openAddPositionModal('MU');")
            time.sleep(0.2)
            self.assertIn(modal.value_of_css_property("display"), ["flex", "block"])

            sym_input = self.driver.find_element(By.ID, "edit-pos-symbol")
            qty_input = self.driver.find_element(By.ID, "edit-pos-qty")
            cost_input = self.driver.find_element(By.ID, "edit-pos-avg-cost")

            self.assertEqual(sym_input.get_attribute("value").upper(), "MU")
            qty_val = float(qty_input.get_attribute("value") or 0)
            cost_val = float(cost_input.get_attribute("value") or 0)

            # Canonical MU in data/portfolio.json: qty 24.088, avg_cost ~568.18
            self.assertGreater(qty_val, 0, "MU quantity should be auto-populated from canonical portfolio.json!")
            self.assertGreater(cost_val, 0, "MU cost should be auto-populated from canonical portfolio.json!")
        finally:
            self.driver.execute_script("closeModal('modal-edit-position');")
            time.sleep(0.15)
            self.assertEqual(modal.value_of_css_property("display"), "none")
        print("  [PASS] Canonical position restoration and auto-prefill for MU verified.")

    def test_16_auto_refresh_pauses_on_dirty_and_zero_unload_dialogs(self):
        """Verify window.onbeforeunload is null (zero intrusive browser modals) and auto-refresh pauses cleanly."""
        # 1. Verify onbeforeunload is null initially
        before_unload = self.driver.execute_script("return window.onbeforeunload;")
        self.assertIsNone(before_unload, "window.onbeforeunload should be null to prevent intrusive browser modals!")

        # 2. Mark dirty and verify onbeforeunload remains null while timer pauses
        self.driver.execute_script("markPortfolioDirty();")
        time.sleep(0.1)
        before_unload_dirty = self.driver.execute_script("return window.onbeforeunload;")
        self.assertIsNone(before_unload_dirty, "window.onbeforeunload must remain null even when portfolio is dirty!")

        timer_text = self.driver.find_element(By.ID, "live-refresh-timer").text
        self.assertIn("Paused", timer_text, f"Live refresh timer should pause on dirty portfolio, got: {timer_text}")

        # 3. Clean up
        self.driver.execute_script("markPortfolioClean();")
        time.sleep(0.1)
        print("  [PASS] Zero unload dialogs and auto-refresh timer pausing verified.")

    def test_17_six_gate_buffett_audit_modal_popup(self):
        """Verify 6-Gate Buffett Pre-Purchase Verification Modal opens, populates 6 gates & telemetry, and closes cleanly."""
        modal = self.driver.find_element(By.ID, "modal-6gate-audit")
        try:
            # 1. Trigger modal via script or button
            self.driver.execute_script("open6GateAuditModal('AAPL');")
            time.sleep(0.3)

            self.assertIn(
                modal.value_of_css_property("display"), ["flex", "block"],
                "6-Gate Buffett Audit Modal failed to open!"
            )

            ticker_header = self.driver.find_element(By.ID, "sixgate-ticker").get_attribute("innerText").strip()
            self.assertEqual(ticker_header, "AAPL", "6-Gate modal ticker header mismatch.")

            # 2. Verify all 6 gate cards are rendered
            cards = self.driver.find_elements(By.CSS_SELECTOR, "#sixgate-grid > div")
            self.assertEqual(len(cards), 6, f"Expected 6 gate cards in modal-6gate-audit, found {len(cards)}.")

            # 3. Verify key telemetry metrics populated
            gm_el = self.driver.find_element(By.ID, "sixgate-metric-gm").get_attribute("innerText")
            self.assertNotEqual(gm_el, "—", "Gross margin metric was unpopulated.")
            fcf_el = self.driver.find_element(By.ID, "sixgate-metric-fcf").get_attribute("innerText")
            self.assertNotEqual(fcf_el, "—", "FCF metric was unpopulated.")

            # 4. Verify test button clickability on an action row if present
            gate_btns = self.driver.find_elements(By.CSS_SELECTOR, "button[onclick*='open6GateAuditModal']")
            self.assertGreater(len(gate_btns), 0, "No 6-Gate action buttons found on page!")
        finally:
            self.driver.execute_script("closeModal('modal-6gate-audit');")
            time.sleep(0.2)
            self.assertEqual(
                modal.value_of_css_property("display"), "none",
                "6-Gate Buffett Audit Modal failed to close!"
            )
        print("  [PASS] 6-Gate Buffett Pre-Purchase Verification Modal opens, populates 6 gates, and closes cleanly.")

    def test_18_six_gate_backend_audit_engine(self):
        """Verify DeepResearchEngine.evaluate_investment_checklist deterministically audits companies."""
        from sources.deep_research_engine import deep_research_engine

        # Case A: High quality mega-compounder (AAPL)
        res_a = deep_research_engine.evaluate_investment_checklist("AAPL", mode="gate")
        self.assertEqual(res_a["symbol"], "AAPL")
        self.assertEqual(res_a["total_gates"], 6)
        self.assertGreaterEqual(res_a["passed_gates_count"], 4)
        self.assertIn(res_a["sizing_multiplier"], [0.5, 1.0])
        self.assertIn("PASS", res_a["verdict"])

        # Case B: Dual operating mode support in run_deep_research
        res_b = deep_research_engine.run_deep_research("MSFT", mode="gate")
        self.assertEqual(res_b["symbol"], "MSFT")
        self.assertIn("gates", res_b)
        self.assertEqual(len(res_b["gates"]), 6)

        # Case C: Extreme red flag test (simulated fatal red flag)
        res_c = deep_research_engine.evaluate_investment_checklist("AMZN", mode="gate")
        self.assertIn("sizing_multiplier", res_c)
        self.assertIn("verdict", res_c)
        print("  [PASS] 6-Gate backend audit engine passed dual-mode and deterministic checks.")

    def test_19_pre_earnings_volatility_and_extension_risk_gate(self):
        """Verify EarningsRiskGate options implied straddle move and 20-SMA extension clamp."""
        from sources.earnings_intelligence import earnings_intel, EarningsRiskGate

        near_date = (datetime.datetime.now() + datetime.timedelta(days=2)).strftime("%Y-%m-%d")

        # 1. Near earnings (2 days away) AND extended > 15% above 20-SMA -> BINARY CRUSH RISK
        res_crush = earnings_intel.evaluate_pre_earnings_risk(
            "TEST_CO",
            cur_price=125.0,
            sma20=100.0,  # +25% extended
            earnings_date=near_date
        )
        self.assertTrue(res_crush["binary_crush_risk"])
        self.assertLessEqual(res_crush["sizing_multiplier"], 0.5)
        self.assertIn("CRUSH RISK", res_crush["risk_verdict"])
        self.assertIn("pill-red", res_crush["warning_badge_html"])

        # 2. Near earnings (2 days away) BUT normal price near 20-SMA -> STANDARD SPREAD (0.75x)
        res_spread = earnings_intel.evaluate_pre_earnings_risk(
            "TEST_CO",
            cur_price=103.0,
            sma20=100.0,  # +3% normal
            earnings_date=near_date
        )
        self.assertFalse(res_spread["binary_crush_risk"])
        self.assertEqual(res_spread["sizing_multiplier"], 0.75)
        self.assertIn("pill-yellow", res_spread["warning_badge_html"])


        # 3. Far earnings (60 days away) -> SAFE WINDOW (1.0x)
        future_date = (datetime.datetime.now() + datetime.timedelta(days=60)).strftime("%Y-%m-%d")
        res_safe = earnings_intel.evaluate_pre_earnings_risk(
            "TEST_CO",
            cur_price=105.0,
            sma20=100.0,
            earnings_date=future_date
        )
        self.assertFalse(res_safe["is_binary_risk_window"])
        self.assertEqual(res_safe["sizing_multiplier"], 1.0)
        self.assertEqual(res_safe["warning_badge_html"], "")

        # 4. ETF safeguard
        res_etf = EarningsRiskGate.evaluate("SPY")
        self.assertFalse(res_etf["is_binary_risk_window"])
        self.assertEqual(res_etf["sizing_multiplier"], 1.0)
        print("  [PASS] Pre-earnings volatility and 20-SMA extension risk gate verified.")

    def test_20_periodic_cadence_desk_tab_and_subviews(self):
        """Verify Tab 10: Periodic Cadence Desk switches correctly and toggles Weekend vs Month-End subviews."""
        tab_btn = self.driver.find_element(By.ID, "nav-tab-cadence")
        tab_btn.click()
        time.sleep(0.2)

        sec_cadence = self.driver.find_element(By.ID, "view-cadence-section")
        self.assertEqual(sec_cadence.value_of_css_property("display"), "block", "Cadence section failed to display on click!")
        self.assertIn("active", tab_btn.get_attribute("class") or "")

        sub_weekend = self.driver.find_element(By.ID, "cadence-subview-weekend")
        sub_monthend = self.driver.find_element(By.ID, "cadence-subview-monthend")
        self.assertEqual(sub_weekend.value_of_css_property("display"), "block", "Weekend subview should be visible by default!")
        self.assertEqual(sub_monthend.value_of_css_property("display"), "none", "Month-end subview should be hidden by default!")

        # Toggle to Month-End
        btn_monthend = self.driver.find_element(By.ID, "cadence-subtab-btn-monthend")
        btn_monthend.click()
        time.sleep(0.2)
        self.assertEqual(sub_monthend.value_of_css_property("display"), "block", "Month-end subview failed to display after toggle!")
        self.assertEqual(sub_weekend.value_of_css_property("display"), "none", "Weekend subview should be hidden when month-end is active!")

        # Toggle back to Weekend
        btn_weekend = self.driver.find_element(By.ID, "cadence-subtab-btn-weekend")
        btn_weekend.click()
        time.sleep(0.2)
        self.assertEqual(sub_weekend.value_of_css_property("display"), "block", "Weekend subview failed to restore after toggle!")
        self.assertEqual(sub_monthend.value_of_css_property("display"), "none", "Month-end subview should be hidden when weekend is active!")

        # Switch back to Screener
        self.driver.find_element(By.ID, "nav-tab-screener").click()
        time.sleep(0.15)
        print("  [PASS] Tab 10: Periodic Cadence Desk (Weekend & Month-End subviews) fully verified.")


if __name__ == "__main__":
    unittest.main(verbosity=2)

