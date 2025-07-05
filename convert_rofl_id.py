#!/usr/bin/env python3
"""Convert ROFL app ID (bech32) to Ethereum address format."""

import sys

def bech32_decode(bech_str):
    """Decode a bech32 string."""
    charset = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
    
    # Find the separator
    sep = bech_str.rfind('1')
    if sep < 0:
        raise ValueError("No separator found")
    
    hrp = bech_str[:sep]
    data = bech_str[sep+1:]
    
    # Convert characters to values
    values = []
    for char in data:
        idx = charset.find(char)
        if idx < 0:
            raise ValueError(f"Invalid character: {char}")
        values.append(idx)
    
    # Convert from 5-bit to 8-bit
    bits = 0
    value = 0
    output = []
    for v in values[:-6]:  # Skip checksum
        value = (value << 5) | v
        bits += 5
        while bits >= 8:
            bits -= 8
            output.append((value >> bits) & 0xff)
    
    return hrp, bytes(output)

def rofl_id_to_eth_address(rofl_id):
    """Convert ROFL app ID to Ethereum address format."""
    hrp, data = bech32_decode(rofl_id)
    if hrp != "rofl":
        raise ValueError(f"Expected 'rofl' prefix, got '{hrp}'")
    
    # Convert to hex
    eth_address = "0x" + data.hex()
    return eth_address

if __name__ == "__main__":
    rofl_id = "rofl1qq9vdpxduln5utg3htkhvzwhvhdnzttylunuy6wm"
    try:
        eth_address = rofl_id_to_eth_address(rofl_id)
        print(f"ROFL App ID: {rofl_id}")
        print(f"Ethereum Address: {eth_address}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
