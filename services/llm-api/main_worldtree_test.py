#!/usr/bin/env python3
"""ROFL-aware service with WorldtreeTest contract integration and genetic analysis."""

import os
import logging
import asyncio
import httpx
import json
from aiohttp import web
from snp_analyzer import SNPAnalyzer
from abi_encoder import encode_function_call, decode_function_result

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL = "deepseek-r1:1.5b"
PORT = 8080
WORLDTREE_CONTRACT = os.getenv("WORLDTREE_CONTRACT")
ROFL_SOCKET = "/run/rofl-appd.sock"
POLL_INTERVAL = 30  # seconds

class WorldtreeROFLBridge:
    """Handle communication with WorldtreeTest contract via ROFL authenticated transactions."""
    
    def __init__(self):
        self.contract = WORLDTREE_CONTRACT
        self.snp_analyzer = SNPAnalyzer()
        logger.info(f"WorldtreeROFLBridge initialized with contract: {self.contract}")
    
    async def call_contract_view(self, function_name, args=[]):
        """Call a view function on the contract."""
        try:
            async with httpx.AsyncClient(transport=httpx.HTTPTransport(uds=ROFL_SOCKET)) as client:
                # Encode the function call
                encoded_data = encode_function_call(function_name, args)
                
                # For view functions, we use eth_call
                call_data = {
                    "method": "eth_call",
                    "params": [{
                        "to": self.contract,
                        "data": encoded_data
                    }, "latest"]
                }
                
                response = await client.post(
                    "http://localhost/rofl/v1/eth/call",
                    json=call_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return decode_function_result(function_name, result.get("result", "0x"))
                else:
                    logger.error(f"Failed to call {function_name}: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling {function_name}: {e}")
            return None
    
    async def submit_transaction(self, function_name, args):
        """Submit an authenticated transaction to the contract."""
        try:
            async with httpx.AsyncClient(transport=httpx.HTTPTransport(uds=ROFL_SOCKET)) as client:
                # Encode the function call
                encoded_data = encode_function_call(function_name, args)
                
                tx_data = {
                    "tx": {
                        "kind": "eth",
                        "data": {
                            "gas_limit": 800000,
                            "to": self.contract,
                            "value": 0,
                            "data": encoded_data
                        }
                    }
                }
                
                response = await client.post(
                    "http://localhost/rofl/v1/tx/sign-submit",
                    json=tx_data
                )
                
                if response.status_code == 200:
                    logger.info(f"Transaction {function_name} submitted successfully")
                    return response.json()
                else:
                    logger.error(f"Failed to submit {function_name}: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error submitting {function_name}: {e}")
            return None
    
    async def get_pending_requests(self):
        """Get all pending analysis requests from the contract."""
        result = await self.call_contract_view("getPendingRequests")
        if result:
            return result[0]  # The function returns a tuple with array as first element
        return []
    
    async def get_snp_data(self, request_id):
        """Get SNP data for a specific request."""
        result = await self.call_contract_view("getSNPDataForAnalysis", [request_id])
        if result:
            return result[0], result[1]  # user1SNP, user2SNP
        return None, None
    
    async def process_analysis_request(self, request_id):
        """Process a single analysis request."""
        logger.info(f"Processing analysis request {request_id}")
        
        try:
            # Get SNP data for both users
            user1_snp_raw, user2_snp_raw = await self.get_snp_data(request_id)
            
            if not user1_snp_raw or not user2_snp_raw:
                await self.submit_transaction("markAnalysisFailed", [
                    request_id,
                    "Failed to retrieve SNP data"
                ])
                return
            
            # Parse SNP data
            user1_snp_lines = user1_snp_raw.strip().split('\n')
            user2_snp_lines = user2_snp_raw.strip().split('\n')
            
            user1_snps = self.snp_analyzer.parse_snp_data(user1_snp_lines)
            user2_snps = self.snp_analyzer.parse_snp_data(user2_snp_lines)
            
            if len(user1_snps) < 100 or len(user2_snps) < 100:
                await self.submit_transaction("markAnalysisFailed", [
                    request_id,
                    "Insufficient SNP data (minimum 100 SNPs required per user)"
                ])
                return
            
            # Run genetic analysis
            analysis_result = self.snp_analyzer.run_pca_analysis(user1_snps, user2_snps)
            
            # Submit results to contract
            confidence = int(analysis_result["confidence"] * 100)  # Convert to percentage
            relationship = analysis_result["relationship"]
            result_json = json.dumps(analysis_result)
            
            await self.submit_transaction("submitAnalysisResult", [
                request_id,
                result_json,
                confidence,
                relationship
            ])
            
            logger.info(f"Analysis complete for request {request_id}: {relationship} ({confidence}%)")
            
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}")
            await self.submit_transaction("markAnalysisFailed", [
                request_id,
                f"Analysis error: {str(e)}"
            ])
    
    async def start_polling(self):
        """Start polling for pending analysis requests."""
        logger.info("Starting WorldtreeTest contract polling...")
        
        while True:
            try:
                # Get pending requests
                pending_requests = await self.get_pending_requests()
                
                if pending_requests:
                    logger.info(f"Found {len(pending_requests)} pending requests")
                    
                    # Process each request
                    for request_id in pending_requests:
                        await self.process_analysis_request(request_id)
                else:
                    logger.debug("No pending requests")
                
            except Exception as e:
                logger.error(f"Polling error: {e}")
            
            # Wait before next poll
            await asyncio.sleep(POLL_INTERVAL)

class LLMService:
    """LLM service with genetic analysis tips generation."""
    
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.model = MODEL
        logger.info(f"LLM Service initialized")
    
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

# Initialize services
llm_service = LLMService()
bridge = WorldtreeROFLBridge() if WORLDTREE_CONTRACT else None

# API Routes
async def health_check(request):
    """Health check endpoint."""
    return web.json_response({
        "status": "healthy", 
        "model": MODEL,
        "worldtree_contract": WORLDTREE_CONTRACT or "Not configured",
        "genetic_analysis": True,
        "polling_active": bool(bridge)
    })

async def genetic_tips_handler(request):
    """Generate LLM tips for reconnecting with family."""
    try:
        data = await request.json()
        relationship = data.get("relationship", "")
        confidence = data.get("confidence", 0)
        context = data.get("context", "")
        
        prompt = f"""You are a helpful assistant specializing in family connections and genealogy.
        
A genetic test has revealed a {relationship} relationship with {confidence}% confidence.
Additional context: {context}

Please provide:
1. Tips for reaching out and making initial contact
2. Conversation starters appropriate for this relationship
3. Important questions to verify the relationship
4. Cultural considerations for family reunions
5. Next steps for building the relationship

Be warm, supportive, and practical in your advice."""

        result = await llm_service.generate(prompt)
        
        return web.json_response({
            "status": "success",
            "tips": result.get("response", "")
        })
        
    except Exception as e:
        logger.error(f"Tips generation error: {e}")
        return web.json_response(
            {"error": str(e)}, 
            status=500
        )

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
    
    # Health check
    app.router.add_get("/health", health_check)
    
    # LLM endpoints
    app.router.add_post("/generate", generate_handler)
    app.router.add_post("/genetic-tips", genetic_tips_handler)
    
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
    logger.info("Starting ROFL WorldtreeTest service...")
    
    # Log configuration
    logger.info(f"Worldtree Contract: {WORLDTREE_CONTRACT or 'Not configured'}")
    logger.info(f"ROFL Socket: {ROFL_SOCKET}")
    logger.info(f"Poll Interval: {POLL_INTERVAL} seconds")
    
    # Wait for Ollama
    await wait_for_ollama()
    
    # Start contract polling if configured
    if bridge:
        asyncio.create_task(bridge.start_polling())
        logger.info("Started WorldtreeTest contract polling")
    else:
        logger.warning("No Worldtree contract configured - polling disabled")
    
    # Create and run app
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logger.info(f"API running on port {PORT}")
    logger.info("Endpoints:")
    logger.info("  GET  /health        - Health check")
    logger.info("  POST /generate      - Generate text")
    logger.info("  POST /genetic-tips  - Family reconnection tips")
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
