"""Test script for Phase 3: Order Execution Desk, Alert Dispatcher & System Daemon."""

import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Ensure project root in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sources.order_execution_desk import order_desk
from sources.alert_dispatcher import alert_dispatcher
from scheduler.system_daemon import SystemDaemon

print("==================================================")
print("  PHASE 3 FEATURES VERIFICATION & UNIT TEST")
print("==================================================")

# 1. Test Order Execution Desk Ticket Generation
print("\n--- TEST 1: FIDELITY ACTIVE TRADER PRO (ATP) TICKET GENERATION ---")
ticket = order_desk.create_fidelity_bracket_ticket(
    ticker="NVDA",
    action="BUY",
    shares=25,
    entry_price=219.62,
    stop_price=210.00,
    target_1=229.24,
    target_2=243.67,
    setup_type="BASE_BREAKOUT",
    conviction_tier="Tier 2: High-Growth Tactical Leaders",
)

print(f"Order ID: {ticket['order_id']}")
print(f"Concise Clipboard String:\n  👉 {ticket['clipboard_str']}\n")
print(f"Fidelity.com Web Format:\n{ticket['fidelity_web_text']}\n")
print(f"Fidelity ATP Bracket Ticket:\n{ticket['fidelity_atp_bracket_text']}")

assert "BUY 25 NVDA" in ticket["clipboard_str"], "Clipboard string missing BUY 25 NVDA"
assert "OTOCO" in ticket["fidelity_atp_bracket_text"], "ATP text missing OTOCO"
assert "229.24" in ticket["fidelity_atp_bracket_text"], "ATP text missing target 1"
print("\n[OK] Test 1: Fidelity ATP & Web Tickets Verified Successfully.")

# 2. Test Emergency Exit & Trim Tickets
print("\n--- TEST 2: EMERGENCY STOP EXIT & TRIM TICKETS ---")
exit_ticket = order_desk.create_fidelity_exit_ticket(
    ticker="SOXL",
    shares=34,
    current_price=102.38,
    stop_price=103.42,
    reason="Protective Stop Breached",
)
print(f"Emergency Exit Clipboard String:\n  👉 {exit_ticket['clipboard_str']}")

trim_ticket = order_desk.create_fidelity_trim_ticket(
    ticker="SMH",
    trim_shares=15,
    current_price=245.50,
    reason="Sector Flow Distribution Invalidation",
)
print(f"Trim Ticket Clipboard String:\n  👉 {trim_ticket['clipboard_str']}")

assert exit_ticket["action"] == "SELL"
assert trim_ticket["action"] == "SELL"
print("\n[OK] Test 2: Exit & Trim Tickets Verified Successfully.")

# 3. Test Alert Dispatcher
print("\n--- TEST 3: ALERT DISPATCHER (DESKTOP & TELEGRAM) ---")
print(f"Telegram Configured: {alert_dispatcher.is_telegram_configured()}")
print(f"Notification Level:  {alert_dispatcher.notification_level}")
print(f"Desktop Toast:       {alert_dispatcher.enable_desktop}")
print(f"Audio Chime:         {alert_dispatcher.enable_audio}")

# Trigger test dispatch (Desktop toast + sound)
res = alert_dispatcher.dispatch(
    title="Institutional Screener Phase 3",
    message="Phase 3 Order Desk & Daemon features initialized successfully.",
    urgency="NORMAL",
    sound=False,
)
print(f"Dispatch Result: {res}")
assert res["desktop"] is True
print("\n[OK] Test 3: Alert Dispatcher Verified Successfully.")

# 4. Test System Daemon Session Classifier & Heartbeat
print("\n--- TEST 4: SYSTEM DAEMON SESSION STATE MACHINE ---")
daemon = SystemDaemon()
sess = daemon.get_current_session()
print(f"Timestamp:       {sess['timestamp']}")
print(f"Market Phase:    {sess['phase']}")
print(f"Market Status:   {sess['status']}")
print(f"Is Regular Hrs:  {sess['is_regular_hours']}")

daemon.emit_heartbeat("TEST_VERIFICATION")
assert daemon.heartbeat_file.exists(), "Heartbeat file was not written"
print(f"Heartbeat File:  {daemon.heartbeat_file} (Written successfully)")
print("\n[OK] Test 4: System Daemon State Machine & Heartbeat Verified.")

print("\n==================================================")
print("  ALL PHASE 3 UNIT TESTS PASSED (4/4)")
print("==================================================")
