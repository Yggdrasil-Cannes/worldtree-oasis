#!/usr/bin/env python3
"""
ROFL Genetic Analysis Service for WorldtreeTest Contract
Processes real genetic analysis requests from the blockchain
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

import aiohttp
import requests
from web3 import Web3

from abi_encoder import encode_function_call
from snp_analyzer import SNPAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WorldtreeGeneticAnalysisService:
    """ROFL service for processing genetic analysis requests from WorldtreeTest contract"""
    
    def __init__(self):
        self.contract_address = os.getenv("CONTRACT_ADDRESS", "0x614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3")
        self.rofl_socket = "/run/rofl-appd.sock"
        self.poll_interval = int(os.getenv("POLL_INTERVAL", "30"))  # seconds
        self.analyzer = SNPAnalyzer()
        
        # Contract ABI for WorldtreeTest
        self.contract_abi = [
            {
                "inputs": [{"type": "uint256", "name": "requestId"}],
                "name": "getSNPDataForAnalysis",
                "outputs": [
                    {"type": "string", "name": "user1SNP"},
                    {"type": "string", "name": "user2SNP"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getPendingRequests",
                "outputs": [{"type": "uint256[]", "name": ""}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"type": "uint256", "name": "requestId"},
                    {"type": "string", "name": "result"},
                    {"type": "uint256", "name": "confidence"},
                    {"type": "string", "name": "relationshipType"}
                ],
                "name": "submitAnalysisResult",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"type": "uint256", "name": "requestId"},
                    {"type": "string", "name": "reason"}
                ],
                "name": "markAnalysisFailed",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        logger.info("WorldtreeTest Genetic Analysis Service initialized")
        logger.info(f"Contract: {self.contract_address}")
        logger.info(f"ROFL Socket: {self.rofl_socket}")
        logger.info(f"Poll Interval: {self.poll_interval} seconds")

    async def get_rofl_app_id(self) -> str:
        """Get the ROFL app ID from the daemon"""
        try:
            connector = aiohttp.UnixConnector(path=self.rofl_socket)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get("http://localhost/rofl/v1/app/id") as response:
                    if response.status == 200:
                        app_id = await response.text()
                        logger.info(f"ROFL App ID: {app_id}")
                        return app_id.strip()
                    else:
                        logger.error(f"Failed to get app ID: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting ROFL app ID: {e}")
            return None

    async def get_pending_requests(self) -> List[int]:
        """Get pending analysis requests from the contract"""
        try:
            # Encode the function call
            encoded_call = encode_function_call(
                self.contract_abi,
                "getPendingRequests",
                []
            )
            
            # Make the call via ROFL daemon
            tx_data = {
                "tx": {
                    "kind": "eth",
                    "data": {
                        "gas_limit": 200000,
                        "to": self.contract_address,
                        "value": 0,
                        "data": encoded_call
                    }
                },
                "encrypt": False  # Read-only call
            }
            
            connector = aiohttp.UnixConnector(path=self.rofl_socket)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    "http://localhost/rofl/v1/tx/sign-submit",
                    json=tx_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Decode the result - this would be an array of uint256
                        # For now, we'll assume it returns properly formatted data
                        logger.info(f"Pending requests call result: {result}")
                        return []  # TODO: Properly decode the result
                    else:
                        logger.error(f"Failed to get pending requests: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting pending requests: {e}")
            return []

    async def get_snp_data(self, request_id: int) -> Optional[Tuple[str, str]]:
        """Get SNP data for a specific request"""
        try:
            # Encode the function call
            encoded_call = encode_function_call(
                self.contract_abi,
                "getSNPDataForAnalysis",
                [request_id]
            )
            
            # Make the call via ROFL daemon
            tx_data = {
                "tx": {
                    "kind": "eth",
                    "data": {
                        "gas_limit": 200000,
                        "to": self.contract_address,
                        "value": 0,
                        "data": encoded_call
                    }
                },
                "encrypt": False  # Read-only call
            }
            
            connector = aiohttp.UnixConnector(path=self.rofl_socket)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    "http://localhost/rofl/v1/tx/sign-submit",
                    json=tx_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"SNP data call result: {result}")
                        # TODO: Properly decode the result
                        return None, None
                    else:
                        logger.error(f"Failed to get SNP data: {response.status}")
                        return None, None
        except Exception as e:
            logger.error(f"Error getting SNP data: {e}")
            return None, None

    async def submit_analysis_result(self, request_id: int, result: Dict, confidence: int, relationship_type: str):
        """Submit analysis result to the contract"""
        try:
            # Encode the function call
            encoded_call = encode_function_call(
                self.contract_abi,
                "submitAnalysisResult",
                [request_id, json.dumps(result), confidence, relationship_type]
            )
            
            # Submit via ROFL daemon
            tx_data = {
                "tx": {
                    "kind": "eth",
                    "data": {
                        "gas_limit": 300000,
                        "to": self.contract_address,
                        "value": 0,
                        "data": encoded_call
                    }
                }
            }
            
            connector = aiohttp.UnixConnector(path=self.rofl_socket)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    "http://localhost/rofl/v1/tx/sign-submit",
                    json=tx_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Analysis result submitted: {result}")
                        return True
                    else:
                        logger.error(f"Failed to submit analysis result: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error submitting analysis result: {e}")
            return False

    async def mark_analysis_failed(self, request_id: int, reason: str):
        """Mark analysis as failed"""
        try:
            # Encode the function call
            encoded_call = encode_function_call(
                self.contract_abi,
                "markAnalysisFailed",
                [request_id, reason]
            )
            
            # Submit via ROFL daemon
            tx_data = {
                "tx": {
                    "kind": "eth",
                    "data": {
                        "gas_limit": 200000,
                        "to": self.contract_address,
                        "value": 0,
                        "data": encoded_call
                    }
                }
            }
            
            connector = aiohttp.UnixConnector(path=self.rofl_socket)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    "http://localhost/rofl/v1/tx/sign-submit",
                    json=tx_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Analysis marked as failed: {result}")
                        return True
                    else:
                        logger.error(f"Failed to mark analysis as failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error marking analysis as failed: {e}")
            return False

    async def process_request(self, request_id: int):
        """Process a single genetic analysis request"""
        logger.info(f"Processing genetic analysis request {request_id}")
        
        try:
            # Get SNP data for the request
            user1_snp, user2_snp = await self.get_snp_data(request_id)
            
            if not user1_snp or not user2_snp:
                logger.error(f"Could not retrieve SNP data for request {request_id}")
                await self.mark_analysis_failed(request_id, "Could not retrieve SNP data")
                return
            
            logger.info(f"Retrieved SNP data for request {request_id}")
            logger.info(f"User 1 SNPs: {len(user1_snp.split()) if user1_snp else 0}")
            logger.info(f"User 2 SNPs: {len(user2_snp.split()) if user2_snp else 0}")
            
            # Perform genetic analysis
            analysis_result = self.analyzer.analyze_relationship(user1_snp, user2_snp)
            
            if analysis_result:
                logger.info(f"Analysis complete for request {request_id}:")
                logger.info(f"  Relationship: {analysis_result['relationship']}")
                logger.info(f"  Confidence: {analysis_result['confidence']}%")
                logger.info(f"  Common SNPs: {analysis_result['common_snps']}")
                logger.info(f"  IBS2 percentage: {analysis_result['ibs2_percentage']:.2f}%")
                logger.info(f"  PCA distance: {analysis_result['pca_distance']}")
                
                # Submit result to contract
                await self.submit_analysis_result(
                    request_id,
                    analysis_result,
                    analysis_result['confidence'],
                    analysis_result['relationship']
                )
            else:
                logger.error(f"Analysis failed for request {request_id}")
                await self.mark_analysis_failed(request_id, "Analysis computation failed")
                
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}")
            await self.mark_analysis_failed(request_id, f"Processing error: {str(e)}")

    async def polling_loop(self):
        """Main polling loop to check for new requests"""
        logger.info("Starting genetic analysis polling loop...")
        
        while True:
            try:
                # Get pending requests
                pending_requests = await self.get_pending_requests()
                
                if pending_requests:
                    logger.info(f"Found {len(pending_requests)} pending requests")
                    
                    for request_id in pending_requests:
                        await self.process_request(request_id)
                else:
                    logger.info("No pending requests found")
                
                logger.info("Polling cycle complete. Waiting...")
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(self.poll_interval)

    async def run(self):
        """Run the ROFL service"""
        logger.info("============================================================")
        logger.info("Starting ROFL Genetic Analysis Service for WorldtreeTest")
        logger.info(f"Contract: {self.contract_address}")
        logger.info(f"ROFL Socket: {self.rofl_socket}")
        logger.info(f"Poll Interval: {self.poll_interval} seconds")
        logger.info("============================================================")
        
        # Get ROFL app ID
        app_id = await self.get_rofl_app_id()
        if not app_id:
            logger.error("Failed to get ROFL app ID")
            return
        
        # Start polling loop
        await self.polling_loop()

async def main():
    """Main entry point"""
    service = WorldtreeGeneticAnalysisService()
    await service.run()

if __name__ == "__main__":
    asyncio.run(main())
