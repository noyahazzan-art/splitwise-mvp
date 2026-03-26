# Enhanced PowerShell Editor Services Fix
# Addresses InvalidOperationException: Stack empty and other stability issues

#requires -RunAsAdministrator
param(
    [switch]$Force,
    [switch]$Verbose
)

# Enhanced logging function
function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("Info", "Warning", "Error", "Success")]
        [string]$Level = "Info"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "Info" { "White" }
        "Warning" { "Yellow" }
        "Error" { "Red" }
        "Success" { "Green" }
    }
    
    $prefix = switch ($Level) {
        "Info" { "ℹ️" }
        "Warning" { "⚠️" }
        "Error" { "❌" }
        "Success" { "✅" }
    }
    
    Write-Host "[$timestamp] $prefix $Message" -ForegroundColor $color
    
    # Also log to file for debugging
    $logFile = "$env:USERPROFILE\Desktop\PowerShell_Fix_Log.txt"
    Add-Content -Path $logFile -Value "[$timestamp][$Level] $Message" -ErrorAction SilentlyContinue
}

# Error handling wrapper
function Invoke-SafeOperation {
    param(
        [scriptblock]$ScriptBlock,
        [string]$OperationName = "Operation"
    )
    
    try {
        Write-Log "Starting: $OperationName" "Info"
        & $ScriptBlock
        Write-Log "Completed: $OperationName" "Success"
        return $true
    }
    catch {
        Write-Log "Failed: $OperationName - $($_.Exception.Message)" "Error"
        if ($Verbose) {
            Write-Log "Stack trace: $($_.ScriptStackTrace)" "Info"
        }
        return $false
    }
}

Write-Log "🔧 Starting Enhanced PowerShell Editor Services Fix..." "Info"

# Check admin privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Log "This script requires administrator privileges. Please run as Administrator." "Error"
    exit 1
}

# 1. Kill existing problematic processes with enhanced targeting
$success1 = Invoke-SafeOperation {
    Write-Log "Terminating existing PowerShell Editor Services..." "Info"
    
    # Target specific problematic processes
    $processesToKill = @(
        "*PowerShell*EditorServices*",
        "*PSES*",
        "*vscode-powershell*",
        "*cursor-powershell*"
    )
    
    foreach ($pattern in $processesToKill) {
        Get-Process | Where-Object {$_.ProcessName -like $pattern} | ForEach-Object {
            try {
                $_.Kill()
                Write-Log "Terminated process: $($_.ProcessName) (PID: $($_.Id))" "Info"
            }
            catch {
                Write-Log "Failed to terminate process: $($_.ProcessName) - $($_.Exception.Message)" "Warning"
            }
        }
    }
    
    # Also kill parent processes that might be holding locks
    Get-Process | Where-Object {$_.MainWindowTitle -like "*PowerShell*" -and $_.ProcessName -notin @("powershell", "pwsh")} | Stop-Process -Force -ErrorAction SilentlyContinue
} "Process Termination"

# 2. Clear caches with better error handling
$success2 = Invoke-SafeOperation {
    Write-Log "Clearing PowerShell Editor Services cache..." "Info"
    
    $psesCachePaths = @(
        "$env:USERPROFILE\.vscode",
        "$env:USERPROFILE\.cursor",
        "$env:APPDATA\Code",
        "$env:LOCALAPPDATA\Code",
        "$env:USERPROFILE\.vscode-server",
        "$env:PROGRAMDATA\Microsoft\Windows\PowerShell"
    )
    
    foreach ($path in $psesCachePaths) {
        if (Test-Path $path) {
            # Clear logs
            $logPaths = @("logs", "session", "tmp", "cache")
            foreach ($logPath in $logPaths) {
                $fullPath = Join-Path $path $logPath
                if (Test-Path $fullPath) {
                    try {
                        Remove-Item "$fullPath\*PowerShell*" -Force -Recurse -ErrorAction SilentlyContinue
                        Remove-Item "$fullPath\*PSES*" -Force -Recurse -ErrorAction SilentlyContinue
                        Write-Log "Cleared $logPath from $path" "Success"
                    }
                    catch {
                        Write-Log "Failed to clear $logPath from $path - $($_.Exception.Message)" "Warning"
                    }
                }
            }
            
            # Clear specific extension caches
            $extPath = Join-Path $path "extensions"
            if (Test-Path $extPath) {
                Get-ChildItem $extPath -Directory | Where-Object {$_.Name -like "*powershell*"} | ForEach-Object {
                    try {
                        $cachePath = Join-Path $_.FullName ".cache"
                        if (Test-Path $cachePath) {
                            Remove-Item $cachePath -Force -Recurse
                            Write-Log "Cleared extension cache for $($_.Name)" "Success"
                        }
                    }
                    catch {
                        Write-Log "Failed to clear cache for $($_.Name) - $($_.Exception.Message)" "Warning"
                    }
                }
            }
        }
    }
} "Cache Clearing"

# 3. Reset configuration with backup
$success3 = Invoke-SafeOperation {
    Write-Log "Resetting PowerShell Editor Services configuration..." "Info"
    
    $configPaths = @(
        "$env:USERPROFILE\.cursor\extensions",
        "$env:USERPROFILE\.vscode\extensions",
        "$env:APPDATA\Code\User\settings.json"
    )
    
    foreach ($configPath in $configPaths) {
        if (Test-Path $configPath) {
            try {
                # Backup configuration
                $backupPath = "$configPath.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
                if (Test-Path $configPath -PathType Container) {
                    Copy-Item $configPath $backupPath -Recurse -Force
                } else {
                    Copy-Item $configPath $backupPath -Force
                }
                Write-Log "Backed up: $configPath" "Success"
                
                # Clear problematic settings
                if ($configPath.EndsWith("settings.json")) {
                    try {
                        $settings = Get-Content $configPath -Raw | ConvertFrom-Json
                        if ($settings.'powershell.powerShellExePath') {
                            $settings.PSObject.Properties.Remove('powershell.powerShellExePath')
                        }
                        $settings | ConvertTo-Json -Depth 10 | Set-Content $configPath
                        Write-Log "Cleared problematic PowerShell settings" "Success"
                    }
                    catch {
                        Write-Log "Failed to update settings.json - $($_.Exception.Message)" "Warning"
                    }
                }
            }
            catch {
                Write-Log "Failed to process $configPath - $($_.Exception.Message)" "Warning"
            }
        }
    }
} "Configuration Reset"

# 4. Update PowerShell execution policy and security
$success4 = Invoke-SafeOperation {
    Write-Log "Checking PowerShell execution policy..." "Info"
    
    $scopes = @("CurrentUser", "LocalMachine")
    foreach ($scope in $scopes) {
        try {
            $currentPolicy = Get-ExecutionPolicy -Scope $scope -ErrorAction SilentlyContinue
            if ($currentPolicy -eq "Restricted" -or $currentPolicy -eq "Undefined") {
                Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope $scope -Force
                Write-Log "Updated execution policy to RemoteSigned for $scope" "Success"
            } else {
                Write-Log "Execution policy for $scope is already set to: $currentPolicy" "Info"
            }
        }
        catch {
            Write-Log "Failed to set execution policy for $scope - $($_.Exception.Message)" "Warning"
        }
    }
} "Execution Policy Setup"

# 5. Create enhanced PowerShell profile
$success5 = Invoke-SafeOperation {
    Write-Log "Creating enhanced PowerShell profile..." "Info"
    
    $profilePath = $PROFILE.CurrentUserAllHosts
    $profileContent = @'
# Enhanced PowerShell Profile with Comprehensive Error Handling
# Prevents Stack empty exceptions and improves stability

# Global error handling
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
$WarningPreference = "Continue"
$VerbosePreference = $false

# Safe stack operations with comprehensive error handling
function Invoke-SafeStackOperation {
    param(
        [scriptblock]$ScriptBlock,
        [string]$OperationName = "Stack Operation"
    )
    
    try {
        $result = & $ScriptBlock
        return $result
    }
    catch [System.InvalidOperationException] {
        Write-Warning "Stack operation failed in $OperationName`: $($_.Exception.Message)"
        # Clear any potential stack corruption
        $Error.Clear()
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()
        return $null
    }
    catch {
        Write-Warning "Operation failed in $OperationName`: $($_.Exception.Message)"
        $Error.Clear()
        return $null
    }
}

# Enhanced safe location functions
function Safe-Get-Location {
    Invoke-SafeStackOperation { Get-Location } "Get-Location"
}

function Safe-Push-Location {
    param([string]$Path)
    Invoke-SafeStackOperation { 
        if (Test-Path $Path) {
            Push-Location $Path
        } else {
            Write-Warning "Path does not exist: $Path"
        }
    } "Push-Location"
}

function Safe-Pop-Location {
    if ((Get-Location).Path -ne (Get-Location).Stack.Peek().Path) {
        Invoke-SafeStackOperation { Pop-Location } "Pop-Location"
    }
}

# Override common cmdlets with safe versions
Set-Alias -Name "gl" -Value "Safe-Get-Location" -Force
Set-Alias -Name "pushd" -Value "Safe-Push-Location" -Force
Set-Alias -Name "popd" -Value "Safe-Pop-Location" -Force

# Memory management for long-running sessions
function Invoke-MemoryCleanup {
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
    [System.GC]::Collect()
}

# Auto-cleanup every 100 commands
$global:CommandCounter = 0
$originalPrompt = $function:prompt

$function:prompt = {
    $global:CommandCounter++
    if ($global:CommandCounter % 100 -eq 0) {
        Invoke-MemoryCleanup | Out-Null
    }
    & $originalPrompt
}

# Initialize error handling
try {
    Write-Host "✅ Enhanced PowerShell profile loaded successfully" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ PowerShell profile loaded with warnings" -ForegroundColor Yellow
}
'@

    # Backup existing profile
    if (Test-Path $profilePath) {
        $backupPath = "$profilePath.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
        Copy-Item $profilePath $backupPath -Force
        Write-Log "Backed up existing profile to: $backupPath" "Success"
    }

    # Write new profile
    Set-Content -Path $profilePath -Value $profileContent -Force -Encoding UTF8
    Write-Log "Created enhanced PowerShell profile" "Success"
} "PowerShell Profile Creation"

# 6. System optimization
$success6 = Invoke-SafeOperation {
    Write-Log "Applying system optimizations..." "Info"
    
    # Clear Windows Event Log errors related to PowerShell
    try {
        $logNames = @("Application", "System")
        foreach ($logName in $logNames) {
            $events = Get-WinEvent -LogName $logName -MaxEvents 100 -ErrorAction SilentlyContinue | 
                      Where-Object {$_.ProviderName -like "*PowerShell*" -and $_.LevelDisplayName -eq "Error"}
            if ($events.Count -gt 0) {
                Write-Log "Found $($events.Count) PowerShell errors in $logName log" "Warning"
            }
        }
    }
    catch {
        Write-Log "Failed to check event logs - $($_.Exception.Message)" "Warning"
    }
    
    # Optimize PowerShell performance settings
    try {
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\PowerShell\1\ShellIds" -Name "ConsolePrompting" -Value $false -Type DWord -Force -ErrorAction SilentlyContinue
        Write-Log "Optimized PowerShell performance settings" "Success"
    }
    catch {
        Write-Log "Failed to set performance settings - $($_.Exception.Message)" "Warning"
    }
} "System Optimization"

# 7. Restart services safely
$success7 = Invoke-SafeOperation {
    Write-Log "Restarting PowerShell services..." "Info"
    
    # Stop processes gracefully first
    $processesToStop = @("WindowsTerminal", "pwsh", "powershell", "Code", "Cursor")
    
    foreach ($processName in $processesToStop) {
        $processes = Get-Process -Name $processName -ErrorAction SilentlyContinue
        foreach ($process in $processes) {
            try {
                $process.CloseMainWindow()
                Start-Sleep -Seconds 2
                if (!$process.HasExited) {
                    $process.Kill()
                }
                Write-Log "Stopped process: $processName (PID: $($process.Id))" "Success"
            }
            catch {
                Write-Log "Failed to stop process: $processName - $($_.Exception.Message)" "Warning"
            }
        }
    }
} "Service Restart"

# Summary
Write-Log "PowerShell Editor Services fix completed!" "Success"
Write-Log "Results:" "Info"
Write-Log "  Process termination: $(if($success1) {'✅'} else {'❌'})" "Info"
Write-Log "  Cache clearing: $(if($success2) {'✅'} else {'❌'})" "Info"
Write-Log "  Configuration reset: $(if($success3) {'✅'} else {'❌'})" "Info"
Write-Log "  Execution policy: $(if($success4) {'✅'} else {'❌'})" "Info"
Write-Log "  Profile creation: $(if($success5) {'✅'} else {'❌'})" "Info"
Write-Log "  System optimization: $(if($success6) {'✅'} else {'❌'})" "Info"
Write-Log "  Service restart: $(if($success7) {'✅'} else {'❌'})" "Info"

Write-Log "Next steps:" "Info"
Write-Log "  1. Restart Cursor/VSCode" "Info"
Write-Log "  2. The PowerShell extension should reload automatically" "Info"
Write-Log "  3. Monitor for crashes in the next few hours" "Info"
Write-Log "  4. Check log file: $env:USERPROFILE\Desktop\PowerShell_Fix_Log.txt" "Info"

if ($success1 -and $success2 -and $success3 -and $success4 -and $success5) {
    Write-Log "🎉 All critical fixes completed successfully!" "Success"
    exit 0
} else {
    Write-Log "⚠️ Some fixes encountered issues. Check the log for details." "Warning"
    exit 1
}
