const { ethers } = require("hardhat");

async function main() {
  const [signer, user1, user2] = await ethers.getSigners();
  
  // Contract address - UPDATE THIS after deployment
  const WORLDTREE_TEST_ADDRESS = process.argv[2];
  
  if (!WORLDTREE_TEST_ADDRESS) {
    console.error("Please provide WorldtreeTest contract address as argument");
    process.exit(1);
  }
  
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
  
  // Step 4: Monitor analysis status
  console.log("\n=== Waiting for ROFL Analysis ===");
  console.log("The ROFL app should now:");
  console.log("1. Poll for pending requests");
  console.log("2. Retrieve SNP data");
  console.log("3. Perform genetic analysis");
  console.log("4. Submit results back to the contract");
  
  // Poll for completion
  let completed = false;
  let attempts = 0;
  const maxAttempts = 20;
  
  while (!completed && attempts < maxAttempts) {
    await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
    
    const analysisData = await worldtreeTest.getAnalysisRequest(requestId);
    console.log(`\nAttempt ${attempts + 1}: Status = ${analysisData.status}`);
    
    if (analysisData.status === "completed" || analysisData.status === "failed") {
      completed = true;
      console.log("\n=== Analysis Complete ===");
      console.log("Status:", analysisData.status);
      
      if (analysisData.result) {
        try {
          const result = JSON.parse(analysisData.result);
          console.log("Relationship:", result.relationship);
          console.log("Confidence:", result.confidence);
          console.log("Common SNPs:", result.n_common_snps);
          console.log("IBS Score:", result.ibs_analysis?.ibs_score);
        } catch {
          console.log("Result:", analysisData.result);
        }
      }
    }
    
    attempts++;
  }
  
  if (!completed) {
    console.log("\nAnalysis not completed within timeout period");
    console.log("Check ROFL logs for any errors");
  }
  
  // Step 5: Check relationships
  console.log("\n=== Checking Relationships ===");
  const userRelationships = await worldtreeTest.getUserRelationships(user1.address);
  console.log("User1 relationships:", userRelationships.map(id => id.toString()));
  
  if (userRelationships.length > 0) {
    const relData = await worldtreeTest.getRelationshipDetails(userRelationships[0]);
    console.log("Relationship details:");
    console.log("- Users:", relData.user1, "<->", relData.user2);
    console.log("- Type:", relData.relationshipType);
    console.log("- Confidence:", relData.confidence.toString(), "%");
    console.log("- Confirmed:", relData.confirmed);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
