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

    A streaming agent yields these events to report progress, intermediate
    payloads, completion, or controlled failures. The A2A executor consumes this
    framework-level contract and maps it to A2A task status and artifact events.

    Attributes:
        event_type: Event category. Use `step_completed` when a step, node, or
            tool finishes; `data` when a source emits intermediate payloads;
            `agent_completed` when the final state or output is available; and
            `agent_failed` for controlled failures that should fail the A2A task.
        message: Human-readable progress message suitable for status updates.
        state: Optional snapshot of the agent state at the time of the event.
            The executor reads the final output from this mapping when handling
            `agent_completed`.
        source: Optional name of the component that emitted the event, such as a
            LangGraph node, workflow step, tool, retriever, or model.
        data: Optional intermediate payload emitted by `source`. Use this for
            chunks, tool output, retrieval snippets, or structured partial
            results that are useful before final completion.
    """

    model_config = ConfigDict(frozen=True)

    # Keep events immutable at the Pydantic field level once emitted. This makes
    # each event behave like a point-in-time fact as it moves through adapters.
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
