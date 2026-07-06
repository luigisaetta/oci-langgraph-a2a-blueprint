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
