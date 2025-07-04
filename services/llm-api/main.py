#!/usr/bin/env python3
"""Simple LLM API service running in ROFL TEE."""

import os
import logging
import asyncio
from aiohttp import web
import httpx
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL = "deepseek-r1:1.5b"
PORT = 8080

class LLMService:
    """LLM service that interfaces with Ollama."""
    
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.model = MODEL
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
    
    async def chat(self, messages: list, stream: bool = False):
        """Chat with the LLM."""
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": stream
                    }
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Error in chat: {e}")
                raise

# Initialize service
llm_service = LLMService()

# API Routes
async def health_check(request):
    """Health check endpoint."""
    return web.json_response({"status": "healthy", "model": MODEL})

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

async def chat_handler(request):
    """Handle chat requests."""
    try:
        data = await request.json()
        messages = data.get("messages", [])
        
        if not messages:
            return web.json_response(
                {"error": "Messages are required"}, 
                status=400
            )
        
        result = await llm_service.chat(messages)
        return web.json_response(result)
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return web.json_response(
            {"error": str(e)}, 
            status=500
        )

async def model_info(request):
    """Get model information."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            models = response.json()
            
            # Find our model
            model_info = None
            for model in models.get("models", []):
                if model["name"] == MODEL:
                    model_info = model
                    break
            
            return web.json_response({
                "current_model": MODEL,
                "model_info": model_info,
                "available_models": [m["name"] for m in models.get("models", [])]
            })
        except Exception as e:
            return web.json_response(
                {"error": str(e)}, 
                status=500
            )

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

def create_app():
    """Create the web application."""
    app = web.Application()
    
    # Add routes
    app.router.add_get("/health", health_check)
    app.router.add_post("/generate", generate_handler)
    app.router.add_post("/chat", chat_handler)
    app.router.add_get("/model", model_info)
    
    return app

async def poll_bridge_contract():
    """Poll the LLMBridge contract for requests."""
    contract_address = os.getenv("LLM_BRIDGE_CONTRACT")
    if not contract_address:
        logger.warning("LLM_BRIDGE_CONTRACT not set, skipping bridge integration")
        return
    
    logger.info(f"Starting bridge integration with contract: {contract_address}")
    
    # Simple polling loop - in production, use proper Web3 integration
    while True:
        try:
            # For now, just log that we would poll
            logger.info("Would poll contract for unfulfilled requests...")
            # TODO: Implement actual contract polling via rofl-appd socket
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Bridge polling error: {e}")
            await asyncio.sleep(60)

async def main():
    """Main entry point."""
    logger.info("Starting LLM API service...")
    
    # Wait for Ollama
    await wait_for_ollama()
    
    # Create and run app
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logger.info(f"LLM API running on port {PORT}")
    logger.info(f"Endpoints:")
    logger.info(f"  GET  /health    - Health check")
    logger.info(f"  POST /generate  - Generate text from prompt")
    logger.info(f"  POST /chat      - Chat with message history")
    logger.info(f"  GET  /model     - Get model information")
    
    # Start bridge polling task if configured
    asyncio.create_task(poll_bridge_contract())
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
