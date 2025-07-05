const { ethers } = require("hardhat");

async function main() {
    console.log("Monitoring genetic analysis requests...");
    
    // Get contract instance
    const contractAddress = "0x614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3";
    const contractABI = [
        "function getPendingRequests() external view returns (uint256[] memory)",
        "function getAnalysisRequest(uint256 requestId) external view returns (address, address, address, string, string, uint256, uint256)",
        "function getSNPDataForAnalysis(uint256 requestId) external view returns (string, string)"
    ];
    
    const [signer] = await ethers.getSigners();
    const contract = new ethers.Contract(contractAddress, contractABI, signer);
    
    console.log("Contract address:", contractAddress);
    console.log("Signer address:", signer.address);
    
    // Check pending requests
    console.log("\n=== Checking Pending Requests ===");
    try {
        const pendingRequests = await contract.getPendingRequests();
        console.log("Pending requests:", pendingRequests.map(id => id.toString()));
        
        if (pendingRequests.length > 0) {
            for (const requestId of pendingRequests) {
                console.log(`\n--- Request ${requestId} ---`);
                
                // Get request details
                const requestDetails = await contract.getAnalysisRequest(requestId);
                console.log("Requester:", requestDetails[0]);
                console.log("User 1:", requestDetails[1]);
                console.log("User 2:", requestDetails[2]);
                console.log("Status:", requestDetails[3]);
                console.log("Result:", requestDetails[4]);
                console.log("Request time:", new Date(Number(requestDetails[5]) * 1000).toLocaleString());
                console.log("Completion time:", requestDetails[6] > 0 ? new Date(Number(requestDetails[6]) * 1000).toLocaleString() : "Not completed");
                
                // Try to get SNP data (this will fail if not called by ROFL app)
                try {
                    const snpData = await contract.getSNPDataForAnalysis(requestId);
                    console.log("User 1 SNP data length:", snpData[0].length);
                    console.log("User 2 SNP data length:", snpData[1].length);
                    console.log("User 1 SNP preview:", snpData[0].substring(0, 100) + "...");
                    console.log("User 2 SNP preview:", snpData[1].substring(0, 100) + "...");
                } catch (error) {
                    console.log("SNP data access:", error.message);
                    console.log("(This is expected - only ROFL app can access SNP data)");
                }
            }
        } else {
            console.log("No pending requests found");
        }
    } catch (error) {
        console.error("Error checking pending requests:", error.message);
    }
    
    console.log("\n=== Monitoring Complete ===");
    console.log("The ROFL service should be able to:");
    console.log("1. Get pending requests using getPendingRequests()");
    console.log("2. Access SNP data using getSNPDataForAnalysis() (ROFL-only)");
    console.log("3. Submit results using submitAnalysisResult()");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    }); 