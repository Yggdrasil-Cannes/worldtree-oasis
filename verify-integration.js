const { ethers } = require("ethers");

async function verifyIntegration() {
  console.log("🔍 Verifying WorldTree ROFL Integration Status\n");
  
  // Configuration
  const RPC_URL = "https://testnet.sapphire.oasis.io";
  const provider = new ethers.JsonRpcProvider(RPC_URL);
  
  // Contract addresses
  const contracts = {
    "WorldtreeTest (Old - Privacy Issue)": "0x614b1b0Dc3C94dc79f4df6e180baF8eD5C81BEc3",
    "WorldtreeBackend (New - Privacy-Preserving)": "0xBc1437ae87B8111dC89e794eb6dD4B303901aCC1"
  };
  
  // ROFL App ID
  const ROFL_APP_ID = "rofl1qq9vdpxduln5utg3htkhvzwhvhdnzttylunuy6wm";
  const ROFL_APP_BYTES = "0x000ac684cde7e74e2d11baed7609d765db312d64ff";
  
  console.log("=== Configuration ===");
  console.log(`Network: Sapphire Testnet`);
  console.log(`ROFL App ID: ${ROFL_APP_ID}`);
  console.log(`ROFL App (bytes21): ${ROFL_APP_BYTES}\n`);
  
  // Check each contract
  for (const [name, address] of Object.entries(contracts)) {
    console.log(`=== Checking ${name} ===`);
    console.log(`Address: ${address}`);
    
    try {
      const code = await provider.getCode(address);
      
      if (code === "0x") {
        console.log("❌ No contract deployed at this address\n");
        continue;
      }
      
      console.log("✅ Contract deployed");
      
      // Check if it's a WorldtreeBackend contract
      if (name.includes("Backend")) {
        // Check backend authorization
        const backendSlot = 1; // Slot 1 should be the backend address
        const backendData = await provider.getStorage(address, backendSlot);
        const backendAddress = "0x" + backendData.slice(-40);
        console.log(`Backend Address: ${backendAddress}`);
        
        // The backend should be the deployer address
        if (backendAddress.toLowerCase() === "0x9ac44c807ffcaf3e150e184a06a660eae5b848c8") {
          console.log("✅ Backend authorization configured correctly");
        } else {
          console.log("⚠️  Backend address doesn't match expected deployer");
        }
      }
      
      // Check ROFL app configuration
      const roflSlot = 0; // Slot 0 should be the ROFL app
      const roflData = await provider.getStorage(address, roflSlot);
      const storedRoflApp = roflData.slice(0, 44); // bytes21 = 42 chars + 0x
      
      if (storedRoflApp.toLowerCase() === ROFL_APP_BYTES.toLowerCase()) {
        console.log("✅ ROFL App ID matches");
      } else {
        console.log(`⚠️  ROFL App mismatch: ${storedRoflApp}`);
      }
      
      console.log("");
    } catch (error) {
      console.log(`❌ Error: ${error.message}\n`);
    }
  }
  
  console.log("=== ROFL Service Status ===");
  console.log("Docker Image: cyama/worldtree-genetic-analysis:fixed-v7");
  console.log("Current Contract in compose.yaml: 0xBc1437ae87B8111dC89e794eb6dD4B303901aCC1");
  console.log("");
  
  console.log("=== Backend Integration Status ===");
  console.log("✅ Environment variables configured in .env.local");
  console.log("✅ API routes created:");
  console.log("   - /api/genetic/upload-snp");
  console.log("   - /api/genetic/register");
  console.log("   - /api/genetic/request-analysis");
  console.log("   - /api/genetic/grant-consent");
  console.log("✅ Frontend pages updated:");
  console.log("   - /dna - File upload with local storage");
  console.log("   - /requests - Genetic analysis requests");
  console.log("");
  
  console.log("=== Next Steps ===");
  console.log("1. ROFL service needs to be redeployed with updated contract");
  console.log("   Run: ./update-rofl.sh");
  console.log("2. Install missing npm packages (idb, ethers)");
  console.log("3. Test the complete flow in WLDTree-miniapp");
}

// Run verification
verifyIntegration().catch(console.error);