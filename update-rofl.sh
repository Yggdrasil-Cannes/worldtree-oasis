#!/bin/bash
# Script to update ROFL service with new contract address

echo "Updating ROFL service with new WorldtreeBackend contract..."
echo "New contract address: 0xBc1437ae87B8111dC89e794eb6dD4B303901aCC1"

# Build new Docker image with updated contract
echo "Building new Docker image..."
docker buildx build --platform linux/amd64 \
  -f services/llm-api/Dockerfile.worldtree \
  -t cyama/worldtree-genetic-analysis:backend-v1 \
  --push \
  services/llm-api/

# Update compose.yaml to use new image
sed -i.bak 's/fixed-v7/backend-v1/g' compose.yaml

# Build ROFL bundle
echo "Building ROFL bundle..."
docker run --platform linux/amd64 \
  --volume $(pwd):/src \
  ghcr.io/oasisprotocol/rofl-dev:main \
  oasis rofl build

echo "ROFL bundle built successfully!"
echo ""
echo "Next steps:"
echo "1. Run: docker run --platform linux/amd64 --rm -it -v $(pwd):/src -v ~/Library/Application\ Support/oasis:/root/.config/oasis ghcr.io/oasisprotocol/rofl-dev:main oasis rofl update"
echo "   (Enter passphrase: rofl123 when prompted)"
echo ""
echo "2. Monitor logs with:"
echo "   docker run --platform linux/amd64 --rm -it -v $(pwd):/src -v ~/Library/Application\ Support/oasis:/root/.config/oasis ghcr.io/oasisprotocol/rofl-dev:main oasis rofl machine logs"