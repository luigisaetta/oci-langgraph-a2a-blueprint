"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: State and event models used by the bare LangGraph agent.
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """Shared state passed through the bare LangGraph agent.

    Attributes:
        input_text: Original caller input.
        state1: Output produced by step1.
        state2: Output produced by step2.
        state3: Output produced by step3.
        progress: Ordered progress messages collected during execution.
        final_output: Final response text produced by the graph.
    """

    input_text: str
    state1: str
    state2: str
    state3: str
    progress: Annotated[list[str], operator.add]
    final_output: str


ProgressEventType = Literal["step_completed", "agent_completed"]


class AgentProgressEvent(BaseModel):
    """Structured event emitted by the bare agent streaming API.

    Attributes:
        event_type: Type of progress event.
        message: Human-readable progress message.
        state: Current state snapshot.
        step_name: Step that produced the event, if applicable.
    """

    model_config = ConfigDict(frozen=True)

    event_type: ProgressEventType
    message: str
    state: AgentState
    step_name: str | None = None
