#!/usr/bin/env python3
"""Create minimal test ROFL app to debug transaction format"""

import os
import httpx
import json
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ROFL_SOCKET = "/run/rofl-appd.sock"

async def test_rofl_api():
    """Test different transaction formats against ROFL API"""
    
    # First, check if we can connect
    try:
        transport = httpx.HTTPTransport(uds=ROFL_SOCKET)
        with httpx.Client(transport=transport) as client:
            # Get app ID
            response = client.get("http://localhost/rofl/v1/app/id")
            logger.info(f"App ID response: {response.status_code}")
            if response.status_code == 200:
                logger.info(f"App ID: {response.text}")
    except Exception as e:
        logger.error(f"Cannot connect to ROFL socket: {e}")
        logger.info("This script must be run inside a ROFL container!")
        return
    
    # Test different transaction formats
    tests = [
        {
            "name": "Minimal transaction - no data",
            "tx": {
                "kind": "eth",
                "data": {
                    "gas_limit": 21000,
                    "to": "614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3",
                    "value": 0,
                    "data": "0x"
                }
            }
        },
        {
            "name": "With 0x prefix on address",
            "tx": {
                "kind": "eth",
                "data": {
                    "gas_limit": 21000,
                    "to": "0x614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3",
                    "value": 0,
                    "data": "0x"
                }
            }
        },
        {
            "name": "With encrypt=false",
            "tx": {
                "kind": "eth",
                "data": {
                    "gas_limit": 21000,
                    "to": "614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3",
                    "value": 0,
                    "data": "0x"
                }
            },
            "encrypt": False
        },
        {
            "name": "Simple function call",
            "tx": {
                "kind": "eth",
                "data": {
                    "gas_limit": 100000,
                    "to": "614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3",
                    "value": 0,
                    "data": "0x8da5cb5b"  # owner() function selector
                }
            }
        }
    ]
    
    with httpx.Client(transport=transport, timeout=30.0) as client:
        for test in tests:
            logger.info(f"\n=== Testing: {test['name']} ===")
            
            tx_data = {"tx": test["tx"]}
            if "encrypt" in test:
                tx_data["encrypt"] = test["encrypt"]
            
            logger.debug(f"Request: {json.dumps(tx_data, indent=2)}")
            
            try:
                response = client.post(
                    "http://localhost/rofl/v1/tx/sign-submit",
                    json=tx_data,
                    headers={"Content-Type": "application/json"}
                )
                
                logger.info(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    logger.info(f"Success! Response: {response.json()}")
                else:
                    logger.error(f"Failed! Response: {response.text}")
                    
            except Exception as e:
                logger.error(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_rofl_api())
