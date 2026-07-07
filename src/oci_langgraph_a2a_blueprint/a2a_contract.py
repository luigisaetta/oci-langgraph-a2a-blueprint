"""
Author: L. Saetta
Date last modified: 2026-07-07
License: MIT
Description: Reusable A2A streaming agent contracts.
Agent customization: Do not modify unless the shared agent contract changes.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from a2a import types as a2a_types
from pydantic import BaseModel, ConfigDict, Field

A2A_PROTOCOL_VERSION = "1.0"
REST_PROTOCOL_BINDING = "HTTP+JSON"
AgentEventType = Literal["step_completed", "data", "agent_completed", "agent_failed"]


class AgentProgressEvent(BaseModel):
    """Structured event emitted by a streaming agent.

    Attributes:
        event_type: Type of progress event emitted by the agent.
        message: Human-readable progress message.
        state: Current agent state snapshot, if available.
        source: Agent component that produced the event, if applicable.
        data: Optional intermediate data emitted by the source.
    """

    model_config = ConfigDict(frozen=True)

    event_type: AgentEventType
    message: str
    state: Mapping[str, Any] = Field(default_factory=dict)
    source: str | None = None
    data: Any | None = None


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
