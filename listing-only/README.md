## Purpose

Contribute pull requests to this folder to request the listing of products you have already registered on the AFP. If you have not yet registered your product, please bridge over funds to purchase gas tokens or open a pull request against the `product-registration-and-listing` folder.

## Folder Structure

This folder contains environment-specific subdirectories:

- `bakerloo/` - For products on the Bakerloo testnet
- `mainnet/` - For products on Mainnet

## Process

Please follow the below convention for requesting a product listing on the Autex.

1. Choose the appropriate environment folder (`bakerloo/` or `mainnet/`)
2. If not already done so, create a folder with the name `<FIRST SIX CHARACTERS OF YOUR BUILDER ID>`
3. Within your folder, name your file `<product_symbol>.json`.
4. The file should have the following JSON format:
   ```json
   {
     "product_id": "<YOUR PRODUCT ID>"
   }
   ```
5. Open a pull request against this repository, naming your branch "<FIRST SIX CHARACTERS OF YOUR BUILDER ID>-<product_symbol>"
6. Ensure all the checks pass. Pull requests that fail checks will not be merged.

**Note:** Each PR should only contain changes for a single environment. PRs with changes spanning both `bakerloo/` and `mainnet/` will be rejected.
