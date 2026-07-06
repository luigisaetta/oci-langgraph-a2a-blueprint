"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: A2A HTTP/SSE server factory for the OCI LangGraph A2A blueprint.
"""

from __future__ import annotations

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
)


def create_server(
    agent_factory: AgentFactory,
    server_url: str = DEFAULT_SERVER_URL,
    agent_card: a2a_types.AgentCard | None = None,
) -> Starlette:
    """Create the A2A Starlette server application.

    Args:
        agent_factory: Factory for the streaming LangGraph agent to expose.
        server_url: Public base URL advertised by the generated Agent Card.
        agent_card: Optional Agent Card for a custom agent.

    Returns:
        Configured Starlette application exposing Agent Card and SSE streaming.
    """
    resolved_agent_card = agent_card or create_agent_card(server_url=server_url)
    request_handler = DefaultRequestHandler(
        agent_executor=LangGraphAgentExecutor(agent_factory=agent_factory),
        task_store=InMemoryTaskStore(),
        agent_card=resolved_agent_card,
    )

    routes = create_agent_card_routes(resolved_agent_card)
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
