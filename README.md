# OCI LangGraph A2A Blueprint

![Black](https://img.shields.io/badge/code%20style-black-000000.svg)
![Pylint](https://img.shields.io/badge/lint-pylint-yellowgreen.svg)
![Pytest](https://img.shields.io/badge/tests-pytest-blue.svg)
![A2A](https://img.shields.io/badge/A2A-1.0%20compatible-brightgreen.svg)

Build a production-oriented LangGraph agent, package it as an A2A-compatible server, and deploy it on Oracle Cloud Infrastructure.

This repository is a blueprint for teams that want to move from an agent prototype to a cloud-ready service with a clear protocol boundary. The goal is not only to run a LangGraph workflow, but to expose it through a standard A2A server interface so that other agents, applications, and orchestration layers can discover it, call it, and reason about its task lifecycle.

The blueprint will show how to connect the key pieces:

- a LangGraph agent with explicit state, nodes, tools, and model configuration;
- an A2A-compatible API layer with agent card metadata, request validation, task handling, and structured responses;
- OCI-ready runtime configuration, deployment assets, and operational guidance;
- tests and specifications that make the behavior understandable, repeatable, and safe to evolve.

## Current Implementation

The repository currently includes the first bare LangGraph agent implementation and the first A2A HTTP/SSE wrapper.

The bare agent executes three sequential LangChain `Runnable` steps, shares state across the graph, logs the start and completion of each step, and exposes both synchronous invocation and asynchronous streaming progress events.

```python
from oci_langgraph_a2a_blueprint import BareLangGraphAgent

agent = BareLangGraphAgent(step_sleep_seconds=0)
result = agent.invoke("hello")
print(result["final_output"])
```

The A2A server exposes:

- `GET /.well-known/agent-card.json`
- `POST /message:stream`

It intentionally focuses on the A2A 1.0 HTTP+JSON/REST streaming path with Server-Sent Events.
See [server/a2a/README.md](server/a2a/README.md) for detailed local run instructions.

Start the local server:

```bash
conda activate oci-langgraph-a2a-blueprint
python -m pip install --no-deps -e .
AGENT_STEP_SLEEP_SECONDS=0 a2a-langgraph-server
```

Send a streaming request:

```bash
curl -N \
  -H "Content-Type: application/a2a+json" \
  -H "A2A-Version: 1.0" \
  -d '{"message":{"messageId":"message-1","role":"ROLE_USER","parts":[{"text":"hello"}]},"configuration":{"acceptedOutputModes":["text/plain"]}}' \
  http://localhost:8000/message:stream
```

You can also use the Python A2A streaming client:

```bash
a2a-stream-client "hello"
```

The project follows a strict spec-driven development workflow. Every meaningful feature starts with a specification in `specs/`, and implementation must stay aligned with the approved behavior. This keeps the repository useful as both working code and a reference architecture for building interoperable agent services on OCI.
