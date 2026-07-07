"""
Author: L. Saetta
Date last modified: 2026-07-07
License: MIT
Description: Unit tests for the bare LangGraph agent implementation.
Agent customization: Update when the sample bare agent behavior changes.
"""

from __future__ import annotations

import logging

import pytest
from langchain_core.runnables import Runnable

from oci_langgraph_a2a_blueprint import BareLangGraphAgent
from oci_langgraph_a2a_blueprint.agent.steps import (
    Step1,
    Step2,
    Step3,
    create_default_steps,
)


def test_default_steps_are_langchain_runnables_and_support_invoke() -> None:
    """Verify each workflow step is a LangChain Runnable."""
    steps = create_default_steps(step_sleep_seconds=0)

    state = {"input_text": "hello", "progress": []}
    first_update = steps[0].invoke(state)

    assert [type(step) for step in steps] == [Step1, Step2, Step3]
    assert all(isinstance(step, Runnable) for step in steps)
    assert first_update["state1"] == "step1 processed: hello"
    assert first_update["progress"] == ["step1 completed"]


def test_agent_invocation_updates_shared_state_in_order() -> None:
    """Verify the graph updates state1, state2, state3, and final output."""
    agent = BareLangGraphAgent(step_sleep_seconds=0)

    result = agent.invoke("hello")

    assert result["state1"] == "step1 processed: hello"
    assert result["state2"] == "step2 processed: step1 processed: hello"
    assert (
        result["state3"] == "step3 processed: step2 processed: step1 processed: hello"
    )
    assert result["final_output"] == result["state3"]
    assert result["progress"] == [
        "step1 completed",
        "step2 completed",
        "step3 completed",
    ]


def test_agent_build_graph_returns_invokable_compiled_graph() -> None:
    """Verify the graph builder returns a compiled graph."""
    graph = BareLangGraphAgent.build_graph(create_default_steps(step_sleep_seconds=0))

    result = graph.invoke({"input_text": "graph", "progress": []})

    assert result["final_output"].endswith("graph")


def test_agent_rejects_empty_input() -> None:
    """Verify empty input is rejected before graph execution."""
    agent = BareLangGraphAgent(step_sleep_seconds=0)

    with pytest.raises(ValueError, match="input_text must not be empty"):
        agent.invoke("  ")


def test_agent_rejects_negative_sleep_duration() -> None:
    """Verify invalid sleep configuration is rejected."""
    with pytest.raises(
        ValueError,
        match="step_sleep_seconds must be greater than or equal to 0",
    ):
        BareLangGraphAgent(step_sleep_seconds=-1)


def test_agent_logs_step_start_and_completion(caplog: pytest.LogCaptureFixture) -> None:
    """Verify every step logs start and completion messages."""
    agent = BareLangGraphAgent(step_sleep_seconds=0)

    with caplog.at_level(logging.INFO):
        agent.invoke("logging")

    messages = [record.getMessage() for record in caplog.records]
    assert "step1 started" in messages
    assert "step1 completed" in messages
    assert "step2 started" in messages
    assert "step2 completed" in messages
    assert "step3 started" in messages
    assert "step3 completed" in messages


@pytest.mark.asyncio
async def test_agent_streams_step_updates_in_order() -> None:
    """Verify streaming emits step completion events and final completion."""
    agent = BareLangGraphAgent(step_sleep_seconds=0)

    events = [event async for event in agent.stream("streaming")]

    assert [event.event_type for event in events] == [
        "step_completed",
        "step_completed",
        "step_completed",
        "agent_completed",
    ]
    assert [event.source for event in events] == [
        "step1",
        "step2",
        "step3",
        None,
    ]
    assert events[-1].state["final_output"] == events[-1].state["state3"]
