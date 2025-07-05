// Frontend Service for Local Storage + Walrus Integration
// This handles SNP data locally first, with optional Walrus backup

import { ethers } from 'ethers';
import { create } from '@web3-storage/w3up-client';

export interface SNPData {
  raw: string;                    // Raw SNP data
  hash: string;                   // SHA256 hash
  encrypted?: ArrayBuffer;        // Encrypted version
  encryptionKey?: CryptoKey;      // User's encryption key
  walrusBlobId?: string;         // Walrus blob ID if backed up
}

export interface StorageOptions {
  method: 'local' | 'walrus' | 'both';
  encryptionPassword?: string;
}

export class GeneticDataService {
  private contract: ethers.Contract;
  private walrusClient: any; // Walrus client
  
  constructor(contract: ethers.Contract) {
    this.contract = contract;
  }

  /**
   * Process and store SNP data locally first
   */
  async processAndStoreSNPData(
    file: File,
    options: StorageOptions
  ): Promise<SNPData> {
    // 1. Read file content
    const rawData = await file.text();
    
    // 2. Validate SNP format
    const isValid = this.validateSNPFormat(rawData);
    if (!isValid) {
      throw new Error('Invalid SNP data format');
    }
    
    // 3. Calculate hash for verification
    const hash = await this.calculateHash(rawData);
    
    // 4. Encrypt the data
    const password = options.encryptionPassword || await this.generatePassword();
    const { encrypted, key } = await this.encryptData(rawData, password);
    
    // 5. Store locally first
    const snpData: SNPData = {
      raw: rawData,
      hash,
      encrypted,
      encryptionKey: key
    };
    
    // Store in IndexedDB/localStorage
    await this.storeLocally(snpData);
    
    // 6. Register on-chain (only hash, no actual data)
    await this.registerOnChain(hash);
    
    // 7. Optional: Backup to Walrus
    if (options.method === 'walrus' || options.method === 'both') {
      const walrusBlobId = await this.backupToWalrus(encrypted, key);
      snpData.walrusBlobId = walrusBlobId;
      
      // Update contract with Walrus info
      await this.updateWalrusBackup(walrusBlobId);
    }
    
    return snpData;
  }

  /**
   * Store data locally using IndexedDB
   */
  private async storeLocally(data: SNPData): Promise<void> {
    const db = await this.openDatabase();
    const tx = db.transaction(['snpData'], 'readwrite');
    const store = tx.objectStore('snpData');
    
    await store.put({
      id: 'userSNPData',
      hash: data.hash,
      encrypted: data.encrypted,
      walrusBlobId: data.walrusBlobId,
      timestamp: Date.now()
    });
  }

  /**
   * Retrieve data from local storage
   */
  async retrieveLocalData(): Promise<SNPData | null> {
    const db = await this.openDatabase();
    const tx = db.transaction(['snpData'], 'readonly');
    const store = tx.objectStore('snpData');
    
    const data = await store.get('userSNPData');
    return data || null;
  }

  /**
   * Encrypt SNP data
   */
  private async encryptData(
    data: string,
    password: string
  ): Promise<{ encrypted: ArrayBuffer; key: CryptoKey }> {
    // Generate key from password
    const encoder = new TextEncoder();
    const keyMaterial = await crypto.subtle.importKey(
      'raw',
      encoder.encode(password),
      'PBKDF2',
      false,
      ['deriveKey']
    );
    
    // Generate salt
    const salt = crypto.getRandomValues(new Uint8Array(16));
    
    // Derive key
    const key = await crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt,
        iterations: 100000,
        hash: 'SHA-256'
      },
      keyMaterial,
      { name: 'AES-GCM', length: 256 },
      true,
      ['encrypt', 'decrypt']
    );
    
    // Encrypt data
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encrypted = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      key,
      encoder.encode(data)
    );
    
    // Combine salt, iv, and encrypted data
    const combined = new Uint8Array(salt.length + iv.length + encrypted.byteLength);
    combined.set(salt, 0);
    combined.set(iv, salt.length);
    combined.set(new Uint8Array(encrypted), salt.length + iv.length);
    
    return { encrypted: combined.buffer, key };
  }

  /**
   * Backup encrypted data to Walrus
   */
  private async backupToWalrus(
    encryptedData: ArrayBuffer,
    encryptionKey: CryptoKey
  ): Promise<string> {
    // Initialize Walrus client
    if (!this.walrusClient) {
      this.walrusClient = await this.initializeWalrusClient();
    }
    
    // Create a blob with encrypted data
    const blob = new Blob([encryptedData], { type: 'application/octet-stream' });
    
    // Upload to Walrus
    const result = await this.walrusClient.uploadBlob(blob);
    
    return result.blobId;
  }

  /**
   * Grant temporary access for analysis
   */
  async grantAnalysisAccess(
    requestId: number,
    method: 'direct' | 'walrus'
  ): Promise<void> {
    const localData = await this.retrieveLocalData();
    if (!localData) {
      throw new Error('No local SNP data found');
    }
    
    if (method === 'direct') {
      // For direct upload, we'll establish a secure session
      // and upload data directly to ROFL when ready
      await this.contract.grantConsent(
        requestId,
        1, // DirectUpload enum value
        '0x' // No encryption key needed for direct upload
      );
      
      // Data will be uploaded when ROFL requests it
      this.prepareDirectUploadSession(requestId, localData);
      
    } else if (method === 'walrus' && localData.walrusBlobId) {
      // For Walrus, encrypt the decryption key for ROFL
      const roflPublicKey = await this.getROFLPublicKey();
      const encryptedKey = await this.encryptKeyForROFL(
        localData.encryptionKey!,
        roflPublicKey
      );
      
      await this.contract.grantConsent(
        requestId,
        2, // WalrusRetrieval enum value
        encryptedKey
      );
    }
  }

  /**
   * Prepare for direct upload session
   */
  private async prepareDirectUploadSession(
    requestId: number,
    data: SNPData
  ): Promise<void> {
    // Store in session storage for when ROFL requests
    sessionStorage.setItem(`analysis_${requestId}`, JSON.stringify({
      hash: data.hash,
      encrypted: Array.from(new Uint8Array(data.encrypted!)),
      timestamp: Date.now()
    }));
    
    // Set up WebRTC or WebSocket connection for secure transfer
    // This would be implemented based on ROFL's communication protocol
  }

  /**
   * Handle ROFL data request (for direct upload)
   */
  async handleROFLDataRequest(requestId: number): Promise<void> {
    const sessionData = sessionStorage.getItem(`analysis_${requestId}`);
    if (!sessionData) {
      throw new Error('No session data found');
    }
    
    const { encrypted, hash } = JSON.parse(sessionData);
    
    // Establish secure channel to ROFL
    const secureChannel = await this.establishSecureChannel();
    
    // Send encrypted data
    await secureChannel.send({
      requestId,
      hash,
      encryptedData: new Uint8Array(encrypted)
    });
    
    // Wait for confirmation
    const confirmation = await secureChannel.receive();
    if (confirmation.status === 'received') {
      // Clean up session data
      sessionStorage.removeItem(`analysis_${requestId}`);
    }
  }

  /**
   * Calculate SHA256 hash of data
   */
  private async calculateHash(data: string): Promise<string> {
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(data);
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return '0x' + hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Register user on-chain (only hash)
   */
  private async registerOnChain(dataHash: string): Promise<void> {
    const tx = await this.contract.registerUser(dataHash);
    await tx.wait();
  }

  /**
   * Update contract with Walrus backup info
   */
  private async updateWalrusBackup(walrusBlobId: string): Promise<void> {
    const tx = await this.contract.addWalrusBackup(walrusBlobId);
    await tx.wait();
  }

  /**
   * Validate SNP data format
   */
  private validateSNPFormat(data: string): boolean {
    const lines = data.trim().split('\n');
    
    // Basic validation - check if it looks like SNP data
    for (const line of lines.slice(0, 10)) { // Check first 10 lines
      const parts = line.split(/\s+/);
      if (parts.length < 4) return false;
      
      // Should have: rsid, position, chromosome, genotype
      const [rsid, position, chromosome, genotype] = parts;
      
      if (!rsid.startsWith('rs')) return false;
      if (isNaN(Number(position))) return false;
      if (isNaN(Number(chromosome))) return false;
      if (!/^[ACGT]{1,2}$/.test(genotype)) return false;
    }
    
    return true;
  }

  /**
   * Generate secure password
   */
  private async generatePassword(): Promise<string> {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Open IndexedDB
   */
  private async openDatabase(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('GeneticDataDB', 1);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
      
      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains('snpData')) {
          db.createObjectStore('snpData', { keyPath: 'id' });
        }
      };
    });
  }

  /**
   * Initialize Walrus client
   */
  private async initializeWalrusClient(): Promise<any> {
    // This would be the actual Walrus client initialization
    // For now, returning a mock
    return {
      uploadBlob: async (blob: Blob) => {
        // Actual Walrus upload logic
        return { blobId: 'walrus_blob_' + Date.now() };
      }
    };
  }

  /**
   * Get ROFL public key for encryption
   */
  private async getROFLPublicKey(): Promise<CryptoKey> {
    // This would fetch the ROFL app's public key
    // For secure key exchange
    throw new Error('Not implemented');
  }

  /**
   * Encrypt user's key for ROFL
   */
  private async encryptKeyForROFL(
    userKey: CryptoKey,
    roflPublicKey: CryptoKey
  ): Promise<string> {
    // Export user's key
    const exportedKey = await crypto.subtle.exportKey('raw', userKey);
    
    // Encrypt with ROFL's public key
    // This would use ECIES or similar
    throw new Error('Not implemented');
  }

  /**
   * Establish secure channel to ROFL
   */
  private async establishSecureChannel(): Promise<any> {
    // This would establish WebRTC or WebSocket connection
    // with mutual TLS or similar security
    throw new Error('Not implemented');
  }
}

// Usage Example:
/*
const service = new GeneticDataService(contract);

// Initial upload (stays local)
const snpData = await service.processAndStoreSNPData(file, {
  method: 'local',
  encryptionPassword: userPassword
});

// Later: User decides to backup to Walrus
await service.processAndStoreSNPData(file, {
  method: 'walrus',
  encryptionPassword: userPassword
});

// When analysis is requested
await service.grantAnalysisAccess(requestId, 'direct'); // or 'walrus'
*/
