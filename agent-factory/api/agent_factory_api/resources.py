"""
Author: L. Saetta
Date last modified: 2026-07-08
License: MIT
Description: External resource validation helpers for A2A Agent Factory.
"""

from __future__ import annotations

import os
import subprocess
import tempfile

OCIR_LOGIN_TIMEOUT_SECONDS = 60


class ResourceProvisioningError(RuntimeError):
    """Raised when Agent Factory cannot validate an external resource."""


def validate_ocir_login(
    *, registry: str, username: str, password: str
) -> dict[str, str]:
    """Validate OCI Container Registry Docker credentials.

    Args:
        registry: OCIR registry hostname, such as `fra.ocir.io`.
        username: OCIR login username.
        password: OCIR auth token or password.

    Returns:
        dict[str, str]: Non-secret validation result.

    Raises:
        ResourceProvisioningError: If Docker login fails or Docker is missing.
    """

    if not registry.strip():
        raise ResourceProvisioningError("OCIR registry is required.")
    if not username.strip():
        raise ResourceProvisioningError("OCIR username is required.")
    if not password:
        raise ResourceProvisioningError("OCIR password is required.")

    with tempfile.TemporaryDirectory(prefix="agent-factory-docker-") as docker_dir:
        environment = dict(os.environ)
        environment["DOCKER_CONFIG"] = docker_dir
        try:
            result = subprocess.run(
                [
                    "docker",
                    "login",
                    registry,
                    "--username",
                    username,
                    "--password-stdin",
                ],
                input=password,
                text=True,
                capture_output=True,
                check=False,
                timeout=OCIR_LOGIN_TIMEOUT_SECONDS,
                env=environment,
            )
        except FileNotFoundError as exc:
            raise ResourceProvisioningError("Docker CLI is required.") from exc
        except subprocess.TimeoutExpired as exc:
            raise ResourceProvisioningError("OCIR Docker login timed out.") from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "Docker login failed.").strip()
        detail = detail.replace(password, "********")
        raise ResourceProvisioningError(detail)

    return {
        "ocir_registry": registry,
        "ocir_username": username,
    }
