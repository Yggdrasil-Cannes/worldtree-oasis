import React, { useState } from 'react';
import { ethers } from 'ethers';

const WORLDTREE_ABI = [
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
  }
];

const CONTRACT_ADDRESS = "0x614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3";

function GeneticAnalysis() {
  const [user1Address, setUser1Address] = useState('');
  const [user2Address, setUser2Address] = useState('');
  const [loading, setLoading] = useState(false);
  const [requestId, setRequestId] = useState(null);
  const [status, setStatus] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  // Connect to wallet
  const connectWallet = async () => {
    try {
      await window.ethereum.request({ method: 'eth_requestAccounts' });
      setStatus('Wallet connected');
    } catch (err) {
      setError('Failed to connect wallet');
    }
  };

  // Submit analysis request
  const submitAnalysis = async () => {
    try {
      setLoading(true);
      setError('');
      setStatus('Submitting analysis request...');

      const provider = new ethers.BrowserProvider(window.ethereum);
      const signer = await provider.getSigner();
      const contract = new ethers.Contract(CONTRACT_ADDRESS, WORLDTREE_ABI, signer);

      // Submit request
      const tx = await contract.requestAnalysis(user1Address, user2Address);
      setStatus('Transaction submitted, waiting for confirmation...');
      
      const receipt = await tx.wait();
      
      // Extract request ID from logs
      const iface = new ethers.Interface(WORLDTREE_ABI);
      let foundRequestId = null;
      
      for (const log of receipt.logs) {
        try {
          const parsed = iface.parseLog(log);
          if (parsed && parsed.name === 'AnalysisRequested') {
            foundRequestId = parsed.args.id.toString();
            break;
          }
        } catch (e) {
          // Not our event, continue
        }
      }

      if (foundRequestId) {
        setRequestId(foundRequestId);
        setStatus(`Analysis request created with ID: ${foundRequestId}`);
        
        // Start polling for results
        pollForResults(foundRequestId);
      } else {
        // Fallback: try to find the request ID by checking recent requests
        setStatus('Request submitted, checking for ID...');
        // You could implement logic to find the most recent request here
      }

    } catch (err) {
      console.error(err);
      setError(err.message);
      setLoading(false);
    }
  };

  // Poll for analysis results
  const pollForResults = async (reqId) => {
    setStatus('Waiting for ROFL analysis to complete...');
    
    const provider = new ethers.BrowserProvider(window.ethereum);
    const contract = new ethers.Contract(CONTRACT_ADDRESS, WORLDTREE_ABI, provider);

    const checkStatus = async () => {
      try {
        const request = await contract.getAnalysisRequest(reqId);
        
        if (request.status === 'completed') {
          setStatus('Analysis completed!');
          const analysisResult = JSON.parse(request.result);
          setResult(analysisResult);
          setLoading(false);
          return true; // Stop polling
        } else if (request.status === 'failed') {
          setStatus('Analysis failed');
          setError(request.result);
          setLoading(false);
          return true; // Stop polling
        } else {
          setStatus(`Analysis status: ${request.status}. Checking again in 5 seconds...`);
          return false; // Continue polling
        }
      } catch (err) {
        console.error('Error checking status:', err);
        return false; // Continue polling
      }
    };

    // Initial check
    const completed = await checkStatus();
    if (!completed) {
      // Set up polling interval
      const interval = setInterval(async () => {
        const done = await checkStatus();
        if (done) {
          clearInterval(interval);
        }
      }, 5000); // Poll every 5 seconds
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h2>Genetic Analysis Service</h2>
      
      <button onClick={connectWallet} style={{ marginBottom: '20px' }}>
        Connect Wallet
      </button>

      <div style={{ marginBottom: '20px' }}>
        <h3>Request Analysis</h3>
        <input
          type="text"
          placeholder="User 1 Address (0x...)"
          value={user1Address}
          onChange={(e) => setUser1Address(e.target.value)}
          style={{ width: '100%', marginBottom: '10px', padding: '8px' }}
        />
        <input
          type="text"
          placeholder="User 2 Address (0x...)"
          value={user2Address}
          onChange={(e) => setUser2Address(e.target.value)}
          style={{ width: '100%', marginBottom: '10px', padding: '8px' }}
        />
        <button 
          onClick={submitAnalysis} 
          disabled={loading || !user1Address || !user2Address}
          style={{ width: '100%', padding: '10px' }}
        >
          {loading ? 'Processing...' : 'Submit Analysis Request'}
        </button>
      </div>

      {status && (
        <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#f0f0f0' }}>
          <strong>Status:</strong> {status}
        </div>
      )}

      {error && (
        <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#ffcccc' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: '20px', padding: '20px', backgroundColor: '#e6f7ff' }}>
          <h3>Analysis Results</h3>
          <p><strong>Relationship:</strong> {result.relationship}</p>
          <p><strong>Confidence:</strong> {result.confidence}%</p>
          <p><strong>Similarity Score:</strong> {result.similarity}%</p>
          <p><strong>Shared Markers:</strong> {result.shared_markers}</p>
        </div>
      )}

      {requestId && (
        <div style={{ marginTop: '20px', fontSize: '12px', color: '#666' }}>
          Request ID: {requestId}
        </div>
      )}
    </div>
  );
}

export default GeneticAnalysis;
