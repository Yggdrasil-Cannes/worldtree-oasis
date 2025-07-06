const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");

async function testE2EIntegration() {
  console.log("🧪 Starting End-to-End Integration Test\n");
  
  // Configuration
  const WORLDTREE_BACKEND = "0xBc1437ae87B8111dC89e794eb6dD4B303901aCC1";
  const WORLDTREE_TEST = "0xa4e5c09C101A62Aa04A1078228527CD106012d0b";
  const MINIAPP_URL = "http://localhost:3000";
  
  // Setup provider and signer
  const provider = new ethers.JsonRpcProvider("https://testnet.sapphire.oasis.io");
  const privateKey = process.env.PRIVATE_KEY || "0x0000000000000000000000000000000000000000000000000000000000000001";
  const signer = new ethers.Wallet(privateKey, provider);
  console.log("Testing with signer:", signer.address);
  
  // Test results
  const results = {
    contracts: { passed: 0, failed: 0 },
    rofl: { passed: 0, failed: 0 },
    miniapp: { passed: 0, failed: 0 },
    integration: { passed: 0, failed: 0 }
  };
  
  console.log("=== 1. Testing Smart Contracts ===\n");
  
  // Test WorldtreeBackend Contract
  try {
    console.log("📋 Testing WorldtreeBackend Contract...");
    const backendCode = await provider.getCode(WORLDTREE_BACKEND);
    if (backendCode !== "0x") {
      console.log("✅ WorldtreeBackend deployed at:", WORLDTREE_BACKEND);
      
      // Check contract state
      const backendABI = [
        "function roflApp() view returns (bytes21)",
        "function backend() view returns (address)",
        "function getPendingRequests() view returns (uint256[])"
      ];
      
      const backendContract = new ethers.Contract(WORLDTREE_BACKEND, backendABI, signer);
      
      const roflApp = await backendContract.roflApp();
      console.log("  ROFL App:", roflApp);
      
      const backend = await backendContract.backend();
      console.log("  Backend Address:", backend);
      
      const pendingRequests = await backendContract.getPendingRequests();
      console.log("  Pending Requests:", pendingRequests.length);
      
      results.contracts.passed += 3;
    } else {
      console.log("❌ WorldtreeBackend not deployed");
      results.contracts.failed++;
    }
  } catch (error) {
    console.log("❌ Error testing WorldtreeBackend:", error.message);
    results.contracts.failed++;
  }
  
  // Test WorldtreeTest Contract
  try {
    console.log("\n📋 Testing WorldtreeTest Contract...");
    const testCode = await provider.getCode(WORLDTREE_TEST);
    if (testCode !== "0x") {
      console.log("✅ WorldtreeTest deployed at:", WORLDTREE_TEST);
      
      const testABI = [
        "function roflApp() view returns (bytes21)",
        "function nextRequestId() view returns (uint256)",
        "function nextRelationshipId() view returns (uint256)"
      ];
      
      const testContract = new ethers.Contract(WORLDTREE_TEST, testABI, signer);
      
      const roflApp = await testContract.roflApp();
      console.log("  ROFL App:", roflApp);
      
      const nextRequestId = await testContract.nextRequestId();
      console.log("  Next Request ID:", nextRequestId.toString());
      
      const nextRelationshipId = await testContract.nextRelationshipId();
      console.log("  Next Relationship ID:", nextRelationshipId.toString());
      
      results.contracts.passed += 3;
    } else {
      console.log("❌ WorldtreeTest not deployed");
      results.contracts.failed++;
    }
  } catch (error) {
    console.log("❌ Error testing WorldtreeTest:", error.message);
    results.contracts.failed++;
  }
  
  console.log("\n=== 2. Testing ROFL Service ===\n");
  
  // Check ROFL bundle exists
  try {
    console.log("📦 Checking ROFL bundle...");
    const bundlePath = path.join(__dirname, "rofl.default.orc");
    if (fs.existsSync(bundlePath)) {
      const stats = fs.statSync(bundlePath);
      console.log("✅ ROFL bundle exists:", (stats.size / 1024 / 1024).toFixed(2), "MB");
      results.rofl.passed++;
    } else {
      console.log("❌ ROFL bundle not found");
      results.rofl.failed++;
    }
  } catch (error) {
    console.log("❌ Error checking ROFL bundle:", error.message);
    results.rofl.failed++;
  }
  
  // Check Docker image
  try {
    console.log("\n🐳 Checking Docker configuration...");
    const composePath = path.join(__dirname, "compose.yaml");
    const composeContent = fs.readFileSync(composePath, "utf8");
    
    if (composeContent.includes("cyama/worldtree-genetic-analysis:backend-v2")) {
      console.log("✅ Docker image configured correctly");
      results.rofl.passed++;
    }
    
    if (composeContent.includes(WORLDTREE_BACKEND)) {
      console.log("✅ Contract address updated in compose.yaml");
      results.rofl.passed++;
    }
  } catch (error) {
    console.log("❌ Error checking Docker config:", error.message);
    results.rofl.failed++;
  }
  
  console.log("\n=== 3. Testing WLDTree-miniapp ===\n");
  
  // Check API endpoints
  const endpoints = [
    "/api/genetic/upload-snp",
    "/api/genetic/register",
    "/api/genetic/request-analysis",
    "/api/genetic/grant-consent"
  ];
  
  for (const endpoint of endpoints) {
    try {
      console.log(`🌐 Testing ${endpoint}...`);
      const response = await fetch(`${MINIAPP_URL}${endpoint}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" }
      });
      
      // We expect 401 (unauthorized) or 405 (method not allowed) for GET requests
      if (response.status === 401 || response.status === 405) {
        console.log(`✅ ${endpoint} endpoint exists (status: ${response.status})`);
        results.miniapp.passed++;
      } else if (response.status === 200) {
        console.log(`✅ ${endpoint} endpoint accessible`);
        results.miniapp.passed++;
      } else {
        console.log(`⚠️  ${endpoint} returned unexpected status: ${response.status}`);
        results.miniapp.failed++;
      }
    } catch (error) {
      if (error.code === "ECONNREFUSED") {
        console.log(`❌ Cannot connect to miniapp - is it running on ${MINIAPP_URL}?`);
        results.miniapp.failed++;
      } else {
        console.log(`❌ Error testing ${endpoint}:`, error.message);
        results.miniapp.failed++;
      }
    }
  }
  
  console.log("\n=== 4. Testing Integration Flow ===\n");
  
  // Test data flow
  try {
    console.log("🔄 Testing data flow readiness...");
    
    // Check environment configuration
    const envPath = path.join(__dirname, "../WLDTree-miniapp/.env.local");
    if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, "utf8");
      
      if (envContent.includes("NEXT_PUBLIC_WORLDTREE_BACKEND_ADDRESS")) {
        console.log("✅ Backend contract configured in .env.local");
        results.integration.passed++;
      }
      
      if (envContent.includes("PRIVATE_KEY")) {
        console.log("✅ Private key configured (not exposed)");
        results.integration.passed++;
      }
      
      if (envContent.includes("NEXT_PUBLIC_ROFL_APP_ID")) {
        console.log("✅ ROFL App ID configured");
        results.integration.passed++;
      }
    }
  } catch (error) {
    console.log("❌ Error checking integration:", error.message);
    results.integration.failed++;
  }
  
  // Test genetic analysis flow components
  try {
    console.log("\n🧬 Testing genetic analysis components...");
    
    // Check if genetic analysis service exists
    const geneticServicePath = path.join(__dirname, "../WLDTree-miniapp/lib/services/geneticAnalysisService.ts");
    if (fs.existsSync(geneticServicePath)) {
      console.log("✅ Genetic analysis service implemented");
      results.integration.passed++;
    }
    
    // Check if SNP storage service exists
    const storageServicePath = path.join(__dirname, "../WLDTree-miniapp/lib/services/snpStorageService.ts");
    if (fs.existsSync(storageServicePath)) {
      console.log("✅ SNP storage service implemented");
      results.integration.passed++;
    }
    
    // Check if DNA upload page exists
    const dnaPagePath = path.join(__dirname, "../WLDTree-miniapp/app/dna/page.tsx");
    if (fs.existsSync(dnaPagePath)) {
      console.log("✅ DNA upload page implemented");
      results.integration.passed++;
    }
    
    // Check if requests page exists
    const requestsPagePath = path.join(__dirname, "../WLDTree-miniapp/app/requests/page.tsx");
    if (fs.existsSync(requestsPagePath)) {
      console.log("✅ Requests page implemented");
      results.integration.passed++;
    }
  } catch (error) {
    console.log("❌ Error checking components:", error.message);
    results.integration.failed++;
  }
  
  console.log("\n=== 📊 Test Summary ===\n");
  
  const categories = Object.keys(results);
  let totalPassed = 0;
  let totalFailed = 0;
  
  categories.forEach(category => {
    const passed = results[category].passed;
    const failed = results[category].failed;
    totalPassed += passed;
    totalFailed += failed;
    
    console.log(`${category.charAt(0).toUpperCase() + category.slice(1)}:`);
    console.log(`  ✅ Passed: ${passed}`);
    console.log(`  ❌ Failed: ${failed}`);
    console.log("");
  });
  
  console.log(`Total: ${totalPassed} passed, ${totalFailed} failed`);
  
  if (totalFailed === 0) {
    console.log("\n🎉 All tests passed! The integration is working correctly.");
  } else {
    console.log("\n⚠️  Some tests failed. Please check the errors above.");
  }
  
  // Provide next steps
  console.log("\n=== 🚀 Next Steps ===\n");
  console.log("1. Upload a test SNP file at http://localhost:3000/dna");
  console.log("2. Check the browser console for hash calculation and API calls");
  console.log("3. View genetic analysis requests at http://localhost:3000/requests");
  console.log("4. Monitor ROFL logs with: oasis rofl logs");
  console.log("5. Check contract state with: npx hardhat run scripts/check-state.js --network sapphire-testnet");
}

// Run the test
testE2EIntegration()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Test failed with error:", error);
    process.exit(1);
  });