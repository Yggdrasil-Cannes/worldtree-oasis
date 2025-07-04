import os
import json
import asyncio
import httpx
from web3 import Web3
from eth_account import Account
import structlog
from typing import Dict, List, Optional
import hashlib
from cryptography.fernet import Fernet
from aiohttp import web

# Configure structured logging
logger = structlog.get_logger()

class ROFLClient:
    """Client for interacting with ROFL app daemon"""
    
    def __init__(self, socket_path="/run/rofl-appd.sock"):
        self.client = httpx.Client(
            transport=httpx.HTTPTransport(uds=socket_path),
            timeout=30.0
        )
        self.app_id = None
        self._init_app_id()
    
    def _init_app_id(self):
        """Initialize app ID from ROFL daemon"""
        try:
            response = self.client.get("http://localhost/rofl/v1/app/id")
            self.app_id = response.text.strip()
            logger.info("initialized_rofl_client", app_id=self.app_id)
        except Exception as e:
            logger.error("failed_to_get_app_id", error=str(e))
            raise
    
    def generate_key(self, key_id: str, kind: str = "secp256k1") -> str:
        """Generate a key using ROFL's key management"""
        response = self.client.post(
            "http://localhost/rofl/v1/keys/generate",
            json={"key_id": key_id, "kind": kind}
        )
        return response.json()["key"]
    
    def sign_and_submit_tx(self, tx_data: dict) -> dict:
        """Sign and submit transaction through ROFL"""
        response = self.client.post(
            "http://localhost/rofl/v1/tx/sign-submit",
            json={"tx": tx_data}
        )
        return response.json()


class FamilyConnectorService:
    """Main service for family connection platform"""
    
    def __init__(self):
        self.rofl = ROFLClient()
        self.contract_address = os.environ.get("CONTRACT_ADDRESS")
        self.ollama_host = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
        self.worldcoin_verify_url = os.environ.get("WORLDCOIN_VERIFY_URL")
        self.walrus_api_key = os.environ.get("WALRUS_API_KEY")
        
        # Initialize Web3 (for ABI encoding)
        self.w3 = Web3()
        
        # Load contract ABI
        self.contract_abi = self._load_contract_abi()
        
        logger.info("service_initialized", 
                   contract_address=self.contract_address,
                   rofl_app_id=self.rofl.app_id)
    
    def _load_contract_abi(self) -> dict:
        """Load contract ABI from artifacts"""
        # In production, this would load from compiled artifacts
        # For now, we'll define the essential parts
        return [
            {
                "name": "submitVerification",
                "type": "function",
                "inputs": [
                    {"name": "connectionId", "type": "bytes32"},
                    {"name": "zkProof", "type": "bytes32"},
                    {"name": "isGenetic", "type": "bool"}
                ],
                "outputs": []
            }
        ]
    
    async def verify_worldcoin_identity(self, proof: str, nullifier_hash: str) -> bool:
        """Verify Worldcoin identity proof"""
        if not self.worldcoin_verify_url:
            logger.warning("worldcoin_url_not_configured")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.worldcoin_verify_url,
                    json={
                        "proof": proof,
                        "nullifier_hash": nullifier_hash,
                        "action_id": "family-connection-verification"
                    }
                )
                result = response.json()
                return result.get("verified", False)
        except Exception as e:
            logger.error("worldcoin_verification_failed", error=str(e))
            return False
    
    async def analyze_family_connection(self, user_data: dict, relative_data: dict) -> dict:
        """Use local LLM to analyze potential family connections"""
        try:
            # Prepare privacy-preserving prompt
            prompt = self._prepare_analysis_prompt(user_data, relative_data)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=60.0
                )
                
                result = response.json()
                return {
                    "analysis": result.get("response", ""),
                    "confidence": self._extract_confidence(result.get("response", ""))
                }
        except Exception as e:
            logger.error("llm_analysis_failed", error=str(e))
            return {"analysis": "Analysis failed", "confidence": 0}
    
    def _prepare_analysis_prompt(self, user_data: dict, relative_data: dict) -> str:
        """Prepare privacy-preserving prompt for LLM analysis"""
        # Extract non-sensitive features
        return f"""
        Analyze potential family connection based on these anonymized features:
        
        Person A:
        - Region of origin: {user_data.get('region', 'Unknown')}
        - Approximate migration period: {user_data.get('migration_period', 'Unknown')}
        - Number of surname variations: {len(user_data.get('surname_variations', []))}
        - Known ancestral locations: {len(user_data.get('locations', []))}
        
        Person B:
        - Region of origin: {relative_data.get('region', 'Unknown')}
        - Approximate migration period: {relative_data.get('migration_period', 'Unknown')}
        - Surname similarity score: {relative_data.get('surname_similarity', 0)}
        
        Provide:
        1. Likelihood of family connection (0-100%)
        2. Suggested verification methods
        3. Common patterns that indicate relationship
        
        Be specific and practical in your recommendations.
        """
    
    def _extract_confidence(self, analysis: str) -> float:
        """Extract confidence score from LLM response"""
        # Simple extraction - in production, use better parsing
        import re
        match = re.search(r'(\d+)%', analysis)
        if match:
            return float(match.group(1)) / 100
        return 0.5
    
    async def submit_verification(self, connection_id: str, proof_data: dict) -> bool:
        """Submit verification to smart contract through ROFL"""
        try:
            # Prepare verification data
            zk_proof = self._generate_zk_proof(proof_data)
            is_genetic = proof_data.get("type") == "genetic"
            
            # Encode contract call
            contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=self.contract_abi
            )
            
            encoded_data = contract.encodeABI(
                fn_name="submitVerification",
                args=[
                    bytes.fromhex(connection_id),
                    bytes.fromhex(zk_proof),
                    is_genetic
                ]
            )
            
            # Submit through ROFL
            tx_data = {
                "kind": "eth",
                "data": {
                    "gas_limit": 200000,
                    "to": self.contract_address.replace("0x", ""),
                    "value": 0,
                    "data": encoded_data.hex().replace("0x", "")
                }
            }
            
            result = self.rofl.sign_and_submit_tx(tx_data)
            logger.info("verification_submitted", 
                       connection_id=connection_id,
                       tx_result=result)
            return True
            
        except Exception as e:
            logger.error("verification_submission_failed", 
                        error=str(e),
                        connection_id=connection_id)
            return False
    
    def _generate_zk_proof(self, proof_data: dict) -> str:
        """Generate zero-knowledge proof from verification data"""
        # In production, this would use proper ZK circuits
        # For now, we'll create a deterministic hash
        proof_string = json.dumps(proof_data, sort_keys=True)
        return hashlib.sha256(proof_string.encode()).hexdigest()
    
    async def store_encrypted_data(self, user_id: str, data: dict) -> str:
        """Store encrypted family data"""
        try:
            # Generate encryption key from ROFL KMS
            key_hex = self.rofl.generate_key(f"user_data_{user_id}", "raw-256")
            key = bytes.fromhex(key_hex)[:32]  # Use first 32 bytes for Fernet
            fernet_key = Fernet(key)
            
            # Encrypt data
            encrypted = fernet_key.encrypt(json.dumps(data).encode())
            
            # Store to Walrus (or mock storage for now)
            storage_key = f"family_data_{user_id}_{hashlib.sha256(encrypted).hexdigest()[:8]}"
            
            # In production, upload to Walrus
            logger.info("data_encrypted_and_stored", 
                       user_id=user_id,
                       storage_key=storage_key)
            
            return storage_key
            
        except Exception as e:
            logger.error("data_storage_failed", error=str(e))
            raise
    
    async def run_verification_loop(self):
        """Main loop for processing verification requests"""
        logger.info("starting_verification_loop")
        
        while True:
            try:
                # In production, this would listen to events or a queue
                # For now, we'll simulate with a sleep
                await asyncio.sleep(30)
                
                # Check for pending verifications
                # This would normally query the blockchain or a database
                logger.debug("checking_for_pending_verifications")
                
            except Exception as e:
                logger.error("verification_loop_error", error=str(e))
                await asyncio.sleep(5)


async def main():
    """Main entry point"""
    logger.info("starting_family_connector_service")
    
    # Verify required environment variables
    required_vars = ["CONTRACT_ADDRESS"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error("missing_required_environment_variables", vars=missing_vars)
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    # Initialize service
    service = FamilyConnectorService()
    
    # Import and initialize API
    from api import FamilyAPI
    api = FamilyAPI(service)
    
    # Run both API server and verification loop
    api_task = asyncio.create_task(
        web._run_app(api.app, host='0.0.0.0', port=8080)
    )
    verification_task = asyncio.create_task(
        service.run_verification_loop()
    )
    
    # Wait for both tasks
    await asyncio.gather(api_task, verification_task)


if __name__ == "__main__":
    asyncio.run(main())
