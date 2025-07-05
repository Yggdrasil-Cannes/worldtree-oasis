# Worldtree Genetic Analysis API

## Overview

The Worldtree ROFL app provides confidential genetic analysis using SNP (Single Nucleotide Polymorphism) data in a Trusted Execution Environment (TEE). It can determine genetic relationships between individuals using PCA analysis on SNP data.

## SNP Data Format

The API accepts SNP data in the standard format used by consumer genetic testing companies:

```
rs8628373 2738 2 AT
rs12345678 1234 1 GG
rs987654 5678 3 AC
...
```

Format: `<rsID> <position> <chromosome> <genotype>`
- **rsID**: Reference SNP cluster ID (e.g., rs8628373)
- **position**: Position identifier
- **chromosome**: Chromosome number (1-22, X, Y)
- **genotype**: Two-letter allele code (e.g., AT, GG, AC)

## API Endpoints

### 1. Genetic PCA Analysis

**Endpoint**: `POST /pca-analysis`

**Request**:
```json
{
  "user1_snps": [
    "rs8628373 2738 2 AT",
    "rs12345678 1234 1 GG",
    "rs987654 5678 3 AC",
    "... more SNPs ..."
  ],
  "user2_snps": [
    "rs8628373 2738 2 AA",
    "rs12345678 1234 1 GT",
    "rs987654 5678 3 AC",
    "... more SNPs ..."
  ],
  "n_components": 10,
  "user1_address": "0x123...",  // Optional - for blockchain integration
  "user2_address": "0x456..."   // Optional
}
```

**Response**:
```json
{
  "status": "success",
  "n_common_snps": 5234,
  "ibs_analysis": {
    "ibs0": 234,          // No alleles shared
    "ibs1": 1856,         // One allele shared
    "ibs2": 3144,         // Both alleles shared
    "total_snps": 5234,
    "ibs_score": 0.7234   // Identity-by-state score
  },
  "ibs2_percentage": 60.12,
  "relationship": "first cousins",
  "confidence": 0.80,
  "pca_distance": 2.34,
  "recommendations": [
    "Genetic match suggests cousin relationship",
    "Look for common grandparents or great-grandparents"
  ]
}
```

### 2. Family Reconnection Tips

**Endpoint**: `POST /genetic-tips`

**Request**:
```json
{
  "relationship": "first cousins",
  "context": "Found through genetic testing, living in different countries"
}
```

**Response**:
```json
{
  "status": "success",
  "tips": "Based on the first cousins relationship discovered through genetic testing..."
}
```

## Relationship Classifications

Based on IBS (Identity-By-State) analysis:

| Relationship | IBS Score | IBS2% | Confidence |
|--------------|-----------|-------|------------|
| Identical/Twin | >0.99 | >99% | 99% |
| Parent-Child | >0.85 | >85% | 95% |
| Full Siblings | >0.85 | >75% | 90% |
| Grandparent/Aunt/Uncle | >0.70 | >65% | 85% |
| First Cousins | >0.65 | >60% | 80% |
| Second Cousins | >0.60 | >55% | 70% |
| Third Cousins | >0.55 | >50% | 60% |
| Unrelated | <0.55 | <50% | 50% |

## Example Usage

### Python Example

```python
import requests
import json

# API endpoint (replace with actual ROFL endpoint)
API_URL = "http://rofl-endpoint/pca-analysis"

# Load SNP data (example format)
user1_snps = []
with open("user1_23andme.txt", "r") as f:
    for line in f:
        if not line.startswith("#") and line.strip():
            user1_snps.append(line.strip())

user2_snps = []
with open("user2_23andme.txt", "r") as f:
    for line in f:
        if not line.startswith("#") and line.strip():
            user2_snps.append(line.strip())

# Make request
response = requests.post(API_URL, json={
    "user1_snps": user1_snps[:10000],  # Use first 10k SNPs for testing
    "user2_snps": user2_snps[:10000],
    "n_components": 10
})

result = response.json()
print(f"Relationship: {result['relationship']}")
print(f"Confidence: {result['confidence']*100:.1f}%")
print(f"Common SNPs analyzed: {result['n_common_snps']}")
```

### JavaScript Example

```javascript
async function analyzeGeneticRelationship(user1File, user2File) {
  // Parse SNP files
  const user1Snps = user1File.split('\n')
    .filter(line => !line.startsWith('#') && line.trim())
    .slice(0, 10000);
    
  const user2Snps = user2File.split('\n')
    .filter(line => !line.startsWith('#') && line.trim())
    .slice(0, 10000);
  
  // Call API
  const response = await fetch('/pca-analysis', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      user1_snps: user1Snps,
      user2_snps: user2Snps,
      n_components: 10
    })
  });
  
  const result = await response.json();
  console.log(`Relationship: ${result.relationship}`);
  console.log(`Confidence: ${result.confidence * 100}%`);
}
```

## Privacy & Security

- All genetic data is processed inside a TEE (Trusted Execution Environment)
- No genetic data is stored permanently
- Results can optionally be recorded on blockchain with user consent
- Only aggregate statistics (relationship type, confidence) are returned

## Requirements

- Minimum 100 SNPs per user (recommended: 1000+ for accurate results)
- SNPs must be from the same reference genome (typically GRCh37/hg19)
- Common consumer genetic tests (23andMe, AncestryDNA, etc.) provide compatible data

## Integration with Worldtree Contract

When blockchain addresses are provided, matches are automatically submitted to the Worldtree smart contract for:
- Permanent relationship recording
- Bounty claiming for family connections
- Building verifiable family trees
