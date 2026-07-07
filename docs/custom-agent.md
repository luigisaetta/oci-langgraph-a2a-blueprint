# How to Plug Your Own LangGraph Agent

This guide shows the smallest practical path for replacing the sample
LangGraph agent with your own agent while keeping the reusable A2A framework in
place.

The stable boundary is:

```text
A2A client
  -> framework/a2a_server.py
  -> framework/a2a_executor.py
  -> agent/agent_adapter.py
  -> your agent.stream(input_text)
```

For most custom agents, only files under
`src/oci_langgraph_a2a_blueprint/agent/` should change.

## Package Layout

Reusable A2A framework files live here:

```text
src/oci_langgraph_a2a_blueprint/framework/
```

Replaceable agent files live here:

```text
src/oci_langgraph_a2a_blueprint/agent/
```

The framework expects the agent package to expose an adapter through
`create_agent_adapter()` in `agent/agent_adapter.py`.

## Custom State

Define the state your LangGraph workflow needs. Keep a `final_output` field if
you want to reuse the existing A2A executor without changes.

```python
from typing import TypedDict


class CustomAgentState(TypedDict, total=False):
    """State shared by the custom LangGraph workflow."""

    user_input: str
    retrieved_context: str
    answer: str
    final_output: str
```

## Custom Graph

Build a LangGraph graph that reads and writes your custom state. The example
below keeps two simple nodes so the shape is easy to see.

```python
from langgraph.graph import END, START, StateGraph


def retrieve_context(state: CustomAgentState) -> CustomAgentState:
    """Retrieve or compute context for the user input."""

    user_input = state["user_input"]
    return {
        **state,
        "retrieved_context": f"context for: {user_input}",
    }


def generate_answer(state: CustomAgentState) -> CustomAgentState:
    """Generate the final answer from the state."""

    answer = f"answer using {state['retrieved_context']}"
    return {
        **state,
        "answer": answer,
        "final_output": answer,
    }


def build_custom_graph():
    """Build and compile the custom LangGraph workflow."""

    graph = StateGraph(CustomAgentState)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("generate_answer", generate_answer)
    graph.add_edge(START, "retrieve_context")
    graph.add_edge("retrieve_context", "generate_answer")
    graph.add_edge("generate_answer", END)
    return graph.compile()
```

## Custom stream()

The A2A executor calls `agent.stream(input_text)` and expects
`AgentProgressEvent` objects. The event contract lives in
`framework/a2a_contract.py`.

```python
from collections.abc import AsyncIterator

from oci_langgraph_a2a_blueprint.framework.a2a_contract import AgentProgressEvent


class CustomLangGraphAgent:
    """Custom agent exposed through the A2A framework."""

    def __init__(self) -> None:
        """Initialize the custom agent graph."""

        self.graph = build_custom_graph()

    async def stream(self, input_text: str) -> AsyncIterator[AgentProgressEvent]:
        """Run the graph and emit framework-compatible progress events.

        Args:
            input_text: Plain text extracted from the A2A request.

        Yields:
            AgentProgressEvent objects consumed by the A2A executor.
        """

        yield AgentProgressEvent(
            event_type="step_completed",
            source="request_received",
            message="Custom agent received the request.",
            state={"user_input": input_text},
        )

        result = await self.graph.ainvoke({"user_input": input_text})

        yield AgentProgressEvent(
            event_type="data",
            source="generate_answer",
            message="Custom agent generated an answer.",
            data={"answer": result["answer"]},
            state=result,
        )

        yield AgentProgressEvent(
            event_type="agent_completed",
            source="custom_agent",
            message="Custom agent completed.",
            state=result,
        )
```

The existing framework maps:

* `step_completed` and `data` to A2A working status updates;
* `agent_completed` to the final A2A artifact and completed task status.

The default executor reads the final response from `state["final_output"]`.

## Custom Agent Card

Edit `src/oci_langgraph_a2a_blueprint/agent/agent_adapter.py` so it returns
your custom agent factory and Agent Card factory.

```python
from a2a import types as a2a_types

from oci_langgraph_a2a_blueprint.framework.a2a_contract import (
    A2A_PROTOCOL_VERSION,
    REST_PROTOCOL_BINDING,
    AgentAdapter,
)
from oci_langgraph_a2a_blueprint.framework.a2a_server_config import (
    DEFAULT_SERVER_URL,
)


def create_custom_agent() -> CustomLangGraphAgent:
    """Create one custom agent instance for a request execution."""

    return CustomLangGraphAgent()


def create_agent_card(
    server_url: str = DEFAULT_SERVER_URL,
) -> a2a_types.AgentCard:
    """Create the public Agent Card for the custom agent."""

    return a2a_types.AgentCard(
        name="Custom LangGraph Agent",
        description="Custom LangGraph agent exposed through A2A.",
        version="0.1.0",
        supported_interfaces=[
            a2a_types.AgentInterface(
                url=server_url,
                protocol_binding=REST_PROTOCOL_BINDING,
                protocol_version=A2A_PROTOCOL_VERSION,
            )
        ],
        provider=a2a_types.AgentProvider(
            organization="Your Organization",
            url="https://example.com/",
        ),
        capabilities=a2a_types.AgentCapabilities(streaming=True),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            a2a_types.AgentSkill(
                id="custom_langgraph_skill",
                name="Custom LangGraph Skill",
                description="Runs the custom LangGraph workflow.",
                tags=["langgraph", "a2a"],
                examples=["Run the custom workflow for this input text."],
                input_modes=["text/plain"],
                output_modes=["text/plain"],
            )
        ],
    )


def create_agent_adapter() -> AgentAdapter:
    """Create the adapter consumed by the reusable A2A server entry point."""

    return AgentAdapter(
        agent_factory=create_custom_agent,
        agent_card_factory=create_agent_card,
    )
```

Keep the function name `create_agent_adapter()`. The server entry point imports
that function as the stable plug point.

## What Not to Touch in the Framework

Do not change files under `src/oci_langgraph_a2a_blueprint/framework/` when your
agent can follow the existing stream contract.

In particular, leave these files unchanged for normal agent replacement:

* `framework/a2a_contract.py`;
* `framework/a2a_executor.py`;
* `framework/a2a_server.py`;
* `framework/a2a_server_config.py`.

Change framework code only when the public A2A behavior changes, such as:

* input extraction needs more than plain text;
* stream events must map to different A2A task states;
* final output is not available as `state["final_output"]`;
* the server must expose additional A2A routes;
* task storage, authentication, or deployment middleware changes.

## Test with a2a-stream-client

Install the project in editable mode from the repository root:

```bash
conda activate oci-langgraph-a2a-blueprint
python -m pip install --no-deps -e .
```

Start the local A2A server:

```bash
a2a-langgraph-server
```

In another terminal, call your custom agent through the public A2A boundary:

```bash
a2a-stream-client "hello custom agent"
```

For a non-default server URL:

```bash
a2a-stream-client \
  "hello custom agent" \
  --server-url http://localhost:8123
```

The stream should show:

```text
Task submitted
Working status updates from your AgentProgressEvent objects
Final artifact containing state["final_output"]
Task completed
```

Run the project checks after replacing the agent:

```bash
black --check .
pylint src tests
pytest --cov=oci_langgraph_a2a_blueprint --cov-report=term-missing
```
