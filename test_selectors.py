#!/usr/bin/env python3
"""Test function selector computation"""

# First, let's test if we can compute them locally
import sys
sys.path.append('/Users/pc/projects/worldtree/rofl/services/llm-api')

from compute_selectors import compute_selector, FUNCTION_SIGNATURES

print("Testing function selector computation...")
print("=" * 60)

for name, signature in FUNCTION_SIGNATURES.items():
    selector = compute_selector(signature)
    print(f"{name}:")
    print(f"  Signature: {signature}")
    print(f"  Selector:  {selector}")
    print()

# Also test the specific encoding for submitAnalysisResult
print("\nTest encoding for submitAnalysisResult:")
print("-" * 60)

# The actual function parameters
request_id = 1
result_json = '{"status":"success","confidence":0.85}'
confidence = 85
relationship = "siblings"

print(f"Request ID: {request_id}")
print(f"Result JSON: {result_json}")
print(f"Confidence: {confidence}")
print(f"Relationship: {relationship}")

# In proper ABI encoding, we would need:
# 1. Function selector (4 bytes)
# 2. uint256 request_id (32 bytes)
# 3. Offset to string result_json (32 bytes)
# 4. uint256 confidence (32 bytes)
# 5. Offset to string relationship (32 bytes)
# 6. Length of result_json + padded data
# 7. Length of relationship + padded data

print("\nNote: Proper ABI encoding is complex and requires:")
print("- Dynamic offsets for strings")
print("- Proper padding to 32-byte boundaries")
print("- Correct ordering of static and dynamic data")
