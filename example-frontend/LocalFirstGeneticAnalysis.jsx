import React, { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import { GeneticDataService } from './GeneticDataService';

const LocalFirstGeneticAnalysis = () => {
  const [hasLocalData, setHasLocalData] = useState(false);
  const [hasWalrusBackup, setHasWalrusBackup] = useState(false);
  const [dataHash, setDataHash] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [analysisRequests, setAnalysisRequests] = useState([]);
  const [service, setService] = useState(null);

  useEffect(() => {
    checkLocalStorage();
  }, []);

  const checkLocalStorage = async () => {
    try {
      const db = await openDatabase();
      const tx = db.transaction(['snpData'], 'readonly');
      const store = tx.objectStore('snpData');
      const data = await store.get('userSNPData');
      
      if (data) {
        setHasLocalData(true);
        setDataHash(data.hash);
        setHasWalrusBackup(!!data.walrusBlobId);
      }
    } catch (error) {
      console.log('No local data found');
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsProcessing(true);
    try {
      // Initialize service
      const provider = new ethers.BrowserProvider(window.ethereum);
      const signer = await provider.getSigner();
      const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, signer);
      const geneticService = new GeneticDataService(contract);
      setService(geneticService);

      // Process and store locally
      const snpData = await geneticService.processAndStoreSNPData(file, {
        method: 'local'
      });

      setHasLocalData(true);
      setDataHash(snpData.hash);
      
      alert('SNP data processed and stored locally. Only the hash was registered on-chain.');
    } catch (error) {
      alert('Error processing SNP data: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const backupToWalrus = async () => {
    if (!service || !hasLocalData) return;

    setIsProcessing(true);
    try {
      // Re-process with Walrus backup
      const localData = await service.retrieveLocalData();
      if (!localData) throw new Error('No local data found');

      // This would need the original file or encrypted data
      await service.processAndStoreSNPData(null, {
        method: 'walrus'
      });

      setHasWalrusBackup(true);
      alert('Data successfully backed up to Walrus!');
    } catch (error) {
      alert('Error backing up to Walrus: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const requestAnalysis = async (otherUserAddress) => {
    if (!service) return;

    try {
      const tx = await service.contract.requestAnalysis(
        await service.contract.signer.getAddress(),
        otherUserAddress
      );
      const receipt = await tx.wait();
      
      // Extract request ID from events
      const requestId = extractRequestId(receipt);
      
      setAnalysisRequests([...analysisRequests, {
        id: requestId,
        otherUser: otherUserAddress,
        status: 'pending_consent',
        method: null
      }]);
    } catch (error) {
      alert('Error requesting analysis: ' + error.message);
    }
  };

  const grantConsent = async (requestId, method) => {
    if (!service) return;

    setIsProcessing(true);
    try {
      await service.grantAnalysisAccess(requestId, method);
      
      // Update request status
      setAnalysisRequests(requests => 
        requests.map(req => 
          req.id === requestId 
            ? { ...req, status: 'consented', method } 
            : req
        )
      );
      
      alert(`Consent granted! Data will be shared via ${method} method.`);
    } catch (error) {
      alert('Error granting consent: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Privacy-First Genetic Analysis</h1>
      
      {/* Local Data Status */}
      <div style={{
        backgroundColor: hasLocalData ? '#e6ffe6' : '#ffe6e6',
        padding: '20px',
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3>Your Genetic Data</h3>
        {hasLocalData ? (
          <div>
            <p>✅ SNP data stored locally (encrypted)</p>
            <p>📍 Data Hash: {dataHash.substring(0, 10)}...</p>
            <p>
              {hasWalrusBackup 
                ? '☁️ Backed up to Walrus' 
                : '💾 Local storage only'}
            </p>
            {!hasWalrusBackup && (
              <button onClick={backupToWalrus} disabled={isProcessing}>
                Backup to Walrus
              </button>
            )}
          </div>
        ) : (
          <div>
            <p>No genetic data stored yet.</p>
            <input 
              type="file" 
              accept=".txt,.csv" 
              onChange={handleFileUpload}
              disabled={isProcessing}
            />
            <p style={{ fontSize: '12px', marginTop: '10px' }}>
              Your data will be encrypted and stored locally. 
              Only a hash will be registered on-chain.
            </p>
          </div>
        )}
      </div>

      {/* Analysis Requests */}
      {hasLocalData && (
        <div style={{
          backgroundColor: '#f0f0f0',
          padding: '20px',
          borderRadius: '8px',
          marginBottom: '20px'
        }}>
          <h3>Request Analysis</h3>
          <input 
            type="text" 
            placeholder="Other user's address (0x...)"
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                requestAnalysis(e.target.value);
                e.target.value = '';
              }
            }}
          />
          <p style={{ fontSize: '12px' }}>
            Both users must consent before analysis can begin.
          </p>
        </div>
      )}

      {/* Pending Requests */}
      {analysisRequests.length > 0 && (
        <div>
          <h3>Analysis Requests</h3>
          {analysisRequests.map(request => (
            <div key={request.id} style={{
              border: '1px solid #ddd',
              padding: '15px',
              marginBottom: '10px',
              borderRadius: '5px'
            }}>
              <p>Request #{request.id} with {request.otherUser.substring(0, 10)}...</p>
              <p>Status: {request.status}</p>
              
              {request.status === 'pending_consent' && (
                <div>
                  <p>Choose how to share your data:</p>
                  <button 
                    onClick={() => grantConsent(request.id, 'direct')}
                    disabled={isProcessing}
                    style={{ marginRight: '10px' }}
                  >
                    Direct Upload (One-time)
                  </button>
                  {hasWalrusBackup && (
                    <button 
                      onClick={() => grantConsent(request.id, 'walrus')}
                      disabled={isProcessing}
                    >
                      Use Walrus Backup
                    </button>
                  )}
                </div>
              )}
              
              {request.status === 'consented' && (
                <p>✅ You consented via {request.method} method</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Privacy Notice */}
      <div style={{
        backgroundColor: '#f9f9f9',
        padding: '15px',
        borderRadius: '5px',
        marginTop: '20px',
        fontSize: '14px'
      }}>
        <h4>🔒 Privacy Features</h4>
        <ul>
          <li>Your genetic data never leaves your device unless you explicitly consent</li>
          <li>All data is encrypted with your personal key</li>
          <li>Only data hashes are stored on-chain</li>
          <li>You control when and how your data is shared</li>
          <li>Consent can be revoked before analysis begins</li>
          <li>ROFL processes data in a secure TEE environment</li>
        </ul>
      </div>
    </div>
  );
};

// Helper functions
const openDatabase = () => {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('GeneticDataDB', 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('snpData')) {
        db.createObjectStore('snpData', { keyPath: 'id' });
      }
    };
  });
};

const extractRequestId = (receipt) => {
  // Extract from event logs
  return '1'; // Placeholder
};

const CONTRACT_ADDRESS = "0x..."; // New privacy-preserving contract
const ABI = []; // Contract ABI

export default LocalFirstGeneticAnalysis;
