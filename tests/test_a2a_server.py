"""
Author: L. Saetta
Date last modified: 2026-07-07
License: MIT
Description: Unit tests for the A2A HTTP/SSE server wrapper.
Agent customization: Update when the A2A wrapper contract changes.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
import inspect
import json

from a2a import types as a2a_types
from starlette.testclient import TestClient

from oci_langgraph_a2a_blueprint.framework.a2a_contract import (
    A2A_PROTOCOL_VERSION,
    AgentProgressEvent,
    REST_PROTOCOL_BINDING,
)
from oci_langgraph_a2a_blueprint.agent.agent_adapter import (
    create_agent_adapter,
    load_agent_settings,
    create_agent_card,
    create_agent_factory,
)
from oci_langgraph_a2a_blueprint.framework.a2a_server import create_server
from oci_langgraph_a2a_blueprint.clients.a2a_stream_client import build_stream_request


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
            source="custom_step",
            message="custom step completed",
            state={
                "input_text": input_text,
                "progress": ["custom step completed"],
                "final_output": f"custom processed: {input_text}",
            },
        )
        yield AgentProgressEvent(
            event_type="data",
            source="custom_step",
            message="custom data emitted",
            data={"chunk": "intermediate"},
            state={
                "input_text": input_text,
                "progress": ["custom step completed", "custom data emitted"],
                "final_output": f"custom processed: {input_text}",
            },
        )
        yield AgentProgressEvent(
            event_type="agent_completed",
            source=None,
            message="custom agent completed",
            state={
                "input_text": input_text,
                "progress": ["custom step completed"],
                "final_output": f"custom processed: {input_text}",
            },
        )


class FakeLlmResponder:
    """Fake LLM responder used to avoid network calls in server tests."""

    def answer(self, input_text: str) -> str:
        """Return a deterministic answer for the original input."""
        return f"llm answered: {input_text}"


class FailingStreamingAgent:
    """Test streaming agent that raises an unexpected runtime failure."""

    async def stream(self, input_text: str) -> AsyncIterator[AgentProgressEvent]:
        """Raise while satisfying the streaming agent protocol."""
        if input_text:
            raise RuntimeError("provider rejected the request")
        yield AgentProgressEvent(
            event_type="agent_completed",
            source=None,
            message="unreachable",
            state={},
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
    app = create_server(
        agent_factory=create_agent_factory(0),
        agent_card=create_agent_card(),
    )

    assert [route.path for route in app.routes] == [
        "/.well-known/agent-card.json",
        "/message:stream",
    ]


def test_create_server_signature_has_only_server_concerns() -> None:
    """Verify reusable server creation does not expose sample-agent settings."""
    parameters = inspect.signature(create_server).parameters

    assert list(parameters) == ["agent_factory", "agent_card"]
    assert "step_sleep_seconds" not in parameters


def test_agent_adapter_contract_uses_generic_function_name() -> None:
    """Verify the server bootstrap can load the standard agent adapter."""
    parameters = inspect.signature(create_agent_adapter).parameters
    adapter = create_agent_adapter()
    agent_card = adapter.agent_card_factory("http://testserver")

    assert not list(parameters)
    assert agent_card.supported_interfaces[0].url == "http://testserver"
    assert callable(adapter.agent_factory)
    assert callable(adapter.agent_card_factory)


def test_agent_card_endpoint_returns_json() -> None:
    """Verify Agent Card discovery returns the expected public metadata."""
    app = create_server(
        agent_factory=create_agent_factory(0),
        agent_card=create_agent_card(server_url="http://testserver"),
    )

    with TestClient(app) as client:
        response = client.get("/.well-known/agent-card.json")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "OCI LangGraph A2A Blueprint Agent"
    assert body["capabilities"]["streaming"] is True
    assert body["supportedInterfaces"][0]["protocolVersion"] == "1.0"


def test_agent_card_endpoint_uses_request_public_url() -> None:
    """Verify Agent Card URLs work behind Hosted Application invoke paths."""
    app = create_server(
        agent_factory=create_agent_factory(0),
        agent_card=create_agent_card(server_url="http://placeholder"),
    )

    with TestClient(app) as client:
        response = client.get(
            "/.well-known/agent-card.json",
            headers={
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": (
                    "inference.generativeai.us-chicago-1.oci.oraclecloud.com"
                ),
                "X-Forwarded-Prefix": (
                    "/20251112/hostedApplications/ocid1.example/actions/invoke"
                ),
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["supportedInterfaces"][0]["url"] == (
        "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/"
        "20251112/hostedApplications/ocid1.example/actions/invoke"
    )


def test_message_stream_returns_sse_progress_and_completion() -> None:
    """Verify the A2A streaming endpoint emits progress and completion events."""
    app = create_server(
        agent_factory=create_agent_factory(0, llm_client=FakeLlmResponder()),
        agent_card=create_agent_card(server_url="http://testserver"),
    )
    payload = build_stream_request("hello", message_id="message-1")

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
    assert "step3 processed: llm answered: hello" in serialized_events
    assert "TASK_STATE_COMPLETED" in serialized_events


def test_message_stream_accepts_custom_agent_factory() -> None:
    """Verify the server can wrap another streaming agent via factory injection."""
    app = create_server(
        agent_factory=CustomStreamingAgent,
        agent_card=_custom_agent_card(),
    )
    payload = build_stream_request("hello", message_id="message-1")

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
    assert "custom data emitted" in serialized_events
    assert "langgraph_source" in serialized_events
    assert "custom processed: hello" in serialized_events
    assert "TASK_STATE_COMPLETED" in serialized_events


def test_message_stream_maps_unexpected_agent_errors_to_failed_task() -> None:
    """Verify provider failures do not crash the SSE stream as HTTP 500."""
    app = create_server(
        agent_factory=FailingStreamingAgent,
        agent_card=_custom_agent_card(),
    )
    payload = build_stream_request("hello", message_id="message-1")

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
    assert "TASK_STATE_FAILED" in serialized_events
    assert "Agent execution failed: provider rejected the request" in serialized_events


def test_sample_agent_settings_read_agent_sleep_value() -> None:
    """Verify sample-agent sleep configuration is owned by the agent plug point."""
    settings = load_agent_settings({"AGENT_STEP_SLEEP_SECONDS": "0.25"})

    assert settings.step_sleep_seconds == 0.25


def test_sample_agent_settings_reject_invalid_sleep_value() -> None:
    """Verify invalid sample-agent sleep values fail with a clear error."""
    try:
        load_agent_settings({"AGENT_STEP_SLEEP_SECONDS": "abc"})
    except ValueError as exc:
        assert str(exc) == "AGENT_STEP_SLEEP_SECONDS must be a float"
    else:  # pragma: no cover
        raise AssertionError("Expected invalid sleep value to raise ValueError")


def _custom_agent_card() -> a2a_types.AgentCard:
    """Create an Agent Card for the custom test agent.

    Returns:
        A2A Agent Card protobuf object.
    """
    return a2a_types.AgentCard(
        name="Custom Test Agent",
        description="Custom test streaming agent.",
        version="0.1.0",
        supported_interfaces=[
            a2a_types.AgentInterface(
                url="http://testserver",
                protocol_binding=REST_PROTOCOL_BINDING,
                protocol_version=A2A_PROTOCOL_VERSION,
            )
        ],
        capabilities=a2a_types.AgentCapabilities(streaming=True),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            a2a_types.AgentSkill(
                id="custom-test-skill",
                name="Custom test skill",
                description="Streams one custom step.",
                input_modes=["text/plain"],
                output_modes=["text/plain"],
            )
        ],
    )


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
