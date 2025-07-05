// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@oasisprotocol/sapphire-contracts/contracts/Subcall.sol";

/**
 * @title WorldtreeWalrus
 * @dev Privacy-preserving genetic analysis with local storage and Walrus backup
 */
contract WorldtreeWalrus {
    bytes21 public immutable roflApp;
    
    struct User {
        address wallet;
        bool registered;
        bytes32 snpDataHash;           // Hash of the SNP data for verification
        string walrusBlob;             // Optional: Walrus blob ID if user chose to backup
        bool hasWalrusBackup;          // Whether data is on Walrus
        uint256 registrationTime;
    }
    
    struct AnalysisRequest {
        uint256 id;
        address requester;
        address user1;
        address user2;
        bool user1Consented;
        bool user2Consented;
        DataSubmissionMethod user1Method;  // How user1 will provide data
        DataSubmissionMethod user2Method;  // How user2 will provide data
        string status;
        string result;
        uint256 requestTime;
        uint256 completionTime;
    }
    
    enum DataSubmissionMethod {
        NotSpecified,
        DirectUpload,      // User will upload directly to ROFL during session
        WalrusRetrieval,   // ROFL will retrieve from Walrus
        EncryptedLink      // User provides encrypted data URL
    }
    
    struct TemporaryDataGrant {
        uint256 requestId;
        address grantedTo;
        uint256 expiryTime;
        bytes encryptedWalrusKey;  // If using Walrus, key to decrypt
        string encryptedDataUrl;   // If direct upload, temporary URL
    }
    
    mapping(address => User) public users;
    mapping(uint256 => AnalysisRequest) public analysisRequests;
    mapping(address => mapping(uint256 => TemporaryDataGrant)) public dataGrants;
    mapping(address => uint256[]) public userRequests;
    
    // For direct upload sessions
    mapping(uint256 => mapping(address => bytes32)) public sessionDataHashes;
    mapping(uint256 => mapping(address => bool)) public dataUploaded;
    
    uint256 public nextRequestId;
    
    event UserRegistered(address indexed user, bool hasWalrusBackup);
    event AnalysisRequested(uint256 indexed id, address indexed requester);
    event ConsentGranted(uint256 indexed requestId, address indexed user, DataSubmissionMethod method);
    event DataUploaded(uint256 indexed requestId, address indexed user, bytes32 dataHash);
    event AnalysisCompleted(uint256 indexed id);
    
    constructor(bytes21 _roflApp) {
        roflApp = _roflApp;
    }
    
    /**
     * @dev Register user without uploading data (data stays local)
     * @param snpDataHash Hash of the user's local SNP data
     */
    function registerUser(bytes32 snpDataHash) external {
        users[msg.sender] = User({
            wallet: msg.sender,
            registered: true,
            snpDataHash: snpDataHash,
            walrusBlob: "",
            hasWalrusBackup: false,
            registrationTime: block.timestamp
        });
        
        emit UserRegistered(msg.sender, false);
    }
    
    /**
     * @dev Update registration with Walrus backup info
     * @param walrusBlobId The Walrus blob ID where encrypted data is stored
     */
    function addWalrusBackup(string memory walrusBlobId) external {
        require(users[msg.sender].registered, "Not registered");
        
        users[msg.sender].walrusBlob = walrusBlobId;
        users[msg.sender].hasWalrusBackup = true;
    }
    
    /**
     * @dev Request analysis between two users
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
            user1Consented: (msg.sender == user1),
            user2Consented: (msg.sender == user2),
            user1Method: DataSubmissionMethod.NotSpecified,
            user2Method: DataSubmissionMethod.NotSpecified,
            status: "pending_consent",
            result: "",
            requestTime: block.timestamp,
            completionTime: 0
        });
        
        userRequests[user1].push(requestId);
        if (user1 != user2) {
            userRequests[user2].push(requestId);
        }
        
        emit AnalysisRequested(requestId, msg.sender);
        
        return requestId;
    }
    
    /**
     * @dev Grant consent and specify how data will be provided
     * @param requestId The analysis request ID
     * @param method How the user will provide their data
     * @param encryptedWalrusKey If using Walrus, encryption key for ROFL
     */
    function grantConsent(
        uint256 requestId,
        DataSubmissionMethod method,
        bytes memory encryptedWalrusKey
    ) external {
        AnalysisRequest storage req = analysisRequests[requestId];
        require(
            msg.sender == req.user1 || msg.sender == req.user2,
            "Not part of this analysis"
        );
        require(
            method != DataSubmissionMethod.NotSpecified,
            "Must specify data submission method"
        );
        
        // If using Walrus, must have backup
        if (method == DataSubmissionMethod.WalrusRetrieval) {
            require(users[msg.sender].hasWalrusBackup, "No Walrus backup found");
            require(encryptedWalrusKey.length > 0, "Must provide encryption key");
        }
        
        // Update consent and method
        if (msg.sender == req.user1) {
            req.user1Consented = true;
            req.user1Method = method;
        } else {
            req.user2Consented = true;
            req.user2Method = method;
        }
        
        // Store grant if using Walrus
        if (method == DataSubmissionMethod.WalrusRetrieval) {
            dataGrants[msg.sender][requestId] = TemporaryDataGrant({
                requestId: requestId,
                grantedTo: address(uint160(uint256(roflApp))),
                expiryTime: block.timestamp + 24 hours,
                encryptedWalrusKey: encryptedWalrusKey,
                encryptedDataUrl: users[msg.sender].walrusBlob
            });
        }
        
        emit ConsentGranted(requestId, msg.sender, method);
        
        // Update status based on consent state
        if (req.user1Consented && req.user2Consented) {
            // Check if both chose direct upload
            if (req.user1Method == DataSubmissionMethod.DirectUpload && 
                req.user2Method == DataSubmissionMethod.DirectUpload) {
                req.status = "awaiting_uploads";
            } else {
                req.status = "pending_analysis";
            }
        }
    }
    
    /**
     * @dev ROFL acknowledges receiving direct upload data
     * @param requestId The analysis request
     * @param user The user who uploaded
     * @param dataHash Hash of received data for verification
     */
    function confirmDataUpload(
        uint256 requestId,
        address user,
        bytes32 dataHash
    ) external {
        Subcall.roflEnsureAuthorizedOrigin(roflApp);
        
        AnalysisRequest storage req = analysisRequests[requestId];
        require(
            user == req.user1 || user == req.user2,
            "User not part of request"
        );
        
        // Verify hash matches registered data
        require(users[user].snpDataHash == dataHash, "Data hash mismatch");
        
        sessionDataHashes[requestId][user] = dataHash;
        dataUploaded[requestId][user] = true;
        
        emit DataUploaded(requestId, user, dataHash);
        
        // Check if both uploads complete
        if (dataUploaded[requestId][req.user1] && 
            dataUploaded[requestId][req.user2]) {
            req.status = "pending_analysis";
        }
    }
    
    /**
     * @dev Get requests ready for analysis
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
     * @dev ROFL retrieves data access information
     */
    function getDataAccessInfo(uint256 requestId) external view returns (
        DataSubmissionMethod user1Method,
        DataSubmissionMethod user2Method,
        string memory user1WalrusBlob,
        string memory user2WalrusBlob,
        bytes memory user1Key,
        bytes memory user2Key
    ) {
        Subcall.roflEnsureAuthorizedOrigin(roflApp);
        
        AnalysisRequest memory req = analysisRequests[requestId];
        
        user1Method = req.user1Method;
        user2Method = req.user2Method;
        
        // Provide Walrus info if applicable
        if (req.user1Method == DataSubmissionMethod.WalrusRetrieval) {
            user1WalrusBlob = users[req.user1].walrusBlob;
            user1Key = dataGrants[req.user1][requestId].encryptedWalrusKey;
        }
        
        if (req.user2Method == DataSubmissionMethod.WalrusRetrieval) {
            user2WalrusBlob = users[req.user2].walrusBlob;
            user2Key = dataGrants[req.user2][requestId].encryptedWalrusKey;
        }
    }
    
    /**
     * @dev Submit analysis results
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
            keccak256(bytes(req.status)) == keccak256(bytes("pending_analysis")) ||
            keccak256(bytes(req.status)) == keccak256(bytes("processing")),
            "Invalid status"
        );
        
        req.status = "completed";
        req.result = result;
        req.completionTime = block.timestamp;
        
        // Clean up temporary data
        delete dataGrants[req.user1][requestId];
        delete dataGrants[req.user2][requestId];
        delete sessionDataHashes[requestId][req.user1];
        delete sessionDataHashes[requestId][req.user2];
        delete dataUploaded[requestId][req.user1];
        delete dataUploaded[requestId][req.user2];
        
        emit AnalysisCompleted(requestId);
    }
    
    /**
     * @dev Check if a user has local data only or Walrus backup
     */
    function getUserStorageInfo(address user) external view returns (
        bool registered,
        bool hasLocalOnly,
        bool hasWalrusBackup,
        string memory walrusBlobId
    ) {
        User memory u = users[user];
        return (
            u.registered,
            u.registered && !u.hasWalrusBackup,
            u.hasWalrusBackup,
            u.walrusBlob
        );
    }
}
