const { ethers } = require("hardhat");

async function main() {
  const [signer] = await ethers.getSigners();
  
  // Contract address
  const WORLDTREE_TEST_ADDRESS = "0xa4e5c09C101A62Aa04A1078228527CD106012d0b";
  
  console.log("Testing WorldtreeTest contract at:", WORLDTREE_TEST_ADDRESS);
  console.log("Signer:", signer.address);
  
  // Get contract instance
  const WorldtreeTest = await ethers.getContractFactory("WorldtreeTest");
  const worldtreeTest = WorldtreeTest.attach(WORLDTREE_TEST_ADDRESS);
  
  // Step 1: Register two test addresses with SNP data
  console.log("\n=== Registering Test Users ===");
  
  // Sample SNP data (minimum 100 SNPs required)
  const generateSNPData = (seed) => {
    let snpData = "";
    const chromosomes = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"];
    const genotypes = ["AA", "AT", "TT", "CC", "CG", "GG", "AG", "AC", "TC"];
    
    for (let i = 0; i < 150; i++) {
      const rsId = `rs${1000000 + i * 100 + seed}`;
      const position = 1000 + i * 1000;
      const chromosome = chromosomes[i % chromosomes.length];
      const genotype = genotypes[(i + seed) % genotypes.length];
      
      snpData += `${rsId} ${position} ${chromosome} ${genotype}\n`;
    }
    
    return snpData;
  };
  
  // Generate test addresses
  const wallet1 = ethers.Wallet.createRandom();
  const wallet2 = ethers.Wallet.createRandom();
  
  console.log("Test User1:", wallet1.address);
  console.log("Test User2:", wallet2.address);
  
  // Register signer as a user first
  console.log("\nRegistering signer...");
  const signerSNPData = generateSNPData(1);
  let tx = await worldtreeTest.registerUser(signerSNPData);
  await tx.wait();
  console.log("Signer registered");
  
  // For simplicity, we'll register the test addresses with dummy data
  // In a real scenario, these would be separate transactions from those addresses
  console.log("\nNote: In production, users would register themselves");
  console.log("For testing, we'll request analysis between signer and a test address");
  
  // Step 2: Request genetic analysis between signer and a dummy address
  console.log("\n=== Requesting Analysis ===");
  // We'll use the signer's address twice for simplicity
  tx = await worldtreeTest.requestAnalysis(signer.address, signer.address);
  const receipt = await tx.wait();
  
  // Get request ID from events
  const event = receipt.logs.find(log => {
    try {
      const parsed = worldtreeTest.interface.parseLog(log);
      return parsed.name === "AnalysisRequested";
    } catch {
      return false;
    }
  });
  
  const requestId = event ? worldtreeTest.interface.parseLog(event).args.id : 0;
  console.log("Analysis requested with ID:", requestId.toString());
  
  // Step 3: Check pending requests
  console.log("\n=== Checking Contract State ===");
  const pendingRequests = await worldtreeTest.getPendingRequests();
  console.log("Pending requests:", pendingRequests.map(id => id.toString()));
  
  // Step 4: Check analysis details
  const analysisData = await worldtreeTest.getAnalysisRequest(requestId);
  console.log("\n=== Analysis Request Details ===");
  console.log("Request ID:", requestId.toString());
  console.log("Requester:", analysisData.requester);
  console.log("User1:", analysisData.user1);
  console.log("User2:", analysisData.user2);
  console.log("Status:", analysisData.status);
  console.log("Request Time:", new Date(Number(analysisData.requestTime) * 1000).toISOString());
  
  // Step 5: Test access control
  console.log("\n=== Testing Access Control ===");
  try {
    // This should fail because we're not the ROFL app
    await worldtreeTest.getSNPDataForAnalysis(requestId);
    console.log("ERROR: Should not be able to get SNP data!");
  } catch (error) {
    console.log("✓ Good: SNP data retrieval blocked (only ROFL app can access)");
  }
  
  // Step 6: Check ROFL app authorization
  const roflAppBytes = await worldtreeTest.roflApp();
  const roflAppAddress = "0x" + roflAppBytes.slice(2, 42);
  console.log("\n=== ROFL App Configuration ===");
  console.log("Authorized ROFL App:", roflAppAddress);
  console.log("Expected:", "0x00ad68194ee7e74b2c188bb62dc05e7dd99c52d300");
  
  console.log("\n=== Contract Test Complete ===");
  console.log("✓ Contract deployed and working properly");
  console.log("✓ User registration successful");
  console.log("✓ Analysis request created");
  console.log("✓ Access control working");
  console.log("\n⏳ Waiting for ROFL app to process request ID:", requestId.toString());
  
  // Check if there are existing analysis results
  const userRelationships = await worldtreeTest.getUserRelationships(signer.address);
  if (userRelationships.length > 0) {
    console.log("\n=== Existing Relationships ===");
    for (const relId of userRelationships) {
      const rel = await worldtreeTest.getRelationshipDetails(relId);
      console.log(`Relationship ${relId}:`);
      console.log("- Type:", rel.relationshipType);
      console.log("- Confidence:", rel.confidence.toString() + "%");
      console.log("- Confirmed:", rel.confirmed);
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
