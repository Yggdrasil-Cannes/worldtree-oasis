const { ethers } = require("hardhat");

async function main() {
  const CONTRACT_ADDRESS = "0xDF4A26832c770EeC30442337a4F9dd51bbC0a832";
  
  console.log("Monitoring Genetic Analysis Results...");
  console.log("Contract:", CONTRACT_ADDRESS);
  
  // Connect to contract
  const WorldtreeTest = await ethers.getContractFactory("WorldtreeTest");
  const contract = WorldtreeTest.attach(CONTRACT_ADDRESS);
  
  // Check multiple request IDs
  console.log("\n=== Checking Analysis Requests ===");
  
  for (let requestId = 0; requestId < 10; requestId++) {
    try {
      const request = await contract.getAnalysisRequest(requestId);
      
      // Skip if request doesn't exist (requester is zero address)
      if (request.requester === ethers.ZeroAddress) {
        continue;
      }
      
      console.log(`\nRequest ID ${requestId}:`);
      console.log("  Requester:", request.requester);
      console.log("  User1:", request.user1);
      console.log("  User2:", request.user2);
      console.log("  Status:", request.status);
      console.log("  Request Time:", new Date(Number(request.requestTime) * 1000).toISOString());
      
      if (request.status === "completed") {
        console.log("  Completion Time:", new Date(Number(request.completionTime) * 1000).toISOString());
        
        // Parse the result JSON
        try {
          const result = JSON.parse(request.result);
          console.log("  Analysis Result:");
          console.log("    Relationship:", result.relationship);
          console.log("    Confidence:", result.confidence * 100 + "%");
          console.log("    Common SNPs:", result.n_common_snps);
          console.log("    IBS Score:", result.ibs_analysis?.ibs_score);
          console.log("    IBS2 Percentage:", result.ibs2_percentage + "%");
          console.log("    PCA Distance:", result.pca_distance);
          console.log("    Recommendations:");
          result.recommendations?.forEach((rec, i) => {
            console.log(`      ${i + 1}. ${rec}`);
          });
        } catch (e) {
          console.log("  Result:", request.result);
        }
      } else if (request.status === "failed") {
        console.log("  Failure Reason:", request.result);
      }
      
      // Check for relationships
      const [user1] = await ethers.getSigners();
      const relationships = await contract.getUserRelationships(request.user1);
      if (relationships.length > 0) {
        console.log("  Created Relationships:", relationships.map(id => id.toString()).join(", "));
      }
      
    } catch (error) {
      // Request doesn't exist
      break;
    }
  }
  
  console.log("\n=== Summary ===");
  console.log("Use 'npx hardhat run scripts/test-genetic-analysis.js --network sapphire-testnet' to create new analysis requests");
  console.log("The ROFL app will automatically process pending requests and submit results");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
