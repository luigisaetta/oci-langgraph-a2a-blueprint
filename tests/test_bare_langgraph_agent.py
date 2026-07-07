"""
Author: L. Saetta
Date last modified: 2026-07-07
License: MIT
Description: Unit tests for the sample LangGraph agent implementation.
Agent customization: Update when the sample agent behavior changes.
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


class FakeLlmResponder:
    """Fake LLM responder used to avoid network calls in unit tests."""

    def __init__(self, answer_text: str = "llm answered: hello") -> None:
        self.answer_text = answer_text
        self.requests: list[str] = []

    def answer(self, input_text: str) -> str:
        """Return a deterministic answer and record the input text."""
        self.requests.append(input_text)
        return self.answer_text


def test_default_steps_are_langchain_runnables_and_support_invoke() -> None:
    """Verify each workflow step is a LangChain Runnable."""
    llm_client = FakeLlmResponder()
    steps = create_default_steps(step_sleep_seconds=0, llm_client=llm_client)

    state = {"input_text": "hello", "progress": []}
    first_update = steps[0].invoke(state)
    second_update = steps[1].invoke({**state, **first_update})

    assert [type(step) for step in steps] == [Step1, Step2, Step3]
    assert all(isinstance(step, Runnable) for step in steps)
    assert first_update["state1"] == "step1 processed: hello"
    assert first_update["progress"] == ["step1 completed"]
    assert second_update["state2"] == "llm answered: hello"
    assert llm_client.requests == ["hello"]


def test_agent_invocation_updates_shared_state_in_order() -> None:
    """Verify the graph updates state1, state2, state3, and final output."""
    agent = BareLangGraphAgent(
        step_sleep_seconds=0,
        llm_client=FakeLlmResponder("llm answered: hello"),
    )

    result = agent.invoke("hello")

    assert result["state1"] == "step1 processed: hello"
    assert result["state2"] == "llm answered: hello"
    assert result["state3"] == "step3 processed: llm answered: hello"
    assert result["final_output"] == result["state3"]
    assert result["progress"] == [
        "step1 completed",
        "step2 completed",
        "step3 completed",
    ]


def test_agent_build_graph_returns_invokable_compiled_graph() -> None:
    """Verify the graph builder returns a compiled graph."""
    graph = BareLangGraphAgent.build_graph(
        create_default_steps(
            step_sleep_seconds=0,
            llm_client=FakeLlmResponder("graph llm answer"),
        )
    )

    result = graph.invoke({"input_text": "graph", "progress": []})

    assert result["final_output"] == "step3 processed: graph llm answer"


def test_agent_rejects_empty_input() -> None:
    """Verify empty input is rejected before graph execution."""
    agent = BareLangGraphAgent(step_sleep_seconds=0, llm_client=FakeLlmResponder())

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
    agent = BareLangGraphAgent(step_sleep_seconds=0, llm_client=FakeLlmResponder())

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
    agent = BareLangGraphAgent(
        step_sleep_seconds=0,
        llm_client=FakeLlmResponder("streamed llm answer"),
    )

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
    assert events[-1].state["state2"] == "streamed llm answer"
