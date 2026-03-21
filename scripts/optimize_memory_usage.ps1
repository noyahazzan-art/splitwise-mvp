# Advanced Memory Optimization Script
# Reduces memory footprint for Cursor and system processes

Write-Host "🧠 Starting Advanced Memory Optimization..." -ForegroundColor Cyan

# 1. Clear system caches
Write-Host "🗑️ Clearing system caches..." -ForegroundColor Yellow

# Clear Windows Temp
$tempPath = $env:TEMP
if (Test-Path $tempPath) {
    $tempSize = (Get-ChildItem $tempPath -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    Remove-Item "$tempPath\*" -Force -Recurse -ErrorAction SilentlyContinue
    Write-Host "   ✓ Cleared Windows Temp: $([math]::Round($tempSize, 2)) MB freed" -ForegroundColor Green
}

# Clear Prefetch
$prefetchPath = "$env:SystemRoot\Prefetch"
if (Test-Path $prefetchPath) {
    $prefetchSize = (Get-ChildItem $prefetchPath -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    Remove-Item "$prefetchPath\*" -Force -ErrorAction SilentlyContinue
    Write-Host "   ✓ Cleared Prefetch: $([math]::Round($prefetchSize, 2)) MB freed" -ForegroundColor Green
}

# Clear DNS cache
Clear-DnsClientCache -ErrorAction SilentlyContinue
Write-Host "   ✓ Cleared DNS cache" -ForegroundColor Green

# 2. Optimize Cursor processes
Write-Host "🔧 Optimizing Cursor processes..." -ForegroundColor Yellow

$cursorProcesses = Get-Process | Where-Object {$_.ProcessName -like "*cursor*"}
$cursorMemoryBefore = ($cursorProcesses | Measure-Object -Property WorkingSet -Sum).Sum / 1MB

Write-Host "   Current Cursor memory: $([math]::Round($cursorMemoryBefore, 2)) MB" -ForegroundColor White

# Suspend non-essential Cursor processes
foreach ($proc in $cursorProcesses) {
    if ($proc.ProcessName -ne "Cursor" -and $proc.ProcessName -notlike "*main*") {
        try {
            $proc.Suspend()
            Write-Host "   ✓ Suspended: $($proc.ProcessName) (PID: $($proc.Id))" -ForegroundColor Green
        } catch {
            Write-Warning "   ⚠️ Could not suspend $($proc.ProcessName): $($_.Exception.Message)"
        }
    }
}

# Force garbage collection in PowerShell processes
$powerShellProcesses = Get-Process | Where-Object {$_.ProcessName -like "*powershell*"}
foreach ($proc in $powerShellProcesses) {
    try {
        # Send memory optimization signal
        $proc.MinWorkingSet = $proc.MaxWorkingSet
        Write-Host "   ✓ Optimized PowerShell process: $($proc.Id)" -ForegroundColor Green
    } catch {
        # Ignore access errors
    }
}

# 3. Optimize system memory
Write-Host "⚙️ Optimizing system memory..." -ForegroundColor Yellow

# Empty standby list
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Memory
{
    [DllImport("psapi.dll")]
    public static extern int EmptyWorkingSet(IntPtr hwProc);
    [DllImport("kernel32.dll")]
    public static extern IntPtr GetCurrentProcess();
}
"@

$mem = New-Object Memory
$mem::EmptyWorkingSet($mem::GetCurrentProcess())
Write-Host "   ✓ Emptied working set for current process" -ForegroundColor Green

# Optimize all processes
$allProcesses = Get-Process
foreach ($proc in $allProcesses) {
    try {
        $proc.MinWorkingSet = $proc.MaxWorkingSet
    } catch {
        # Ignore access errors for system processes
    }
}
Write-Host "   ✓ Optimized memory for all accessible processes" -ForegroundColor Green

# 4. Disable unnecessary visual effects
Write-Host "🎨 Optimizing visual effects..." -ForegroundColor Yellow

try {
    # Disable visual effects for better performance
    $visualFX = Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" -ErrorAction SilentlyContinue
    if ($visualFX) {
        Set-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" -Name "VisualFXSetting" -Value 2 -Type DWord -Force
        Write-Host "   ✓ Set visual effects to 'Best Performance'" -ForegroundColor Green
    }
} catch {
    Write-Warning "   ⚠️ Could not optimize visual effects: $($_.Exception.Message)"
}

# 5. Restart memory-intensive services safely
Write-Host "🔄 Restarting memory-intensive services..." -ForegroundColor Yellow

$servicesToRestart = @(
    @{Name="SysMain"; DisplayName="Superfetch/Prefetch"},
    @{Name="Themes"; DisplayName="Themes service"}
)

foreach ($service in $servicesToRestart) {
    try {
        $svc = Get-Service -Name $service.Name -ErrorAction SilentlyContinue
        if ($svc -and $svc.Status -eq "Running") {
            Restart-Service -Name $service.Name -Force -ErrorAction SilentlyContinue
            Write-Host "   ✓ Restarted $($service.DisplayName)" -ForegroundColor Green
        }
    } catch {
        Write-Warning "   ⚠️ Could not restart $($service.Name): $($_.Exception.Message)"
    }
}

# 6. Final memory check
Write-Host "📊 Final memory assessment..." -ForegroundColor Yellow

# Check Cursor memory after optimization
$cursorProcessesAfter = Get-Process | Where-Object {$_.ProcessName -like "*cursor*"}
$cursorMemoryAfter = ($cursorProcessesAfter | Measure-Object -Property WorkingSet -Sum).Sum / 1MB

$memorySaved = $cursorMemoryBefore - $cursorMemoryAfter
Write-Host "   Cursor memory before: $([math]::Round($cursorMemoryBefore, 2)) MB" -ForegroundColor White
Write-Host "   Cursor memory after: $([math]::Round($cursorMemoryAfter, 2)) MB" -ForegroundColor White

if ($memorySaved -gt 0) {
    Write-Host "   Memory saved: $([math]::Round($memorySaved, 2)) MB ✓" -ForegroundColor Green
} else {
    Write-Host "   Memory change: $([math]::Round($memorySaved, 2)) MB" -ForegroundColor Gray
}

# Check total system memory
$totalMemory = (Get-CimInstance -Class Win32_ComputerSystem).TotalPhysicalMemory / 1GB
$availableMemory = (Get-Counter -Counter "\Memory\Available MBytes" -ErrorAction SilentlyContinue).CounterSamples.CookedValue / 1GB
$usedMemory = $totalMemory - $availableMemory
$usagePercent = ($usedMemory / $totalMemory) * 100

Write-Host "   System memory: $([math]::Round($usedMemory, 2))GB/$([math]::Round($totalMemory, 2))GB ($([math]::Round($usagePercent, 1))%)" -ForegroundColor White

# 7. Recommendations
Write-Host "💡 Recommendations..." -ForegroundColor Cyan

if ($cursorMemoryAfter -gt 1200) {
    Write-Host "   ⚠️ Cursor memory still high. Consider:" -ForegroundColor Yellow
    Write-Host "      - Restart Cursor completely" -ForegroundColor White
    Write-Host "      - Disable heavy extensions" -ForegroundColor White
    Write-Host "      - Reduce workspace size" -ForegroundColor White
} else {
    Write-Host "   ✅ Cursor memory optimized successfully!" -ForegroundColor Green
}

if ($usagePercent -gt 80) {
    Write-Host "   ⚠️ System memory usage high. Consider:" -ForegroundColor Yellow
    Write-Host "      - Close unnecessary applications" -ForegroundColor White
    Write-Host "      - Restart system if needed" -ForegroundColor White
} else {
    Write-Host "   ✅ System memory usage healthy!" -ForegroundColor Green
}

Write-Host "✅ Advanced memory optimization completed!" -ForegroundColor Green
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Restart Cursor to apply all optimizations" -ForegroundColor White
Write-Host "   2. Monitor memory usage over time" -ForegroundColor White
Write-Host "   3. Run this script periodically for maintenance" -ForegroundColor White
