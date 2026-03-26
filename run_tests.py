#!/usr/bin/env python3
"""
Comprehensive test runner for Splitwise MVP.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle the result."""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print(f"PASSED {description}")
            if result.stdout:
                print(f"Output: {result.stdout}")
        else:
            print(f"FAILED {description}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            if result.stdout:
                print(f"Output: {result.stdout}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"ERROR {description}: {e}")
        return False


def main():
    """Run all tests and checks."""
    print("Splitwise MVP Test Suite")
    print("=" * 60)
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    tests = [
        ("python -m pytest tests/test_auth.py -v", "Authentication Tests"),
        ("python -m pytest tests/test_groups.py -v", "Groups Tests"),
        ("python -m pytest tests/test_expenses.py -v", "Expenses Tests"),
        ("python -c \"from app.main import app; print('Application imports successfully')\"", "Application Import Test"),
        ("python -c \"import httpx; print('HTTP client available')\"", "HTTP Client Test"),
        ("python -c \"from app.auth import get_password_hash; print('Auth module works')\"", "Auth Module Test"),
    ]
    
    results = []
    for cmd, desc in tests:
        results.append(run_command(cmd, desc))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed == total:
        print("\nALL TESTS PASSED!")
        print("Splitwise MVP is ready for deployment")
        return 0
    else:
        print(f"\n{total - passed} TESTS FAILED")
        print("Please review the failed tests above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
