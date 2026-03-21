# Complete System Fix - One-Click Solution
# Executes all fixes and optimizations in sequence

Write-Host "🚀 Starting Complete System Fix..." -ForegroundColor Cyan
Write-Host "This will:" -ForegroundColor White
Write-Host "   1. Fix PowerShell Editor Services crashes" -ForegroundColor Gray
Write-Host "   2. Optimize system services" -ForegroundColor Gray
Write-Host "   3. Optimize memory usage" -ForegroundColor Gray
Write-Host "   4. Setup auto-start monitoring" -ForegroundColor Gray

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run this script as Administrator!"
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "`n🔧 Phase 1: PowerShell Editor Services Fix" -ForegroundColor Cyan
try {
    & "$scriptPath\fix_powershell_editor_services_fixed.ps1"
    Write-Host "✅ Phase 1 completed" -ForegroundColor Green
} catch {
    Write-Error "❌ Phase 1 failed: $($_.Exception.Message)"
}

Write-Host "`n⚙️ Phase 2: System Services Fix" -ForegroundColor Cyan
try {
    & "$scriptPath\fix_system_services.ps1"
    Write-Host "✅ Phase 2 completed" -ForegroundColor Green
} catch {
    Write-Error "❌ Phase 2 failed: $($_.Exception.Message)"
}

Write-Host "`n🧠 Phase 3: Memory Optimization" -ForegroundColor Cyan
try {
    & "$scriptPath\optimize_memory_usage.ps1"
    Write-Host "✅ Phase 3 completed" -ForegroundColor Green
} catch {
    Write-Error "❌ Phase 3 failed: $($_.Exception.Message)"
}

Write-Host "`n📊 Phase 4: Auto-Start Monitoring Setup" -ForegroundColor Cyan
try {
    & "$scriptPath\setup_monitoring_autostart.ps1"
    Write-Host "✅ Phase 4 completed" -ForegroundColor Green
} catch {
    Write-Error "❌ Phase 4 failed: $($_.Exception.Message)"
}

Write-Host "`n🎯 Final System Status" -ForegroundColor Cyan

# Check services
$services = Get-Service FDResPub, HPAppHelperCap -ErrorAction SilentlyContinue
Write-Host "Services Status:" -ForegroundColor White
foreach ($svc in $services) {
    $status = if ($svc.Status -eq "Running") { "✅" } else { "❌" }
    Write-Host "   $status $($svc.Name): $($svc.Status)" -ForegroundColor White
}

# Check memory
$cursorMemory = (Get-Process | Where-Object {$_.ProcessName -like "*cursor*"} | Measure-Object -Property WorkingSet -Sum).Sum / 1MB
$memoryStatus = if ($cursorMemory -lt 1200) { "✅" } else { "⚠️" }
Write-Host "   $memoryStatus Cursor Memory: $([math]::Round($cursorMemory, 2)) MB" -ForegroundColor White

# Check scheduled task
$task = Get-ScheduledTask -TaskName "PowerShell_Crash_Monitor" -ErrorAction SilentlyContinue
$taskStatus = if ($task) { "✅" } else { "❌" }
Write-Host "   $taskStatus Auto-Start Monitor: $(if ($task) { 'Configured' } else { 'Not found' })" -ForegroundColor White

Write-Host "`n📝 Post-Fix Instructions:" -ForegroundColor Cyan
Write-Host "1. RESTART YOUR COMPUTER for all changes to take full effect" -ForegroundColor Yellow
Write-Host "2. After restart, monitor should start automatically" -ForegroundColor White
Write-Host "3. Check log file: $env:USERPROFILE\Desktop\PowerShell_Crash_Monitor.log" -ForegroundColor White
Write-Host "4. Monitor for 48 hours to ensure stability" -ForegroundColor White

Write-Host "`n✅ Complete System Fix Finished!" -ForegroundColor Green
Write-Host "🎉 Your system should now be stable and optimized!" -ForegroundColor Green

Read-Host "Press Enter to exit"
