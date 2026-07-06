# Direct Agent CLI Client Specification

Date: 2026-07-06
Status: Draft

## Purpose

This specification defines the first Python command-line client for the bare LangGraph agent.

The client invokes the agent directly, without A2A, HTTP, or SSE. Its purpose is to demonstrate the internal streaming behaviour of the bare agent before introducing the A2A server wrapper.

## Scope

The client must:

* run from the command line;
* accept input text from a command-line argument;
* instantiate `BareLangGraphAgent`;
* consume `BareLangGraphAgent.stream()`;
* print progress events as they arrive;
* print the final output at the end;
* allow overriding the simulated step sleep duration;
* provide basic logging configuration.

The client must not:

* expose an HTTP server;
* use A2A SDK classes;
* call OCI services;
* call a real LLM;
* require secrets or configuration files.

## Command

The project package must be installed in editable mode inside the Conda environment:

```text
python -m pip install --no-deps -e .
```

After that, the client must be executable as a Python module from the repository root
without setting `PYTHONPATH`:

```text
python -m oci_langgraph_a2a_blueprint.clients.direct_agent_cli "hello"
```

The editable install must also provide the `direct-agent-cli` console command:

```text
direct-agent-cli "hello"
```

The client must support:

* positional `input_text`;
* `--sleep-seconds`, defaulting to `1.0`;
* `--log-level`, defaulting to `WARNING`;
* `--show-state`, defaulting to false.

## Output

For each streamed event, the client must print one line containing:

* event type;
* step name when available;
* event message.

When `--show-state` is enabled, the client must also print the current state snapshot after each event.

After the stream completes, the client must print:

* `Final output: <final_output>`

## Error Handling

The client must:

* return exit code `0` for successful execution;
* return exit code `1` when the agent rejects input or sleep configuration;
* let `argparse` handle invalid command-line arguments.

## README

A dedicated README must document:

* how to activate the Conda environment;
* how to run the client;
* how to reduce sleep duration for fast demos;
* how to enable logging;
* what output to expect.

## Acceptance Criteria

This specification is accepted when:

* the project can be installed with `python -m pip install --no-deps -e .`;
* the direct client can be executed with `python -m` without setting `PYTHONPATH`;
* the direct client can be executed with the `direct-agent-cli` console command;
* the client streams `step1`, `step2`, and `step3` progress in order;
* the client prints final output;
* the client has a dedicated README;
* tests cover output formatting and successful client execution with zero sleep;
* formatting, linting, and tests pass.
