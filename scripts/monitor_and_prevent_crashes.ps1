# Monitor and Prevent PowerShell Editor Services Crashes
# Continuous monitoring and prevention script

Write-Host "🔍 Starting Crash Prevention Monitor..." -ForegroundColor Cyan

# Configuration
$monitorInterval = 300  # 5 minutes
$logFile = "$env:USERPROFILE\Desktop\PowerShell_Crash_Monitor.log"
$maxLogSize = 1MB  # Rotate log when it reaches 1MB

# Initialize log
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Add to log file
    Add-Content -Path $logFile -Value $logEntry -ErrorAction SilentlyContinue
    
    # Rotate log if too large
    if ((Get-Item $logFile -ErrorAction SilentlyContinue).Length -gt $maxLogSize) {
        $backupLog = "$logFile.$(Get-Date -Format 'yyyyMMddHHmmss')"
        Move-Item $logFile $backupLog -Force
        Write-Log "Log rotated to $backupLog" -Level "INFO"
    }
    
    # Display with color
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        default { Write-Host $logEntry -ForegroundColor White }
    }
}

# Check for PowerShell Editor Services crashes
function Check-PSEditorServicesCrashes {
    $crashCount = 0
    $recentCrashes = @()
    
    # Check Application event log for PowerShell crashes
    try {
        $psCrashes = Get-EventLog -LogName Application -Newest 10 -EntryType Error -Source ".NET Runtime" -ErrorAction SilentlyContinue |
                    Where-Object {$_.Message -like "*pwsh.exe*" -and $_.Message -like "*Stack empty*"}
        
        if ($psCrashes) {
            $crashCount = $psCrashes.Count
            $recentCrashes = $psCrashes | ForEach-Object {
                [PSCustomObject]@{
                    Time = $_.TimeGenerated
                    Message = "PowerShell Editor Services Crash: Stack empty"
                    Details = $_.Message.Substring(0, 100) + "..."
                }
            }
        }
    } catch {
        Write-Log "Could not check event logs: $($_.Exception.Message)" -Level "WARNING"
    }
    
    return $crashCount, $recentCrashes
}

# Check service health
function Check-ServiceHealth {
    $problematicServices = @()
    
    $servicesToCheck = @(
        @{Name="FDResPub"; DisplayName="Function Discovery Resource Publication"},
        @{Name="HPAppHelperCap"; DisplayName="HP Application Helper"},
        @{Name="PCManager"; DisplayName="Microsoft PC Manager"}
    )
    
    foreach ($service in $servicesToCheck) {
        try {
            $svc = Get-Service -Name $service.Name -ErrorAction SilentlyContinue
            if ($svc) {
                if ($svc.Status -eq "Stopped") {
                    $problematicServices += [PSCustomObject]@{
                        Name = $service.DisplayName
                        Status = $svc.Status
                        Issue = "Service stopped"
                    }
                }
                
                # Check for recent service failures in event log
                $serviceFailures = Get-EventLog -LogName System -Newest 5 -EntryType Error -Source "Service Control Manager" -ErrorAction SilentlyContinue |
                                 Where-Object {$_.Message -like "*$($service.Name)*"}
                
                if ($serviceFailures) {
                    $problematicServices += [PSCustomObject]@{
                        Name = $service.DisplayName
                        Status = "Failing"
                        Issue = "Recent failures detected"
                    }
                }
            }
        } catch {
            # Service not found or access denied
        }
    }
    
    return $problematicServices
}

# Check memory usage
function Check-MemoryUsage {
    $totalMemory = (Get-CimInstance -Class Win32_ComputerSystem).TotalPhysicalMemory / 1GB
    $availableMemory = (Get-Counter -Counter "\Memory\Available MBytes" -ErrorAction SilentlyContinue).CounterSamples.CookedValue / 1GB
    $usedMemory = $totalMemory - $availableMemory
    $memoryUsagePercent = ($usedMemory / $totalMemory) * 100
    
    return [PSCustomObject]@{
        TotalGB = [math]::Round($totalMemory, 2)
        AvailableGB = [math]::Round($availableMemory, 2)
        UsedGB = [math]::Round($usedMemory, 2)
        UsagePercent = [math]::Round($memoryUsagePercent, 1)
    }
}

# Check Cursor processes
function Check-CursorProcesses {
    $cursorProcesses = Get-Process | Where-Object {$_.ProcessName -like "*cursor*"} | Measure-Object -Property WorkingSet -Sum
    $cursorMemoryMB = [math]::Round($cursorProcesses.Sum / 1MB, 2)
    
    return [PSCustomObject]@{
        ProcessCount = (Get-Process | Where-Object {$_.ProcessName -like "*cursor*"}).Count
        MemoryMB = $cursorMemoryMB
        MemoryGB = [math]::Round($cursorMemoryMB / 1024, 2)
    }
}

# Automatic recovery actions
function Invoke-AutoRecovery {
    param([array]$Crashes, [array]$ServiceIssues)
    
    $recoveryActions = @()
    
    # Recover from PowerShell crashes
    if ($Crashes.Count -gt 0) {
        Write-Log "Detected PowerShell Editor Services crashes - initiating recovery" -Level "WARNING"
        
        # Kill problematic PowerShell processes
        Get-Process | Where-Object {$_.ProcessName -like "*powershell*" -and $_.CommandLine -like "*EditorServices*"} | Stop-Process -Force -ErrorAction SilentlyContinue
        $recoveryActions += "Terminated problematic PowerShell processes"
        
        # Clear caches
        $cachePaths = @("$env:USERPROFILE\.cursor\logs", "$env:USERPROFILE\.vscode\logs")
        foreach ($path in $cachePaths) {
            if (Test-Path $path) {
                Remove-Item "$path\*PowerShell*" -Force -Recurse -ErrorAction SilentlyContinue
                $recoveryActions += "Cleared PowerShell cache from $path"
            }
        }
    }
    
    # Recover from service issues
    foreach ($issue in $ServiceIssues) {
        if ($issue.Name -like "*FDResPub*") {
            try {
                Start-Service -Name "FDResPub" -ErrorAction SilentlyContinue
                $recoveryActions += "Restarted FDResPub service"
            } catch {
                $recoveryActions += "Failed to restart FDResPub: $($_.Exception.Message)"
            }
        }
    }
    
    return $recoveryActions
}

# Main monitoring loop
function Start-Monitoring {
    Write-Log "PowerShell Crash Prevention Monitor started" -Level "SUCCESS"
    Write-Log "Monitoring interval: $monitorInterval seconds" -Level "INFO"
    
    while ($true) {
        try {
            # Check for crashes
            $crashCount, $crashes = Check-PSEditorServicesCrashes
            
            # Check service health
            $serviceIssues = Check-ServiceHealth
            
            # Check memory
            $memory = Check-MemoryUsage
            Write-Log "Memory: $($memory.UsedGB)GB/$($memory.TotalGB)GB ($($memory.UsagePercent)%)" -Level "INFO"
            
            # Check Cursor
            $cursor = Check-CursorProcesses
            Write-Log "Cursor: $($cursor.ProcessCount) processes, $($cursor.MemoryGB)GB RAM" -Level "INFO"
            
            # Report issues
            if ($crashes.Count -gt 0) {
                Write-Log "🚨 PowerShell Editor Services crashes detected: $crashCount" -Level "ERROR"
                foreach ($crash in $crashes) {
                    Write-Log "   - $($crash.Time): $($crash.Message)" -Level "ERROR"
                }
            }
            
            if ($serviceIssues.Count -gt 0) {
                Write-Log "⚠️ Service issues detected: $($serviceIssues.Count)" -Level "WARNING"
                foreach ($issue in $serviceIssues) {
                    Write-Log "   - $($issue.Name): $($issue.Issue)" -Level "WARNING"
                }
            }
            
            # Auto-recovery if needed
            if ($crashes.Count -gt 0 -or $serviceIssues.Count -gt 0) {
                $recoveryActions = Invoke-AutoRecovery -Crashes $crashes -ServiceIssues $serviceIssues
                if ($recoveryActions.Count -gt 0) {
                    Write-Log "🔧 Auto-recovery actions performed:" -Level "SUCCESS"
                    foreach ($action in $recoveryActions) {
                        Write-Log "   ✓ $action" -Level "SUCCESS"
                    }
                }
            }
            
            # Health check summary
            if ($crashes.Count -eq 0 -and $serviceIssues.Count -eq 0 -and $memory.UsagePercent -lt 85) {
                Write-Log "✅ System healthy" -Level "SUCCESS"
            }
            
            Write-Log "Next check in $monitorInterval seconds..." -Level "INFO"
            Write-Host "---" -ForegroundColor Gray
            
            # Wait for next interval
            Start-Sleep -Seconds $monitorInterval
            
        } catch {
            Write-Log "Monitor error: $($_.Exception.Message)" -Level "ERROR"
            Start-Sleep -Seconds 60  # Wait 1 minute on error
        }
    }
}

# Start monitoring
try {
    Start-Monitoring
} catch {
    Write-Log "Fatal monitor error: $($_.Exception.Message)" -Level "ERROR"
    Write-Host "Monitor stopped. Check log file: $logFile" -ForegroundColor Red
}
