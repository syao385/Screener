# Windows Task Scheduler & Automation Guide
 
## Living Document Version History

| Version | Date | Changes & Enhancements | Author / Status |
|---|---|---|---|
| **v1.0.0** | 2026-08-20 | Initial setup guide for 5:45 AM PST scheduled task with WakeToRun power flags. | Production |
| **v3.0.0** | 2026-08-22 | Documented multi-session real-time streaming mode (`--realtime`), 24/7 background execution, and CLI controls. | Production |
| **v4.0.0** | 2026-09-04 | Added documentation for Phase 3 5-session scheduler registration (`register_windows_tasks.ps1`), Post-Market Attribution Lake syncer (16:30 ET), and Overnight Parameter Auto-Tuning workflow (20:00 ET, `--session calibration`). | Active Standard |
| **v5.0.0** | 2026-09-06 | Phase 6: Added manual test verification procedures for autonomous daemon workflows (`--session premarket`, `--session postmarket`, `--status`), confirming 2-factor News Pulse attribution and thesis drift auditing. | Production |
| **v6.0.0** | 2026-09-13 | Phase 7: Documented `Start_Live_Screener.bat` continuous execution with Zero-Redundancy Fundamental Caching and Client-Side Smart 60s Auto-Refresh with typing/modal guards. | Production |
| **v7.0.0** | 2026-09-22 | Phase 9-11 Institutional v2.0 Release: Documented the 4-session daily cadence automation (Premarket, Opening Bell, Mid-Day, Postmarket), Windows Task batch manager (`manage_tasks.bat`), and Hands-Off Earnings Review Daemon (`setup_earnings_hands_off_task.ps1`). | Active Standard |

---

## 1. Automated Execution Modes

### Mode A: Windows Scheduled Task (Daily Morning Snapshot)
- **Task Name**: `PremarketDashboard`
- **Trigger**: Every weekday (Monday through Friday) at **5:45 AM PST** (8:45 AM EST).
- **Action**: Executes `run_screener.py --headless` via Python 3.12.
- **Output**: Generates fresh [`latest_report.html`](file:///c:/Users/jfan/Documents/Screener/latest_report.html).

### Mode B: Continuous Real-Time Streaming & Live Cockpit
- **Batch Launcher**: Double-click [`Start_Live_Screener.bat`](file:///c:/Users/jfan/Documents/Screener/Start_Live_Screener.bat) or run `python run_screener.py --realtime`
- **Zero-Redundancy Fundamental Caching**: Reuses local DuckDB lake & JSON caches; only fetches remote fundamentals when earnings actively break.
- **Smart 60s Live Auto-Refresh**: `latest_report.html` features an integrated live reload engine that refreshes the browser every 60 seconds.
  - **Typing & Modal Activity Guard**: Reloads pause automatically when modals are open or text inputs are focused.
  - **Scroll & View Tab Memory**: Preserves exact tab selection and pixel scroll position between reloads.

### Mode C: Autonomous Multi-Session System Daemon (4 Cadence Sessions)
- **Script**: [`scheduler/system_daemon.py`](file:///c:/Users/jfan/Documents/Screener/scheduler/system_daemon.py)
- **Session 1: Premarket (08:00 - 09:15 EST, `--session premarket`)**: Scans universe, triggers macro circuit breaker, evaluates morning gaps, and runs **News Pulse mover & stealth flow sentry** across all portfolio holdings.
- **Session 2: Opening Bell (09:30 - 10:15 EST, `--session regular`)**: Evaluates 5-minute Opening Range Breakouts (ORB), monitors RVOL surges against the 09:30 anchor, and stages Tier 1/2 execution queue.
- **Session 3: Mid-Day (12:00 - 13:00 EST, `--session intraday`)**: Re-evaluates VWAP hold/loss levels, audits intra-day thesis drift, and detects stealth volume accumulation.
- **Session 4: Postmarket (16:30 - 18:00 EST, `--session postmarket`)**: Runs EOD screener, commits NAV/equity to DuckDB Attribution Lake, executes bounded auto-tuning, audits fleet-wide **Thesis Health scores**, and ingests **Post-Market News Pulse attribution** and SEC filings for movers.

### Mode D: Hands-Off Earnings Review Daemon
- **Registration**: Execute `scheduler/setup_earnings_hands_off_task.ps1` to register the dedicated scheduled task.
- **Script**: [`scripts/run_hands_off_earnings_daemon.py`](file:///c:/Users/jfan/Documents/Screener/scripts/run_hands_off_earnings_daemon.py)
- **Operation**: Automatically scans the 3-day active earnings calendar (Yesterday AMC, Today BMO, Today AMC), downloads and parses fresh SEC 10-Q/8-K filings into `data/earnings_lake.duckdb`, executes 4-master consensus reviews, and generates comprehensive markdown audit dossiers in `reports/earnings_review/` with zero human intervention.

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

### A. Testing the System Daemon Sessions
Run these commands from PowerShell or cmd in the project root:

```powershell
# 1. Query current daemon heartbeat and market session phase
python scheduler/system_daemon.py --status

# 2. Manually test Premarket Session (Screener + News Pulse Portfolio Sentry)
python scheduler/system_daemon.py --session premarket

# 3. Manually test Postmarket Session (Attribution Lake + Thesis Health Audit + News Pulse Ingestion)
python scheduler/system_daemon.py --session postmarket

# 4. Check live DuckDB recorded events
python -c "from sources.thesis_lake import thesis_lake; print(thesis_lake.get_recent_news_events(limit=5))"
```

### B. Testing Windows Task Scheduler Task
```powershell
# Manually trigger the scheduled task right now
Start-ScheduledTask -TaskName "PremarketDashboard"

# Check status and last run time of the scheduled task
Get-ScheduledTask -TaskName "PremarketDashboard" | Get-ScheduledTaskInfo
```

