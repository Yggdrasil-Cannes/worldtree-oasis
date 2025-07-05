#!/usr/bin/env python3
"""ROFL-aware LLM API service with bridge integration and SNP-based genetic analysis."""

import os
import logging
import asyncio
import httpx
import json
import subprocess
from aiohttp import web
from snp_analyzer import SNPAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL = "deepseek-r1:1.5b"
PORT = 8080
CONTRACT_ADDRESS = os.getenv("LLM_BRIDGE_CONTRACT")
WORLDTREE_CONTRACT = os.getenv("WORLDTREE_CONTRACT")
ROFL_SOCKET = "/run/rofl-appd.sock"

class ROFLBridge:
    """Handle communication with smart contract via ROFL authenticated transactions."""
    
    def __init__(self):
        self.contract = CONTRACT_ADDRESS
        self.worldtree_contract = WORLDTREE_CONTRACT
        logger.info(f"ROFLBridge initialized with contracts: {self.contract}, {self.worldtree_contract}")
    
    async def submit_genetic_match(self, user1, user2, confidence, relationship):
        """Submit genetic match result to Worldtree contract."""
        if not self.worldtree_contract:
            return None
            
        try:
            async with httpx.AsyncClient(transport=httpx.HTTPTransport(uds=ROFL_SOCKET)) as client:
                # Encode the function call for submitGeneticMatch
                # In production, use proper ABI encoding
                tx_data = {
                    "tx": {
                        "kind": "eth",
                        "data": {
                            "gas_limit": 800000,
                            "to": self.worldtree_contract,
                            "value": 0,
                            "data": f"0x12345678"  # Placeholder for actual encoding
                        }
                    }
                }
                
                response = await client.post(
                    "http://localhost/rofl/v1/tx/sign-submit",
                    json=tx_data
                )
                
                if response.status_code == 200:
                    logger.info(f"Genetic match submitted for {user1} and {user2}")
                    return response.json()
                else:
                    logger.error(f"Failed to submit match: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error submitting genetic match: {e}")

class LLMService:
    """LLM service with SNP-based genetic analysis capabilities."""
    
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.model = MODEL
        self.bridge = ROFLBridge() if CONTRACT_ADDRESS else None
        self.snp_analyzer = SNPAnalyzer()
        logger.info(f"LLM Service initialized with SNP genetic analysis")
    
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

# Initialize service
llm_service = LLMService()

# API Routes
async def health_check(request):
    """Health check endpoint."""
    return web.json_response({
        "status": "healthy", 
        "model": MODEL,
        "bridge_enabled": bool(CONTRACT_ADDRESS),
        "genetic_analysis": True
    })

async def pca_analysis_handler(request):
    """Handle PCA analysis for SNP-based genetic relatedness."""
    try:
        data = await request.json()
        
        # Extract SNP data
        user1_snp_data = data.get("user1_snps", [])
        user2_snp_data = data.get("user2_snps", [])
        
        if not user1_snp_data or not user2_snp_data:
            return web.json_response(
                {"error": "Both user1_snps and user2_snps are required"}, 
                status=400
            )
        
        # Parse SNP data
        user1_snps = llm_service.snp_analyzer.parse_snp_data(user1_snp_data)
        user2_snps = llm_service.snp_analyzer.parse_snp_data(user2_snp_data)
        
        if len(user1_snps) < 100 or len(user2_snps) < 100:
            return web.json_response(
                {"error": "Insufficient SNP data. At least 100 SNPs required per user"}, 
                status=400
            )
        
        # Run PCA analysis
        result = llm_service.snp_analyzer.run_pca_analysis(
            user1_snps, 
            user2_snps,
            n_components=data.get("n_components", 10)
        )
        
        # Optionally submit to blockchain if addresses provided
        if data.get("user1_address") and data.get("user2_address") and llm_service.bridge:
            await llm_service.bridge.submit_genetic_match(
                data["user1_address"],
                data["user2_address"],
                result["confidence"],
                result["relationship"]
            )
        
        return web.json_response(result)
    
    except Exception as e:
        logger.error(f"PCA analysis error: {e}")
        return web.json_response(
            {"error": str(e)}, 
            status=500
        )

async def genetic_tips_handler(request):
    """Generate LLM tips for reconnecting with family."""
    try:
        data = await request.json()
        relationship = data.get("relationship", "")
        context = data.get("context", "")
        
        prompt = f"""You are a helpful assistant specializing in family connections and genealogy.
        
A genetic test has revealed a {relationship} relationship. 
Additional context: {context}

Please provide:
1. Tips for reaching out and making initial contact
2. Conversation starters
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
    
    # Genetic analysis endpoints
    app.router.add_post("/pca-analysis", pca_analysis_handler)
    
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
    logger.info("Starting ROFL-aware LLM API with genetic analysis...")
    
    # Log configuration
    logger.info(f"LLM Bridge Contract: {CONTRACT_ADDRESS or 'Not configured'}")
    logger.info(f"Worldtree Contract: {WORLDTREE_CONTRACT or 'Not configured'}")
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
    logger.info("Endpoints:")
    logger.info("  GET  /health        - Health check")
    logger.info("  POST /generate      - Generate text")
    logger.info("  POST /pca-analysis  - Genetic PCA analysis")
    logger.info("  POST /genetic-tips  - Family reconnection tips")
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
