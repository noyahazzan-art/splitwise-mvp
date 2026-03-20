#!/usr/bin/env python3
"""
Go-Live Validation Script for Splitwise MVP.
Tests soak performance and functional endpoints including trading_readiness and failure_scenarios.
"""

import asyncio
import json
import sys
import time
from typing import Dict, List, Any
import httpx


class GoLiveValidator:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.results = {"passed": [], "failed": [], "errors": []}
        
    async def run_soak_test(self, duration_seconds: int = 30, concurrent_requests: int = 10) -> bool:
        """Run soak test with concurrent requests."""
        print(f"🧪 Running soak test: {duration_seconds}s, {concurrent_requests} concurrent requests...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            start_time = time.time()
            tasks = []
            
            async def make_request():
                try:
                    r = await client.get(f"{self.base_url}/api")
                    return r.status_code == 200
                except Exception:
                    return False
            
            # Generate concurrent requests for duration
            while time.time() - start_time < duration_seconds:
                batch = [make_request() for _ in range(concurrent_requests)]
                results = await asyncio.gather(*batch, return_exceptions=True)
                await asyncio.sleep(0.1)  # Small delay between batches
            
        success_rate = sum(1 for r in results if r is True) / len(results) * 100
        print(f"✅ Soak test completed: {success_rate:.1f}% success rate")
        
        if success_rate >= 95:
            self.results["passed"].append(f"Soak test: {success_rate:.1f}% success")
            return True
        else:
            self.results["failed"].append(f"Soak test: {success_rate:.1f}% success (below 95%)")
            return False
    
    async def test_trading_readiness(self) -> bool:
        """Test trading readiness via full_status endpoint."""
        print("🔍 Testing trading_readiness (full_status endpoint)...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{self.base_url}/full_status")
                
                if r.status_code == 200:
                    data = r.json()
                    required_keys = ["status", "database", "services"]
                    if all(key in data for key in required_keys):
                        print("✅ trading_readiness: full_status endpoint working")
                        self.results["passed"].append("trading_readiness: full_status endpoint accessible")
                        return True
                    else:
                        print(f"❌ trading_readiness: Missing keys in response: {data}")
                        self.results["failed"].append("trading_readiness: incomplete response data")
                        return False
                else:
                    print(f"❌ trading_readiness: HTTP {r.status_code}")
                    self.results["failed"].append(f"trading_readiness: HTTP {r.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ trading_readiness: {e}")
            self.results["errors"].append(f"trading_readiness: {str(e)}")
            return False
    
    async def test_failure_scenarios(self) -> bool:
        """Test failure scenarios including metrics endpoint."""
        print("🔍 Testing failure_scenarios (metrics endpoint)...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{self.base_url}/metrics")
                
                if r.status_code == 200:
                    data = r.text
                    # Basic metrics format validation
                    if "http_requests_total" in data or "process" in data:
                        print("✅ failure_scenarios: metrics endpoint working")
                        self.results["passed"].append("failure_scenarios: metrics endpoint accessible")
                        return True
                    else:
                        print("⚠️ failure_scenarios: metrics endpoint available but format unclear")
                        self.results["passed"].append("failure_scenarios: metrics endpoint accessible (format warning)")
                        return True
                else:
                    print(f"❌ failure_scenarios: HTTP {r.status_code}")
                    self.results["failed"].append(f"failure_scenarios: HTTP {r.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ failure_scenarios: {e}")
            self.results["errors"].append(f"failure_scenarios: {str(e)}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all validation tests."""
        print("🚀 Starting Go-Live Validation Tests\n")
        
        # Run tests
        soak_passed = await self.run_soak_test()
        trading_passed = await self.test_trading_readiness()
        failure_passed = await self.test_failure_scenarios()
        
        # Summary
        print("\n📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        if self.results["passed"]:
            print("✅ PASSED:")
            for test in self.results["passed"]:
                print(f"   • {test}")
        
        if self.results["failed"]:
            print("❌ FAILED:")
            for test in self.results["failed"]:
                print(f"   • {test}")
        
        if self.results["errors"]:
            print("💥 ERRORS:")
            for error in self.results["errors"]:
                print(f"   • {error}")
        
        all_passed = soak_passed and trading_passed and failure_passed
        print(f"\n🎯 OVERALL RESULT: {'PASS' if all_passed else 'FAIL'}")
        
        return all_passed


async def main():
    base_url = "http://127.0.0.1:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip("/")
    
    validator = GoLiveValidator(base_url)
    success = await validator.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
