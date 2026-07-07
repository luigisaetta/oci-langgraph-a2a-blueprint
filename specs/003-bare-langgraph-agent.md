# Bare LangGraph Agent Specification

Date: 2026-07-06
Status: Draft

## Purpose

This specification defines the first implementation of the bare LangGraph agent described by the general architecture specification.

The agent is intentionally simple. It demonstrates the blueprint structure, shared state, LangChain `Runnable` steps, logging, simulated execution latency, and streaming progress without introducing real LLM calls, OCI calls, tools, or A2A protocol classes.

## Scope

This specification covers only the bare LangGraph agent layer.

The A2A server wrapper is part of the target architecture, but it is not implemented by this specification.

## Functional Requirements

The implementation must provide a reusable bare agent class that:

* builds a LangGraph `StateGraph`;
* executes three sequential steps named `step1`, `step2`, and `step3`;
* uses shared graph state across all steps;
* implements every step as a separate, human-readable class;
* makes every step class a LangChain `Runnable`;
* implements the LangChain `Runnable.invoke()` method directly in every step class;
* logs the beginning and end of each step;
* sleeps inside each step to simulate work;
* exposes a synchronous invocation API;
* exposes an asynchronous streaming API.

## Graph Structure

The graph must execute this sequence:

```text
START -> step1 -> step2 -> step3 -> END
```

The graph must be compiled before execution.

## State Schema

The shared state must contain:

* `input_text`: original caller input.
* `state1`: output produced by `step1`.
* `state2`: output produced by `step2`.
* `state3`: output produced by `step3`.
* `progress`: ordered progress messages collected during graph execution.
* `final_output`: final response text produced by `step3`.

The state schema must be explicit and typed.

The `progress` field must preserve all progress messages from all steps.

## Step Behaviour

Each step must:

* be implemented as a dedicated class: `Step1`, `Step2`, or `Step3`;
* be a LangChain `Runnable`;
* implement `invoke()` directly;
* accept the current shared state;
* log `<step_name> started`;
* sleep for the configured duration;
* add its output to the corresponding state field;
* add a progress message;
* log `<step_name> completed`;
* return a partial state update.

Default outputs:

* `step1` writes `state1`.
* `step2` writes `state2`.
* `step3` writes `state3` and `final_output`.

The default sleep duration must be `1.0` second.

The sleep duration must be configurable so tests can run without waiting.

The implementation must avoid generic step factories, `RunnableLambda`, or lambda-based business logic for the three default steps. The goal is to make each step obvious and easy for a human user to replace.

## Streaming Behaviour

The bare agent must expose an asynchronous streaming method.

The streaming method must:

* execute the LangGraph graph;
* yield structured progress events as the graph produces updates;
* yield one `step_completed` event for each completed step;
* yield one final `agent_completed` event after all steps finish;
* use the reusable `AgentProgressEvent` contract from the framework layer;
* set each step completion event `source` to the LangGraph step name;
* include the current state snapshot in every event;
* preserve step order.

The streaming contract must remain independent from A2A-specific SDK classes.
The A2A wrapper maps these framework progress events to A2A streaming events.

## Public API

The implementation must expose:

* `BareLangGraphAgent.invoke(input_text: str) -> AgentState`
* `BareLangGraphAgent.stream(input_text: str) -> AsyncIterator[AgentProgressEvent]`
* `BareLangGraphAgent.build_graph(steps: Iterable[BaseStep]) -> CompiledStateGraph`

The implementation may expose additional helpers if they improve readability and testing.

## Logging

Logging must use Python standard logging.

The logger name must be under the package namespace.

For a successful invocation, logs must include:

* `step1 started`
* `step1 completed`
* `step2 started`
* `step2 completed`
* `step3 started`
* `step3 completed`

## Error Handling

The bare agent must raise `ValueError` when:

* `input_text` is empty;
* `step_sleep_seconds` is negative.

Unexpected graph or runnable errors may propagate to the caller. A later A2A wrapper specification will define protocol-level error mapping.

## Non-Goals

This specification does not implement:

* A2A server routes;
* A2A agent cards;
* SSE HTTP endpoints;
* OCI service calls;
* real LLM calls;
* tool integration;
* durable checkpoint storage.

## Acceptance Criteria

This specification is accepted when:

* a bare agent package exists under `src/`;
* the graph executes `step1`, `step2`, and `step3` in order;
* `Step1`, `Step2`, and `Step3` are separate classes;
* each step class is a LangChain `Runnable`;
* each step can be invoked through `invoke()`;
* no default step uses `RunnableLambda`;
* each step writes the expected state field;
* the final state contains `state1`, `state2`, `state3`, `progress`, and `final_output`;
* step start and completion logs are emitted;
* the default sleep duration is `1.0` second;
* tests can override sleep duration to `0`;
* streaming yields step completion events in order and a final completion event;
* unit tests cover normal invocation, invalid input, invalid sleep duration, logging, and streaming.
