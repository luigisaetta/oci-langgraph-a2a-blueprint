"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: A2A HTTP/SSE server factory for the OCI LangGraph A2A blueprint.
"""

from __future__ import annotations

import logging
import os

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.rest_routes import create_rest_routes
from a2a.server.tasks import InMemoryTaskStore
from starlette.applications import Starlette

from oci_langgraph_a2a_blueprint.a2a_card import DEFAULT_SERVER_URL, create_agent_card
from oci_langgraph_a2a_blueprint.a2a_executor import LangGraphAgentExecutor
from oci_langgraph_a2a_blueprint.agent import DEFAULT_STEP_SLEEP_SECONDS

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
DEFAULT_LOG_LEVEL = "INFO"


def create_app(
    server_url: str = DEFAULT_SERVER_URL,
    step_sleep_seconds: float = DEFAULT_STEP_SLEEP_SECONDS,
) -> Starlette:
    """Create the A2A Starlette application.

    Args:
        server_url: Public base URL advertised by the Agent Card.
        step_sleep_seconds: Simulated work duration for each LangGraph step.

    Returns:
        Configured Starlette application exposing Agent Card and SSE streaming.
    """
    agent_card = create_agent_card(server_url=server_url)
    request_handler = DefaultRequestHandler(
        agent_executor=LangGraphAgentExecutor(
            step_sleep_seconds=step_sleep_seconds,
        ),
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )

    routes = create_agent_card_routes(agent_card)
    routes.extend(_streaming_only_routes(request_handler))
    return Starlette(routes=routes)


def main() -> None:
    """Run the local A2A server with uvicorn."""
    host = os.getenv("A2A_SERVER_HOST", DEFAULT_HOST)
    port = int(os.getenv("A2A_SERVER_PORT", str(DEFAULT_PORT)))
    public_url = os.getenv("A2A_SERVER_PUBLIC_URL", _default_public_url(host, port))
    step_sleep_seconds = float(
        os.getenv("AGENT_STEP_SLEEP_SECONDS", str(DEFAULT_STEP_SLEEP_SECONDS))
    )
    log_level = os.getenv("AGENT_LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()

    logging.basicConfig(level=getattr(logging, log_level))
    uvicorn.run(
        create_app(
            server_url=public_url,
            step_sleep_seconds=step_sleep_seconds,
        ),
        host=host,
        port=port,
    )


def _streaming_only_routes(request_handler: DefaultRequestHandler) -> list:
    """Create only the A2A REST streaming route from the SDK route set.

    Args:
        request_handler: SDK request handler.

    Returns:
        Routes limited to `POST /message:stream`.
    """
    return [
        route
        for route in create_rest_routes(request_handler)
        if getattr(route, "path", None) == "/message:stream"
    ]


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


if __name__ == "__main__":
    main()
