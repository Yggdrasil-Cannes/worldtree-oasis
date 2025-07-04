#!/usr/bin/env python3
"""ROFL-aware LLM API service with bridge integration."""

import os
import logging
import asyncio
import httpx
import json
from aiohttp import web
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL = "deepseek-r1:1.5b"
PORT = 8080
CONTRACT_ADDRESS = os.getenv("LLM_BRIDGE_CONTRACT")
ROFL_SOCKET = "/run/rofl-appd.sock"

class ROFLBridge:
    """Handle communication with smart contract via ROFL authenticated transactions."""
    
    def __init__(self):
        self.contract = CONTRACT_ADDRESS
        logger.info(f"ROFLBridge initialized with contract: {self.contract}")
    
    async def check_unfulfilled_requests(self):
        """Check for unfulfilled requests via eth_call."""
        # In a real implementation, we'd use the ROFL API to make an eth_call
        # to getUnfulfilledRequests(10) on the contract
        # For now, we'll use a simple approach
        
        # Function selector for getUnfulfilledRequests(uint256)
        # This is 0x5e9a523c + encoded uint256(10)
        call_data = "0x5e9a523c000000000000000000000000000000000000000000000000000000000000000a"
        
        try:
            # Make the call via curl to the ROFL socket
            # In production, use proper HTTP client with UNIX socket support
            result = subprocess.run([
                'curl', '-X', 'POST',
                '--unix-socket', ROFL_SOCKET,
                'http://localhost/rofl/v1/tx/eth-call',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps({
                    "to": self.contract,
                    "data": call_data
                })
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse result - would need proper ABI decoding
                logger.info(f"Contract call result: {result.stdout}")
                return []
            else:
                logger.error(f"Contract call failed: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"Error checking requests: {e}")
            return []
    
    async def submit_response(self, request_id: int, response: str):
        """Submit response via authenticated transaction."""
        # Function selector for submitResponse(uint256,string)
        # This is 0xdae1ee1f + encoded parameters
        
        # Simplified encoding - in production use proper ABI encoder
        request_id_hex = format(request_id, '064x')
        # For the string, we need proper ABI encoding with offset and length
        # This is a simplified version
        
        try:
            # Use the ROFL authenticated transaction API
            async with httpx.AsyncClient(transport=httpx.HTTPTransport(uds=ROFL_SOCKET)) as client:
                tx_data = {
                    "tx": {
                        "kind": "eth",
                        "data": {
                            "gas_limit": 500000,
                            "to": self.contract,
                            "value": 0,
                            "data": f"0xdae1ee1f{request_id_hex}"  # Simplified
                        }
                    }
                }
                
                response = await client.post(
                    "http://localhost/rofl/v1/tx/sign-submit",
                    json=tx_data
                )
                
                if response.status_code == 200:
                    logger.info(f"Response submitted for request {request_id}")
                    return response.json()
                else:
                    logger.error(f"Failed to submit response: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error submitting response: {e}")

class LLMService:
    """LLM service that interfaces with Ollama."""
    
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.model = MODEL
        self.bridge = ROFLBridge() if CONTRACT_ADDRESS else None
        logger.info(f"LLM Service initialized with Ollama at {self.ollama_url}, model: {self.model}")
    
    async def generate(self, prompt: str, stream: bool = False):
        """Generate a response from the LLM."""
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": stream
                    }
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                raise
    
    async def process_bridge_requests(self):
        """Poll and process requests from the bridge contract."""
        if not self.bridge:
            return
            
        while True:
            try:
                # Check for unfulfilled requests
                request_ids = await self.bridge.check_unfulfilled_requests()
                
                if request_ids:
                    logger.info(f"Found {len(request_ids)} unfulfilled requests")
                    # In a real implementation, we'd process each request
                    # For now, let's handle a hardcoded test
                    
                    # Process request ID 0 as a test
                    test_prompt = "Hello, can you explain what ROFL is?"
                    logger.info(f"Processing test request: {test_prompt}")
                    
                    result = await self.generate(test_prompt)
                    response_text = result.get('response', 'ROFL is Runtime Off-chain Logic...')
                    
                    # Submit response
                    await self.bridge.submit_response(0, response_text[:200])  # Truncate for now
                    
                await asyncio.sleep(30)  # Poll every 30 seconds
                
            except Exception as e:
                logger.error(f"Bridge processing error: {e}")
                await asyncio.sleep(60)

# Initialize service
llm_service = LLMService()

# API Routes (same as before)
async def health_check(request):
    """Health check endpoint."""
    return web.json_response({
        "status": "healthy", 
        "model": MODEL,
        "bridge_enabled": bool(CONTRACT_ADDRESS)
    })

async def generate_handler(request):
    """Handle text generation requests."""
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        
        if not prompt:
            return web.json_response(
                {"error": "Prompt is required"}, 
                status=400
            )
        
        result = await llm_service.generate(prompt)
        return web.json_response(result)
    
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return web.json_response(
            {"error": str(e)}, 
            status=500
        )

def create_app():
    """Create the web application."""
    app = web.Application()
    app.router.add_get("/health", health_check)
    app.router.add_post("/generate", generate_handler)
    return app

async def wait_for_ollama():
    """Wait for Ollama to be ready."""
    logger.info("Waiting for Ollama to be ready...")
    max_retries = 30
    
    for i in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{OLLAMA_URL}/api/tags")
                if response.status_code == 200:
                    logger.info("Ollama is ready!")
                    return True
        except:
            pass
        
        await asyncio.sleep(5)
        logger.info(f"Waiting for Ollama... ({i+1}/{max_retries})")
    
    raise Exception("Ollama failed to start in time")

async def main():
    """Main entry point."""
    logger.info("Starting ROFL-aware LLM API service...")
    
    # Log configuration
    logger.info(f"Contract: {CONTRACT_ADDRESS or 'Not configured'}")
    logger.info(f"ROFL Socket: {ROFL_SOCKET}")
    
    # Wait for Ollama
    await wait_for_ollama()
    
    # Create and run app
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logger.info(f"LLM API running on port {PORT}")
    
    # Start bridge polling if configured
    if llm_service.bridge:
        logger.info("Starting bridge contract polling...")
        asyncio.create_task(llm_service.process_bridge_requests())
    else:
        logger.warning("No bridge contract configured, running in standalone mode")
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
