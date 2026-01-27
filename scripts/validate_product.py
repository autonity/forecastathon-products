#!/usr/bin/env python3
"""
Validate product_id format.

Usage:
    python validate_product.py <product_id>

Exit codes:
    0: Product ID format is valid
    1: Product ID format is invalid
"""

import re
import sys


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_product.py <product_id>", file=sys.stderr)
        sys.exit(1)

    product_id = sys.argv[1]

    print(f"Validating product ID format: {product_id}")

    # Validate product_id is a valid 32-byte hex string (with 0x prefix)
    pattern = r"^0x[a-fA-F0-9]{64}$"

    if not re.match(pattern, product_id):
        print(f"Error: Invalid product_id format. Expected 0x followed by 64 hex characters.", file=sys.stderr)
        print(f"Got: {product_id}", file=sys.stderr)
        sys.exit(1)

    print("Product ID format is valid")
    sys.exit(0)


if __name__ == "__main__":
    main()
