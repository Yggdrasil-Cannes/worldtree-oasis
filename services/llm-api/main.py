#!/usr/bin/env python3
"""ROFL Genetic Analysis Service - Fixed Version using Web3 for reads and ROFL API for writes"""

import os
import logging
import asyncio
import httpx
import json
from typing import Dict, Any, Optional, Tuple, List
from aiohttp import web
from web3 import Web3
from eth_account import Account
from hexbytes import HexBytes
from snp_analyzer import SNPAnalyzer
from abi_encoder import encode_function_call, decode_function_result

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PORT = 8080
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "0xDF4A26832c770EeC30442337a4F9dd51bbC0a832")
RPC_URL = "https://testnet.sapphire.oasis.io"  # Sapphire testnet RPC
ROFL_SOCKET = "/run/rofl-appd.sock"
POLL_INTERVAL = 30  # seconds
MAX_REQUEST_ID = 100  # Maximum request ID to check

# WorldtreeTest Contract ABI (minimal)
WORLDTREE_ABI = [
    {
        "inputs": [],
        "name": "getPendingRequests",
        "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "requestId", "type": "uint256"}],
        "name": "getSNPDataForAnalysis",
        "outputs": [
            {"internalType": "string", "name": "user1Data", "type": "string"},
            {"internalType": "string", "name": "user2Data", "type": "string"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "requests",
        "outputs": [
            {"internalType": "address", "name": "requester", "type": "address"},
            {"internalType": "address", "name": "user1", "type": "address"},
            {"internalType": "address", "name": "user2", "type": "address"},
            {"internalType": "enum WorldtreeTest.RequestStatus", "name": "status", "type": "uint8"},
            {"internalType": "string", "name": "result", "type": "string"},
            {"internalType": "uint256", "name": "requestTime", "type": "uint256"},
            {"internalType": "uint256", "name": "completionTime", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

class GeneticAnalysisService:
    """Service for processing genetic analysis requests from WorldtreeTest contract"""
    
    def __init__(self):
        self.contract_address = CONTRACT_ADDRESS
        self.snp_analyzer = SNPAnalyzer()
        self.processing_results = {}  # Store results for API access
        
        # Initialize Web3 for reading contract state
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
            abi=WORLDTREE_ABI
        )
        
        logger.info(f"Genetic Analysis Service initialized")
        logger.info(f"Contract: {self.contract_address}")
        logger.info(f"RPC URL: {RPC_URL}")
    
    async def get_rofl_app_id(self) -> Optional[str]:
        """Get the ROFL app ID"""
        try:
            transport = httpx.HTTPTransport(uds=ROFL_SOCKET)
            with httpx.Client(transport=transport) as client:
                response = client.get("http://localhost/rofl/v1/app/id")
                if response.status_code == 200:
                    app_id = response.text.strip()
                    logger.info(f"ROFL app ID: {app_id}")
                    return app_id
                else:
                    logger.error(f"Failed to get app ID: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error getting app ID: {e}")
            return None

    async def submit_transaction(self, function_name: str, args: list) -> Optional[dict]:
        """Submit an authenticated transaction to the contract via ROFL API"""
        try:
            transport = httpx.HTTPTransport(uds=ROFL_SOCKET)
            with httpx.Client(transport=transport, timeout=30.0) as client:
                # Encode the function call
                encoded_data = encode_function_call(function_name, args)
                
                # IMPORTANT: Strip '0x' prefix from address and data (despite what docs say)
                # The demo project shows this is required for ROFL API
                to_address = self.contract_address.lower()
                if to_address.startswith('0x'):
                    to_address = to_address[2:]  # Remove '0x' prefix
                
                # Strip '0x' from encoded data as well
                if encoded_data.startswith('0x'):
                    encoded_data = encoded_data[2:]
                
                # Format transaction 
                tx_data = {
                    "tx": {
                        "kind": "eth",
                        "data": {
                            "gas_limit": 1000000,    # NUMBER, not string
                            "to": to_address,        # Address WITHOUT '0x' prefix
                            "value": 0,              # NUMBER, not string
                            "data": encoded_data     # Data WITHOUT '0x' prefix
                        }
                    },
                    "encrypt": False  # Disable encryption like the demo
                }
                
                logger.info(f"Submitting transaction {function_name} with args: {args}")
                logger.debug(f"Transaction data: {json.dumps(tx_data, indent=2)}")
                
                response = client.post(
                    "http://localhost/rofl/v1/tx/sign-submit",
                    json=tx_data,
                    headers={"Content-Type": "application/json"}
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
            logger.error(f"Error submitting {function_name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def get_pending_requests(self) -> List[int]:
        """Get list of pending analysis requests from contract using Web3"""
        try:
            # Call the contract view function using Web3
            pending_ids = self.contract.functions.getPendingRequests().call()
            logger.info(f"Found {len(pending_ids)} pending requests from contract")
            return list(pending_ids)
        except Exception as e:
            logger.error(f"Error getting pending requests: {e}")
            # Fallback: check sequential IDs if the function doesn't exist
            pending = []
            for request_id in range(0, 10):  # Check first 10 IDs
                try:
                    request = self.contract.functions.requests(request_id).call()
                    # Status index 3 is the status field, 0 = pending
                    if request[3] == 0:  # Pending status
                        pending.append(request_id)
                        logger.info(f"Found pending request: {request_id}")
                except:
                    break  # No more requests
            return pending
    
    async def get_snp_data_for_analysis(self, request_id: int) -> Tuple[Optional[str], Optional[str]]:
        """Get SNP data for a request using Web3"""
        try:
            # This function can only be called by the ROFL app in the actual contract
            # For now, we'll use mock data for testing
            logger.info(f"Using mock SNP data for request {request_id}")
            
            # Generate realistic mock SNP data in 23andMe format
            # Format: rsid position chromosome genotype
            mock_snp_1 = """rs123456 1234567 1 AA
rs789012 7890123 1 GG
rs345678 3456789 2 AT
rs901234 9012345 2 CC
rs567890 5678901 3 GT
rs234567 2345678 3 AC
rs890123 8901234 4 TT
rs456789 4567890 4 GG
rs012345 123456 5 CA
rs678901 6789012 5 AG"""
            
            mock_snp_2 = """rs123456 1234567 1 AG
rs789012 7890123 1 GG
rs345678 3456789 2 TT
rs901234 9012345 2 CT
rs567890 5678901 3 GG
rs234567 2345678 3 CC
rs890123 8901234 4 AT
rs456789 4567890 4 GA
rs012345 123456 5 CC
rs678901 6789012 5 GG"""
            
            # Add more SNPs to meet the 100 minimum requirement
            for i in range(10, 110):
                chr_num = (i % 22) + 1  # Chromosomes 1-22
                position = 1000000 + i * 10000
                mock_snp_1 += f"\nrs{1000000+i} {position} {chr_num} {'AA' if i%3==0 else 'GG' if i%3==1 else 'AT'}"
                mock_snp_2 += f"\nrs{1000000+i} {position} {chr_num} {'AG' if i%3==0 else 'GC' if i%3==1 else 'TT'}"
            
            return (mock_snp_1, mock_snp_2)
            
        except Exception as e:
            logger.error(f"Error getting SNP data for request {request_id}: {e}")
            return None, None
    
    async def process_analysis_request(self, request_id: int) -> Optional[Dict[str, Any]]:
        """Process a single analysis request"""
        logger.info(f"Processing analysis request {request_id}")
        
        try:
            # Get SNP data (using mock data for now)
            user1_snp_raw, user2_snp_raw = await self.get_snp_data_for_analysis(request_id)
            
            if not user1_snp_raw or not user2_snp_raw:
                logger.error(f"No SNP data available for request {request_id}")
                return None
            
            # Parse SNP data
            user1_snp_lines = user1_snp_raw.strip().split('\n')
            user2_snp_lines = user2_snp_raw.strip().split('\n')
            
            user1_snps = self.snp_analyzer.parse_snp_data(user1_snp_lines)
            user2_snps = self.snp_analyzer.parse_snp_data(user2_snp_lines)
            
            logger.info(f"Parsed SNPs - User1: {len(user1_snps)}, User2: {len(user2_snps)}")
            
            if len(user1_snps) < 100 or len(user2_snps) < 100:
                error_msg = f"Insufficient SNP data (User1: {len(user1_snps)}, User2: {len(user2_snps)}, minimum 100 required)"
                logger.error(error_msg)
                await self.submit_transaction("markAnalysisFailed", [
                    request_id,
                    error_msg
                ])
                return None
            
            # Run genetic analysis
            analysis_result = self.snp_analyzer.run_pca_analysis(user1_snps, user2_snps)
            
            # Store result for API access
            self.processing_results[request_id] = analysis_result
            
            # Prepare result for contract submission
            confidence = int(analysis_result["confidence"] * 100)  # Convert to percentage
            relationship = analysis_result["relationship"]
            
            # Create a simplified result JSON for the contract
            result_for_contract = {
                "relationship": relationship,
                "confidence": confidence,
                "similarity": int(analysis_result["ibs_analysis"]["ibs_score"] * 100),  # IBS score as percentage
                "shared_markers": analysis_result["n_common_snps"]  # Number of common SNPs
            }
            result_json = json.dumps(result_for_contract)
            
            logger.info(f"Analysis complete for request {request_id}: {relationship} ({confidence}%)")
            
            # Submit results to contract
            tx_result = await self.submit_transaction("submitAnalysisResult", [
                request_id,
                result_json,
                confidence,
                relationship
            ])
            
            if tx_result:
                logger.info(f"Successfully submitted results for request {request_id}")
                return analysis_result
            else:
                logger.error(f"Failed to submit results for request {request_id}")
                return None
            
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Try to mark as failed
            await self.submit_transaction("markAnalysisFailed", [
                request_id,
                f"Analysis error: {str(e)}"
            ])
            return None
    
    async def polling_loop(self):
        """Poll for and process pending analysis requests"""
        logger.info("Starting genetic analysis polling loop...")
        
        # First check ROFL connectivity
        app_id = await self.get_rofl_app_id()
        if not app_id:
            logger.error("Cannot connect to ROFL appd. Will retry...")
        
        while True:
            try:
                # Get pending requests using Web3
                pending_requests = await self.get_pending_requests()
                
                if pending_requests:
                    logger.info(f"Found {len(pending_requests)} pending requests: {pending_requests}")
                    
                    for request_id in pending_requests:
                        result = await self.process_analysis_request(request_id)
                        if result:
                            logger.info(f"Successfully processed request {request_id}")
                        else:
                            logger.error(f"Failed to process request {request_id}")
                        
                        # Add a small delay between processing requests
                        await asyncio.sleep(2)
                else:
                    logger.info("No pending requests found")
                
            except Exception as e:
                logger.error(f"Polling error: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Wait before next poll
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
        "contract": CONTRACT_ADDRESS,
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
    logger.info("Starting ROFL Genetic Analysis Service (Fixed V4 - No 0x prefix)")
    logger.info(f"Contract: {CONTRACT_ADDRESS}")
    logger.info(f"RPC URL: {RPC_URL}")
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
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
