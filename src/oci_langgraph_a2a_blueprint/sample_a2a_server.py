"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: Local sample A2A server entry point for the default LangGraph agent.
"""

from __future__ import annotations

import logging

import uvicorn

from oci_langgraph_a2a_blueprint.a2a_server import create_server
from oci_langgraph_a2a_blueprint.config import load_a2a_server_settings
from oci_langgraph_a2a_blueprint.sample_agent_definition import (
    create_sample_agent_definition,
)


def main() -> None:
    """Run the local sample A2A server with uvicorn."""
    settings = load_a2a_server_settings()
    agent_definition = create_sample_agent_definition(
        server_url=settings.public_url,
    )

    logging.basicConfig(level=getattr(logging, settings.log_level))
    uvicorn.run(
        create_server(
            agent_factory=agent_definition.agent_factory,
            agent_card=agent_definition.agent_card,
        ),
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()
