const { ethers } = require("hardhat");

async function main() {
  // Contract address
  const contractAddress = "0x614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3";
  
  // Get the contract
  const WorldtreeTest = await ethers.getContractFactory("WorldtreeTest");
  const contract = WorldtreeTest.attach(contractAddress);
  
  // Get the ROFL app ID stored in the contract
  const roflAppId = await contract.roflApp();
  console.log("Contract ROFL App ID (bytes21):", roflAppId);
  
  // Convert to address format (remove leading zeros)
  const cleanAddress = roflAppId.replace(/^0x0+/, "0x");
  console.log("Contract ROFL App ID (address):", cleanAddress);
  
  // Our ROFL app ID from deployment
  const ourRoflId = "rofl1qq9vdpxduln5utg3htkhvzwhvhdnzttylunuy6wm";
  console.log("Our ROFL App ID:", ourRoflId);
  
  // Convert our ROFL ID to address format
  // rofl1 prefix = 0x00, then bech32 decode
  // For testing, let's check pending requests
  console.log("\nChecking pending requests...");
  const pending = await contract.getPendingRequests();
  console.log("Pending requests:", pending.map(p => p.toString()));
  
  // Get request details for debugging
  if (pending.length > 0) {
    const req = await contract.analysisRequests(pending[0]);
    console.log("\nFirst request details:");
    console.log("- Requester:", req[0]);
    console.log("- User1:", req[1]);
    console.log("- User2:", req[2]);
    console.log("- Status:", req[3]);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
