"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: Local sample A2A server entry point for the default LangGraph agent.
"""

from __future__ import annotations

import logging

import uvicorn

from oci_langgraph_a2a_blueprint.a2a_executor import create_default_agent_factory
from oci_langgraph_a2a_blueprint.a2a_server import create_server
from oci_langgraph_a2a_blueprint.config import load_a2a_server_settings


def main() -> None:
    """Run the local sample A2A server with uvicorn."""
    settings = load_a2a_server_settings()
    agent_factory = create_default_agent_factory(settings.step_sleep_seconds)

    logging.basicConfig(level=getattr(logging, settings.log_level))
    uvicorn.run(
        create_server(
            agent_factory=agent_factory,
            server_url=settings.public_url,
        ),
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()
