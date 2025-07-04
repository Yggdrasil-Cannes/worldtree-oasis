.PHONY: help install compile deploy test clean local-test build-rofl

# Default target
help:
	@echo "WorldTree ROFL App - Available Commands:"
	@echo ""
	@echo "  make install        - Install contract dependencies"
	@echo "  make compile        - Compile smart contracts"
	@echo "  make deploy         - Deploy contracts to Sapphire Testnet"
	@echo "  make test           - Run API tests"
	@echo "  make local-test     - Run services locally with Docker Compose"
	@echo "  make build-rofl     - Build ROFL bundle"
	@echo "  make clean          - Clean build artifacts"

# Install dependencies
install:
	cd contracts && npm install

# Compile contracts
compile:
	cd contracts && npx hardhat compile

# Deploy to Sapphire Testnet
deploy: compile
	@echo "Deploying FamilyBounty contract..."
	@if [ -z "$(ROFL_APP_ID)" ]; then \
		echo "Error: ROFL_APP_ID is not set"; \
		exit 1; \
	fi
	cd contracts && ROFL_APP_ID=$(ROFL_APP_ID) npx hardhat run scripts/deploy.js --network sapphire-testnet

# Local testing with Docker Compose
local-test:
	@if [ ! -f .env ]; then \
		echo "Creating .env file from example..."; \
		cp .env.example .env; \
	fi
	docker compose up --build

# Build ROFL bundle
build-rofl:
	oasis rofl build

# Run API tests
test:
	python3 test_api.py

# Clean build artifacts
clean:
	rm -rf contracts/artifacts contracts/cache contracts/typechain-types
	rm -f *.orc
	docker compose down -v
