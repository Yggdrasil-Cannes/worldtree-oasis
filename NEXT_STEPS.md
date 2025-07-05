# Next Steps - ROFL Worldtree Deployment

## Immediate Actions Required

### 1. Complete ROFL Update (Manual Step)
```bash
cd /Users/pc/projects/worldtree/rofl
docker run --platform linux/amd64 --rm -it \
  -v .:/src \
  -v ~/Library/Application\ Support/oasis:/root/.config/oasis \
  ghcr.io/oasisprotocol/rofl-dev:main \
  oasis rofl update
```
**When prompted**: Enter your passphrase and select "Yes" to sign the transaction

### 2. Deploy ROFL
```bash
docker run --platform linux/amd64 --rm -it \
  -v .:/src \
  -v ~/Library/Application\ Support/oasis:/root/.config/oasis \
  ghcr.io/oasisprotocol/rofl-dev:main \
  oasis rofl deploy
```

### 3. Monitor Deployment
```bash
docker run --platform linux/amd64 --rm -it \
  -v .:/src \
  -v ~/Library/Application\ Support/oasis:/root/.config/oasis \
  ghcr.io/oasisprotocol/rofl-dev:main \
  oasis rofl machine logs
```

### 4. Test the System
```bash
cd /Users/pc/projects/worldtree/rofl/contracts
npx hardhat run scripts/check-state.js --network sapphire-testnet
```

## What's Ready

✅ WorldtreeTest contract deployed: `0xa4e5c09C101A62Aa04A1078228527CD106012d0b`
✅ Docker image ready: `cyama/llm-api:worldtree-test`
✅ ROFL bundle built with genetic analysis
✅ Test scripts prepared

## What Will Happen

Once deployed, the ROFL app will:
- Poll for genetic analysis requests every 30 seconds
- Process SNP data using PCA analysis
- Identify relationships (twins, siblings, cousins, etc.)
- Submit results back to the blockchain

## If Issues Arise

1. Check ROFL logs for errors
2. Verify contract has pending requests
3. Look for "Error calling getPendingRequests" - indicates view function issue
4. If view functions fail, implement the authenticated transaction approach documented in the handoff

The system is ready - only the manual passphrase entry stands between current state and operational genetic analysis.
