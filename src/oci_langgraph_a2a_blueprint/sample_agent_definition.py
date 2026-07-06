"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: Sample LangGraph agent definition used by the local A2A runner.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from a2a import types as a2a_types

from oci_langgraph_a2a_blueprint.a2a_contract import AgentCardFactory, AgentFactory
from oci_langgraph_a2a_blueprint.agent import (
    DEFAULT_STEP_SLEEP_SECONDS,
    BareLangGraphAgent,
)

A2A_PROTOCOL_VERSION = "1.0"
DEFAULT_SERVER_URL = "http://localhost:8000"
REST_PROTOCOL_BINDING = "HTTP+JSON"
SAMPLE_AGENT_STEP_SLEEP_SECONDS_ENV = "AGENT_STEP_SLEEP_SECONDS"


@dataclass(frozen=True)
class AgentDefinition:
    """Complete definition required to expose an agent through A2A.

    Attributes:
        agent_factory: Factory that creates streaming agent instances.
        agent_card_factory: Factory that creates the public Agent Card for a
            server URL.
    """

    agent_factory: AgentFactory
    agent_card_factory: AgentCardFactory


def create_agent_definition() -> AgentDefinition:
    """Create the LangGraph agent definition exposed by the A2A server.

    Returns:
        Agent definition containing the agent factory and Agent Card factory.
    """
    return AgentDefinition(
        agent_factory=create_sample_agent_factory(),
        agent_card_factory=create_sample_agent_card,
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
        step_sleep_seconds = load_sample_agent_settings().step_sleep_seconds

    return lambda: BareLangGraphAgent(step_sleep_seconds=step_sleep_seconds)


@dataclass(frozen=True)
class SampleAgentSettings:
    """Runtime settings owned by the sample LangGraph agent.

    Attributes:
        step_sleep_seconds: Simulated work duration for each sample step.
    """

    step_sleep_seconds: float


def load_sample_agent_settings(
    environ: Mapping[str, str] | None = None,
) -> SampleAgentSettings:
    """Load sample-agent settings from environment variables.

    Args:
        environ: Optional environment mapping. Defaults to `os.environ`.

    Returns:
        Parsed sample-agent settings.

    Raises:
        ValueError: If the sample-agent sleep setting is invalid.
    """
    source = environ or os.environ
    return SampleAgentSettings(
        step_sleep_seconds=_parse_sample_agent_sleep_seconds(
            source.get(SAMPLE_AGENT_STEP_SLEEP_SECONDS_ENV)
        )
    )


def _parse_sample_agent_sleep_seconds(value: str | None) -> float:
    """Parse the sample-agent sleep duration.

    Args:
        value: Raw value from the environment.

    Returns:
        Parsed sleep duration.

    Raises:
        ValueError: If `value` is not a valid float.
    """
    if value is None:
        return DEFAULT_STEP_SLEEP_SECONDS
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(
            f"{SAMPLE_AGENT_STEP_SLEEP_SECONDS_ENV} must be a float"
        ) from exc


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
