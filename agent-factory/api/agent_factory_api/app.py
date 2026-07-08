"""
Author: L. Saetta
Date last modified: 2026-07-08
License: MIT
Description: FastAPI backend for A2A Agent Factory deployment orchestration.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from agent_factory_api.commands import (
    build_deployment_plan,
    build_ocir_registry,
    redact_runtime_environment,
)
from agent_factory_api.executor import (
    CommandExecutionError,
    execute_live_deployment_commands,
)
from agent_factory_api.idcs import (
    IdcsTokenValidationError,
    IdcsTokenValidationInput,
    validate_idcs_token,
)
from agent_factory_api.models import (
    DeploymentRun,
    FactoryStep,
    SUPPORTED_REGIONS,
    format_commands,
    redact_payload,
    utc_now,
    validate_deployment_payload,
)
from agent_factory_api.ready_script import build_ready_to_run_script
from agent_factory_api.resources import ResourceProvisioningError, validate_ocir_login

RUNS: dict[str, DeploymentRun] = {}
HOSTED_APPLICATION_API_VERSION = "20251112"

app = FastAPI(title="A2A Agent Factory API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/factory/health")
def health() -> dict[str, str]:
    """Return Agent Factory backend health.

    Returns:
        dict[str, str]: Health response.
    """

    return {"status": "ok"}


@app.post("/factory/ocir-login/check")
async def check_ocir_login(request: Request) -> JSONResponse:
    """Validate submitted OCIR Docker credentials without creating resources."""

    payload = await _read_json_object(request)
    if isinstance(payload, JSONResponse):
        return payload

    validation_errors = _validate_ocir_login_check_payload(payload)
    if validation_errors:
        return JSONResponse(
            {
                "error": "OCIR credential validation input failed.",
                "field_errors": validation_errors,
            },
            status_code=400,
        )

    normalized_payload = {
        "region": str(payload["region"]).strip(),
        "ocir_username": str(payload["ocir_username"]).strip(),
        "ocir_password": str(payload["ocir_password"]).strip(),
    }
    try:
        result = validate_ocir_login(
            registry=build_ocir_registry(normalized_payload),
            username=normalized_payload["ocir_username"],
            password=normalized_payload["ocir_password"],
        )
    except ResourceProvisioningError as exc:
        return JSONResponse(
            {"status": "failed", "error": str(exc), "field_errors": {}},
            status_code=400,
        )

    return JSONResponse(
        {
            "status": "succeeded",
            "message": "OCIR Docker login succeeded.",
            "ocir_registry": result["ocir_registry"],
            "ocir_username": result["ocir_username"],
        }
    )


@app.post("/factory/idcs-token/check")
async def check_idcs_token(request: Request) -> JSONResponse:
    """Validate IDCS confidential application token settings."""

    payload = await _read_json_object(request)
    if isinstance(payload, JSONResponse):
        return payload

    validation_errors = _validate_idcs_token_check_payload(payload)
    if validation_errors:
        return JSONResponse(
            {
                "error": "IDCS token validation input failed.",
                "field_errors": validation_errors,
            },
            status_code=400,
        )

    token_input = IdcsTokenValidationInput(
        identity_domain_url=str(payload["identity_domain_url"]).strip(),
        confidential_application_id=str(payload["confidential_application_id"]).strip(),
        confidential_application_secret=str(
            payload["confidential_application_secret"]
        ).strip(),
        audience_claim=str(payload["auth_audience"]).strip(),
        scope_claim=str(payload["auth_scope"]).strip(),
    )
    try:
        result = validate_idcs_token(token_input)
    except IdcsTokenValidationError as exc:
        return JSONResponse(
            {"status": "failed", "error": str(exc), "field_errors": {}},
            status_code=400,
        )

    return JSONResponse(result)


@app.post("/factory/deployments")
async def create_deployment(
    request: Request, background_tasks: BackgroundTasks
) -> JSONResponse:
    """Create an Agent Factory deployment run."""

    payload = await _read_json_object(request)
    if isinstance(payload, JSONResponse):
        return payload

    validation = validate_deployment_payload(payload)
    if validation.errors:
        return JSONResponse(
            {
                "error": "Deployment input validation failed.",
                "field_errors": validation.errors,
            },
            status_code=400,
        )

    assert validation.payload is not None
    if bool(validation.payload["dry_run"]):
        deployment_run = _create_run(validation.payload)
    else:
        deployment_run = _create_live_run(validation.payload)
        background_tasks.add_task(
            _execute_live_run,
            deployment_run.deployment_run_id,
            validation.payload,
        )
    RUNS[deployment_run.deployment_run_id] = deployment_run
    return JSONResponse(deployment_run.to_dict(), status_code=201)


@app.get("/factory/deployments/{deployment_run_id}")
def get_deployment(deployment_run_id: str) -> dict[str, Any]:
    """Return an Agent Factory deployment run by ID."""

    deployment_run = RUNS.get(deployment_run_id)
    if deployment_run is None:
        raise HTTPException(status_code=404, detail="Deployment run not found.")

    return deployment_run.to_dict()


@app.get("/factory/deployments/{deployment_run_id}/commands")
def get_deployment_commands(deployment_run_id: str) -> PlainTextResponse:
    """Return deployment commands as a downloadable shell script."""

    deployment_run = RUNS.get(deployment_run_id)
    if deployment_run is None:
        raise HTTPException(status_code=404, detail="Deployment run not found.")

    return PlainTextResponse(
        format_commands(deployment_run.commands),
        media_type="text/x-shellscript",
        headers={
            "Content-Disposition": (
                f'attachment; filename="agent-factory-{deployment_run_id}.sh"'
            )
        },
    )


@app.post("/factory/deployment-script", response_model=None)
async def create_ready_deployment_script(
    request: Request,
) -> PlainTextResponse | JSONResponse:
    """Return a ready-to-run live deployment shell script."""

    payload = await _read_json_object(request)
    if isinstance(payload, JSONResponse):
        return payload

    validation = validate_deployment_payload(payload)
    if validation.errors:
        return JSONResponse(
            {
                "error": "Deployment script input validation failed.",
                "field_errors": validation.errors,
            },
            status_code=400,
        )

    assert validation.payload is not None
    script_text = build_ready_to_run_script(validation.payload)
    return PlainTextResponse(
        script_text,
        media_type="text/x-shellscript",
        headers={
            "Content-Disposition": (
                'attachment; filename="agent-factory-ready-deploy.sh"'
            )
        },
    )


async def _read_json_object(request: Request) -> dict[str, Any] | JSONResponse:
    """Read a JSON object request or return a standard error response."""

    try:
        payload = await request.json()
    except ValueError:
        return JSONResponse(
            {"error": "Invalid JSON payload.", "field_errors": {}},
            status_code=400,
        )

    if not isinstance(payload, dict):
        return JSONResponse(
            {"error": "Payload must be a JSON object.", "field_errors": {}},
            status_code=400,
        )
    return payload


def _validate_idcs_token_check_payload(payload: dict[str, Any]) -> dict[str, str]:
    """Validate the minimal payload required for IDCS token checks."""

    errors: dict[str, str] = {}
    required_fields = (
        "identity_domain_url",
        "auth_scope",
        "auth_audience",
        "confidential_application_id",
        "confidential_application_secret",
    )
    for field_name in required_fields:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            errors[field_name] = "This field is required."

    domain_url = str(payload.get("identity_domain_url", "")).strip()
    if domain_url and not domain_url.startswith("https://"):
        errors["identity_domain_url"] = (
            "Identity Domain URL must be the exact https:// URL from OCI Console."
        )

    return errors


def _validate_ocir_login_check_payload(payload: dict[str, Any]) -> dict[str, str]:
    """Validate the minimal payload required for OCIR login checks."""

    errors: dict[str, str] = {}
    for field_name in ("region", "ocir_username", "ocir_password"):
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            errors[field_name] = "This field is required."

    region = str(payload.get("region", "")).strip()
    if region and region not in SUPPORTED_REGIONS:
        accepted = ", ".join(sorted(SUPPORTED_REGIONS))
        errors["region"] = f"Expected one of: {accepted}."

    return errors


def _create_run(payload: dict[str, Any]) -> DeploymentRun:
    """Create an in-memory dry-run deployment result."""

    dry_run = bool(payload["dry_run"])
    now = utc_now()
    plan = build_deployment_plan(payload, dry_run)
    commands = plan["commands"]
    steps = _build_steps(commands)
    status = "succeeded"

    for step in steps:
        if step.status != "skipped":
            step.status = "succeeded"
        step.started_at = now
        step.ended_at = now

    return DeploymentRun(
        deployment_run_id=str(uuid4()),
        dry_run=dry_run,
        status=status,
        submitted_at=now,
        completed_at=now,
        request=redact_payload(payload),
        steps=steps,
        commands=commands,
        outputs=_build_run_outputs(
            plan_payload=payload,
            plan=plan,
            dry_run=dry_run,
        ),
    )


def _create_live_run(payload: dict[str, Any]) -> DeploymentRun:
    """Create an in-memory live deployment run before execution starts."""

    now = utc_now()
    plan = build_deployment_plan(payload, dry_run=False)
    steps = _build_steps(plan["commands"])
    _set_step_status(steps, "validate-input", "succeeded", timestamp=now)

    return DeploymentRun(
        deployment_run_id=str(uuid4()),
        dry_run=False,
        status="running",
        submitted_at=now,
        completed_at=None,
        request=redact_payload(payload),
        steps=steps,
        commands=plan["commands"],
        outputs={
            "image_reference": plan["image_reference"],
            "hosted_application_name": payload["hosted_application_name"],
            "deployment_name": payload["deployment_name"],
            "endpoint_url": None,
            "resolved_identifiers": plan["resolved_identifiers"],
            "runtime_environment": redact_runtime_environment(
                plan["runtime_environment"]
            ),
            "dry_run_artifacts": plan["artifacts"],
            "note": "Live deployment started.",
        },
    )


def _execute_live_run(deployment_run_id: str, payload: dict[str, Any]) -> None:
    """Execute a live Agent Factory run and update its status incrementally."""

    deployment_run = RUNS[deployment_run_id]

    def update_progress(
        step_id: str, status: str, outputs: dict[str, Any] | None
    ) -> None:
        _set_step_status(
            deployment_run.steps,
            step_id,
            status,
            outputs=outputs,
            timestamp=utc_now(),
        )

    planned_steps = _build_steps(deployment_run.commands)
    try:
        execution_outputs = execute_live_deployment_commands(
            payload,
            _commands_by_step_id(planned_steps),
            update_progress,
        )
    except CommandExecutionError as exc:
        _mark_live_run_failed(
            deployment_run,
            payload,
            str(exc),
            exc.step_id,
            execution_outputs=exc.partial_outputs,
        )
        return

    plan = build_deployment_plan(payload, dry_run=False)
    deployment_run.outputs = _build_run_outputs(
        plan_payload=payload,
        plan=plan,
        dry_run=False,
        execution_outputs=execution_outputs,
    )
    deployment_run.status = "succeeded"
    deployment_run.completed_at = utc_now()


def _build_run_outputs(
    *,
    plan_payload: dict[str, Any],
    plan: dict[str, Any],
    dry_run: bool,
    execution_outputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build non-secret deployment run outputs."""

    outputs = {
        "image_reference": plan["image_reference"],
        "hosted_application_name": plan_payload["hosted_application_name"],
        "deployment_name": plan_payload["deployment_name"],
        "endpoint_url": None,
        "resolved_identifiers": plan["resolved_identifiers"],
        "runtime_environment": redact_runtime_environment(plan["runtime_environment"]),
        "dry_run_artifacts": plan["artifacts"],
        "note": (
            "Dry run completed with read-only checks and without OCI writes."
            if dry_run
            else (
                "Deployment workflow completed with Docker, OCIR, and Hosted "
                "Application operations."
            )
        ),
    }
    if execution_outputs:
        endpoint_url = execution_outputs.get("endpoint_url")
        hosted_application_id = execution_outputs.get("hosted_application_id")
        outputs.update(
            {
                "endpoint_url": endpoint_url,
                "hosted_application_id": hosted_application_id,
                "hosted_deployment_id": execution_outputs.get("hosted_deployment_id"),
            }
        )
        if endpoint_url:
            outputs.update(_build_hosted_application_urls(str(endpoint_url)))
        elif hosted_application_id:
            outputs.update(
                _build_hosted_application_urls(
                    _build_invoke_url(
                        region=str(plan_payload["region"]),
                        hosted_application_id=str(hosted_application_id),
                    )
                )
            )
    return outputs


def _build_hosted_application_urls(invoke_url: str) -> dict[str, str]:
    """Build public invoke URLs for a Hosted Application."""

    clean_url = invoke_url.rstrip("/")
    return {
        "hosted_application_invoke_url": clean_url,
        "hosted_application_health_url": f"{clean_url}/health",
        "hosted_application_agent_card_url": (
            f"{clean_url}/.well-known/agent-card.json"
        ),
        "hosted_application_message_stream_url": f"{clean_url}/message:stream",
    }


def _build_invoke_url(*, region: str, hosted_application_id: str) -> str:
    """Build the OCI Hosted Application invoke URL."""

    return (
        f"https://inference.generativeai.{region}.oci.oraclecloud.com/"
        f"{HOSTED_APPLICATION_API_VERSION}/hostedApplications/"
        f"{hosted_application_id}/actions/invoke"
    )


def _mark_live_run_failed(
    deployment_run: DeploymentRun,
    payload: dict[str, Any],
    error_message: str,
    failed_step_id: str | None = None,
    execution_outputs: dict[str, Any] | None = None,
) -> None:
    """Mark a live deployment run as failed."""

    timestamp = utc_now()
    _set_step_status(
        deployment_run.steps,
        failed_step_id or "hosted-deployment",
        "failed",
        error=error_message,
        timestamp=timestamp,
    )
    _mark_running_steps_failed(
        deployment_run.steps,
        error_message=error_message,
        timestamp=timestamp,
    )
    plan = build_deployment_plan(payload, dry_run=False)
    deployment_run.status = "failed"
    deployment_run.completed_at = timestamp
    deployment_run.outputs = _build_run_outputs(
        plan_payload=payload,
        plan=plan,
        dry_run=False,
        execution_outputs=execution_outputs,
    )
    deployment_run.outputs["note"] = (
        "Live deployment failed before completion. Previously completed "
        "steps may have created resources."
    )
    deployment_run.error = error_message


def _commands_by_step_id(steps: list[FactoryStep]) -> dict[str, list[str]]:
    """Return commands keyed by workflow step identifier."""

    return {step.step_id: step.command for step in steps if step.command is not None}


def _set_step_status(  # pylint: disable=too-many-arguments
    steps: list[FactoryStep],
    step_id: str,
    status: str,
    *,
    timestamp: str,
    outputs: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    """Update a workflow step status in place."""

    step = _find_step(steps, step_id)
    if step is None:
        return
    if step.started_at is None:
        step.started_at = timestamp
    step.status = status  # type: ignore[assignment]
    if status in {"succeeded", "failed", "skipped"}:
        step.ended_at = timestamp
    if outputs is not None:
        step.outputs = outputs
    if error is not None:
        step.error = error


def _mark_running_steps_failed(
    steps: list[FactoryStep], *, error_message: str, timestamp: str
) -> None:
    """Fail any step still marked running after a run-level failure."""

    for step in steps:
        if step.status == "running":
            step.status = "failed"
            step.ended_at = timestamp
            if step.error is None:
                step.error = error_message


def _find_step(steps: list[FactoryStep], step_id: str) -> FactoryStep | None:
    """Return a step by identifier."""

    for step in steps:
        if step.step_id == step_id:
            return step
    return None


def _build_steps(commands: list[list[str]]) -> list[FactoryStep]:
    """Build ordered Agent Factory workflow steps."""

    return [
        FactoryStep("validate-input", "Validate deployment inputs"),
        FactoryStep(
            "resolve-compartment",
            "Resolve target compartment",
            command=commands[0],
        ),
        FactoryStep(
            "docker-build",
            "Build A2A server image",
            command=commands[1],
        ),
        FactoryStep(
            "registry",
            "Check or prepare OCI Container Registry",
            command=commands[2],
        ),
        FactoryStep(
            "registry-login",
            "Authenticate Docker to OCI Container Registry",
            command=commands[3],
        ),
        FactoryStep(
            "docker-push",
            "Push image to OCI Container Registry",
            command=commands[4],
        ),
        FactoryStep(
            "runtime-environment",
            "Generate Hosted Application runtime environment",
        ),
        FactoryStep(
            "hosted-application",
            "Create OCI Enterprise AI Hosted Application",
            command=commands[5],
        ),
        FactoryStep(
            "hosted-deployment",
            "Create Hosted Application deployment",
            command=commands[6],
        ),
        FactoryStep(
            "deployment-readiness",
            "Wait for Hosted Application deployment readiness",
            command=commands[7],
        ),
        FactoryStep(
            "health",
            "Validate deployed health endpoint",
            command=commands[8],
        ),
    ]
