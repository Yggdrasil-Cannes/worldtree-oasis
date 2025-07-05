#!/usr/bin/env python3
"""Compute Ethereum function selectors for WorldtreeTest contract"""

try:
    # Try pycryptodome first
    from Crypto.Hash import keccak
    
    def compute_selector(signature):
        """Compute the 4-byte function selector from signature"""
        k = keccak.new(digest_bits=256)
        k.update(signature.encode('utf-8'))
        return '0x' + k.hexdigest()[:8]
except ImportError:
    # Fallback to hashlib if available
    import hashlib
    
    def compute_selector(signature):
        """Compute the 4-byte function selector from signature"""
        if hasattr(hashlib, 'sha3_256'):
            # This is actually Keccak-256 in older Python versions
            h = hashlib.sha3_256(signature.encode('utf-8'))
            return '0x' + h.hexdigest()[:8]
        else:
            raise ImportError("No keccak256 implementation available")

# WorldtreeTest contract function signatures
FUNCTION_SIGNATURES = {
    "submitAnalysisResult": "submitAnalysisResult(uint256,string,uint256,string)",
    "markAnalysisFailed": "markAnalysisFailed(uint256,string)",
    "getSNPDataForAnalysis": "getSNPDataForAnalysis(uint256)",
    "getPendingRequests": "getPendingRequests()"
}

if __name__ == "__main__":
    print("WorldtreeTest Function Selectors:")
    print("-" * 50)
    
    for name, signature in FUNCTION_SIGNATURES.items():
        selector = compute_selector(signature)
        print(f"{name}:")
        print(f"  Signature: {signature}")
        print(f"  Selector:  {selector}")
        print()
