const { ethers } = require("hardhat");

async function main() {
    console.log("Creating test wallets and funding them...");
    
    // Get the deployer account (with private key)
    const [deployer] = await ethers.getSigners();
    console.log("Deployer address:", deployer.address);
    console.log("Deployer balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)), "ETH");
    
    // Generate two random wallets
    const wallet1 = ethers.Wallet.createRandom();
    const wallet2 = ethers.Wallet.createRandom();
    
    console.log("\n=== Test Wallet 1 ===");
    console.log("Address:", wallet1.address);
    console.log("Private Key:", wallet1.privateKey);
    console.log("Mnemonic:", wallet1.mnemonic.phrase);
    
    console.log("\n=== Test Wallet 2 ===");
    console.log("Address:", wallet2.address);
    console.log("Private Key:", wallet2.privateKey);
    console.log("Mnemonic:", wallet2.mnemonic.phrase);
    
    // Fund each wallet with 1 TEST token
    const fundAmount = ethers.parseEther("1.0");
    
    console.log("\n=== Funding Wallets ===");
    
    // Fund wallet 1
    const tx1 = await deployer.sendTransaction({
        to: wallet1.address,
        value: fundAmount
    });
    await tx1.wait();
    console.log("Funded wallet 1 with 1 TEST token");
    console.log("Transaction hash:", tx1.hash);
    
    // Fund wallet 2
    const tx2 = await deployer.sendTransaction({
        to: wallet2.address,
        value: fundAmount
    });
    await tx2.wait();
    console.log("Funded wallet 2 with 1 TEST token");
    console.log("Transaction hash:", tx2.hash);
    
    // Verify balances
    const balance1 = await ethers.provider.getBalance(wallet1.address);
    const balance2 = await ethers.provider.getBalance(wallet2.address);
    
    console.log("\n=== Final Balances ===");
    console.log("Wallet 1 balance:", ethers.formatEther(balance1), "TEST");
    console.log("Wallet 2 balance:", ethers.formatEther(balance2), "TEST");
    
    // Create wallet instances connected to the provider for testing
    const connectedWallet1 = wallet1.connect(ethers.provider);
    const connectedWallet2 = wallet2.connect(ethers.provider);
    
    console.log("\n=== Test Wallet Setup Complete ===");
    console.log("You can now use these wallets for testing:");
    console.log("- Import them into your testing scripts");
    console.log("- Use the private keys to create signers");
    console.log("- Each wallet has 1 TEST token for gas fees");
    
    // Save wallet info to a file for easy access
    const walletInfo = {
        wallet1: {
            address: wallet1.address,
            privateKey: wallet1.privateKey,
            mnemonic: wallet1.mnemonic.phrase
        },
        wallet2: {
            address: wallet2.address,
            privateKey: wallet2.privateKey,
            mnemonic: wallet2.mnemonic.phrase
        }
    };
    
    const fs = require('fs');
    fs.writeFileSync('test-wallets.json', JSON.stringify(walletInfo, null, 2));
    console.log("\nWallet info saved to test-wallets.json");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    }); 