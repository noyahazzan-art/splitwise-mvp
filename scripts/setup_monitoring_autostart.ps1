# Setup Auto-Start Monitoring with Windows Task Scheduler
# This creates a scheduled task to auto-start the crash prevention monitor

Write-Host "🔧 Setting up auto-start monitoring..." -ForegroundColor Cyan

# Task details
$taskName = "PowerShell_Crash_Monitor"
$taskDescription = "PowerShell Editor Services Crash Prevention Monitor"
$scriptPath = "$PSScriptRoot\monitor_and_prevent_crashes.ps1"
$workingDirectory = Split-Path $scriptPath -Parent

# Check if script exists
if (-not (Test-Path $scriptPath)) {
    Write-Error "Monitor script not found: $scriptPath"
    exit 1
}

# Remove existing task if it exists
try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "   ✓ Removed existing task" -ForegroundColor Green
} catch {
    Write-Host "   ℹ️ No existing task to remove" -ForegroundColor Gray
}

# Create new scheduled task
try {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`"" -WorkingDirectory $workingDirectory
    $trigger = New-ScheduledTaskTrigger -AtLogon -User $env:USERNAME
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Days 9999)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description $taskDescription
    
    Write-Host "   ✓ Created scheduled task: $taskName" -ForegroundColor Green
    Write-Host "   ✓ Monitor will start automatically on user login" -ForegroundColor Green
    
} catch {
    Write-Error "Failed to create scheduled task: $($_.Exception.Message)"
    exit 1
}

# Verify task creation
try {
    $task = Get-ScheduledTask -TaskName $taskName
    if ($task) {
        Write-Host "   ✓ Task verification successful" -ForegroundColor Green
        Write-Host "   ✓ Task will run as: $($task.Principal.UserId)" -ForegroundColor Green
        Write-Host "   ✓ Trigger: At user logon" -ForegroundColor Green
    }
} catch {
    Write-Warning "Task verification failed: $($_.Exception.Message)"
}

Write-Host "✅ Auto-start monitoring setup completed!" -ForegroundColor Green
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Log off and log back in to test auto-start" -ForegroundColor White
Write-Host "   2. Check Task Scheduler for the '$taskName' task" -ForegroundColor White
Write-Host "   3. Monitor should start automatically and create log file" -ForegroundColor White
