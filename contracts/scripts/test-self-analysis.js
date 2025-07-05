const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const [signer] = await ethers.getSigners();
  
  // Contract address
  const WORLDTREE_TEST_ADDRESS = "0xa4e5c09C101A62Aa04A1078228527CD106012d0b";
  
  console.log("Testing WorldtreeTest contract at:", WORLDTREE_TEST_ADDRESS);
  console.log("Signer:", signer.address);
  
  // Get contract instance
  const WorldtreeTest = await ethers.getContractFactory("WorldtreeTest");
  const worldtreeTest = WorldtreeTest.attach(WORLDTREE_TEST_ADDRESS);
  
  // Check if signer is already registered
  const user = await worldtreeTest.users(signer.address);
  console.log("\n=== Registration Status ===");
  console.log("Signer registered:", user.registered);
  
  if (!user.registered) {
    console.log("\n=== Registering Signer ===");
    // Read SNP data from file
    const snpDataPath = path.join(__dirname, '..', 'example_snp_data_user1.txt');
    const snpData = fs.readFileSync(snpDataPath, 'utf8');
    
    const tx = await worldtreeTest.registerUser(snpData);
    await tx.wait();
    console.log("Signer registered successfully");
  }
  
  // Create a second test address with the same address (self-analysis)
  console.log("\n=== Requesting Self-Analysis ===");
  const tx = await worldtreeTest.requestAnalysis(signer.address, signer.address);
  const receipt = await tx.wait();
  
  // Get request ID from event
  const event = receipt.logs.find(log => log.fragment?.name === 'AnalysisRequested');
  const requestId = event.args[0];
  
  console.log("Analysis requested with ID:", requestId.toString());
  console.log("Requester:", signer.address);
  console.log("User1:", signer.address);
  console.log("User2:", signer.address);
  
  // Monitor for results
  console.log("\n=== Monitoring for Results ===");
  console.log("The ROFL app should process this request within 30 seconds...");
  
  let attempts = 0;
  const maxAttempts = 10; // 5 minutes with 30-second intervals
  
  const checkResults = async () => {
    attempts++;
    console.log(`\nAttempt ${attempts}/${maxAttempts}...`);
    
    const request = await worldtreeTest.getAnalysisRequest(requestId);
    console.log("Status:", request.status);
    
    if (request.status === "completed") {
      console.log("\n🎉 Analysis completed!");
      console.log("Result:", request.result);
      
      try {
        const parsedResult = JSON.parse(request.result);
        console.log("\nParsed Result:");
        console.log("- Relationship:", parsedResult.relationship);
        console.log("- Confidence:", parsedResult.confidence);
        console.log("- Shared SNPs:", parsedResult.shared_snps);
        console.log("- IBS Score:", parsedResult.ibs_score);
      } catch (e) {
        console.log("Could not parse result JSON");
      }
      
      return true;
    } else if (request.status === "failed") {
      console.log("\n❌ Analysis failed!");
      console.log("Result:", request.result);
      return true;
    }
    
    return false;
  };
  
  // Check immediately
  if (await checkResults()) return;
  
  // Then check every 30 seconds
  const interval = setInterval(async () => {
    const completed = await checkResults();
    
    if (completed || attempts >= maxAttempts) {
      clearInterval(interval);
      
      if (attempts >= maxAttempts) {
        console.log("\n⏰ Timeout: Analysis not completed within 5 minutes");
        console.log("The ROFL app might not be running or might be experiencing issues");
      }
    }
  }, 30000);
}

main()
  .then(() => console.log("\n✅ Test completed"))
  .catch((error) => {
    console.error("\n❌ Error:", error);
    process.exit(1);
  });
