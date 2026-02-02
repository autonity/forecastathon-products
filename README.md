# Forecastathon Products

This repository manages product registrations on the AFP (Autonomous Futures Protocol) and product listings on the Autex. Products are validated and listed automatically through GitHub Actions workflows, subject to manual checks.

## Season 4 Products

During Season 4 of the Forecastathon, event contracts will be included as products on the AFP, alongside Forecast Futures similar to previous seasons. However, one crucial difference is that all products in Season 4 are unleveraged and require a minimum and maximum price band. This change significantly reduces the complexity of product building as collateralisation ratios do not have to be explicitly dealt with as part of the product building process.

## Product Requirements

For a product to be listed on the Autex, it must satisfy the following requirements:

### Required Contract Addresses

| Field             | Bakerloo                                     | Mainnet                                      |
| ----------------- | -------------------------------------------- | -------------------------------------------- |
| `oracleAddress`   | `0x72EeD9f7286292f119089F56e3068a3A931FCD49` | `0x06CaDDDf6CC08048596aE051c8ce644725219C73` |
| `collateralAsset` | `0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5` | `0xAE2C6c29F6403fDf5A31e74CC8bFd1D75a3CcB8d` |

### Validation Checks

- `builder` must be a registered participant in the [Forecastathon](https://forecastathon.ai/join-now)
- `startTime` should be at least **two full working days** after PR contribution
- Extended metadata must be pinned on IPFS
- Extended metadata must conform to the expected schemas
- API source (if applicable) must be valid and freely accessible
- All data types must be correct and within expected bounds

## AFP SDK

The [AFP SDK](https://github.com/autonity/afp-sdk) is the primary tool for creating and registering products on the Autonomous Futures Protocol. It provides:

- **Product specification creation** - Build valid product JSON specifications with proper schema validation
- **Extended metadata generation** - Create and validate extended metadata structures
- **IPFS pinning** - Native integration with Filebase for pinning extended metadata
- **On-chain registration** - Register products directly on the AFP smart contracts
- **Product validation** - Validate existing products and their extended metadata

### Installation

```bash
pip install afp-sdk
```

### Documentation

For detailed usage instructions, API reference, and examples, visit the [AFP SDK](https://github.com/autonity/afp-sdk).

## Local Development

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install afp-sdk
```

### IPFS Pinning with Filebase

Extended metadata must be pinned on IPFS. We recommend using [Filebase](https://filebase.com/) which offers a free tier and native integration with the AFP-SDK.

1. Sign up for a free account at [filebase.com](https://filebase.com/)
2. Create an IPFS bucket in the Filebase console
3. Go to **Access Keys** > **Choose Bucket to Generate Token** > Select your IPFS bucket
4. Copy the Secret Access Token
5. Copy `.env.example` to `.env` and add your Filebase token:

The AFP-SDK will use this token to pin your extended metadata when creating products.

### Validate a Product Locally

The validation script supports two modes:

**Pre-registration validation** (validate a product specification JSON file):

```bash
export AUTONITY_RPC_URL="https://rpc1.bakerloo.autonity.org"
export VALIDATION_PRIVATE_KEY="your_private_key"

python scripts/validate.py path/to/product_spec.json
```

**Post-registration validation** (validate an on-chain product):

```bash
export AUTONITY_RPC_URL="https://rpc1.bakerloo.autonity.org"
export VALIDATION_PRIVATE_KEY="your_private_key"
export EXCHANGE_URL="https://exchange-server-next.up.railway.app"
export IPFS_API_URL="https://rpc.filebase.io"
export IPFS_API_KEY="your_filebase_token"

python scripts/validate.py <product_id>
```

## Product Registration Paths

### Self-Funded Product Registration

1. Bridge over a small amount of USDC to Autonity from your chosen chain via the [ProtoUSD bridge](https://autonity.protousd.com/). As part of your first bridging operation you will receive a small amount of ATN to pay for a swap on an AMM.
2. Exchange some of your bridged USDC for ATN to ensure you have sufficient gas (1 USDC worth of ATN is more than sufficient to register a few products!). For example, [Mori](https://morifi.xyz/autonity#swap) and [Leibniz](https://leibnizv3.de/#/swap) can be used to make such swaps.
3. You now have sufficient ATN to register a product on the AFP!
4. Using the [AFP SDK](https://github.com/autonity/afp-sdk), configure a product specification according to your desired product parameters. Ensure you use the required `oracleAddress` and `collateralAsset` from the table above.
5. Generate an extended metadata structure using the SDK and ensure it conforms to the expected schemas (required to be listed on the Autex).
6. Pin the extended metadata on IPFS via any pinning service, using either DAG-CBOR or DAG-JSON codec. The AFP-SDK offers native pinning; any service can be used.
7. Submit your product registration transaction to the AFP, ensuring that the address submitting the transaction is registered for the Forecastathon. This address will be the Product's Builder ID.
8. Open a PR against this repo, adding your ProductId to the `listing-only` folder. Name the file the same as your Product Symbol (e.g. `BTCVOL51W25.json`) and place it in a subfolder named after the first six characters of your builder ID (e.g. `0x123456`). Name your branch using the format `<first-six-characters-of-builder-id>-<symbol>-<network>` (e.g. `0x123456-BTCVOL51W25-mainnet`).
9. If your product passes the validation checks, it will be listed on the Autex and your PR will be merged.

### Funding Requested Product Registration

**Pre-requisite**: You must be a participant in the [Forecastathon](https://forecastathon.ai/join-now)

1. Using the [AFP SDK](https://github.com/autonity/afp-sdk), construct a valid product specification using the required `oracleAddress` and `collateralAsset` from the table above. Note: the `extendedMetadata` field can be omitted or set to `null` as it will be automatically generated when the workflow pins to IPFS.
2. Generate an extended metadata structure using the SDK and ensure it conforms to the expected schemas.
3. Open a PR against this repo, contributing to the `product-registration-and-listing` folder the complete product details (product specification and extended metadata). Please ensure the configured builder ID is your Forecastathon participant address as scores will be associated with this account. Name the file the same as your Product Symbol (e.g. `BTCVOL51W25.json`) and place it in a subfolder named after the first six characters of your builder ID (e.g. `0x123456`). Name your branch using the format `<first-six-characters-of-builder-id>-<symbol>-<network>` (e.g. `0x123456-BTCVOL51W25-mainnet`).
4. If all checks pass, your product will be registered by the AFP team (including IPFS pinning), and automatically listed on the Autex.

### Which Path Should I Choose?

Choosing the Self-Funded Product Registration path is closer to target state so products registered that way and subsequently listed on Autex will receive a **30% score boost** relative to those registered via the Funding Requested Product Registration path.

### Accessing Your Private Key (Web3Auth Social Login)

If you registered for the Forecastathon using social login (Google, Twitter, etc.) via Web3Auth, you can access your private key by:

1. Log in to your wallet at [wallet.web3auth.io](https://wallet.web3auth.io/)
2. Go to **Settings** > **Privacy & Security**
3. Click **Copy Private Key**

This private key is required for self-funded product registration via the AFP SDK.

## Directory Structure

```
├── listing-only/
│   ├── bakerloo/          # Bakerloo testnet products
│   └── mainnet/           # Mainnet products
├── product-registration-and-listing/
│   ├── bakerloo/          # Bakerloo testnet products
│   └── mainnet/           # Mainnet products
└── scripts/
    ├── validate.py           # Validates product specs (pre-registration) or on-chain products (post-registration)
    ├── register_product.py   # Pins to IPFS and registers product on-chain
    └── list_product.py       # Lists product on Autex
```

## Automated Workflows

### Listing Only

For products that are **already registered on-chain** and just need to be listed on the Autex.

**On Pull Request:**

- Retrieve product from on-chain registry
- Retrieve extended metadata from IPFS
- Validates JSON structure
- Validates extended metadata conforms to schema

**On Merge to Main:**

- Lists and reveals product on the Autex

### Product Registration and Listing

For products that need to be **registered on-chain first**, then listed on the Autex.

**On Pull Request:**

- Validates JSON structure
- Validates extended metadata conforms to schema

**On Merge to Main:**

- Pins extended metadata to IPFS
- Registers product on-chain
- Lists and reveals product on the Autex

## Environment Selection

- `listing-only/bakerloo/` or `product-registration-and-listing/bakerloo/` → Uses **Bakerloo** environment
- `listing-only/mainnet/` or `product-registration-and-listing/mainnet/` → Uses **Mainnet** environment

PRs must not contain changes to both environments.

## Agentic Development

An AFP Product Builder agent skill is available to install that includes instructions for AI coding agents on how to build valid products:

```py
npx skills add autonity/afp-sdk
```

It follows the [Agent Skills Specification](https://agentskills.io) that is supported by the majority of coding agents.
