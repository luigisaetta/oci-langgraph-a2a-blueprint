"""
Author: L. Saetta
Date last modified: 2026-07-07
License: MIT
Description: Runtime configuration helpers for the local A2A server.
Agent customization: Do not add agent-specific settings here.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from oci_langgraph_a2a_blueprint.parse_utils import parse_int

DEFAULT_A2A_SERVER_HOST = "0.0.0.0"
DEFAULT_A2A_SERVER_PORT = 8080
DEFAULT_SERVER_URL = "http://localhost:8080"
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
    port = parse_int(
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
