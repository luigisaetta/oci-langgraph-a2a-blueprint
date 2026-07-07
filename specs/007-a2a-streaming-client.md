# A2A Streaming CLI Client Specification

Date: 2026-07-06
Status: Draft

## Purpose

This specification defines a Python command-line client that calls the local A2A
server over HTTP and consumes Server-Sent Events from `POST /message:stream`.

The client complements the direct bare-agent CLI by exercising the public A2A
protocol boundary.

## Scope

The client must:

* run from the command line;
* accept user input text as a positional argument;
* call `POST /message:stream`;
* send the `A2A-Version: 1.0` header;
* request and accept JSON over the A2A REST streaming binding;
* consume SSE events as they arrive;
* print a compact human-readable line for each event;
* print task status messages;
* print artifact text chunks;
* return exit code `0` on success;
* return exit code `1` for HTTP or SSE errors.

The client must not:

* instantiate the sample LangGraph agent directly;
* require OCI configuration;
* require secrets;
* implement a full A2A SDK client abstraction.

## Command

The client must be available as:

```text
a2a-stream-client "hello"
```

It must also be executable as a Python module:

```text
python -m oci_langgraph_a2a_blueprint.clients.a2a_stream_client "hello"
```

Supported options:

```text
--server-url URL      A2A server base URL. Defaults to http://localhost:8080.
--message-id VALUE    Message identifier. Defaults to a generated UUID.
--timeout SECONDS     HTTP timeout. Defaults to 30.0.
--show-raw            Print raw SSE JSON payloads.
```

## Output

For status updates, the client prints:

```text
status: TASK_STATE_WORKING - step1 completed
```

For artifact updates, the client prints:

```text
artifact: final_output - step3 processed: <LLM answer for "hello">
```

For the initial task, the client prints:

```text
task: TASK_STATE_SUBMITTED
```

If `--show-raw` is enabled, the client also prints the raw decoded JSON event.

## Acceptance Criteria

This specification is accepted when:

* the client can parse and format task, status, and artifact stream events;
* the client sends the correct A2A `POST /message:stream` request;
* tests cover output formatting and a successful mocked streaming response;
* the client has a dedicated README;
* formatting, linting, and tests pass.
