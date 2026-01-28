#!/usr/bin/env python3
"""
Unified validation script for AFP products.

Supports two modes:
1. Pre-registration: Validate a product specification JSON file
2. Post-registration: Validate a product exists on-chain with valid extended metadata

Usage:
    python validate.py <json_file>    # Pre-registration (file ends with .json)
    python validate.py <product_id>   # Post-registration (starts with 0x)

Environment variables required:
    AUTONITY_RPC_URL: The RPC URL for the network
    VALIDATION_PRIVATE_KEY: Private key for SDK initialization

Environment variables required for post-registration validation:
    IPFS_API_URL: The IPFS API URL (e.g., https://rpc.filebase.io)
    EXCHANGE_URL: The exchange server URL

Environment variables optional:
    IPFS_API_KEY: The IPFS API key/token for authentication

Environment variables for builder registration check (all required if any set):
    DB_HOST: Database host
    DB_PORT: Database port
    DB_NAME: Database name
    DB_USERNAME: Database username
    DB_PWD: Database password

Environment variables for post-registration validation:
    VALIDATE_ENVIRONMENT: Environment name (bakerloo or mainnet) for address validation

Exit codes:
    0: Validation successful
    1: Validation failed
"""

import json
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal

import afp
import psycopg2
from afp.exceptions import IPFSError, NotFoundError, ValidationError

# Minimum working days required between PR submission and product start time
MIN_WORKING_DAYS_BEFORE_START = 2

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


def count_working_days(start_date: datetime, end_date: datetime) -> int:
    """
    Count the number of full working days between two dates.
    Working days are Monday (0) through Friday (4).
    Returns the count of complete working days between start and end.
    """
    from datetime import timedelta

    if end_date <= start_date:
        return 0

    working_days = 0
    # Start from the next calendar day after start_date
    current = (start_date + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

    while current <= end:
        # Monday = 0, Sunday = 6
        if current.weekday() < 5:  # Monday to Friday
            working_days += 1
        current += timedelta(days=1)

    return working_days


def detect_environment(file_path: str) -> str | None:
    """Detect environment from file path."""
    if "/bakerloo/" in file_path or "\\bakerloo\\" in file_path:
        return "bakerloo"
    elif "/mainnet/" in file_path or "\\mainnet\\" in file_path:
        return "mainnet"
    return None


def detect_input_type(arg: str) -> str:
    """Detect whether input is a JSON file or product ID."""
    if arg.endswith(".json"):
        return "spec"
    elif arg.startswith("0x") and len(arg) == 66:
        return "product_id"
    else:
        # Try to determine by checking if it's a file
        if os.path.isfile(arg):
            return "spec"
        return "unknown"


def check_builder_registered(builder_address: str) -> bool:
    """
    Check if a builder address is registered in the Forecastathon.

    Requires environment variables:
        DB_HOST: Database host
        DB_PORT: Database port
        DB_NAME: Database name
        DB_USERNAME: Database username
        DB_PWD: Database password

    Args:
        builder_address: The wallet address to check

    Returns:
        True if the builder is registered, False otherwise
    """
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT")
    db_name = os.environ.get("DB_NAME")
    db_user = os.environ.get("DB_USERNAME")
    db_password = os.environ.get("DB_PWD")

    if not all([db_host, db_port, db_name, db_user, db_password]):
        raise RuntimeError(
            "Database configuration incomplete. Required: DB_HOST, DB_PORT, DB_NAME, DB_USERNAME, DB_PWD"
        )

    try:
        conn = psycopg2.connect(
            host=db_host,
            port=int(db_port),
            dbname=db_name,
            user=db_user,
            password=db_password,
            sslmode="require",
        )
        cursor = conn.cursor()

        # Query to check if the wallet address exists (case-insensitive)
        cursor.execute(
            "SELECT 1 FROM forecastathon.users WHERE LOWER(wallet_address) = LOWER(%s)",
            (builder_address,),
        )

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        return result is not None

    except psycopg2.Error as e:
        raise RuntimeError(f"Database error: {e}")


def validate_spec(json_file: str, rpc_url: str, private_key: str) -> None:
    """Validate a product specification JSON file (pre-registration)."""
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
                    f"Error: Incorrect oracle address for {environment}",
                    file=sys.stderr,
                )
                print(f"  Expected: {expected['oracle_address']}", file=sys.stderr)
                print(f"  Got: {actual_oracle}", file=sys.stderr)
                sys.exit(1)

            if actual_collateral.lower() != expected["collateral_asset"].lower():
                print(
                    f"Error: Incorrect collateral asset for {environment}",
                    file=sys.stderr,
                )
                print(f"  Expected: {expected['collateral_asset']}", file=sys.stderr)
                print(f"  Got: {actual_collateral}", file=sys.stderr)
                sys.exit(1)

            print(f"  Oracle address: {actual_oracle} ✓")
            print(f"  Collateral asset: {actual_collateral} ✓")
        else:
            print("Warning: Could not detect environment from file path")

        # 7. Validate startTime is at least 2 working days in the future (mainnet only)
        if environment == "mainnet":
            start_time = specification.product.base.start_time
            now = datetime.now(timezone.utc)
            working_days = count_working_days(now, start_time)

            print(f"  Start time: {start_time.isoformat()}")
            print(f"  Current time: {now.isoformat()}")
            print(f"  Working days until start: {working_days}")

            if working_days < MIN_WORKING_DAYS_BEFORE_START:
                print(
                    f"Error: startTime must be at least {MIN_WORKING_DAYS_BEFORE_START} "
                    f"full working days in the future",
                    file=sys.stderr,
                )
                print(f"  Start time: {start_time.isoformat()}", file=sys.stderr)
                print(f"  Current time: {now.isoformat()}", file=sys.stderr)
                print(
                    f"  Working days until start: {working_days} "
                    f"(need at least {MIN_WORKING_DAYS_BEFORE_START})",
                    file=sys.stderr,
                )
                print("", file=sys.stderr)
                print(
                    "Working days are Monday through Friday. Weekends do not count.",
                    file=sys.stderr,
                )
                sys.exit(1)

            print(f"  Working days check: {working_days} >= {MIN_WORKING_DAYS_BEFORE_START} ✓")

        # 8. Validate builder is a registered Forecastathon participant
        db_configured = all([
            os.environ.get("DB_HOST"),
            os.environ.get("DB_PORT"),
            os.environ.get("DB_NAME"),
            os.environ.get("DB_USERNAME"),
            os.environ.get("DB_PWD"),
        ])
        if db_configured:
            builder_address = specification.product.base.metadata.builder
            print(f"  Checking builder registration: {builder_address}")

            try:
                is_registered = check_builder_registered(builder_address)
                if not is_registered:
                    print(
                        f"Error: Builder {builder_address} is not a registered "
                        f"Forecastathon participant",
                        file=sys.stderr,
                    )
                    print("", file=sys.stderr)
                    print(
                        "Please register at https://forecastathon.ai/join-now",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                print(f"  Builder registration: {builder_address} ✓")
            except RuntimeError as e:
                print(
                    f"Error: Could not verify builder registration: {e}",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            print("  Builder registration check: skipped (DB_* env vars not set)")

        # 9. Output computed product ID for reference
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

    except ValidationError as e:
        print("Error: Product specification validation failed", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print("Error: Unexpected validation error", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)


def validate_product(
    product_id: str,
    rpc_url: str,
    private_key: str,
    exchange_url: str,
    ipfs_api_url: str,
    ipfs_api_key: str | None,
) -> None:
    """Validate a product exists on-chain with valid extended metadata (post-registration)."""
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

        # Validate oracle and collateral addresses match environment
        environment = os.environ.get("VALIDATE_ENVIRONMENT")
        if environment and environment in ENVIRONMENT_CONFIG:
            expected = ENVIRONMENT_CONFIG[environment]
            actual_oracle = info.product.base.oracle_spec.oracle_address
            actual_collateral = info.product.base.collateral_asset

            print(f"Environment: {environment}")

            if actual_oracle.lower() != expected["oracle_address"].lower():
                print(
                    f"Error: Incorrect oracle address for {environment}",
                    file=sys.stderr,
                )
                print(f"  Expected: {expected['oracle_address']}", file=sys.stderr)
                print(f"  Got: {actual_oracle}", file=sys.stderr)
                sys.exit(1)

            if actual_collateral.lower() != expected["collateral_asset"].lower():
                print(
                    f"Error: Incorrect collateral asset for {environment}",
                    file=sys.stderr,
                )
                print(f"  Expected: {expected['collateral_asset']}", file=sys.stderr)
                print(f"  Got: {actual_collateral}", file=sys.stderr)
                sys.exit(1)

            print(f"  Oracle address: {actual_oracle} ✓")
            print(f"  Collateral asset: {actual_collateral} ✓")

            # Validate startTime is at least 2 working days in the future (mainnet only)
            if environment == "mainnet":
                start_time = info.product.base.start_time
                now = datetime.now(timezone.utc)
                working_days = count_working_days(now, start_time)

                print(f"  Start time: {start_time.isoformat()}")
                print(f"  Current time: {now.isoformat()}")
                print(f"  Working days until start: {working_days}")

                if working_days < MIN_WORKING_DAYS_BEFORE_START:
                    print(
                        f"Error: startTime must be at least {MIN_WORKING_DAYS_BEFORE_START} "
                        f"full working days in the future",
                        file=sys.stderr,
                    )
                    print(f"  Start time: {start_time.isoformat()}", file=sys.stderr)
                    print(f"  Current time: {now.isoformat()}", file=sys.stderr)
                    print(
                        f"  Working days until start: {working_days} "
                        f"(need at least {MIN_WORKING_DAYS_BEFORE_START})",
                        file=sys.stderr,
                    )
                    print("", file=sys.stderr)
                    print(
                        "Working days are Monday through Friday. Weekends do not count.",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                print(f"  Working days check: {working_days} >= {MIN_WORKING_DAYS_BEFORE_START} ✓")
        else:
            print("Warning: VALIDATE_ENVIRONMENT not set, skipping oracle/collateral/startTime checks")

        # Validate builder is a registered Forecastathon participant
        db_configured = all([
            os.environ.get("DB_HOST"),
            os.environ.get("DB_PORT"),
            os.environ.get("DB_NAME"),
            os.environ.get("DB_USERNAME"),
            os.environ.get("DB_PWD"),
        ])
        if db_configured:
            builder_address = info.product.base.metadata.builder
            print(f"Checking builder registration: {builder_address}")

            try:
                is_registered = check_builder_registered(builder_address)
                if not is_registered:
                    print(
                        f"Error: Builder {builder_address} is not a registered "
                        f"Forecastathon participant",
                        file=sys.stderr,
                    )
                    print("", file=sys.stderr)
                    print(
                        "Please register at https://forecastathon.ai/join-now",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                print(f"Builder registration: {builder_address} ✓")
            except RuntimeError as e:
                print(
                    f"Error: Could not verify builder registration: {e}",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            print("Builder registration check: skipped (DB_* env vars not set)")

        print("Validation successful")
        sys.exit(0)

    except ValidationError as e:
        print("Error: Extended metadata schema validation failed.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        print("", file=sys.stderr)
        print(
            "The product exists on-chain but its extended metadata is invalid.",
            file=sys.stderr,
        )
        print("Please verify:", file=sys.stderr)
        print(
            "  1. The extended metadata conforms to the expected schema", file=sys.stderr
        )
        print(
            "  2. All required fields are present and have correct types", file=sys.stderr
        )
        print(
            "  3. The schema CID matches a supported schema version", file=sys.stderr
        )
        sys.exit(1)

    except IPFSError as e:
        print("Error: Failed to fetch extended metadata from IPFS.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        print("", file=sys.stderr)
        print(
            "The product exists on-chain but its extended metadata could not be retrieved.",
            file=sys.stderr,
        )
        print("Please verify:", file=sys.stderr)
        print(
            "  1. The extended metadata CID is correct and pinned to IPFS",
            file=sys.stderr,
        )
        print("  2. The IPFS gateway is accessible", file=sys.stderr)
        sys.exit(1)

    except NotFoundError as e:
        print(f"Error: Product '{product_id}' not found.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Please verify:", file=sys.stderr)
        print(
            "  1. The product_id is correct (should be 0x followed by 64 hex characters)",
            file=sys.stderr,
        )
        print(
            "  2. The product has been registered on the AFP contract", file=sys.stderr
        )
        print(
            "  3. You are submitting to the correct environment (bakerloo vs mainnet)",
            file=sys.stderr,
        )
        sys.exit(1)

    except Exception as e:
        error_msg = str(e)
        if "Contract call reverted" in error_msg or "Invalid type" in error_msg:
            print(
                f"Error: Product '{product_id}' does not exist on-chain.",
                file=sys.stderr,
            )
            print("", file=sys.stderr)
            print("Please verify:", file=sys.stderr)
            print(
                "  1. The product_id is correct (should be 0x followed by 64 hex characters)",
                file=sys.stderr,
            )
            print(
                "  2. The product has been registered on the AFP contract",
                file=sys.stderr,
            )
            print(
                "  3. You are submitting to the correct environment (bakerloo vs mainnet)",
                file=sys.stderr,
            )
        else:
            print("Error: Product validation failed.", file=sys.stderr)
            print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python validate.py <json_file>   # Pre-registration validation",
            file=sys.stderr,
        )
        print(
            "       python validate.py <product_id>  # Post-registration validation",
            file=sys.stderr,
        )
        sys.exit(1)

    arg = sys.argv[1]
    input_type = detect_input_type(arg)

    # Common environment variables
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

    if input_type == "spec":
        # Pre-registration validation
        validate_spec(arg, rpc_url, private_key)

    elif input_type == "product_id":
        # Post-registration validation - requires additional env vars
        exchange_url = os.environ.get("EXCHANGE_URL")
        if not exchange_url:
            print(
                "Error: EXCHANGE_URL environment variable not set", file=sys.stderr
            )
            sys.exit(1)

        ipfs_api_url = os.environ.get("IPFS_API_URL")
        if not ipfs_api_url:
            print(
                "Error: IPFS_API_URL environment variable not set", file=sys.stderr
            )
            sys.exit(1)

        ipfs_api_key = os.environ.get("IPFS_API_KEY")  # Optional

        validate_product(
            arg, rpc_url, private_key, exchange_url, ipfs_api_url, ipfs_api_key
        )

    else:
        print(f"Error: Could not determine input type for '{arg}'", file=sys.stderr)
        print("", file=sys.stderr)
        print("Expected one of:", file=sys.stderr)
        print("  - Path to a .json file (pre-registration validation)", file=sys.stderr)
        print(
            "  - Product ID starting with 0x (post-registration validation)",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
