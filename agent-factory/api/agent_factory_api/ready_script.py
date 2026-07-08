"""
Author: L. Saetta
Date last modified: 2026-07-08
License: MIT
Description: Ready-to-run deployment script generation for A2A Agent Factory.
"""

# pylint: disable=duplicate-code

from __future__ import annotations

import json
from typing import Any

from agent_factory_api.commands import (
    build_hosted_application_artifacts,
    build_ocir_registry,
    build_resolved_identifiers,
    redact_runtime_environment,
)

AGENT_LLM_API_KEY_MARKER = "__AGENT_FACTORY_AGENT_LLM_API_KEY__"
OCIR_PASSWORD_MARKER = "__AGENT_FACTORY_OCIR_PASSWORD__"


def build_ready_to_run_script(payload: dict[str, Any]) -> str:
    """Build a Linux-first Bash script for live A2A Hosted Deployment.

    Args:
        payload: Validated Agent Factory deployment payload.

    Returns:
        str: Bash script that runs the deployment workflow.
    """

    script_payload = _script_payload(payload)
    artifacts = build_hosted_application_artifacts(
        script_payload,
        redact_runtime_environment(_runtime_environment_for_script(script_payload)),
        build_resolved_identifiers(script_payload),
    )
    ocir_registry = build_ocir_registry(script_payload)
    payload_json = json.dumps(script_payload, indent=2, sort_keys=True)

    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "",
            "# A2A Agent Factory ready-to-run deployment script.",
            "# This script creates OCI resources when executed.",
            "",
            'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
            'if [ -n "${AGENT_FACTORY_REPO_ROOT:-}" ]; then',
            '  REPO_ROOT="${AGENT_FACTORY_REPO_ROOT}"',
            'elif [ -f "${PWD}/Dockerfile" ] && [ -d "${PWD}/agent-factory" ]; then',
            '  REPO_ROOT="${PWD}"',
            "else",
            '  REPO_ROOT="${SCRIPT_DIR}"',
            "fi",
            "",
            'if [ -z "${AGENT_LLM_API_KEY:-}" ]; then',
            '  printf "AGENT_LLM_API_KEY: " >&2',
            "  read -r -s AGENT_LLM_API_KEY",
            '  printf "\\n" >&2',
            "fi",
            "",
            'if [ -z "${OCIR_PASSWORD:-}" ]; then',
            '  printf "OCIR_PASSWORD: " >&2',
            "  read -r -s OCIR_PASSWORD",
            '  printf "\\n" >&2',
            "fi",
            "",
            'WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/a2a-agent-factory.XXXXXX")"',
            'cleanup() { rm -rf "${WORK_DIR}"; }',
            "trap cleanup EXIT",
            'ARTIFACT_DIR="${WORK_DIR}/artifacts"',
            'mkdir -p "${ARTIFACT_DIR}"',
            "",
            'PAYLOAD_FILE="${WORK_DIR}/payload.json"',
            "cat > \"${PAYLOAD_FILE}\" <<'JSON'",
            payload_json,
            "JSON",
            "",
            'REGION="' + str(script_payload["region"]) + '"',
            'COMPARTMENT_ID="' + str(script_payload["compartment"]) + '"',
            f'OCIR_REGISTRY="{ocir_registry}"',
            'OCIR_USERNAME="' + str(script_payload["ocir_username"]) + '"',
            'IMAGE_REFERENCE="' + _image_reference(script_payload) + '"',
            'CONTAINER_REPOSITORY_NAME="'
            + str(script_payload["container_repository_name"])
            + '"',
            'HOSTED_APPLICATION_NAME="'
            + str(script_payload["hosted_application_name"])
            + '"',
            'DEPLOYMENT_NAME="' + str(script_payload["deployment_name"]) + '"',
            "",
            'INBOUND_AUTH_CONFIG="${ARTIFACT_DIR}/hosted-application-inbound-auth-config.json"',
            'NETWORKING_CONFIG="${ARTIFACT_DIR}/hosted-application-networking-config.json"',
            'ENVIRONMENT_VARIABLES="${ARTIFACT_DIR}/hosted-application-environment-variables.json"',
            "",
            "json_string() {",
            "  python3 -c 'import json, sys; print(json.dumps(sys.argv[1]))' \"$1\"",
            "}",
            "",
            "extract_first_ocid() {",
            '  python3 - "$1" "$2" <<\'PY\'',
            "import json, sys",
            "prefix = sys.argv[2]",
            "with open(sys.argv[1], encoding='utf-8') as handle:",
            "    data = json.load(handle)",
            "def walk(value):",
            "    if isinstance(value, dict):",
            "        for item in value.values():",
            "            yield from walk(item)",
            "    elif isinstance(value, list):",
            "        for item in value:",
            "            yield from walk(item)",
            "    else:",
            "        yield value",
            "for value in walk(data):",
            "    if isinstance(value, str) and value.startswith(prefix):",
            "        print(value)",
            "        raise SystemExit(0)",
            "raise SystemExit(1)",
            "PY",
            "}",
            "",
            "# Resolve tenancy namespace for OCIR image reference.",
            'NAMESPACE="$(oci --region "${REGION}" --output json os ns get | \\',
            '  python3 -c \'import json, sys; print(json.load(sys.stdin)["data"])\')"',
            'IMAGE_REFERENCE="${OCIR_REGISTRY}/${NAMESPACE}/${CONTAINER_REPOSITORY_NAME}:'
            + str(script_payload["container_image_tag"])
            + '"',
            "",
            "# JSON artifact: Hosted Application inbound authentication config.",
            "cat > \"${INBOUND_AUTH_CONFIG}\" <<'JSON'",
            json.dumps(
                artifacts["hosted-application-inbound-auth-config.json"], indent=2
            ),
            "JSON",
            "",
            "# JSON artifact: Hosted Application networking config.",
            "cat > \"${NETWORKING_CONFIG}\" <<'JSON'",
            json.dumps(
                artifacts["hosted-application-networking-config.json"], indent=2
            ),
            "JSON",
            "",
            "# JSON artifact: Hosted Application runtime environment variables.",
            'cat > "${ENVIRONMENT_VARIABLES}" <<JSON',
            "[",
            '  {"name": "A2A_SERVER_HOST", "type": "PLAINTEXT", "value": "0.0.0.0"},',
            '  {"name": "A2A_SERVER_PORT", "type": "PLAINTEXT", "value": "8080"},',
            '  {"name": "A2A_SERVER_PUBLIC_URL", "type": "PLAINTEXT", "value": ""},',
            '  {"name": "AGENT_LOG_LEVEL", "type": "PLAINTEXT", "value": '
            '$(json_string "' + str(script_payload["agent_log_level"]).upper() + '")},',
            '  {"name": "AGENT_STEP_SLEEP_SECONDS", "type": "PLAINTEXT", "value": '
            '$(json_string "'
            + str(script_payload["agent_step_sleep_seconds"])
            + '")},',
            '  {"name": "AGENT_LLM_MODEL_ID", "type": "PLAINTEXT", "value": '
            '$(json_string "' + str(script_payload["model_id"]) + '")},',
            '  {"name": "AGENT_LLM_API_KEY", "type": "PLAINTEXT", "value": '
            '$(json_string "${AGENT_LLM_API_KEY}")},',
            '  {"name": "AGENT_LLM_OCI_REGION", "type": "PLAINTEXT", "value": '
            '$(json_string "${REGION}")}',
            "]",
            "JSON",
            "",
            'cd "${REPO_ROOT}"',
            'docker build --platform linux/amd64 -t "${IMAGE_REFERENCE}" -f Dockerfile .',
            "",
            'oci --region "${REGION}" --output json artifacts container repository create \\',
            '  --display-name "${CONTAINER_REPOSITORY_NAME}" \\',
            '  --compartment-id "${COMPARTMENT_ID}" || true',
            "",
            'printf "%s\\n" "${OCIR_PASSWORD}" | docker login "${OCIR_REGISTRY}" \\',
            '  --username "${OCIR_USERNAME}" --password-stdin',
            'docker push "${IMAGE_REFERENCE}"',
            "",
            'HOSTED_APPLICATION_OUTPUT="${WORK_DIR}/hosted-application.json"',
            'oci --region "${REGION}" --output json generative-ai hosted-application create \\',
            '  --display-name "${HOSTED_APPLICATION_NAME}" \\',
            '  --compartment-id "${COMPARTMENT_ID}" \\',
            '  --inbound-auth-config "file://${INBOUND_AUTH_CONFIG}" \\',
            '  --networking-config "file://${NETWORKING_CONFIG}" \\',
            '  --environment-variables "file://${ENVIRONMENT_VARIABLES}" \\',
            '  --wait-for-state SUCCEEDED | tee "${HOSTED_APPLICATION_OUTPUT}"',
            'HOSTED_APPLICATION_ID="$(extract_first_ocid \\',
            '  "${HOSTED_APPLICATION_OUTPUT}" \\',
            '  "ocid1.generativeaihostedapplication.")"',
            "",
            'CONTAINER_URI="${IMAGE_REFERENCE%:*}"',
            'IMAGE_TAG="${IMAGE_REFERENCE##*:}"',
            'HOSTED_DEPLOYMENT_OUTPUT="${WORK_DIR}/hosted-deployment.json"',
            'oci --region "${REGION}" --output json generative-ai hosted-deployment \\',
            "  create-hosted-deployment-single-docker-artifact \\",
            '  --hosted-application-id "${HOSTED_APPLICATION_ID}" \\',
            '  --active-artifact-container-uri "${CONTAINER_URI}" \\',
            '  --active-artifact-tag "${IMAGE_TAG}" \\',
            '  --display-name "${DEPLOYMENT_NAME}" \\',
            '  --compartment-id "${COMPARTMENT_ID}" \\',
            '  --wait-for-state SUCCEEDED | tee "${HOSTED_DEPLOYMENT_OUTPUT}"',
            "",
            'echo "Hosted Application ID: ${HOSTED_APPLICATION_ID}"',
            'echo "Image: ${IMAGE_REFERENCE}"',
            "",
        ]
    )


def _script_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a non-secret payload for embedding in the script."""

    script_payload = dict(payload)
    script_payload["dry_run"] = False
    script_payload["agent_llm_api_key"] = AGENT_LLM_API_KEY_MARKER
    script_payload["ocir_password"] = OCIR_PASSWORD_MARKER
    return script_payload


def _runtime_environment_for_script(payload: dict[str, Any]) -> dict[str, str]:
    """Build a redaction-ready A2A runtime environment for script artifacts."""

    environment = {
        "A2A_SERVER_HOST": "0.0.0.0",
        "A2A_SERVER_PORT": "8080",
        "A2A_SERVER_PUBLIC_URL": "",
        "AGENT_LOG_LEVEL": str(payload["agent_log_level"]).upper(),
        "AGENT_STEP_SLEEP_SECONDS": str(payload["agent_step_sleep_seconds"]),
        "AGENT_LLM_MODEL_ID": str(payload["model_id"]),
        "AGENT_LLM_API_KEY": str(payload["agent_llm_api_key"]),
        "AGENT_LLM_OCI_REGION": str(payload["region"]),
    }
    if payload.get("agent_llm_base_url"):
        environment["AGENT_LLM_BASE_URL"] = str(payload["agent_llm_base_url"])
    return environment


def _image_reference(payload: dict[str, Any]) -> str:
    """Build the image reference embedded before runtime namespace resolution."""

    repository = str(payload["container_repository_name"]).strip("/")
    namespace = str(payload.get("object_storage_namespace") or "<resolved-namespace>")
    return (
        f"{build_ocir_registry(payload)}/{namespace}/{repository}:"
        f"{payload['container_image_tag']}"
    )
