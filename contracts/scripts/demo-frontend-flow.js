const { ethers } = require("hardhat");

async function main() {
  console.log("=== ROFL Genetic Analysis Frontend Integration Demo ===\n");
  
  const CONTRACT_ADDRESS = "0x614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3";
  
  // Get signer
  const [signer] = await ethers.getSigners();
  console.log("Using account:", signer.address);
  
  // Connect to contract
  const WorldtreeTest = await ethers.getContractFactory("WorldtreeTest");
  const contract = WorldtreeTest.attach(CONTRACT_ADDRESS);
  
  // Example addresses (you can change these)
  const user1 = signer.address;
  const user2 = "0xbFbB95c74FaB7F9066711966CB50209176C37fFe";
  
  console.log("\n1. Submitting Analysis Request");
  console.log("   User 1:", user1);
  console.log("   User 2:", user2);
  
  try {
    // Submit analysis request
    const tx = await contract.requestAnalysis(user1, user2);
    console.log("   Transaction submitted:", tx.hash);
    
    const receipt = await tx.wait();
    console.log("   Transaction confirmed!");
    
    // Extract request ID from events
    const event = receipt.logs.find(log => {
      try {
        const parsed = contract.interface.parseLog(log);
        return parsed.name === 'AnalysisRequested';
      } catch {
        return false;
      }
    });
    
    if (!event) {
      console.error("   Failed to find AnalysisRequested event");
      return;
    }
    
    const parsedEvent = contract.interface.parseLog(event);
    const requestId = parsedEvent.args.id;
    console.log("   Request ID:", requestId.toString());
    
    // Poll for results
    console.log("\n2. Waiting for ROFL Analysis to Complete");
    console.log("   (This typically takes 30-60 seconds)");
    
    let completed = false;
    let attempts = 0;
    const maxAttempts = 20;
    
    while (!completed && attempts < maxAttempts) {
      attempts++;
      console.log(`   Checking status... (attempt ${attempts}/${maxAttempts})`);
      
      const request = await contract.getAnalysisRequest(requestId);
      
      if (request.status === 'completed') {
        completed = true;
        console.log("\n3. Analysis Completed!");
        
        // Parse and display results
        const result = JSON.parse(request.result);
        console.log("\n   === ANALYSIS RESULTS ===");
        console.log("   Relationship:", result.relationship);
        console.log("   Confidence:", result.confidence + "%");
        console.log("   Similarity Score:", result.similarity + "%");
        console.log("   Shared Markers:", result.shared_markers);
        console.log("   =======================");
        
        // Show how to access raw data
        console.log("\n4. Raw Contract Data:");
        console.log("   Request Time:", new Date(Number(request.requestTime) * 1000).toISOString());
        console.log("   Completion Time:", new Date(Number(request.completionTime) * 1000).toISOString());
        console.log("   Processing Duration:", Number(request.completionTime - request.requestTime), "seconds");
        
      } else if (request.status === 'failed') {
        completed = true;
        console.error("\n   Analysis failed:", request.result);
        
      } else {
        // Still pending, wait before next check
        await new Promise(resolve => setTimeout(resolve, 5000)); // 5 seconds
      }
    }
    
    if (!completed) {
      console.log("\n   Analysis is taking longer than expected. Request ID:", requestId.toString());
      console.log("   You can check status manually with:");
      console.log(`   await contract.getAnalysisRequest(${requestId})`);
    }
    
  } catch (error) {
    console.error("\nError:", error.message);
    
    if (error.message.includes("User not registered")) {
      console.log("\nNote: Both users must be registered with SNP data first.");
      console.log("Use the registration scripts to register users before requesting analysis.");
    }
  }
  
  console.log("\n=== Demo Complete ===");
  console.log("\nThis demonstrates the complete flow that a frontend would implement:");
  console.log("1. Submit analysis request transaction");
  console.log("2. Extract request ID from transaction receipt");
  console.log("3. Poll for completion status");
  console.log("4. Display results when ready");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
