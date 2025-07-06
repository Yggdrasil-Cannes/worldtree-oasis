# WorldTree ROFL Genetic Analysis

Privacy-preserving genetic analysis on Oasis Sapphire using Runtime Off-chain Logic (ROFL) in Trusted Execution Environments.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Client   │───▶│  Smart Contract  │───▶│   ROFL App      │
│                 │    │  (Sapphire)      │    │   (TEE)         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │                        │
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Register w/ SNP │    │ Store Encrypted  │    │ Process Analysis│
│ Submit Requests │    │ Data & Requests  │    │ Submit Results  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Components

**Smart Contracts** (`/contracts/contracts/`)
- `WorldtreeBackend.sol` - Stores SNP data hashes and manages analysis requests
- `WorldtreeTest.sol` - Direct SNP data storage for testing
- Backend address: `0xBc1437ae87B8111dC89e794eb6dD4B303901aCC1`

**ROFL Service** (`/services/llm-api/`)
- `main.py` - Polls blockchain for pending analyses, performs PCA-based genetic similarity
- `snp_analyzer.py` - SNP data processing and similarity calculations
- `abi_encoder.py` - Ethereum ABI encoding for ROFL transactions
- Runs DeepSeek-R1:1.5b via Ollama for potential LLM features

**Integration**
- ROFL polls smart contract every 30 seconds for pending requests
- Retrieves encrypted SNP data for both users
- Calculates genetic similarity using PCA
- Submits results via ROFL's authenticated transaction API

### Data Flow

1. **Registration**: Users upload SNP data hash to `WorldtreeBackend.sol`
   - Raw genetic data never leaves user's device
   - Only SHA-256 hash stored on-chain
   - User gets derived address for privacy

2. **Analysis Request**: User A calls `requestAnalysisFor(userA, userB)`
   - Creates pending request on-chain
   - Emits `AnalysisRequested` event
   - Request ID generated for tracking

3. **Consent**: User B calls `grantConsentFor(userB, requestId, method, key)`
   - Marks request as consented
   - Provides decryption key if using encrypted storage
   - Triggers ROFL processing

4. **ROFL Processing**: TEE polls for consented requests every 30s
   - Retrieves encrypted SNP data for both users
   - Decrypts data inside secure enclave
   - Runs PCA-based genetic similarity analysis
   - Calculates relationship probability

5. **Result Submission**: ROFL calls `submitAnalysisResult(requestId, similarity)`
   - Posts similarity score on-chain
   - Emits `AnalysisComplete` event
   - Raw genetic data remains private

## Setup

### Prerequisites
- Docker (linux/amd64 support)
- Oasis CLI tools
- Node.js 18+

### Deploy Contract
```bash
cd contracts
npm install
npx hardhat run scripts/deploy-worldtree-backend.js --network sapphire-testnet
```

### Build and Deploy ROFL

```bash
# Build Docker image - must be linux/amd64
docker buildx build --platform linux/amd64 -t your-registry/worldtree-genetic-analysis:backend-v2 services/llm-api/ --push

# Update compose.yaml with image SHA256 hash from push output
# Important: Use the full SHA256 digest, not the tag

# Build ROFL bundle
docker run --platform linux/amd64 --rm -it \
  -v .:/src \
  -v ~/Library/Application\ Support/oasis:/root/.config/oasis \
  ghcr.io/oasisprotocol/rofl-dev:main \
  oasis rofl build

# Deploy ROFL
oasis rofl deploy
```

### Docker Command Nuances
- **Platform**: Always use `--platform linux/amd64` even on ARM Macs
- **Volume Mounts**: The oasis config path varies by OS
  - macOS: `~/Library/Application\ Support/oasis`
  - Linux: `~/.config/oasis`
- **Image Hash**: compose.yaml requires the SHA256 digest, not the tag

## Testing

```bash
cd contracts

# Check contract state
npx hardhat run scripts/check-state.js --network sapphire-testnet

# Test registration and analysis
npx hardhat run scripts/test-e2e-integration.js --network sapphire-testnet

# Monitor ROFL logs
oasis rofl logs
```

## Current Status

- Contract deployed and functional
- ROFL app running in Intel TDX
- Genetic analysis uses PCA for similarity scoring
- Integration with WLDTree-miniapp frontend complete

### Similarity Thresholds
- Parent/Child: >50%
- Siblings: 40-50%
- First Cousins: 12.5-25%
- Second Cousins: 3-12.5%

## Troubleshooting

**ROFL Build Fails**
- Ensure Docker image is linux/amd64
- Check compose.yaml has correct SHA256 hash
- Verify rofl.yaml points to correct contract

**Contract Errors**
- Confirm contract address in environment
- Check wallet has sufficient TEST tokens
- Verify ROFL app is authorized on contract

**Analysis Not Processing**
- Check `oasis rofl logs` for polling activity
- Ensure both users have consented
- Verify SNP data format is correct