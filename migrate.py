#!/usr/bin/env python3
"""
Database migration management for Splitwise MVP.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle result."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                print(f"Output: {result.stdout}")
        else:
            print(f"❌ {description} failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return False


def main():
    """Main migration management interface."""
    print("🗄️ Splitwise MVP Database Migration Manager")
    print("=" * 50)
    
    # Check if alembic is available
    try:
        import alembic
        print("✅ Alembic is available")
    except ImportError:
        print("❌ Alembic not found. Installing...")
        run_command("pip install alembic", "Installing Alembic")
    
    print("\n📋 Available commands:")
    print("1. Initialize migrations (alembic init)")
    print("2. Create new migration (alembic revision)")
    print("3. Run migrations (alembic upgrade head)")
    print("4. Check current version (alembic current)")
    print("5. Show migration history (alembic history)")
    print("6. Rollback migration (alembic downgrade)")
    print("7. Auto-generate migration (alembic revision --autogenerate)")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            run_command("alembic init migrations", "Initializing migrations")
            
        elif command == "revision":
            message = sys.argv[2] if len(sys.argv) > 2 else "Auto migration"
            run_command(f'alembic revision --autogenerate -m "{message}"', "Creating migration")
            
        elif command == "upgrade":
            version = sys.argv[2] if len(sys.argv) > 2 else "head"
            run_command(f"alembic upgrade {version}", "Running migrations")
            
        elif command == "current":
            run_command("alembic current", "Checking current version")
            
        elif command == "history":
            run_command("alembic history", "Showing migration history")
            
        elif command == "downgrade":
            version = sys.argv[2] if len(sys.argv) > 2 else "-1"
            run_command(f"alembic downgrade {version}", "Rolling back migration")
            
        elif command == "autogenerate":
            message = sys.argv[2] if len(sys.argv) > 2 else "Auto migration"
            run_command(f'alembic revision --autogenerate -m "{message}"', "Auto-generating migration")
            
        else:
            print(f"❌ Unknown command: {command}")
            sys.exit(1)
    else:
        print("\n💡 Usage examples:")
        print("  python migrate.py init")
        print("  python migrate.py revision \"Add user table\"")
        print("  python migrate.py upgrade")
        print("  python migrate.py upgrade head")
        print("  python migrate.py current")
        print("  python migrate.py history")
        print("  python migrate.py downgrade")
        print("  python migrate.py autogenerate \"Add new field\"")


if __name__ == "__main__":
    main()
