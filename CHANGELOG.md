# Changelog

## 2026-07-06

* Added the initial general architecture specification for the LangGraph agent blueprint and A2A server wrapper.
* Revised the architecture specification to describe the target A2A architecture independently from delivery order.
* Added the runtime dependencies specification and initial Conda environment definition.
* Added the bare LangGraph agent specification, implementation, streaming API, and unit tests.
* Refined the bare agent implementation so `step1`, `step2`, and `step3` are separate human-readable Runnable classes.
* Simplified the step implementation to extend LangChain `Runnable` directly and implement `invoke()` without `RunnableLambda`.
* Added the direct Python CLI client specification, implementation, README, and tests.
* Added the first A2A HTTP/SSE server wrapper with Agent Card discovery and streaming execution.
* Added local A2A server run documentation.
