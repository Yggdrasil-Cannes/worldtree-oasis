require("@nomicfoundation/hardhat-toolbox");
require("@oasisprotocol/sapphire-hardhat");

// Load environment variables
require("dotenv").config();

const PRIVATE_KEY = process.env.PRIVATE_KEY || "";

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    "sapphire-testnet": {
      url: "https://testnet.sapphire.oasis.io",
      chainId: 0x5aff,
      accounts: [PRIVATE_KEY]
    },
    "sapphire-mainnet": {
      url: "https://sapphire.oasis.io",
      chainId: 0x5afe,
      accounts: [PRIVATE_KEY]
    }
  }
};