# A2A Server Runtime Configuration Specification

Date: 2026-07-06
Status: Draft

## Purpose

This specification defines a small centralized runtime configuration module for
the local A2A server.

The goal is to keep environment variable parsing out of server wiring code while
remaining easy to read and modify.

## Scope

The A2A server configuration module must:

* expose a typed settings object for the local A2A server;
* read environment variables from an injectable mapping for testability;
* provide defaults suitable for local development;
* derive the public server URL when it is not explicitly provided;
* validate numeric values with clear `ValueError` messages;
* keep sample-agent settings separate from generic A2A server settings.

The A2A server configuration module must not:

* read secrets;
* call OCI services;
* introduce a configuration framework;
* require a `.env` file;
* hide defaults in multiple modules.

## Environment Variables

The local server configuration supports:

```text
A2A_SERVER_HOST              Bind host. Defaults to 0.0.0.0.
A2A_SERVER_PORT              Bind port. Defaults to 8080.
A2A_SERVER_PUBLIC_URL        Public URL advertised in the Agent Card.
AGENT_LOG_LEVEL              Python logging level. Defaults to INFO.
```

`AGENT_STEP_SLEEP_SECONDS` is a sample-agent setting and must not be part of the
local server settings object.

## Acceptance Criteria

This specification is accepted when:

* A2A server configuration is loaded through a dedicated module;
* `a2a_server.py` no longer parses environment variables directly;
* defaults match the existing local server behaviour;
* invalid port values raise clear errors;
* tests cover defaults, explicit overrides, derived public URL, and validation.
