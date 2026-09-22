<#
.SYNOPSIS
  Registers Institutional Screener multi-session workflows into Windows Task Scheduler.

.DESCRIPTION
  Creates scheduled tasks for:
    1. Screener_PreMarket       (Mon-Fri at 08:45 AM)
    2. Screener_OpeningBell     (Mon-Fri at 09:35 AM)
    3. Screener_MidDay          (Mon-Fri at 12:00 PM)
    4. Screener_PowerHour_EOD   (Mon-Fri at 03:45 PM)
    5. Screener_PostMarket      (Mon-Fri at 04:30 PM)
    6. Screener_Live_Daemon     (Continuous background service at startup/logon)

.PARAMETER Action
  Register, Unregister, Status, or RunNow. Default is Register.
#>

param(
    [ValidateSet("Register", "Unregister", "Status", "RunNow")]
    [string]$Action = "Register",
    [string]$TaskName = ""
)

$ErrorActionPreference = "Stop"
$WorkingDir = (Get-Item $PSScriptRoot).Parent.FullName

# Locate Python Interpreter
$PythonPath = "C:\Users\jfan\AppData\Local\Programs\Python\Python312\python.exe"
if (-not (Test-Path $PythonPath)) {
    $PythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCmd) {
        $PythonPath = $PythonCmd.Source
    } else {
        Write-Error "Python interpreter not found. Please install Python 3.12 or specify path."
        exit 1
    }
}

$DaemonScript = Join-Path $WorkingDir "scheduler\system_daemon.py"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  INSTITUTIONAL SCREENER - WINDOWS TASK SCHEDULER" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Working Directory: $WorkingDir"
Write-Host "Python Executable: $PythonPath"
Write-Host "Action:            $Action"
Write-Host ""

$Tasks = @(
    @{
        Name        = "Screener_PreMarket"
        Description = "Institutional Screener 08:45 ET Pre-Market Focus Scan"
        Session     = "premarket"
        Time        = "08:45"
    },
    @{
        Name        = "Screener_OpeningBell"
        Description = "Institutional Screener 09:35 ET Opening Bell and ORB Surge Check"
        Session     = "opening_bell"
        Time        = "09:35"
    },
    @{
        Name        = "Screener_MidDay"
        Description = "Institutional Screener 12:00 ET Mid-Day Pullback and Stop Audit"
        Session     = "midday"
        Time        = "12:00"
    },
    @{
        Name        = "Screener_PowerHour_EOD"
        Description = "Institutional Screener 15:45 ET Power Hour and EOD Exit Checks"
        Session     = "eod"
        Time        = "15:45"
    },
    @{
        Name        = "Screener_PostMarket"
        Description = "Institutional Screener 16:30 ET Post-Market Earnings Syncer"
        Session     = "postmarket"
        Time        = "16:30"
    }
)

if ($Action -eq "Register") {
    foreach ($t in $Tasks) {
        Write-Host "Registering task: $($t.Name) at $($t.Time) (Mon-Fri)..." -ForegroundColor Yellow
        $Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $t.Time
        $ArgsStr = "`"$DaemonScript`" --session $($t.Session)"
        $TaskAction = New-ScheduledTaskAction -Execute $PythonPath -Argument $ArgsStr -WorkingDirectory $WorkingDir
        $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2)

        Register-ScheduledTask -TaskName $t.Name `
            -Trigger $Trigger `
            -Action $TaskAction `
            -Settings $Settings `
            -Description $t.Description `
            -Force | Out-Null

        Write-Host "  [OK] $($t.Name) successfully registered." -ForegroundColor Green
    }

    # Also register continuous daemon for background live monitoring
    Write-Host "Registering task: Screener_Live_Daemon (Continuous at Logon)..." -ForegroundColor Yellow
    try {
        $LogonTrigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
        $DaemonArgs = "`"$DaemonScript`" --continuous"
        $DaemonAction = New-ScheduledTaskAction -Execute $PythonPath -Argument $DaemonArgs -WorkingDirectory $WorkingDir
        $DaemonSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit 0

        Register-ScheduledTask -TaskName "Screener_Live_Daemon" `
            -Trigger $LogonTrigger `
            -Action $DaemonAction `
            -Settings $DaemonSettings `
            -Description "Institutional Screener 24/7 Continuous Background Risk Daemon" `
            -Force | Out-Null
        Write-Host "  [OK] Screener_Live_Daemon successfully registered." -ForegroundColor Green
    } catch {
        Write-Host "  [NOTE] Screener_Live_Daemon at logon requires elevated admin ($($_.Exception.Message))." -ForegroundColor Gray
        Write-Host "         The 5 session tasks (PreMarket, OpeningBell, MidDay, PowerHour, PostMarket) are active and do not require admin." -ForegroundColor Green
    }

    Write-Host "`nTasks registered successfully in Windows Task Scheduler." -ForegroundColor Green
}
elseif ($Action -eq "Unregister") {
    foreach ($t in $Tasks) {
        Write-Host "Unregistering task: $($t.Name)..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $t.Name -Confirm:$false -ErrorAction SilentlyContinue
    }
    Unregister-ScheduledTask -TaskName "Screener_Live_Daemon" -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "All screener scheduled tasks unregistered." -ForegroundColor Green
}
elseif ($Action -eq "Status") {
    Write-Host "Checking scheduled task statuses:" -ForegroundColor Yellow
    Write-Host ""
    $AllNames = ($Tasks | ForEach-Object { $_.Name }) + @("Screener_Live_Daemon")
    foreach ($name in $AllNames) {
        $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
        if ($task) {
            $info = Get-ScheduledTaskInfo -TaskName $name -ErrorAction SilentlyContinue
            Write-Host "  * $($name): State=$($task.State) | LastRun=$($info.LastRunTime) | LastResult=$($info.LastTaskResult)" -ForegroundColor Green
        } else {
            Write-Host "  * $($name): NOT REGISTERED" -ForegroundColor Gray
        }
    }
}
elseif ($Action -eq "RunNow") {
    if (-not $TaskName) {
        $TaskName = "Screener_PreMarket"
    }
    Write-Host "Triggering scheduled task now: $TaskName..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "Task triggered." -ForegroundColor Green
}
