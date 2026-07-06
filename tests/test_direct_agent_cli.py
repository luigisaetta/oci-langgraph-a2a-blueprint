"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: Unit tests for the direct bare-agent command-line client.
"""

from __future__ import annotations

import pytest

from oci_langgraph_a2a_blueprint import AgentProgressEvent
from oci_langgraph_a2a_blueprint.clients.direct_agent_cli import (
    format_event,
    run_client,
)


def test_format_event_with_step_name() -> None:
    """Verify formatting for a step progress event."""
    event = AgentProgressEvent(
        event_type="step_completed",
        step_name="step1",
        message="step1 completed",
        state={"input_text": "hello", "progress": ["step1 completed"]},
    )

    assert format_event(event) == "step_completed: step1 - step1 completed"


def test_format_event_without_step_name() -> None:
    """Verify formatting for a final agent event."""
    event = AgentProgressEvent(
        event_type="agent_completed",
        step_name=None,
        message="agent completed",
        state={"input_text": "hello", "progress": []},
    )

    assert format_event(event) == "agent_completed: agent completed"


@pytest.mark.asyncio
async def test_run_client_streams_agent_events(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify the direct client prints streaming progress and final output."""
    exit_code = await run_client(
        input_text="hello",
        sleep_seconds=0,
        show_state=False,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "step_completed: step1 - step1 completed" in captured.out
    assert "step_completed: step2 - step2 completed" in captured.out
    assert "step_completed: step3 - step3 completed" in captured.out
    assert "agent_completed: agent completed" in captured.out
    assert "Final output: step3 processed:" in captured.out
    assert captured.err == ""


@pytest.mark.asyncio
async def test_run_client_reports_value_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify the direct client returns an error code for invalid input."""
    exit_code = await run_client(
        input_text=" ",
        sleep_seconds=0,
        show_state=False,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "input_text must not be empty" in captured.err
