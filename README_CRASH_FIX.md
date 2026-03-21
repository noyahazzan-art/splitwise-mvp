# PowerShell Editor Services Crash Fix Guide

## 🚨 Problem Summary

**Critical Issues Identified:**
1. **PowerShell Editor Services Crashes** - `InvalidOperationException: Stack empty`
2. **System Service Timeouts** - FDResPub, HPAppHelperCap, PC Manager services
3. **Resource Impact** - ~1.2GB RAM usage by Cursor, system stability concerns

## 🛠️ Solution Overview

### **Phase 1: Immediate Fix (Run Now)**
```powershell
# Run as Administrator
.\scripts\fix_powershell_editor_services.ps1
.\scripts\fix_system_services.ps1
```

### **Phase 2: Prevention (Background Monitor)**
```powershell
# Start continuous monitoring
.\scripts\monitor_and_prevent_crashes.ps1
```

---

## 📋 Detailed Fix Procedures

### **1. PowerShell Editor Services Fix**

**What it does:**
- Terminates crashed PowerShell Editor Services processes
- Clears corrupted cache and session files
- Creates robust PowerShell profile with error handling
- Resets PowerShell extension configuration

**Key Changes:**
- Safe stack operations to prevent "Stack empty" exceptions
- Error handling wrapper for common operations
- Automatic cache cleanup on startup

**Expected Results:**
- No more PowerShell Editor Services crashes
- Stable PowerShell extension in Cursor/VSCode
- Improved IDE responsiveness

### **2. System Services Fix**

**What it does:**
- **FDResPub**: Resets to Automatic startup, restarts service
- **HPAppHelperCap**: Sets to Manual startup (prevents timeouts)
- **PCManager**: Disables service (prevents crashes)
- Increases service timeout from 30s to 60s
- Restarts critical system services

**Expected Results:**
- No more service timeout errors
- Reduced system event log noise
- Better system stability

### **3. Continuous Monitoring**

**Features:**
- Real-time crash detection
- Automatic recovery actions
- Memory usage monitoring
- Service health checks
- Detailed logging to `Desktop\PowerShell_Crash_Monitor.log`

**Monitoring Intervals:**
- Every 5 minutes for system health
- Immediate response to crashes
- Automatic cleanup and recovery

---

## 🎯 Step-by-Step Instructions

### **Step 1: Immediate Fixes**

1. **Open PowerShell as Administrator**
   ```powershell
   # Right-click PowerShell -> Run as Administrator
   cd "C:\Users\nchma\CascadeProjects\splitwise"
   ```

2. **Run PowerShell Fix**
   ```powershell
   .\scripts\fix_powershell_editor_services.ps1
   ```
   - This will terminate problematic processes
   - Clear caches and reset configurations
   - Create robust PowerShell profile

3. **Run Services Fix**
   ```powershell
   .\scripts\fix_system_services.ps1
   ```
   - This will fix service timeout issues
   - Optimize service configurations
   - Restart critical services

4. **Restart Cursor/VSCode**
   - Close all IDE instances
   - Restart Cursor
   - Verify PowerShell extension loads without crashes

### **Step 2: Enable Monitoring**

1. **Start Background Monitor**
   ```powershell
   # In a new PowerShell window (can be regular user)
   .\scripts\monitor_and_prevent_crashes.ps1
   ```

2. **Monitor Log File**
   - Check `Desktop\PowerShell_Crash_Monitor.log`
   - Look for "✅ System healthy" messages
   - Monitor for any "🚨" error messages

### **Step 3: Verification**

1. **Check Event Logs**
   ```powershell
   # Should show no new PowerShell crashes
   Get-EventLog -LogName Application -Newest 5 -EntryType Error -Source ".NET Runtime"
   ```

2. **Check Service Status**
   ```powershell
   Get-Service FDResPub, HPAppHelperCap | Select-Object Name, Status, StartType
   ```

3. **Check Memory Usage**
   ```powershell
   Get-Process | Where-Object {$_.ProcessName -like "*cursor*"} | Measure-Object -Property WorkingSet -Sum
   ```

---

## 📊 Expected Results

### **Before Fix:**
- ❌ PowerShell Editor Services crashes (3x in 24h)
- ❌ Service timeout errors in Event Log
- ❌ 1.2GB+ RAM usage by Cursor
- ❌ System instability

### **After Fix:**
- ✅ No PowerShell crashes
- ✅ Services running optimally
- ✅ Stable memory usage (~1GB)
- ✅ Continuous monitoring and prevention

---

## 🔄 Maintenance

### **Weekly:**
- Check monitor log file
- Verify no new crashes
- Review memory usage trends

### **Monthly:**
- Clear PowerShell caches manually if needed
- Update PowerShell extension
- Review service configurations

### **If Issues Recur:**
1. Run the fix scripts again
2. Check for Windows updates
3. Consider reinstalling PowerShell extension
4. Review monitor logs for patterns

---

## 🚨 Emergency Procedures

### **If PowerShell Extension Fails Completely:**
```powershell
# Uninstall and reinstall PowerShell extension
code --uninstall-extension ms-vscode.powershell
code --install-extension ms-vscode.powershell
```

### **If System Becomes Unstable:**
```powershell
# Stop all monitoring
Get-Process | Where-Object {$_.ProcessName -like "*monitor*"} | Stop-Process -Force

# Reset all services
.\scripts\fix_system_services.ps1

# Restart system
Restart-Computer -Force
```

---

## 📞 Support

**Monitor Log Location:** `Desktop\PowerShell_Crash_Monitor.log`

**Key Log Entries to Watch:**
- `[ERROR] PowerShell Editor Services crashes detected`
- `[WARNING] Service issues detected`
- `[SUCCESS] Auto-recovery actions performed`

**Healthy System Indicators:**
- `✅ System healthy` messages
- Memory usage < 85%
- No crash entries in event logs

---

## 🎉 Success Criteria

1. **No PowerShell crashes for 48+ hours**
2. **All services running without timeouts**
3. **Stable memory usage (< 1.2GB for Cursor)**
4. **Monitor shows consistent "System healthy" status**
5. **IDE responsiveness improved**

**Estimated Fix Time:** 15-30 minutes for initial setup
**Monitoring:** Continuous (5-minute intervals)
