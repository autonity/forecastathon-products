# Forecastathon Products

This repository manages product listings for the AFP (Autonomous Futures Protocol) exchange. Products are validated and listed automatically through GitHub Actions workflows.

## Directory Structure

```
├── listing-only/
│   ├── bakerloo/          # Bakerloo testnet products
│   └── mainnet/           # Mainnet products
├── product-registration-and-listing/
│   ├── bakerloo/          # Bakerloo testnet products (full registration)
│   └── mainnet/           # Mainnet products (full registration)
└── scripts/
    ├── validate_product.py   # Validates product exists on-chain
    └── list_product.py       # Lists product on exchange
```

## Workflows

### Listing Only

For products that are **already registered on-chain** and just need to be listed on the exchange.

**On Pull Request:**
- Validates JSON structure
- Validates product exists on-chain
- Validates extended metadata conforms to schema

**On Merge to Master:**
- Lists and reveals product on the exchange

### Product Registration and Listing

For products that need to be **registered on-chain first**, then listed on the exchange.

## Adding a Product

### Listing Only (Product Already Registered)

1. Create a new directory under `listing-only/<environment>/`
2. Add a `product.json` file with the product ID:

```json
{
  "product_id": "0x..."
}
```

3. Open a PR targeting `master`
4. Wait for validation to pass
5. Merge to list the product

### Environment Selection

- `listing-only/bakerloo/` → Uses **Bakerloo** environment
- `listing-only/mainnet/` → Uses **Mainnet** environment

PRs must not contain changes to both environments.

## GitHub Environment Setup

Each environment (Bakerloo, Mainnet) requires:

### Variables
- `AUTONITY_RPC_URL` - RPC endpoint for the network
- `EXCHANGE_URL` - Exchange server URL
- `IPFS_API_URL` - IPFS API endpoint (e.g., `https://rpc.filebase.io`)

### Secrets
- `VALIDATION_PRIVATE_KEY` - Private key for read-only validation
- `IPFS_API_KEY` - IPFS API authentication token
- `EXCHANGE_ADMIN_KEY` - Admin key for listing products

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

## Validation

The validation script checks:

1. Product exists on-chain in the AFP contract
2. Extended metadata CID is valid
3. Extended metadata can be fetched from IPFS
4. Extended metadata conforms to the expected schema
