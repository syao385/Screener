"""
One-click CLI Runner for UI Interactivity & Regression Testing
============================================================
Executes the headless Selenium Chrome UI regression guard:
  - Asserts 0 JavaScript syntax, runtime, or template errors.
  - Tests native clickability for all 5 dashboard navigation tabs.
  - Verifies modal opening, calculations, and clean closing.
  - Verifies zero click-blocking backdrops remain active.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath("."))
import unittest

if __name__ == "__main__":
    print("=" * 60)
    print("  INSTITUTIONAL SCREENER — REAL BROWSER UI REGRESSION SUITE")
    print("=" * 60)
    suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_ui_regression")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n[SUCCESS] All UI regression guards passed with 0 errors!")
        sys.exit(0)
    else:
        print("\n[FAILURE] UI regression detected! Check details above.")
        sys.exit(1)
