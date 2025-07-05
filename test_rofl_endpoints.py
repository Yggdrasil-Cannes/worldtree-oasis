#!/usr/bin/env python3
"""Create a minimal test to verify ROFL API connectivity"""

import httpx
import json

def test_rofl_endpoints():
    """Test basic ROFL API endpoints"""
    # These will fail locally but show us the expected format
    endpoints = [
        ("GET", "/rofl/v1/app/id", None),
        ("POST", "/rofl/v1/keys/generate", {"key_id": "test", "kind": "raw-256"}),
        ("GET", "/rofl/v1/health", None),
    ]
    
    print("Testing ROFL REST API endpoints...")
    print("="*60)
    
    for method, endpoint, data in endpoints:
        print(f"\n{method} {endpoint}")
        if data:
            print(f"Body: {json.dumps(data, indent=2)}")
        print("-"*40)
        
        # Show expected curl command
        if method == "GET":
            print(f"curl --unix-socket /run/rofl-appd.sock http://localhost{endpoint}")
        else:
            print(f"curl --unix-socket /run/rofl-appd.sock -X POST http://localhost{endpoint} \\")
            print(f"  -H 'Content-Type: application/json' \\")
            print(f"  -d '{json.dumps(data)}'")

if __name__ == "__main__":
    test_rofl_endpoints()
