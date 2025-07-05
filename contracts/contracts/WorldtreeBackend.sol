// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@oasisprotocol/sapphire-contracts/contracts/Subcall.sol";

/**
 * @title WorldtreeBackend
 * @dev Modified contract for World Mini App with backend transaction support
 */
contract WorldtreeBackend {
    bytes21 public immutable roflApp;
    address public immutable backend;  // Authorized backend address
    
    struct User {
        address derivedAddress;     // Derived from World ID
        bytes32 worldIdHash;        // Hash of World ID for privacy
        bool registered;
        bytes32 snpDataHash;
        string walrusBlob;
        bool hasWalrusBackup;
        uint256 registrationTime;
    }
    
    struct AnalysisRequest {
        uint256 id;
        address requester;          // Derived address of requester
        address user1;
        address user2;
        bool user1Consented;
        bool user2Consented;
        string status;
        string result;
        uint256 requestTime;
        uint256 completionTime;
    }
    
    // Mapping from derived address to user data
    mapping(address => User) public users;
    
    // Mapping from World ID hash to derived address (for lookups)
    mapping(bytes32 => address) public worldIdToAddress;
    
    mapping(uint256 => AnalysisRequest) public analysisRequests;
    mapping(address => uint256[]) public userRequests;
    
    uint256 public nextRequestId;
    
    event UserRegistered(address indexed derivedAddress, bytes32 indexed worldIdHash);
    event AnalysisRequested(uint256 indexed id, address indexed requester);
    event ConsentGranted(uint256 indexed requestId, address indexed user);
    event AnalysisCompleted(uint256 indexed id);
    
    modifier onlyBackend() {
        require(msg.sender == backend, "Only backend can call");
        _;
    }
    
    modifier onlyBackendOrUser(address userAddress) {
        require(
            msg.sender == backend || msg.sender == userAddress,
            "Only backend or user can call"
        );
        _;
    }
    
    constructor(bytes21 _roflApp, address _backend) {
        roflApp = _roflApp;
        backend = _backend;
    }
    
    /**
     * @dev Register user on behalf (called by backend after World ID verification)
     * @param derivedAddress Address derived from World ID
     * @param worldIdHash Hash of World ID for privacy
     * @param snpDataHash Hash of user's SNP data
     */
    function registerUserFor(
        address derivedAddress,
        bytes32 worldIdHash,
        bytes32 snpDataHash
    ) external onlyBackend {
        require(!users[derivedAddress].registered, "Already registered");
        
        users[derivedAddress] = User({
            derivedAddress: derivedAddress,
            worldIdHash: worldIdHash,
            registered: true,
            snpDataHash: snpDataHash,
            walrusBlob: "",
            hasWalrusBackup: false,
            registrationTime: block.timestamp
        });
        
        worldIdToAddress[worldIdHash] = derivedAddress;
        
        emit UserRegistered(derivedAddress, worldIdHash);
    }
    
    /**
     * @dev Update Walrus backup on behalf of user
     */
    function addWalrusBackupFor(
        address userAddress,
        string memory walrusBlobId
    ) external onlyBackend {
        require(users[userAddress].registered, "Not registered");
        
        users[userAddress].walrusBlob = walrusBlobId;
        users[userAddress].hasWalrusBackup = true;
    }
    
    /**
     * @dev Request analysis on behalf of user
     */
    function requestAnalysisFor(
        address requesterAddress,
        address targetUserAddress
    ) external onlyBackend returns (uint256) {
        require(users[requesterAddress].registered, "Requester not registered");
        require(users[targetUserAddress].registered, "Target not registered");
        require(requesterAddress != targetUserAddress, "Cannot analyze self");
        
        uint256 requestId = nextRequestId++;
        
        analysisRequests[requestId] = AnalysisRequest({
            id: requestId,
            requester: requesterAddress,
            user1: requesterAddress,
            user2: targetUserAddress,
            user1Consented: true,  // Requester auto-consents
            user2Consented: false,
            status: "pending_consent",
            result: "",
            requestTime: block.timestamp,
            completionTime: 0
        });
        
        userRequests[requesterAddress].push(requestId);
        userRequests[targetUserAddress].push(requestId);
        
        emit AnalysisRequested(requestId, requesterAddress);
        
        return requestId;
    }
    
    /**
     * @dev Grant consent on behalf of user
     */
    function grantConsentFor(
        address userAddress,
        uint256 requestId,
        uint8 method,  // 1=direct, 2=walrus
        bytes memory encryptedKey
    ) external onlyBackend {
        AnalysisRequest storage req = analysisRequests[requestId];
        require(
            userAddress == req.user1 || userAddress == req.user2,
            "Not part of this analysis"
        );
        
        if (userAddress == req.user1) {
            req.user1Consented = true;
        } else {
            req.user2Consented = true;
        }
        
        emit ConsentGranted(requestId, userAddress);
        
        if (req.user1Consented && req.user2Consented) {
            req.status = "pending_analysis";
        }
        
        // Store encrypted key if using Walrus
        if (method == 2 && encryptedKey.length > 0) {
            // Store in separate mapping (not shown for brevity)
        }
    }
    
    /**
     * @dev Get pending analysis requests (for ROFL)
     */
    function getPendingRequests() external view returns (uint256[] memory) {
        uint256[] memory pending = new uint256[](nextRequestId);
        uint256 count = 0;
        
        for (uint256 i = 0; i < nextRequestId; i++) {
            if (keccak256(bytes(analysisRequests[i].status)) == 
                keccak256(bytes("pending_analysis"))) {
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
     * @dev ROFL submits analysis results
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
            keccak256(bytes(req.status)) == keccak256(bytes("pending_analysis")),
            "Invalid status"
        );
        
        req.status = "completed";
        req.result = result;
        req.completionTime = block.timestamp;
        
        emit AnalysisCompleted(requestId);
    }
    
    /**
     * @dev Get user requests
     */
    function getUserRequests(address userAddress) external view returns (uint256[] memory) {
        return userRequests[userAddress];
    }
    
    /**
     * @dev Lookup address by World ID hash
     */
    function getAddressByWorldId(bytes32 worldIdHash) external view returns (address) {
        return worldIdToAddress[worldIdHash];
    }
    
    /**
     * @dev Check if backend transaction or direct user transaction
     */
    function isBackendTransaction() external view returns (bool) {
        return msg.sender == backend;
    }
}
