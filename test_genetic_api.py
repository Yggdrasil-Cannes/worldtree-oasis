#!/usr/bin/env python3
"""Test script for genetic analysis API with SNP data."""

import json

# Example SNP data (from 23andMe format)
# In production, you would read this from a file

user1_snps = [
    "rs8628373 2738 2 AT",
    "rs12345678 1234 1 GG",
    "rs987654 5678 3 AC",
    "rs11111111 9999 4 TT",
    "rs22222222 8888 5 CC",
    "rs33333333 7777 6 AG",
    "rs44444444 6666 7 GT",
    "rs55555555 5555 8 AA",
    "rs66666666 4444 9 CT",
    "rs77777777 3333 10 GC",
    # Add more SNPs here - minimum 100 recommended
]

user2_snps = [
    "rs8628373 2738 2 AA",  # Different from user1
    "rs12345678 1234 1 GT", # One allele shared
    "rs987654 5678 3 AC",   # Same as user1
    "rs11111111 9999 4 TT", # Same as user1
    "rs22222222 8888 5 CT", # One allele shared
    "rs33333333 7777 6 AG", # Same as user1
    "rs44444444 6666 7 TT", # Different from user1
    "rs55555555 5555 8 AC", # One allele shared
    "rs66666666 4444 9 CC", # One allele shared
    "rs77777777 3333 10 GC", # Same as user1
    # Add more SNPs here
]

# API request format
request_data = {
    "user1_snps": user1_snps,
    "user2_snps": user2_snps,
    "n_components": 10
}

print("API Request:")
print(json.dumps(request_data, indent=2))

print("\nExpected Response Format:")
response_example = {
    "status": "success",
    "n_common_snps": 10,
    "ibs_analysis": {
        "ibs0": 2,          # No alleles shared (e.g., AT vs AA)
        "ibs1": 4,          # One allele shared (e.g., GG vs GT)
        "ibs2": 4,          # Both alleles shared (e.g., AC vs AC)
        "total_snps": 10,
        "ibs_score": 0.65   # (4*2 + 4*1) / (10*2) = 0.6
    },
    "ibs2_percentage": 40.0,
    "relationship": "second cousins",
    "confidence": 0.70,
    "pca_distance": 2.34,
    "recommendations": [
        "Genetic match suggests cousin relationship",
        "Look for common grandparents or great-grandparents"
    ]
}

print(json.dumps(response_example, indent=2))

# How to read from actual 23andMe file
print("\n\nReading from 23andMe file:")
print("""
# Read SNP data from file
user1_snps = []
with open("genome_John_Doe_Full.txt", "r") as f:
    for line in f:
        line = line.strip()
        # Skip comments and empty lines
        if not line or line.startswith("#"):
            continue
        # Parse the line
        parts = line.split("\\t")  # Tab-separated
        if len(parts) >= 4:
            rsid = parts[0]
            chromosome = parts[1]
            position = parts[2]
            genotype = parts[3]
            # Format for API
            snp_line = f"{rsid} {position} {chromosome} {genotype}"
            user1_snps.append(snp_line)
""")
