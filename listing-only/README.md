# Listing Only

Contribute pull requests to this folder to request the listing of products you have **already registered** on the AFP.

If you have not yet registered your product, please use the `product-registration-and-listing` folder instead.

## Product Requirements

See the [root README](../README.md#product-requirements) for full requirements. Key points:

| Field             | Bakerloo                                     | Mainnet                                      |
| ----------------- | -------------------------------------------- | -------------------------------------------- |
| `oracleAddress`   | `0x72EeD9f7286292f119089F56e3068a3A931FCD49` | `0x06CaDDDf6CC08048596aE051c8ce644725219C73` |
| `collateralAsset` | `0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5` | `0xAE2C6c29F6403fDf5A31e74CC8bFd1D75a3CcB8d` |

- `builder` must be a registered Forecastathon participant
- `startTime` should be at least **two full working days** after PR contribution
- Extended metadata must be pinned on IPFS and conform to expected schemas

## Folder Structure

- `bakerloo/` - For products on the Bakerloo testnet
- `mainnet/` - For products on Mainnet

## Process

1. Choose the appropriate environment folder (`bakerloo/` or `mainnet/`)
2. Create a folder named after the first six characters of your builder ID (e.g. `0x1234ab/`)
3. Create a file named `<PRODUCT_SYMBOL>.json` (e.g. `BTCVOL51W25.json`)
4. The file should contain:
   ```json
   {
     "product_id": "0x..."
   }
   ```
5. Create a branch using the format `<first-six-characters-of-builder-id>-<symbol>-<network>` (e.g. `0x123456-BTCVOL51W25-mainnet`)
6. Open a pull request against `main`
7. Ensure all validation checks pass

**Note:** Each PR should only contain changes for a single environment. PRs with changes spanning both `bakerloo/` and `mainnet/` will be rejected.
