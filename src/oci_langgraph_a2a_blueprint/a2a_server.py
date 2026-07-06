"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: A2A HTTP/SSE server factory for the OCI LangGraph A2A blueprint.
"""

from __future__ import annotations

import logging

import uvicorn
from a2a import types as a2a_types
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.rest_routes import create_rest_routes
from a2a.server.tasks import InMemoryTaskStore
from starlette.applications import Starlette

from oci_langgraph_a2a_blueprint.a2a_card import DEFAULT_SERVER_URL, create_agent_card
from oci_langgraph_a2a_blueprint.a2a_executor import (
    AgentFactory,
    LangGraphAgentExecutor,
    create_default_agent_factory,
)
from oci_langgraph_a2a_blueprint.agent import DEFAULT_STEP_SLEEP_SECONDS
from oci_langgraph_a2a_blueprint.config import load_a2a_server_settings


def create_app(
    server_url: str = DEFAULT_SERVER_URL,
    step_sleep_seconds: float = DEFAULT_STEP_SLEEP_SECONDS,
    agent_factory: AgentFactory | None = None,
    agent_card: a2a_types.AgentCard | None = None,
) -> Starlette:
    """Create the A2A Starlette application.

    Args:
        server_url: Public base URL advertised by the Agent Card.
        step_sleep_seconds: Simulated work duration for the sample agent.
        agent_factory: Optional factory for a custom streaming LangGraph agent.
        agent_card: Optional Agent Card for a custom agent.

    Returns:
        Configured Starlette application exposing Agent Card and SSE streaming.
    """
    resolved_agent_card = agent_card or create_agent_card(server_url=server_url)
    resolved_agent_factory = agent_factory or create_default_agent_factory(
        step_sleep_seconds=step_sleep_seconds,
    )
    request_handler = DefaultRequestHandler(
        agent_executor=LangGraphAgentExecutor(agent_factory=resolved_agent_factory),
        task_store=InMemoryTaskStore(),
        agent_card=resolved_agent_card,
    )

    routes = create_agent_card_routes(resolved_agent_card)
    routes.extend(_streaming_only_routes(request_handler))
    return Starlette(routes=routes)


def main() -> None:
    """Run the local A2A server with uvicorn."""
    settings = load_a2a_server_settings()

    logging.basicConfig(level=getattr(logging, settings.log_level))
    uvicorn.run(
        create_app(
            server_url=settings.public_url,
            step_sleep_seconds=settings.step_sleep_seconds,
        ),
        host=settings.host,
        port=settings.port,
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


if __name__ == "__main__":
    main()
