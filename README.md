# DeepSeek LLM in TEE (ROFL)

A simple ROFL app that runs DeepSeek-R1:1.5b model inside a Trusted Execution Environment (TEE) with REST API access.

## Features

- **DeepSeek-R1:1.5b** running locally in TEE
- **REST API** for text generation and chat
- **Persistent storage** for model files
- **Secure execution** in Oasis ROFL environment

## API Endpoints

- `GET /health` - Health check
- `POST /generate` - Generate text from prompt
- `POST /chat` - Chat with message history  
- `GET /model` - Get model information

## Quick Start

1. **Create ROFL app:**
   ```bash
   oasis rofl create --network testnet --account <your-account>
   ```

2. **Build ROFL bundle:**
   ```bash
   docker run --platform linux/amd64 --rm -v .:/src -it ghcr.io/oasisprotocol/rofl-dev:main oasis rofl build
   ```

3. **Deploy:**
   ```bash
   oasis rofl update
   oasis rofl deploy
   ```

## Local Testing

```bash
# Test with Docker Compose (requires Docker)
podman-compose up --build

# Test API
python3 test_llm.py
```

## Example Usage

### Generate Text
```bash
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the meaning of life?"}'
```

### Chat
```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
```

## Architecture

- **TEE Type**: TDX containers
- **Model**: DeepSeek-R1:1.5b (1.1GB)
- **Storage**: Persistent at `/storage/ollama`
- **API**: REST on port 8080

## Security

- Runs inside Intel TDX Trusted Execution Environment
- Model weights stored in encrypted persistent storage
- API access authenticated via ROFL framework
