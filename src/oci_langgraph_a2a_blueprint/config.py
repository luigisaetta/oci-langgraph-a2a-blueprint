"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: Runtime configuration helpers for local server and client commands.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_A2A_SERVER_HOST = "0.0.0.0"
DEFAULT_A2A_SERVER_PORT = 8000
DEFAULT_A2A_CLIENT_SERVER_URL = "http://localhost:8000"
DEFAULT_AGENT_LOG_LEVEL = "INFO"


@dataclass(frozen=True)
class A2AServerSettings:
    """Runtime settings for the local A2A server.

    Attributes:
        host: Bind host for uvicorn.
        port: Bind port for uvicorn.
        public_url: URL advertised by the Agent Card.
        log_level: Python logging level name.
    """

    host: str
    port: int
    public_url: str
    log_level: str


def load_a2a_server_settings(
    environ: Mapping[str, str] | None = None,
) -> A2AServerSettings:
    """Load local A2A server settings from environment variables.

    Args:
        environ: Optional environment mapping. Defaults to `os.environ`.

    Returns:
        Parsed A2A server settings.

    Raises:
        ValueError: If numeric settings are invalid.
    """
    source = environ or os.environ
    host = source.get("A2A_SERVER_HOST", DEFAULT_A2A_SERVER_HOST)
    port = _parse_int(
        source.get("A2A_SERVER_PORT"),
        default=DEFAULT_A2A_SERVER_PORT,
        variable_name="A2A_SERVER_PORT",
    )
    public_url = source.get("A2A_SERVER_PUBLIC_URL", _default_public_url(host, port))
    log_level = source.get("AGENT_LOG_LEVEL", DEFAULT_AGENT_LOG_LEVEL).upper()

    return A2AServerSettings(
        host=host,
        port=port,
        public_url=public_url,
        log_level=log_level,
    )


def _parse_int(value: str | None, default: int, variable_name: str) -> int:
    """Parse an integer environment variable.

    Args:
        value: Raw value from the environment.
        default: Default value used when `value` is missing.
        variable_name: Environment variable name for error messages.

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


def _default_public_url(host: str, port: int) -> str:
    """Derive a local public URL from host and port settings.

    Args:
        host: Bind host.
        port: Bind port.

    Returns:
        Local URL suitable for development Agent Cards.
    """
    advertised_host = "localhost" if host in {"0.0.0.0", "::"} else host
    return f"http://{advertised_host}:{port}"
