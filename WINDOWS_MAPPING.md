# Splitwise MVP - Windows Mapping

## System Paths

### Project Root
```
C:\Users\nchma\CascadeProjects\splitwise\
```

### Key Directories
| Path | Purpose | Windows Access |
|------|---------|----------------|
| `C:\Users\nchma\CascadeProjects\splitwise\app\` | Application code | Explorer / VS Code |
| `C:\Users\nchma\CascadeProjects\splitwise\data\` | SQLite database | Explorer / DB tools |
| `C:\Users\nchma\CascadeProjects\splitwise\.venv\` | Python virtual environment | Command line |
| `C:\Users\nchma\CascadeProjects\splitwise\scripts\` | Utility scripts | PowerShell |
| `C:\Users\nchma\CascadeProjects\splitwise\tests\` | Test files | pytest / VS Code |

### Database Location
```
C:\Users\nchma\CascadeProjects\splitwise\data\splitwise.db
```

## Windows Commands

### PowerShell Setup
```powershell
# Navigate to project
cd C:\Users\nchma\CascadeProjects\splitwise

# Create virtual environment
python -m venv .venv

# Activate environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start application
.\run.ps1
```

### Administrative Commands
```powershell
# Check if port 8001 is in use
netstat -ano | findstr ":8001"

# Kill process on port 8001 (if needed)
taskkill /PID <PID> /F

# Check Python processes
tasklist | findstr python

# Clear Python cache
Remove-Item -Recurse -Force .\.pytest_cache\
Remove-Item -Recurse -Force .\app\__pycache__\
```

## File Associations

### Python Files
- `.py` - Python source files (VS Code / Python extension)
- `.pyi` - Python stub files
- `.ipynb` - Jupyter notebooks (if used)

### Configuration Files
- `.gitignore` - Git ignore rules
- `requirements.txt` - Python dependencies
- `run.ps1` - PowerShell startup script

### Data Files
- `.db` - SQLite database file
- `.sqlite` - Alternative SQLite extension

## Windows Services Integration

### Environment Variables
```powershell
# Optional: Set environment variables
$env:SPLITWISE_DB_PATH = "C:\Users\nchma\CascadeProjects\splitwise\data\splitwise.db"
$env:SPLITWISE_LOG_LEVEL = "INFO"
```

### Windows Task Scheduler (Optional)
```xml
<!-- Task to start app on Windows startup -->
<!-- Location: Task Scheduler > Create Basic Task -->
Trigger: At system startup
Action: Start a program
Program: powershell.exe
Arguments: -ExecutionPolicy Bypass -File "C:\Users\nchma\CascadeProjects\splitwise\run.ps1"
```

## Network Configuration

### Local URLs
| Service | URL | Port |
|---------|-----|------|
| API Server | http://localhost:8001 | 8001 |
| API Docs | http://localhost:8001/docs | 8001 |
| Dashboard | http://localhost:8001/dashboard | 8001 |

### Firewall Rules (if needed)
```powershell
# Allow inbound traffic on port 8001
New-NetFirewallRule -DisplayName "Splitwise API" -Direction Inbound -Port 8001 -Protocol TCP -Action Allow
```

## Windows File Explorer Integration

### Quick Access
1. Right-click `C:\Users\nchma\CascadeProjects\splitwise\`
2. Select "Pin to Quick Access"

### Send To Menu (Optional)
```powershell
# Add to Send To menu
$sendToPath = "$env:APPDATA\Microsoft\Windows\SendTo"
New-Item -ItemType SymbolicLink -Path "$sendToPath\Splitwise.lnk" -Target "C:\Users\nchma\CascadeProjects\splitwise"
```

## Development Tools Integration

### VS Code Workspace
```json
{
  "folders": [
    {
      "path": "C:\\Users\\nchma\\CascadeProjects\\splitwise"
    }
  ],
  "settings": {
    "python.defaultInterpreterPath": "C:\\Users\\nchma\\CascadeProjects\\splitwise\\.venv\\Scripts\\python.exe",
    "python.linting.enabled": true,
    "python.formatting.provider": "black"
  }
}
```

### Git Configuration
```powershell
# Set up Git in project directory
cd C:\Users\nchma\CascadeProjects\splitwise
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

## Windows-Specific Considerations

### Path Handling
- Use backslashes `\` for Windows paths
- Long paths may require `\\?\` prefix
- Max path length: 260 characters (default)

### Permissions
- Ensure read/write access to `data\` directory
- Virtual environment may need execution permissions
- PowerShell execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Antivirus Exclusions (if needed)
```
C:\Users\nchma\CascadeProjects\splitwise\.venv\
C:\Users\nchma\CascadeProjects\splitwise\data\*.db
```

## Troubleshooting Windows Issues

### Common Problems
1. **PowerShell execution policy**: Run as Administrator
2. **Port conflicts**: Use `netstat -ano | findstr ":8001"`
3. **Virtual environment issues**: Delete `.venv` and recreate
4. **SQLite locking**: Close all database connections
5. **Path length issues**: Move project closer to root directory

### Windows Event Viewer
```
Event Viewer > Windows Logs > Application
Filter for "python" or "uvicorn" events
```

## Backup Strategy

### Windows Backup Locations
- Project files: `C:\Users\nchma\CascadeProjects\splitwise\`
- Database: `C:\Users\nchma\CascadeProjects\splitwise\data\splitwise.db`
- Config: `C:\Users\nchma\CascadeProjects\splitwise\requirements.txt`

### PowerShell Backup Script
```powershell
# backup.ps1
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = "C:\Users\nchma\Backups\splitwise-$timestamp"
New-Item -ItemType Directory -Path $backupDir
Copy-Item -Recurse "C:\Users\nchma\CascadeProjects\splitwise\*" $backupDir
```

## Performance Optimization

### Windows SSD Optimization
- Move database to SSD if available
- Enable Windows Defender exclusions for project directory
- Use Windows Performance Monitor to track application metrics

### Memory Management
```powershell
# Monitor Python process memory
Get-Process python | Select-Object ProcessName, Id, WorkingSet, CPU
```
