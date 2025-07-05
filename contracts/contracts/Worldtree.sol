// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@oasisprotocol/sapphire-contracts/contracts/Subcall.sol";

contract Worldtree {
    // ROFL app authorized to submit genetic matches
    bytes21 public immutable roflApp;
    
    // Worldcoin integration (simplified for now)
    address public immutable worldcoinVerifier;
    
    // Structures
    struct User {
        address wallet;
        bool worldcoinVerified;
        string encryptedGeneticDataCID; // Walrus CID for encrypted genetic data
        uint256 registrationTime;
    }
    
    struct Relationship {
        address user1;
        address user2;
        string relationshipType; // "parent-child", "siblings", "cousins", etc.
        uint256 confidence; // 0-100 percentage
        uint256 establishedTime;
        bool confirmed; // Both parties agreed
        bool bountyPaid;
    }
    
    struct Bounty {
        address creator;
        uint256 amount;
        string relationshipCriteria;
        uint256 deadline;
        bool claimed;
    }
    
    // State variables
    mapping(address => User) public users;
    mapping(uint256 => Relationship) public relationships;
    mapping(uint256 => Bounty) public bounties;
    mapping(address => uint256[]) public userRelationships;
    mapping(address => uint256[]) public userBounties;
    
    uint256 public nextRelationshipId;
    uint256 public nextBountyId;
    
    // Events
    event UserRegistered(address indexed user, string geneticDataCID);
    event RelationshipProposed(uint256 indexed id, address user1, address user2, string relationshipType);
    event RelationshipConfirmed(uint256 indexed id);
    event BountyCreated(uint256 indexed id, address creator, uint256 amount, string criteria);
    event BountyClaimed(uint256 indexed id, address claimant);
    event GeneticMatchSubmitted(address user1, address user2, uint256 confidence, string relationship);
    
    constructor(bytes21 _roflApp, address _worldcoinVerifier) {
        roflApp = _roflApp;
        worldcoinVerifier = _worldcoinVerifier;
    }
    
    // Register user with Worldcoin verification
    function registerUser(
        string memory encryptedGeneticDataCID,
        bytes memory worldcoinProof
    ) external {
        // Verify Worldcoin proof (simplified - in production use proper verification)
        require(worldcoinProof.length > 0, "Worldcoin proof required");
        
        users[msg.sender] = User({
            wallet: msg.sender,
            worldcoinVerified: true,
            encryptedGeneticDataCID: encryptedGeneticDataCID,
            registrationTime: block.timestamp
        });
        
        emit UserRegistered(msg.sender, encryptedGeneticDataCID);
    }
    
    // ROFL app submits genetic match results
    function submitGeneticMatch(
        address user1,
        address user2,
        uint256 confidence,
        string memory relationshipType
    ) external {
        // Only ROFL app can submit matches
        Subcall.roflEnsureAuthorizedOrigin(roflApp);
        
        require(users[user1].wallet != address(0), "User1 not registered");
        require(users[user2].wallet != address(0), "User2 not registered");
        
        uint256 relationshipId = nextRelationshipId++;
        
        relationships[relationshipId] = Relationship({
            user1: user1,
            user2: user2,
            relationshipType: relationshipType,
            confidence: confidence,
            establishedTime: block.timestamp,
            confirmed: false,
            bountyPaid: false
        });
        
        userRelationships[user1].push(relationshipId);
        userRelationships[user2].push(relationshipId);
        
        emit RelationshipProposed(relationshipId, user1, user2, relationshipType);
        emit GeneticMatchSubmitted(user1, user2, confidence, relationshipType);
        
        // Check if this fulfills any bounties
        _checkBountyFulfillment(relationshipId);
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
    
    // Create a bounty for finding relatives
    function createBounty(string memory relationshipCriteria, uint256 deadline) external payable {
        require(msg.value > 0, "Bounty must have value");
        require(deadline > block.timestamp, "Deadline must be in future");
        
        uint256 bountyId = nextBountyId++;
        
        bounties[bountyId] = Bounty({
            creator: msg.sender,
            amount: msg.value,
            relationshipCriteria: relationshipCriteria,
            deadline: deadline,
            claimed: false
        });
        
        userBounties[msg.sender].push(bountyId);
        
        emit BountyCreated(bountyId, msg.sender, msg.value, relationshipCriteria);
    }
    
    // Internal function to check bounty fulfillment
    function _checkBountyFulfillment(uint256 relationshipId) internal {
        Relationship memory rel = relationships[relationshipId];
        
        // Check all bounties created by either user
        for (uint256 i = 0; i < userBounties[rel.user1].length; i++) {
            _processBounty(userBounties[rel.user1][i], relationshipId);
        }
        
        for (uint256 i = 0; i < userBounties[rel.user2].length; i++) {
            _processBounty(userBounties[rel.user2][i], relationshipId);
        }
    }
    
    function _processBounty(uint256 bountyId, uint256 relationshipId) internal {
        Bounty storage bounty = bounties[bountyId];
        if (bounty.claimed || block.timestamp > bounty.deadline) return;
        
        Relationship memory rel = relationships[relationshipId];
        
        // Simple criteria matching (in production, use more sophisticated matching)
        if (keccak256(bytes(bounty.relationshipCriteria)) == keccak256(bytes(rel.relationshipType))) {
            bounty.claimed = true;
            relationships[relationshipId].bountyPaid = true;
            
            // Pay bounty to the other party
            address payTo = rel.user1 == bounty.creator ? rel.user2 : rel.user1;
            payable(payTo).transfer(bounty.amount);
            
            emit BountyClaimed(bountyId, payTo);
        }
    }
    
    // View functions
    function getUserRelationships(address user) external view returns (uint256[] memory) {
        return userRelationships[user];
    }
    
    function getUserBounties(address user) external view returns (uint256[] memory) {
        return userBounties[user];
    }
    
    function getRelationshipDetails(uint256 relationshipId) external view returns (
        address user1,
        address user2,
        string memory relationshipType,
        uint256 confidence,
        bool confirmed,
        bool bountyPaid
    ) {
        Relationship memory rel = relationships[relationshipId];
        return (
            rel.user1,
            rel.user2,
            rel.relationshipType,
            rel.confidence,
            rel.confirmed,
            rel.bountyPaid
        );
    }
}
