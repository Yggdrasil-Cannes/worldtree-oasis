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
from abi_simple import encode_submit_analysis_result, encode_mark_analysis_failed

# Try to import keccak for function selectors
try:
    from Crypto.Hash import keccak
    def compute_selector(signature):
        k = keccak.new(digest_bits=256)
        k.update(signature.encode('utf-8'))
        return '0x' + k.hexdigest()[:8]
except ImportError:
    # Basic implementation without proper keccak
    def compute_selector(signature):
        # This is a fallback - ideally we should have pycryptodome installed
        logger.warning("Using fallback selector computation - install pycryptodome for proper implementation")
        # These are the actual computed selectors
        selectors = {
            "submitAnalysisResult(uint256,string,uint256,string)": "0xdae1ee1f",
            "markAnalysisFailed(uint256,string)": "0x89c4811c"
        }
        return selectors.get(signature, "0x00000000")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PORT = 8080
# Contract address from the handoff document
WORLDTREE_CONTRACT = "0xDF4A26832c770EeC30442337a4F9dd51bbC0a832"
ROFL_SOCKET = "/run/rofl-appd.sock"
POLL_INTERVAL = 30  # seconds
MAX_REQUEST_ID = 1000  # Maximum request ID to check

# Compute function selectors
FUNCTION_SELECTORS = {
    "submitAnalysisResult": compute_selector("submitAnalysisResult(uint256,string,uint256,string)"),
    "markAnalysisFailed": compute_selector("markAnalysisFailed(uint256,string)")
}

class GeneticAnalysisService:
    """Service for processing genetic analysis requests from WorldtreeTest contract"""
    
    def __init__(self):
        self.contract = WORLDTREE_CONTRACT
        self.snp_analyzer = SNPAnalyzer()
        self.last_processed_id = -1
        self.processing_results = {}  # Store results for API access
        logger.info(f"Genetic Analysis Service initialized")
        logger.info(f"Contract: {self.contract}")
        logger.info(f"Function selectors: {FUNCTION_SELECTORS}")
    
    def encode_function_call(self, function_name: str, args: List[Any]) -> str:
        """Encode a function call with arguments using proper ABI encoding"""
        if function_name == "submitAnalysisResult":
            request_id, result_json, confidence, relationship = args
            return encode_submit_analysis_result(request_id, result_json, confidence, relationship)
        elif function_name == "markAnalysisFailed":
            request_id, reason = args
            return encode_mark_analysis_failed(request_id, reason)
        else:
            raise ValueError(f"Unknown function: {function_name}")
    
    async def submit_transaction(self, function_name: str, args: list) -> Optional[dict]:
        """Submit an authenticated transaction to the contract"""
        try:
            # Encode the function call
            encoded_data = self.encode_function_call(function_name, args)
            
            # Prepare the transaction for ROFL appd API
            tx_data = {
                "tx": {
                    "kind": "eth",
                    "data": {
                        "gas_limit": 500000,  # Increased gas limit
                        "to": self.contract.replace("0x", ""),  # Remove 0x prefix
                        "value": 0,
                        "data": encoded_data
                    }
                }
            }
            
            logger.info(f"Submitting transaction {function_name}")
            logger.info(f"Transaction data: {json.dumps(tx_data, indent=2)}")
            
            async with httpx.AsyncClient(transport=httpx.HTTPTransport(uds=ROFL_SOCKET)) as client:
                response = await client.post(
                    "http://localhost/rofl/v1/tx/sign-submit",
                    json=tx_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Transaction submitted successfully: {result}")
                    return result
                else:
                    logger.error(f"Transaction failed with status {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error submitting {function_name}: {e}")
            return None
    
    async def process_test_request(self, request_id: int, user1_snp_data: str, user2_snp_data: str) -> Optional[Dict[str, Any]]:
        """Process a test analysis request with provided SNP data"""
        logger.info(f"Processing test analysis request {request_id}")
        
        try:
            # Parse SNP data
            user1_snp_lines = user1_snp_data.strip().split('\n')
            user2_snp_lines = user2_snp_data.strip().split('\n')
            
            user1_snps = self.snp_analyzer.parse_snp_data(user1_snp_lines)
            user2_snps = self.snp_analyzer.parse_snp_data(user2_snp_lines)
            
            logger.info(f"User 1 SNPs: {len(user1_snps)}")
            logger.info(f"User 2 SNPs: {len(user2_snps)}")
            
            if len(user1_snps) < 100 or len(user2_snps) < 100:
                logger.warning(f"Insufficient SNP data for request {request_id}")
                # Still try to process if we have at least some data
                if len(user1_snps) < 20 or len(user2_snps) < 20:
                    await self.submit_transaction("markAnalysisFailed", [
                        request_id,
                        "Insufficient SNP data"
                    ])
                    return None
            
            # Run genetic analysis
            analysis_result = self.snp_analyzer.run_pca_analysis(user1_snps, user2_snps)
            
            # Store result for API access
            self.processing_results[request_id] = analysis_result
            
            # Submit results to contract
            confidence = int(analysis_result["confidence"] * 100)
            relationship = analysis_result["relationship"]
            
            logger.info(f"Analysis complete for request {request_id}:")
            logger.info(f"  Relationship: {relationship}")
            logger.info(f"  Confidence: {confidence}%")
            logger.info(f"  Common SNPs: {analysis_result['n_common_snps']}")
            logger.info(f"  IBS2 percentage: {analysis_result['ibs2_percentage']:.2f}%")
            logger.info(f"  PCA distance: {analysis_result.get('pca_distance', 'N/A')}")
            
            await self.submit_transaction("submitAnalysisResult", [
                request_id,
                json.dumps(analysis_result),
                confidence,
                relationship
            ])
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}")
            await self.submit_transaction("markAnalysisFailed", [
                request_id,
                f"Processing error: {str(e)}"
            ])
            return None
    
    async def polling_loop(self):
        """Poll for and process pending analysis requests"""
        logger.info("Starting genetic analysis polling loop...")
        
        # Generate more comprehensive test SNP data (200+ SNPs)
        sample_user1_snp = self.generate_test_snp_data(1)
        sample_user2_snp = self.generate_test_snp_data(2)
        
        # Process one test request on startup
        await self.process_test_request(1, sample_user1_snp, sample_user2_snp)
        
        while True:
            try:
                # In production, this would poll the contract for pending requests
                # Since we can't call view functions from ROFL, we'd need an alternative approach
                logger.info("Polling cycle complete. Waiting...")
            except Exception as e:
                logger.error(f"Polling error: {e}")
            
            await asyncio.sleep(POLL_INTERVAL)
    
    def generate_test_snp_data(self, user_id: int) -> str:
        """Generate comprehensive test SNP data with 200+ SNPs"""
        lines = [f"# Sample SNP data for User {user_id}"]
        
        # Common SNPs from chromosome 1
        base_snps = [
            ("rs4477212", "72017", "1", ["AA", "AG"][user_id - 1]),
            ("rs3094315", "742584", "1", "GG"),
            ("rs3131972", "742825", "1", ["AG", "GG"][user_id - 1]),
            ("rs12562034", "758311", "1", "GG"),
            ("rs12124819", "766409", "1", ["AG", "AA"][user_id - 1]),
            ("rs11240777", "788822", "1", ["AG", "GG"][user_id - 1]),
            ("rs6681049", "789870", "1", ["CC", "CT"][user_id - 1]),
            ("rs4970383", "828418", "1", "CC"),
            ("rs4475691", "836671", "1", ["CC", "CT"][user_id - 1]),
            ("rs7537756", "844113", "1", ["AA", "AG"][user_id - 1]),
            ("rs13302982", "845381", "1", ["GG", "AG"][user_id - 1]),
            ("rs1110052", "863421", "1", "GG"),
            ("rs2272756", "882033", "1", ["GG", "AG"][user_id - 1]),
            ("rs3748597", "888639", "1", ["CC", "CT"][user_id - 1]),
            ("rs13303106", "891945", "1", ["AA", "AG"][user_id - 1]),
            ("rs4970421", "903104", "1", "CC"),
            ("rs12726255", "907247", "1", ["GG", "AG"][user_id - 1]),
            ("rs11260542", "910935", "1", "GG"),
            ("rs6672353", "949608", "1", "CC"),
            ("rs7519837", "957898", "1", ["CC", "CT"][user_id - 1]),
        ]
        
        # Add the base SNPs
        for snp in base_snps:
            lines.append("\t".join(snp))
        
        # Generate additional SNPs to reach 200+
        chromosomes = list(range(1, 23)) + ["X", "Y", "MT"]
        alleles = ["AA", "AG", "GG", "CC", "CT", "TT", "AC", "GT"]
        
        for i in range(180):  # Add 180 more to get 200 total
            chr_idx = i % len(chromosomes)
            chromosome = str(chromosomes[chr_idx])
            position = 1000000 + (i * 10000)
            
            # Make some SNPs common between users, others different
            if i % 3 == 0:
                # Common SNP
                genotype = alleles[i % len(alleles)]
            else:
                # Different SNP based on user
                genotype = alleles[(i + user_id) % len(alleles)]
            
            rs_id = f"rs{8000000 + i}"
            lines.append(f"{rs_id}\t{position}\t{chromosome}\t{genotype}")
        
        return "\n".join(lines)
    
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
        "service": "genetic-analysis-fixed",
        "contract": WORLDTREE_CONTRACT,
        "last_processed_id": service.last_processed_id,
        "results_cached": len(service.processing_results),
        "selectors": FUNCTION_SELECTORS
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
        request_id = data.get("request_id", 999)
        
        # If no SNP data provided, use generated test data
        if not user1_snp:
            user1_snp = service.generate_test_snp_data(1)
        if not user2_snp:
            user2_snp = service.generate_test_snp_data(2)
        
        result = await service.process_test_request(request_id, user1_snp, user2_snp)
        
        if result:
            return web.json_response({
                "status": "success",
                "request_id": request_id,
                "result": result
            })
        else:
            return web.json_response({
                "status": "error",
                "message": "Analysis failed"
            }, status=500)
        
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
    logger.info("Starting ROFL Genetic Analysis Service (Fixed Version)")
    logger.info(f"Contract: {WORLDTREE_CONTRACT}")
    logger.info(f"ROFL Socket: {ROFL_SOCKET}")
    logger.info(f"Poll Interval: {POLL_INTERVAL} seconds")
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
    logger.info("")
    logger.info("Processing test genetic analysis on startup...")
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
