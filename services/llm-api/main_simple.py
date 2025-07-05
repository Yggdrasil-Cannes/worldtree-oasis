#!/usr/bin/env python3
"""ROFL Genetic Analysis Service for WorldtreeTest Contract - Simplified Version"""

import os
import logging
import asyncio
import httpx
import json
from typing import Dict, Any, Optional, Tuple
from aiohttp import web
from snp_analyzer import SNPAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PORT = 8080
WORLDTREE_CONTRACT = os.getenv("WORLDTREE_CONTRACT", "0xDF4A26832c770EeC30442337a4F9dd51bbC0a832")
ROFL_SOCKET = "/run/rofl-appd.sock"
POLL_INTERVAL = 30  # seconds
MAX_REQUEST_ID = 1000  # Maximum request ID to check

# Manually encode function signatures (avoiding eth_abi import issues)
FUNCTION_SIGNATURES = {
    "submitAnalysisResult": "0x12345678",  # Placeholder - we'll need the actual signature
    "markAnalysisFailed": "0x87654321"     # Placeholder - we'll need the actual signature
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
    
    async def submit_transaction(self, function_name: str, args: list) -> Optional[dict]:
        """Submit an authenticated transaction to the contract"""
        try:
            async with httpx.AsyncClient(transport=httpx.HTTPTransport(uds=ROFL_SOCKET)) as client:
                # For now, we'll use a simplified approach
                # In production, you'd properly encode the function call
                logger.info(f"Would submit {function_name} with args: {args}")
                
                # Just log for now since we can't properly encode without eth_abi
                return {"status": "logged"}
                    
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
                logger.warning("Insufficient SNP data")
                return None
            
            # Run genetic analysis
            analysis_result = self.snp_analyzer.run_pca_analysis(user1_snps, user2_snps)
            
            # Store result for API access
            self.processing_results[request_id] = analysis_result
            
            # Log results (in production, this would submit to contract)
            confidence = int(analysis_result["confidence"] * 100)
            relationship = analysis_result["relationship"]
            
            logger.info(f"Analysis complete for request {request_id}:")
            logger.info(f"  Relationship: {relationship}")
            logger.info(f"  Confidence: {confidence}%")
            logger.info(f"  Common SNPs: {analysis_result['n_common_snps']}")
            logger.info(f"  IBS2 percentage: {analysis_result['ibs2_percentage']:.2f}%")
            logger.info(f"  PCA distance: {analysis_result.get('pca_distance', 'N/A')}")
            
            # Would submit to contract here
            await self.submit_transaction("submitAnalysisResult", [
                request_id,
                json.dumps(analysis_result),
                confidence,
                relationship
            ])
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}")
            return None
    
    async def polling_loop(self):
        """Poll for and process pending analysis requests"""
        logger.info("Starting genetic analysis polling loop...")
        
        # For testing, let's process a sample request
        sample_user1_snp = """# Sample SNP data for User 1
rs4477212	72017	1	AA
rs3094315	742584	1	GG
rs3131972	742825	1	AG
rs12562034	758311	1	GG
rs12124819	766409	1	AG
rs11240777	788822	1	AG
rs6681049	789870	1	CC
rs4970383	828418	1	CC
rs4475691	836671	1	CC
rs7537756	844113	1	AA
rs13302982	845381	1	GG
rs1110052	863421	1	GG
rs2272756	882033	1	GG
rs3748597	888639	1	CC
rs13303106	891945	1	AA
rs4970421	903104	1	CC
rs12726255	907247	1	GG
rs11260542	910935	1	GG
rs6672353	949608	1	CC
rs7519837	957898	1	CC"""

        sample_user2_snp = """# Sample SNP data for User 2
rs4477212	72017	1	AG
rs3094315	742584	1	GG
rs3131972	742825	1	GG
rs12562034	758311	1	GG
rs12124819	766409	1	AA
rs11240777	788822	1	GG
rs6681049	789870	1	CT
rs4970383	828418	1	CC
rs4475691	836671	1	CT
rs7537756	844113	1	AG
rs13302982	845381	1	AG
rs1110052	863421	1	GG
rs2272756	882033	1	AG
rs3748597	888639	1	CT
rs13303106	891945	1	AG
rs4970421	903104	1	CC
rs12726255	907247	1	AG
rs11260542	910935	1	GG
rs6672353	949608	1	CC
rs7519837	957898	1	CT"""

        # Process one test request on startup
        await self.process_test_request(1, sample_user1_snp, sample_user2_snp)
        
        while True:
            try:
                logger.info("Polling cycle complete. Waiting...")
            except Exception as e:
                logger.error(f"Polling error: {e}")
            
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
        "service": "genetic-analysis-simplified",
        "contract": WORLDTREE_CONTRACT,
        "last_processed_id": service.last_processed_id,
        "results_cached": len(service.processing_results)
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
    logger.info("Starting ROFL Genetic Analysis Service (Simplified)")
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
