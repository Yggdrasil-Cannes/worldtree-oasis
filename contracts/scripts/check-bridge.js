const { ethers } = require("hardhat");

async function main() {
  const CONTRACT_ADDRESS = "0x32f22B267Be8CD47FAF93Bcd1CC31059bdc24FD2";
  
  // Contract ABI
  const ABI = [
    "function createRequest(string prompt) returns (uint256)",
    "function getRequest(uint256 requestId) view returns (address, string, uint256, bool, string)",
    "function getUnfulfilledRequests(uint256 limit) view returns (uint256[])"
  ];
  
  // Get signer
  const [signer] = await ethers.getSigners();
  console.log("Using account:", signer.address);
  
  // Connect to contract
  const llmBridge = new ethers.Contract(CONTRACT_ADDRESS, ABI, signer);
  
  // Check unfulfilled requests
  console.log("\nChecking unfulfilled requests...");
  const unfulfilledIds = await llmBridge.getUnfulfilledRequests(10);
  console.log("Unfulfilled request IDs:", unfulfilledIds.map(id => id.toString()));
  
  // Check the sample request (ID: 0)
  console.log("\nChecking request ID 0...");
  const [requester, prompt, timestamp, fulfilled, response] = await llmBridge.getRequest(0);
  
  console.log("Requester:", requester);
  console.log("Prompt:", prompt);
  console.log("Timestamp:", new Date(Number(timestamp) * 1000).toISOString());
  console.log("Fulfilled:", fulfilled);
  console.log("Response:", response || "(waiting for response)");
  
  // Create a new request if desired
  const CREATE_NEW = process.argv[2] === "create";
  if (CREATE_NEW) {
    console.log("\nCreating new request...");
    const newPrompt = "What are the key features of Oasis Sapphire?";
    const tx = await llmBridge.createRequest(newPrompt);
    const receipt = await tx.wait();
    console.log("New request created! Transaction:", receipt.hash);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
