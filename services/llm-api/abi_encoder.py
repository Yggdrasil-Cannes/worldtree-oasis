#!/usr/bin/env python3
"""ABI encoding utilities for ROFL authenticated transactions."""

import json
from eth_abi import encode_abi
from eth_utils import function_signature_to_4byte_selector
import logging

logger = logging.getLogger(__name__)

# ABI for WorldtreeTest contract functions
WORLDTREE_TEST_ABI = {
    "getPendingRequests": {
        "signature": "getPendingRequests()",
        "inputs": [],
        "outputs": ["uint256[]"]
    },
    "getSNPDataForAnalysis": {
        "signature": "getSNPDataForAnalysis(uint256)",
        "inputs": ["uint256"],
        "outputs": ["string", "string"]
    },
    "submitAnalysisResult": {
        "signature": "submitAnalysisResult(uint256,string,uint256,string)",
        "inputs": ["uint256", "string", "uint256", "string"],
        "outputs": []
    },
    "markAnalysisFailed": {
        "signature": "markAnalysisFailed(uint256,string)",
        "inputs": ["uint256", "string"],
        "outputs": []
    }
}

def encode_function_call(function_name, args):
    """Encode a function call to ABI-encoded hex string."""
    if function_name not in WORLDTREE_TEST_ABI:
        raise ValueError(f"Unknown function: {function_name}")
    
    func_def = WORLDTREE_TEST_ABI[function_name]
    
    # Get function selector (first 4 bytes of keccak256 hash)
    selector = function_signature_to_4byte_selector(func_def["signature"]).hex()
    
    # Encode arguments
    if args:
        encoded_args = encode_abi(func_def["inputs"], args).hex()
        return "0x" + selector + encoded_args
    else:
        return "0x" + selector

def decode_function_result(function_name, data):
    """Decode ABI-encoded result from a function call."""
    if function_name not in WORLDTREE_TEST_ABI:
        raise ValueError(f"Unknown function: {function_name}")
    
    func_def = WORLDTREE_TEST_ABI[function_name]
    
    # Remove 0x prefix if present
    if data.startswith("0x"):
        data = data[2:]
    
    # Decode based on output types
    from eth_abi import decode_abi
    decoded = decode_abi(func_def["outputs"], bytes.fromhex(data))
    
    return decoded

# Test the encoding
if __name__ == "__main__":
    # Test getPendingRequests encoding
    print("getPendingRequests():", encode_function_call("getPendingRequests", []))
    
    # Test getSNPDataForAnalysis encoding
    print("getSNPDataForAnalysis(5):", encode_function_call("getSNPDataForAnalysis", [5]))
    
    # Test submitAnalysisResult encoding
    result_json = json.dumps({"confidence": 85, "relationship": "siblings"})
    print("submitAnalysisResult:", encode_function_call("submitAnalysisResult", [
        5,  # requestId
        result_json,  # result JSON
        85,  # confidence
        "siblings"  # relationship type
    ]))
