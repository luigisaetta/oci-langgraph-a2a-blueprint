# Runtime Dependencies Specification

Date: 2026-07-06
Status: Draft

## Purpose

This specification defines the first dependency set for the `oci-langgraph-a2a-blueprint` Conda environment.

The dependency set supports the target architecture described in `specs/001-general-architecture.md`:

* a bare LangGraph agent composed of sequential LangChain `Runnable` steps;
* a shared typed state;
* internal async streaming of progress updates;
* an A2A-compatible HTTP server wrapper with Server-Sent Events;
* unit testing, formatting, linting, and coverage checks.

## Conda Environment

The project development and test environment is:

```text
oci-langgraph-a2a-blueprint
```

The repository must provide an `environment.yml` file so the environment can be created or updated repeatably.

## Dependency Groups

### Core Python Runtime

The environment must use Python `3.11`.

Python `3.11` is selected because it is broadly supported by LangGraph, LangChain, the A2A Python SDK, and common OCI deployment runtimes while avoiding unnecessary constraints from newer interpreter versions.

### Bare LangGraph Agent

The bare agent requires:

* `langgraph`: graph runtime used to define and execute the shared-state workflow.
* `langchain-core`: provides the LangChain `Runnable` abstraction used by each step.
* `pydantic`: validates structured configuration and event payloads where useful.
* `typing-extensions`: supports portable typing features used by LangGraph and state schemas.

### A2A Server and Streaming

The A2A server wrapper requires:

* `a2a-sdk[http-server]`: official Python SDK for the A2A protocol with HTTP server support.
* `starlette`: ASGI framework used by the A2A SDK examples and route integration.
* `uvicorn`: local ASGI server used to run the HTTP endpoint.
* `httpx`: async HTTP client used by tests and A2A client utilities.
* `httpx-sse`: SSE client support for streaming tests and local clients.

The target A2A protocol version is `1.0`, as defined by the current upstream A2A specification and implemented by the official SDK.

### Local Configuration

The environment should include:

* `python-dotenv`: optional local development helper for loading environment variables from `.env` files.

`.env` files must remain excluded from version control.

### Testing and Quality

The environment must include:

* `pytest`: unit test runner.
* `pytest-asyncio`: async test support for streaming and server tests.
* `pytest-cov`: coverage reporting.
* `black`: Python formatter.
* `pylint`: Python linter.

## Deferred Dependencies

The following libraries are intentionally not part of the first dependency set:

* `oci`
* `langchain-oci`
* `langchain-community`
* `langchain-openai`
* `langchain-google-genai`

These dependencies must be added only when a later specification introduces real OCI service calls, OCI Generative AI integration, external tools, or real LLM providers.

## Environment File Requirements

The `environment.yml` file must:

* use the environment name `oci-langgraph-a2a-blueprint`;
* use `conda-forge` as the primary Conda channel;
* install Python, `pip`, and quality/test tools through Conda where practical;
* install LangGraph, LangChain Core, and A2A SDK packages through `pip`;
* avoid secrets, local machine paths, private package indexes, or customer-specific configuration.

## Acceptance Criteria

This specification is accepted when:

* `environment.yml` exists in the repository root;
* the dependency list supports both the bare LangGraph agent and the A2A HTTP/SSE wrapper;
* optional and deferred dependencies are clearly identified;
* the `oci-langgraph-a2a-blueprint` Conda environment can be updated from `environment.yml`;
* imports for the core packages can be verified from the Conda environment.

