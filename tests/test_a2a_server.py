"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: Unit tests for the A2A HTTP/SSE server wrapper.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
import json

from starlette.testclient import TestClient

from oci_langgraph_a2a_blueprint.a2a_card import (
    A2A_PROTOCOL_VERSION,
    REST_PROTOCOL_BINDING,
    create_agent_card,
)
from oci_langgraph_a2a_blueprint.a2a_server import create_app
from oci_langgraph_a2a_blueprint.state import AgentProgressEvent


class CustomStreamingAgent:
    """Test streaming agent used to verify server reuse."""

    async def stream(self, input_text: str) -> AsyncIterator[AgentProgressEvent]:
        """Stream custom progress and final output events.

        Args:
            input_text: User input extracted from the A2A request.

        Yields:
            Progress and completion events using the server stream contract.
        """
        yield AgentProgressEvent(
            event_type="step_completed",
            step_name="custom_step",
            message="custom step completed",
            state={
                "input_text": input_text,
                "progress": ["custom step completed"],
                "final_output": f"custom processed: {input_text}",
            },
        )
        yield AgentProgressEvent(
            event_type="agent_completed",
            step_name=None,
            message="custom agent completed",
            state={
                "input_text": input_text,
                "progress": ["custom step completed"],
                "final_output": f"custom processed: {input_text}",
            },
        )


def test_agent_card_declares_a2a_1_streaming() -> None:
    """Verify the public Agent Card declares A2A 1.0 streaming support."""
    card = create_agent_card(server_url="http://testserver")

    assert card.name == "OCI LangGraph A2A Blueprint Agent"
    assert card.capabilities.streaming is True
    assert card.capabilities.push_notifications is False
    assert card.default_input_modes == ["text/plain"]
    assert card.default_output_modes == ["text/plain"]
    assert card.supported_interfaces[0].url == "http://testserver"
    assert card.supported_interfaces[0].protocol_binding == REST_PROTOCOL_BINDING
    assert card.supported_interfaces[0].protocol_version == A2A_PROTOCOL_VERSION
    assert card.skills[0].id == "three-step-langgraph-workflow"


def test_app_exposes_only_agent_card_and_streaming_route() -> None:
    """Verify the first server keeps the public A2A route surface small."""
    app = create_app(step_sleep_seconds=0)

    assert [route.path for route in app.routes] == [
        "/.well-known/agent-card.json",
        "/message:stream",
    ]


def test_agent_card_endpoint_returns_json() -> None:
    """Verify Agent Card discovery returns the expected public metadata."""
    app = create_app(server_url="http://testserver", step_sleep_seconds=0)

    with TestClient(app) as client:
        response = client.get("/.well-known/agent-card.json")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "OCI LangGraph A2A Blueprint Agent"
    assert body["capabilities"]["streaming"] is True
    assert body["supportedInterfaces"][0]["protocolVersion"] == "1.0"


def test_message_stream_returns_sse_progress_and_completion() -> None:
    """Verify the A2A streaming endpoint emits progress and completion events."""
    app = create_app(server_url="http://testserver", step_sleep_seconds=0)
    payload = {
        "message": {
            "messageId": "message-1",
            "role": "ROLE_USER",
            "parts": [{"text": "hello"}],
        },
        "configuration": {"acceptedOutputModes": ["text/plain"]},
    }

    with TestClient(app) as client:
        with client.stream(
            "POST",
            "/message:stream",
            json=payload,
            headers={"A2A-Version": "1.0"},
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            events = _read_sse_events(response.iter_lines())

    serialized_events = json.dumps(events)
    assert "step1 completed" in serialized_events
    assert "step2 completed" in serialized_events
    assert "step3 completed" in serialized_events
    assert "step3 processed: step2 processed: step1 processed: hello" in (
        serialized_events
    )
    assert "TASK_STATE_COMPLETED" in serialized_events


def test_message_stream_accepts_custom_agent_factory() -> None:
    """Verify the server can wrap another streaming agent via factory injection."""
    app = create_app(
        server_url="http://testserver",
        agent_factory=CustomStreamingAgent,
    )
    payload = {
        "message": {
            "messageId": "message-1",
            "role": "ROLE_USER",
            "parts": [{"text": "hello"}],
        },
        "configuration": {"acceptedOutputModes": ["text/plain"]},
    }

    with TestClient(app) as client:
        with client.stream(
            "POST",
            "/message:stream",
            json=payload,
            headers={"A2A-Version": "1.0"},
        ) as response:
            assert response.status_code == 200
            events = _read_sse_events(response.iter_lines())

    serialized_events = json.dumps(events)
    assert "custom step completed" in serialized_events
    assert "custom processed: hello" in serialized_events
    assert "TASK_STATE_COMPLETED" in serialized_events


def _read_sse_events(lines: list[str]) -> list[dict]:
    """Read JSON payloads from SSE data lines.

    Args:
        lines: SSE response lines.

    Returns:
        Decoded JSON event payloads.
    """
    events = []
    for line in lines:
        if line.startswith("data: "):
            events.append(json.loads(line.removeprefix("data: ")))
    return events
