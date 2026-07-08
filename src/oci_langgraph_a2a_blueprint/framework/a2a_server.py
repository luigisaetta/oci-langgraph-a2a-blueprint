"""
Author: L. Saetta
Date last modified: 2026-07-08
License: MIT
Description: A2A HTTP/SSE server factory for the OCI LangGraph A2A blueprint.
Agent customization: Do not modify for normal agent replacement.
"""

from __future__ import annotations

import logging
from copy import deepcopy

from a2a import types as a2a_types
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.rest_routes import create_rest_routes
from a2a.server.tasks import InMemoryTaskStore
from google.protobuf.json_format import MessageToDict
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn

from oci_langgraph_a2a_blueprint.framework.a2a_contract import AgentFactory
from oci_langgraph_a2a_blueprint.framework.a2a_executor import LangGraphAgentExecutor
from oci_langgraph_a2a_blueprint.framework.a2a_server_config import (
    load_a2a_server_settings,
)
from oci_langgraph_a2a_blueprint.agent.agent_adapter import create_agent_adapter


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

    routes = [_agent_card_route(agent_card)]
    routes.extend(_streaming_only_routes(request_handler))
    return Starlette(routes=routes)


def _agent_card_route(agent_card: a2a_types.AgentCard) -> Route:
    """Create an Agent Card route that reflects the incoming public URL.

    Args:
        agent_card: Base Agent Card for the exposed agent.

    Returns:
        Starlette route for public Agent Card discovery.
    """

    async def get_agent_card(request: Request) -> JSONResponse:
        public_url = _public_url_from_request(request)
        card = deepcopy(agent_card)
        for supported_interface in card.supported_interfaces:
            supported_interface.url = public_url
        return JSONResponse(MessageToDict(card))

    return Route("/.well-known/agent-card.json", get_agent_card, methods=["GET"])


def _public_url_from_request(request: Request) -> str:
    """Build the public base URL for the current Agent Card request.

    Args:
        request: Incoming Starlette request.

    Returns:
        Public URL without the Agent Card discovery suffix.
    """

    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host")
    forwarded_prefix = request.headers.get("x-forwarded-prefix", "").rstrip("/")

    if forwarded_proto and forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}{forwarded_prefix}"

    request_url = str(request.url)
    return request_url.removesuffix("/.well-known/agent-card.json")


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
    agent_adapter = create_agent_adapter()
    agent_card = agent_adapter.agent_card_factory(settings.public_url)

    logging.basicConfig(level=getattr(logging, settings.log_level))
    uvicorn.run(
        create_server(
            agent_factory=agent_adapter.agent_factory,
            agent_card=agent_card,
        ),
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()
