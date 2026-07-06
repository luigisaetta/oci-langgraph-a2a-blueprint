"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: Command-line client for A2A HTTP/SSE streaming execution.
Agent customization: Do not modify unless the client protocol usage changes.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import httpx
from httpx_sse import SSEError, connect_sse

A2A_PROTOCOL_VERSION = "1.0"
DEFAULT_A2A_CLIENT_SERVER_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class A2AStreamClientSettings:
    """Settings for one A2A streaming client run.

    Attributes:
        server_url: A2A server base URL.
        message_id: Optional caller-provided message identifier.
        timeout: HTTP timeout in seconds.
        show_raw: Whether to print raw decoded JSON events.
    """

    server_url: str = DEFAULT_A2A_CLIENT_SERVER_URL
    message_id: str | None = None
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    show_raw: bool = False


def build_parser() -> argparse.ArgumentParser:
    """Build the A2A streaming client argument parser.

    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Call an A2A server and stream task progress over SSE.",
    )
    parser.add_argument(
        "input_text",
        help="Text input sent to the A2A agent.",
    )
    parser.add_argument(
        "--server-url",
        default=DEFAULT_A2A_CLIENT_SERVER_URL,
        help=f"A2A server base URL. Defaults to {DEFAULT_A2A_CLIENT_SERVER_URL}.",
    )
    parser.add_argument(
        "--message-id",
        default=None,
        help="A2A message identifier. Defaults to a generated UUID.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"HTTP timeout in seconds. Defaults to {DEFAULT_TIMEOUT_SECONDS}.",
    )
    parser.add_argument(
        "--show-raw",
        action="store_true",
        help="Print raw decoded SSE JSON payloads.",
    )
    return parser


def build_stream_request(input_text: str, message_id: str | None = None) -> dict:
    """Build the A2A `message:stream` request body.

    Args:
        input_text: Text input sent to the agent.
        message_id: Optional caller-provided message identifier.

    Returns:
        JSON-serializable A2A request payload.
    """
    return {
        "message": {
            "messageId": message_id or str(uuid4()),
            "role": "ROLE_USER",
            "parts": [{"text": input_text}],
        },
        "configuration": {"acceptedOutputModes": ["text/plain"]},
    }


def format_stream_event(event: dict[str, Any]) -> str:
    """Format one decoded A2A stream event for console output.

    Args:
        event: Decoded JSON event payload from the SSE stream.

    Returns:
        Human-readable event line.
    """
    if "task" in event:
        state = event["task"].get("status", {}).get("state", "UNKNOWN")
        return f"task: {state}"

    if "statusUpdate" in event:
        status = event["statusUpdate"].get("status", {})
        state = status.get("state", "UNKNOWN")
        text = _message_text(status.get("message", {}))
        if text:
            return f"status: {state} - {text}"
        return f"status: {state}"

    if "artifactUpdate" in event:
        artifact = event["artifactUpdate"].get("artifact", {})
        name = artifact.get("name", "artifact")
        text = _parts_text(artifact.get("parts", []))
        if text:
            return f"artifact: {name} - {text}"
        return f"artifact: {name}"

    return f"event: {json.dumps(event, sort_keys=True)}"


def run_client(
    input_text: str,
    settings: A2AStreamClientSettings | None = None,
    http_client: httpx.Client | None = None,
) -> int:
    """Run the A2A streaming client.

    Args:
        input_text: Text input sent to the A2A agent.
        settings: Optional client settings.
        http_client: Optional client used by tests.

    Returns:
        Process-style exit code.
    """
    resolved_settings = settings or A2AStreamClientSettings()
    request = build_stream_request(
        input_text=input_text,
        message_id=resolved_settings.message_id,
    )
    owns_client = http_client is None
    client = http_client or httpx.Client(timeout=resolved_settings.timeout)

    try:
        with connect_sse(
            client,
            "POST",
            _message_stream_url(resolved_settings.server_url),
            json=request,
            headers={
                "Accept": "text/event-stream",
                "Content-Type": "application/a2a+json",
                "A2A-Version": A2A_PROTOCOL_VERSION,
            },
        ) as event_source:
            for sse in event_source.iter_sse():
                event = json.loads(sse.data)
                if resolved_settings.show_raw:
                    print(f"raw: {json.dumps(event, sort_keys=True)}")
                print(format_stream_event(event))
    except (httpx.HTTPError, SSEError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        if owns_client:
            client.close()

    return 0


def main() -> int:
    """Run the A2A streaming command-line client.

    Returns:
        Process-style exit code.
    """
    parser = build_parser()
    args = parser.parse_args()

    return run_client(
        input_text=args.input_text,
        settings=A2AStreamClientSettings(
            server_url=args.server_url,
            message_id=args.message_id,
            timeout=args.timeout,
            show_raw=args.show_raw,
        ),
    )


def _message_stream_url(server_url: str) -> str:
    """Build the A2A streaming endpoint URL.

    Args:
        server_url: A2A server base URL.

    Returns:
        Full `message:stream` endpoint URL.
    """
    return f"{server_url.rstrip('/')}/message:stream"


def _message_text(message: dict[str, Any]) -> str:
    """Extract text from an A2A message object.

    Args:
        message: Decoded A2A message.

    Returns:
        Combined text parts.
    """
    return _parts_text(message.get("parts", []))


def _parts_text(parts: list[dict[str, Any]]) -> str:
    """Extract text from A2A parts.

    Args:
        parts: Decoded A2A parts.

    Returns:
        Combined text values.
    """
    return " ".join(part["text"] for part in parts if "text" in part)


if __name__ == "__main__":
    raise SystemExit(main())
