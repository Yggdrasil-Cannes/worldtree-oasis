# LLMBridge Contract Integration

## Contract Details

- **Contract Address**: `0x32f22B267Be8CD47FAF93Bcd1CC31059bdc24FD2`
- **Network**: Sapphire Testnet
- **Authorized ROFL App**: `rofl1qq9vdpxduln5utg3htkhvzwhvhdnzttylunuy6wm`

## How it Works

The LLMBridge contract enables external users to interact with the LLM running inside the ROFL TEE:

1. **Users submit requests** by calling `createRequest(prompt)` on the contract
2. **ROFL app polls** for unfulfilled requests using `getUnfulfilledRequests(limit)`
3. **ROFL app processes** the prompt using the DeepSeek LLM
4. **ROFL app submits** the response via authenticated transaction to `submitResponse(requestId, response)`
5. **Users can query** their responses using `getRequest(requestId)`

## Usage Example

### From Web3 (JavaScript)

```javascript
const ethers = require('ethers');

// Contract ABI (simplified)
const ABI = [
  "function createRequest(string prompt) returns (uint256)",
  "function getRequest(uint256 requestId) view returns (address, string, uint256, bool, string)"
];

// Connect to Sapphire Testnet
const provider = new ethers.JsonRpcProvider('https://testnet.sapphire.oasis.io');
const signer = new ethers.Wallet(PRIVATE_KEY, provider);

// Contract instance
const llmBridge = new ethers.Contract(
  '0x32f22B267Be8CD47FAF93Bcd1CC31059bdc24FD2',
  ABI,
  signer
);

// Submit a request
async function askLLM(prompt) {
  console.log('Submitting request...');
  const tx = await llmBridge.createRequest(prompt);
  const receipt = await tx.wait();
  
  // Get request ID from event (or it's the return value)
  const requestId = 0; // In production, parse from events
  
  console.log('Request ID:', requestId);
  
  // Poll for response
  while (true) {
    const [requester, prompt, timestamp, fulfilled, response] = 
      await llmBridge.getRequest(requestId);
    
    if (fulfilled) {
      console.log('Response:', response);
      break;
    }
    
    console.log('Waiting for response...');
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
}

// Example usage
askLLM("What is ROFL and how does it work?");
```

### From Command Line (using cast)

```bash
# Create a request
cast send 0x32f22B267Be8CD47FAF93Bcd1CC31059bdc24FD2 \
  "createRequest(string)" \
  "What is the meaning of life?" \
  --rpc-url https://testnet.sapphire.oasis.io \
  --private-key $PRIVATE_KEY

# Check request status (replace 0 with your request ID)
cast call 0x32f22B267Be8CD47FAF93Bcd1CC31059bdc24FD2 \
  "getRequest(uint256)" \
  0 \
  --rpc-url https://testnet.sapphire.oasis.io
```

## Integration Notes

1. **Authentication**: Only the authorized ROFL app can submit responses
2. **Gas Costs**: Creating requests requires gas on Sapphire Testnet
3. **Response Time**: Depends on ROFL polling interval (currently 10 seconds)
4. **Rate Limiting**: Consider implementing rate limiting in production

## Next Steps

To complete the integration:

1. Update the Python integration script with proper ABI encoding
2. Add the bridge integration to your ROFL app's main.py
3. Rebuild and redeploy the ROFL bundle
4. Monitor logs to ensure polling is working

## Testing

A sample request (ID: 0) has already been created with the prompt:
"Hello, can you explain what ROFL is?"

You can check its status and wait for the ROFL app to respond.
