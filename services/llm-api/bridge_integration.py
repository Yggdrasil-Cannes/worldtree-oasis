#!/usr/bin/env python3
"""ROFL LLM Bridge Integration - Polls contract for requests and submits responses."""

import asyncio
import httpx
import json
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CONTRACT_ADDRESS = "0x32f22B267Be8CD47FAF93Bcd1CC31059bdc24FD2"
ROFL_API_SOCKET = "/run/rofl-appd.sock"
POLL_INTERVAL = 10  # seconds

# Contract ABI for the functions we need
CONTRACT_ABI = [
    {
        "name": "getUnfulfilledRequests",
        "type": "function",
        "inputs": [{"name": "limit", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256[]"}],
        "stateMutability": "view"
    },
    {
        "name": "getRequest",
        "type": "function",
        "inputs": [{"name": "requestId", "type": "uint256"}],
        "outputs": [
            {"name": "requester", "type": "address"},
            {"name": "prompt", "type": "string"},
            {"name": "timestamp", "type": "uint256"},
            {"name": "fulfilled", "type": "bool"},
            {"name": "response", "type": "string"}
        ],
        "stateMutability": "view"
    },
    {
        "name": "submitResponse",
        "type": "function",
        "inputs": [
            {"name": "requestId", "type": "uint256"},
            {"name": "response", "type": "string"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    }
]

class LLMBridgeClient:
    """Client for interacting with the LLMBridge contract via ROFL authenticated transactions."""
    
    def __init__(self):
        self.transport = httpx.HTTPTransport(uds=ROFL_API_SOCKET)
        
    async def call_contract_view(self, function_name: str, params: List) -> any:
        """Call a view function on the contract."""
        # Encode function call (simplified - in production use proper ABI encoding)
        # For now, we'll use the ROFL API to handle encoding
        
        async with httpx.AsyncClient(transport=self.transport, base_url="http://localhost") as client:
            # This is a simplified example - actual implementation would need proper ABI encoding
            logger.info(f"Calling {function_name} with params: {params}")
            # For view functions, we'd use eth_call through the ROFL API
            # Implementation depends on ROFL API specifics
            return []
    
    async def submit_transaction(self, function_name: str, params: List) -> str:
        """Submit an authenticated transaction to the contract."""
        async with httpx.AsyncClient(transport=self.transport, base_url="http://localhost") as client:
            # Prepare transaction data
            tx_data = {
                "tx": {
                    "kind": "eth",
                    "data": {
                        "gas_limit": 500000,
                        "to": CONTRACT_ADDRESS,
                        "value": 0,
                        "data": self._encode_function_call(function_name, params)
                    }
                }
            }
            
            response = await client.post("/rofl/v1/tx/sign-submit", json=tx_data)
            response.raise_for_status()
            return response.json()
    
    def _encode_function_call(self, function_name: str, params: List) -> str:
        """Encode function call data (simplified)."""
        # In production, use proper ABI encoding library
        # This is a placeholder that would need proper implementation
        if function_name == "submitResponse":
            # submitResponse(uint256,string) signature
            return "0xdae1ee1f" + "0" * 64  # Simplified encoding
        return "0x"

async def process_llm_request(prompt: str) -> str:
    """Send prompt to Ollama and get response."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "deepseek-r1:1.5b",
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "Error: No response from model")
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return f"Error processing request: {str(e)}"

async def main():
    """Main loop to poll for requests and submit responses."""
    logger.info("Starting LLM Bridge integration...")
    client = LLMBridgeClient()
    
    while True:
        try:
            # Get unfulfilled requests (limit 10)
            logger.info("Checking for unfulfilled requests...")
            request_ids = await client.call_contract_view("getUnfulfilledRequests", [10])
            
            if request_ids:
                logger.info(f"Found {len(request_ids)} unfulfilled requests")
                
                for request_id in request_ids:
                    # Get request details
                    request_data = await client.call_contract_view("getRequest", [request_id])
                    requester, prompt, timestamp, fulfilled, _ = request_data
                    
                    if not fulfilled:
                        logger.info(f"Processing request {request_id}: {prompt[:50]}...")
                        
                        # Process with LLM
                        response = await process_llm_request(prompt)
                        
                        # Submit response
                        logger.info(f"Submitting response for request {request_id}")
                        tx_result = await client.submit_transaction(
                            "submitResponse", 
                            [request_id, response]
                        )
                        logger.info(f"Response submitted: {tx_result}")
            
            else:
                logger.info("No unfulfilled requests found")
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        
        # Wait before next poll
        await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
