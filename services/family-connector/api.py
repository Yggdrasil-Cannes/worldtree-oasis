import os
import json
from typing import Dict, List, Optional
from aiohttp import web
import aiohttp_cors
from web3 import Web3
import structlog
from datetime import datetime

logger = structlog.get_logger()

class FamilyAPI:
    """REST API for family connection platform"""
    
    def __init__(self, connector_service):
        self.connector = connector_service
        self.app = web.Application()
        self.setup_routes()
        self.setup_cors()
    
    def setup_routes(self):
        """Setup API routes"""
        self.app.router.add_post('/api/v1/verify-identity', self.verify_identity)
        self.app.router.add_post('/api/v1/analyze-connection', self.analyze_connection)
        self.app.router.add_post('/api/v1/submit-proof', self.submit_proof)
        self.app.router.add_post('/api/v1/store-profile', self.store_profile)
        self.app.router.add_get('/api/v1/health', self.health_check)
        self.app.router.add_get('/api/v1/recommendations/{user_id}', self.get_recommendations)
    
    def setup_cors(self):
        """Setup CORS for browser access"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "rofl_app_id": self.connector.rofl.app_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def verify_identity(self, request):
        """Verify user identity with Worldcoin"""
        try:
            data = await request.json()
            proof = data.get("proof")
            nullifier_hash = data.get("nullifier_hash")
            
            if not proof or not nullifier_hash:
                return web.json_response(
                    {"error": "Missing proof or nullifier_hash"},
                    status=400
                )
            
            verified = await self.connector.verify_worldcoin_identity(
                proof, nullifier_hash
            )
            
            return web.json_response({
                "verified": verified,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error("identity_verification_error", error=str(e))
            return web.json_response(
                {"error": "Verification failed"},
                status=500
            )
    
    async def analyze_connection(self, request):
        """Analyze potential family connection"""
        try:
            data = await request.json()
            user_data = data.get("user_data", {})
            relative_data = data.get("relative_data", {})
            
            # Validate input
            if not user_data or not relative_data:
                return web.json_response(
                    {"error": "Missing user_data or relative_data"},
                    status=400
                )
            
            # Perform analysis
            result = await self.connector.analyze_family_connection(
                user_data, relative_data
            )
            
            return web.json_response({
                "analysis": result["analysis"],
                "confidence": result["confidence"],
                "recommendations": self._generate_recommendations(result),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error("connection_analysis_error", error=str(e))
            return web.json_response(
                {"error": "Analysis failed"},
                status=500
            )
    
    async def submit_proof(self, request):
        """Submit verification proof for a connection"""
        try:
            data = await request.json()
            connection_id = data.get("connection_id")
            proof_data = data.get("proof_data", {})
            
            if not connection_id:
                return web.json_response(
                    {"error": "Missing connection_id"},
                    status=400
                )
            
            # Submit verification
            success = await self.connector.submit_verification(
                connection_id, proof_data
            )
            
            return web.json_response({
                "success": success,
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error("proof_submission_error", error=str(e))
            return web.json_response(
                {"error": "Proof submission failed"},
                status=500
            )
    
    async def store_profile(self, request):
        """Store encrypted user profile"""
        try:
            data = await request.json()
            user_id = data.get("user_id")
            profile_data = data.get("profile", {})
            
            if not user_id or not profile_data:
                return web.json_response(
                    {"error": "Missing user_id or profile"},
                    status=400
                )
            
            # Store encrypted data
            storage_key = await self.connector.store_encrypted_data(
                user_id, profile_data
            )
            
            return web.json_response({
                "storage_key": storage_key,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error("profile_storage_error", error=str(e))
            return web.json_response(
                {"error": "Profile storage failed"},
                status=500
            )
    
    async def get_recommendations(self, request):
        """Get family connection recommendations for a user"""
        try:
            user_id = request.match_info['user_id']
            
            # In production, this would query stored profiles and find matches
            # For now, return mock recommendations
            recommendations = [
                {
                    "potential_relative_id": "user_123",
                    "confidence": 0.75,
                    "connection_type": "3rd cousin",
                    "common_ancestors": ["region:Eastern Europe", "period:1880-1920"],
                    "verification_methods": ["genetic", "document"]
                },
                {
                    "potential_relative_id": "user_456",
                    "confidence": 0.60,
                    "connection_type": "distant cousin",
                    "common_ancestors": ["surname:similar", "migration:same_ship"],
                    "verification_methods": ["document", "family_tree"]
                }
            ]
            
            return web.json_response({
                "user_id": user_id,
                "recommendations": recommendations,
                "total": len(recommendations),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error("recommendations_error", error=str(e))
            return web.json_response(
                {"error": "Failed to get recommendations"},
                status=500
            )
    
    def _generate_recommendations(self, analysis_result: dict) -> List[str]:
        """Generate actionable recommendations from analysis"""
        recommendations = []
        confidence = analysis_result.get("confidence", 0)
        
        if confidence > 0.7:
            recommendations.append("High likelihood of family connection - proceed with verification")
            recommendations.append("Consider genetic testing for definitive proof")
        elif confidence > 0.4:
            recommendations.append("Moderate likelihood - gather more information")
            recommendations.append("Check immigration records and ship manifests")
            recommendations.append("Compare family stories and oral histories")
        else:
            recommendations.append("Low likelihood based on current data")
            recommendations.append("Expand search to include surname variations")
            recommendations.append("Consider broader geographic regions")
        
        return recommendations
    
    def run(self, host='0.0.0.0', port=8080):
        """Run the API server"""
        logger.info("starting_api_server", host=host, port=port)
        web.run_app(self.app, host=host, port=port)


# Add aiohttp-cors to requirements
requirements_addition = """
# API framework
aiohttp-cors==0.7.0
"""
