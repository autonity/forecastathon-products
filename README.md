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
- `startTime` must be at least **two full working days** after PR contribution
- Extended metadata must be pinned on IPFS
- Extended metadata must conform to the expected schemas
- API source (if applicable) must be valid and freely accessible
- All data types must be correct and within expected bounds

## Local Development

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install git+https://github.com/autonity/afp-sdk@v0.6.0-rc.6
```

### Validate a Product Locally

```bash
export AUTONITY_RPC_URL="https://bakerloo.autonity-apis.com"
export EXCHANGE_URL="https://exchange-server-next.up.railway.app"
export VALIDATION_PRIVATE_KEY="your_private_key"
export IPFS_API_URL="https://rpc.filebase.io"
export IPFS_API_KEY="your_filebase_token"

python scripts/validate_product.py <product_id>
```

## Product Registration Paths

### Self-Funded Product Registration

1. Bridge over a small amount of USDC to Autonity from your chosen chain via the [ProtoUSD bridge](https://autonity.protousd.com/). As part of your first bridging operation you will receive a small amount of ATN to pay for a swap on an AMM.
2. Exchange some of your bridged USDC for ATN to ensure you have sufficient gas (1 USDC worth of ATN is more than sufficient to register a few products!). For example, [Mori](https://morifi.xyz/autonity#swap) and [Leibniz](https://leibnizv3.de/#/swap) can be used to make such swaps.
3. You now have sufficient ATN to register a product on the AFP!
4. Using the [AFP SDK](https://pypi.org/project/afp-sdk/), configure a product specification according to your desired product parameters. Ensure you use the required `oracleAddress` and `collateralAsset` from the table above.
5. Generate an extended metadata structure using the SDK and ensure it conforms to the expected schemas (required to be listed on the Autex).
6. Pin the extended metadata on IPFS via any pinning service. The AFP-SDK offers native pinning via Filebase, but any service can be used.
7. Submit your product registration transaction to the AFP, ensuring that the address submitting the transaction is registered for the Forecastathon. This address will be the Product's Builder ID.
8. Open a PR against this repo, adding your ProductId to the `listing-only` folder. Name the file the same as your Product Symbol (e.g. `BTCVOL51W25.json`) and place it in a subfolder named after the first six characters of your builder ID (e.g. `0x123456`).
9. If your product passes the validation checks, it will be listed on the Autex and your PR will be merged.

### Funding Requested Product Registration

**Pre-requisite**: You must be a participant in the [Forecastathon](https://forecastathon.ai/join-now)

1. Using the [AFP SDK](https://pypi.org/project/afp-sdk/), construct a valid product specification using the required `oracleAddress` and `collateralAsset` from the table above.
2. Generate an extended metadata structure using the SDK and ensure it conforms to the expected schemas.
3. Pin the extended metadata on IPFS via any pinning service. The AFP-SDK offers native pinning via Filebase, but any service can be used.
4. Open a PR against this repo, contributing to the `product-registration-and-listing` folder the complete product details (product specification and extended metadata). Please ensure the configured builder ID is your Forecastathon participant address as scores will be associated with this account. Name the file the same as your Product Symbol (e.g. `USCPI-MAR26.json`) and place it in a subfolder named after the first six characters of your builder ID (e.g. `0x123456`).
5. If all checks pass, your product will be registered by the AFP team, and automatically listed on the Autex.

### Which Path Should I Choose?

Choosing the Self-Funded Product Registration path is closer to target state so products registered that way and subsequently listed on Autex will receive a **30% score boost** relative to those registered via the Funding Requested Product Registration path.

## Directory Structure

```
├── listing-only/
│   ├── bakerloo/          # Bakerloo testnet products
│   └── mainnet/           # Mainnet products
├── product-registration-and-listing/
│   ├── bakerloo/          # Bakerloo testnet products
│   └── mainnet/           # Mainnet products
└── scripts/
    ├── validate_product.py   # Validates product exists on-chain and satisfies all requirements
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

**On Merge to Master:**

- Lists and reveals product on the Autex

### Product Registration and Listing

For products that need to be **registered on-chain first**, then listed on the Autex.

**On Pull Request:**

- Validates JSON structure
- Validates extended metadata conforms to schema

**On Merge to Master:**

- Pins extended metadata to IPFS
- Registers product on-chain
- Lists and reveals product on the Autex

## Environment Selection

- `listing-only/bakerloo/` or `product-registration-and-listing/bakerloo/` → Uses **Bakerloo** environment
- `listing-only/mainnet/` or `product-registration-and-listing/mainnet/` → Uses **Mainnet** environment

PRs must not contain changes to both environments.
