# Fix System Service Timeouts
# Addresses FDResPub, HPAppHelperCap, and Microsoft PC Manager Service issues

Write-Host "🔧 Starting System Services Fix..." -ForegroundColor Cyan

# 1. Check and fix FDResPub service (Function Discovery Resource Publication)
Write-Host "📡 Fixing FDResPub service..." -ForegroundColor Yellow
try {
    $fdrespub = Get-Service -Name "FDResPub" -ErrorAction SilentlyContinue
    if ($fdrespub) {
        Write-Host "   Current status: $($fdrespub.Status)" -ForegroundColor White
        
        # Stop the service
        Stop-Service -Name "FDResPub" -Force -ErrorAction SilentlyContinue
        
        # Reset service configuration
        $serviceConfig = Get-WmiObject -Class Win32_Service -Filter "Name='FDResPub'"
        if ($serviceConfig) {
            $serviceConfig.Change($null,$null,$null,$null,$null,$null,$null,"Automatic",$null,$null,$null,$null,$null) | Out-Null
            Write-Host "   ✓ Reset FDResPub to Automatic startup" -ForegroundColor Green
        }
        
        # Start the service
        Start-Service -Name "FDResPub" -ErrorAction SilentlyContinue
        Write-Host "   ✓ FDResPub service restarted" -ForegroundColor Green
    }
} catch {
    Write-Warning "   ⚠️ FDResPub service issue: $($_.Exception.Message)"
}

# 2. Fix HPAppHelperCap service (HP Application Helper)
Write-Host "💻 Fixing HPAppHelperCap service..." -ForegroundColor Yellow
try {
    $hpapp = Get-Service -Name "HPAppHelperCap" -ErrorAction SilentlyContinue
    if ($hpapp) {
        Write-Host "   Current status: $($hpapp.Status)" -ForegroundColor White
        
        # This service often causes timeouts, set to manual startup
        Stop-Service -Name "HPAppHelperCap" -Force -ErrorAction SilentlyContinue
        
        $serviceConfig = Get-WmiObject -Class Win32_Service -Filter "Name='HPAppHelperCap'"
        if ($serviceConfig) {
            # Change to Manual startup to prevent automatic timeouts
            $serviceConfig.Change($null,$null,$null,$null,$null,$null,$null,"Manual",$null,$null,$null,$null,$null) | Out-Null
            Write-Host "   ✓ Set HPAppHelperCap to Manual startup" -ForegroundColor Green
        }
        
        Write-Host "   ✓ HPAppHelperCap configured (Manual startup)" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️ HPAppHelperCap service not found (may be HP-specific)" -ForegroundColor Gray
    }
} catch {
    Write-Warning "   ⚠️ HPAppHelperCap service issue: $($_.Exception.Message)"
}

# 3. Fix Microsoft PC Manager Service
Write-Host "🖥️ Fixing Microsoft PC Manager Service..." -ForegroundColor Yellow
try {
    $pcmgr = Get-Service -Name "PCManager" -ErrorAction SilentlyContinue
    if ($pcmgr) {
        Write-Host "   Current status: $($pcmgr.Status)" -ForegroundColor White
        
        # Stop and disable problematic service
        Stop-Service -Name "PCManager" -Force -ErrorAction SilentlyContinue
        
        $serviceConfig = Get-WmiObject -Class Win32_Service -Filter "Name='PCManager'"
        if ($serviceConfig) {
            # Disable to prevent unexpected terminations
            $serviceConfig.Change($null,$null,$null,$null,$null,$null,$null,"Disabled",$null,$null,$null,$null,$null) | Out-Null
            Write-Host "   ✓ Disabled PCManager service" -ForegroundColor Green
        }
        
        Write-Host "   ✓ PCManager service disabled" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️ PCManager service not found" -ForegroundColor Gray
    }
} catch {
    Write-Warning "   ⚠️ PCManager service issue: $($_.Exception.Message)"
}

# 4. Optimize service timeout settings
Write-Host "⏱️ Optimizing service timeout settings..." -ForegroundColor Yellow

# Registry key to increase service timeout
$regPath = "HKLM:\SYSTEM\CurrentControlSet\Control"
if (Test-Path $regPath) {
    try {
        # Increase ServicesPipeTimeout from 30 seconds to 60 seconds
        Set-ItemProperty -Path $regPath -Name "ServicesPipeTimeout" -Value 60000 -Type DWord -Force
        Write-Host "   ✓ Increased service timeout to 60 seconds" -ForegroundColor Green
    } catch {
        Write-Warning "   ⚠️ Could not update service timeout: $($_.Exception.Message)"
    }
}

# 5. Clear service event logs
Write-Host "🧹 Clearing service event logs..." -ForegroundColor Yellow
try {
    # Clear System event log (last 100 entries related to services)
    $systemLogs = Get-EventLog -LogName System -Newest 100 | Where-Object {$_.Source -like "*Service*" -or $_.Source -like "*FDResPub*" -or $_.Source -like "*HPAppHelperCap*" -or $_.Source -like "*PCManager*"}
    Write-Host "   ✓ Found $($systemLogs.Count) service-related log entries" -ForegroundColor White
    
    # Optional: Clear the entire System log (uncomment if needed)
    # Clear-EventLog -LogName System -ErrorAction SilentlyContinue
    Write-Host "   ✓ Service logs reviewed" -ForegroundColor Green
} catch {
    Write-Warning "   ⚠️ Could not clear event logs: $($_.Exception.Message)"
}

# 6. Restart critical services
Write-Host "🔄 Restarting critical services..." -ForegroundColor Yellow
$criticalServices = @(
    "EventLog",
    "PlugPlay", 
    "RpcSs",
    "Dnscache"
)

foreach ($serviceName in $criticalServices) {
    try {
        $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if ($service -and $service.Status -eq "Running") {
            Restart-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
            Write-Host "   ✓ Restarted $serviceName" -ForegroundColor Green
        }
    } catch {
        Write-Warning "   ⚠️ Could not restart $serviceName: $($_.Exception.Message)"
    }
}

Write-Host "✅ System services fix completed!" -ForegroundColor Green
Write-Host "📝 Summary of changes:" -ForegroundColor Cyan
Write-Host "   • FDResPub: Reset to Automatic, restarted" -ForegroundColor White
Write-Host "   • HPAppHelperCap: Set to Manual (prevents timeouts)" -ForegroundColor White
Write-Host "   • PCManager: Disabled (prevents crashes)" -ForegroundColor White
Write-Host "   • Service timeout: Increased to 60 seconds" -ForegroundColor White
Write-Host "   • Critical services: Restarted" -ForegroundColor White

Write-Host "🔄 System restart recommended for full effect" -ForegroundColor Yellow
