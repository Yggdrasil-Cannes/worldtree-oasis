const hre = require("hardhat");

async function main() {
  // Get ROFL app ID from command line or environment
  const roflAppID = process.env.ROFL_APP_ID || process.argv[2];
  
  if (!roflAppID) {
    console.error("Please provide ROFL app ID as environment variable or argument");
    process.exit(1);
  }

  console.log("Deploying FamilyBounty contract...");
  console.log("ROFL App ID:", roflAppID);

  const FamilyBounty = await hre.ethers.getContractFactory("FamilyBounty");
  const familyBounty = await FamilyBounty.deploy(roflAppID);

  await familyBounty.waitForDeployment();

  const address = await familyBounty.getAddress();
  console.log("FamilyBounty deployed to:", address);
  
  // Save deployment info
  const fs = require("fs");
  const deploymentInfo = {
    contract: "FamilyBounty",
    address: address,
    network: hre.network.name,
    roflAppID: roflAppID,
    timestamp: new Date().toISOString()
  };
  
  fs.writeFileSync(
    "deployment.json",
    JSON.stringify(deploymentInfo, null, 2)
  );
  
  console.log("Deployment info saved to deployment.json");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
