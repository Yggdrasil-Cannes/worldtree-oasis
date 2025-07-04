# WorldTree ROFL App - Deployment Guide

## Overview

This guide walks you through deploying the WorldTree family connection platform on Oasis ROFL.

## Prerequisites

1. **Oasis CLI** installed and configured
2. **Docker** installed (for local testing)
3. **Node.js** and npm installed
4. **Funded Oasis account** with at least 110 TEST tokens

## Step-by-Step Deployment

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values (for local testing)
```

### 2. Install Dependencies

```bash
make install
```

### 3. Create ROFL App

```bash
# Create ROFL app on testnet
oasis rofl create --network testnet --account <your-account-name>
```

Save the returned ROFL app ID (e.g., `rofl1qqn9xndja7e2pnxhttktmecvwzz0yqwxsquqyxdf`)

### 4. Deploy Smart Contract

```bash
# Deploy FamilyBounty contract
ROFL_APP_ID=<your-rofl-app-id> make deploy
```

Save the deployed contract address from the output.

### 5. Configure Secrets

```bash
# Set contract address
echo -n "<deployed-contract-address>" | oasis rofl secret set CONTRACT_ADDRESS -

# Set Worldcoin verification URL
echo -n "https://developer.worldcoin.org/api/v1/verify" | oasis rofl secret set WORLDCOIN_VERIFY_URL -

# Set Walrus API key (when available)
echo -n "<your-walrus-api-key>" | oasis rofl secret set WALRUS_API_KEY -
```

### 6. Build ROFL Bundle

```bash
# Build the ROFL app
make build-rofl

# Update on-chain configuration
oasis rofl update
```

### 7. Deploy to ROFL Node

```bash
# Deploy to ROFL marketplace
oasis rofl deploy
```

### 8. Verify Deployment

```bash
# Check ROFL app status
oasis rofl show

# Check machine status
oasis rofl machine show

# View logs
oasis rofl machine logs
```

## Local Testing

Before deploying to ROFL, you can test locally:

```bash
# Start services locally
make local-test

# In another terminal, run API tests
make test
```

## Interacting with the Deployed App

Once deployed, your ROFL app exposes an API on port 8080. The ROFL node provider will give you access details.

### Example API Usage

```python
import httpx

# Health check
response = httpx.get("https://<rofl-node-url>/api/v1/health")

# Analyze connection
response = httpx.post(
    "https://<rofl-node-url>/api/v1/analyze-connection",
    json={
        "user_data": {...},
        "relative_data": {...}
    }
)
```

## Smart Contract Interaction

Use the deployed FamilyBounty contract to:

1. Create bounties for family connections
2. Submit claims with evidence
3. Verify connections through ROFL
4. Claim bounties for verified connections

Example using ethers.js:

```javascript
const contract = new ethers.Contract(contractAddress, FamilyBountyABI, signer);

// Create a bounty
await contract.createBounty(
    relativeAddress,
    ethers.utils.toUtf8Bytes("encrypted_metadata"),
    { value: ethers.utils.parseEther("1.0") }
);
```

## Troubleshooting

### ROFL daemon not found
- This is normal for local testing. The service runs in "mock mode" locally.

### Contract deployment fails
- Ensure your account has sufficient TEST tokens
- Verify the ROFL_APP_ID is set correctly

### ROFL deployment fails
- Check that you have at least 100 TEST tokens for registration
- Verify all secrets are set correctly
- Check `oasis rofl machine show` for machine status

## Security Considerations

1. **Never commit real secrets** to git
2. **Contract address** in .env is only for local testing
3. **All sensitive data** is processed inside the TEE
4. **LLM prompts** with private data never leave the TEE

## Next Steps

1. Integrate with frontend application
2. Set up monitoring and alerts
3. Implement additional verification methods
4. Add support for more languages
5. Integrate with genealogy databases

## Support

For issues or questions:
- Check the [Oasis documentation](https://docs.oasis.io)
- Join the [Oasis Discord](https://oasis.io/discord)
- Review the [ROFL troubleshooting guide](https://docs.oasis.io/rofl/troubleshooting)
