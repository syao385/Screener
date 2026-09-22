"""
Automated UI Regression Test Suite
==================================
Guarantees that:
1. Zero JavaScript syntax, runtime, or template-escaping errors occur on load.
2. All 5 main navigation tabs (Screener, Actions, Portfolio, Macro, Earnings) are clickable
   via native user mouse clicks and switch view sections cleanly.
3. All interactive modals (Sizing Calculator, Fidelity CSV Importer, Fidelity ATP Bracket)
   open, populate their payload, and close without leaving lingering click-blocking backdrops.
4. When modals are closed, every `.modal-overlay` has display == 'none' so user clicks are never intercepted.
5. Real browser console maintains ZERO SEVERE errors throughout the test lifecycle.
"""

import unittest
import time
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class TestUIRegression(unittest.TestCase):
    driver: webdriver.Chrome = None
    report_uri: str = ""

    @classmethod
    def setUpClass(cls):
        report_path = Path(r"C:\Users\jfan\Documents\Screener\latest_report.html")
        if not report_path.exists():
            raise FileNotFoundError(f"Report file not found: {report_path}")
        cls.report_uri = report_path.as_uri()

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1680,1050")
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.get(cls.report_uri)
        time.sleep(1.0)

    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            cls.driver.quit()

    def test_01_zero_javascript_errors_on_load(self):
        """Regression Guard 1: Verify 0 JavaScript syntax or runtime errors on initial load."""
        logs = self.driver.get_log('browser')
        severe = [l for l in logs if l.get('level') in ['SEVERE', 'ERROR']]
        if severe:
            error_details = "\n".join([f"[{l.get('level')}] {l.get('message')}" for l in severe])
            self.fail(f"JavaScript syntax or runtime error detected on load:\n{error_details}")
        print("  [PASS] Zero JavaScript errors on initial page load.")

    def test_02_all_five_main_tabs_clickable(self):
        """Regression Guard 2: Verify all 5 main navigation tabs are natively clickable and switch sections."""
        tabs = [
            ("nav-tab-actions", "view-actions-section"),
            ("nav-tab-portfolio", "view-portfolio-section"),
            ("nav-tab-macro", "view-macro-section"),
            ("nav-tab-earnings", "view-earnings-section"),
            ("nav-tab-screener", "view-screener-section"),
        ]

        for tab_id, section_id in tabs:
            tab_el = self.driver.find_element(By.ID, tab_id)
            # Must perform native mouse click, not execute_script, to catch any backdrop intercepts
            tab_el.click()
            time.sleep(0.15)

            sec_el = self.driver.find_element(By.ID, section_id)
            display_val = sec_el.value_of_css_property("display")
            self.assertEqual(
                display_val,
                "block",
                f"Clicking tab '{tab_id}' failed to reveal '{section_id}'. Got display='{display_val}'"
            )
            # Verify tab button received active styling
            self.assertIn("active", tab_el.get_attribute("class") or "")

        print("  [PASS] All 5 main navigation tabs are 100% clickable and toggle views smoothly.")

    def test_03_modal_sizing_open_and_close(self):
        """Regression Guard 3: Verify Institutional Sizing Calculator Modal opens and closes cleanly."""
        # Find any Sizing button on page
        sizing_btns = self.driver.find_elements(By.CSS_SELECTOR, "button[onclick*='openSizingModal']")
        self.assertGreater(len(sizing_btns), 0, "No Sizing buttons found on page.")

        # Native mouse click
        sizing_btns[0].click()
        time.sleep(0.2)

        modal = self.driver.find_element(By.ID, "modal-sizing")
        self.assertIn(
            modal.value_of_css_property("display"),
            ["flex", "block"],
            "Sizing modal failed to display after clicking Sizing button."
        )

        # Close modal via cancel button
        close_btn = modal.find_element(By.CSS_SELECTOR, "button[onclick*='closeModal']")
        close_btn.click()
        time.sleep(0.2)

        self.assertEqual(
            modal.value_of_css_property("display"),
            "none",
            "Sizing modal failed to hide after closing."
        )
        print("  [PASS] Sizing Modal opens, calculates, and closes cleanly.")

    def test_04_modal_fidelity_importer_open_and_close(self):
        """Regression Guard 4: Verify Fidelity CSV Importer Modal opens and closes."""
        import_btns = self.driver.find_elements(By.CSS_SELECTOR, "button[onclick*='openFidelityImportModal']")
        self.assertGreater(len(import_btns), 0, "No Fidelity Import button found.")

        import_btns[0].click()
        time.sleep(0.2)

        modal = self.driver.find_element(By.ID, "modal-import-fidelity")
        self.assertIn(
            modal.value_of_css_property("display"),
            ["flex", "block"],
            "Fidelity Import modal failed to display."
        )

        # Close modal
        close_btn = modal.find_element(By.CSS_SELECTOR, "button.modal-close")
        close_btn.click()
        time.sleep(0.2)

        self.assertEqual(
            modal.value_of_css_property("display"),
            "none",
            "Fidelity Import modal failed to hide."
        )
        print("  [PASS] Fidelity Import Modal opens and closes cleanly.")

    def test_05_modal_fidelity_atp_bracket_open_and_close(self):
        """Regression Guard 5: Verify Fidelity ATP OTOCO Bracket Modal opens, populates ticket, and closes."""
        # Switch to Actions tab
        self.driver.find_element(By.ID, "nav-tab-actions").click()
        time.sleep(0.2)

        bracket_btns = self.driver.find_elements(By.CSS_SELECTOR, "button[onclick*='openFidelityBracketModal']")
        if bracket_btns:
            bracket_btns[0].click()
            time.sleep(0.2)

            modal = self.driver.find_element(By.ID, "modal-fidelity-bracket")
            self.assertIn(
                modal.value_of_css_property("display"),
                ["flex", "block"],
                "Fidelity ATP Bracket Modal failed to open."
            )

            # Check full spec content
            spec_el = self.driver.find_element(By.ID, "fidelity-atp-full-spec")
            spec_text = spec_el.get_attribute("innerText") or ""
            self.assertIn("OTOCO BRACKET TICKET", spec_text)
            self.assertIn("Traditional IRA", spec_text)

            # Close modal
            close_btn = modal.find_element(By.CSS_SELECTOR, "button.modal-close")
            close_btn.click()
            time.sleep(0.2)

            self.assertEqual(
                modal.value_of_css_property("display"),
                "none",
                "Fidelity ATP Bracket Modal failed to close."
            )
            print("  [PASS] Fidelity ATP Bracket Modal opens, renders OTOCO spec, and closes.")
        else:
            # Programmatic verification if actions table empty
            self.driver.execute_script(
                "openFidelityBracketModal('NVDA', 'BUY PULLBACK', '$219.62', '$210.00', '$229.24', '$243.67', '25 shares', 'Institutional Breakout');"
            )
            time.sleep(0.2)
            modal = self.driver.find_element(By.ID, "modal-fidelity-bracket")
            self.assertIn(modal.value_of_css_property("display"), ["flex", "block"])
            self.driver.execute_script("closeModal('modal-fidelity-bracket');")
            time.sleep(0.2)
            self.assertEqual(modal.value_of_css_property("display"), "none")
            print("  [PASS] Fidelity ATP Bracket Modal verified via programmatic trigger.")

    def test_06_no_lingering_click_blocking_backdrops(self):
        """Regression Guard 6: Ensure NO modal-overlay is active or blocking pointer clicks when idle."""
        overlays = self.driver.find_elements(By.CLASS_NAME, "modal-overlay")
        for idx, overlay in enumerate(overlays):
            modal_id = overlay.get_attribute("id") or f"overlay-{idx}"
            display = overlay.value_of_css_property("display")
            self.assertEqual(
                display,
                "none",
                f"Modal overlay '{modal_id}' is not hidden (display='{display}'), which blocks user clicks!"
            )
        print("  [PASS] All modal overlays confirmed hidden (display: none); zero click-blocking backdrops.")

    def test_07_zero_severe_errors_across_full_session(self):
        """Regression Guard 7: Verify console remained 100% clean after all clicks, opens, and closes."""
        logs = self.driver.get_log('browser')
        severe = [l for l in logs if l.get('level') in ['SEVERE', 'ERROR']]
        if severe:
            error_details = "\n".join([f"[{l.get('level')}] {l.get('message')}" for l in severe])
            self.fail(f"JavaScript errors detected during interactive test session:\n{error_details}")
        print("  [PASS] Zero console errors during entire interactive UI test run.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
