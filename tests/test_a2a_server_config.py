"""
Author: L. Saetta
Date last modified: 2026-07-07
License: MIT
Description: Unit tests for A2A server runtime configuration helpers.
Agent customization: Update only for server or client configuration changes.
"""

from __future__ import annotations

import pytest

from oci_langgraph_a2a_blueprint.framework.a2a_server_config import (
    DEFAULT_SERVER_URL,
    load_a2a_server_settings,
)


def test_load_a2a_server_settings_defaults() -> None:
    """Verify local server settings defaults."""
    settings = load_a2a_server_settings({})

    assert settings.host == "0.0.0.0"
    assert settings.port == 8080
    assert settings.public_url == DEFAULT_SERVER_URL
    assert settings.log_level == "INFO"


def test_load_a2a_server_settings_overrides() -> None:
    """Verify explicit environment values override defaults."""
    settings = load_a2a_server_settings(
        {
            "A2A_SERVER_HOST": "127.0.0.1",
            "A2A_SERVER_PORT": "8123",
            "A2A_SERVER_PUBLIC_URL": "https://agent.example.com",
            "AGENT_LOG_LEVEL": "debug",
        }
    )

    assert settings.host == "127.0.0.1"
    assert settings.port == 8123
    assert settings.public_url == "https://agent.example.com"
    assert settings.log_level == "DEBUG"


def test_load_a2a_server_settings_excludes_sample_agent_sleep() -> None:
    """Verify sample-agent sleep values are not server settings."""
    settings = load_a2a_server_settings({"AGENT_STEP_SLEEP_SECONDS": "0.25"})

    assert not hasattr(settings, "step_sleep_seconds")


def test_load_a2a_server_settings_derives_public_url_from_host() -> None:
    """Verify public URL derivation for a concrete bind host."""
    settings = load_a2a_server_settings(
        {
            "A2A_SERVER_HOST": "127.0.0.1",
            "A2A_SERVER_PORT": "9000",
        }
    )

    assert settings.public_url == "http://127.0.0.1:9000"


def test_load_a2a_server_settings_rejects_invalid_port() -> None:
    """Verify invalid port values fail with a clear error."""
    with pytest.raises(ValueError, match="A2A_SERVER_PORT must be an integer"):
        load_a2a_server_settings({"A2A_SERVER_PORT": "abc"})
