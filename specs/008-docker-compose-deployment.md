# Docker Compose Deployment Specification

Date: 2026-07-06
Status: Draft

## Purpose

This specification defines the first local Docker Compose deployment path for
the OCI LangGraph A2A Blueprint.

The deployment must run the sample LangGraph agent and the A2A HTTP/SSE server
in a single container. The container is intended for local validation and as a
simple deployment blueprint, not as a full production OCI deployment.

## Scope

The Docker Compose deployment must:

* build one container image from the repository source;
* run the existing `a2a-langgraph-server` entry point;
* expose the A2A server on host port `8080` by default;
* include the sample LangGraph agent and A2A server in the same container;
* use the same environment variables as the local server runtime;
* provide root-level `start_server.sh` and `stop_server.sh` scripts;
* document how to start, stop, and test the composed server;
* avoid hard-coded secrets, tenancy identifiers, private endpoints, or local
  machine paths.

The deployment must not:

* add a second container for the sample agent;
* add a reverse proxy, database, queue, or durable task store;
* call OCI services;
* require Docker-specific changes to the Python runtime code;
* replace the Conda-based local development workflow.

## Container Image

The container image must use a Python `3.11` runtime and install the project
package with its runtime dependencies.

Runtime dependencies must be declared in package metadata so the image can be
built from source without relying on a pre-existing Conda environment.

The image command must run:

```text
a2a-langgraph-server
```

The container must listen on port `8080`.

## Docker Compose Service

The Docker Compose file must define one service named `a2a-server`.

The service must:

* build from the repository root;
* publish `${A2A_SERVER_PORT:-8080}:8080`;
* set `A2A_SERVER_HOST=0.0.0.0`;
* set `A2A_SERVER_PORT=8080` inside the container;
* set `A2A_SERVER_PUBLIC_URL` to
  `${A2A_SERVER_PUBLIC_URL:-http://localhost:8080}`;
* set `AGENT_LOG_LEVEL` to `${AGENT_LOG_LEVEL:-INFO}`;
* set `AGENT_STEP_SLEEP_SECONDS` to `${AGENT_STEP_SLEEP_SECONDS:-0}`;
* restart only when explicitly requested by Docker Compose defaults, not through
  an always-on restart policy.

The default sample-agent sleep duration for the composed server should be `0`
to make local smoke tests fast. Users can override it with
`AGENT_STEP_SLEEP_SECONDS`.

## Root Scripts

`start_server.sh` must:

* be executable;
* run from any current working directory by resolving the repository root from
  the script location;
* accept `--sleep-seconds VALUE` and `-s VALUE` to set the sample agent step
  duration for the composed server;
* continue to support `AGENT_STEP_SLEEP_SECONDS` as an environment override;
* start the Docker Compose service in detached mode;
* build the image when needed.

`stop_server.sh` must:

* be executable;
* run from any current working directory by resolving the repository root from
  the script location;
* stop and remove the Docker Compose service using `docker compose down`.

## Documentation

The main README and local A2A server README must document:

* Docker Compose as an alternative to the Conda local server;
* the root start and stop scripts;
* the default server URL;
* the supported environment variable overrides;
* the `start_server.sh --sleep-seconds VALUE` option;
* a simple smoke test using the A2A streaming client or `curl`.

## Acceptance Criteria

This specification is accepted when:

* `Dockerfile` exists at the repository root;
* `docker-compose.yml` exists at the repository root;
* `.dockerignore` exists and excludes local caches, virtual environments, and
  Git metadata;
* `start_server.sh` and `stop_server.sh` exist at the repository root and are
  executable;
* `start_server.sh` exposes an explicit sleep duration option;
* `docker compose config` validates the Compose file;
* package metadata declares the runtime dependencies needed by the container;
* tests cover the presence and key contents of the Docker deployment files;
* documentation describes the Compose workflow;
* formatting, linting, and unit tests pass.
