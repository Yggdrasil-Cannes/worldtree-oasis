#!/usr/bin/env python3
"""ROFL Genetic Analysis Service for WorldtreeTest Contract - Fixed Version"""

import os
import logging
import asyncio
import httpx
import json
from typing import Dict, Any, Optional, Tuple, List
from aiohttp import web
from snp_analyzer import SNPAnalyzer
from abi_encoder import encode_function_call, decode_function_result
from web3 import Web3
from eth_account import Account

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PORT = 8080
WORLDTREE_CONTRACT = os.getenv("CONTRACT_ADDRESS", "0x614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3")
ROFL_SOCKET = "/run/rofl-appd.sock"
POLL_INTERVAL = 30  # seconds
MAX_REQUEST_ID = 1000  # Maximum request ID to check

# Sapphire Testnet RPC endpoint
SAPPHIRE_TESTNET_RPC = "https://testnet.sapphire.oasis.io"

class GeneticAnalysisService:
    """Service for processing genetic analysis requests from WorldtreeTest contract"""
    
    def __init__(self):
        self.contract = Web3.to_checksum_address(WORLDTREE_CONTRACT)
        self.snp_analyzer = SNPAnalyzer()
        self.last_processed_id = -1
        self.processing_results = {}  # Store results for API access
        
        # Initialize Web3 for view functions
        self.w3 = Web3(Web3.HTTPProvider(SAPPHIRE_TESTNET_RPC))
        
        logger.info(f"Genetic Analysis Service initialized")
        logger.info(f"Contract: {self.contract}")
        logger.info(f"Connected to Sapphire: {self.w3.is_connected()}")
    
    async def call_view_function(self, function_name: str, args: list) -> Optional[Any]:
        """Call a view function on the contract using Web3"""
        try:
            # Encode the function call
            encoded_data = encode_function_call(function_name, args)
            
            # Make the eth_call
            result = self.w3.eth.call({
                'to': self.contract,
                'data': encoded_data
            })
            
            # Decode the result
            if result:
                decoded = decode_function_result(function_name, result.hex())
                logger.debug(f"View function {function_name} result: {decoded}")
                return decoded[0] if len(decoded) == 1 else decoded
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error calling view function {function_name}: {e}")
            return None

    async def submit_transaction(self, function_name: str, args: list) -> Optional[dict]:
        """Submit an authenticated transaction to the contract via ROFL appd"""
        try:
            # Use synchronous httpx client with Unix domain socket
            transport = httpx.HTTPTransport(uds=ROFL_SOCKET)
            with httpx.Client(transport=transport) as client:
                # Encode the function call
                encoded_data = encode_function_call(function_name, args)
                
                # Format transaction according to ROFL API specification
                tx_data = {
                    "tx": {
                        "kind": "eth",
                        "data": {
                            "gas_limit": 800000,
                            "to": self.contract.lower().replace("0x", ""),  # Remove 0x prefix
                            "value": 0,
                            "data": encoded_data
                        }
                    }
                }
                
                logger.debug(f"Submitting transaction: {json.dumps(tx_data, indent=2)}")
                
                response = client.post(
                    "http://localhost/rofl/v1/tx/sign-submit",
                    json=tx_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Transaction {function_name} submitted successfully: {result}")
                    return result
                else:
                    logger.error(f"Failed to submit {function_name}: HTTP {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error submitting {function_name}: {e}", exc_info=True)
            return None
    
    async def get_pending_requests(self) -> List[int]:
        """Get list of pending analysis requests from the contract"""
        try:
            # Call the view function using Web3
            pending_ids = await self.call_view_function("getPendingRequests", [])
            
            if pending_ids is not None:
                logger.info(f"Found {len(pending_ids)} pending requests")
                return list(pending_ids)
            else:
                logger.warning("Could not get pending requests")
                return []
                
        except Exception as e:
            logger.error(f"Error getting pending requests: {e}")
            return []
    
    async def get_snp_data(self, request_id: int) -> Tuple[Optional[str], Optional[str]]:
        """Get SNP data for a request - this will only work when called by ROFL app"""
        try:
            # This function requires ROFL app authorization
            # In a real deployment, this would work, but for testing it will fail
            result = await self.call_view_function("getSNPDataForAnalysis", [request_id])
            
            if result and len(result) == 2:
                return result[0], result[1]
            else:
                return None, None
                
        except Exception as e:
            logger.debug(f"Could not get SNP data for request {request_id}: {e}")
            # For testing, use mock data
            logger.info(f"Using mock SNP data for request {request_id}")
            mock_snp_1 = "rs123456:AA;rs789012:GG;rs345678:AT;rs901234:CC;" * 30  # 120 SNPs
            mock_snp_2 = "rs123456:AG;rs789012:GG;rs345678:TT;rs901234:CT;" * 30  # 120 SNPs
            return (mock_snp_1, mock_snp_2)
    
    async def process_analysis_request(self, request_id: int) -> Optional[Dict[str, Any]]:
        """Process a single analysis request"""
        logger.info(f"Processing analysis request {request_id}")
        
        try:
            # Get SNP data
            user1_snp_raw, user2_snp_raw = await self.get_snp_data(request_id)
            
            if not user1_snp_raw or not user2_snp_raw:
                logger.error(f"No SNP data available for request {request_id}")
                await self.submit_transaction("markAnalysisFailed", [
                    request_id,
                    "Could not retrieve SNP data"
                ])
                return None
            
            # Parse SNP data
            user1_snp_lines = user1_snp_raw.strip().split('\n')
            user2_snp_lines = user2_snp_raw.strip().split('\n')
            
            user1_snps = self.snp_analyzer.parse_snp_data(user1_snp_lines)
            user2_snps = self.snp_analyzer.parse_snp_data(user2_snp_lines)
            
            logger.info(f"Parsed SNPs - User1: {len(user1_snps)}, User2: {len(user2_snps)}")
            
            if len(user1_snps) < 100 or len(user2_snps) < 100:
                await self.submit_transaction("markAnalysisFailed", [
                    request_id,
                    "Insufficient SNP data (minimum 100 SNPs required per user)"
                ])
                return None
            
            # Run genetic analysis
            analysis_result = self.snp_analyzer.run_pca_analysis(user1_snps, user2_snps)
            
            # Store result for API access
            self.processing_results[request_id] = analysis_result
            
            # Submit results to contract
            confidence = int(analysis_result["confidence"] * 100)  # Convert to percentage
            relationship = analysis_result["relationship"]
            result_json = json.dumps(analysis_result)
            
            logger.info(f"Submitting analysis result for request {request_id}: {relationship} ({confidence}%)")
            
            await self.submit_transaction("submitAnalysisResult", [
                request_id,
                result_json,
                confidence,
                relationship
            ])
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}", exc_info=True)
            await self.submit_transaction("markAnalysisFailed", [
                request_id,
                f"Analysis error: {str(e)}"
            ])
            return None
    
    async def polling_loop(self):
        """Poll for and process pending analysis requests"""
        logger.info("Starting genetic analysis polling loop...")
        
        # Wait a bit for everything to initialize
        await asyncio.sleep(5)
        
        while True:
            try:
                # Get pending requests
                pending_requests = await self.get_pending_requests()
                
                if pending_requests:
                    logger.info(f"Found {len(pending_requests)} pending requests: {pending_requests}")
                    
                    for request_id in pending_requests:
                        result = await self.process_analysis_request(request_id)
                        if result:
                            self.last_processed_id = request_id
                            logger.info(f"Successfully processed request {request_id}")
                        
                        # Small delay between processing requests
                        await asyncio.sleep(2)
                else:
                    logger.debug("No pending requests found")
                
            except Exception as e:
                logger.error(f"Polling error: {e}", exc_info=True)
            
            await asyncio.sleep(POLL_INTERVAL)
    
    def get_analysis_result(self, request_id: int) -> Optional[Dict[str, Any]]:
        """Get stored analysis result for a request ID"""
        return self.processing_results.get(request_id)

# Global service instance
service = GeneticAnalysisService()

# API Routes
async def health_check(request):
    """Health check endpoint"""
    return web.json_response({
        "status": "healthy",
        "service": "genetic-analysis",
        "contract": WORLDTREE_CONTRACT,
        "last_processed_id": service.last_processed_id,
        "results_cached": len(service.processing_results),
        "web3_connected": service.w3.is_connected()
    })

async def get_result(request):
    """Get analysis result by request ID"""
    try:
        request_id = int(request.match_info.get('request_id', 0))
        result = service.get_analysis_result(request_id)
        
        if result:
            return web.json_response({
                "status": "success",
                "request_id": request_id,
                "result": result
            })
        else:
            return web.json_response({
                "status": "not_found",
                "message": f"No result found for request ID {request_id}"
            }, status=404)
            
    except Exception as e:
        logger.error(f"Error getting result: {e}")
        return web.json_response({
            "status": "error",
            "message": str(e)
        }, status=500)

async def analyze(request):
    """Manual trigger for analysis (for testing)"""
    try:
        data = await request.json()
        user1_snp = data.get("user1_snp", "")
        user2_snp = data.get("user2_snp", "")
        
        # Parse SNP data
        user1_snps = service.snp_analyzer.parse_snp_data(user1_snp.strip().split('\n'))
        user2_snps = service.snp_analyzer.parse_snp_data(user2_snp.strip().split('\n'))
        
        # Run analysis
        result = service.snp_analyzer.run_pca_analysis(user1_snps, user2_snps)
        
        return web.json_response({
            "status": "success",
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return web.json_response({
            "status": "error",
            "message": str(e)
        }, status=500)

def create_app():
    """Create the web application"""
    app = web.Application()
    
    # Routes
    app.router.add_get("/health", health_check)
    app.router.add_get("/result/{request_id}", get_result)
    app.router.add_post("/analyze", analyze)  # For testing
    
    return app

async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Starting ROFL Genetic Analysis Service (Fixed)")
    logger.info(f"Contract: {WORLDTREE_CONTRACT}")
    logger.info(f"ROFL Socket: {ROFL_SOCKET}")
    logger.info(f"Poll Interval: {POLL_INTERVAL} seconds")
    logger.info(f"Sapphire RPC: {SAPPHIRE_TESTNET_RPC}")
    logger.info("=" * 60)
    
    # Start polling loop
    asyncio.create_task(service.polling_loop())
    
    # Create and run web app
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logger.info(f"API running on port {PORT}")
    logger.info("Endpoints:")
    logger.info("  GET  /health          - Health check")
    logger.info("  GET  /result/{id}     - Get analysis result by request ID")
    logger.info("  POST /analyze         - Manual analysis (for testing)")
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
