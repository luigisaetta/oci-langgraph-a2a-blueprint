# Changelog

## 2026-07-06

* Moved the reusable agent progress event contract into the A2A framework layer and generalized event source metadata.
* Separated reusable A2A framework modules from the replaceable sample agent package.
* Added a documentation index and a custom LangGraph agent plug-in guide.
* Clarified where each custom agent guide example should be placed or run.
* Moved graph construction behind `BareLangGraphAgent.build_graph` and removed the module-level graph builder export.
* Added the initial general architecture specification for the LangGraph agent blueprint and A2A server wrapper.
* Revised the architecture specification to describe the target A2A architecture independently from delivery order.
* Added the runtime dependencies specification and initial Conda environment definition.
* Added the bare LangGraph agent specification, implementation, streaming API, and unit tests.
* Refined the bare agent implementation so `step1`, `step2`, and `step3` are separate human-readable Runnable classes.
* Simplified the step implementation to extend LangChain `Runnable` directly and implement `invoke()` without `RunnableLambda`.
* Added the direct Python CLI client specification, implementation, README, and tests.
* Added the first A2A HTTP/SSE server wrapper with Agent Card discovery and streaming execution.
* Added local A2A server run documentation.
* Expanded the local A2A server README with wrapper architecture and adaptation guidance.
* Generalized A2A server reuse by injecting streaming agent factories.
* Added centralized runtime configuration loading for local server settings.
* Added the A2A streaming Python CLI client, documentation, and tests.
* Updated the main README with the current feature list and quickstart.
* Renamed the reusable A2A server factory to `create_server` and removed sample-agent sleep settings from its public API.
* Moved the local sample A2A server entry point out of the reusable server factory module.
* Introduced an explicit sample agent definition plug point for agent factory and Agent Card replacement.
* Moved shared A2A protocol constants and the default local server URL out of the sample agent adapter.
* Added a single-container Docker Compose deployment with root start and stop scripts.
* Added an explicit sleep duration option to the Docker Compose start script.
