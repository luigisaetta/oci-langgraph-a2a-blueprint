"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: Adapter that plugs the LangGraph agent into the A2A server.
Agent customization: Modify this file to plug in a different agent.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from a2a import types as a2a_types

from oci_langgraph_a2a_blueprint.a2a_contract import AgentAdapter, AgentFactory
from oci_langgraph_a2a_blueprint.agent import (
    DEFAULT_STEP_SLEEP_SECONDS,
    BareLangGraphAgent,
)
from oci_langgraph_a2a_blueprint.parse_utils import parse_float

A2A_PROTOCOL_VERSION = "1.0"
DEFAULT_SERVER_URL = "http://localhost:8080"
REST_PROTOCOL_BINDING = "HTTP+JSON"
AGENT_STEP_SLEEP_SECONDS_ENV = "AGENT_STEP_SLEEP_SECONDS"


def create_agent_adapter() -> AgentAdapter:
    """Create the adapter used by the A2A server to expose the agent.

    Returns:
        Agent adapter containing the agent factory and Agent Card factory.
    """
    return AgentAdapter(
        agent_factory=create_agent_factory(),
        agent_card_factory=create_agent_card,
    )


def create_agent_factory(
    step_sleep_seconds: float | None = None,
) -> AgentFactory:
    """Create the LangGraph agent factory.

    Args:
        step_sleep_seconds: Optional simulated work duration for each step.
            Defaults to the local agent environment setting.

    Returns:
        Factory that creates configured agent instances.
    """
    if step_sleep_seconds is None:
        step_sleep_seconds = load_agent_settings().step_sleep_seconds

    return lambda: BareLangGraphAgent(step_sleep_seconds=step_sleep_seconds)


@dataclass(frozen=True)
class AgentSettings:
    """Runtime settings owned by the LangGraph agent.

    Attributes:
        step_sleep_seconds: Simulated work duration for each step.
    """

    step_sleep_seconds: float


def load_agent_settings(
    environ: Mapping[str, str] | None = None,
) -> AgentSettings:
    """Load agent settings from environment variables.

    Args:
        environ: Optional environment mapping. Defaults to `os.environ`.

    Returns:
        Parsed agent settings.

    Raises:
        ValueError: If the agent sleep setting is invalid.
    """
    source = environ or os.environ
    return AgentSettings(
        step_sleep_seconds=parse_float(
            source.get(AGENT_STEP_SLEEP_SECONDS_ENV),
            default=DEFAULT_STEP_SLEEP_SECONDS,
            variable_name=AGENT_STEP_SLEEP_SECONDS_ENV,
        )
    )


def create_agent_card(
    server_url: str = DEFAULT_SERVER_URL,
) -> a2a_types.AgentCard:
    """Create the public A2A Agent Card for the agent.

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
