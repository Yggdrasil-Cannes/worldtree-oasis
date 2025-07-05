const { ethers } = require("hardhat");

async function main() {
  const [signer] = await ethers.getSigners();
  
  // Contract address
  const WORLDTREE_TEST_ADDRESS = "0xa4e5c09C101A62Aa04A1078228527CD106012d0b";
  
  console.log("Creating analysis request");
  console.log("Contract:", WORLDTREE_TEST_ADDRESS);
  console.log("Signer:", signer.address);
  
  // Get contract instance
  const WorldtreeTest = await ethers.getContractFactory("WorldtreeTest");
  const worldtreeTest = WorldtreeTest.attach(WORLDTREE_TEST_ADDRESS);
  
  // Use a different address for user2
  // This is a hardcoded address that may not be registered
  const user2Address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8";
  
  console.log("\n=== Creating Analysis Request ===");
  console.log("User1 (registered):", signer.address);
  console.log("User2 (target):", user2Address);
  
  try {
    const tx = await worldtreeTest.requestAnalysis(signer.address, user2Address);
    const receipt = await tx.wait();
    
    // Get request ID from event
    const event = receipt.logs.find(log => log.fragment?.name === 'AnalysisRequested');
    const requestId = event.args[0];
    
    console.log("\n✅ Analysis requested successfully!");
    console.log("Request ID:", requestId.toString());
    console.log("\nNote: This request will fail if user2 is not registered.");
    console.log("The ROFL app should process this and mark it as failed.");
  } catch (error) {
    console.error("\n❌ Failed to create analysis request:");
    console.error(error.message);
    
    if (error.message.includes("User not registered")) {
      console.log("\nUser2 is not registered. The contract requires both users to be registered.");
    }
  }
  
  console.log("\nRun 'npx hardhat run scripts/check-all-requests.js --network sapphire-testnet' to monitor status");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
