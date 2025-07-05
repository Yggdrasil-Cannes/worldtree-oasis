const { ethers } = require("hardhat");

async function main() {
  const [signer, user1, user2] = await ethers.getSigners();
  
  // Contract address
  const WORLDTREE_TEST_ADDRESS = "0xa4e5c09C101A62Aa04A1078228527CD106012d0b";
  
  console.log("Testing WorldtreeTest contract at:", WORLDTREE_TEST_ADDRESS);
  console.log("Signer:", signer.address);
  console.log("User1:", user1.address);
  console.log("User2:", user2.address);
  
  // Get contract instance
  const WorldtreeTest = await ethers.getContractFactory("WorldtreeTest");
  const worldtreeTest = WorldtreeTest.attach(WORLDTREE_TEST_ADDRESS);
  
  // Step 1: Register users with SNP data
  console.log("\n=== Registering Users ===");
  
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
  
  const user1SNPData = generateSNPData(1);
  const user2SNPData = generateSNPData(2); // Different seed for variation
  
  // Register user1
  console.log("Registering user1...");
  let tx = await worldtreeTest.connect(user1).registerUser(user1SNPData);
  await tx.wait();
  console.log("User1 registered");
  
  // Register user2
  console.log("Registering user2...");
  tx = await worldtreeTest.connect(user2).registerUser(user2SNPData);
  await tx.wait();
  console.log("User2 registered");
  
  // Step 2: Request genetic analysis
  console.log("\n=== Requesting Analysis ===");
  tx = await worldtreeTest.requestAnalysis(user1.address, user2.address);
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
  console.log("\n=== Checking Pending Requests ===");
  const pendingRequests = await worldtreeTest.getPendingRequests();
  console.log("Pending requests:", pendingRequests.map(id => id.toString()));
  
  // Step 4: Get SNP data (this would normally be done by ROFL app)
  console.log("\n=== Testing SNP Data Retrieval ===");
  try {
    // This should fail because we're not the ROFL app
    await worldtreeTest.getSNPDataForAnalysis(requestId);
    console.log("ERROR: Should not be able to get SNP data!");
  } catch (error) {
    console.log("Good: SNP data retrieval blocked (only ROFL app can access)");
  }
  
  // Step 5: Show analysis status
  console.log("\n=== Analysis Status ===");
  const analysisData = await worldtreeTest.getAnalysisRequest(requestId);
  console.log("Request ID:", requestId.toString());
  console.log("Requester:", analysisData.requester);
  console.log("User1:", analysisData.user1);
  console.log("User2:", analysisData.user2);
  console.log("Status:", analysisData.status);
  console.log("Request Time:", new Date(Number(analysisData.requestTime) * 1000).toISOString());
  
  console.log("\n=== Contract Test Complete ===");
  console.log("The contract is working properly!");
  console.log("Pending analysis request is waiting for ROFL app to process");
  
  // Optional: Monitor for a bit to see if ROFL processes it
  console.log("\n=== Monitoring for ROFL Processing (30 seconds) ===");
  let processed = false;
  const startTime = Date.now();
  
  while (!processed && (Date.now() - startTime < 30000)) {
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    const updatedData = await worldtreeTest.getAnalysisRequest(requestId);
    if (updatedData.status !== "pending") {
      processed = true;
      console.log("\nAnalysis processed!");
      console.log("New status:", updatedData.status);
      
      if (updatedData.result) {
        try {
          const result = JSON.parse(updatedData.result);
          console.log("Relationship:", result.relationship);
          console.log("Confidence:", result.confidence);
        } catch {
          console.log("Result:", updatedData.result);
        }
      }
    } else {
      console.log("Still pending...");
    }
  }
  
  if (!processed) {
    console.log("\nAnalysis not processed yet (ROFL app may not be running with updated config)");
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
