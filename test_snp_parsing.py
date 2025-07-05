#!/usr/bin/env python3
"""Test SNP parsing to debug the issue"""

import sys
sys.path.append('/Users/pc/projects/worldtree/rofl/services/llm-api')

from snp_analyzer import SNPAnalyzer

# Test the parse_snp_data function
analyzer = SNPAnalyzer()

# Mock SNP data from main.py
mock_snp_1 = """rs123456 1234567 1 AA
rs789012 7890123 1 GG
rs345678 3456789 2 AT
rs901234 9012345 2 CC
rs567890 5678901 3 GT
rs234567 2345678 3 AC
rs890123 8901234 4 TT
rs456789 4567890 4 GG
rs012345 123456 5 CA
rs678901 6789012 5 AG"""

# Test 1: Parse as lines
print("Test 1: Parsing lines directly")
lines = mock_snp_1.strip().split('\n')
print(f"Number of lines: {len(lines)}")
parsed = analyzer.parse_snp_data(lines)
print(f"Parsed SNPs: {len(parsed)}")
if parsed:
    first_key = list(parsed.keys())[0]
    print(f"First SNP: {first_key} -> {parsed[first_key]}")

# Test 2: Debug line by line
print("\nTest 2: Debug line by line")
for i, line in enumerate(lines[:3]):
    print(f"Line {i}: '{line}'")
    parts = line.strip().split()
    print(f"  Parts: {parts} (length: {len(parts)})")
    if len(parts) >= 4:
        rsid, pos, chrom, gt = parts[:4]
        print(f"  Parsed: rsid={rsid}, pos={pos}, chrom={chrom}, gt={gt}")
