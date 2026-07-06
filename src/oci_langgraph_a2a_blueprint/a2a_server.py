"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: A2A HTTP/SSE server factory for the OCI LangGraph A2A blueprint.
Agent customization: Do not modify for normal agent replacement.
"""

from __future__ import annotations

import logging

from a2a import types as a2a_types
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.rest_routes import create_rest_routes
from a2a.server.tasks import InMemoryTaskStore
from starlette.applications import Starlette
import uvicorn

from oci_langgraph_a2a_blueprint.a2a_contract import AgentFactory
from oci_langgraph_a2a_blueprint.a2a_executor import LangGraphAgentExecutor
from oci_langgraph_a2a_blueprint.config import load_a2a_server_settings
from oci_langgraph_a2a_blueprint.sample_agent_definition import (
    create_agent_definition,
)


def create_server(
    agent_factory: AgentFactory,
    agent_card: a2a_types.AgentCard,
) -> Starlette:
    """Create the A2A Starlette server application.

    Args:
        agent_factory: Factory for the streaming LangGraph agent to expose.
        agent_card: Agent Card for the exposed agent.

    Returns:
        Configured Starlette application exposing Agent Card and SSE streaming.
    """
    request_handler = DefaultRequestHandler(
        agent_executor=LangGraphAgentExecutor(agent_factory=agent_factory),
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )

    routes = create_agent_card_routes(agent_card)
    routes.extend(_streaming_only_routes(request_handler))
    return Starlette(routes=routes)


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


def main() -> None:
    """Run the local A2A server with uvicorn."""
    settings = load_a2a_server_settings()
    agent_definition = create_agent_definition()
    agent_card = agent_definition.agent_card_factory(settings.public_url)

    logging.basicConfig(level=getattr(logging, settings.log_level))
    uvicorn.run(
        create_server(
            agent_factory=agent_definition.agent_factory,
            agent_card=agent_card,
        ),
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()
