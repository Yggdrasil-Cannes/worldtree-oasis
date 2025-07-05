#!/usr/bin/env python3
"""Debug script to test transaction format issues with ROFL API"""

import httpx
import json
import sys
sys.path.append('/Users/pc/projects/worldtree/rofl/services/llm-api')

from abi_encoder import encode_function_call

# Test different transaction formats
def test_transaction_formats():
    transport = httpx.HTTPTransport(uds="/run/rofl-appd.sock")
    
    # Test data - markAnalysisFailed with request ID 0
    request_id = 0
    reason = "Test failure"
    
    # Encode the function call
    encoded_data = encode_function_call("markAnalysisFailed", [request_id, reason])
    print(f"Encoded data: {encoded_data}")
    
    # Test 1: Original format (address without 0x)
    print("\n=== Test 1: Address without 0x prefix ===")
    tx_data_1 = {
        "tx": {
            "kind": "eth",
            "data": {
                "gas_limit": 500000,
                "to": "614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3",  # No 0x
                "value": 0,
                "data": encoded_data  # Has 0x prefix
            }
        },
        "encrypt": True
    }
    print(f"Transaction: {json.dumps(tx_data_1, indent=2)}")
    
    # Test 2: Address with 0x prefix
    print("\n=== Test 2: Address with 0x prefix ===")
    tx_data_2 = {
        "tx": {
            "kind": "eth", 
            "data": {
                "gas_limit": 500000,
                "to": "0x614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3",  # With 0x
                "value": 0,
                "data": encoded_data
            }
        },
        "encrypt": True
    }
    print(f"Transaction: {json.dumps(tx_data_2, indent=2)}")
    
    # Test 3: Without encrypt parameter
    print("\n=== Test 3: Without encrypt parameter ===")
    tx_data_3 = {
        "tx": {
            "kind": "eth",
            "data": {
                "gas_limit": 500000,
                "to": "614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3",
                "value": 0,
                "data": encoded_data
            }
        }
    }
    print(f"Transaction: {json.dumps(tx_data_3, indent=2)}")
    
    # Test 4: With string value for gas_limit
    print("\n=== Test 4: String gas_limit ===")
    tx_data_4 = {
        "tx": {
            "kind": "eth",
            "data": {
                "gas_limit": "500000",  # As string
                "to": "614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3",
                "value": "0",  # As string
                "data": encoded_data
            }
        },
        "encrypt": True
    }
    print(f"Transaction: {json.dumps(tx_data_4, indent=2)}")

if __name__ == "__main__":
    test_transaction_formats()
