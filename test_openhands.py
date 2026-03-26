#!/usr/bin/env python3
"""Test OpenHands installation and functionality."""

try:
    import openhands
    print("✅ OpenHands imported successfully")
    
    # Check available modules
    modules = [x for x in dir(openhands) if not x.startswith('_')]
    print(f"📦 Available modules: {modules[:10]}...")  # Show first 10
    
    # Try to import agent
    try:
        from openhands import agent
        print("✅ Agent module imported successfully")
    except ImportError as e:
        print(f"❌ Agent import failed: {e}")
    
    # Try to import core components
    try:
        from openhands.core import agent as core_agent
        print("✅ Core agent imported successfully")
    except ImportError as e:
        print(f"⚠️ Core agent import failed: {e}")
    
    print("\n🎯 OpenHands installation test completed")
    
except ImportError as e:
    print(f"❌ OpenHands import failed: {e}")
except Exception as e:
    print(f"💥 Unexpected error: {e}")
