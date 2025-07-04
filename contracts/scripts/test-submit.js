const { ethers } = require("hardhat");

async function main() {
  const CONTRACT_ADDRESS = "0x32f22B267Be8CD47FAF93Bcd1CC31059bdc24FD2";
  
  // For testing, we'll try to submit a response directly
  // (This will fail because we're not the authorized ROFL app, but let's try)
  
  const ABI = [
    "function submitResponse(uint256 requestId, string response)"
  ];
  
  const [signer] = await ethers.getSigners();
  const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, signer);
  
  console.log("Attempting to submit response as:", signer.address);
  console.log("(This should fail since we're not the authorized ROFL app)");
  
  try {
    const tx = await contract.submitResponse(
      0, 
      "ROFL (Runtime Off-chain Logic) is a framework by Oasis that enables off-chain computation with on-chain trust guarantees, running in Trusted Execution Environments."
    );
    await tx.wait();
    console.log("Response submitted successfully!");
  } catch (error) {
    console.log("\nExpected error:", error.message);
    console.log("\nThis confirms only the ROFL app can submit responses!");
  }
}

main().catch(console.error);
