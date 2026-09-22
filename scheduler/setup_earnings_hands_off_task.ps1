<#
.SYNOPSIS
    Registers Windows Scheduled Tasks to execute Hands-Off Earnings Intelligence & Thesis Drift:
    1. Morning BMO Releases (8:00 AM EST / 5:00 AM PST)
    2. After-Hours AMC Releases (4:15 PM EST / 1:15 PM PST)
    3. Nightly SEC 10-Q / 10-K Audit Sweep (9:00 PM EST / 6:00 PM PST)
#>

$ErrorActionPreference = "Stop"

$PythonPath = "C:\Users\jfan\AppData\Local\Programs\Python\Python312\python.exe"
$ScriptPath = "c:\Users\jfan\Documents\Screener\scripts\run_hands_off_earnings_daemon.py"
$WorkingDir = "c:\Users\jfan\Documents\Screener"

if (-not (Test-Path $PythonPath)) {
    Write-Error "Python executable not found at: $PythonPath"
}
if (-not (Test-Path $ScriptPath)) {
    Write-Error "Daemon script not found at: $ScriptPath"
}

# Function to calculate local machine time for a given EST time
function Get-LocalTimeForEst {
    param ([int]$Hour, [int]$Minute)
    try {
        $tzEastern = [System.TimeZoneInfo]::FindSystemTimeZoneById("Eastern Standard Time")
        $nowUtc = [System.DateTime]::UtcNow
        $easternNow = [System.TimeZoneInfo]::ConvertTimeFromUtc($nowUtc, $tzEastern)
        $targetEastern = [System.DateTime]::new($easternNow.Year, $easternNow.Month, $easternNow.Day, $Hour, $Minute, 0)
        $targetUtc = [System.TimeZoneInfo]::ConvertTimeToUtc($targetEastern, $tzEastern)
        $targetLocal = [System.TimeZoneInfo]::ConvertTimeFromUtc($targetUtc, [System.TimeZoneInfo]::Local)
        return $targetLocal.ToString("HH:mm")
    } catch {
        # Fallback approximation: EST is 3 hours ahead of PST
        $localHour = ($Hour - 3 + 24) % 24
        return ("{0:D2}:{1:D2}" -f $localHour, $Minute)
    }
}

$Tasks = @(
    @{
        Name = "Earnings_BMO_FlashReview"
        Description = "Automated Morning BMO Earnings Processing & Flash Review"
        EstHour = 8
        EstMinute = 0
        Args = "`"$ScriptPath`" --session BMO"
    },
    @{
        Name = "Earnings_AMC_FlashReview"
        Description = "Automated After-Hours AMC Earnings Processing & Trade Desk Playbook"
        EstHour = 16
        EstMinute = 15
        Args = "`"$ScriptPath`" --session AMC"
    },
    @{
        Name = "Earnings_Nightly_10Q_Audit"
        Description = "Nightly SEC 10-Q/10-K Audit Sweep, True Accruals, and DuckDB Drift Logging"
        EstHour = 21
        EstMinute = 0
        Args = "`"$ScriptPath`" --audit-10q"
    }
)

Write-Host "Registering Hands-Off Earnings Intelligence Tasks in Windows Task Scheduler..." -ForegroundColor Cyan

foreach ($t in $Tasks) {
    $localTime = Get-LocalTimeForEst -Hour $t.EstHour -Minute $t.EstMinute
    Write-Host "Configuring '$($t.Name)' to run Mon-Fri at $localTime local time ($($t.EstHour):$($t.EstMinute) EST)..."
    
    $Action = New-ScheduledTaskAction -Execute $PythonPath -Argument $t.Args -WorkingDirectory $WorkingDir
    $Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At $localTime
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -WakeToRun

    try {
        Unregister-ScheduledTask -TaskName $t.Name -Confirm:$false -ErrorAction SilentlyContinue
        Register-ScheduledTask -TaskName $t.Name -Action $Action -Trigger $Trigger -Settings $Settings -Description $t.Description
        Write-Host " -> Task '$($t.Name)' successfully registered!" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to register '$($t.Name)': $_"
    }
}

Write-Host "`nAll Earnings Hands-Off tasks configured successfully!" -ForegroundColor Green
