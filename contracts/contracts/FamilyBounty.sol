// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Subcall} from "@oasisprotocol/sapphire-paratime/contracts/Subcall.sol";

/**
 * @title FamilyBounty
 * @dev Smart contract for managing family connection bounties and verification
 */
contract FamilyBounty {
    // ROFL app ID that can submit verifications
    address public immutable roflAppID;
    
    // Admin address
    address public admin;
    
    // Connection states
    enum ConnectionState {
        NONE,
        WEAK_LINK,      // Unverified claim
        ESTABLISHED     // ZK-verified (genetic or other proof)
    }
    
    struct Connection {
        address initiator;
        address relative;
        uint256 bounty;
        ConnectionState state;
        bytes32 zkProof;
        bytes metadata;  // Additional encrypted metadata
        uint256 createdAt;
        uint256 verifiedAt;
    }
    
    struct PendingClaim {
        address claimant;
        bytes32 connectionId;
        string evidence;  // IPFS hash or encrypted data reference
        uint256 timestamp;
    }
    
    // Mapping from connection ID to connection details
    mapping(bytes32 => Connection) public connections;
    
    // Mapping from address to their connection IDs
    mapping(address => bytes32[]) public userConnections;
    
    // Pending claims for connections
    mapping(bytes32 => PendingClaim[]) public pendingClaims;
    
    // Events
    event BountyCreated(
        bytes32 indexed connectionId,
        address indexed initiator,
        address indexed relative,
        uint256 bounty
    );
    
    event ConnectionVerified(
        bytes32 indexed connectionId,
        ConnectionState state,
        bytes32 zkProof
    );
    
    event ClaimSubmitted(
        bytes32 indexed connectionId,
        address indexed claimant,
        string evidence
    );
    
    event BountyClaimed(
        bytes32 indexed connectionId,
        address indexed claimant,
        uint256 amount
    );
    
    // Modifiers
    modifier onlyROFL() {
        Subcall.roflEnsureAuthorizedOrigin(roflAppID);
        _;
    }
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }
    
    constructor(address _roflAppID) {
        roflAppID = _roflAppID;
        admin = msg.sender;
    }
    
    /**
     * @dev Create a new family connection bounty
     * @param relative Address of the potential relative
     * @param metadata Encrypted metadata about the connection
     */
    function createBounty(
        address relative,
        bytes calldata metadata
    ) external payable {
        require(msg.value > 0, "Bounty must be greater than 0");
        require(relative != address(0), "Invalid relative address");
        require(relative != msg.sender, "Cannot create bounty for self");
        
        bytes32 connectionId = keccak256(
            abi.encodePacked(msg.sender, relative, block.timestamp)
        );
        
        require(
            connections[connectionId].initiator == address(0),
            "Connection already exists"
        );
        
        connections[connectionId] = Connection({
            initiator: msg.sender,
            relative: relative,
            bounty: msg.value,
            state: ConnectionState.WEAK_LINK,
            zkProof: bytes32(0),
            metadata: metadata,
            createdAt: block.timestamp,
            verifiedAt: 0
        });
        
        userConnections[msg.sender].push(connectionId);
        userConnections[relative].push(connectionId);
        
        emit BountyCreated(connectionId, msg.sender, relative, msg.value);
    }
    
    /**
     * @dev Submit a claim for a connection
     * @param connectionId The connection to claim
     * @param evidence IPFS hash or reference to evidence
     */
    function submitClaim(
        bytes32 connectionId,
        string calldata evidence
    ) external {
        Connection storage connection = connections[connectionId];
        require(connection.initiator != address(0), "Connection does not exist");
        require(
            msg.sender == connection.relative || 
            msg.sender == connection.initiator,
            "Not part of this connection"
        );
        
        pendingClaims[connectionId].push(PendingClaim({
            claimant: msg.sender,
            connectionId: connectionId,
            evidence: evidence,
            timestamp: block.timestamp
        }));
        
        emit ClaimSubmitted(connectionId, msg.sender, evidence);
    }
    
    /**
     * @dev Submit verification from ROFL app
     * @param connectionId Connection to verify
     * @param zkProof Zero-knowledge proof of relationship
     * @param isGenetic Whether this is genetic verification
     */
    function submitVerification(
        bytes32 connectionId,
        bytes32 zkProof,
        bool isGenetic
    ) external onlyROFL {
        Connection storage connection = connections[connectionId];
        require(connection.initiator != address(0), "Connection does not exist");
        require(
            connection.state != ConnectionState.ESTABLISHED,
            "Already verified"
        );
        
        connection.zkProof = zkProof;
        connection.state = ConnectionState.ESTABLISHED;
        connection.verifiedAt = block.timestamp;
        
        emit ConnectionVerified(
            connectionId,
            ConnectionState.ESTABLISHED,
            zkProof
        );
    }
    
    /**
     * @dev Claim bounty for verified connection
     * @param connectionId Connection with bounty to claim
     */
    function claimBounty(bytes32 connectionId) external {
        Connection storage connection = connections[connectionId];
        require(
            connection.state == ConnectionState.ESTABLISHED,
            "Connection not verified"
        );
        require(
            msg.sender == connection.relative,
            "Only relative can claim"
        );
        require(connection.bounty > 0, "No bounty to claim");
        
        uint256 bountyAmount = connection.bounty;
        connection.bounty = 0;
        
        (bool success, ) = msg.sender.call{value: bountyAmount}("");
        require(success, "Transfer failed");
        
        emit BountyClaimed(connectionId, msg.sender, bountyAmount);
    }
    
    /**
     * @dev Get user's connections
     * @param user Address to query
     */
    function getUserConnections(address user) 
        external 
        view 
        returns (bytes32[] memory) 
    {
        return userConnections[user];
    }
    
    /**
     * @dev Get pending claims for a connection
     * @param connectionId Connection to query
     */
    function getPendingClaims(bytes32 connectionId)
        external
        view
        returns (PendingClaim[] memory)
    {
        return pendingClaims[connectionId];
    }
    
    /**
     * @dev Update ROFL app ID (admin only)
     * @param newRoflAppID New ROFL app ID
     */
    function updateAdmin(address newAdmin) external onlyAdmin {
        admin = newAdmin;
    }
}
