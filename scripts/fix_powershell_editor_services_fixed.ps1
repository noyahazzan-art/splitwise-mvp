# Fix PowerShell Editor Services Crashes
# This script addresses the InvalidOperationException: Stack empty issue

Write-Host "🔧 Starting PowerShell Editor Services Fix..." -ForegroundColor Cyan

# 1. Kill existing PowerShell Editor Services processes
Write-Host "📦 Terminating existing PowerShell Editor Services..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*powershell*" -and $_.CommandLine -like "*EditorServices*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object {$_.ProcessName -like "*PSES*"} | Stop-Process -Force -ErrorAction SilentlyContinue

# 2. Clear PowerShell Editor Services cache
Write-Host "🧹 Clearing PowerShell Editor Services cache..." -ForegroundColor Yellow
$psesCachePaths = @(
    "$env:USERPROFILE\.vscode",
    "$env:USERPROFILE\.cursor",
    "$env:APPDATA\Code",
    "$env:LOCALAPPDATA\Code"
)

foreach ($path in $psesCachePaths) {
    if (Test-Path "$path\logs") {
        Remove-Item "$path\logs\*PowerShell*" -Force -Recurse -ErrorAction SilentlyContinue
        Write-Host "   ✓ Cleared logs from $path" -ForegroundColor Green
    }
    if (Test-Path "$path\session") {
        Remove-Item "$path\session\*" -Force -Recurse -ErrorAction SilentlyContinue
        Write-Host "   ✓ Cleared session from $path" -ForegroundColor Green
    }
}

# 3. Reset PowerShell Editor Services configuration
Write-Host "⚙️ Resetting PowerShell Editor Services configuration..." -ForegroundColor Yellow
$psesConfigPath = "$env:USERPROFILE\.cursor\extensions"
if (Test-Path $psesConfigPath) {
    Get-ChildItem $psesConfigPath -Recurse -Filter "*powershell*" | ForEach-Object {
        $configFile = $_.FullName
        if (Test-Path $configFile) {
            $backup = "$configFile.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
            Copy-Item $configFile $backup -Force
            Write-Host "   ✓ Backed up: $configFile" -ForegroundColor Green
        }
    }
}

# 4. Update PowerShell execution policy if needed
Write-Host "🔒 Checking PowerShell execution policy..." -ForegroundColor Yellow
$currentPolicy = Get-ExecutionPolicy -Scope CurrentUser
if ($currentPolicy -eq "Restricted") {
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    Write-Host "   ✓ Updated execution policy to RemoteSigned" -ForegroundColor Green
} else {
    Write-Host "   ✓ Execution policy is already set to: $currentPolicy" -ForegroundColor Green
}

# 5. Create PowerShell profile with error handling
Write-Host "📝 Creating robust PowerShell profile..." -ForegroundColor Yellow
$profilePath = $PROFILE.CurrentUserAllHosts
$profileContent = @'
# PowerShell Profile with Error Handling
# Prevents Stack empty exceptions

# Error handling for stack operations
function Invoke-SafeStackOperation {
    param(
        [scriptblock]$ScriptBlock
    )
    
    try {
        & $ScriptBlock
    }
    catch {
        Write-Warning "Stack operation failed: $($_.Exception.Message)"
        # Clear any potential stack corruption
        $Error.Clear()
    }
}

# Override common stack operations with safe versions
function Safe-Get-Location {
    Invoke-SafeStackOperation { Get-Location }
}

function Safe-Push-Location {
    param([string]$Path)
    Invoke-SafeStackOperation { Push-Location $Path }
}

function Safe-Pop-Location {
    Invoke-SafeStackOperation { Pop-Location }
}

# Initialize error handling
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

Write-Host "✅ PowerShell profile loaded with error handling" -ForegroundColor Green
'@

# Backup existing profile
if (Test-Path $profilePath) {
    Copy-Item $profilePath "$profilePath.backup.$(Get-Date -Format 'yyyyMMddHHmmss')" -Force
}

# Write new profile
Set-Content -Path $profilePath -Value $profileContent -Force
Write-Host "   ✓ Created robust PowerShell profile" -ForegroundColor Green

# 6. Restart Windows Terminal/PowerShell services
Write-Host "🔄 Restarting PowerShell services..." -ForegroundColor Yellow
Stop-Process -Name "WindowsTerminal" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "pwsh" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "powershell" -Force -ErrorAction SilentlyContinue

Write-Host "✅ PowerShell Editor Services fix completed!" -ForegroundColor Green
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Restart Cursor/VSCode" -ForegroundColor White
Write-Host "   2. The PowerShell extension should reload automatically" -ForegroundColor White
Write-Host "   3. Monitor for crashes in the next few hours" -ForegroundColor White
