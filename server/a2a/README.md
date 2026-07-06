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

The A2A server is intentionally split into three small files:

```text
src/oci_langgraph_a2a_blueprint/a2a_card.py
src/oci_langgraph_a2a_blueprint/a2a_executor.py
src/oci_langgraph_a2a_blueprint/a2a_server.py
```

`a2a_card.py` describes the agent to A2A clients. It builds the public Agent
Card with protocol version `1.0`, the HTTP+JSON interface, streaming capability,
text input/output modes, and the sample LangGraph skill.

`a2a_server.py` wires the A2A SDK to Starlette. It creates the Agent Card,
registers `LangGraphAgentExecutor` as the protocol adapter, uses the SDK
`DefaultRequestHandler`, and exposes only the Agent Card route plus the REST
streaming route.

```python
agent_card = create_agent_card(server_url=server_url)
request_handler = DefaultRequestHandler(
    agent_executor=LangGraphAgentExecutor(
        step_sleep_seconds=step_sleep_seconds,
    ),
    task_store=InMemoryTaskStore(),
    agent_card=agent_card,
)

routes = create_agent_card_routes(agent_card)
routes.extend(_streaming_only_routes(request_handler))
app = Starlette(routes=routes)
```

`a2a_executor.py` is the actual bridge between A2A and LangGraph. It implements
the SDK `AgentExecutor` interface. The executor reads user text from the A2A
request context, invokes the bare LangGraph agent streaming API, and maps each
internal event to A2A task events.

```python
agent = BareLangGraphAgent(step_sleep_seconds=self.step_sleep_seconds)
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

## Adapting This Server to Another LangGraph Agent

For another LangGraph agent, keep the A2A server structure and replace only the
agent-specific pieces.

Change `src/oci_langgraph_a2a_blueprint/a2a_executor.py` when:

* the bare agent class changes;
* the input extraction needs more than plain text;
* internal stream event names are different;
* final output is stored under a different state key;
* the agent should emit multiple artifacts instead of one final text artifact.

The smallest replacement is usually this line:

```python
agent = BareLangGraphAgent(step_sleep_seconds=self.step_sleep_seconds)
```

Replace it with your own agent class:

```python
agent = MyLangGraphAgent(...)
```

Then adapt the event mapping loop so it matches your agent's stream contract.
The recommended internal contract is still simple:

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

The local server supports these environment variables:

```text
A2A_SERVER_HOST              Bind host. Defaults to 0.0.0.0.
A2A_SERVER_PORT              Bind port. Defaults to 8000.
A2A_SERVER_PUBLIC_URL        Public URL advertised in the Agent Card.
AGENT_STEP_SLEEP_SECONDS     Simulated duration for each LangGraph step. Defaults to 1.0.
AGENT_LOG_LEVEL              Python logging level. Defaults to INFO.
```

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
