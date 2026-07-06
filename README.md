# OCI LangGraph A2A Blueprint

Build a production-oriented LangGraph agent, package it as an A2A-compatible server, and deploy it on Oracle Cloud Infrastructure.

This repository is a blueprint for teams that want to move from an agent prototype to a cloud-ready service with a clear protocol boundary. The goal is not only to run a LangGraph workflow, but to expose it through a standard A2A server interface so that other agents, applications, and orchestration layers can discover it, call it, and reason about its task lifecycle.

The blueprint will show how to connect the key pieces:

- a LangGraph agent with explicit state, nodes, tools, and model configuration;
- an A2A-compatible API layer with agent card metadata, request validation, task handling, and structured responses;
- OCI-ready runtime configuration, deployment assets, and operational guidance;
- tests and specifications that make the behavior understandable, repeatable, and safe to evolve.

The project follows a strict spec-driven development workflow. Every meaningful feature starts with a specification in `specs/`, and implementation must stay aligned with the approved behavior. This keeps the repository useful as both working code and a reference architecture for building interoperable agent services on OCI.
