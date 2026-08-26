<#
.SYNOPSIS
    Registers a Windows Scheduled Task to execute the Premarket Screener every weekday at 8:45 AM EST (5:45 AM PST).
#>

$ErrorActionPreference = "Stop"

$TaskName = "PremarketDashboard"
$PythonPath = "C:\Users\jfan\AppData\Local\Programs\Python\Python312\python.exe"
$ScriptPath = "c:\Users\jfan\Documents\Screener\run_screener.py"
$WorkingDir = "c:\Users\jfan\Documents\Screener"

# Verify files exist
if (-not (Test-Path $PythonPath)) {
    Write-Error "Python executable not found at: $PythonPath"
}
if (-not (Test-Path $ScriptPath)) {
    Write-Error "Screener script not found at: $ScriptPath"
}

# Determine local time corresponding to 8:45 AM EST (America/New_York)
try {
    $tzEastern = [System.TimeZoneInfo]::FindSystemTimeZoneById("Eastern Standard Time")
    $nowUtc = [System.DateTime]::UtcNow
    $easternNow = [System.TimeZoneInfo]::ConvertTimeFromUtc($nowUtc, $tzEastern)
    
    # Target 8:45 AM Eastern today
    $targetEastern = [System.DateTime]::new($easternNow.Year, $easternNow.Month, $easternNow.Day, 8, 45, 0)
    $targetUtc = [System.TimeZoneInfo]::ConvertTimeToUtc($targetEastern, $tzEastern)
    $targetLocal = [System.TimeZoneInfo]::ConvertTimeFromUtc($targetUtc, [System.TimeZoneInfo]::Local)
    $localTimeStr = $targetLocal.ToString("HH:mm")
    Write-Host "Target: 8:45 AM EST -> Local Machine Time: $localTimeStr ($([System.TimeZoneInfo]::Local.DisplayName))"
} catch {
    # Fallback to 5:45 AM for PST or 8:45 AM
    $localTimeStr = "05:45"
    Write-Host "Using default PST morning time: $localTimeStr"
}

Write-Host "Creating Scheduled Task '$TaskName' to run Mon-Fri at $localTimeStr local time..."

# Create Action
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$ScriptPath`"" -WorkingDirectory $WorkingDir

# Create Trigger (Weekly Monday through Friday)
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At $localTimeStr

# Create Settings (Wake computer, run as soon as possible if missed)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -WakeToRun

# Register or update task
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Runs the Automated Premarket Intelligence Screener and generates latest_report.html every morning at 8:45 AM EST."
    Write-Host "Task '$TaskName' successfully registered in Windows Task Scheduler!" -ForegroundColor Green
    Write-Host "Next run schedule:"
    Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo
} catch {
    Write-Warning "Could not register scheduled task: $_"
}
