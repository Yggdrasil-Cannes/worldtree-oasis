# WorldTree - Family Connection Platform

A privacy-preserving family connection platform built on Oasis ROFL (Runtime Off-chain Logic) that helps people discover and verify family relationships through secure computation and local AI processing.

## Features

- **Privacy-First Design**: All sensitive data processing happens inside a Trusted Execution Environment (TEE)
- **Local LLM Analysis**: Uses Ollama to run AI models locally for analyzing family connections
- **Worldcoin Identity Verification**: Ensures unique human users through privacy-preserving identity proofs
- **Smart Contract Bounties**: Create and claim bounties for verified family connections
- **Zero-Knowledge Proofs**: Verify relationships without exposing private genetic or personal data
- **Encrypted Storage**: Family data stored encrypted on Walrus decentralized storage

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   ROFL TEE                          │
│  ┌─────────────┐        ┌─────────────────────┐    │
│  │   Ollama    │        │  Family Connector   │    │
│  │  (Local LLM)│◄──────►│     Service         │    │
│  └─────────────┘        └──────────┬──────────┘    │
│                                    │                │
│                         ┌──────────▼──────────┐    │
│                         │    ROFL App Daemon   │    │
│                         └──────────┬──────────┘    │
└────────────────────────────────────┼───────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  Sapphire Blockchain │
                          │  (FamilyBounty.sol)  │
                          └─────────────────────┘
```

## Prerequisites

- Oasis CLI installed
- Docker and Docker Compose
- Node.js and npm (for smart contract deployment)
- Funded Oasis Sapphire Testnet account (100+ TEST tokens)

## Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd worldtree/rofl
   ```

2. Copy environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

3. Install contract dependencies:
   ```bash
   cd contracts
   npm install
   cd ..
   ```

4. Create ROFL app on-chain:
   ```bash
   oasis rofl create --network testnet
   ```

5. Deploy the smart contract:
   ```bash
   cd contracts
   ROFL_APP_ID=<your-rofl-app-id> npx hardhat run scripts/deploy.js --network sapphire-testnet
   cd ..
   ```

6. Update CONTRACT_ADDRESS in your .env file with the deployed address

7. Build the ROFL bundle:
   ```bash
   oasis rofl build
   ```

8. Set secrets:
   ```bash
   echo -n "your-worldcoin-url" | oasis rofl secret set WORLDCOIN_VERIFY_URL -
   echo -n "your-walrus-key" | oasis rofl secret set WALRUS_API_KEY -
   echo -n "your-contract-address" | oasis rofl secret set CONTRACT_ADDRESS -
   ```

9. Update and deploy:
   ```bash
   oasis rofl update
   oasis rofl deploy
   ```

## Local Development

To test locally with Docker Compose:

```bash
export CONTRACT_ADDRESS=0x1234...
export WORLDCOIN_VERIFY_URL=https://...
export WALRUS_API_KEY=...

docker compose up --build
```

## API Endpoints

The Family Connector service exposes the following REST API:

- `GET /api/v1/health` - Health check
- `POST /api/v1/verify-identity` - Verify Worldcoin identity
- `POST /api/v1/analyze-connection` - Analyze potential family connection
- `POST /api/v1/submit-proof` - Submit verification proof
- `POST /api/v1/store-profile` - Store encrypted user profile
- `GET /api/v1/recommendations/{user_id}` - Get family recommendations

## Smart Contract Interface

The `FamilyBounty` contract provides:

- `createBounty(address relative, bytes metadata)` - Create a connection bounty
- `submitClaim(bytes32 connectionId, string evidence)` - Submit a claim
- `claimBounty(bytes32 connectionId)` - Claim verified bounty
- `getUserConnections(address user)` - Get user's connections

## Security Considerations

- All sensitive data processing happens inside the TEE
- Private keys are managed by ROFL's secure key management system
- User data is encrypted before storage
- Smart contract calls are authenticated through ROFL's subcall mechanism
- Local LLM ensures prompts with private data never leave the TEE

## Future Enhancements

- [ ] Integration with genetic testing services (with user consent)
- [ ] Multi-language support for global family connections
- [ ] Advanced matching algorithms using graph databases
- [ ] Integration with historical immigration databases
- [ ] Mobile app with secure enclave support

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## License

[License details here]
