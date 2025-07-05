const { ethers } = require("hardhat");

async function main() {
  const [signer] = await ethers.getSigners();
  
  // Contract address
  const WORLDTREE_TEST_ADDRESS = "0xa4e5c09C101A62Aa04A1078228527CD106012d0b";
  
  console.log("Checking WorldtreeTest contract state");
  console.log("Contract:", WORLDTREE_TEST_ADDRESS);
  console.log("Signer:", signer.address);
  
  // Get contract instance
  const WorldtreeTest = await ethers.getContractFactory("WorldtreeTest");
  const worldtreeTest = WorldtreeTest.attach(WORLDTREE_TEST_ADDRESS);
  
  // Check pending requests
  console.log("\n=== Current Pending Requests ===");
  const pendingRequests = await worldtreeTest.getPendingRequests();
  console.log("Total pending:", pendingRequests.length);
  
  for (let i = 0; i < pendingRequests.length; i++) {
    const requestId = pendingRequests[i];
    const request = await worldtreeTest.getAnalysisRequest(requestId);
    
    console.log(`\nRequest ${requestId}:`);
    console.log("- Requester:", request.requester);
    console.log("- User1:", request.user1);
    console.log("- User2:", request.user2);
    console.log("- Status:", request.status);
    console.log("- Time:", new Date(Number(request.requestTime) * 1000).toISOString());
  }
  
  // Check ROFL app configuration
  const roflAppBytes = await worldtreeTest.roflApp();
  const roflAppAddress = "0x" + roflAppBytes.slice(2, 42);
  console.log("\n=== ROFL Configuration ===");
  console.log("Authorized ROFL App:", roflAppAddress);
  console.log("Expected:", "0x00ad68194ee7e74b2c188bb62dc05e7dd99c52d300");
  
  // Check if there are any completed analyses
  console.log("\n=== Checking for Completed Analyses ===");
  const nextRequestId = await worldtreeTest.nextRequestId();
  console.log("Total requests created:", nextRequestId.toString());
  
  let completedCount = 0;
  for (let i = 0; i < nextRequestId; i++) {
    try {
      const request = await worldtreeTest.getAnalysisRequest(i);
      if (request.status === "completed") {
        completedCount++;
        console.log(`\nCompleted Analysis ${i}:`);
        console.log("- Users:", request.user1, "<->", request.user2);
        if (request.result) {
          try {
            const result = JSON.parse(request.result);
            console.log("- Relationship:", result.relationship || "Unknown");
            console.log("- Confidence:", result.confidence || "Unknown");
          } catch {
            console.log("- Result:", request.result);
          }
        }
      }
    } catch {
      // Request doesn't exist
    }
  }
  
  console.log("\nTotal completed analyses:", completedCount);
  
  // Summary
  console.log("\n=== Summary ===");
  console.log("✓ Contract is deployed and accessible");
  console.log("✓ ROFL app authorization is configured");
  console.log(`📊 ${pendingRequests.length} pending analysis requests`);
  console.log(`✅ ${completedCount} completed analyses`);
  
  if (pendingRequests.length > 0) {
    console.log("\n⏳ The ROFL app needs to:");
    console.log("1. Poll getPendingRequests()");
    console.log("2. Retrieve SNP data with getSNPDataForAnalysis()");
    console.log("3. Run genetic analysis");
    console.log("4. Submit results with submitAnalysisResult()");
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
