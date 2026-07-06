"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: Unit tests for the A2A HTTP/SSE command-line client.
"""

from __future__ import annotations

import json

import httpx

from oci_langgraph_a2a_blueprint.clients.a2a_stream_client import (
    A2AStreamClientSettings,
    build_stream_request,
    format_stream_event,
    run_client,
)


def test_build_stream_request_uses_text_input_and_message_id() -> None:
    """Verify A2A stream request payload construction."""
    request = build_stream_request("hello", message_id="message-1")

    assert request == {
        "message": {
            "messageId": "message-1",
            "role": "ROLE_USER",
            "parts": [{"text": "hello"}],
        },
        "configuration": {"acceptedOutputModes": ["text/plain"]},
    }


def test_format_stream_event_for_task() -> None:
    """Verify formatting for an initial task event."""
    event = {"task": {"status": {"state": "TASK_STATE_SUBMITTED"}}}

    assert format_stream_event(event) == "task: TASK_STATE_SUBMITTED"


def test_format_stream_event_for_status_update() -> None:
    """Verify formatting for an A2A status update event."""
    event = {
        "statusUpdate": {
            "status": {
                "state": "TASK_STATE_WORKING",
                "message": {"parts": [{"text": "step1 completed"}]},
            }
        }
    }

    assert format_stream_event(event) == "status: TASK_STATE_WORKING - step1 completed"


def test_format_stream_event_for_artifact_update() -> None:
    """Verify formatting for an A2A artifact update event."""
    event = {
        "artifactUpdate": {
            "artifact": {
                "name": "final_output",
                "parts": [{"text": "done"}],
            }
        }
    }

    assert format_stream_event(event) == "artifact: final_output - done"


def test_run_client_streams_mocked_sse_response(
    capsys,
) -> None:
    """Verify the client sends the A2A request and prints streamed events."""
    captured_request = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["method"] = request.method
        captured_request["url"] = str(request.url)
        captured_request["a2a_version"] = request.headers["A2A-Version"]
        captured_request["body"] = json.loads(request.content)

        return httpx.Response(
            status_code=200,
            headers={"content-type": "text/event-stream"},
            content=_sse_body(
                [
                    {"task": {"status": {"state": "TASK_STATE_SUBMITTED"}}},
                    {
                        "statusUpdate": {
                            "status": {
                                "state": "TASK_STATE_WORKING",
                                "message": {
                                    "parts": [{"text": "step1 completed"}],
                                },
                            }
                        }
                    },
                    {
                        "artifactUpdate": {
                            "artifact": {
                                "name": "final_output",
                                "parts": [{"text": "done"}],
                            }
                        }
                    },
                ]
            ),
            request=request,
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))

    exit_code = run_client(
        input_text="hello",
        settings=A2AStreamClientSettings(
            server_url="http://testserver",
            message_id="message-1",
        ),
        http_client=client,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured_request["method"] == "POST"
    assert captured_request["url"] == "http://testserver/message:stream"
    assert captured_request["a2a_version"] == "1.0"
    assert captured_request["body"]["message"]["parts"] == [{"text": "hello"}]
    assert "task: TASK_STATE_SUBMITTED" in captured.out
    assert "status: TASK_STATE_WORKING - step1 completed" in captured.out
    assert "artifact: final_output - done" in captured.out
    assert captured.err == ""


def _sse_body(events: list[dict]) -> str:
    """Build a text/event-stream body from JSON events.

    Args:
        events: Events to encode as SSE data lines.

    Returns:
        SSE response body.
    """
    return "".join(f"data: {json.dumps(event)}\n\n" for event in events)
