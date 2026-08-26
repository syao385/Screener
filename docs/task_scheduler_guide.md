# Windows Task Scheduler & Automation Guide
 
## Living Document Version History

| Version | Date | Changes & Enhancements | Author / Status |
|---|---|---|---|
| **v1.0.0** | 2026-08-20 | Initial setup guide for 5:45 AM PST scheduled task with WakeToRun power flags. | Production |
| **v2.0.0** | 2026-08-21 | Added sleep mode troubleshooting and instant catch-up verification. | Production |
| **v3.0.0** | 2026-08-22 | Documented multi-session real-time streaming mode (`--realtime`), 24/7 background execution, and CLI controls. | Active Standard |

---

## 1. Automated Execution Modes

### Mode A: Windows Scheduled Task (Daily Morning Snapshot)
- **Task Name**: `PremarketDashboard`
- **Trigger**: Every weekday (Monday through Friday) at **5:45 AM PST** (8:45 AM EST).
- **Action**: Executes `run_screener.py --headless` via Python 3.12.
- **Output**: Generates fresh [`latest_report.html`](file:///c:/Users/jfan/Documents/Screener/latest_report.html).

### Mode B: Continuous Real-Time Streaming (Live Intraday Loop)
- **Command**: `python run_screener.py --realtime`
- **Behavior**: Executes continuous scan cycles every 60 seconds (`REALTIME_REFRESH_INTERVAL = 60`), dynamically updating `latest_report.html` and terminal viewer.

---

## 2. Configured Windows Power Settings for Sleep & Wake

| Setting | Value | Meaning |
|---|---|---|
| **WakeToRun** | `True` | Instructs Windows to wake the laptop from Sleep (S3 / Modern Standby) to run the task at 5:45 AM. |
| **StartWhenAvailable** | `True` | **Missed Run Catch-up**: If the laptop is closed or in deep sleep at 5:45 AM, the moment you open the lid or wake the laptop, Windows **immediately** triggers the screener. |
| **DisallowStartIfOnBatteries** | `False` | Allows the task to start even if running on battery power. |
| **StopIfGoingOnBatteries** | `False` | Does not terminate execution if the power cable is unplugged. |

---

## 3. Best Practices for Unattended Execution

1. **Keep Connected to AC Power**: Plug your laptop into its charger overnight. Windows reliably wakes up on AC power.
2. **Leave in Sleep Mode**: Put the laptop to Sleep (do not shut down or drain battery into deep hibernate).
3. **Instant Catch-up**: Because `StartWhenAvailable: True` is enabled, even if the lid was closed at 5:45 AM, opening the lid triggers the pipeline instantly.

---

## 4. Manual Verification & Test Commands

```powershell
# Manually trigger the scheduled task right now
Start-ScheduledTask -TaskName "PremarketDashboard"

# Check status and last run time of the scheduled task
Get-ScheduledTask -TaskName "PremarketDashboard" | Get-ScheduledTaskInfo
```

