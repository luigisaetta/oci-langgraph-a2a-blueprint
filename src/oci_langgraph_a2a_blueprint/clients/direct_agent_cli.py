"""
Author: L. Saetta
Date last modified: 2026-07-07
License: MIT
Description: Command-line client that invokes the bare LangGraph agent directly.
Agent customization: Modify only if the direct sample-agent demo changes.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from oci_langgraph_a2a_blueprint import AgentProgressEvent, BareLangGraphAgent


def build_parser() -> argparse.ArgumentParser:
    """Build the direct agent client argument parser.

    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Invoke the bare LangGraph agent directly and stream progress.",
    )
    parser.add_argument(
        "input_text",
        help="Text input passed to the bare LangGraph agent.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=1.0,
        help="Simulated work duration for each step. Defaults to 1.0.",
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Python logging level. Defaults to WARNING.",
    )
    parser.add_argument(
        "--show-state",
        action="store_true",
        help="Print the current state snapshot after each streamed event.",
    )
    return parser


def format_event(event: AgentProgressEvent) -> str:
    """Format one progress event for console output.

    Args:
        event: Progress event emitted by the bare agent.

    Returns:
        Human-readable event line.
    """
    if event.source:
        return f"{event.event_type}: {event.source} - {event.message}"

    return f"{event.event_type}: {event.message}"


async def run_client(
    input_text: str,
    sleep_seconds: float,
    show_state: bool = False,
) -> int:
    """Run the direct client.

    Args:
        input_text: Text input passed to the bare agent.
        sleep_seconds: Simulated work duration for each step.
        show_state: Whether to print full state snapshots while streaming.

    Returns:
        Process-style exit code.
    """
    try:
        agent = BareLangGraphAgent(step_sleep_seconds=sleep_seconds)

        final_output = ""
        async for event in agent.stream(input_text):
            print(format_event(event))
            if show_state:
                print(f"state: {event.state}")
            final_output = event.state.get("final_output", final_output)

        print(f"Final output: {final_output}")
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


def main() -> int:
    """Run the command-line client.

    Returns:
        Process-style exit code.
    """
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level))

    return asyncio.run(
        run_client(
            input_text=args.input_text,
            sleep_seconds=args.sleep_seconds,
            show_state=args.show_state,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
