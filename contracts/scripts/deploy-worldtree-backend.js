const hre = require("hardhat");

async function main() {
  console.log("Deploying WorldtreeBackend contract...");

  // Get the contract factory
  const WorldtreeBackend = await hre.ethers.getContractFactory("WorldtreeBackend");
  
  // ROFL app ID from the deployment (converted from bech32)
  const roflAppId = "0x000ac684cde7e74e2d11baed7609d765db312d64ff";
  
  // Get the deployer's address to use as backend
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with account:", deployer.address);
  
  // Deploy the contract
  const worldtreeBackend = await WorldtreeBackend.deploy(
    roflAppId,
    deployer.address  // Use deployer as authorized backend for now
  );

  await worldtreeBackend.waitForDeployment();

  const contractAddress = await worldtreeBackend.getAddress();
  console.log("WorldtreeBackend deployed to:", contractAddress);
  console.log("Authorized backend:", deployer.address);
  console.log("ROFL App ID:", roflAppId);
  
  // Save deployment info
  const fs = require("fs");
  const deploymentInfo = {
    network: hre.network.name,
    contractAddress: contractAddress,
    backendAddress: deployer.address,
    roflAppId: roflAppId,
    deploymentTime: new Date().toISOString()
  };
  
  fs.writeFileSync(
    "./deployments/worldtree-backend.json",
    JSON.stringify(deploymentInfo, null, 2)
  );
  
  console.log("\nDeployment info saved to deployments/worldtree-backend.json");
  console.log("\nNext steps:");
  console.log("1. Update ROFL service with new contract address");
  console.log("2. Update WLDTree-miniapp .env.local with contract address");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });