# General Architecture Specification

Date: 2026-07-06
Status: Draft

Note: The initial baseline used deterministic sample steps. The later
`specs/010-llm-backed-agent-step.md` specification adds a real LLM call to
`step2` while preserving the same framework and A2A boundaries.

## Purpose

This specification defines a first architecture baseline for the OCI LangGraph A2A Blueprint.

The repository is a blueprint, not a fixed business application. The sample agent logic must be easy for a customer to replace while preserving the runtime architecture, protocol boundary, streaming behaviour, and deployment model.

## Goals

The solution must provide:

* A minimal LangGraph agent with several sequential steps: `step1`, `step2`, and `step3`.
* A shared state passed through the full graph execution.
* Each step implemented as a LangChain `Runnable`.
* Logging at the beginning and end of every step.
* A configurable sleep delay in every step to simulate long-running work.
* Streaming updates while the agent is running.
* An A2A-compatible HTTP server wrapper that streams updates to clients using Server-Sent Events.
* A2A protocol support based on the official A2A Python SDK and the latest A2A protocol version currently defined by the upstream specification.

## Verified Upstream Facts

The architecture is based on the following verified upstream facts:

* The current A2A specification documents version negotiation using `Major.Minor` protocol versions and shows `1.0` as the current latest protocol version.
* A2A clients should send the `A2A-Version` header, and servers must return `VersionNotSupportedError` when a requested protocol version is unsupported.
* The official A2A Python SDK repository identifies the package name as `a2a-sdk`.
* The official A2A Python SDK states that it implements A2A Protocol Specification `1.0`, with compatibility mode for `0.3`.
* A2A supports HTTP streaming with Server-Sent Events for streaming message execution.
* The A2A Python SDK exposes an `AgentExecutor` abstraction that bridges protocol requests to application-specific agent logic.
* LangGraph `StateGraph` nodes communicate by reading and writing shared state.
* LangGraph `StateGraph.add_node` accepts a function or runnable as the node action.
* A compiled LangGraph state graph supports synchronous, asynchronous, and streaming execution methods.

## References

* A2A Protocol Specification: https://a2a-protocol.org/latest/specification/
* A2A Python SDK: https://github.com/a2aproject/a2a-python
* A2A Python Quickstart, Agent Executor: https://a2a-protocol.org/latest/tutorials/python/4-agent-executor/
* A2A Python Quickstart, Streaming and LangGraph: https://a2a-protocol.org/latest/tutorials/python/7-streaming-and-multiturn/
* LangGraph StateGraph Reference: https://reference.langchain.com/python/langgraph/graphs/
* LangChain Runnable Reference: https://reference.langchain.com/python/langchain_core/runnables/

## Architecture Overview

The target architecture is composed of two layers:

1. Bare LangGraph agent layer.
2. A2A HTTP server layer.

Both layers are part of the architecture. The LangGraph layer owns the workflow and state transitions, while the A2A layer owns protocol exposure, discovery metadata, task lifecycle mapping, and HTTP streaming.

```text
Client
  |
  | HTTP/SSE A2A request
  v
A2A Server Wrapper
  |
  | calls bare agent and maps stream events
  v
Bare LangGraph Agent
  |
  +--> step1 Runnable
  |
  +--> step2 Runnable
  |
  +--> step3 Runnable
  |
  v
Shared Agent State
```

## Bare LangGraph Agent

The bare agent must be implemented as a LangGraph `StateGraph`.

The graph must execute the following sequence:

```text
START -> step1 -> step2 -> step3 -> END
```

The graph state must be explicit and typed. At minimum, it must support:

* the original client input text;
* per-step outputs;
* a list of progress events or status messages;
* timestamps or execution metadata useful for logging and tests;
* an optional final response text.

The exact state schema will be finalized in the implementation specification before code is written.

## Step Design

Each step must be implemented as a LangChain `Runnable`.

Each step must:

* accept the current shared state;
* log a start message before simulated work begins;
* sleep for a configurable duration;
* update the shared state with its output;
* append or emit a progress update;
* log an end message after state update is complete;
* return only the partial state update expected by LangGraph.

The default business logic must be intentionally simple because this repository is a blueprint. Customers must be able to replace the step logic without rewriting the graph, streaming adapter, or A2A wrapper.

## Streaming Behaviour

The bare LangGraph agent must support streaming so a caller can observe progress while `step1`, `step2`, and `step3` execute.

The agent layer must expose an internal async streaming interface that yields
structured progress events defined by the reusable A2A framework contract. The
A2A wrapper maps those internal events to A2A streaming events.

Internal progress events should include:

* task or run identifier;
* source name, such as a LangGraph node, step, tool, or component;
* event type, such as `step_completed`, `data`, `agent_completed`, or `agent_failed`;
* human-readable message;
* timestamp;
* optional intermediate data emitted by a source;
* optional state snapshot or output fragment where useful.

The event contract must live in the reusable framework layer, not in the sample
agent state module. The bare agent must keep this streaming contract independent
from A2A-specific SDK classes. This keeps the core agent testable without an
HTTP server and makes the A2A integration a protocol adapter rather than part of
the business logic.

## A2A Server Wrapper

The A2A server must use the official `a2a-sdk` package.

The server must target A2A protocol version `1.0`. Compatibility with `0.3` may be enabled by the SDK but must not be the primary contract of this blueprint.

The server must expose an A2A agent card. The agent card must declare:

* protocol version `1.0`;
* streaming capability enabled;
* text input and text output support;
* a skill describing the sample three-step LangGraph workflow;
* server URL and protocol binding appropriate for the selected A2A binding.

The preferred server binding is HTTP+JSON/REST because it exposes `POST /message:stream` with an SSE response. JSON-RPC may be added later if required by interoperability tests or by the reference SDK defaults.

The A2A executor must:

* implement the SDK `AgentExecutor` interface;
* translate incoming A2A messages into the bare agent input schema;
* create or reuse A2A tasks using the SDK request context and task store;
* map bare-agent progress events to A2A `TaskStatusUpdateEvent` objects;
* map final output to an A2A artifact update;
* mark the task as completed when the graph finishes;
* map exceptions to a failed task state and a clear error message.

## Logging

The implementation must use Python standard logging.

Each step must log:

* `step1 started`;
* `step1 completed`;
* `step2 started`;
* `step2 completed`;
* `step3 started`;
* `step3 completed`.

The messages may include contextual fields such as task ID, run ID, sleep duration, and elapsed time.

The implementation must avoid printing directly to stdout except in command-line demo clients.

## Configuration

The sleep duration must be configurable as a sample-agent setting, not as an
A2A server setting.

The local implementation may use a simple configuration mechanism, but deployment-oriented specs must define the complete environment variable set. Secrets must be supplied through environment variables or ignored local files.

Candidate sample-agent configuration values:

* `AGENT_STEP_SLEEP_SECONDS`: simulated work duration for each step.
* `AGENT_LLM_MODEL_ID`: OCI OpenAI-compatible model id.
* `AGENT_LLM_API_KEY`: OCI OpenAI-compatible API key.
* `AGENT_LLM_OCI_REGION`: OCI region used to derive the inference endpoint.
* `AGENT_LLM_BASE_URL`: optional explicit OpenAI-compatible inference endpoint.

Candidate local runtime values:

* `AGENT_LOG_LEVEL`: logging level for local runs.

## Non-Goals

This architecture specification does not require:

* broader OCI service integration beyond the OpenAI-compatible inference call;
* tools or MCP integration;
* authentication and authorization;
* durable external task storage;
* push notifications;
* OCI deployment automation;
* production hardening beyond the blueprint scope.

These capabilities may be added by later specifications.

## Implementation Workstreams

### Bare LangGraph Agent

Implement the core workflow agent.

Expected outputs:

* project packaging and dependency definition;
* typed state schema;
* three LangChain Runnable steps;
* LangGraph graph builder;
* synchronous or asynchronous invocation helper;
* internal streaming helper;
* unit tests for normal execution, state updates, logging, sleep configuration, and streaming progress.

### A2A Server Wrapper

Wrap the bare agent as an A2A-compatible HTTP server.

Expected outputs:

* A2A agent card;
* `AgentExecutor` implementation;
* A2A route setup using the official SDK;
* SSE streaming support;
* local client or smoke test;
* unit tests for event mapping and task status transitions.

### OCI Deployment Blueprint

Add OCI deployment guidance and assets.

Expected outputs:

* runtime configuration specification;
* containerization or deployment packaging;
* OCI service assumptions;
* IAM and networking notes;
* deployment and smoke-test instructions.

## Acceptance Criteria

This architecture specification is accepted when:

* it clearly separates the bare LangGraph agent from the A2A wrapper;
* it defines the initial three-step graph sequence;
* it requires each step to be a LangChain `Runnable`;
* it requires shared state across all steps;
* it requires logging at step start and completion;
* it requires sleep-based simulated execution;
* it requires an internal streaming contract for progress updates;
* it states that the A2A wrapper targets protocol version `1.0`;
* it identifies the official A2A Python SDK package as `a2a-sdk`;
* it defines implementation workstreams and test expectations.

## Test Expectations

Bare LangGraph agent tests must verify:

* the graph executes `step1`, `step2`, and `step3` in order;
* each step updates the shared state;
* each step emits start and completion logs;
* sleep configuration is applied without making tests slow;
* streaming yields progress events in the expected order;
* the final state contains all step outputs and final response text.

A2A server wrapper tests must verify:

* A2A message input is translated into bare-agent input;
* bare-agent progress events are mapped to A2A task status updates;
* final output is mapped to an A2A artifact update;
* the stream closes with a completed task status;
* unsupported or invalid inputs produce clear A2A errors.

## Open Questions

* Should the A2A server expose only HTTP+JSON/REST, only JSON-RPC, or both?
* Should the bare agent streaming contract expose state snapshots or only event metadata?
* Should task state be kept only in memory for the blueprint, or should a later workstream include a durable store option?
* Should OCI deployment target a container runtime first, or an OCI Functions style deployment?
