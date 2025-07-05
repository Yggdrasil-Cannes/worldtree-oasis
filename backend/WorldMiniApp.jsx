// World Mini App Frontend (React example)
import React, { useState, useEffect } from 'react';
import { WorldIDWidget } from '@worldcoin/id';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:3000';

function WorldMiniApp() {
  const [sessionId, setSessionId] = useState(null);
  const [userAddress, setUserAddress] = useState(null);
  const [isRegistered, setIsRegistered] = useState(false);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');

  // Check session on load
  useEffect(() => {
    const savedSession = localStorage.getItem('worldtree_session');
    if (savedSession) {
      setSessionId(savedSession);
      checkRegistrationStatus(savedSession);
    }
  }, []);

  // Check if user is registered
  const checkRegistrationStatus = async (session) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/my-requests/${session}`);
      if (response.ok) {
        setIsRegistered(true);
        fetchMyRequests(session);
      }
    } catch (error) {
      console.error('Error checking status:', error);
    }
  };

  // Handle World ID verification
  const handleWorldIDSuccess = async (proof) => {
    setLoading(true);
    setStatus('Verifying World ID...');

    try {
      const response = await fetch(`${BACKEND_URL}/api/verify-world-id`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(proof),
      });

      const data = await response.json();
      
      if (data.success) {
        setSessionId(data.sessionId);
        localStorage.setItem('worldtree_session', data.sessionId);
        setStatus('World ID verified! Now you can register your genetic data.');
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      setStatus(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Handle file upload and registration
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file || !sessionId) return;

    setLoading(true);
    setStatus('Processing genetic data...');

    const formData = new FormData();
    formData.append('snpFile', file);
    formData.append('sessionId', sessionId);

    try {
      const response = await fetch(`${BACKEND_URL}/api/register`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (data.success) {
        setUserAddress(data.userAddress);
        setIsRegistered(true);
        setStatus('Successfully registered! Your genetic data is stored locally.');
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      setStatus(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Request analysis with another user
  const requestAnalysis = async () => {
    const targetAddress = prompt('Enter the other user\'s address:');
    if (!targetAddress || !sessionId) return;

    setLoading(true);
    setStatus('Requesting analysis...');

    try {
      const response = await fetch(`${BACKEND_URL}/api/request-analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          targetUserAddress: targetAddress,
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setStatus(`Analysis request created! Request ID: ${data.requestId}`);
        fetchMyRequests(sessionId);
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      setStatus(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Fetch user's requests
  const fetchMyRequests = async (session) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/my-requests/${session || sessionId}`);
      const data = await response.json();
      
      if (data.success) {
        setRequests(data.requests);
      }
    } catch (error) {
      console.error('Error fetching requests:', error);
    }
  };

  // Grant consent for analysis
  const grantConsent = async (requestId, method) => {
    setLoading(true);
    setStatus('Granting consent...');

    try {
      const response = await fetch(`${BACKEND_URL}/api/grant-consent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          requestId,
          method,
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setStatus(data.message);
        fetchMyRequests(sessionId);
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      setStatus(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Check analysis status
  const checkAnalysisStatus = async (requestId) => {
    try {
      const response = await fetch(
        `${BACKEND_URL}/api/analysis-status/${sessionId}/${requestId}`
      );
      const data = await response.json();
      
      if (data.success) {
        if (data.status === 'completed') {
          alert(`Analysis complete!\n\nRelationship: ${data.result.relationship}\nConfidence: ${data.result.confidence}%`);
        } else {
          alert(`Analysis status: ${data.status}`);
        }
      }
    } catch (error) {
      console.error('Error checking status:', error);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h1>🧬 Worldtree Genetic Analysis</h1>
      
      {/* World ID Verification */}
      {!sessionId && (
        <div style={{ marginBottom: '20px' }}>
          <h3>Step 1: Verify with World ID</h3>
          <WorldIDWidget
            actionId={process.env.REACT_APP_WORLD_ID_ACTION}
            signal="genetic_analysis_app"
            enableTelemetry
            onSuccess={handleWorldIDSuccess}
            onError={(error) => setStatus(`Error: ${error.message}`)}
          />
        </div>
      )}

      {/* Registration */}
      {sessionId && !isRegistered && (
        <div style={{ marginBottom: '20px' }}>
          <h3>Step 2: Register Your Genetic Data</h3>
          <p>Your data will be encrypted and stored locally. Only a hash will be saved on-chain.</p>
          <input
            type="file"
            accept=".txt,.csv"
            onChange={handleFileUpload}
            disabled={loading}
          />
        </div>
      )}

      {/* Main Interface */}
      {isRegistered && (
        <div>
          <div style={{ marginBottom: '20px' }}>
            <h3>Your Account</h3>
            <p>Address: {userAddress}</p>
            <button onClick={requestAnalysis} disabled={loading}>
              Request New Analysis
            </button>
          </div>

          {/* Analysis Requests */}
          <div>
            <h3>Analysis Requests</h3>
            {requests.length === 0 ? (
              <p>No requests yet.</p>
            ) : (
              requests.map((request) => (
                <div
                  key={request.id}
                  style={{
                    border: '1px solid #ddd',
                    padding: '15px',
                    marginBottom: '10px',
                    borderRadius: '5px',
                  }}
                >
                  <p>Request #{request.id}</p>
                  <p>Status: {request.status}</p>
                  <p>Role: {request.role}</p>
                  
                  {request.needsMyConsent && (
                    <div>
                      <p>⚠️ Your consent required!</p>
                      <button
                        onClick={() => grantConsent(request.id, 'direct')}
                        disabled={loading}
                      >
                        Grant Consent (Direct Upload)
                      </button>
                    </div>
                  )}
                  
                  {request.status === 'pending_analysis' && (
                    <button onClick={() => checkAnalysisStatus(request.id)}>
                      Check Status
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Status Messages */}
      {status && (
        <div
          style={{
            marginTop: '20px',
            padding: '10px',
            backgroundColor: status.includes('Error') ? '#ffcccc' : '#ccffcc',
            borderRadius: '5px',
          }}
        >
          {status}
        </div>
      )}

      {/* Loading Indicator */}
      {loading && (
        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          <p>Loading...</p>
        </div>
      )}

      {/* Privacy Notice */}
      <div
        style={{
          marginTop: '30px',
          padding: '15px',
          backgroundColor: '#f0f0f0',
          borderRadius: '5px',
          fontSize: '14px',
        }}
      >
        <h4>🔒 Privacy Features</h4>
        <ul>
          <li>Your World ID is never exposed - only a hash is used</li>
          <li>Genetic data is encrypted and stored locally</li>
          <li>All blockchain transactions are handled by our backend</li>
          <li>You don't need to manage wallets or pay gas fees</li>
          <li>Analysis happens in a secure TEE environment</li>
        </ul>
      </div>
    </div>
  );
}

export default WorldMiniApp;
