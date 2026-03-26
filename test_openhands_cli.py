#!/usr/bin/env python3
"""Test OpenHands CLI functionality."""

import subprocess
import sys

def run_command(cmd):
    """Run command and return result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def test_openhands():
    """Test OpenHands CLI."""
    print("🧪 Testing OpenHands CLI...")
    
    # Test 1: Check if openhands command exists
    print("\n1. Testing openhands command...")
    code, stdout, stderr = run_command("openhands --help")
    if code == 0:
        print("✅ OpenHands CLI is available")
        print(f"📄 Help output (first 200 chars): {stdout[:200]}...")
    else:
        print(f"❌ OpenHands CLI failed: {stderr}")
    
    # Test 2: Try python -m openhands
    print("\n2. Testing python -m openhands...")
    code, stdout, stderr = run_command("python -m openhands --help")
    if code == 0:
        print("✅ Python module OpenHands works")
        print(f"📄 Help output (first 200 chars): {stdout[:200]}...")
    else:
        print(f"❌ Python module failed: {stderr}")
    
    # Test 3: Check installation
    print("\n3. Checking installation details...")
    code, stdout, stderr = run_command("pip show openhands")
    if code == 0:
        print("✅ Package info retrieved")
        print(f"📦 Version: {stdout.split('Version: ')[1].split()[0] if 'Version: ' in stdout else 'Unknown'}")
    else:
        print(f"❌ Package info failed: {stderr}")

if __name__ == "__main__":
    test_openhands()
