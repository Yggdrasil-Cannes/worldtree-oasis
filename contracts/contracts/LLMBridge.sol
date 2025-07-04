// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@oasisprotocol/sapphire-contracts/contracts/Subcall.sol";

contract LLMBridge {
    // The ROFL app that's authorized to submit responses
    bytes21 public immutable roflApp;
    
    // Request structure
    struct Request {
        address requester;
        string prompt;
        uint256 timestamp;
        bool fulfilled;
        string response;
    }
    
    // Mapping from request ID to request data
    mapping(uint256 => Request) public requests;
    
    // Current request ID counter
    uint256 public nextRequestId;
    
    // Events
    event RequestCreated(uint256 indexed requestId, address indexed requester, string prompt);
    event ResponseSubmitted(uint256 indexed requestId, string response);
    
    // Constructor to set the authorized ROFL app
    constructor(bytes21 _roflApp) {
        roflApp = _roflApp;
    }
    
    // Create a new LLM request
    function createRequest(string memory prompt) external returns (uint256) {
        uint256 requestId = nextRequestId++;
        
        requests[requestId] = Request({
            requester: msg.sender,
            prompt: prompt,
            timestamp: block.timestamp,
            fulfilled: false,
            response: ""
        });
        
        emit RequestCreated(requestId, msg.sender, prompt);
        return requestId;
    }
    
    // Submit a response (only callable by the authorized ROFL app)
    function submitResponse(uint256 requestId, string memory response) external {
        // Ensure the caller is the authorized ROFL app
        Subcall.roflEnsureAuthorizedOrigin(roflApp);
        
        Request storage request = requests[requestId];
        require(!request.fulfilled, "Request already fulfilled");
        require(request.requester != address(0), "Request does not exist");
        
        request.response = response;
        request.fulfilled = true;
        
        emit ResponseSubmitted(requestId, response);
    }
    
    // Get unfulfilled request IDs (for ROFL app to poll)
    function getUnfulfilledRequests(uint256 limit) external view returns (uint256[] memory) {
        uint256 count = 0;
        
        // First, count unfulfilled requests
        for (uint256 i = 0; i < nextRequestId; i++) {
            if (!requests[i].fulfilled && requests[i].requester != address(0)) {
                count++;
                if (count >= limit) break;
            }
        }
        
        // Create array with the right size
        uint256[] memory unfulfilledIds = new uint256[](count);
        uint256 index = 0;
        
        // Fill the array
        for (uint256 i = 0; i < nextRequestId && index < count; i++) {
            if (!requests[i].fulfilled && requests[i].requester != address(0)) {
                unfulfilledIds[index++] = i;
            }
        }
        
        return unfulfilledIds;
    }
    
    // Get request details
    function getRequest(uint256 requestId) external view returns (
        address requester,
        string memory prompt,
        uint256 timestamp,
        bool fulfilled,
        string memory response
    ) {
        Request memory request = requests[requestId];
        return (
            request.requester,
            request.prompt,
            request.timestamp,
            request.fulfilled,
            request.response
        );
    }
}
