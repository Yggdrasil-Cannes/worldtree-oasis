#!/usr/bin/env python3
"""
Example client for testing the WorldTree Family Connection API
"""

import asyncio
import httpx
import json
from datetime import datetime

# API base URL
API_BASE_URL = "http://localhost:8080/api/v1"

async def test_health_check():
    """Test health check endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/health")
        print("Health Check Response:")
        print(json.dumps(response.json(), indent=2))
        print("-" * 50)

async def test_analyze_connection():
    """Test family connection analysis"""
    # Example user data (anonymized features)
    user_data = {
        "region": "Eastern Europe",
        "migration_period": "1880-1920",
        "surname_variations": ["Smith", "Schmidt", "Smythe"],
        "locations": ["Poland", "Germany", "Ellis Island", "New York"]
    }
    
    relative_data = {
        "region": "Eastern Europe",
        "migration_period": "1890-1910",
        "surname_similarity": 0.85
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/analyze-connection",
            json={
                "user_data": user_data,
                "relative_data": relative_data
            }
        )
        print("Connection Analysis Response:")
        print(json.dumps(response.json(), indent=2))
        print("-" * 50)

async def test_store_profile():
    """Test profile storage"""
    profile_data = {
        "user_id": "test_user_123",
        "profile": {
            "birth_year_range": "1950-1960",
            "known_regions": ["Eastern Europe", "United States"],
            "family_stories": ["Immigration through Ellis Island", "Surname changed at border"],
            "genetic_markers": "encrypted_genetic_data_here"
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/store-profile",
            json=profile_data
        )
        print("Profile Storage Response:")
        print(json.dumps(response.json(), indent=2))
        print("-" * 50)

async def test_submit_proof():
    """Test proof submission"""
    proof_data = {
        "connection_id": "abcdef1234567890" * 4,  # 64 char hex string
        "proof_data": {
            "type": "document",  # or "genetic"
            "evidence": "Immigration records match",
            "confidence": 0.85,
            "verified_by": "test_system"
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/submit-proof",
            json=proof_data
        )
        print("Proof Submission Response:")
        print(json.dumps(response.json(), indent=2))
        print("-" * 50)

async def test_get_recommendations():
    """Test getting recommendations"""
    user_id = "test_user_123"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/recommendations/{user_id}")
        print("Recommendations Response:")
        print(json.dumps(response.json(), indent=2))
        print("-" * 50)

async def main():
    """Run all tests"""
    print("=" * 50)
    print("WorldTree API Test Client")
    print(f"Testing API at: {API_BASE_URL}")
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 50)
    print()
    
    # Run tests
    await test_health_check()
    await test_analyze_connection()
    await test_store_profile()
    await test_get_recommendations()
    
    # Note: Submit proof will fail without a real connection ID
    # await test_submit_proof()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
