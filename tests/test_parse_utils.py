"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: Unit tests for shared parsing helpers.
Agent customization: Update only if shared parsing behavior changes.
"""

from __future__ import annotations

import pytest

from oci_langgraph_a2a_blueprint.parse_utils import parse_float, parse_int


def test_parse_int_uses_default_for_missing_value() -> None:
    """Verify missing integer values resolve to the provided default."""
    assert parse_int(None, default=8000, variable_name="PORT") == 8000


def test_parse_int_rejects_invalid_value() -> None:
    """Verify invalid integer values fail with a clear error."""
    with pytest.raises(ValueError, match="PORT must be an integer"):
        parse_int("abc", default=8000, variable_name="PORT")


def test_parse_float_uses_default_for_missing_value() -> None:
    """Verify missing float values resolve to the provided default."""
    assert parse_float(None, default=1.0, variable_name="SLEEP") == 1.0


def test_parse_float_rejects_invalid_value() -> None:
    """Verify invalid float values fail with a clear error."""
    with pytest.raises(ValueError, match="SLEEP must be a float"):
        parse_float("abc", default=1.0, variable_name="SLEEP")
