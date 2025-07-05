import { ethers } from 'ethers';

// Types
export interface AnalysisRequest {
  requester: string;
  user1: string;
  user2: string;
  status: 'pending' | 'completed' | 'failed';
  result: string;
  requestTime: Date;
  completionTime: Date | null;
}

export interface AnalysisResult {
  relationship: string;
  confidence: number;
  similarity: number;
  shared_markers: number;
}

export interface SubmitAnalysisResponse {
  requestId: string;
  transactionHash: string;
}

// Contract configuration
const CONTRACT_ADDRESS = "0x614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3";

const CONTRACT_ABI = [
  {
    "inputs": [
      {"internalType": "address", "name": "user1", "type": "address"},
      {"internalType": "address", "name": "user2", "type": "address"}
    ],
    "name": "requestAnalysis",
    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [{"internalType": "uint256", "name": "requestId", "type": "uint256"}],
    "name": "getAnalysisRequest",
    "outputs": [
      {"internalType": "address", "name": "requester", "type": "address"},
      {"internalType": "address", "name": "user1", "type": "address"},
      {"internalType": "address", "name": "user2", "type": "address"},
      {"internalType": "string", "name": "status", "type": "string"},
      {"internalType": "string", "name": "result", "type": "string"},
      {"internalType": "uint256", "name": "requestTime", "type": "uint256"},
      {"internalType": "uint256", "name": "completionTime", "type": "uint256"}
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "anonymous": false,
    "inputs": [
      {"indexed": true, "internalType": "uint256", "name": "id", "type": "uint256"},
      {"indexed": false, "internalType": "address", "name": "requester", "type": "address"},
      {"indexed": false, "internalType": "address", "name": "user1", "type": "address"},
      {"indexed": false, "internalType": "address", "name": "user2", "type": "address"}
    ],
    "name": "AnalysisRequested",
    "type": "event"
  },
  {
    "anonymous": false,
    "inputs": [
      {"indexed": true, "internalType": "uint256", "name": "id", "type": "uint256"},
      {"indexed": false, "internalType": "string", "name": "result", "type": "string"}
    ],
    "name": "AnalysisCompleted",
    "type": "event"
  }
];

export class GeneticAnalysisService {
  private provider: ethers.Provider;
  private signer?: ethers.Signer;
  private contract: ethers.Contract;

  constructor(provider: ethers.Provider, signer?: ethers.Signer) {
    this.provider = provider;
    this.signer = signer;
    this.contract = new ethers.Contract(
      CONTRACT_ADDRESS,
      CONTRACT_ABI,
      signer || provider
    );
  }

  /**
   * Submit a genetic analysis request for two users
   */
  async submitAnalysisRequest(
    user1Address: string, 
    user2Address: string
  ): Promise<SubmitAnalysisResponse> {
    if (!this.signer) {
      throw new Error('Signer required for submitting transactions');
    }

    // Submit the transaction
    const tx = await this.contract.requestAnalysis(user1Address, user2Address);
    const receipt = await tx.wait();

    // Extract request ID from events
    const event = receipt.logs.find((log: any) => {
      try {
        const parsed = this.contract.interface.parseLog(log);
        return parsed.name === 'AnalysisRequested';
      } catch {
        return false;
      }
    });

    if (!event) {
      throw new Error('Failed to find AnalysisRequested event');
    }

    const parsedEvent = this.contract.interface.parseLog(event);
    const requestId = parsedEvent.args.id.toString();

    return {
      requestId,
      transactionHash: receipt.hash
    };
  }

  /**
   * Get the status and result of an analysis request
   */
  async getAnalysisRequest(requestId: string | number): Promise<AnalysisRequest> {
    const request = await this.contract.getAnalysisRequest(requestId);
    
    return {
      requester: request.requester,
      user1: request.user1,
      user2: request.user2,
      status: request.status as 'pending' | 'completed' | 'failed',
      result: request.result,
      requestTime: new Date(Number(request.requestTime) * 1000),
      completionTime: request.completionTime > 0 
        ? new Date(Number(request.completionTime) * 1000)
        : null
    };
  }

  /**
   * Get parsed analysis results
   */
  async getAnalysisResult(requestId: string | number): Promise<AnalysisResult | null> {
    const request = await this.getAnalysisRequest(requestId);
    
    if (request.status !== 'completed') {
      return null;
    }

    try {
      return JSON.parse(request.result);
    } catch {
      throw new Error('Failed to parse analysis result');
    }
  }

  /**
   * Wait for an analysis to complete (with polling)
   */
  async waitForCompletion(
    requestId: string | number, 
    pollInterval: number = 5000,
    maxAttempts: number = 60
  ): Promise<AnalysisResult> {
    let attempts = 0;
    
    while (attempts < maxAttempts) {
      const request = await this.getAnalysisRequest(requestId);
      
      if (request.status === 'completed') {
        return JSON.parse(request.result);
      } else if (request.status === 'failed') {
        throw new Error(`Analysis failed: ${request.result}`);
      }
      
      // Wait before next poll
      await new Promise(resolve => setTimeout(resolve, pollInterval));
      attempts++;
    }
    
    throw new Error('Analysis timeout - exceeded maximum attempts');
  }

  /**
   * Listen for analysis completion events (alternative to polling)
   */
  async listenForCompletion(requestId: string | number): Promise<AnalysisResult> {
    return new Promise((resolve, reject) => {
      const filter = this.contract.filters.AnalysisCompleted(requestId);
      
      this.contract.on(filter, async (eventRequestId, result) => {
        try {
          // Remove listener
          this.contract.off(filter);
          
          // Get full request details
          const request = await this.getAnalysisRequest(requestId);
          
          if (request.status === 'completed') {
            resolve(JSON.parse(request.result));
          } else {
            reject(new Error(`Analysis failed: ${request.result}`));
          }
        } catch (error) {
          reject(error);
        }
      });

      // Set a timeout in case event is missed
      setTimeout(() => {
        this.contract.off(filter);
        reject(new Error('Event listener timeout'));
      }, 300000); // 5 minutes timeout
    });
  }

  /**
   * Get all analysis requests for a specific user
   */
  async getUserAnalysisRequests(userAddress: string): Promise<string[]> {
    // Note: This would require the contract to have a getUserAnalysisRequests function
    // For now, you'd need to scan events or maintain this off-chain
    throw new Error('Not implemented - requires contract support');
  }
}

// Usage example:
/*
// For read-only operations
const provider = new ethers.BrowserProvider(window.ethereum);
const service = new GeneticAnalysisService(provider);

// For write operations
const signer = await provider.getSigner();
const service = new GeneticAnalysisService(provider, signer);

// Submit analysis
const { requestId } = await service.submitAnalysisRequest(
  "0x123...", 
  "0x456..."
);

// Wait for completion
const result = await service.waitForCompletion(requestId);
console.log(`Relationship: ${result.relationship} (${result.confidence}% confidence)`);
*/
