import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_argument('--headless')
options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
driver = webdriver.Chrome(options=options)

html_path = 'file:///' + os.path.abspath('latest_report.html').replace('\\', '/')
print(f"Loading {html_path}...")
driver.get(html_path)

logs = driver.get_log('browser')
print(f"Console Logs ({len(logs)} entries):")
for entry in logs:
    print(f"  [{entry['level']}] {entry['message']}")

# Test clicking nav tabs
tabs = ["nav-tab-screener", "nav-tab-actions", "nav-tab-portfolio", "nav-tab-macro", "nav-tab-earnings"]
for tab_id in tabs:
    try:
        el = driver.find_element(By.ID, tab_id)
        el.click()
        print(f"Tab click {tab_id}: SUCCESS")
    except Exception as e:
        print(f"Tab click {tab_id}: FAILED -> {e}")

# Test clicking sizing button
try:
    btn = driver.find_element(By.CSS_SELECTOR, "button[onclick*='openSizingModal']")
    btn.click()
    print("Sizing modal button click: SUCCESS")
    modal = driver.find_element(By.ID, "modal-sizing")
    print("modal-sizing display:", modal.value_of_css_property("display"))
except Exception as e:
    print(f"Sizing modal button click: FAILED -> {e}")

driver.quit()
