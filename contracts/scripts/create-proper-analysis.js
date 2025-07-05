const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const signers = await ethers.getSigners();
  
  // Contract address
  const WORLDTREE_TEST_ADDRESS = "0xa4e5c09C101A62Aa04A1078228527CD106012d0b";
  
  console.log("Creating analysis request between two users");
  console.log("Contract:", WORLDTREE_TEST_ADDRESS);
  console.log("Available signers:", signers.length);
  
  if (signers.length < 2) {
    console.error("Need at least 2 signers to create analysis between different users");
    process.exit(1);
  }
  
  const [user1, user2] = signers;
  console.log("\nUser1:", user1.address);
  console.log("User2:", user2.address);
  
  // Get contract instance
  const WorldtreeTest = await ethers.getContractFactory("WorldtreeTest");
  const worldtreeTest = WorldtreeTest.attach(WORLDTREE_TEST_ADDRESS);
  
  // Check if both users are registered
  const user1Info = await worldtreeTest.users(user1.address);
  const user2Info = await worldtreeTest.users(user2.address);
  
  console.log("\n=== Registration Status ===");
  console.log("User1 registered:", user1Info.registered);
  console.log("User2 registered:", user2Info.registered);
  
  // Register user1 if needed
  if (!user1Info.registered) {
    console.log("\n=== Registering User1 ===");
    const snpDataPath = path.join(__dirname, '..', 'example_snp_data_user1.txt');
    const snpData = fs.readFileSync(snpDataPath, 'utf8');
    
    const tx = await worldtreeTest.connect(user1).registerUser(snpData);
    await tx.wait();
    console.log("✅ User1 registered successfully");
  }
  
  // Register user2 if needed
  if (!user2Info.registered) {
    console.log("\n=== Registering User2 ===");
    const snpDataPath = path.join(__dirname, '..', 'example_snp_data_user2.txt');
    const snpData = fs.readFileSync(snpDataPath, 'utf8');
    
    const tx = await worldtreeTest.connect(user2).registerUser(snpData);
    await tx.wait();
    console.log("✅ User2 registered successfully");
  }
  
  // Request analysis
  console.log("\n=== Requesting Analysis ===");
  console.log("Requesting analysis between:", user1.address, "and", user2.address);
  
  const tx = await worldtreeTest.connect(user1).requestAnalysis(user1.address, user2.address);
  const receipt = await tx.wait();
  
  // Get request ID from event
  const event = receipt.logs.find(log => log.fragment?.name === 'AnalysisRequested');
  const requestId = event.args[0];
  
  console.log("\n✅ Analysis requested successfully!");
  console.log("Request ID:", requestId.toString());
  console.log("\nThe ROFL app should process this request within 30 seconds...");
  console.log("Run 'npx hardhat run scripts/check-all-requests.js --network sapphire-testnet' to monitor status");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
