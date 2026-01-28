#!/usr/bin/env python3
"""
Validate a product specification JSON file using the AFP SDK.

Usage:
    python validate_product_spec.py <json_file>

Environment variables required:
    AUTONITY_RPC_URL: The RPC URL for the network (for contract validation)
    VALIDATION_PRIVATE_KEY: Private key for SDK initialization (required by SDK)

Exit codes:
    0: Validation successful
    1: Validation failed
"""

import json
import os
import sys
from decimal import Decimal

import afp


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_product_spec.py <json_file>", file=sys.stderr)
        sys.exit(1)

    json_file = sys.argv[1]

    # Get configuration from environment
    rpc_url = os.environ.get("AUTONITY_RPC_URL")
    if not rpc_url:
        print("Error: AUTONITY_RPC_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    private_key = os.environ.get("VALIDATION_PRIVATE_KEY")
    if not private_key:
        print(
            "Error: VALIDATION_PRIVATE_KEY environment variable not set",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Validating product specification: {json_file}")
    print(f"RPC URL: {rpc_url}")

    try:
        # 1. Read the JSON file
        with open(json_file, "r") as f:
            raw_data = json.load(f)

        # 2. Extract and validate initial_builder_stake (not part of SDK schema)
        initial_builder_stake_str = raw_data.pop("initial_builder_stake", None)
        if initial_builder_stake_str is not None:
            try:
                initial_builder_stake = Decimal(initial_builder_stake_str)
                print(f"Initial builder stake: {initial_builder_stake}")
            except Exception as e:
                print(
                    f"Error: Invalid initial_builder_stake value: {e}", file=sys.stderr
                )
                sys.exit(1)
        else:
            print("Warning: initial_builder_stake not specified, defaulting to 0")

        # 3. Convert remaining data back to JSON for SDK validation
        product_json = json.dumps(raw_data)

        # 4. Initialize AFP SDK with authenticator (required by SDK)
        authenticator = afp.PrivateKeyAuthenticator(private_key)
        app = afp.AFP(authenticator=authenticator, rpc_url=rpc_url)
        product_api = app.Product()

        # 5. Validate using SDK
        specification = product_api.validate_json(product_json)

        # 6. Output computed product ID for reference
        product_id = product_api.id(specification)
        print("Validation successful!")
        print(f"  Product symbol: {specification.product.base.metadata.symbol}")
        print(f"  Builder: {specification.product.base.metadata.builder}")
        print(f"  Computed product ID: {product_id}")

        sys.exit(0)

    except json.JSONDecodeError as e:
        print("Error: Invalid JSON format", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)

    except afp.exceptions.ValidationError as e:
        print("Error: Product specification validation failed", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print("Error: Unexpected validation error", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
