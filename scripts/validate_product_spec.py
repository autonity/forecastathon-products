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

# Expected addresses per environment
ENVIRONMENT_CONFIG = {
    "bakerloo": {
        "oracle_address": "0x72EeD9f7286292f119089F56e3068a3A931FCD49",
        "collateral_asset": "0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
    },
    "mainnet": {
        "oracle_address": "0x06CaDDDf6CC08048596aE051c8ce644725219C73",
        "collateral_asset": "0xAE2C6c29F6403fDf5A31e74CC8bFd1D75a3CcB8d",
    },
}


def detect_environment(file_path: str) -> str | None:
    """Detect environment from file path."""
    if "/bakerloo/" in file_path:
        return "bakerloo"
    elif "/mainnet/" in file_path:
        return "mainnet"
    return None


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

        # 6. Validate oracle and collateral addresses match environment
        environment = detect_environment(json_file)
        if environment:
            expected = ENVIRONMENT_CONFIG[environment]
            actual_oracle = specification.product.base.oracle_spec.oracle_address
            actual_collateral = specification.product.base.collateral_asset

            print(f"Environment: {environment}")

            if actual_oracle.lower() != expected["oracle_address"].lower():
                print(
                    f"Error: Oracle address mismatch for {environment}",
                    file=sys.stderr,
                )
                print(f"  Expected: {expected['oracle_address']}", file=sys.stderr)
                print(f"  Got: {actual_oracle}", file=sys.stderr)
                sys.exit(1)

            if actual_collateral.lower() != expected["collateral_asset"].lower():
                print(
                    f"Error: Collateral asset mismatch for {environment}",
                    file=sys.stderr,
                )
                print(f"  Expected: {expected['collateral_asset']}", file=sys.stderr)
                print(f"  Got: {actual_collateral}", file=sys.stderr)
                sys.exit(1)

            print(f"  Oracle address: {actual_oracle} ✓")
            print(f"  Collateral asset: {actual_collateral} ✓")
        else:
            print("Warning: Could not detect environment from file path")

        # 7. Output computed product ID for reference
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
