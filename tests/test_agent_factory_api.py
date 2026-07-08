"""
Author: L. Saetta
Date last modified: 2026-07-08
License: MIT
Description: Unit tests for A2A Agent Factory deployment planning.
"""

from __future__ import annotations

import sys
from pathlib import Path

# pylint: disable=wrong-import-position

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
AGENT_FACTORY_API = REPOSITORY_ROOT / "agent-factory" / "api"
sys.path.insert(0, str(AGENT_FACTORY_API))

from agent_factory_api.app import (  # noqa: E402
    _build_hosted_application_urls,
    _create_run,
)
from agent_factory_api.commands import (  # noqa: E402
    build_deployment_plan,
    build_hosted_application_artifacts,
    build_resolved_identifiers,
)
from agent_factory_api.models import (  # noqa: E402
    redact_payload,
    validate_deployment_payload,
)
from agent_factory_api.ready_script import build_ready_to_run_script  # noqa: E402


def test_validate_deployment_payload_accepts_a2a_minimum() -> None:
    """Verify the factory accepts the required A2A deployment fields."""
    validation = validate_deployment_payload(_valid_payload())

    assert not validation.errors
    assert validation.payload is not None
    assert validation.payload["agent_llm_api_key"] == "secret-key"
    assert validation.payload["agent_step_sleep_seconds"] == 0


def test_validate_deployment_payload_rejects_latest_tag() -> None:
    """Verify floating image tags are rejected."""
    payload = {**_valid_payload(), "container_image_tag": "latest"}

    validation = validate_deployment_payload(payload)

    assert validation.errors["container_image_tag"] == "Use a non-floating image tag."


def test_redact_payload_hides_secrets() -> None:
    """Verify status payloads do not expose secrets."""
    redacted = redact_payload(_valid_payload())

    assert redacted["agent_llm_api_key"] == "********"
    assert redacted["ocir_password"] == "********"


def test_deployment_plan_uses_a2a_runtime_environment() -> None:
    """Verify command planning targets the root A2A server image."""
    plan = build_deployment_plan(_valid_payload(), dry_run=True)

    assert plan["runtime_environment"]["A2A_SERVER_HOST"] == "0.0.0.0"
    assert plan["runtime_environment"]["A2A_SERVER_PORT"] == "8080"
    assert plan["runtime_environment"]["AGENT_LLM_MODEL_ID"] == "openai.gpt-5.5"
    assert plan["redacted_runtime_environment"]["AGENT_LLM_API_KEY"] == "********"
    assert any(command[:2] == ["docker", "build"] for command in plan["commands"])
    assert "OCI_VECTOR_STORE_ID" not in plan["runtime_environment"]


def test_dry_run_resolves_namespace_for_displayed_docker_commands(monkeypatch) -> None:
    """Verify dry-run command display uses the real OCI tenancy namespace."""
    monkeypatch.setattr(
        "agent_factory_api.app.resolve_object_storage_namespace",
        lambda *, region: "mytenancy",
    )

    deployment_run = _create_run(_valid_payload())
    docker_build_command = next(
        command
        for command in deployment_run.commands
        if command[:2] == ["docker", "build"]
    )

    assert "ord.ocir.io/mytenancy/oci-langgraph-a2a-blueprint-agent:2026-07-08" in (
        docker_build_command
    )
    assert "<tenancy-namespace>" not in " ".join(docker_build_command)


def test_hosted_application_artifacts_support_optional_idcs_auth() -> None:
    """Verify JWT protection maps to OCI Hosted Application IDCS auth config."""
    payload = {
        **_valid_payload(),
        "jwt_protection_enabled": True,
        "identity_domain_compartment": "Security",
        "identity_domain_url": "https://idcs.example.com",
        "auth_scope": "invoke",
        "auth_audience": "a2a-agent",
    }
    artifacts = build_hosted_application_artifacts(
        payload,
        {"AGENT_LLM_API_KEY": "********"},
        build_resolved_identifiers(payload),
    )

    auth_config = artifacts["hosted-application-inbound-auth-config.json"]
    assert auth_config["inboundAuthConfigType"] == "IDCS_AUTH_CONFIG"
    assert auth_config["idcsConfig"]["domainUrl"] == "https://idcs.example.com"
    assert auth_config["idcsConfig"]["scope"] == "invoke"
    assert auth_config["idcsConfig"]["audience"] == "a2a-agent"


def test_hosted_application_urls_are_a2a_specific() -> None:
    """Verify live outputs expose A2A endpoint URLs."""
    urls = _build_hosted_application_urls("https://example.test/invoke/")

    assert urls["hosted_application_invoke_url"] == "https://example.test/invoke"
    assert (
        urls["hosted_application_agent_card_url"]
        == "https://example.test/invoke/.well-known/agent-card.json"
    )
    assert (
        urls["hosted_application_message_stream_url"]
        == "https://example.test/invoke/message:stream"
    )


def test_ready_script_does_not_embed_plaintext_secrets() -> None:
    """Verify exported scripts prompt for secrets instead of embedding them."""
    script = build_ready_to_run_script(_valid_payload())

    assert "secret-key" not in script
    assert "ocir-secret" not in script
    assert "AGENT_LLM_API_KEY" in script
    assert "docker build --platform linux/amd64" in script
    assert "create-hosted-deployment-single-docker-artifact" in script


def _valid_payload() -> dict[str, object]:
    """Build a valid A2A Agent Factory payload."""

    return {
        "compartment": "ocid1.compartment.oc1..example",
        "region": "us-chicago-1",
        "hosted_application_name": "a2a-agent",
        "deployment_name": "a2a-agent-v1",
        "model_id": "openai.gpt-5.5",
        "agent_llm_api_key": "secret-key",
        "agent_llm_base_url": "",
        "agent_log_level": "INFO",
        "agent_step_sleep_seconds": 0,
        "container_repository_name": "oci-langgraph-a2a-blueprint-agent",
        "container_image_tag": "2026-07-08",
        "ocir_username": "tenant/user",
        "ocir_password": "ocir-secret",
        "endpoint_visibility": "public",
        "network_mode": "oracle_managed",
        "jwt_protection_enabled": False,
        "dry_run": True,
    }
