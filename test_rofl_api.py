#!/usr/bin/env python3
"""Test ROFL API endpoints"""

import httpx
import json

ROFL_SOCKET = "/run/rofl-appd.sock"

def test_app_id():
    """Test getting app ID"""
    try:
        transport = httpx.HTTPTransport(uds=ROFL_SOCKET)
        with httpx.Client(transport=transport) as client:
            response = client.get("http://localhost/rofl/v1/app/id")
            print(f"App ID Response: {response.status_code}")
            print(f"App ID: {response.text}")
    except Exception as e:
        print(f"Error getting app ID: {e}")

def test_simple_transaction():
    """Test submitting a simple transaction"""
    try:
        transport = httpx.HTTPTransport(uds=ROFL_SOCKET)
        with httpx.Client(transport=transport) as client:
            # Simple transfer transaction
            tx_data = {
                "tx": {
                    "kind": "eth",
                    "data": {
                        "gas_limit": 100000,
                        "to": "614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3",  # Contract address without 0x
                        "value": 0,
                        "data": "0x"  # Empty data for simple test
                    }
                }
            }
            
            print(f"Sending transaction: {json.dumps(tx_data, indent=2)}")
            
            response = client.post(
                "http://localhost/rofl/v1/tx/sign-submit",
                json=tx_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Transaction Response: {response.status_code}")
            print(f"Response body: {response.text}")
            
    except Exception as e:
        print(f"Error submitting transaction: {e}")

if __name__ == "__main__":
    print("Testing ROFL API endpoints...")
    print("=" * 60)
    
    # Test getting app ID
    test_app_id()
    print("=" * 60)
    
    # Test submitting transaction
    test_simple_transaction()
