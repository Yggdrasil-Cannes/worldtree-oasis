// Express API server for World Mini App
import express from 'express';
import { ethers } from 'ethers';
import multer from 'multer';
import crypto from 'crypto';
import { WorldMiniAppBackend } from './WorldMiniAppBackend';

const app = express();
app.use(express.json());

// Initialize backend service
const backend = new WorldMiniAppBackend(
  process.env.RPC_URL || 'https://testnet.sapphire.oasis.io',
  process.env.MASTER_PRIVATE_KEY!,
  process.env.CONTRACT_ADDRESS!,
  require('./contractABI.json')
);

// In-memory storage for demo (use Redis/DB in production)
const userSessions = new Map<string, any>();
const pendingData = new Map<string, Buffer>();

// Multer for file uploads
const upload = multer({ 
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 } // 10MB limit
});

/**
 * World ID verification endpoint
 */
app.post('/api/verify-world-id', async (req, res) => {
  try {
    const { proof, merkle_root, nullifier_hash, credential_type } = req.body;
    
    // Verify World ID proof
    const response = await fetch('https://developer.worldcoin.org/api/v1/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        proof,
        merkle_root,
        nullifier_hash,
        action: process.env.WORLD_ID_ACTION!,
        signal: 'genetic_analysis_app',
      }),
    });

    if (!response.ok) {
      throw new Error('World ID verification failed');
    }

    const { verified } = await response.json();
    if (!verified) {
      throw new Error('Invalid World ID proof');
    }

    // Create session
    const sessionId = crypto.randomBytes(32).toString('hex');
    userSessions.set(sessionId, {
      worldId: nullifier_hash, // This is the unique identifier
      verified: true,
      timestamp: Date.now()
    });

    res.json({ 
      success: true, 
      sessionId,
      message: 'World ID verified successfully'
    });
    
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

/**
 * Register user with SNP data
 */
app.post('/api/register', upload.single('snpFile'), async (req, res) => {
  try {
    const { sessionId } = req.body;
    const session = userSessions.get(sessionId);
    
    if (!session || !session.verified) {
      throw new Error('Invalid or expired session');
    }

    if (!req.file) {
      throw new Error('SNP file required');
    }

    // Process SNP data
    const snpData = req.file.buffer.toString('utf-8');
    
    // Validate SNP format
    const lines = snpData.split('\n').filter(line => line.trim());
    if (lines.length < 100) {
      throw new Error('Insufficient SNP data');
    }

    // Calculate hash
    const snpDataHash = ethers.keccak256(
      ethers.toUtf8Bytes(snpData)
    );

    // Encrypt and store temporarily (for later upload to ROFL)
    const encryptedData = await encryptData(snpData, session.worldId);
    pendingData.set(session.worldId, encryptedData);

    // Register on-chain (only hash)
    const userAddress = await backend.registerUser(
      session.worldId,
      {}, // World ID proof already verified
      snpDataHash
    );

    // Update session
    session.userAddress = userAddress;
    session.snpDataHash = snpDataHash;
    session.hasLocalData = true;

    res.json({
      success: true,
      userAddress,
      snpDataHash,
      message: 'Successfully registered. SNP data stored locally.'
    });

  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

/**
 * Request genetic analysis
 */
app.post('/api/request-analysis', async (req, res) => {
  try {
    const { sessionId, targetUserAddress } = req.body;
    const session = userSessions.get(sessionId);
    
    if (!session || !session.userAddress) {
      throw new Error('Not registered');
    }

    // Submit analysis request
    const requestId = await backend.requestAnalysis(
      session.worldId,
      targetUserAddress
    );

    res.json({
      success: true,
      requestId,
      message: 'Analysis request created. Waiting for consent from other user.'
    });

  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

/**
 * Get user's analysis requests
 */
app.get('/api/my-requests/:sessionId', async (req, res) => {
  try {
    const session = userSessions.get(req.params.sessionId);
    
    if (!session || !session.userAddress) {
      throw new Error('Not registered');
    }

    const requests = await backend.getUserRequests(session.worldId);
    
    // Add consent status for each request
    const enrichedRequests = requests.map(request => {
      const needsMyConsent = 
        (request.user1 === session.userAddress && !request.user1Consented) ||
        (request.user2 === session.userAddress && !request.user2Consented);
      
      return {
        ...request,
        needsMyConsent,
        role: request.requester === session.userAddress ? 'requester' : 'target'
      };
    });

    res.json({
      success: true,
      requests: enrichedRequests
    });

  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

/**
 * Grant consent for analysis
 */
app.post('/api/grant-consent', async (req, res) => {
  try {
    const { sessionId, requestId, method } = req.body;
    const session = userSessions.get(sessionId);
    
    if (!session || !session.userAddress) {
      throw new Error('Not registered');
    }

    // For direct upload method, prepare data
    if (method === 'direct') {
      const encryptedData = pendingData.get(session.worldId);
      if (!encryptedData) {
        throw new Error('No local data found');
      }

      // Grant consent
      await backend.grantConsent(
        session.worldId,
        requestId,
        'direct'
      );

      // Schedule data upload to ROFL
      setTimeout(async () => {
        try {
          await backend.uploadDataToROFL(
            session.worldId,
            requestId,
            encryptedData
          );
          console.log(`Data uploaded for request ${requestId}`);
        } catch (error) {
          console.error('Failed to upload data:', error);
        }
      }, 5000); // Wait 5 seconds for ROFL to be ready

    } else if (method === 'walrus') {
      // For Walrus method, would provide decryption key
      throw new Error('Walrus not implemented yet');
    }

    res.json({
      success: true,
      message: `Consent granted. Data will be shared via ${method} method.`
    });

  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

/**
 * Check analysis status
 */
app.get('/api/analysis-status/:sessionId/:requestId', async (req, res) => {
  try {
    const session = userSessions.get(req.params.sessionId);
    
    if (!session) {
      throw new Error('Invalid session');
    }

    // Query contract for request status
    const request = await backend.worldtreeContract.analysisRequests(
      req.params.requestId
    );

    res.json({
      success: true,
      status: request.status,
      result: request.status === 'completed' ? JSON.parse(request.result) : null,
      completionTime: request.completionTime > 0 
        ? new Date(Number(request.completionTime) * 1000).toISOString()
        : null
    });

  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

/**
 * Backup to Walrus endpoint
 */
app.post('/api/backup-to-walrus', async (req, res) => {
  try {
    const { sessionId } = req.body;
    const session = userSessions.get(sessionId);
    
    if (!session || !session.hasLocalData) {
      throw new Error('No local data to backup');
    }

    // Get encrypted data
    const encryptedData = pendingData.get(session.worldId);
    if (!encryptedData) {
      throw new Error('Data not found');
    }

    // Upload to Walrus (simplified)
    const walrusBlobId = await uploadToWalrus(encryptedData);
    
    // Update contract
    await backend.worldtreeContract.addWalrusBackupFor(
      session.userAddress,
      walrusBlobId
    );

    session.hasWalrusBackup = true;
    session.walrusBlobId = walrusBlobId;

    res.json({
      success: true,
      walrusBlobId,
      message: 'Successfully backed up to Walrus'
    });

  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Helper functions

async function encryptData(data: string, key: string): Promise<Buffer> {
  const cipher = crypto.createCipher('aes-256-gcm', key);
  const encrypted = Buffer.concat([
    cipher.update(data, 'utf8'),
    cipher.final()
  ]);
  return encrypted;
}

async function uploadToWalrus(data: Buffer): Promise<string> {
  // Simplified Walrus upload
  // In production, use actual Walrus SDK
  return `walrus_blob_${Date.now()}`;
}

// Session cleanup (run periodically)
setInterval(() => {
  const now = Date.now();
  const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes
  
  for (const [sessionId, session] of userSessions) {
    if (now - session.timestamp > SESSION_TIMEOUT) {
      userSessions.delete(sessionId);
      pendingData.delete(session.worldId);
    }
  }
}, 60000); // Check every minute

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`World Mini App backend running on port ${PORT}`);
  console.log('Master wallet:', backend.masterWallet.address);
});

// Error handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal server error' });
});

export default app;
