const { ethers } = require("hardhat");
const fs = require('fs');

async function main() {
    console.log("Testing full genetic analysis workflow...");
    
    // Load test wallets
    let walletInfo;
    try {
        walletInfo = JSON.parse(fs.readFileSync('test-wallets.json', 'utf8'));
    } catch (error) {
        console.error("Could not load test-wallets.json. Please run create-test-wallets.js first.");
        process.exit(1);
    }
    
    // Connect wallets to provider
    const wallet1 = new ethers.Wallet(walletInfo.wallet1.privateKey, ethers.provider);
    const wallet2 = new ethers.Wallet(walletInfo.wallet2.privateKey, ethers.provider);
    
    console.log("User 1 address:", wallet1.address);
    console.log("User 2 address:", wallet2.address);
    
    // Get contract instance with correct ABI
    const contractAddress = "0x614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3";
    const contractABI = [
        "function registerUser(string memory snpData) external",
        "function requestAnalysis(address user1, address user2) external returns (uint256)",
        "function getAnalysisRequest(uint256 requestId) external view returns (address, address, address, string, string, uint256, uint256)",
        "function getPendingRequests() external view returns (uint256[] memory)",
        "function users(address) external view returns (address, bool, string, uint256)"
    ];
    
    const contract1 = new ethers.Contract(contractAddress, contractABI, wallet1);
    const contract2 = new ethers.Contract(contractAddress, contractABI, wallet2);
    
    // Sample SNP data (200 SNPs each for better analysis)
    const snpData1 = generateSNPData(200, "user1");
    const snpData2 = generateSNPData(200, "user2");
    
    console.log("\n=== Step 1: Register User 1 ===");
    try {
        const tx1 = await contract1.registerUser(snpData1);
        await tx1.wait();
        console.log("User 1 registered successfully");
        console.log("Transaction hash:", tx1.hash);
    } catch (error) {
        console.error("Error registering user 1:", error.message);
    }
    
    console.log("\n=== Step 2: Register User 2 ===");
    try {
        const tx2 = await contract2.registerUser(snpData2);
        await tx2.wait();
        console.log("User 2 registered successfully");
        console.log("Transaction hash:", tx2.hash);
    } catch (error) {
        console.error("Error registering user 2:", error.message);
    }
    
    // Verify registrations
    console.log("\n=== Step 3: Verify Registrations ===");
    try {
        const user1Data = await contract1.users(wallet1.address);
        const user2Data = await contract1.users(wallet2.address);
        
        console.log("User 1 registered:", user1Data[1]); // bool registered
        console.log("User 2 registered:", user2Data[1]); // bool registered
        
        if (!user1Data[1] || !user2Data[1]) {
            console.error("One or both users not registered. Stopping test.");
            return;
        }
    } catch (error) {
        console.error("Error verifying registrations:", error.message);
        return;
    }
    
    console.log("\n=== Step 4: Request Genetic Analysis ===");
    let requestId;
    try {
        const tx3 = await contract1.requestAnalysis(wallet1.address, wallet2.address);
        const receipt = await tx3.wait();
        
        console.log("Analysis request submitted");
        console.log("Transaction hash:", tx3.hash);
        console.log("Gas used:", receipt.gasUsed.toString());
        
        // Extract request ID from events
        const events = receipt.logs;
        console.log("Events logged:", events.length);
        
        // The request ID should be the return value, but we can also get it from nextRequestId - 1
        // For now, let's check the latest request
        
    } catch (error) {
        console.error("Error requesting analysis:", error.message);
    }
    
    console.log("\n=== Step 5: Check Pending Requests ===");
    try {
        const pendingRequests = await contract1.getPendingRequests();
        console.log("Pending requests:", pendingRequests.map(id => id.toString()));
        
        if (pendingRequests.length > 0) {
            requestId = pendingRequests[pendingRequests.length - 1]; // Get the latest request
            console.log("Latest request ID:", requestId.toString());
            
            // Get request details
            const requestDetails = await contract1.getAnalysisRequest(requestId);
            console.log("Request details:");
            console.log("  Requester:", requestDetails[0]);
            console.log("  User 1:", requestDetails[1]);
            console.log("  User 2:", requestDetails[2]);
            console.log("  Status:", requestDetails[3]);
            console.log("  Result:", requestDetails[4]);
            console.log("  Request time:", new Date(Number(requestDetails[5]) * 1000).toLocaleString());
        }
    } catch (error) {
        console.error("Error checking pending requests:", error.message);
    }
    
    console.log("\n=== Test Complete ===");
    console.log("The ROFL service should now process the genetic analysis request.");
    console.log("Check the ROFL logs to see if the analysis is being processed.");
    console.log("You can monitor the request by checking the contract state periodically.");
}

function generateSNPData(count, seed) {
    // Generate deterministic but different SNP data for each user
    const snps = [];
    const chromosomes = Array.from({length: 22}, (_, i) => i + 1); // 1-22
    
    for (let i = 0; i < count; i++) {
        const chr = chromosomes[i % chromosomes.length];
        const pos = 1000000 + (i * 1000) + (seed === "user1" ? 0 : 500); // Offset for user2
        
        // Generate genotype with some variation
        let genotype;
        if (seed === "user1") {
            genotype = i % 3 === 0 ? "AA" : i % 3 === 1 ? "AB" : "BB";
        } else {
            genotype = i % 3 === 0 ? "AB" : i % 3 === 1 ? "BB" : "AA";
        }
        
        snps.push(`rs${1000000 + i}\t${chr}\t${pos}\t${genotype}`);
    }
    
    return snps.join('\n');
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    }); 