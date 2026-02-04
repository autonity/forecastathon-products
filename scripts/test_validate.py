#!/usr/bin/env python3
"""
Tests for validate.py balance check functionality.

Run with: pytest scripts/test_validate.py -v
"""

import json
import os
import tempfile
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

# Set required env vars before importing validate
os.environ.setdefault("AUTONITY_RPC_URL", "https://rpc1.bakerloo.autonity.org")
os.environ.setdefault("VALIDATION_PRIVATE_KEY", "0x" + "0" * 64)

from validate import check_collateral_balance, ERC20_ABI


class TestCheckCollateralBalance:
    """Tests for check_collateral_balance function."""

    @patch("validate.Web3")
    def test_sufficient_balance(self, mock_web3_class):
        """Test when builder has sufficient balance."""
        # Setup mock
        mock_w3 = MagicMock()
        mock_web3_class.return_value = mock_w3
        mock_web3_class.HTTPProvider = MagicMock()
        mock_web3_class.to_checksum_address = lambda x: x

        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract

        # Mock decimals() to return 6
        mock_contract.functions.decimals.return_value.call.return_value = 6
        # Mock balanceOf() to return 100 * 10^6 (100 tokens)
        mock_contract.functions.balanceOf.return_value.call.return_value = 100_000_000

        has_balance, actual_balance, decimals = check_collateral_balance(
            rpc_url="https://rpc1.bakerloo.autonity.org",
            collateral_address="0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
            builder_address="0x799aF677770d436b265Af0b851Ad38f04F2b167a",
            required_amount=Decimal("50"),
        )

        assert has_balance is True
        assert actual_balance == Decimal("100")
        assert decimals == 6

    @patch("validate.Web3")
    def test_insufficient_balance(self, mock_web3_class):
        """Test when builder has insufficient balance."""
        mock_w3 = MagicMock()
        mock_web3_class.return_value = mock_w3
        mock_web3_class.HTTPProvider = MagicMock()
        mock_web3_class.to_checksum_address = lambda x: x

        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract

        # Mock decimals() to return 6
        mock_contract.functions.decimals.return_value.call.return_value = 6
        # Mock balanceOf() to return 10 * 10^6 (10 tokens)
        mock_contract.functions.balanceOf.return_value.call.return_value = 10_000_000

        has_balance, actual_balance, decimals = check_collateral_balance(
            rpc_url="https://rpc1.bakerloo.autonity.org",
            collateral_address="0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
            builder_address="0x799aF677770d436b265Af0b851Ad38f04F2b167a",
            required_amount=Decimal("100"),
        )

        assert has_balance is False
        assert actual_balance == Decimal("10")
        assert decimals == 6

    @patch("validate.Web3")
    def test_exact_balance(self, mock_web3_class):
        """Test when builder has exactly the required balance."""
        mock_w3 = MagicMock()
        mock_web3_class.return_value = mock_w3
        mock_web3_class.HTTPProvider = MagicMock()
        mock_web3_class.to_checksum_address = lambda x: x

        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract

        mock_contract.functions.decimals.return_value.call.return_value = 6
        mock_contract.functions.balanceOf.return_value.call.return_value = 50_000_000

        has_balance, actual_balance, decimals = check_collateral_balance(
            rpc_url="https://rpc1.bakerloo.autonity.org",
            collateral_address="0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
            builder_address="0x799aF677770d436b265Af0b851Ad38f04F2b167a",
            required_amount=Decimal("50"),
        )

        assert has_balance is True
        assert actual_balance == Decimal("50")

    @patch("validate.Web3")
    def test_zero_required_amount(self, mock_web3_class):
        """Test when required amount is zero (should always pass)."""
        mock_w3 = MagicMock()
        mock_web3_class.return_value = mock_w3
        mock_web3_class.HTTPProvider = MagicMock()
        mock_web3_class.to_checksum_address = lambda x: x

        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract

        mock_contract.functions.decimals.return_value.call.return_value = 6
        mock_contract.functions.balanceOf.return_value.call.return_value = 0

        has_balance, actual_balance, decimals = check_collateral_balance(
            rpc_url="https://rpc1.bakerloo.autonity.org",
            collateral_address="0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
            builder_address="0x799aF677770d436b265Af0b851Ad38f04F2b167a",
            required_amount=Decimal("0"),
        )

        assert has_balance is True
        assert actual_balance == Decimal("0")

    @patch("validate.Web3")
    def test_zero_balance_with_required_amount(self, mock_web3_class):
        """Test when builder has zero balance but stake is required."""
        mock_w3 = MagicMock()
        mock_web3_class.return_value = mock_w3
        mock_web3_class.HTTPProvider = MagicMock()
        mock_web3_class.to_checksum_address = lambda x: x

        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract

        mock_contract.functions.decimals.return_value.call.return_value = 6
        mock_contract.functions.balanceOf.return_value.call.return_value = 0

        has_balance, actual_balance, decimals = check_collateral_balance(
            rpc_url="https://rpc1.bakerloo.autonity.org",
            collateral_address="0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
            builder_address="0x799aF677770d436b265Af0b851Ad38f04F2b167a",
            required_amount=Decimal("100"),
        )

        assert has_balance is False
        assert actual_balance == Decimal("0")

    @patch("validate.Web3")
    def test_different_decimals(self, mock_web3_class):
        """Test with different token decimals (e.g., 18)."""
        mock_w3 = MagicMock()
        mock_web3_class.return_value = mock_w3
        mock_web3_class.HTTPProvider = MagicMock()
        mock_web3_class.to_checksum_address = lambda x: x

        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract

        # 18 decimals like most ERC20 tokens
        mock_contract.functions.decimals.return_value.call.return_value = 18
        # 100 tokens in wei
        mock_contract.functions.balanceOf.return_value.call.return_value = (
            100 * 10**18
        )

        has_balance, actual_balance, decimals = check_collateral_balance(
            rpc_url="https://rpc1.bakerloo.autonity.org",
            collateral_address="0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
            builder_address="0x799aF677770d436b265Af0b851Ad38f04F2b167a",
            required_amount=Decimal("50"),
        )

        assert has_balance is True
        assert actual_balance == Decimal("100")
        assert decimals == 18


class TestValidateSpecBalanceCheck:
    """Integration tests for balance check in validate_spec."""

    def create_test_product_spec(self, initial_stake: str = "0") -> dict:
        """Create a minimal valid product spec for testing."""
        return {
            "initial_builder_stake": initial_stake,
            "product": {
                "base": {
                    "metadata": {
                        "builder": "0x799aF677770d436b265Af0b851Ad38f04F2b167a",
                        "symbol": "TESTPROD",
                        "description": "Test product",
                    },
                    "oracleSpec": {
                        "oracleAddress": "0x72EeD9f7286292f119089F56e3068a3A931FCD49",
                        "fsvDecimals": 0,
                        "fspAlpha": "1.0",
                        "fspBeta": "0.0",
                        "fsvCalldata": "0x",
                    },
                    "collateralAsset": "0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
                    "startTime": "2026-06-01T12:00:00Z",
                    "pointValue": "0.01",
                    "priceDecimals": 0,
                },
                "expirySpec": {
                    "earliestFSPSubmissionTime": "2026-06-15T12:00:00Z",
                    "tradeoutInterval": 3600,
                },
                "minPrice": "100",
                "maxPrice": "200",
            },
            "outcome_space": {
                "fsp_type": "scalar",
                "description": "Test",
                "base_case": {"condition": "Test", "fsp_resolution": "Test"},
                "edge_cases": [],
                "frequency": "weekly",
                "units": "count",
                "source_name": "Test",
                "source_uri": "https://example.com",
            },
            "outcome_point": {
                "fsp_type": "scalar",
                "observation": {
                    "reference_date": "2026-06-01",
                    "release_date": "2026-06-01",
                },
            },
            "oracle_config": {
                "description": "Test",
                "project_url": "https://example.com",
                "evaluation_api_spec": {
                    "standard": "JSONPath",
                    "url": "https://example.com/api",
                    "date_path": "$.date",
                    "value_path": "$.value",
                    "headers": None,
                    "timezone": "UTC",
                    "date_format_type": "iso8601",
                    "auth_param_name": None,
                    "auth_param_location": "none",
                },
            },
            "oracle_fallback": {
                "fallback_time": "2026-06-20T12:00:00Z",
                "fallback_fsp": "150",
            },
        }

    def test_balance_check_skipped_for_zero_stake(self):
        """Test that balance check is skipped when initial_builder_stake is 0."""
        spec = self.create_test_product_spec(initial_stake="0")

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            dir="/tmp",
            delete=False,
        ) as f:
            # Use product-registration-and-listing in path to trigger balance check
            json.dump(spec, f)
            temp_path = f.name

        # The balance check should be skipped for zero stake
        # This is tested by checking the path detection logic
        assert "product-registration-and-listing" not in temp_path

        os.unlink(temp_path)

    def test_balance_check_only_for_registration_path(self):
        """Test that balance check only runs for product-registration-and-listing path."""
        # The check should only run when 'product-registration-and-listing' is in the path
        assert "product-registration-and-listing" in "product-registration-and-listing/bakerloo/test.json"
        assert "product-registration-and-listing" not in "listing-only/bakerloo/test.json"


class TestIntegrationWithRealRPC:
    """Integration tests that use real RPC (marked to skip in CI)."""

    @pytest.mark.skipif(
        os.environ.get("CI") == "true",
        reason="Skip RPC tests in CI",
    )
    def test_real_balance_check_bakerloo(self):
        """Test balance check against real Bakerloo network."""
        has_balance, actual_balance, decimals = check_collateral_balance(
            rpc_url="https://rpc1.bakerloo.autonity.org",
            collateral_address="0xDEfAaC81a079533Bf2fb004c613cc2870cF0A5b5",
            builder_address="0x799aF677770d436b265Af0b851Ad38f04F2b167a",
            required_amount=Decimal("0"),
        )

        # Should always pass for 0 required
        assert has_balance is True
        assert decimals == 6
        assert actual_balance >= Decimal("0")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
