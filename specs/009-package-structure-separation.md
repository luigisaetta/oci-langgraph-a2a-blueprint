# Package Structure Separation Specification

Date: 2026-07-07
Status: Draft

## Purpose

This specification defines the physical package separation between the reusable
A2A framework code and the replaceable sample LangGraph agent.

The goal is to make the repository easier to reuse as a blueprint: users should
be able to identify what belongs to the reusable A2A wrapper and what belongs to
the agent implementation they are expected to replace.

## Scope

The package must be split into two clear subpackages:

```text
src/oci_langgraph_a2a_blueprint/framework/
src/oci_langgraph_a2a_blueprint/agent/
```

The `framework` package owns reusable A2A concerns:

* A2A protocol constants and streaming agent contracts;
* A2A executor mapping;
* A2A server factory and local server entry point;
* A2A server runtime configuration.

The `agent` package owns the sample LangGraph agent:

* graph construction and invocation;
* sample state schema;
* sample steps;
* sample agent adapter and Agent Card factory.

The sample agent package must be named `agent`, not `sample_agent`.

## Public API

The root package may continue to re-export the most important public classes and
factories for convenience:

* `AgentEventType`;
* `AgentProgressEvent`;
* `AgentState`;
* `BareLangGraphAgent`;
* `create_agent_adapter`;
* `create_agent_card`;
* `create_server`.

The module-level `build_graph` export must remain removed. Graph construction is
owned by `BareLangGraphAgent`.

## Runtime Entry Points

The console scripts must continue to work:

```text
a2a-langgraph-server
a2a-stream-client
direct-agent-cli
```

The `a2a-langgraph-server` script must point to the new framework server module.
The client scripts may remain in the existing clients package.

## Documentation

Documentation must describe the new physical layout and update all referenced
source paths.

The local A2A server README must make it clear that normal agent replacement
should happen in `src/oci_langgraph_a2a_blueprint/agent/`, while reusable A2A
server changes belong under `src/oci_langgraph_a2a_blueprint/framework/`.

## Acceptance Criteria

This specification is accepted when:

* reusable A2A modules live under `framework/`;
* sample agent modules live under `agent/`;
* imports and console entry points use the new module paths;
* root package exports continue to provide the documented convenience API;
* tests import from the new package locations where appropriate;
* README files and relevant specs reference the new paths;
* formatting, linting, and tests pass.
