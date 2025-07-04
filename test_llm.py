#!/usr/bin/env python3
"""Test the LLM API."""

import requests
import json
import sys

# API base URL - update this after deployment
API_BASE_URL = "http://localhost:8080"

def test_health():
    """Test health endpoint."""
    print("Testing health check...")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_generate():
    """Test generation endpoint."""
    print("Testing text generation...")
    response = requests.post(
        f"{API_BASE_URL}/generate",
        json={
            "prompt": "What is the capital of France? Answer in one sentence."
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {result.get('response', 'No response')}")
    else:
        print(f"Error: {response.text}")
    print()

def test_chat():
    """Test chat endpoint."""
    print("Testing chat...")
    response = requests.post(
        f"{API_BASE_URL}/chat",
        json={
            "messages": [
                {"role": "user", "content": "Hi! Can you solve 2+2?"},
            ]
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        message = result.get('message', {})
        print(f"Response: {message.get('content', 'No response')}")
    else:
        print(f"Error: {response.text}")
    print()

def test_model_info():
    """Test model info endpoint."""
    print("Testing model info...")
    response = requests.get(f"{API_BASE_URL}/model")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

if __name__ == "__main__":
    print("=== LLM API Test ===\n")
    
    if len(sys.argv) > 1:
        API_BASE_URL = sys.argv[1]
        print(f"Using API URL: {API_BASE_URL}\n")
    
    try:
        test_health()
        test_generate()
        test_chat()
        test_model_info()
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to API at {API_BASE_URL}")
        print("Make sure the service is running.")
    except Exception as e:
        print(f"Error: {e}")
