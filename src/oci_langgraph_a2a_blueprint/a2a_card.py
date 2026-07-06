"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: A2A Agent Card factory for the OCI LangGraph A2A blueprint.
"""

from __future__ import annotations

from a2a import types as a2a_types

A2A_PROTOCOL_VERSION = "1.0"
DEFAULT_SERVER_URL = "http://localhost:8000"
REST_PROTOCOL_BINDING = "HTTP+JSON"


def create_agent_card(server_url: str = DEFAULT_SERVER_URL) -> a2a_types.AgentCard:
    """Create the public A2A Agent Card for the blueprint agent.

    Args:
        server_url: Public base URL where this A2A server is reachable.

    Returns:
        A2A Agent Card protobuf object.
    """
    return a2a_types.AgentCard(
        name="OCI LangGraph A2A Blueprint Agent",
        description=(
            "Blueprint agent that runs a three-step LangGraph workflow and "
            "streams task progress over the A2A HTTP+JSON/REST binding."
        ),
        version="0.1.0",
        supported_interfaces=[
            a2a_types.AgentInterface(
                url=server_url,
                protocol_binding=REST_PROTOCOL_BINDING,
                protocol_version=A2A_PROTOCOL_VERSION,
            )
        ],
        provider=a2a_types.AgentProvider(
            organization="Oracle",
            url="https://www.oracle.com/cloud/",
        ),
        capabilities=a2a_types.AgentCapabilities(
            streaming=True,
            push_notifications=False,
            extended_agent_card=False,
        ),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            a2a_types.AgentSkill(
                id="three-step-langgraph-workflow",
                name="Three-step LangGraph workflow",
                description=(
                    "Runs step1, step2, and step3 with shared LangGraph state "
                    "and streams progress as each step completes."
                ),
                tags=["langgraph", "blueprint", "streaming"],
                examples=["Run the sample workflow for this input text."],
                input_modes=["text/plain"],
                output_modes=["text/plain"],
            )
        ],
    )
