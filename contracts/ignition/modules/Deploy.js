const hre = require("hardhat");

async function main() {
  // The ROFL app ID we're authorizing
  const ROFL_APP_ID = "0x00ad68194ee7e74b2c188bb62dc05e7dd99c52d3";
  
  console.log("Deploying LLMBridge contract...");
  
  // Deploy the contract
  const LLMBridge = await hre.ethers.getContractFactory("LLMBridge");
  const llmBridge = await LLMBridge.deploy(ROFL_APP_ID);
  
  await llmBridge.waitForDeployment();
  
  const contractAddress = await llmBridge.getAddress();
  console.log("LLMBridge deployed to:", contractAddress);
  console.log("Authorized ROFL App:", ROFL_APP_ID);
  
  // Create a sample request for testing
  console.log("\nCreating a sample request...");
  const tx = await llmBridge.createRequest("Hello, can you explain what ROFL is?");
  await tx.wait();
  console.log("Sample request created!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
