#!/usr/bin/env python3
"""Generate test SNP data with enough entries for analysis"""

import random
import json

# Common SNP IDs and genotypes
rs_ids = [f"rs{i:08d}" for i in range(1, 501)]  # 500 SNPs
chromosomes = list(range(1, 23)) + ["X", "Y"]
genotypes = ["AA", "AT", "AC", "AG", "TT", "TC", "TG", "CC", "CG", "GG"]

def generate_snp_data(user_id, num_snps=200):
    """Generate SNP data for a user"""
    header = f"# Example SNP data for User {user_id} (subset of 23andMe format)\n# rsid\tchromosome\tposition\tgenotype\n"
    
    snps = []
    for i in range(num_snps):
        rs_id = rs_ids[i]
        chromosome = random.choice(chromosomes)
        position = random.randint(1000, 999999)
        genotype = random.choice(genotypes)
        snps.append(f"{rs_id}\t{chromosome}\t{position}\t{genotype}")
    
    return header + "\n".join(snps)

# Generate test data
user1_snp = generate_snp_data(1, 200)
user2_snp = generate_snp_data(2, 200)

# Create JSON test file
test_data = {
    "request_id": 123,
    "user1_snp": user1_snp,
    "user2_snp": user2_snp
}

with open("test_analyze_large.json", "w") as f:
    json.dump(test_data, f, indent=2)

print("Generated test_analyze_large.json with 200 SNPs per user") 