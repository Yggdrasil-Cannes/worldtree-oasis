# Deployment Guide

## Prerequisites

1. **Oasis CLI** installed
2. **Funded account** with 100+ TEST tokens on Sapphire Testnet
3. **Docker** (optional, for local testing)

## Step 1: Create ROFL App

```bash
# List your accounts
oasis wallet list

# Create ROFL app on testnet
oasis rofl create --network testnet --account <your-account-name>
```

Save the returned app ID (e.g., `rofl1qpjsc3qplf2szw7w3rpzrpq5rqvzv4q5x5j23msu`).

## Step 2: Build ROFL Bundle

Since Docker might not be running locally, use the ROFL dev container:

```bash
docker run --platform linux/amd64 --rm -v .:/src -it ghcr.io/oasisprotocol/rofl-dev:main oasis rofl build
```

This creates a `.orc` bundle file.

## Step 3: Deploy

```bash
# Update on-chain configuration
oasis rofl update

# Deploy to ROFL marketplace
oasis rofl deploy
```

## Step 4: Monitor

```bash
# Check ROFL status
oasis rofl show

# View logs
oasis rofl machine logs

# Check machine status
oasis rofl machine show
```

## Testing After Deployment

Get the deployed URL from `oasis rofl machine show` and test:

```bash
# Update the URL in test script
python3 test_llm.py https://your-rofl-url
```

## Troubleshooting

- **Model download**: First boot takes time to download DeepSeek-R1:1.5b (1.1GB)
- **Service startup**: The API waits for Ollama to be ready (up to 2.5 minutes)
- **Logs**: Use `oasis rofl machine logs` to debug issues
