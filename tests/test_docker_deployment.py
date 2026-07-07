"""
Author: L. Saetta
Date last modified: 2026-07-07
License: MIT
Description: Unit tests for Docker Compose deployment support files.
"""

from __future__ import annotations

import os
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_runs_a2a_server_entry_point() -> None:
    """Verify the Docker image installs and runs the A2A server command."""
    dockerfile = (REPOSITORY_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.11-slim" in dockerfile
    assert "pip install --no-cache-dir ." in dockerfile
    assert 'CMD ["a2a-langgraph-server"]' in dockerfile


def test_docker_compose_defines_single_a2a_server_service() -> None:
    """Verify Compose defines one service with the expected server settings."""
    compose = (REPOSITORY_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "a2a-server:" in compose
    assert '"${A2A_SERVER_PORT:-8080}:8080"' in compose
    assert 'A2A_SERVER_HOST: "0.0.0.0"' in compose
    assert 'A2A_SERVER_PORT: "8080"' in compose
    assert (
        'A2A_SERVER_PUBLIC_URL: "${A2A_SERVER_PUBLIC_URL:-http://localhost:8080}"'
        in compose
    )
    assert 'AGENT_STEP_SLEEP_SECONDS: "${AGENT_STEP_SLEEP_SECONDS:-0}"' in compose
    assert 'AGENT_LLM_MODEL_ID: "${AGENT_LLM_MODEL_ID:-openai.gpt5.5}"' in compose
    assert 'AGENT_LLM_API_KEY: "${AGENT_LLM_API_KEY:-}"' in compose
    assert 'AGENT_LLM_OCI_REGION: "${AGENT_LLM_OCI_REGION:-us-chicago-1}"' in compose


def test_root_server_scripts_are_executable() -> None:
    """Verify root start and stop scripts are executable and use Docker Compose."""
    start_script = REPOSITORY_ROOT / "start_server.sh"
    stop_script = REPOSITORY_ROOT / "stop_server.sh"

    assert os.access(start_script, os.X_OK)
    assert os.access(stop_script, os.X_OK)
    start_script_text = start_script.read_text(encoding="utf-8")
    assert "--sleep-seconds|-s" in start_script_text
    assert "export AGENT_STEP_SLEEP_SECONDS=$SLEEP_SECONDS" in start_script_text
    assert "docker compose up --build -d a2a-server" in start_script_text
    assert "docker compose down" in stop_script.read_text(encoding="utf-8")


def test_runtime_dependencies_are_declared_for_container_build() -> None:
    """Verify package metadata includes dependencies needed by the image."""
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert (
        'a2a-langgraph-server = "oci_langgraph_a2a_blueprint.framework.a2a_server:main"'
        in pyproject
    )
    for dependency in [
        '"a2a-sdk[http-server]"',
        '"langchain-core"',
        '"langgraph"',
        '"openai"',
        '"starlette"',
        '"uvicorn"',
    ]:
        assert dependency in pyproject
