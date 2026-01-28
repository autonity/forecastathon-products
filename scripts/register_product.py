#!/usr/bin/env python3
"""
Register a product on-chain using the AFP SDK.

Performs:
1. Validates the product specification
2. Pins extended metadata to IPFS
3. Registers the product using registerPredictionProductFor

Usage:
    python register_product.py <json_file>

Environment variables required:
    AUTONITY_RPC_URL: The RPC URL for the network
    IPFS_API_URL: The IPFS API URL (e.g., https://rpc.filebase.io)
    IPFS_API_KEY: The IPFS API key/token
    REGISTRATION_PRIVATE_KEY: Private key for registration transactions (permissioned)

Exit codes:
    0: Registration successful (prints PRODUCT_ID=<id> to stdout)
    1: Registration failed
"""

import json
import os
import sys
from decimal import Decimal

import afp
from afp.bindings import ProductRegistry
from afp.bindings.erc20 import ERC20


def main():
    if len(sys.argv) != 2:
        print("Usage: python register_product.py <json_file>", file=sys.stderr)
        sys.exit(1)

    json_file = sys.argv[1]

    # Get configuration from environment
    rpc_url = os.environ.get("AUTONITY_RPC_URL")
    ipfs_api_url = os.environ.get("IPFS_API_URL")
    ipfs_api_key = os.environ.get("IPFS_API_KEY")
    private_key = os.environ.get("REGISTRATION_PRIVATE_KEY")

    # Validate environment
    missing = []
    if not rpc_url:
        missing.append("AUTONITY_RPC_URL")
    if not ipfs_api_url:
        missing.append("IPFS_API_URL")
    if not ipfs_api_key:
        missing.append("IPFS_API_KEY")
    if not private_key:
        missing.append("REGISTRATION_PRIVATE_KEY")

    if missing:
        print(
            f"Error: Missing environment variables: {', '.join(missing)}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Registering product from: {json_file}")
    print(f"RPC URL: {rpc_url}")
    print(f"IPFS API URL: {ipfs_api_url}")

    try:
        # 1. Read and parse JSON
        with open(json_file, "r") as f:
            raw_data = json.load(f)

        # 2. Extract initial_builder_stake from user-supplied JSON
        initial_builder_stake_str = raw_data.pop("initial_builder_stake", "0")
        initial_builder_stake = Decimal(initial_builder_stake_str)
        print(f"Initial builder stake: {initial_builder_stake}")

        # 3. Convert to JSON for SDK
        product_json = json.dumps(raw_data)

        # 4. Initialize AFP SDK with authentication
        authenticator = afp.PrivateKeyAuthenticator(private_key)
        app = afp.AFP(
            authenticator=authenticator,
            rpc_url=rpc_url,
            ipfs_api_url=ipfs_api_url,
            ipfs_api_key=ipfs_api_key,
        )
        product_api = app.Product()

        # 5. Validate specification
        print("Validating product specification...")
        specification = product_api.validate_json(product_json)
        print(f"  Symbol: {specification.product.base.metadata.symbol}")
        print(f"  Builder: {specification.product.base.metadata.builder}")

        # Compute product ID
        product_id = product_api.id(specification)
        print(f"  Product ID: {product_id}")

        # 6. Check if product already registered (using direct contract call
        # to avoid needing IPFS access for extended metadata download)
        product_registry = ProductRegistry(
            product_api._w3, product_api._config.product_registry_address
        )
        product_id_bytes = bytes.fromhex(product_id[2:])
        on_chain_product = product_registry.products(product_id_bytes)
        # products() returns (product_type, base_product) where product_type > 0 means registered
        if on_chain_product[0] > 0:
            print(f"Product {product_id} already registered, skipping registration")
            print(f"PRODUCT_ID={product_id}")
            sys.exit(0)

        # 7. Pin extended metadata to IPFS
        print("Pinning extended metadata to IPFS...")
        pinned_specification = product_api.pin(specification)
        extended_metadata_cid = pinned_specification.product.base.extended_metadata
        print(f"  Extended metadata CID: {extended_metadata_cid}")

        # 8. Register product using registerPredictionProductFor
        print("Registering product on-chain...")

        # Get collateral asset decimals for stake conversion
        collateral_address = pinned_specification.product.base.collateral_asset
        erc20 = ERC20(product_api._w3, collateral_address)
        decimals = erc20.decimals()

        # Convert specification to on-chain format
        converted_product = product_api._convert_prediction_product_specification(
            pinned_specification.product, decimals
        )

        # Calculate stake in wei
        stake_wei = int(initial_builder_stake * 10**decimals)

        # Call registerPredictionProductFor (allows msg.sender != builder)
        # product_registry already initialized in step 6
        contract_func = product_registry.register_prediction_product_for(
            converted_product, stake_wei
        )

        # Submit transaction
        tx = product_api._transact(contract_func)

        print("Registration successful!")
        tx_hash = tx.hash.hex() if hasattr(tx.hash, 'hex') else tx.hash
        print(f"  Transaction hash: {tx_hash}")
        print(f"PRODUCT_ID={product_id}")

        sys.exit(0)

    except json.JSONDecodeError as e:
        print("Error: Invalid JSON format", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)

    except afp.exceptions.ValidationError as e:
        print("Error: Product specification validation failed", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)

    except afp.exceptions.IPFSError as e:
        print("Error: Failed to pin metadata to IPFS", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print("Error: Registration failed", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
