const { ethers } = require("hardhat");

async function main() {
  // Current ROFL app ID: rofl1qq9vdpxduln5utg3htkhvzwhvhdnzttylunuy6wm
  // Converted to Ethereum address format
  const ROFL_APP_ID = "0x000ac684cde7e74e2d11baed7609d765db312d64ff";
  
  console.log("Deploying WorldtreeTest contract...");
  console.log("Network:", hre.network.name);
  
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with account:", deployer.address);
  
  // Deploy the test contract
  const WorldtreeTest = await ethers.getContractFactory("WorldtreeTest");
  const worldtreeTest = await WorldtreeTest.deploy(ROFL_APP_ID);
  
  await worldtreeTest.waitForDeployment();
  
  const contractAddress = await worldtreeTest.getAddress();
  console.log("\nWorldtreeTest deployed to:", contractAddress);
  console.log("Authorized ROFL App:", ROFL_APP_ID);
  
  console.log("\n=== Test Contract Features ===");
  console.log("- Users can register with direct SNP data (no Walrus)");
  console.log("- Request genetic analysis between registered users");
  console.log("- ROFL app polls for pending requests");
  console.log("- ROFL app retrieves SNP data and submits results");
  
  console.log("\n=== Next Steps ===");
  console.log("1. Update compose.yaml with:");
  console.log(`   WORLDTREE_CONTRACT=${contractAddress}`);
  console.log("\n2. Register test users with SNP data");
  console.log("3. Request analysis between users");
  console.log("4. ROFL app will process and submit results");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
