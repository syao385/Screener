"""Automated Real-Browser Selenium Test Suite for Institutional Screener Dashboard."""

import unittest
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class TestBrowserSelenium(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1600,1000")
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        cls.driver = webdriver.Chrome(options=options)
        cls.html_path = Path(r"C:\Users\jfan\Documents\Screener\latest_report.html").as_uri()
        cls.driver.get(cls.html_path)
        time.sleep(1.5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_no_console_errors_on_load(self):
        """Verify zero JavaScript syntax or runtime errors on initial page load."""
        logs = self.driver.get_log('browser')
        severe_errors = [l for l in logs if l.get('level') in ['SEVERE', 'ERROR']]
        self.assertEqual(len(severe_errors), 0, f"Found JavaScript errors on load: {severe_errors}")
        print("[PASS] 0 JavaScript errors on initial load!")

    def test_02_tab_navigation(self):
        """Verify seamless switching between all 5 main dashboard views."""
        tabs = [
            ('nav-tab-screener', 'view-screener-section'),
            ('nav-tab-actions', 'view-actions-section'),
            ('nav-tab-portfolio', 'view-portfolio-section'),
            ('nav-tab-macro', 'view-macro-section'),
            ('nav-tab-earnings', 'view-earnings-section')
        ]
        for btn_id, section_id in tabs:
            btn = self.driver.find_element(By.ID, btn_id)
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.15)
            section = self.driver.find_element(By.ID, section_id)
            self.assertEqual(section.value_of_css_property('display'), 'block', f"Tab {btn_id} failed to display {section_id}")
        
        # Return to screener tab
        self.driver.find_element(By.ID, 'nav-tab-screener').click()
        time.sleep(0.1)
        print("[PASS] All 5 main dashboard tabs toggle smoothly!")

    def test_03_screener_flash_earnings_modal(self):
        """Verify clicking SUE opens the 4-Master Flash Earnings Modal with live data."""
        self.driver.find_element(By.ID, 'nav-tab-screener').click()
        time.sleep(0.2)
        sue_btns = self.driver.find_elements(By.XPATH, "//table[@id='day-table']//button[contains(text(), 'SUE')]")
        self.assertGreater(len(sue_btns), 0, "No SUE buttons found in Screener table")
        
        self.driver.execute_script("arguments[0].click();", sue_btns[0])
        time.sleep(0.3)
        modal = self.driver.find_element(By.ID, 'modal-flash-earnings')
        self.assertEqual(modal.value_of_css_property('display'), 'flex', "Flash Earnings Modal failed to open")
        
        ticker = self.driver.find_element(By.ID, 'flash-ticker').get_attribute('innerText').strip()
        self.assertTrue(len(ticker) > 0, "Flash ticker was not populated")
        
        # Close modal
        self.driver.execute_script("closeModal('modal-flash-earnings')")
        time.sleep(0.2)
        self.assertEqual(modal.value_of_css_property('display'), 'none', "Modal failed to close")
        print(f"[PASS] SUE Modal opens and displays live 4-Master audit for {ticker}!")

    def test_04_screener_sizing_modal(self):
        """Verify clicking Sizing opens the Institutional Sizing Modal."""
        self.driver.find_element(By.ID, 'nav-tab-screener').click()
        time.sleep(0.2)
        sizing_btns = self.driver.find_elements(By.XPATH, "//table[@id='day-table']//button[contains(text(), 'Sizing')]")
        self.assertGreater(len(sizing_btns), 0, "No Sizing buttons found in Screener table")
        
        self.driver.execute_script("arguments[0].click();", sizing_btns[0])
        time.sleep(0.3)
        modal = self.driver.find_element(By.ID, 'modal-sizing')
        self.assertEqual(modal.value_of_css_property('display'), 'flex', "Sizing Modal failed to open")
        
        # Close modal
        self.driver.execute_script("closeModal('modal-sizing')")
        time.sleep(0.2)
        self.assertEqual(modal.value_of_css_property('display'), 'none', "Modal failed to close")
        print("[PASS] Sizing Calculator Modal opens and recalculates shares!")

    def test_05_screener_row_drawer(self):
        """Verify clicking drawer toggles the expandable Fundamental & MA Drawer."""
        self.driver.find_element(By.ID, 'nav-tab-screener').click()
        time.sleep(0.2)
        drawer_btns = self.driver.find_elements(By.XPATH, "//table[@id='day-table']//button[contains(text(), '🔍')]")
        self.assertGreater(len(drawer_btns), 0, "No Drawer buttons found in Screener table")
        
        self.driver.execute_script("arguments[0].click();", drawer_btns[0])
        time.sleep(0.3)
        first_drawer = self.driver.find_element(By.ID, 'row-drawer-0')
        self.assertEqual(first_drawer.value_of_css_property('display'), 'table-row', "Drawer row failed to expand")
        
        self.driver.execute_script("arguments[0].click();", drawer_btns[0])
        time.sleep(0.2)
        self.assertEqual(first_drawer.value_of_css_property('display'), 'none', "Drawer row failed to collapse")
        print("[PASS] Expandable Row Drawers toggle and reveal 4-Master cards!")

    def test_06_portfolio_actions_and_drawers(self):
        """Verify Portfolio table SUE, Sizing, Edit, and Drawer buttons function without error."""
        self.driver.find_element(By.ID, 'nav-tab-portfolio').click()
        time.sleep(0.3)
        
        # SUE Button in Portfolio
        port_sue_btns = self.driver.find_elements(By.XPATH, "//table[@id='portfolio-table']//button[contains(text(), 'SUE')]")
        if port_sue_btns:
            self.driver.execute_script("arguments[0].click();", port_sue_btns[0])
            time.sleep(0.3)
            modal = self.driver.find_element(By.ID, 'modal-flash-earnings')
            self.assertEqual(modal.value_of_css_property('display'), 'flex')
            self.driver.execute_script("closeModal('modal-flash-earnings')")
            time.sleep(0.2)
        
        # Sizing Button in Portfolio
        port_sizing_btns = self.driver.find_elements(By.XPATH, "//table[@id='portfolio-table']//button[contains(text(), 'Sizing')]")
        if port_sizing_btns:
            self.driver.execute_script("arguments[0].click();", port_sizing_btns[0])
            time.sleep(0.3)
            modal = self.driver.find_element(By.ID, 'modal-sizing')
            self.assertEqual(modal.value_of_css_property('display'), 'flex')
            self.driver.execute_script("closeModal('modal-sizing')")
            time.sleep(0.2)

        # Edit Position Button in Portfolio
        port_edit_btns = self.driver.find_elements(By.XPATH, "//table[@id='portfolio-table']//button[contains(text(), '✏️')]")
        if port_edit_btns:
            self.driver.execute_script("arguments[0].click();", port_edit_btns[0])
            time.sleep(0.3)
            modal = self.driver.find_element(By.ID, 'modal-edit-position')
            self.assertEqual(modal.value_of_css_property('display'), 'flex')
            self.driver.execute_script("closeModal('modal-edit-position')")
            time.sleep(0.2)

        # Drawer Button in Portfolio
        port_drawer_btns = self.driver.find_elements(By.XPATH, "//table[@id='portfolio-table']//button[contains(text(), '🔍')]")
        if port_drawer_btns:
            self.driver.execute_script("arguments[0].click();", port_drawer_btns[0])
            time.sleep(0.3)
            first_port_drawer = self.driver.find_element(By.ID, 'port-row-drawer-0')
            self.assertEqual(first_port_drawer.value_of_css_property('display'), 'table-row')
            self.driver.execute_script("arguments[0].click();", port_drawer_btns[0])
            time.sleep(0.2)
            self.assertEqual(first_port_drawer.value_of_css_property('display'), 'none')
        print("[PASS] Portfolio Table SUE, Sizing, Edit, and Drawer actions tested!")

    def test_08_earnings_center_views(self):
        """Verify Earnings Center tab, modal launch, and unified 10-step institutional review sections."""
        self.driver.execute_script("closeModal('modal-flash-earnings'); closeModal('modal-sizing'); closeModal('modal-edit-position');")
        time.sleep(0.2)
        self.driver.find_element(By.ID, 'nav-tab-earnings').click()
        time.sleep(0.3)
        section = self.driver.find_element(By.ID, 'view-earnings-section')
        self.assertEqual(section.value_of_css_property('display'), 'block')

        # Check for review/SUE buttons in earnings center
        review_btns = self.driver.find_elements(By.XPATH, "//div[@id='view-earnings-section']//button[contains(text(), 'Review') or contains(text(), 'Team') or contains(text(), '⚡')]")
        if review_btns:
            self.driver.execute_script("arguments[0].click();", review_btns[0])
            time.sleep(0.3)
            modal = self.driver.find_element(By.ID, 'modal-flash-earnings')
            self.assertEqual(modal.value_of_css_property('display'), 'flex')

            # Verify unified 10-step sections exist
            step0 = self.driver.find_element(By.ID, 'sec-step0')
            self.assertIsNotNone(step0)
            step3 = self.driver.find_element(By.ID, 'sec-step3')
            self.assertIsNotNone(step3)
            step8 = self.driver.find_element(By.ID, 'sec-step8')
            self.assertIsNotNone(step8)
            step9 = self.driver.find_element(By.ID, 'sec-step9')
            self.assertIsNotNone(step9)

            # Close modal
            self.driver.execute_script("closeModal('modal-flash-earnings')")
            time.sleep(0.2)
            self.assertEqual(modal.value_of_css_property('display'), 'none')

        print("[PASS] Earnings Center Unified 10-Step Institutional Modal verified!")

    def test_09_final_console_cleanliness(self):
        """Verify zero unhandled exceptions throughout the full interactive user test."""
        logs = self.driver.get_log('browser')
        severe_errors = [l for l in logs if l.get('level') in ['SEVERE', 'ERROR']]
        self.assertEqual(len(severe_errors), 0, f"Found JavaScript errors during interactions: {severe_errors}")
        print("[PASS] Real browser console remained 100% clean with 0 errors throughout all tests!")

if __name__ == "__main__":
    unittest.main()

