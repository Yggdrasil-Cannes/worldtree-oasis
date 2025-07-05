# WorldTree Genetic Analysis ROFL System

A privacy-preserving genetic analysis platform built on Oasis Sapphire using Runtime OFfLoad (ROFL) technology. This system enables secure genetic comparisons between users while keeping their raw genetic data completely private.

## 🧬 System Overview

The WorldTree system consists of:

1. **Smart Contract** (`WorldtreeTest.sol`) - Manages user registration and analysis requests
2. **ROFL Application** - Processes genetic analysis in a Trusted Execution Environment (TEE)
3. **Frontend Interface** - User registration and analysis request interface
4. **Hardhat Scripts** - Testing and deployment automation

### Key Features

- **Privacy-First**: Raw genetic data never leaves the TEE
- **Secure Processing**: Analysis runs in Intel TDX trusted environment
- **Blockchain Integration**: Results recorded on Oasis Sapphire
- **User-Friendly**: Simple registration and request workflow

## 🏗️ Architecture

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

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Docker Desktop
- Oasis CLI tools
- Git

### 1. Clone and Setup

```bash
git clone <repository-url>
cd worldtree-rofl
npm install
```

### 2. Environment Configuration

Create `.env` file in the `contracts/` directory:

```env
PRIVATE_KEY=your_private_key_here
SAPPHIRE_TESTNET_URL=https://testnet.sapphire.oasis.io
```

### 3. Deploy Smart Contract

```bash
cd contracts
npx hardhat run scripts/deploy.js --network sapphire-testnet
```

### 4. Build and Deploy ROFL App

```bash
# Build Docker image
docker buildx build --platform linux/amd64 -t cyama/worldtree-genetic-analysis:latest services/llm-api/ --push

# Update compose.yaml with new image hash
# Build ROFL bundle
docker run --platform linux/amd64 --rm -it -v .:/src -v ~/Library/Application\ Support/oasis:/root/.config/oasis ghcr.io/oasisprotocol/rofl-dev:main oasis rofl build

# Deploy to ROFL infrastructure
docker run --platform linux/amd64 --rm -it -v .:/src -v ~/Library/Application\ Support/oasis:/root/.config/oasis ghcr.io/oasisprotocol/rofl-dev:main oasis rofl deploy
```

## 📋 Current System Status

### ✅ **Working Components**

1. **Smart Contract Deployment**: Successfully deployed to Sapphire testnet
   - Contract Address: `0x614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3`
   - User registration: ✅ Working
   - Analysis requests: ✅ Working
   - Access control: ✅ Working (only ROFL can access SNP data)

2. **ROFL Infrastructure**: Successfully deployed and running
   - TEE Environment: ✅ Intel TDX active
   - Container Runtime: ✅ Running
   - Network: ✅ Configured
   - Storage: ✅ Persistent storage mounted

3. **Test Workflow**: Fully functional
   - User registration: ✅ 2 test users registered
   - Request submission: ✅ 3 analysis requests created
   - Contract monitoring: ✅ All requests visible and pending

### ⚠️ **Known Issues**

1. **Transaction Submission**: ROFL app encounters 422 errors when submitting results
   - **Root Cause**: Transaction format incompatibility with ROFL API
   - **Impact**: Analysis requests remain pending
   - **Status**: Identified, fix in progress

### 🧪 **Testing Results**

Last test run (2025-07-05 17:50:28):

```
=== User Registration ===
✅ User 1: 0x68aAB1F5175e7Fb1439c2F196b78aD57AF378740
✅ User 2: 0xbFbB95c74FaB7F9066711966CB50209176C37fFe

=== Analysis Requests ===
✅ Request 0: Submitted (pending processing)
✅ Request 1: Submitted (pending processing) 
✅ Request 2: Submitted (pending processing)

=== Security Verification ===
✅ SNP data access restricted to ROFL app only
✅ Regular users cannot access raw genetic data
```

## 🔧 Usage

### Register a User

```javascript
// Using Hardhat scripts
npx hardhat run scripts/test-genetic-workflow.js --network sapphire-testnet
```

### Monitor System

```javascript
// Check pending requests
npx hardhat run scripts/monitor-requests.js --network sapphire-testnet

// View ROFL logs
docker run --platform linux/amd64 --rm -it -v .:/src -v ~/Library/Application\ Support/oasis:/root/.config/oasis ghcr.io/oasisprotocol/rofl-dev:main oasis rofl machine logs
```

### Check ROFL Status

```bash
# View ROFL app status
docker run --platform linux/amd64 --rm -it -v .:/src -v ~/Library/Application\ Support/oasis:/root/.config/oasis ghcr.io/oasisprotocol/rofl-dev:main oasis rofl show

# View machine details
docker run --platform linux/amd64 --rm -it -v .:/src -v ~/Library/Application\ Support/oasis:/root/.config/oasis ghcr.io/oasisprotocol/rofl-dev:main oasis rofl machine show
```

## 📁 Project Structure

```
worldtree-rofl/
├── contracts/                 # Smart contracts and deployment scripts
│   ├── contracts/
│   │   └── WorldtreeTest.sol  # Main contract
│   ├── scripts/
│   │   ├── deploy.js          # Contract deployment
│   │   ├── test-genetic-workflow.js  # End-to-end testing
│   │   └── monitor-requests.js       # System monitoring
│   └── hardhat.config.js      # Hardhat configuration
├── services/
│   └── llm-api/               # ROFL application
│       ├── main.py            # Main application logic
│       ├── abi_encoder.py     # Contract interaction utilities
│       ├── Dockerfile         # Container definition
│       └── requirements.txt   # Python dependencies
├── compose.yaml               # ROFL deployment configuration
├── rofl.yaml                  # ROFL app manifest
└── README.md                  # This file
```

## 🔐 Security Features

### Privacy Protection
- **Encrypted Storage**: SNP data encrypted on-chain
- **TEE Processing**: Analysis runs in trusted environment
- **Access Control**: Only ROFL app can decrypt genetic data
- **Zero Knowledge**: Results published without revealing raw data

### Authentication
- **ROFL Origin Verification**: Contract validates ROFL app identity
- **User Signatures**: All requests cryptographically signed
- **Nonce Protection**: Prevents replay attacks

## 🧬 Genetic Analysis

The system performs genetic compatibility analysis by:

1. **SNP Comparison**: Analyzing Single Nucleotide Polymorphisms
2. **Compatibility Scoring**: Computing genetic compatibility metrics
3. **Privacy-Preserving Results**: Publishing scores without raw data

### Supported Analysis Types
- Genetic compatibility scoring
- Trait compatibility analysis
- Health risk factor comparison

## 📊 Performance Metrics

### Current Deployment
- **TEE Type**: Intel TDX
- **Memory**: 4096 MiB
- **vCPUs**: 2
- **Storage**: 20000 MiB
- **Network**: 10.0.2.15/24

### Transaction Costs
- User Registration: ~200,000 gas
- Analysis Request: ~200,886 gas
- Result Submission: ~300,000 gas (estimated)

## 🔄 Development Workflow

### Making Changes

1. **Update Contract**: Modify `contracts/WorldtreeTest.sol`
2. **Redeploy**: Run deployment script
3. **Update ROFL App**: Modify `services/llm-api/main.py`
4. **Rebuild Image**: Build and push new Docker image
5. **Update Deployment**: Update `compose.yaml` with new hash
6. **Redeploy ROFL**: Build and deploy new ROFL bundle

### Testing

```bash
# Run full test suite
cd contracts
npx hardhat run scripts/test-genetic-workflow.js --network sapphire-testnet

# Monitor system status
npx hardhat run scripts/monitor-requests.js --network sapphire-testnet
```

## 🚨 Troubleshooting

### Common Issues

1. **ROFL Deployment Fails**
   - Check Docker image architecture (must be linux/amd64)
   - Verify image SHA256 hash in compose.yaml
   - Ensure sufficient wallet balance for deployment

2. **Contract Interactions Fail**
   - Verify network configuration in hardhat.config.js
   - Check private key and wallet balance
   - Confirm contract address in environment

3. **TEE Environment Issues**
   - Monitor ROFL logs for initialization errors
   - Check Intel TDX availability
   - Verify container resource allocation

### Log Analysis

```bash
# View recent ROFL logs
docker run --platform linux/amd64 --rm -it -v .:/src -v ~/Library/Application\ Support/oasis:/root/.config/oasis ghcr.io/oasisprotocol/rofl-dev:main oasis rofl machine logs

# Check contract events
npx hardhat run scripts/monitor-requests.js --network sapphire-testnet
```

## 🔮 Future Enhancements

### Planned Features
- [ ] Advanced genetic analysis algorithms
- [ ] Multi-user family tree analysis
- [ ] Integration with genetic testing APIs
- [ ] Web-based user interface
- [ ] Mobile application
- [ ] Enhanced privacy features (ZK-SNARKs)

### Technical Improvements
- [ ] Fix ROFL transaction submission format
- [ ] Optimize gas usage
- [ ] Add comprehensive error handling
- [ ] Implement result caching
- [ ] Add analysis result verification

## 📚 Resources

- [Oasis ROFL Documentation](https://docs.oasis.io/rofl/)
- [Sapphire Network Guide](https://docs.oasis.io/sapphire/)
- [Intel TDX Overview](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions and support:
- Create an issue in this repository
- Join the Oasis Discord community
- Consult the documentation links above

---

**Status**: Development Phase - Core functionality implemented, transaction format fix in progress
**Last Updated**: July 5, 2025
**Version**: 1.0.0-beta
