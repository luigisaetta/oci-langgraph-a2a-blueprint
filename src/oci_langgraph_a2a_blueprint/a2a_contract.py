"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: Reusable A2A streaming agent contracts.
Agent customization: Do not modify unless the shared agent contract changes.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Protocol

from a2a import types as a2a_types

from oci_langgraph_a2a_blueprint.state import AgentProgressEvent

A2A_PROTOCOL_VERSION = "1.0"
REST_PROTOCOL_BINDING = "HTTP+JSON"


class StreamingAgent(Protocol):
    """Minimal streaming contract required by the A2A executor."""

    def stream(self, input_text: str) -> AsyncIterator[AgentProgressEvent]:
        """Stream agent progress events for the provided input text."""


AgentFactory = Callable[[], StreamingAgent]
AgentCardFactory = Callable[[str], a2a_types.AgentCard]


@dataclass(frozen=True)
class AgentAdapter:
    """Complete adapter required to expose an agent through A2A.

    Attributes:
        agent_factory: Factory that creates streaming agent instances.
        agent_card_factory: Factory that creates the public Agent Card for a
            server URL.
    """

    agent_factory: AgentFactory
    agent_card_factory: AgentCardFactory
