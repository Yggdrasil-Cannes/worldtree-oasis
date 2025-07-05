#!/usr/bin/env python3
"""Test ROFL API transaction submission locally"""

import httpx
import json
import sys
import os

# Add the service directory to path
sys.path.append('/Users/pc/projects/worldtree/rofl/services/llm-api')

from abi_encoder import encode_function_call

ROFL_SOCKET = "/run/rofl-appd.sock"
CONTRACT_ADDRESS = "0x614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3"

def test_local_submission():
    """Test if we can submit a transaction locally"""
    
    # Create HTTP client with Unix socket transport
    transport = httpx.HTTPTransport(uds=ROFL_SOCKET)
    
    # First, test if we can connect to the ROFL app
    print("Testing ROFL app connection...")
    
    try:
        with httpx.Client(transport=transport) as client:
            # Try to get app ID
            response = client.get("http://localhost/rofl/v1/app/id")
            if response.status_code == 200:
                app_id = response.text.strip()
                print(f"✓ Connected to ROFL app: {app_id}")
            else:
                print(f"✗ Failed to get app ID: HTTP {response.status_code}")
                return
    except Exception as e:
        print(f"✗ Cannot connect to ROFL socket: {e}")
        print("  Make sure you're running inside the ROFL container")
        return
    
    # Now test transaction submission with minimal data
    print("\nTesting transaction submission...")
    
    # Prepare a simple transaction - just marking request 0 as failed
    request_id = 0
    reason = "Test"
    
    # Encode the function call
    encoded_data = encode_function_call("markAnalysisFailed", [request_id, reason])
    print(f"Encoded data: {encoded_data}")
    
    # Test different formats
    test_cases = [
        {
            "name": "Format 1: No 0x on address, numbers",
            "tx": {
                "kind": "eth",
                "data": {
                    "gas_limit": 500000,
                    "to": CONTRACT_ADDRESS[2:].lower(),  # Remove 0x and lowercase
                    "value": 0,
                    "data": encoded_data
                }
            },
            "encrypt": True
        },
        {
            "name": "Format 2: With 0x on address, numbers",
            "tx": {
                "kind": "eth",
                "data": {
                    "gas_limit": 500000,
                    "to": CONTRACT_ADDRESS.lower(),  # Keep 0x and lowercase
                    "value": 0,
                    "data": encoded_data
                }
            },
            "encrypt": True
        },
        {
            "name": "Format 3: No 0x, strings",
            "tx": {
                "kind": "eth",
                "data": {
                    "gas_limit": "500000",
                    "to": CONTRACT_ADDRESS[2:].lower(),
                    "value": "0",
                    "data": encoded_data
                }
            },
            "encrypt": True
        },
        {
            "name": "Format 4: No encrypt parameter",
            "tx": {
                "kind": "eth",
                "data": {
                    "gas_limit": 500000,
                    "to": CONTRACT_ADDRESS[2:].lower(),
                    "value": 0,
                    "data": encoded_data
                }
            }
        }
    ]
    
    with httpx.Client(transport=transport, timeout=10.0) as client:
        for test_case in test_cases:
            print(f"\n{test_case['name']}:")
            print(f"Request: {json.dumps(test_case, indent=2)}")
            
            try:
                response = client.post(
                    "http://localhost/rofl/v1/tx/sign-submit",
                    json=test_case,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"Response: HTTP {response.status_code}")
                if response.status_code == 200:
                    print(f"✓ Success! Response: {response.json()}")
                    break  # Found working format
                else:
                    print(f"✗ Failed: {response.text[:200]}...")
                    
            except Exception as e:
                print(f"✗ Error: {e}")

if __name__ == "__main__":
    # Check if we're in the right environment
    if not os.path.exists(ROFL_SOCKET):
        print(f"Error: ROFL socket {ROFL_SOCKET} not found.")
        print("This script must be run inside the ROFL container.")
        print("\nTo test locally, run:")
        print("docker compose run --rm genetic-analysis python test_local_rofl.py")
    else:
        test_local_submission()
