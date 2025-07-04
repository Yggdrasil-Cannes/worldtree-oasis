.PHONY: build test clean

# Build ROFL bundle
build:
	docker run --platform linux/amd64 --rm -v .:/src -it ghcr.io/oasisprotocol/rofl-dev:main oasis rofl build

# Test locally with Docker Compose  
test:
	podman-compose up --build

# Test API
test-api:
	python3 test_llm.py

# Clean up
clean:
	rm -f *.orc
	podman-compose down -v

# Show ROFL status
status:
	oasis rofl show

# Show machine logs
logs:
	oasis rofl machine logs
