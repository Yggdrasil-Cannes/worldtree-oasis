const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const [signer] = await ethers.getSigners();
  
  // Contract address
  const WORLDTREE_TEST_ADDRESS = "0xa4e5c09C101A62Aa04A1078228527CD106012d0b";
  
  console.log("Checking registration status");
  console.log("Contract:", WORLDTREE_TEST_ADDRESS);
  console.log("Signer:", signer.address);
  
  // Get contract instance
  const WorldtreeTest = await ethers.getContractFactory("WorldtreeTest");
  const worldtreeTest = WorldtreeTest.attach(WORLDTREE_TEST_ADDRESS);
  
  // Check if signer is registered
  const user = await worldtreeTest.users(signer.address);
  console.log("\n=== Registration Status ===");
  console.log("Registered:", user.registered);
  console.log("SNP Hash:", user.snpDataHash);
  
  if (!user.registered) {
    console.log("\n=== Registering User ===");
    // Read SNP data from file
    const snpDataPath = path.join(__dirname, '..', 'example_snp_data_user1.txt');
    const snpData = fs.readFileSync(snpDataPath, 'utf8');
    
    console.log("Registering with example SNP data...");
    const tx = await worldtreeTest.registerUser(snpData);
    await tx.wait();
    console.log("✅ User registered successfully");
    
    // Verify registration
    const updatedUser = await worldtreeTest.users(signer.address);
    console.log("\nUpdated registration status:", updatedUser.registered);
  } else {
    console.log("✅ User is already registered");
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
