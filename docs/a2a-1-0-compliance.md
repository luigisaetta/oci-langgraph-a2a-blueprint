# A2A 1.0 Compliance Notes

This document records the current compliance position for the OCI LangGraph A2A
blueprint.

The short version is:

```text
The project implements the A2A 1.0 HTTP+JSON/REST streaming path used by this
blueprint, but it does not claim to be a complete implementation of every A2A
1.0 operation.
```

## Compliance Claim

The implemented server should be described as:

```text
A2A 1.0 HTTP+JSON/REST streaming-path compatible.
```

Avoid describing the current implementation as:

```text
Fully A2A 1.0 compliant.
```

That stronger statement would require broader endpoint coverage and a formal
compliance test matrix.

## Why the Streaming Path Is Aligned with A2A 1.0

The current implementation is aligned with the A2A 1.0 HTTP+JSON/REST streaming
path for these reasons:

* The project depends on the official Python package `a2a-sdk[http-server]`.
* The installed SDK version used during local validation was `a2a-sdk 1.1.0`.
* The official `a2a-python` SDK repository states that the SDK implements A2A
  Protocol Specification `1.0`, including HTTP+JSON/REST client and server
  support.
* The server uses SDK-provided protocol components:
  * `DefaultRequestHandler`;
  * `create_agent_card_routes`;
  * `create_rest_routes`;
  * `InMemoryTaskStore`;
  * `AgentExecutor`.
* The project declares protocol version `1.0` through
  `A2A_PROTOCOL_VERSION = "1.0"`.
* The sample Agent Card advertises a supported interface with:
  * protocol binding `HTTP+JSON`;
  * protocol version `1.0`;
  * streaming capability enabled.
* The A2A streaming client sends:
  * `Content-Type: application/a2a+json`;
  * `A2A-Version: 1.0`;
  * a `POST /message:stream` request body using the A2A message shape.
* The server exposes `POST /message:stream`, which is the HTTP+JSON/REST
  streaming message operation in the A2A 1.0 specification.
* The executor maps internal agent progress to A2A task lifecycle events:
  * initial `Task` with `TASK_STATE_SUBMITTED`;
  * working status updates for progress;
  * final artifact for the task result;
  * completed task status when the workflow finishes;
  * failed task status for controlled agent failures.

## Implemented A2A Surface

The server intentionally exposes a small route surface:

```text
GET  /.well-known/agent-card.json
POST /message:stream
```

This is enough for the current blueprint goal: expose a LangGraph agent through
Agent Card discovery and the A2A HTTP+JSON/REST streaming execution path.

## A2A 1.0 Operations Not Implemented

The current server does not expose the full set of A2A 1.0 HTTP+JSON/REST
operations.

Not implemented today:

```text
POST   /message:send
GET    /tasks/{id}
GET    /tasks
POST   /tasks/{id}:cancel
POST   /tasks/{id}:subscribe
POST   /tasks/{id}/pushNotificationConfigs
GET    /tasks/{id}/pushNotificationConfigs/{configId}
GET    /tasks/{id}/pushNotificationConfigs
DELETE /tasks/{id}/pushNotificationConfigs/{configId}
GET    /extendedAgentCard
```

Some of these operations may be added later, but they are outside the current
scope of the blueprint.

## Important Limitations

The current implementation should not be treated as formally certified A2A 1.0
compliance.

Known limitations:

* The route surface is intentionally narrower than the full HTTP+JSON/REST
  binding.
* The implementation has not been validated with a formal A2A conformance
  suite.
* The implementation has not yet been validated with `a2a-inspector`.
* The server currently focuses on plain text input and plain text output.
* The server does not implement push notifications.
* The server does not implement authenticated extended Agent Cards.
* The server does not implement persistent task storage.
* The server does not expose task polling or task subscription endpoints.
* Version negotiation behavior is delegated to the A2A SDK for SDK-owned routes,
  but the project does not yet have explicit tests for unsupported
  `A2A-Version` values.

## Suggested Wording for Documentation

Use this wording:

```text
This blueprint implements the A2A 1.0 HTTP+JSON/REST streaming path using the
official A2A Python SDK.
```

For a shorter feature bullet:

```text
A2A 1.0 HTTP+JSON/REST streaming-path support.
```

Avoid this wording unless full endpoint coverage and compliance validation are
added:

```text
Fully A2A 1.0 compliant server.
```

## Recommended Compliance Test Matrix

A future compliance-focused specification should add tests for at least:

* Agent Card route returns an A2A Agent Card at
  `/.well-known/agent-card.json`.
* Agent Card advertises `HTTP+JSON` and protocol version `1.0`.
* Agent Card declares `capabilities.streaming` as `true`.
* `POST /message:stream` accepts a valid A2A message request.
* `POST /message:stream` requires or correctly handles `A2A-Version: 1.0`.
* Unsupported A2A protocol versions produce the expected
  `VersionNotSupportedError` behavior.
* Request payloads use `application/a2a+json`.
* Streaming responses use Server-Sent Events.
* The stream begins with a `Task`.
* Progress events are emitted as `TaskStatusUpdateEvent` objects.
* Final output is emitted as a `TaskArtifactUpdateEvent`.
* Successful execution ends in `TASK_STATE_COMPLETED`.
* Controlled agent failures end in `TASK_STATE_FAILED`.
* The exposed route surface matches the documented route surface.

## Primary References

Use these upstream references when reviewing or extending compliance:

* A2A Protocol Specification:
  <https://a2a-protocol.org/latest/specification/>
* A2A Python SDK:
  <https://github.com/a2aproject/a2a-python>

