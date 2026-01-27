#!/usr/bin/env python3
"""
List and reveal a product on the AFP exchange.

Usage:
    python list_product.py <product_id>

Environment variables required:
    AUTONITY_RPC_URL: The RPC URL for the network
    EXCHANGE_URL: The exchange server URL
    EXCHANGE_ADMIN_KEY: The private key for authentication
"""

import os
import sys

import afp


def main():
    if len(sys.argv) != 2:
        print("Usage: python list_product.py <product_id>", file=sys.stderr)
        sys.exit(1)

    product_id = sys.argv[1]

    # Get configuration from environment
    rpc_url = os.environ.get("AUTONITY_RPC_URL")
    exchange_url = os.environ.get("EXCHANGE_URL")
    private_key = os.environ.get("EXCHANGE_ADMIN_KEY")

    if not rpc_url:
        print("Error: AUTONITY_RPC_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    if not exchange_url:
        print("Error: EXCHANGE_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    if not private_key:
        print("Error: EXCHANGE_ADMIN_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    print(f"Connecting to AFP...")
    print(f"  RPC URL: {rpc_url}")
    print(f"  Exchange URL: {exchange_url}")

    app = afp.AFP(
        authenticator=afp.PrivateKeyAuthenticator(private_key),
        rpc_url=rpc_url,
        exchange_url=exchange_url,
    )

    admin = app.Admin()

    print(f"Listing product: {product_id}")
    admin.list_product(product_id)
    print("Product listed successfully")

    print(f"Revealing product: {product_id}")
    admin.reveal_product(product_id)
    print("Product revealed successfully")


if __name__ == "__main__":
    main()
