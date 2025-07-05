// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@oasisprotocol/sapphire-contracts/contracts/Subcall.sol";

contract WorldtreeTest {
    // ROFL app authorized to submit genetic matches
    bytes21 public immutable roflApp;
    
    // Structures
    struct User {
        address wallet;
        bool registered;
        string snpData; // Direct SNP data for testing (not encrypted)
        uint256 registrationTime;
    }
    
    struct Relationship {
        address user1;
        address user2;
        string relationshipType; // "parent-child", "siblings", "cousins", etc.
        uint256 confidence; // 0-100 percentage
        uint256 establishedTime;
        bool confirmed; // Both parties agreed
    }
    
    struct GeneticAnalysisRequest {
        uint256 id;
        address requester;
        address user1;
        address user2;
        string status; // "pending", "processing", "completed", "failed"
        string result; // JSON result from ROFL analysis
        uint256 requestTime;
        uint256 completionTime;
    }
    
    // State variables
    mapping(address => User) public users;
    mapping(uint256 => Relationship) public relationships;
    mapping(uint256 => GeneticAnalysisRequest) public analysisRequests;
    mapping(address => uint256[]) public userRelationships;
    mapping(address => uint256[]) public userAnalysisRequests;
    
    uint256 public nextRelationshipId;
    uint256 public nextRequestId;
    
    // Events
    event UserRegistered(address indexed user);
    event RelationshipProposed(uint256 indexed id, address user1, address user2, string relationshipType);
    event RelationshipConfirmed(uint256 indexed id);
    event GeneticMatchSubmitted(address user1, address user2, uint256 confidence, string relationship);
    event AnalysisRequested(uint256 indexed id, address requester, address user1, address user2);
    event AnalysisCompleted(uint256 indexed id, string result);
    
    constructor(bytes21 _roflApp) {
        roflApp = _roflApp;
    }
    
    // Register user with direct SNP data (for testing)
    function registerUser(string memory snpData) external {
        require(bytes(snpData).length > 0, "SNP data required");
        
        users[msg.sender] = User({
            wallet: msg.sender,
            registered: true,
            snpData: snpData,
            registrationTime: block.timestamp
        });
        
        emit UserRegistered(msg.sender);
    }
    
    // Update user's SNP data
    function updateSNPData(string memory newSnpData) external {
        require(users[msg.sender].registered, "User not registered");
        users[msg.sender].snpData = newSnpData;
    }
    
    // Request genetic analysis between two registered users
    function requestAnalysis(address user1, address user2) external returns (uint256) {
        require(users[user1].registered, "User1 not registered");
        require(users[user2].registered, "User2 not registered");
        require(user1 != user2, "Cannot analyze same user");
        
        uint256 requestId = nextRequestId++;
        
        analysisRequests[requestId] = GeneticAnalysisRequest({
            id: requestId,
            requester: msg.sender,
            user1: user1,
            user2: user2,
            status: "pending",
            result: "",
            requestTime: block.timestamp,
            completionTime: 0
        });
        
        userAnalysisRequests[msg.sender].push(requestId);
        
        emit AnalysisRequested(requestId, msg.sender, user1, user2);
        
        return requestId;
    }
    
    // Get pending analysis requests (for ROFL app to poll)
    function getPendingRequests() external view returns (uint256[] memory) {
        uint256[] memory pending = new uint256[](nextRequestId);
        uint256 count = 0;
        
        for (uint256 i = 0; i < nextRequestId; i++) {
            if (keccak256(bytes(analysisRequests[i].status)) == keccak256(bytes("pending"))) {
                pending[count] = i;
                count++;
            }
        }
        
        // Resize array to actual count
        uint256[] memory result = new uint256[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = pending[i];
        }
        
        return result;
    }
    
    // Get SNP data for analysis (only callable by ROFL app)
    function getSNPDataForAnalysis(uint256 requestId) external view returns (
        string memory user1SNP,
        string memory user2SNP
    ) {
        // Only ROFL app can access SNP data
        Subcall.roflEnsureAuthorizedOrigin(roflApp);
        
        GeneticAnalysisRequest memory req = analysisRequests[requestId];
        require(req.id == requestId, "Invalid request");
        
        return (
            users[req.user1].snpData,
            users[req.user2].snpData
        );
    }
    
    // ROFL app submits analysis results
    function submitAnalysisResult(
        uint256 requestId,
        string memory result,
        uint256 confidence,
        string memory relationshipType
    ) external {
        // Only ROFL app can submit results
        Subcall.roflEnsureAuthorizedOrigin(roflApp);
        
        GeneticAnalysisRequest storage req = analysisRequests[requestId];
        require(keccak256(bytes(req.status)) == keccak256(bytes("pending")), "Request not pending");
        
        // Update analysis request
        req.status = "completed";
        req.result = result;
        req.completionTime = block.timestamp;
        
        // Create relationship if confidence is high enough
        if (confidence >= 50) {
            uint256 relationshipId = nextRelationshipId++;
            
            relationships[relationshipId] = Relationship({
                user1: req.user1,
                user2: req.user2,
                relationshipType: relationshipType,
                confidence: confidence,
                establishedTime: block.timestamp,
                confirmed: false
            });
            
            userRelationships[req.user1].push(relationshipId);
            userRelationships[req.user2].push(relationshipId);
            
            emit RelationshipProposed(relationshipId, req.user1, req.user2, relationshipType);
            emit GeneticMatchSubmitted(req.user1, req.user2, confidence, relationshipType);
        }
        
        emit AnalysisCompleted(requestId, result);
    }
    
    // Mark analysis as failed (only callable by ROFL app)
    function markAnalysisFailed(uint256 requestId, string memory reason) external {
        // Only ROFL app can mark as failed
        Subcall.roflEnsureAuthorizedOrigin(roflApp);
        
        GeneticAnalysisRequest storage req = analysisRequests[requestId];
        require(keccak256(bytes(req.status)) == keccak256(bytes("pending")), "Request not pending");
        
        req.status = "failed";
        req.result = reason;
        req.completionTime = block.timestamp;
        
        emit AnalysisCompleted(requestId, reason);
    }
    
    // Users confirm relationships (handshake)
    function confirmRelationship(uint256 relationshipId) external {
        Relationship storage rel = relationships[relationshipId];
        require(rel.user1 == msg.sender || rel.user2 == msg.sender, "Not part of relationship");
        require(!rel.confirmed, "Already confirmed");
        
        // For simplicity, we'll confirm immediately
        // In production, track confirmations from both parties
        rel.confirmed = true;
        
        emit RelationshipConfirmed(relationshipId);
    }
    
    // View functions
    function getUserRelationships(address user) external view returns (uint256[] memory) {
        return userRelationships[user];
    }
    
    function getUserAnalysisRequests(address user) external view returns (uint256[] memory) {
        return userAnalysisRequests[user];
    }
    
    function getRelationshipDetails(uint256 relationshipId) external view returns (
        address user1,
        address user2,
        string memory relationshipType,
        uint256 confidence,
        bool confirmed
    ) {
        Relationship memory rel = relationships[relationshipId];
        return (
            rel.user1,
            rel.user2,
            rel.relationshipType,
            rel.confidence,
            rel.confirmed
        );
    }
    
    function getAnalysisRequest(uint256 requestId) external view returns (
        address requester,
        address user1,
        address user2,
        string memory status,
        string memory result,
        uint256 requestTime,
        uint256 completionTime
    ) {
        GeneticAnalysisRequest memory req = analysisRequests[requestId];
        return (
            req.requester,
            req.user1,
            req.user2,
            req.status,
            req.result,
            req.requestTime,
            req.completionTime
        );
    }
}
