const { ethers } = require("hardhat");

async function main() {
  // ROFL app ID (same as before)
  const ROFL_APP_ID = "0x00ad68194ee7e74b2c188bb62dc05e7dd99c52d300";
  
  // Simplified Worldcoin verifier for testing
  const WORLDCOIN_VERIFIER = "0x0000000000000000000000000000000000000000";
  
  console.log("Deploying Worldtree contract...");
  console.log("Network:", hre.network.name);
  
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with account:", deployer.address);
  
  // Deploy the contract
  const Worldtree = await ethers.getContractFactory("Worldtree");
  const worldtree = await Worldtree.deploy(ROFL_APP_ID, WORLDCOIN_VERIFIER);
  
  await worldtree.waitForDeployment();
  
  const contractAddress = await worldtree.getAddress();
  console.log("\nWorldtree deployed to:", contractAddress);
  console.log("Authorized ROFL App:", ROFL_APP_ID);
  console.log("Worldcoin Verifier:", WORLDCOIN_VERIFIER);
  
  // Update compose.yaml with the new contract address
  console.log("\nIMPORTANT: Update compose.yaml with:");
  console.log(`WORLDTREE_CONTRACT=${contractAddress}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
