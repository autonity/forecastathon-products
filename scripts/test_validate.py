#!/usr/bin/env python3
"""
Tests for validate.py margin capital check functionality.

Run with: pytest scripts/test_validate.py -v
"""

import os
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

# Set required env vars before importing validate
os.environ.setdefault("AUTONITY_RPC_URL", "https://rpc1.bakerloo.autonity.org")
os.environ.setdefault("VALIDATION_PRIVATE_KEY", "0x" + "0" * 64)

from validate import check_margin_capital


class TestCheckMarginCapital:
    """Tests for check_margin_capital function."""

    def test_sufficient_capital(self):
        """Test when builder has sufficient margin capital."""
        mock_margin_api = MagicMock()
        mock_margin_contract = MagicMock()
        mock_margin_api._margin_contract.return_value = mock_margin_contract
        mock_margin_api._decimals.return_value = 6

        # Mock capital() to return 100 * 10^6 (100 tokens)
        mock_margin_contract.capital.return_value = 100_000_000

        has_capital, actual_capital = check_margin_capital(
            margin_api=mock_margin_api,
            collateral_address="0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
            builder_address="0x799aF677770d436b265Af0b851Ad38f04F2b167a",
            required_amount=Decimal("50"),
        )

        assert has_capital is True
        assert actual_capital == Decimal("100")

    def test_insufficient_capital(self):
        """Test when builder has insufficient margin capital."""
        mock_margin_api = MagicMock()
        mock_margin_contract = MagicMock()
        mock_margin_api._margin_contract.return_value = mock_margin_contract
        mock_margin_api._decimals.return_value = 6

        # Mock capital() to return 10 * 10^6 (10 tokens)
        mock_margin_contract.capital.return_value = 10_000_000

        has_capital, actual_capital = check_margin_capital(
            margin_api=mock_margin_api,
            collateral_address="0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
            builder_address="0x799aF677770d436b265Af0b851Ad38f04F2b167a",
            required_amount=Decimal("100"),
        )

        assert has_capital is False
        assert actual_capital == Decimal("10")

    def test_exact_capital(self):
        """Test when builder has exactly the required capital."""
        mock_margin_api = MagicMock()
        mock_margin_contract = MagicMock()
        mock_margin_api._margin_contract.return_value = mock_margin_contract
        mock_margin_api._decimals.return_value = 6

        mock_margin_contract.capital.return_value = 50_000_000

        has_capital, actual_capital = check_margin_capital(
            margin_api=mock_margin_api,
            collateral_address="0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
            builder_address="0x799aF677770d436b265Af0b851Ad38f04F2b167a",
            required_amount=Decimal("50"),
        )

        assert has_capital is True
        assert actual_capital == Decimal("50")

    def test_zero_required_amount(self):
        """Test when required amount is zero (should always pass)."""
        mock_margin_api = MagicMock()
        mock_margin_contract = MagicMock()
        mock_margin_api._margin_contract.return_value = mock_margin_contract
        mock_margin_api._decimals.return_value = 6

        mock_margin_contract.capital.return_value = 0

        has_capital, actual_capital = check_margin_capital(
            margin_api=mock_margin_api,
            collateral_address="0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
            builder_address="0x799aF677770d436b265Af0b851Ad38f04F2b167a",
            required_amount=Decimal("0"),
        )

        assert has_capital is True
        assert actual_capital == Decimal("0")

    def test_zero_capital_with_required_amount(self):
        """Test when builder has zero capital but stake is required."""
        mock_margin_api = MagicMock()
        mock_margin_contract = MagicMock()
        mock_margin_api._margin_contract.return_value = mock_margin_contract
        mock_margin_api._decimals.return_value = 6

        mock_margin_contract.capital.return_value = 0

        has_capital, actual_capital = check_margin_capital(
            margin_api=mock_margin_api,
            collateral_address="0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
            builder_address="0x799aF677770d436b265Af0b851Ad38f04F2b167a",
            required_amount=Decimal("100"),
        )

        assert has_capital is False
        assert actual_capital == Decimal("0")

    def test_different_decimals(self):
        """Test with different token decimals (e.g., 18)."""
        mock_margin_api = MagicMock()
        mock_margin_contract = MagicMock()
        mock_margin_api._margin_contract.return_value = mock_margin_contract
        mock_margin_api._decimals.return_value = 18

        # 100 tokens with 18 decimals
        mock_margin_contract.capital.return_value = 100 * 10**18

        has_capital, actual_capital = check_margin_capital(
            margin_api=mock_margin_api,
            collateral_address="0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
            builder_address="0x799aF677770d436b265Af0b851Ad38f04F2b167a",
            required_amount=Decimal("50"),
        )

        assert has_capital is True
        assert actual_capital == Decimal("100")


class TestValidateSpecMarginCheck:
    """Integration tests for margin check in validate_spec."""

    def test_margin_check_only_for_registration_path(self):
        """Test that margin check only runs for product-registration-and-listing path."""
        assert "product-registration-and-listing" in "product-registration-and-listing/bakerloo/test.json"
        assert "product-registration-and-listing" not in "listing-only/bakerloo/test.json"


class TestIntegrationWithRealRPC:
    """Integration tests that use real RPC (marked to skip in CI)."""

    @pytest.mark.skipif(
        os.environ.get("CI") == "true",
        reason="Skip RPC tests in CI",
    )
    def test_real_margin_capital_check_bakerloo(self):
        """Test margin capital check against real Bakerloo network."""
        import afp

        auth = afp.PrivateKeyAuthenticator("0x" + "1" * 64)
        app = afp.AFP(
            authenticator=auth,
            rpc_url="https://rpc1.bakerloo.autonity.org",
        )
        margin_api = app.MarginAccount()

        # Test with an address that has capital deposited
        has_capital, actual_capital = check_margin_capital(
            margin_api=margin_api,
            collateral_address="0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
            builder_address="0x9c4D46aa6cFF3Bd55642d285893557633D863b91",
            required_amount=Decimal("0"),
        )

        assert has_capital is True
        assert actual_capital > Decimal("0")

    @pytest.mark.skipif(
        os.environ.get("CI") == "true",
        reason="Skip RPC tests in CI",
    )
    def test_real_margin_capital_check_zero_capital(self):
        """Test margin capital check for address with no capital."""
        import afp

        auth = afp.PrivateKeyAuthenticator("0x" + "1" * 64)
        app = afp.AFP(
            authenticator=auth,
            rpc_url="https://rpc1.bakerloo.autonity.org",
        )
        margin_api = app.MarginAccount()

        # Test with an address that has no capital
        has_capital, actual_capital = check_margin_capital(
            margin_api=margin_api,
            collateral_address="0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
            builder_address="0x799aF677770d436b265Af0b851Ad38f04F2b167a",
            required_amount=Decimal("100"),
        )

        assert has_capital is False
        assert actual_capital == Decimal("0")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
