const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  const CONTRACT_ADDRESS = "0xDF4A26832c770EeC30442337a4F9dd51bbC0a832";
  
  console.log("Testing Genetic Analysis System...");
  console.log("Contract:", CONTRACT_ADDRESS);
  
  const [user1, user2] = await ethers.getSigners();
  console.log("User1:", user1.address);
  console.log("User2:", user2.address);
  
  // Connect to contract
  const WorldtreeTest = await ethers.getContractFactory("WorldtreeTest");
  const contract = WorldtreeTest.attach(CONTRACT_ADDRESS);
  
  try {
    // Step 1: Register both users with SNP data
    console.log("\n=== Step 1: Registering Users ===");
    
    // Read example SNP data
    const snpData1 = fs.readFileSync("../example_snp_data_user1.txt", "utf8");
    const snpData2 = fs.readFileSync("../example_snp_data_user2.txt", "utf8");
    
    console.log("Registering User1...");
    const tx1 = await contract.connect(user1).registerUser(snpData1);
    await tx1.wait();
    console.log("User1 registered successfully");
    
    console.log("Registering User2...");
    const tx2 = await contract.connect(user2).registerUser(snpData2);
    await tx2.wait();
    console.log("User2 registered successfully");
    
    // Step 2: Create analysis request
    console.log("\n=== Step 2: Creating Analysis Request ===");
    console.log("User1 requesting analysis between User1 and User2...");
    
    const requestTx = await contract.connect(user1).requestAnalysis(
      user1.address,
      user2.address
    );
    const receipt = await requestTx.wait();
    
    // Find the request ID from events
    const event = receipt.logs.find(log => {
      try {
        const parsed = contract.interface.parseLog(log);
        return parsed.name === "AnalysisRequested";
      } catch {
        return false;
      }
    });
    
    if (event) {
      const parsed = contract.interface.parseLog(event);
      const requestId = parsed.args.id;
      console.log(`Analysis request created with ID: ${requestId}`);
      
      // Step 3: Check request status
      console.log("\n=== Step 3: Checking Request Status ===");
      const request = await contract.getAnalysisRequest(requestId);
      console.log("Request details:");
      console.log("  Requester:", request.requester);
      console.log("  User1:", request.user1);
      console.log("  User2:", request.user2);
      console.log("  Status:", request.status);
      console.log("  Request Time:", new Date(Number(request.requestTime) * 1000).toISOString());
      
      console.log("\n=== Waiting for ROFL Processing ===");
      console.log("The ROFL app should now:");
      console.log("1. Detect this pending request");
      console.log("2. Retrieve SNP data for both users");
      console.log("3. Perform genetic analysis");
      console.log("4. Submit results back to the contract");
      console.log("\nMonitor ROFL logs to see processing status.");
      
    } else {
      console.error("Failed to find AnalysisRequested event");
    }
    
  } catch (error) {
    console.error("Error:", error.message);
    if (error.data) {
      console.error("Error data:", error.data);
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
