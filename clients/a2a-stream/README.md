# A2A Streaming CLI Client

This client calls an A2A server over HTTP and consumes Server-Sent Events from
`POST /message:stream`.

Use this client when you want to test the public A2A protocol boundary. For
direct in-process agent execution, use the direct agent client instead.

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

## Start the A2A Server

In one terminal:

```bash
AGENT_STEP_SLEEP_SECONDS=0 a2a-langgraph-server
```

The server listens on `http://localhost:8080` by default.

## Run the Client

In another terminal:

```bash
a2a-stream-client "hello from A2A"
```

The client can also run as a Python module:

```bash
python -m oci_langgraph_a2a_blueprint.clients.a2a_stream_client "hello from A2A"
```

## Expected Output Shape

```text
task: TASK_STATE_SUBMITTED
status: TASK_STATE_WORKING - LangGraph workflow started.
status: TASK_STATE_WORKING - step1 completed
status: TASK_STATE_WORKING - step2 completed
status: TASK_STATE_WORKING - step3 completed
artifact: final_output - step3 processed: step2 processed: step1 processed: hello from A2A
status: TASK_STATE_COMPLETED - LangGraph workflow completed.
```

## Options

```text
input_text            Text input sent to the A2A agent.
--server-url URL      A2A server base URL. Defaults to http://localhost:8080.
--message-id VALUE    Message identifier. Defaults to a generated UUID.
--timeout SECONDS     HTTP timeout. Defaults to 30.0.
--show-raw            Print raw decoded SSE JSON payloads.
```

Example with a custom server URL:

```bash
a2a-stream-client "hello" --server-url http://localhost:8123
```
