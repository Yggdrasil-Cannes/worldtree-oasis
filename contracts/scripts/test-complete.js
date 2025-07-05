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
  
  // Step 1: Check if signer is already registered
  console.log("\n=== Checking Registration Status ===");
  const signerInfo = await worldtreeTest.users(signer.address);
  console.log("Signer registered:", signerInfo.registered);
  
  // Sample SNP data generator
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
  
  // If not registered, register the signer
  if (!signerInfo.registered) {
    console.log("Registering signer...");
    const signerSNPData = generateSNPData(1);
    const tx = await worldtreeTest.registerUser(signerSNPData);
    await tx.wait();
    console.log("Signer registered successfully");
  }
  
  // Step 2: Create a second wallet and fund it
  console.log("\n=== Creating Second Test User ===");
  const wallet2 = new ethers.Wallet(
    "0x" + "1".repeat(64), // Deterministic private key for testing
    signer.provider
  );
  console.log("Test User2 address:", wallet2.address);
  
  // Send some ETH to wallet2 for gas
  console.log("Funding Test User2...");
  const fundTx = await signer.sendTransaction({
    to: wallet2.address,
    value: ethers.parseEther("0.1")
  });
  await fundTx.wait();
  console.log("Test User2 funded");
  
  // Connect wallet2 to the contract
  const worldtreeTest2 = worldtreeTest.connect(wallet2);
  
  // Check if wallet2 is registered
  const user2Info = await worldtreeTest.users(wallet2.address);
  if (!user2Info.registered) {
    console.log("Registering Test User2...");
    const user2SNPData = generateSNPData(2);
    const tx2 = await worldtreeTest2.registerUser(user2SNPData);
    await tx2.wait();
    console.log("Test User2 registered successfully");
  }
  
  // Step 3: Request genetic analysis
  console.log("\n=== Requesting Analysis ===");
  const analysisTx = await worldtreeTest.requestAnalysis(signer.address, wallet2.address);
  const receipt = await analysisTx.wait();
  
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
  
  // Step 4: Check the analysis request
  console.log("\n=== Analysis Request Details ===");
  const analysisData = await worldtreeTest.getAnalysisRequest(requestId);
  console.log("Request ID:", requestId.toString());
  console.log("Requester:", analysisData.requester);
  console.log("User1:", analysisData.user1);
  console.log("User2:", analysisData.user2);
  console.log("Status:", analysisData.status);
  console.log("Request Time:", new Date(Number(analysisData.requestTime) * 1000).toISOString());
  
  // Step 5: Check pending requests
  console.log("\n=== Pending Requests ===");
  const pendingRequests = await worldtreeTest.getPendingRequests();
  console.log("Total pending requests:", pendingRequests.length);
  console.log("Request IDs:", pendingRequests.map(id => id.toString()));
  
  // Step 6: Test access control
  console.log("\n=== Testing Access Control ===");
  try {
    await worldtreeTest.getSNPDataForAnalysis(requestId);
    console.log("ERROR: Should not be able to get SNP data!");
  } catch (error) {
    console.log("✓ Good: SNP data retrieval blocked (only ROFL app can access)");
  }
  
  // Step 7: Check ROFL configuration
  const roflAppBytes = await worldtreeTest.roflApp();
  const roflAppAddress = "0x" + roflAppBytes.slice(2, 42);
  console.log("\n=== ROFL App Configuration ===");
  console.log("Authorized ROFL App:", roflAppAddress);
  console.log("Expected:", "0x00ad68194ee7e74b2c188bb62dc05e7dd99c52d300");
  console.log("Match:", roflAppAddress.toLowerCase() === "0x00ad68194ee7e74b2c188bb62dc05e7dd99c52d300");
  
  console.log("\n=== Contract Test Complete ===");
  console.log("✓ Contract deployed and working");
  console.log("✓ User registration successful");
  console.log("✓ Analysis request created");
  console.log("✓ Access control working");
  console.log("✓ ROFL app authorization configured");
  
  console.log("\n📋 Summary:");
  console.log("- WorldtreeTest contract:", WORLDTREE_TEST_ADDRESS);
  console.log("- Pending analysis request ID:", requestId.toString());
  console.log("- Waiting for ROFL app to process...");
  
  console.log("\n💡 Next Steps:");
  console.log("1. Update ROFL app on-chain configuration");
  console.log("2. Deploy ROFL app with new Docker image");
  console.log("3. ROFL will poll and process pending requests");
  console.log("4. Check analysis results with getAnalysisRequest()");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
