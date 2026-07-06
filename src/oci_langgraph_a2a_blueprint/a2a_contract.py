"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: Reusable A2A streaming agent contracts.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Protocol

from a2a import types as a2a_types

from oci_langgraph_a2a_blueprint.state import AgentProgressEvent


class StreamingAgent(Protocol):
    """Minimal streaming contract required by the A2A executor."""

    def stream(self, input_text: str) -> AsyncIterator[AgentProgressEvent]:
        """Stream agent progress events for the provided input text."""


AgentFactory = Callable[[], StreamingAgent]
AgentCardFactory = Callable[[str], a2a_types.AgentCard]
