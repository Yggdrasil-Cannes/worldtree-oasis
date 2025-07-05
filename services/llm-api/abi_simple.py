#!/usr/bin/env python3
"""
Simple ABI encoder for WorldtreeTest contract functions.
This is a minimal implementation without external dependencies.
"""

def encode_uint256(value: int) -> str:
    """Encode a uint256 as 32 bytes hex string"""
    if value < 0 or value >= 2**256:
        raise ValueError(f"Value {value} out of range for uint256")
    return format(value, '064x')

def encode_string(s: str) -> tuple[str, str]:
    """
    Encode a string for Solidity ABI.
    Returns (offset_placeholder, encoded_data)
    """
    data = s.encode('utf-8')
    length = len(data)
    
    # Length (32 bytes)
    encoded_length = encode_uint256(length)
    
    # Data padded to 32-byte boundary
    hex_data = data.hex()
    padding_needed = (32 - (length % 32)) % 32
    padded_data = hex_data + '00' * padding_needed
    
    return encoded_length + padded_data

def encode_dynamic_params(static_parts: list[str], dynamic_parts: list[str]) -> str:
    """
    Encode parameters with dynamic types (strings).
    static_parts: list of 32-byte hex strings for static parameters
    dynamic_parts: list of encoded dynamic data
    """
    # Calculate offsets for dynamic data
    num_params = len(static_parts) + len([d for d in dynamic_parts if d is not None])
    base_offset = 32 * num_params  # After all parameter slots
    
    encoded = ""
    dynamic_data = ""
    current_offset = base_offset
    
    # Encode all parameters
    param_index = 0
    dynamic_index = 0
    
    for part in static_parts:
        if part == "DYNAMIC":
            # This is a placeholder for dynamic data offset
            encoded += encode_uint256(current_offset)
            dynamic_data += dynamic_parts[dynamic_index]
            current_offset += len(dynamic_parts[dynamic_index]) // 2  # hex to bytes
            dynamic_index += 1
        else:
            # Static parameter
            encoded += part
    
    return encoded + dynamic_data

def encode_submit_analysis_result(request_id: int, result_json: str, confidence: int, relationship: str) -> str:
    """
    Encode submitAnalysisResult(uint256,string,uint256,string)
    """
    # Function selector
    selector = "dae1ee1f"
    
    # Encode parameters
    # Layout: uint256, string (offset), uint256, string (offset), string data, string data
    
    # Static parts
    static_parts = [
        encode_uint256(request_id),      # uint256 requestId
        "DYNAMIC",                        # offset for result_json string
        encode_uint256(confidence),       # uint256 confidence  
        "DYNAMIC"                         # offset for relationship string
    ]
    
    # Dynamic parts
    result_encoded = encode_string(result_json)
    relationship_encoded = encode_string(relationship)
    dynamic_parts = [result_encoded, relationship_encoded]
    
    # Calculate actual offsets
    base_offset = 32 * 4  # 4 parameters * 32 bytes each = 128 bytes
    result_offset = base_offset
    relationship_offset = base_offset + len(result_encoded) // 2
    
    # Build the encoded data
    encoded = selector
    encoded += encode_uint256(request_id)
    encoded += encode_uint256(result_offset)
    encoded += encode_uint256(confidence)
    encoded += encode_uint256(relationship_offset)
    encoded += result_encoded
    encoded += relationship_encoded
    
    return encoded

def encode_mark_analysis_failed(request_id: int, reason: str) -> str:
    """
    Encode markAnalysisFailed(uint256,string)
    """
    # Function selector  
    selector = "89c4811c"
    
    # Layout: uint256, string (offset), string data
    base_offset = 32 * 2  # 2 parameters * 32 bytes each = 64 bytes
    
    reason_encoded = encode_string(reason)
    
    encoded = selector
    encoded += encode_uint256(request_id)
    encoded += encode_uint256(base_offset)
    encoded += reason_encoded
    
    return encoded

# Test the encoding
if __name__ == "__main__":
    print("Testing ABI encoding for WorldtreeTest contract")
    print("=" * 60)
    
    # Test submitAnalysisResult
    request_id = 1
    result_json = '{"status":"success","confidence":0.85,"relationship":"siblings"}'
    confidence = 85
    relationship = "siblings"
    
    encoded = encode_submit_analysis_result(request_id, result_json, confidence, relationship)
    
    print("submitAnalysisResult encoding:")
    print(f"  Request ID: {request_id}")
    print(f"  Result JSON: {result_json}")
    print(f"  Confidence: {confidence}")
    print(f"  Relationship: {relationship}")
    print(f"\nEncoded data:")
    print(f"  {encoded[:10]}... (selector + {len(encoded)-8} hex chars)")
    print(f"\nBreakdown:")
    print(f"  Selector: {encoded[:8]}")
    print(f"  Request ID: {encoded[8:72]}")
    print(f"  Result offset: {encoded[72:136]}")
    print(f"  Confidence: {encoded[136:200]}")
    print(f"  Relationship offset: {encoded[200:264]}")
    
    # Test markAnalysisFailed
    print("\n" + "-" * 60)
    print("markAnalysisFailed encoding:")
    request_id = 2
    reason = "Insufficient SNP data"
    
    encoded = encode_mark_analysis_failed(request_id, reason)
    
    print(f"  Request ID: {request_id}")
    print(f"  Reason: {reason}")
    print(f"\nEncoded data:")
    print(f"  {encoded[:10]}... (selector + {len(encoded)-8} hex chars)")
