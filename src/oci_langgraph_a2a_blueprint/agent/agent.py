"""
Author: L. Saetta
Date last modified: 2026-07-07
License: MIT
Description: Bare LangGraph agent implementation for the OCI A2A blueprint.
Agent customization: Modify only when changing the sample bare agent itself.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from oci_langgraph_a2a_blueprint.framework.a2a_contract import AgentProgressEvent
from oci_langgraph_a2a_blueprint.agent.state import AgentState
from oci_langgraph_a2a_blueprint.agent.steps import BaseStep, create_default_steps

DEFAULT_STEP_SLEEP_SECONDS = 1.0


def _initial_state(input_text: str) -> AgentState:
    """Build the initial graph state from caller input.

    Args:
        input_text: Original caller input.

    Returns:
        Initial agent state.

    Raises:
        ValueError: If `input_text` is empty or only whitespace.
    """
    if not input_text.strip():
        raise ValueError("input_text must not be empty")

    return {"input_text": input_text, "progress": []}


def _merge_state(current_state: AgentState, partial_update: AgentState) -> AgentState:
    """Merge a LangGraph partial update into the local streaming snapshot.

    Args:
        current_state: Current state snapshot.
        partial_update: Partial state update emitted by a graph node.

    Returns:
        New merged state snapshot.
    """
    merged: AgentState = {**current_state}
    for key, value in partial_update.items():
        if key == "progress":
            merged["progress"] = merged.get("progress", []) + list(value)
        else:
            merged[key] = value
    return merged


class BareLangGraphAgent:
    """Bare three-step LangGraph agent used by the blueprint.

    Args:
        step_sleep_seconds: Simulated work duration for each step.
    """

    def __init__(
        self,
        step_sleep_seconds: float = DEFAULT_STEP_SLEEP_SECONDS,
    ) -> None:
        self.steps = create_default_steps(step_sleep_seconds=step_sleep_seconds)
        self.graph = self.build_graph(self.steps)

    def invoke(self, input_text: str) -> AgentState:
        """Run the full graph synchronously.

        Args:
            input_text: Original caller input.

        Returns:
            Final shared agent state.

        Raises:
            ValueError: If `input_text` is empty or only whitespace.
        """
        return self.graph.invoke(_initial_state(input_text))

    async def stream(self, input_text: str) -> AsyncIterator[AgentProgressEvent]:
        """Run the graph and stream structured progress events.

        Args:
            input_text: Original caller input.

        Yields:
            Step completion events and a final agent completion event.

        Raises:
            ValueError: If `input_text` is empty or only whitespace.
        """
        state = _initial_state(input_text)

        async for update in self.graph.astream(state, stream_mode="updates"):
            for step_name, partial_update in update.items():
                state = _merge_state(state, partial_update)
                yield AgentProgressEvent(
                    event_type="step_completed",
                    source=step_name,
                    message=f"{step_name} completed",
                    state=state,
                )

        yield AgentProgressEvent(
            event_type="agent_completed",
            source=None,
            message="agent completed",
            state=state,
        )

    @staticmethod
    def build_graph(
        steps: Iterable[BaseStep],
    ) -> CompiledStateGraph:
        """Build and compile a graph from explicit step definitions.

        Args:
            steps: Ordered step definitions to add as graph nodes.

        Returns:
            Compiled LangGraph state graph.
        """
        builder = StateGraph(AgentState)

        previous_node = START
        for step in steps:
            builder.add_node(step.name, step)
            builder.add_edge(previous_node, step.name)
            previous_node = step.name

        builder.add_edge(previous_node, END)
        return builder.compile()
