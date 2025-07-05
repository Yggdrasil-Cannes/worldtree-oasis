const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  // Contract address
  const WORLDTREE_TEST_ADDRESS = "0xa4e5c09C101A62Aa04A1078228527CD106012d0b";
  
  console.log("Creating analysis request with two test users");
  console.log("Contract:", WORLDTREE_TEST_ADDRESS);
  
  // Get the main signer
  const [signer] = await ethers.getSigners();
  console.log("Main signer:", signer.address);
  
  // Create a second wallet manually (for testing only - DO NOT use in production)
  // This is a test private key - DO NOT use real funds
  const testPrivateKey = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80";
  const provider = signer.provider;
  const user2Wallet = new ethers.Wallet(testPrivateKey, provider);
  
  console.log("\n=== Test Users ===");
  console.log("User1:", signer.address);
  console.log("User2:", user2Wallet.address);
  
  // Get contract instance
  const WorldtreeTest = await ethers.getContractFactory("WorldtreeTest");
  const worldtreeTest = WorldtreeTest.attach(WORLDTREE_TEST_ADDRESS);
  
  // Check registration status
  const user1Info = await worldtreeTest.users(signer.address);
  const user2Info = await worldtreeTest.users(user2Wallet.address);
  
  console.log("\n=== Registration Status ===");
  console.log("User1 registered:", user1Info.registered);
  console.log("User2 registered:", user2Info.registered);
  
  // Register user1 if needed
  if (!user1Info.registered) {
    console.log("\n=== Registering User1 ===");
    const snpDataPath = path.join(__dirname, '..', 'example_snp_data_user1.txt');
    const snpData = fs.readFileSync(snpDataPath, 'utf8');
    
    const tx = await worldtreeTest.connect(signer).registerUser(snpData);
    await tx.wait();
    console.log("✅ User1 registered successfully");
  }
  
  // Register user2 if needed
  if (!user2Info.registered) {
    console.log("\n=== Registering User2 ===");
    console.log("Note: User2 needs TEST tokens to pay for gas");
    console.log("Please fund this address first:", user2Wallet.address);
    
    // Check balance
    const balance = await provider.getBalance(user2Wallet.address);
    console.log("User2 balance:", ethers.formatEther(balance), "TEST");
    
    if (balance < ethers.parseEther("0.01")) {
      console.log("\n❌ User2 needs at least 0.01 TEST to pay for gas");
      console.log("Please fund the address and run this script again");
      return;
    }
    
    const snpDataPath = path.join(__dirname, '..', 'example_snp_data_user2.txt');
    const snpData = fs.readFileSync(snpDataPath, 'utf8');
    
    const worldtreeTestUser2 = WorldtreeTest.attach(WORLDTREE_TEST_ADDRESS).connect(user2Wallet);
    const tx = await worldtreeTestUser2.registerUser(snpData);
    await tx.wait();
    console.log("✅ User2 registered successfully");
  }
  
  // Request analysis
  console.log("\n=== Requesting Analysis ===");
  console.log("Requesting analysis between:", signer.address, "and", user2Wallet.address);
  
  const tx = await worldtreeTest.connect(signer).requestAnalysis(signer.address, user2Wallet.address);
  const receipt = await tx.wait();
  
  // Get request ID from event
  const event = receipt.logs.find(log => log.fragment?.name === 'AnalysisRequested');
  const requestId = event.args[0];
  
  console.log("\n✅ Analysis requested successfully!");
  console.log("Request ID:", requestId.toString());
  console.log("\nIMPORTANT: The ROFL app view functions might not work properly");
  console.log("The /rofl/v1/eth/call endpoint is uncertain in ROFL v0.5.0");
  console.log("\nTo monitor the request, run:");
  console.log("npx hardhat run scripts/check-all-requests.js --network sapphire-testnet");
  
  // Check pending requests
  console.log("\n=== Checking Pending Requests ===");
  const pendingRequests = await worldtreeTest.getPendingRequests();
  console.log("Pending requests:", pendingRequests.map(id => id.toString()));
}

main()
  .then(() => {
    console.log("\n✅ Script completed");
    process.exit(0);
  })
  .catch((error) => {
    console.error("\n❌ Error:", error);
    process.exit(1);
  });
