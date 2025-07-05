const { ethers } = require("hardhat");

async function main() {
  console.log("Checking WorldtreeTest contract addresses...\n");
  
  // Two addresses mentioned in the project
  const addresses = [
    "0xDF4A26832c770EeC30442337a4F9dd51bbC0a832",  // From handoff document
    "0xa4e5c09C101A62Aa04A1078228527CD106012d0b"   // From scripts
  ];
  
  const [signer] = await ethers.getSigners();
  console.log("Checking from account:", signer.address);
  
  for (const address of addresses) {
    console.log(`\n=== Checking ${address} ===`);
    
    try {
      // Check if it's a contract
      const code = await ethers.provider.getCode(address);
      
      if (code === "0x") {
        console.log("❌ No contract deployed at this address");
        continue;
      }
      
      console.log("✅ Contract found");
      
      // Try to interact with it as WorldtreeTest
      try {
        const WorldtreeTest = await ethers.getContractFactory("WorldtreeTest");
        const contract = WorldtreeTest.attach(address);
        
        // Try to read roflApp
        const roflApp = await contract.roflApp();
        console.log("ROFL App (bytes21):", roflApp);
        
        // Convert to address format (first 20 bytes)
        const roflAppAddress = "0x" + roflApp.slice(2, 42);
        console.log("ROFL App Address:", roflAppAddress);
        
        // Check some basic stats
        const nextRequestId = await contract.nextRequestId();
        const nextRelationshipId = await contract.nextRelationshipId();
        
        console.log("Next Request ID:", nextRequestId.toString());
        console.log("Next Relationship ID:", nextRelationshipId.toString());
        
        // This is likely the correct contract
        console.log("\n✅ This appears to be a valid WorldtreeTest contract!");
        
      } catch (error) {
        console.log("❌ Error interacting with contract:", error.message);
      }
      
    } catch (error) {
      console.log("❌ Error checking address:", error.message);
    }
  }
  
  console.log("\n=== Summary ===");
  console.log("Update the contract address in:");
  console.log("1. /services/llm-api/main_fixed.py (WORLDTREE_CONTRACT variable)");
  console.log("2. /contracts/.env (if used)");
  console.log("3. Any deployment scripts");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
