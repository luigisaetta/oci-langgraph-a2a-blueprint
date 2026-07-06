# Local A2A Server

This README explains how to run the local A2A HTTP/SSE server for the sample
LangGraph agent.

The server exposes the bare three-step LangGraph agent through the A2A `1.0`
HTTP+JSON/REST streaming binding. It is intentionally small and focused on the
streaming path so it can be used as a blueprint for wrapping other LangGraph
agents.

## Exposed Endpoints

```text
GET  /.well-known/agent-card.json
POST /message:stream
```

The `POST /message:stream` endpoint returns Server-Sent Events with
`Content-Type: text/event-stream`.

## How the Wrapper Works

The A2A integration is intentionally split into four small files:

```text
src/oci_langgraph_a2a_blueprint/a2a_card.py
src/oci_langgraph_a2a_blueprint/a2a_executor.py
src/oci_langgraph_a2a_blueprint/a2a_server.py
src/oci_langgraph_a2a_blueprint/sample_a2a_server.py
```

`a2a_card.py` describes the agent to A2A clients. It builds the public Agent
Card with protocol version `1.0`, the HTTP+JSON interface, streaming capability,
text input/output modes, and the sample LangGraph skill.

`a2a_server.py` is the reusable A2A server wrapper. It wires the A2A SDK to
Starlette. It receives an `agent_factory`, creates the Agent Card, registers
`LangGraphAgentExecutor` as the protocol adapter, uses the SDK
`DefaultRequestHandler`, and exposes only the Agent Card route plus the REST
streaming route.

It does not know about the sample agent's sleep setting, local environment
variables, or `uvicorn`.

```python
def create_server(
    agent_factory: AgentFactory,
    server_url: str = DEFAULT_SERVER_URL,
    agent_card: a2a_types.AgentCard | None = None,
) -> Starlette:
    resolved_agent_card = agent_card or create_agent_card(server_url=server_url)
    request_handler = DefaultRequestHandler(
        agent_executor=LangGraphAgentExecutor(agent_factory=agent_factory),
        task_store=InMemoryTaskStore(),
        agent_card=resolved_agent_card,
    )

    routes = create_agent_card_routes(resolved_agent_card)
    routes.extend(_streaming_only_routes(request_handler))
    return Starlette(routes=routes)
```

`sample_a2a_server.py` is only the local sample entry point behind the
`a2a-langgraph-server` command. It reads local settings, creates the sample agent
factory, and then calls the generic `create_server()`.

```python
settings = load_a2a_server_settings()
agent_factory = create_default_agent_factory(settings.step_sleep_seconds)

uvicorn.run(
    create_server(
        agent_factory=agent_factory,
        server_url=settings.public_url,
    ),
    host=settings.host,
    port=settings.port,
)
```

`a2a_executor.py` is the actual bridge between A2A and LangGraph. It implements
the SDK `AgentExecutor` interface. The executor reads user text from the A2A
request context, invokes the bare LangGraph agent streaming API, and maps each
internal event to A2A task events.

```python
agent = self.agent_factory()
async for event in agent.stream(context.get_user_input()):
    if event.event_type == "step_completed":
        await updater.update_status(
            a2a_types.TaskState.TASK_STATE_WORKING,
            message=self._new_agent_message(updater, event.message),
            metadata={
                "langgraph_event_type": event.event_type,
                "langgraph_step_name": event.step_name,
            },
        )
    elif event.event_type == "agent_completed":
        final_output = event.state.get("final_output", "")
```

When the graph completes, the executor sends the final LangGraph output as an
A2A artifact and marks the task as completed:

```python
await updater.add_artifact(
    parts=[a2a_types.Part(text=final_output)],
    name="final_output",
    last_chunk=True,
    metadata={"artifact_type": "final_output"},
)
await updater.complete(
    self._new_agent_message(updater, "LangGraph workflow completed.")
)
```

The first event is an explicit A2A `Task` with `TASK_STATE_SUBMITTED`. The A2A
SDK requires task-mode streams to start with a `Task` before status or artifact
updates are emitted.

The reusable server wrapper depends on an `agent_factory`, not on sample-agent
settings. The default command-line entry point lives in `sample_a2a_server.py`
and reads `AGENT_STEP_SLEEP_SECONDS` only to build the sample agent factory
before the server is created.

## Adapting This Server to Another LangGraph Agent

For another LangGraph agent, keep the A2A server structure and replace only the
agent-specific pieces. The main extension point is `agent_factory`.

Your custom agent should provide this minimal stream method:

```python
class MyLangGraphAgent:
    async def stream(self, input_text: str):
        yield AgentProgressEvent(
            event_type="step_completed",
            step_name="my_node",
            message="my_node completed",
            state={"final_output": "partial or final value"},
        )
        yield AgentProgressEvent(
            event_type="agent_completed",
            step_name=None,
            message="agent completed",
            state={"final_output": "final response text"},
        )
```

Then pass a factory to the server app:

```python
from oci_langgraph_a2a_blueprint.a2a_server import create_server


def create_my_agent():
    return MyLangGraphAgent(...)


app = create_server(
    agent_factory=create_my_agent,
    server_url="http://localhost:8000",
)
```

Change `src/oci_langgraph_a2a_blueprint/a2a_executor.py` when:

* the input extraction needs more than plain text;
* internal stream event names are different;
* final output is stored under a different state key;
* the agent should emit multiple artifacts instead of one final text artifact.

If your custom agent follows the same event contract and keeps final output in
`state["final_output"]`, you should not need to modify the executor. The
recommended internal contract is intentionally small:

```python
async for event in agent.stream(input_text):
    ...
```

Each streamed event should include enough information to map it to A2A:

```text
event_type
message
step_name or node_name
state snapshot or output fragment
```

Change `src/oci_langgraph_a2a_blueprint/a2a_card.py` when:

* the agent name changes;
* the public description changes;
* skills, tags, examples, or input/output modes change;
* the server supports more capabilities.

Change `src/oci_langgraph_a2a_blueprint/a2a_server.py` only when:

* more A2A routes must be exposed;
* task storage should move from `InMemoryTaskStore` to a durable store;
* authentication, tenancy, or deployment-specific middleware is introduced;
* multiple executors or multiple agent cards are needed.

For a custom Agent Card, pass `agent_card` to `create_server()` or change
`src/oci_langgraph_a2a_blueprint/a2a_card.py`:

```python
app = create_server(
    agent_factory=create_my_agent,
    agent_card=my_agent_card,
)
```

For most blueprint adaptations, the stable boundary is:

```text
A2A client
  -> POST /message:stream
  -> A2A SDK DefaultRequestHandler
  -> LangGraphAgentExecutor.execute()
  -> your LangGraph agent.stream()
  -> A2A TaskStatusUpdateEvent / TaskArtifactUpdateEvent
  -> SSE response
```

## Setup

Run commands from the repository root.

Activate the Conda environment:

```bash
conda activate oci-langgraph-a2a-blueprint
```

Install the project package in editable mode:

```bash
python -m pip install --no-deps -e .
```

This makes the `a2a-langgraph-server` command available in the environment and
keeps local source changes immediately visible without reinstalling dependencies.

## Start the Server

For a fast local demo, disable the simulated step delay:

```bash
AGENT_STEP_SLEEP_SECONDS=0 a2a-langgraph-server
```

The server listens on `0.0.0.0:8000` by default and advertises
`http://localhost:8000` in the Agent Card.

## Configuration

The local sample runner supports these environment variables:

```text
A2A_SERVER_HOST              Bind host. Defaults to 0.0.0.0.
A2A_SERVER_PORT              Bind port. Defaults to 8000.
A2A_SERVER_PUBLIC_URL        Public URL advertised in the Agent Card.
AGENT_STEP_SLEEP_SECONDS     Simulated duration for each sample LangGraph step. Defaults to 1.0.
AGENT_LOG_LEVEL              Python logging level. Defaults to INFO.
```

These variables are consumed by `sample_a2a_server.py`, not by the reusable
`a2a_server.py` wrapper.

Example with a custom port:

```bash
A2A_SERVER_PORT=8123 \
A2A_SERVER_PUBLIC_URL=http://localhost:8123 \
AGENT_STEP_SLEEP_SECONDS=0 \
a2a-langgraph-server
```

## Read the Agent Card

```bash
curl -s http://localhost:8000/.well-known/agent-card.json
```

The response includes the A2A protocol version, supported interface, streaming
capability, input/output modes, and the sample LangGraph skill.

## Send a Streaming Request

```bash
curl -N \
  -H "Content-Type: application/a2a+json" \
  -H "A2A-Version: 1.0" \
  -d '{"message":{"messageId":"message-1","role":"ROLE_USER","parts":[{"text":"hello"}]},"configuration":{"acceptedOutputModes":["text/plain"]}}' \
  http://localhost:8000/message:stream
```

The stream emits:

```text
Task with TASK_STATE_SUBMITTED
TASK_STATE_WORKING update: LangGraph workflow started.
TASK_STATE_WORKING update: step1 completed
TASK_STATE_WORKING update: step2 completed
TASK_STATE_WORKING update: step3 completed
Artifact update: final_output
TASK_STATE_COMPLETED
```

The final artifact contains:

```text
step3 processed: step2 processed: step1 processed: hello
```

## Stop the Server

Press `Ctrl+C` in the terminal where the server is running.
