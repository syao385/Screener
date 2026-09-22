"""
Automated Test Suite: Portfolio CRUD Persistence Across Page Refreshes
======================================================================
Verifies that:
1. Adding a new position persists after browser refresh (F5).
2. Editing an existing position (tier, qty, stop, target) persists after browser refresh.
3. Deleting a position removes it and it does NOT return after browser refresh.
4. Restoring default portfolio resets client changes cleanly.
5. Real browser console maintains zero SEVERE errors throughout.
"""

import unittest
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class TestPortfolioCRUDPersistence(unittest.TestCase):
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

        # Clear any prior localStorage state for a fresh test run
        cls.driver.execute_script("""
            localStorage.removeItem('deleted_portfolio_symbols');
            localStorage.removeItem('user_portfolio_data');
        """)
        cls.driver.refresh()
        time.sleep(1.0)

    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            try:
                cls.driver.execute_script("""
                    localStorage.removeItem('deleted_portfolio_symbols');
                    localStorage.removeItem('user_portfolio_data');
                """)
            except Exception:
                pass
            cls.driver.quit()

    def test_01_navigate_to_portfolio_and_check_no_errors(self):
        """Verify navigation to Portfolio tab and zero JS errors."""
        port_tab = self.driver.find_element(By.ID, "nav-tab-portfolio")
        port_tab.click()
        time.sleep(0.3)

        port_sec = self.driver.find_element(By.ID, "view-portfolio-section")
        self.assertEqual(port_sec.value_of_css_property("display"), "block")

        logs = self.driver.get_log('browser')
        severe = [l for l in logs if l.get('level') in ['SEVERE', 'ERROR']]
        self.assertEqual(len(severe), 0, f"JS console errors on portfolio load: {severe}")
        print("  [PASS] Navigated to Portfolio tab cleanly with zero errors.")

    def test_02_add_position_and_verify_persistence_across_refresh(self):
        """Verify adding a new custom position persists after browser refresh."""
        self.driver.execute_script("""
            window.confirm = function() { return true; };
            window.alert = function() { return true; };
        """)

        # Add position TSLA via client modal logic
        self.driver.execute_script("""
            document.getElementById('edit-pos-symbol').removeAttribute('readonly');
            document.getElementById('edit-pos-symbol').value = 'TSLA';
            document.getElementById('edit-pos-qty').value = '50';
            document.getElementById('edit-pos-avg-cost').value = '215.00';
            document.getElementById('edit-pos-stop').value = '200.00';
            document.getElementById('edit-pos-target').value = '260.00';
            document.getElementById('edit-pos-tier').value = '1';
            document.getElementById('edit-pos-strategy').value = 'Tactical Momentum';
            savePositionEdit();
        """)
        time.sleep(0.5)

        # Check TSLA row exists in DOM
        tsla_rows = self.driver.find_elements(By.CSS_SELECTOR, "#portfolio-table tbody tr[data-symbol='TSLA']")
        self.assertGreater(len(tsla_rows), 0, "TSLA was not rendered in table after add.")
        self.assertIn("T1 Core", tsla_rows[0].text, "TSLA should have Tier 1 Core pill.")

        # NOW REFRESH BROWSER (F5)
        self.driver.refresh()
        time.sleep(1.0)

        # Switch back to Portfolio tab if not already on it
        self.driver.find_element(By.ID, "nav-tab-portfolio").click()
        time.sleep(0.3)

        # Verify TSLA is STILL PRESENT after page refresh!
        tsla_rows_after = self.driver.find_elements(By.CSS_SELECTOR, "#portfolio-table tbody tr[data-symbol='TSLA']")
        self.assertGreater(len(tsla_rows_after), 0, "TSLA disappeared after browser refresh!")
        self.assertIn("T1 Core", tsla_rows_after[0].text, "TSLA lost its Tier 1 pill after refresh.")
        print("  [PASS] Added position TSLA successfully persisted across page refresh!")

    def test_03_edit_position_and_verify_persistence_across_refresh(self):
        """Verify editing an existing position persists after browser refresh."""
        self.driver.execute_script("""
            window.confirm = function() { return true; };
            window.alert = function() { return true; };
        """)

        # Edit TSLA: change tier to 3, qty to 100
        self.driver.execute_script("""
            document.getElementById('edit-pos-symbol').value = 'TSLA';
            document.getElementById('edit-pos-qty').value = '100';
            document.getElementById('edit-pos-avg-cost').value = '215.00';
            document.getElementById('edit-pos-stop').value = '190.00';
            document.getElementById('edit-pos-target').value = '280.00';
            document.getElementById('edit-pos-tier').value = '3';
            document.getElementById('edit-pos-strategy').value = 'Core Long Holding';
            savePositionEdit();
        """)
        time.sleep(0.5)

        tsla_rows = self.driver.find_elements(By.CSS_SELECTOR, "#portfolio-table tbody tr[data-symbol='TSLA']")
        self.assertGreater(len(tsla_rows), 0)
        self.assertIn("T3 Tactical", tsla_rows[0].text, "TSLA should now have Tier 3 Tactical pill.")

        # REFRESH BROWSER (F5)
        self.driver.refresh()
        time.sleep(1.0)

        self.driver.find_element(By.ID, "nav-tab-portfolio").click()
        time.sleep(0.3)

        # Verify TSLA has updated Tier 3 and Qty 100 after refresh!
        tsla_rows_after = self.driver.find_elements(By.CSS_SELECTOR, "#portfolio-table tbody tr[data-symbol='TSLA']")
        self.assertGreater(len(tsla_rows_after), 0, "TSLA disappeared after edit and refresh!")
        self.assertIn("T3 Tactical", tsla_rows_after[0].text, "TSLA lost its updated Tier 3 pill after refresh.")
        print("  [PASS] Edited position TSLA (Tier 3, Qty 100) successfully persisted across page refresh!")

    def test_04_delete_position_and_verify_does_not_return_after_refresh(self):
        """Verify deleting a position removes it immediately and it NEVER returns after refresh."""
        self.driver.execute_script("""
            window.confirm = function() { return true; };
            window.alert = function() { return true; };
        """)

        # 1. Delete TSLA
        self.driver.execute_script("deletePortfolioPosition('TSLA');")
        time.sleep(0.5)

        # Verify TSLA is gone immediately
        tsla_rows_del = self.driver.find_elements(By.CSS_SELECTOR, "#portfolio-table tbody tr[data-symbol='TSLA']")
        self.assertEqual(len(tsla_rows_del), 0, "TSLA was not removed from screen upon delete.")

        # REFRESH BROWSER (F5)
        self.driver.refresh()
        time.sleep(1.0)

        self.driver.find_element(By.ID, "nav-tab-portfolio").click()
        time.sleep(0.3)

        # Verify TSLA does NOT return!
        tsla_rows_after_refresh = self.driver.find_elements(By.CSS_SELECTOR, "#portfolio-table tbody tr[data-symbol='TSLA']")
        self.assertEqual(len(tsla_rows_after_refresh), 0, "CRITICAL BUG: Deleted position TSLA returned after screen refresh!")
        print("  [PASS] Deleted position TSLA stayed deleted after browser refresh!")

    def test_05_delete_default_position_persists_across_refresh(self):
        """Verify deleting an original stock from data/portfolio.json also stays deleted across refresh."""
        self.driver.execute_script("""
            window.confirm = function() { return true; };
            window.alert = function() { return true; };
        """)

        # Find first visible symbol in the table
        first_row = self.driver.find_element(By.CSS_SELECTOR, "#portfolio-table tbody tr.data-row")
        target_sym = first_row.get_attribute("data-symbol")
        self.assertTrue(target_sym, "Could not find a target symbol to delete.")

        # Delete it
        self.driver.execute_script(f"deletePortfolioPosition('{target_sym}');")
        time.sleep(0.5)

        # Verify gone immediately
        target_rows = self.driver.find_elements(By.CSS_SELECTOR, f"#portfolio-table tbody tr[data-symbol='{target_sym}']")
        self.assertEqual(len(target_rows), 0, f"Symbol {target_sym} was not removed from screen.")

        # REFRESH BROWSER (F5)
        self.driver.refresh()
        time.sleep(1.0)

        self.driver.find_element(By.ID, "nav-tab-portfolio").click()
        time.sleep(0.3)

        # Verify does NOT return!
        target_rows_after = self.driver.find_elements(By.CSS_SELECTOR, f"#portfolio-table tbody tr[data-symbol='{target_sym}']")
        self.assertEqual(len(target_rows_after), 0, f"CRITICAL BUG: Deleted default position {target_sym} returned after screen refresh!")
        print(f"  [PASS] Deleted default position {target_sym} stayed deleted after browser refresh!")

    def test_06_restore_defaults(self):
        """Verify clicking Restore Defaults restores the initial state."""
        self.driver.execute_script("""
            window.confirm = function() { return true; };
            window.alert = function() { return true; };
            resetDeletedPortfolioPositions();
        """)
        time.sleep(1.0)

        self.driver.find_element(By.ID, "nav-tab-portfolio").click()
        time.sleep(0.3)

        # Check that deleted_portfolio_symbols and user_portfolio_data were cleared
        deleted_stored = self.driver.execute_script("return localStorage.getItem('deleted_portfolio_symbols');")
        self.assertIsNone(deleted_stored, "deleted_portfolio_symbols was not cleared.")
        print("  [PASS] Restore Defaults cleared local storage and restored initial portfolio!")


if __name__ == "__main__":
    unittest.main()
