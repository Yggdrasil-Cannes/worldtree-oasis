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
  
  // Check all analysis requests
  console.log("\n=== Checking All Analysis Requests ===");
  const nextRequestId = await worldtreeTest.nextRequestId();
  console.log("Total requests created:", nextRequestId.toString());
  
  for (let i = 0; i < nextRequestId; i++) {
    try {
      const request = await worldtreeTest.getAnalysisRequest(i);
      console.log(`\nRequest ${i}:`);
      console.log("- Requester:", request.requester);
      console.log("- User1:", request.user1);
      console.log("- User2:", request.user2);
      console.log("- Status:", request.status);
      console.log("- Result:", request.result || "None");
      console.log("- Request Time:", new Date(Number(request.requestTime) * 1000).toISOString());
      
      if (request.completionTime > 0) {
        console.log("- Completion Time:", new Date(Number(request.completionTime) * 1000).toISOString());
      }
    } catch (e) {
      console.log(`Request ${i}: Not found`);
    }
  }
  
  // Check pending requests
  console.log("\n=== Current Pending Requests ===");
  const pendingRequests = await worldtreeTest.getPendingRequests();
  console.log("Total pending:", pendingRequests.length);
  
  for (let i = 0; i < pendingRequests.length; i++) {
    const requestId = pendingRequests[i];
    const request = await worldtreeTest.getAnalysisRequest(requestId);
    
    console.log(`\nPending Request ${requestId}:`);
    console.log("- Requester:", request.requester);
    console.log("- User1:", request.user1);
    console.log("- User2:", request.user2);
    console.log("- Time:", new Date(Number(request.requestTime) * 1000).toISOString());
  }
  
  // Check registered users
  console.log("\n=== Checking Registered Users ===");
  const signerUser = await worldtreeTest.users(signer.address);
  console.log("Signer registered:", signerUser.registered);
  
  // List of common test addresses from Hardhat
  const testAddresses = [
    "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
    "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
    "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65"
  ];
  
  console.log("\nChecking test addresses:");
  for (const addr of testAddresses) {
    const user = await worldtreeTest.users(addr);
    if (user.registered) {
      console.log(`- ${addr}: Registered`);
    }
  }
  
  // Check ROFL app status
  console.log("\n=== ROFL App Status ===");
  const roflAppBytes = await worldtreeTest.roflApp();
  const roflAppAddress = "0x" + roflAppBytes.slice(2, 42);
  console.log("Authorized ROFL App:", roflAppAddress);
  console.log("Expected:", "0x00ad68194ee7e74b2c188bb62dc05e7dd99c52d3");
  
  if (roflAppAddress.toLowerCase() === "0x00ad68194ee7e74b2c188bb62dc05e7dd99c52d3") {
    console.log("✅ ROFL app is correctly authorized");
  } else {
    console.log("❌ ROFL app authorization mismatch!");
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
