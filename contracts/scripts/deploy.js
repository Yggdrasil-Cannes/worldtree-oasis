const hre = require("hardhat");

async function main() {
  // The ROFL app ID we're authorizing (converted from bech32 to hex)
  // rofl1qq9vdpxduln5utg3htkhvzwhvhdnzttylunuy6wm
  // Need to pad to 21 bytes (42 hex chars) for bytes21
  const ROFL_APP_ID = "0x00ad68194ee7e74b2c188bb62dc05e7dd99c52d300";
  
  console.log("Deploying LLMBridge contract...");
  console.log("Network:", hre.network.name);
  
  // Get deployer info
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with account:", deployer.address);
  
  // Deploy the contract
  const LLMBridge = await hre.ethers.getContractFactory("LLMBridge");
  const llmBridge = await LLMBridge.deploy(ROFL_APP_ID);
  
  await llmBridge.waitForDeployment();
  
  const contractAddress = await llmBridge.getAddress();
  console.log("\nLLMBridge deployed to:", contractAddress);
  console.log("Authorized ROFL App:", ROFL_APP_ID);
  
  // Create a sample request for testing
  console.log("\nCreating a sample request...");
  const tx = await llmBridge.createRequest("Hello, can you explain what ROFL is?");
  const receipt = await tx.wait();
  console.log("Sample request created! Transaction hash:", receipt.hash);
  console.log("Request ID: 0");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
