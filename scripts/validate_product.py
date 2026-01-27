#!/usr/bin/env python3
"""
Validate that a product exists on-chain and has valid extended metadata.

Usage:
    python validate_product.py <product_id>

Environment variables required:
    AUTONITY_RPC_URL: The RPC URL for the network
    EXCHANGE_URL: The exchange server URL
    VALIDATION_PRIVATE_KEY: Private key for read-only validation
    IPFS_API_URL: The IPFS API URL (e.g., https://api.filebase.io/v1/ipfs)

Environment variables optional:
    IPFS_API_KEY: The IPFS API key/token for authentication

Exit codes:
    0: Product exists and is valid
    1: Product does not exist or validation failed
"""

import os
import sys

import afp
from afp.exceptions import IPFSError, NotFoundError, ValidationError


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_product.py <product_id>", file=sys.stderr)
        sys.exit(1)

    product_id = sys.argv[1]

    # Get configuration from environment
    rpc_url = os.environ.get("AUTONITY_RPC_URL")
    exchange_url = os.environ.get("EXCHANGE_URL")
    private_key = os.environ.get("VALIDATION_PRIVATE_KEY")
    ipfs_api_url = os.environ.get("IPFS_API_URL")
    ipfs_api_key = os.environ.get("IPFS_API_KEY")

    if not rpc_url:
        print("Error: AUTONITY_RPC_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    if not exchange_url:
        print("Error: EXCHANGE_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    if not private_key:
        print("Error: VALIDATION_PRIVATE_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    if not ipfs_api_url:
        print("Error: IPFS_API_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    print(f"Validating product: {product_id}")
    print(f"RPC URL: {rpc_url}")
    print(f"Exchange URL: {exchange_url}")
    print(f"IPFS API URL: {ipfs_api_url}")

    try:
        app = afp.AFP(
            authenticator=afp.PrivateKeyAuthenticator(private_key),
            rpc_url=rpc_url,
            exchange_url=exchange_url,
            ipfs_api_url=ipfs_api_url,
            ipfs_api_key=ipfs_api_key,
        )

        product_api = app.Product()
        info = product_api.get(product_id)
        print(f"Product found: {info}")
        print("Validation successful")
        sys.exit(0)

    except ValidationError as e:
        print(f"Error: Extended metadata schema validation failed.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        print("", file=sys.stderr)
        print("The product exists on-chain but its extended metadata is invalid.", file=sys.stderr)
        print("Please verify:", file=sys.stderr)
        print("  1. The extended metadata conforms to the expected schema", file=sys.stderr)
        print("  2. All required fields are present and have correct types", file=sys.stderr)
        print("  3. The schema CID matches a supported schema version", file=sys.stderr)
        sys.exit(1)

    except IPFSError as e:
        print(f"Error: Failed to fetch extended metadata from IPFS.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        print("", file=sys.stderr)
        print("The product exists on-chain but its extended metadata could not be retrieved.", file=sys.stderr)
        print("Please verify:", file=sys.stderr)
        print("  1. The extended metadata CID is correct and pinned to IPFS", file=sys.stderr)
        print("  2. The IPFS gateway is accessible", file=sys.stderr)
        sys.exit(1)

    except NotFoundError as e:
        print(f"Error: Product '{product_id}' not found.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Please verify:", file=sys.stderr)
        print("  1. The product_id is correct (should be 0x followed by 64 hex characters)", file=sys.stderr)
        print("  2. The product has been registered on the AFP contract", file=sys.stderr)
        print("  3. You are submitting to the correct environment (bakerloo vs mainnet)", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        error_msg = str(e)
        if "Contract call reverted" in error_msg or "Invalid type" in error_msg:
            print(f"Error: Product '{product_id}' does not exist on-chain.", file=sys.stderr)
            print("", file=sys.stderr)
            print("Please verify:", file=sys.stderr)
            print("  1. The product_id is correct (should be 0x followed by 64 hex characters)", file=sys.stderr)
            print("  2. The product has been registered on the AFP contract", file=sys.stderr)
            print("  3. You are submitting to the correct environment (bakerloo vs mainnet)", file=sys.stderr)
        else:
            print(f"Error: Product validation failed.", file=sys.stderr)
            print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
