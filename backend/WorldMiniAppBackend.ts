// Backend service for managing user accounts and transactions
import { ethers } from 'ethers';
import { WorldIDVerifier } from '@worldcoin/id';

interface UserAccount {
  worldId: string;
  derivedAddress: string;  // Deterministic address from World ID
  nonce: number;
}

export class WorldMiniAppBackend {
  private provider: ethers.Provider;
  private masterWallet: ethers.Wallet;
  private worldtreeContract: ethers.Contract;
  private userAccounts: Map<string, UserAccount> = new Map();

  constructor(
    rpcUrl: string,
    masterPrivateKey: string,  // Master key that pays for all transactions
    contractAddress: string,
    contractABI: any[]
  ) {
    this.provider = new ethers.JsonRpcProvider(rpcUrl);
    this.masterWallet = new ethers.Wallet(masterPrivateKey, this.provider);
    this.worldtreeContract = new ethers.Contract(
      contractAddress,
      contractABI,
      this.masterWallet
    );
  }

  /**
   * Derive a unique address for each World ID user
   * This creates a deterministic mapping: World ID → Ethereum address
   */
  deriveUserAddress(worldId: string): string {
    // Create deterministic address from World ID
    // This ensures same World ID always maps to same address
    const hash = ethers.keccak256(
      ethers.AbiCoder.defaultAbiCoder().encode(
        ['string', 'address'],
        [worldId, this.masterWallet.address]
      )
    );
    
    // Use first 20 bytes as address
    return '0x' + hash.slice(26);
  }

  /**
   * Register a new user (called after World ID verification)
   */
  async registerUser(
    worldId: string,
    worldIdProof: any,  // World ID zero-knowledge proof
    snpDataHash: string
  ): Promise<string> {
    // Verify World ID proof
    const isValid = await this.verifyWorldId(worldId, worldIdProof);
    if (!isValid) {
      throw new Error('Invalid World ID proof');
    }

    // Get or create user account
    const userAddress = this.deriveUserAddress(worldId);
    
    if (!this.userAccounts.has(worldId)) {
      this.userAccounts.set(worldId, {
        worldId,
        derivedAddress: userAddress,
        nonce: 0
      });
    }

    // Execute registration transaction on behalf of user
    const tx = await this.worldtreeContract.registerUserFor(
      userAddress,      // Register for this derived address
      snpDataHash,      // User's SNP data hash
      worldIdProof      // Include proof for verification
    );

    await tx.wait();
    
    return userAddress;
  }

  /**
   * Request analysis on behalf of a user
   */
  async requestAnalysis(
    worldId: string,
    targetUserAddress: string
  ): Promise<number> {
    const userAccount = this.userAccounts.get(worldId);
    if (!userAccount) {
      throw new Error('User not registered');
    }

    // Execute transaction on behalf of user
    const tx = await this.worldtreeContract.requestAnalysisFor(
      userAccount.derivedAddress,  // Requester
      targetUserAddress,           // Target user
      { gasLimit: 500000 }
    );

    const receipt = await tx.wait();
    
    // Extract request ID from events
    const event = receipt.logs.find(log => {
      try {
        const parsed = this.worldtreeContract.interface.parseLog(log);
        return parsed.name === 'AnalysisRequested';
      } catch {
        return false;
      }
    });

    return event.args.id.toNumber();
  }

  /**
   * Grant consent for analysis
   */
  async grantConsent(
    worldId: string,
    requestId: number,
    method: 'direct' | 'walrus',
    encryptedKey?: string
  ): Promise<void> {
    const userAccount = this.userAccounts.get(worldId);
    if (!userAccount) {
      throw new Error('User not registered');
    }

    const methodEnum = method === 'direct' ? 1 : 2;
    
    const tx = await this.worldtreeContract.grantConsentFor(
      userAccount.derivedAddress,
      requestId,
      methodEnum,
      encryptedKey || '0x'
    );

    await tx.wait();
  }

  /**
   * Get user's analysis requests
   */
  async getUserRequests(worldId: string): Promise<any[]> {
    const userAccount = this.userAccounts.get(worldId);
    if (!userAccount) {
      throw new Error('User not registered');
    }

    // Read from contract
    const requestIds = await this.worldtreeContract.getUserRequests(
      userAccount.derivedAddress
    );

    // Fetch details for each request
    const requests = await Promise.all(
      requestIds.map(async (id) => {
        const request = await this.worldtreeContract.analysisRequests(id);
        return {
          id: id.toString(),
          requester: request.requester,
          user1: request.user1,
          user2: request.user2,
          status: request.status,
          // ... other fields
        };
      })
    );

    return requests;
  }

  /**
   * Verify World ID proof
   */
  private async verifyWorldId(
    worldId: string,
    proof: any
  ): Promise<boolean> {
    // Implement World ID verification
    // This would use Worldcoin's SDK
    try {
      const verifier = new WorldIDVerifier();
      return await verifier.verify(worldId, proof);
    } catch {
      return false;
    }
  }

  /**
   * Handle direct data upload to ROFL
   */
  async uploadDataToROFL(
    worldId: string,
    requestId: number,
    encryptedData: Buffer
  ): Promise<void> {
    const userAccount = this.userAccounts.get(worldId);
    if (!userAccount) {
      throw new Error('User not registered');
    }

    // This would establish secure channel to ROFL
    // and upload the encrypted data
    const roflEndpoint = await this.getROFLEndpoint(requestId);
    
    const response = await fetch(roflEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/octet-stream',
        'X-Request-ID': requestId.toString(),
        'X-User-Address': userAccount.derivedAddress,
        'X-Data-Hash': ethers.keccak256(encryptedData)
      },
      body: encryptedData
    });

    if (!response.ok) {
      throw new Error('Failed to upload data to ROFL');
    }
  }

  private async getROFLEndpoint(requestId: number): Promise<string> {
    // This would query the ROFL service for upload endpoint
    // Could be via contract event or direct ROFL API
    return `https://rofl-service.example.com/upload/${requestId}`;
  }
}

// Usage in World Mini App backend:
/*
const backend = new WorldMiniAppBackend(
  'https://testnet.sapphire.oasis.io',
  process.env.MASTER_PRIVATE_KEY,
  CONTRACT_ADDRESS,
  CONTRACT_ABI
);

// API endpoint example
app.post('/api/register', async (req, res) => {
  const { worldId, worldIdProof, snpDataHash } = req.body;
  
  try {
    const userAddress = await backend.registerUser(
      worldId,
      worldIdProof,
      snpDataHash
    );
    
    res.json({ success: true, address: userAddress });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});
*/
