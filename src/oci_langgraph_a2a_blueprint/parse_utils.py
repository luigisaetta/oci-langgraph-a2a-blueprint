"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: Small parsing helpers shared by configuration modules.
Agent customization: Do not modify for normal agent replacement.
"""

from __future__ import annotations


def parse_int(value: str | None, default: int, variable_name: str) -> int:
    """Parse an integer configuration value.

    Args:
        value: Raw string value.
        default: Default value used when `value` is missing.
        variable_name: Configuration variable name for error messages.

    Returns:
        Parsed integer value.

    Raises:
        ValueError: If `value` is not a valid integer.
    """
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{variable_name} must be an integer") from exc


def parse_float(value: str | None, default: float, variable_name: str) -> float:
    """Parse a floating-point configuration value.

    Args:
        value: Raw string value.
        default: Default value used when `value` is missing.
        variable_name: Configuration variable name for error messages.

    Returns:
        Parsed float value.

    Raises:
        ValueError: If `value` is not a valid float.
    """
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{variable_name} must be a float") from exc
