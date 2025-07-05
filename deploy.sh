#!/bin/bash
# Deploy ROFL app to the marketplace

cd /Users/pc/projects/worldtree/rofl

echo "Deploying ROFL app..."
docker run --platform linux/amd64 --rm -it \
  -v .:/src \
  -v ~/Library/Application\ Support/oasis:/root/.config/oasis \
  ghcr.io/oasisprotocol/rofl-dev:main \
  oasis rofl deploy --offer 0000000000000003

echo "Deployment initiated. Check status with: oasis rofl machine show"
