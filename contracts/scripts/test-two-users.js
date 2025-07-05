const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const [signer] = await ethers.getSigners();
  
  // Contract address
  const WORLDTREE_TEST_ADDRESS = "0xa4e5c09C101A62Aa04A1078228527CD106012d0b";
  
  console.log("Testing WorldtreeTest contract at:", WORLDTREE_TEST_ADDRESS);
  console.log("Signer:", signer.address);
  
  // Get contract instance
  const WorldtreeTest = await ethers.getContractFactory("WorldtreeTest");
  const worldtreeTest = WorldtreeTest.attach(WORLDTREE_TEST_ADDRESS);
  
  // Check if signer is already registered
  const user = await worldtreeTest.users(signer.address);
  console.log("\n=== Registration Status ===");
  console.log("Signer registered:", user.registered);
  
  if (!user.registered) {
    console.log("\n=== Registering Signer ===");
    // Read SNP data from file
    const snpDataPath = path.join(__dirname, '..', 'example_snp_data_user1.txt');
    const snpData = fs.readFileSync(snpDataPath, 'utf8');
    
    const tx = await worldtreeTest.registerUser(snpData);
    await tx.wait();
    console.log("Signer registered successfully");
  }
  
  // Use hardcoded test addresses - user1 already registered, user2 not registered
  const user1Address = signer.address;
  const user2Address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"; // Hardhat account #1
  
  console.log("\n=== Test Addresses ===");
  console.log("User1 (signer):", user1Address);
  console.log("User2 (test):", user2Address);
  
  // Check if user2 is registered
  const user2Info = await worldtreeTest.users(user2Address);
  if (!user2Info.registered) {
    console.log("\n=== Registering User2 with Test Data ===");
    
    // Generate different SNP data for user2
    const snpData2 = `# Example SNP data for User 2 (different from user1)
# rsid	chromosome	position	genotype
rs8628373	2	2738	TT
rs12345678	1	1234	AG
rs987654	3	5678	CC
rs11111111	4	9999	AT
rs22222222	5	8888	GG
rs33333333	6	7777	TG
rs44444444	7	6666	AA
rs55555555	8	5555	CC
rs66666666	9	4444	GT
rs77777777	10	3333	AC
rs88888888	11	2222	TT
rs99999999	12	1111	GA
rs10101010	1	9876	CC
rs20202020	2	8765	AT
rs30303030	3	7654	GG
rs40404040	4	6543	TA
rs50505050	5	5432	CC
rs60606060	6	4321	AG
rs70707070	7	3210	TT
rs80808080	8	2109	GC
rs90909090	9	1098	AA
rs10111213	10	9877	CT
rs11121314	11	8766	GA
rs12131415	12	7655	TG
rs13141516	1	6544	AC
rs14151617	2	5433	GT
rs15161718	3	4322	CA
rs16171819	4	3211	TG
rs17181920	5	2100	GC
rs18192021	6	1099	AT
rs19202122	7	9878	CG
rs20212223	8	8767	TA
rs21222324	9	7656	GC
rs22232425	10	6545	AG
rs23242526	11	5434	TC
rs24252627	12	4323	GA
rs25262728	1	3212	CT
rs26272829	2	2101	AG
rs27282930	3	1090	TG
rs28293031	4	9879	CC
rs29303132	5	8768	AT
rs30313233	6	7657	GG
rs31323334	7	6546	TA
rs32333435	8	5435	CC
rs33343536	9	4324	AG
rs34353637	10	3213	TT
rs35363738	11	2102	GC
rs36373839	12	1091	AA
rs37383940	1	9870	CT
rs38394041	2	8769	GA
rs39404142	3	7658	TG
rs40414243	4	6547	AC
rs41424344	5	5436	GT
rs42434445	6	4325	CA
rs43444546	7	3214	TG
rs44454647	8	2103	GC
rs45464748	9	1092	AT
rs46474849	10	9871	CG
rs47484950	11	8760	TA
rs48495051	12	7659	GC
rs49505152	1	6548	AG
rs50515253	2	5437	TC
rs51525354	3	4326	GA
rs52535455	4	3215	CT
rs53545556	5	2104	AG
rs54555657	6	1093	TG
rs55565758	7	9872	CC
rs56575859	8	8761	AT
rs57585960	9	7650	GG
rs58596061	10	6549	TA
rs59606162	11	5438	CC
rs60616263	12	4327	AG
rs61626364	1	3216	TT
rs62636465	2	2105	GC
rs63646566	3	1094	AA
rs64656667	4	9873	CT
rs65666768	5	8762	GA
rs66676869	6	7651	TG
rs67686970	7	6540	AC
rs68697071	8	5439	GT
rs69707172	9	4328	CA
rs70717273	10	3217	TG
rs71727374	11	2106	GC
rs72737475	12	1095	AT
rs73747576	1	9874	CG
rs74757677	2	8763	TA
rs75767778	3	7652	GC
rs76777879	4	6541	AG
rs77787980	5	5430	TC
rs78798081	6	4329	GA
rs79808182	7	3218	CT
rs80818283	8	2107	AG
rs81828384	9	1096	TG
rs82838485	10	9875	CC
rs83848586	11	8764	AT
rs84858687	12	7653	GG
rs85868788	1	6542	TA
rs86878889	2	5431	CC
rs87888990	3	4320	AG
rs88899091	4	3219	TT
rs89909192	5	2108	GC
rs90919293	6	1097	AA
rs91929394	7	9876	CT
rs92939495	8	8765	GA
rs93949596	9	7654	TG
rs94959697	10	6543	AC
rs95969798	11	5432	GT
rs96979899	12	4321	CA
rs97989900	1	3210	TG
rs98990001	2	2109	GC
rs99000102	3	1098	AT
rs10010203	4	9877	CG
rs10110304	5	8766	TA
rs10210405	6	7655	GC
rs10310506	7	6544	AG
rs10410607	8	5433	TC
rs10510708	9	4322	GA
rs10610809	10	3211	CT
rs10710910	11	2100	AG
rs10811011	12	1099	TG
rs10911112	1	9878	CC
rs11011213	2	8767	AT
rs11111314	3	7656	GG
rs11211415	4	6545	TA
rs11311516	5	5434	CC
rs11411617	6	4323	AG
rs11511718	7	3212	TT
rs11611819	8	2101	GC
rs11711920	9	1090	AA`;
    
    // Connect to user2 wallet (needs to be funded)
    console.log("Attempting to register user2 from signer's account...");
    const tx2 = await worldtreeTest.registerUser(snpData2);
    await tx2.wait();
    console.log("User2 registered successfully");
  }
  
  console.log("\n=== Requesting Analysis Between User1 and User2 ===");
  const tx = await worldtreeTest.requestAnalysis(user1Address, user2Address);
  const receipt = await tx.wait();
  
  // Get request ID from event
  const event = receipt.logs.find(log => log.fragment?.name === 'AnalysisRequested');
  const requestId = event.args[0];
  
  console.log("Analysis requested with ID:", requestId.toString());
  console.log("Requester:", signer.address);
  console.log("User1:", user1Address);
  console.log("User2:", user2Address);
  
  // Monitor for results
  console.log("\n=== Monitoring for Results ===");
  console.log("The ROFL app should process this request within 30 seconds...");
  
  let attempts = 0;
  const maxAttempts = 10; // 5 minutes with 30-second intervals
  
  const checkResults = async () => {
    attempts++;
    console.log(`\nAttempt ${attempts}/${maxAttempts}...`);
    
    const request = await worldtreeTest.getAnalysisRequest(requestId);
    console.log("Status:", request.status);
    
    if (request.status === "completed") {
      console.log("\n🎉 Analysis completed!");
      console.log("Result:", request.result);
      
      try {
        const parsedResult = JSON.parse(request.result);
        console.log("\nParsed Result:");
        console.log("- Relationship:", parsedResult.relationship);
        console.log("- Confidence:", parsedResult.confidence);
        console.log("- Shared SNPs:", parsedResult.shared_snps);
        console.log("- IBS Score:", parsedResult.ibs_score);
      } catch (e) {
        console.log("Could not parse result JSON");
      }
      
      return true;
    } else if (request.status === "failed") {
      console.log("\n❌ Analysis failed!");
      console.log("Result:", request.result);
      return true;
    }
    
    return false;
  };
  
  // Check immediately
  if (await checkResults()) return;
  
  // Then check every 30 seconds
  const interval = setInterval(async () => {
    const completed = await checkResults();
    
    if (completed || attempts >= maxAttempts) {
      clearInterval(interval);
      
      if (attempts >= maxAttempts) {
        console.log("\n⏰ Timeout: Analysis not completed within 5 minutes");
        console.log("The ROFL app might not be running or might be experiencing issues");
      }
    }
  }, 30000);
}

main()
  .then(() => console.log("\n✅ Test completed"))
  .catch((error) => {
    console.error("\n❌ Error:", error);
    process.exit(1);
  });
