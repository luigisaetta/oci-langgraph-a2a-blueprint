"""
Author: L. Saetta
Date last modified: 2026-07-07
License: MIT
Description: State model used by the bare LangGraph agent.
Agent customization: Modify only if the custom agent changes state shape.
"""

from __future__ import annotations

import operator
from typing import Annotated

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
