// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@oasisprotocol/sapphire-contracts/contracts/Subcall.sol";

/**
 * @title WorldtreePrivate
 * @dev Privacy-preserving genetic analysis with user consent
 */
contract WorldtreePrivate {
    bytes21 public immutable roflApp;
    
    struct User {
        address wallet;
        bool registered;
        bytes32 snpDataHash;      // Hash of the SNP data
        string encryptedDataUrl;   // IPFS/Arweave URL to encrypted data
        uint256 registrationTime;
    }
    
    struct AnalysisRequest {
        uint256 id;
        address requester;
        address user1;
        address user2;
        bool user1Consented;
        bool user2Consented;
        string status; // "pending_consent", "pending_analysis", "processing", "completed", "failed"
        string result;
        uint256 requestTime;
        uint256 completionTime;
    }
    
    struct DataAccessGrant {
        address grantedTo;      // ROFL app or other user
        uint256 expiryTime;
        uint256 requestId;      // Specific to this request
        bytes encryptedKey;     // User's data key encrypted for ROFL
    }
    
    mapping(address => User) public users;
    mapping(uint256 => AnalysisRequest) public analysisRequests;
    mapping(address => mapping(uint256 => DataAccessGrant)) public dataGrants;
    mapping(address => uint256[]) public userRequests;
    
    uint256 public nextRequestId;
    
    event UserRegistered(address indexed user, bytes32 dataHash);
    event AnalysisRequested(uint256 indexed id, address indexed requester, address user1, address user2);
    event ConsentGranted(uint256 indexed requestId, address indexed user);
    event AnalysisCompleted(uint256 indexed id);
    
    constructor(bytes21 _roflApp) {
        roflApp = _roflApp;
    }
    
    /**
     * @dev Register user with encrypted SNP data stored off-chain
     * @param snpDataHash Hash of the user's SNP data
     * @param encryptedDataUrl URL to encrypted SNP data (IPFS, Arweave, etc.)
     */
    function registerUser(
        bytes32 snpDataHash,
        string memory encryptedDataUrl
    ) external {
        users[msg.sender] = User({
            wallet: msg.sender,
            registered: true,
            snpDataHash: snpDataHash,
            encryptedDataUrl: encryptedDataUrl,
            registrationTime: block.timestamp
        });
        
        emit UserRegistered(msg.sender, snpDataHash);
    }
    
    /**
     * @dev Request analysis between two users (requires their consent)
     */
    function requestAnalysis(address user1, address user2) external returns (uint256) {
        require(users[user1].registered, "User1 not registered");
        require(users[user2].registered, "User2 not registered");
        require(user1 != user2, "Cannot analyze same user");
        
        uint256 requestId = nextRequestId++;
        
        analysisRequests[requestId] = AnalysisRequest({
            id: requestId,
            requester: msg.sender,
            user1: user1,
            user2: user2,
            user1Consented: (msg.sender == user1),  // Auto-consent if requester
            user2Consented: (msg.sender == user2),  // Auto-consent if requester
            status: "pending_consent",
            result: "",
            requestTime: block.timestamp,
            completionTime: 0
        });
        
        userRequests[user1].push(requestId);
        if (user1 != user2) {
            userRequests[user2].push(requestId);
        }
        
        emit AnalysisRequested(requestId, msg.sender, user1, user2);
        
        // If both already consented, mark ready for analysis
        if (analysisRequests[requestId].user1Consented && 
            analysisRequests[requestId].user2Consented) {
            analysisRequests[requestId].status = "pending_analysis";
        }
        
        return requestId;
    }
    
    /**
     * @dev Grant consent and provide encrypted data access for analysis
     * @param requestId The analysis request ID
     * @param encryptedKey User's data encryption key, encrypted for ROFL app
     */
    function grantConsent(
        uint256 requestId,
        bytes memory encryptedKey
    ) external {
        AnalysisRequest storage req = analysisRequests[requestId];
        require(
            msg.sender == req.user1 || msg.sender == req.user2,
            "Not part of this analysis"
        );
        
        // Update consent
        if (msg.sender == req.user1) {
            req.user1Consented = true;
        } else {
            req.user2Consented = true;
        }
        
        // Store encrypted key grant
        dataGrants[msg.sender][requestId] = DataAccessGrant({
            grantedTo: address(uint160(bytes20(roflApp))),
            expiryTime: block.timestamp + 7 days,  // Expires in 7 days
            requestId: requestId,
            encryptedKey: encryptedKey
        });
        
        emit ConsentGranted(requestId, msg.sender);
        
        // If both consented, mark ready for analysis
        if (req.user1Consented && req.user2Consented) {
            req.status = "pending_analysis";
        }
    }
    
    /**
     * @dev Revoke consent for an analysis
     */
    function revokeConsent(uint256 requestId) external {
        AnalysisRequest storage req = analysisRequests[requestId];
        require(
            msg.sender == req.user1 || msg.sender == req.user2,
            "Not part of this analysis"
        );
        require(
            keccak256(bytes(req.status)) == keccak256(bytes("pending_consent")) ||
            keccak256(bytes(req.status)) == keccak256(bytes("pending_analysis")),
            "Analysis already started"
        );
        
        if (msg.sender == req.user1) {
            req.user1Consented = false;
        } else {
            req.user2Consented = false;
        }
        
        delete dataGrants[msg.sender][requestId];
        req.status = "pending_consent";
    }
    
    /**
     * @dev Get analysis requests pending consent or ready for processing
     */
    function getPendingRequests() external view returns (uint256[] memory) {
        uint256[] memory pending = new uint256[](nextRequestId);
        uint256 count = 0;
        
        for (uint256 i = 0; i < nextRequestId; i++) {
            string memory status = analysisRequests[i].status;
            if (keccak256(bytes(status)) == keccak256(bytes("pending_analysis"))) {
                pending[count] = i;
                count++;
            }
        }
        
        uint256[] memory result = new uint256[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = pending[i];
        }
        
        return result;
    }
    
    /**
     * @dev ROFL app retrieves data access for analysis
     */
    function getDataAccess(uint256 requestId) external view returns (
        string memory user1DataUrl,
        string memory user2DataUrl,
        bytes memory user1EncryptedKey,
        bytes memory user2EncryptedKey
    ) {
        // Only ROFL app can access
        Subcall.roflEnsureAuthorizedOrigin(roflApp);
        
        AnalysisRequest memory req = analysisRequests[requestId];
        require(
            keccak256(bytes(req.status)) == keccak256(bytes("pending_analysis")),
            "Not ready for analysis"
        );
        
        DataAccessGrant memory grant1 = dataGrants[req.user1][requestId];
        DataAccessGrant memory grant2 = dataGrants[req.user2][requestId];
        
        require(grant1.expiryTime > block.timestamp, "User1 grant expired");
        require(grant2.expiryTime > block.timestamp, "User2 grant expired");
        
        return (
            users[req.user1].encryptedDataUrl,
            users[req.user2].encryptedDataUrl,
            grant1.encryptedKey,
            grant2.encryptedKey
        );
    }
    
    /**
     * @dev ROFL app marks analysis as processing
     */
    function markProcessing(uint256 requestId) external {
        Subcall.roflEnsureAuthorizedOrigin(roflApp);
        
        AnalysisRequest storage req = analysisRequests[requestId];
        require(
            keccak256(bytes(req.status)) == keccak256(bytes("pending_analysis")),
            "Invalid status"
        );
        
        req.status = "processing";
    }
    
    /**
     * @dev ROFL app submits analysis results
     */
    function submitAnalysisResult(
        uint256 requestId,
        string memory result,
        uint256 confidence,
        string memory relationshipType
    ) external {
        Subcall.roflEnsureAuthorizedOrigin(roflApp);
        
        AnalysisRequest storage req = analysisRequests[requestId];
        require(
            keccak256(bytes(req.status)) == keccak256(bytes("processing")),
            "Not in processing state"
        );
        
        req.status = "completed";
        req.result = result;
        req.completionTime = block.timestamp;
        
        // Clean up grants after use
        delete dataGrants[req.user1][requestId];
        delete dataGrants[req.user2][requestId];
        
        emit AnalysisCompleted(requestId);
    }
    
    /**
     * @dev Get user's analysis requests
     */
    function getUserRequests(address user) external view returns (uint256[] memory) {
        return userRequests[user];
    }
    
    /**
     * @dev Check if user has consented to a specific request
     */
    function hasConsented(address user, uint256 requestId) external view returns (bool) {
        AnalysisRequest memory req = analysisRequests[requestId];
        if (user == req.user1) return req.user1Consented;
        if (user == req.user2) return req.user2Consented;
        return false;
    }
}
