"""
Author: L. Saetta
Date last modified: 2026-07-08
License: MIT
Description: Command planning helpers for A2A Agent Factory deployment runs.
"""

from __future__ import annotations

from typing import Any

DEFAULT_WAIT_STATE = "SUCCEEDED"
GENERATED_ARTIFACT_DIR = "agent-factory/generated"
COMPARTMENT_OCID_PREFIX = "ocid1.compartment."
REGION_KEYS = {
    "eu-frankfurt-1": "fra",
    "us-chicago-1": "ord",
}


def build_deployment_plan(payload: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    """Build commands and JSON artifacts for an Agent Factory run.

    Args:
        payload: Normalized deployment payload.
        dry_run: Whether to build non-mutating check commands.

    Returns:
        dict[str, Any]: Command plan, image reference, runtime environment, and
        JSON artifacts.
    """

    resolved_identifiers = build_resolved_identifiers(payload)
    runtime_environment = build_agent_runtime_environment(payload, resolved_identifiers)
    redacted_environment = redact_runtime_environment(runtime_environment)
    artifacts = build_hosted_application_artifacts(
        payload,
        redacted_environment,
        resolved_identifiers,
    )
    image_reference = build_image_reference(payload)
    commands = (
        _build_dry_run_commands(
            payload, artifacts, image_reference, resolved_identifiers
        )
        if dry_run
        else _build_apply_commands(
            payload,
            artifacts,
            image_reference,
            resolved_identifiers,
        )
    )
    return {
        "commands": commands,
        "image_reference": image_reference,
        "resolved_identifiers": resolved_identifiers,
        "runtime_environment": runtime_environment,
        "redacted_runtime_environment": redacted_environment,
        "artifacts": artifacts,
    }


def build_dry_run_commands(payload: dict[str, Any]) -> list[list[str]]:
    """Build non-mutating validation commands for an Agent Factory dry run.

    Args:
        payload: Normalized deployment payload.

    Returns:
        list[list[str]]: Structured command arguments.
    """

    return build_deployment_plan(payload, dry_run=True)["commands"]


def build_apply_commands(payload: dict[str, Any]) -> list[list[str]]:
    """Build mutating command plan for a real deployment run.

    Args:
        payload: Normalized deployment payload.

    Returns:
        list[list[str]]: Structured command arguments.
    """

    return build_deployment_plan(payload, dry_run=False)["commands"]


def _build_dry_run_commands(
    payload: dict[str, Any],
    artifacts: dict[str, Any],
    image_reference: str,
    resolved_identifiers: dict[str, str],
) -> list[list[str]]:
    """Build non-mutating validation commands from prepared artifacts."""

    compartment_id = resolved_identifiers["compartment_id"]
    ocir_registry = build_ocir_registry(payload)
    return [
        _build_compartment_resolution_command(payload),
        [
            "docker",
            "build",
            "--platform",
            "linux/amd64",
            "-f",
            "Dockerfile",
            "-t",
            image_reference,
            ".",
        ],
        [
            "oci",
            "--region",
            payload["region"],
            "--output",
            "json",
            "artifacts",
            "container",
            "repository",
            "list",
            "--compartment-id",
            compartment_id,
            "--display-name",
            payload["container_repository_name"],
            "--all",
        ],
        _build_docker_login_command(payload, ocir_registry),
        [
            "docker",
            "manifest",
            "inspect",
            image_reference,
        ],
        [
            "oci",
            "--region",
            payload["region"],
            "--output",
            "json",
            "generative-ai",
            "hosted-application-collection",
            "list-hosted-applications",
            "--compartment-id",
            compartment_id,
            "--all",
        ],
        [
            "oci",
            "--region",
            payload["region"],
            "--output",
            "json",
            "generative-ai",
            "hosted-deployment",
            "create-hosted-deployment-single-docker-artifact",
            "--hosted-application-id",
            "<hosted-application-ocid-from-create-response>",
            "--active-artifact-container-uri",
            artifacts["create-hosted-deployment.json"]["containerUri"],
            "--active-artifact-tag",
            artifacts["create-hosted-deployment.json"]["artifactTag"],
            "--display-name",
            artifacts["create-hosted-deployment.json"]["displayName"],
            "--compartment-id",
            compartment_id,
            "--wait-for-state",
            DEFAULT_WAIT_STATE,
        ],
        [
            "oci",
            "--region",
            payload["region"],
            "--output",
            "json",
            "generative-ai",
            "hosted-deployment",
            "get",
            "--hosted-deployment-id",
            "<hosted-deployment-ocid>",
        ],
        _build_health_check_command(),
    ]


def _build_apply_commands(
    payload: dict[str, Any],
    artifacts: dict[str, Any],
    image_reference: str,
    resolved_identifiers: dict[str, str],
) -> list[list[str]]:
    """Build mutating command plan from prepared artifacts."""

    compartment_id = resolved_identifiers["compartment_id"]
    ocir_registry = build_ocir_registry(payload)
    return [
        _build_compartment_resolution_command(payload),
        [
            "docker",
            "build",
            "--platform",
            "linux/amd64",
            "-t",
            image_reference,
            "-f",
            "Dockerfile",
            ".",
        ],
        [
            "oci",
            "--region",
            payload["region"],
            "--output",
            "json",
            "artifacts",
            "container",
            "repository",
            "create",
            "--display-name",
            payload["container_repository_name"],
            "--compartment-id",
            compartment_id,
        ],
        _build_docker_login_command(payload, ocir_registry),
        [
            "docker",
            "push",
            image_reference,
        ],
        [
            "oci",
            "--region",
            payload["region"],
            "--output",
            "json",
            "generative-ai",
            "hosted-application",
            "create",
            "--display-name",
            artifacts["create-hosted-application.json"]["displayName"],
            "--compartment-id",
            compartment_id,
            "--inbound-auth-config",
            _file_uri("hosted-application-inbound-auth-config.json"),
            "--networking-config",
            _file_uri("hosted-application-networking-config.json"),
            "--environment-variables",
            _file_uri("hosted-application-environment-variables.json"),
            "--wait-for-state",
            DEFAULT_WAIT_STATE,
        ],
        [
            "oci",
            "--region",
            payload["region"],
            "--output",
            "json",
            "generative-ai",
            "hosted-deployment",
            "create-hosted-deployment-single-docker-artifact",
            "--hosted-application-id",
            "<hosted-application-ocid-from-create-response>",
            "--active-artifact-container-uri",
            artifacts["create-hosted-deployment.json"]["containerUri"],
            "--active-artifact-tag",
            artifacts["create-hosted-deployment.json"]["artifactTag"],
            "--display-name",
            artifacts["create-hosted-deployment.json"]["displayName"],
            "--compartment-id",
            compartment_id,
            "--wait-for-state",
            DEFAULT_WAIT_STATE,
        ],
        [
            "oci",
            "--region",
            payload["region"],
            "--output",
            "json",
            "generative-ai",
            "hosted-deployment",
            "get",
            "--hosted-deployment-id",
            "<hosted-deployment-ocid>",
        ],
        _build_health_check_command(),
    ]


def _build_health_check_command() -> list[str]:
    """Build a portable health check command for the hosted A2A server.

    Returns:
        list[str]: Python command that validates the health endpoint without
        requiring curl to be installed in the Agent Factory API container.
    """

    return [
        "python",
        "-c",
        (
            "import sys, urllib.request; "
            "urllib.request.urlopen(sys.argv[1], timeout=30).read()"
        ),
        "<deployed-health-endpoint>/health",
    ]


def build_image_reference(payload: dict[str, Any]) -> str:
    """Build the target OCI Container Registry image reference.

    Args:
        payload: Normalized deployment payload.

    Returns:
        str: Image reference placeholder suitable for display and execution.
    """

    repository = payload["container_repository_name"].strip("/")
    tenancy_namespace = str(
        payload.get("object_storage_namespace") or "<tenancy-namespace>"
    )
    return (
        f"{build_ocir_registry(payload)}"
        f"/{tenancy_namespace}/{repository}:"
        f"{payload['container_image_tag']}"
    )


def build_ocir_registry(payload: dict[str, Any]) -> str:
    """Build the target OCIR registry hostname for a selected OCI region."""

    region = str(payload["region"])
    region_key = REGION_KEYS.get(region)
    if not region_key:
        raise ValueError(f"Unsupported OCI region for OCIR registry: {region}")
    return f"{region_key}.ocir.io"


def build_hosted_application_artifacts(
    payload: dict[str, Any],
    environment: dict[str, str],
    resolved_identifiers: dict[str, str],
) -> dict[str, Any]:
    """Build OCI CLI JSON artifacts using the deployer-compatible shape."""

    image_reference = build_image_reference(payload)
    compartment_id = resolved_identifiers["compartment_id"]
    container_uri, tag = image_reference.rsplit(":", maxsplit=1)
    return {
        "hosted-application-inbound-auth-config.json": (
            _build_inbound_auth_config(payload)
        ),
        "hosted-application-networking-config.json": {
            "inboundNetworkingConfig": {
                "endpointMode": "PUBLIC",
            },
            "outboundNetworkingConfig": {
                "networkMode": "MANAGED",
            },
        },
        "hosted-application-environment-variables.json": [
            {"name": name, "type": "PLAINTEXT", "value": value}
            for name, value in environment.items()
        ],
        "hosted-deployment-active-artifact.json": {
            "artifactType": "SIMPLE_DOCKER_ARTIFACT",
            "containerUri": container_uri,
            "tag": tag,
        },
        "create-hosted-application.json": {
            "compartmentId": compartment_id,
            "createIfMissing": True,
            "displayName": payload["hosted_application_name"],
            "jsonFiles": {
                "inboundAuthConfig": _artifact_path(
                    "hosted-application-inbound-auth-config.json"
                ),
                "networkingConfig": _artifact_path(
                    "hosted-application-networking-config.json"
                ),
                "environmentVariables": _artifact_path(
                    "hosted-application-environment-variables.json"
                ),
            },
            "updateIfExists": False,
        },
        "create-hosted-deployment.json": {
            "activate": True,
            "activeArtifact": _artifact_path("hosted-deployment-active-artifact.json"),
            "artifactTag": tag,
            "compartmentId": compartment_id,
            "containerUri": container_uri,
            "createNewVersion": True,
            "displayName": payload["deployment_name"],
            "imageUri": image_reference,
        },
    }


def build_agent_runtime_environment(
    payload: dict[str, Any],
    resolved_identifiers: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build environment variables required by the deployed A2A server."""

    del resolved_identifiers
    environment = {
        "A2A_SERVER_HOST": "0.0.0.0",
        "A2A_SERVER_PORT": "8080",
        "A2A_SERVER_PUBLIC_URL": "<hosted-application-invoke-url>",
        "AGENT_LOG_LEVEL": str(payload["agent_log_level"]).upper(),
        "AGENT_STEP_SLEEP_SECONDS": str(payload["agent_step_sleep_seconds"]),
        "AGENT_LLM_MODEL_ID": str(payload["model_id"]),
        "AGENT_LLM_API_KEY": str(payload["agent_llm_api_key"]),
        "AGENT_LLM_OCI_REGION": str(payload["region"]),
    }
    if payload.get("agent_llm_base_url"):
        environment["AGENT_LLM_BASE_URL"] = str(payload["agent_llm_base_url"])
    return environment


def redact_runtime_environment(environment: dict[str, str]) -> dict[str, str]:
    """Redact secret values from runtime environment output."""

    redacted = dict(environment)
    if redacted.get("AGENT_LLM_API_KEY"):
        redacted["AGENT_LLM_API_KEY"] = "********"
    return redacted


def build_resolved_identifiers(payload: dict[str, Any]) -> dict[str, str]:
    """Build resolved resource identifiers for command planning."""

    return {
        "compartment_id": _resolved_compartment_id(payload),
        "object_storage_namespace": _resolved_object_storage_namespace(payload),
    }


def _build_inbound_auth_config(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the Hosted Application inbound authentication configuration."""

    if not payload.get("jwt_protection_enabled"):
        return {"inboundAuthConfigType": "NO_AUTH_CONFIG"}

    return {
        "inboundAuthConfigType": "IDCS_AUTH_CONFIG",
        "idcsConfig": {
            "domainUrl": str(payload["identity_domain_url"]).rstrip("/"),
            "scope": str(payload["auth_scope"]),
            "audience": str(payload["auth_audience"]),
        },
    }


def _resolved_compartment_id(payload: dict[str, Any]) -> str:
    """Return the compartment OCID or the placeholder produced by resolution."""

    compartment = str(payload["compartment"])
    if compartment.startswith(COMPARTMENT_OCID_PREFIX):
        return compartment
    return "<resolved-compartment-ocid>"


def _resolved_object_storage_namespace(payload: dict[str, Any]) -> str:
    """Return the Object Storage namespace or the placeholder from resolution."""

    return str(payload.get("object_storage_namespace") or "<resolved-namespace>")


def _build_compartment_resolution_command(payload: dict[str, Any]) -> list[str]:
    """Build the command that resolves a compartment name or validates an OCID."""

    compartment = str(payload["compartment"])
    command = [
        "oci",
        "--region",
        payload["region"],
        "--output",
        "json",
        "iam",
        "compartment",
    ]
    if compartment.startswith(COMPARTMENT_OCID_PREFIX):
        return [
            *command,
            "get",
            "--compartment-id",
            compartment,
        ]
    return [
        *command,
        "list",
        "--name",
        compartment,
        "--compartment-id-in-subtree",
        "true",
        "--access-level",
        "ANY",
        "--include-root",
        "--all",
    ]


def _build_docker_login_command(
    payload: dict[str, Any], ocir_registry: str
) -> list[str]:
    """Build the Docker login command for OCI Container Registry."""

    return [
        "docker",
        "login",
        ocir_registry,
        "--username",
        str(payload["ocir_username"]),
        "--password",
        "********",
    ]


def _artifact_path(filename: str) -> str:
    """Return the relative path used by generated dry-run artifacts."""

    return f"{GENERATED_ARTIFACT_DIR}/{filename}"


def _file_uri(filename: str) -> str:
    """Return an OCI CLI file URI for a generated dry-run artifact."""

    return f"file://{_artifact_path(filename)}"
