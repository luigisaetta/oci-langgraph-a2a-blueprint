"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: Sample LangGraph agent definition used by the local A2A runner.
"""

from __future__ import annotations

from dataclasses import dataclass

from a2a import types as a2a_types

from oci_langgraph_a2a_blueprint.a2a_contract import AgentFactory
from oci_langgraph_a2a_blueprint.agent import BareLangGraphAgent
from oci_langgraph_a2a_blueprint.config import load_a2a_server_settings

A2A_PROTOCOL_VERSION = "1.0"
DEFAULT_SERVER_URL = "http://localhost:8000"
REST_PROTOCOL_BINDING = "HTTP+JSON"


@dataclass(frozen=True)
class AgentDefinition:
    """Complete definition required to expose an agent through A2A.

    Attributes:
        agent_factory: Factory that creates streaming agent instances.
        agent_card: A2A Agent Card describing the exposed agent.
    """

    agent_factory: AgentFactory
    agent_card: a2a_types.AgentCard


def create_sample_agent_definition(
    server_url: str = DEFAULT_SERVER_URL,
    step_sleep_seconds: float | None = None,
) -> AgentDefinition:
    """Create the sample LangGraph agent definition.

    Args:
        server_url: Public base URL where this A2A server is reachable.
        step_sleep_seconds: Optional simulated work duration for each sample
            step. Defaults to the local sample-agent environment setting.

    Returns:
        Agent definition containing sample factory and Agent Card.
    """
    return AgentDefinition(
        agent_factory=create_sample_agent_factory(
            step_sleep_seconds=step_sleep_seconds,
        ),
        agent_card=create_sample_agent_card(server_url=server_url),
    )


def create_sample_agent_factory(
    step_sleep_seconds: float | None = None,
) -> AgentFactory:
    """Create the sample LangGraph agent factory.

    Args:
        step_sleep_seconds: Optional simulated work duration for each sample
            step. Defaults to the local sample-agent environment setting.

    Returns:
        Factory that creates configured sample agent instances.
    """
    if step_sleep_seconds is None:
        step_sleep_seconds = load_a2a_server_settings().step_sleep_seconds

    return lambda: BareLangGraphAgent(step_sleep_seconds=step_sleep_seconds)


def create_sample_agent_card(
    server_url: str = DEFAULT_SERVER_URL,
) -> a2a_types.AgentCard:
    """Create the public A2A Agent Card for the sample agent.

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
