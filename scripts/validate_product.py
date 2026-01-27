#!/usr/bin/env python3
"""
Validate that a product exists on-chain.

Usage:
    python validate_product.py <product_id>

Environment variables required:
    AUTONITY_RPC_URL: The RPC URL for the network
    EXCHANGE_URL: The exchange server URL
    VALIDATION_PRIVATE_KEY: Private key for read-only validation

Exit codes:
    0: Product exists and is valid
    1: Product does not exist or validation failed
"""

import os
import sys

import afp


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_product.py <product_id>", file=sys.stderr)
        sys.exit(1)

    product_id = sys.argv[1]

    # Get configuration from environment
    rpc_url = os.environ.get("AUTONITY_RPC_URL")
    exchange_url = os.environ.get("EXCHANGE_URL")
    private_key = os.environ.get("VALIDATION_PRIVATE_KEY")

    if not rpc_url:
        print("Error: AUTONITY_RPC_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    if not exchange_url:
        print("Error: EXCHANGE_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    if not private_key:
        print("Error: VALIDATION_PRIVATE_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    print(f"Validating product: {product_id}")
    print(f"RPC URL: {rpc_url}")
    print(f"Exchange URL: {exchange_url}")

    try:
        app = afp.AFP(
            authenticator=afp.PrivateKeyAuthenticator(private_key),
            rpc_url=rpc_url,
            exchange_url=exchange_url,
        )

        product_api = app.Product()
        info = product_api.get(product_id)
        print(f"Product found: {info}")
        print("Validation successful")
        sys.exit(0)

    except Exception as e:
        print(f"Error: Product validation failed - {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
