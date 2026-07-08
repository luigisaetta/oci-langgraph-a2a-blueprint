# OCI Hosted Deployment Factory Specification

Date: 2026-07-08
Status: Draft

## Purpose

This specification defines an Agent Factory application for deploying the OCI
LangGraph A2A server and bundled sample agent as an OCI Enterprise AI Hosted
Application deployment.

The implementation must follow the deployment approach used by the
`oci-rag-agent-blueprint` Agent Factory. The main difference is that this
repository builds and deploys the root Docker image for the A2A server instead
of the RAG backend image.

## Scope

The Hosted Deployment Factory must:

* provide a separate local Agent Factory application;
* collect deployment inputs through a web UI;
* expose a FastAPI backend that validates inputs and orchestrates deployment
  operations;
* build the repository root Docker image;
* authenticate to OCI Container Registry;
* push the A2A server image to OCI Container Registry;
* create or reuse an OCI Enterprise AI Hosted Application;
* create a Hosted Deployment from the pushed Docker image;
* generate Hosted Application runtime environment configuration for this A2A
  server;
* optionally configure Hosted Application JWT protection through
  `IDCS_AUTH_CONFIG`;
* return Hosted Application invoke, health, Agent Card, and A2A streaming
  endpoint URLs;
* provide a ready-to-run shell script export using the same pattern as the RAG
  blueprint.

The Hosted Deployment Factory must not:

* deploy the factory application as part of the hosted A2A runtime;
* add a second runtime container to the hosted A2A deployment;
* create Object Storage buckets, Vector Stores, Data Sync Connectors, or RAG
  resources;
* call hosted runtime endpoints without an explicit user action;
* hard-code secrets, tenancy identifiers, OCIDs, private endpoints, or local
  machine paths.

## Related Specifications

* [General Architecture](001-general-architecture.md)
* [A2A Server Runtime Configuration](006-runtime-configuration.md)
* [Docker Compose Deployment](008-docker-compose-deployment.md)
* [LLM-Backed Agent Step](010-llm-backed-agent-step.md)

## Application Structure

The Agent Factory application must live under `agent-factory/` and include:

* `api/`: FastAPI backend and deployment orchestration helpers.
* `ui/`: Next.js UI for collecting deployment inputs and displaying progress.
* `docker-compose.yml`: local two-service Compose deployment for the factory.
* root-level `start_factory.sh` and `stop_factory.sh` helpers.

The API container must mount the repository root read-only through
`AGENT_FACTORY_REPO_ROOT` so it can build the root `Dockerfile`.

The API container must have access to Docker CLI, OCI CLI, and the host Docker
socket for local Compose execution, matching the mechanism used by the RAG
blueprint.

## Runtime Environment

The Hosted Application runtime environment must configure the A2A server with:

```text
A2A_SERVER_HOST=0.0.0.0
A2A_SERVER_PORT=8080
A2A_SERVER_PUBLIC_URL=<hosted invoke URL>
AGENT_LOG_LEVEL=<selected log level>
AGENT_STEP_SLEEP_SECONDS=<selected sleep duration>
AGENT_LLM_MODEL_ID=<selected model id>
AGENT_LLM_API_KEY=<secret API key value>
AGENT_LLM_OCI_REGION=<selected OCI region>
AGENT_LLM_BASE_URL=<optional explicit endpoint>
```

`AGENT_LLM_API_KEY` is required by the current A2A sample agent and must be
treated as a secret. It must not be returned in API responses, logs, command
plans, or generated scripts.

## Optional JWT Protection

When JWT protection is disabled, the Hosted Application inbound authentication
configuration must match the unauthenticated pattern used by the RAG blueprint.

When JWT protection is enabled, the factory must generate an `IDCS_AUTH_CONFIG`
inbound authentication payload using the same fields and semantics as the RAG
blueprint:

* OCI IAM Identity Domain URL.
* Client ID.
* Client secret.
* Hosted Application audience claim.
* Hosted Application scope claim.

The factory may validate the submitted IDCS configuration by requesting and
decoding an access token. Token diagnostics must be non-secret and must not
return the access token itself.

Protected deployments must rely on OCI Hosted Application platform-level JWT
enforcement. The A2A server application must not implement a second JWT
validation layer.

## Deployment Workflow

The backend must orchestrate deployment steps in this order:

1. Validate deployment inputs.
2. Validate OCIR login credentials.
3. Build the A2A server image from the repository root `Dockerfile`.
4. Create or reuse the OCIR repository.
5. Push the image to OCIR.
6. Generate Hosted Application runtime environment JSON.
7. Create or reuse the Hosted Application.
8. Create the Hosted Deployment with the pushed Docker image.
9. Poll deployment readiness.
10. Return non-secret deployment outputs and endpoint URLs.

Commands must be built as argument lists, not by concatenating shell strings
from untrusted input.

## Endpoint Outputs

The deployed A2A server must expose `GET /health` so Hosted Deployment
validation can distinguish an unreachable runtime from an agent protocol
failure.

For a completed deployment, the factory must return:

```text
invoke_url
health_url
agent_card_url
message_stream_url
hosted_application_id
hosted_deployment_id
docker_image
```

The URL paths are derived from the Hosted Application invoke URL:

```text
<invoke_url>/health
<invoke_url>/.well-known/agent-card.json
<invoke_url>/message:stream
```

## Documentation

The main README and Agent Factory README must document:

* how to start and stop the factory locally;
* required OCI, Docker, and OCIR prerequisites;
* required A2A server runtime variables;
* optional JWT/IDCS inputs;
* generated endpoint URLs;
* the fact that the factory deploys the root A2A server Docker image.

## Acceptance Criteria

This specification is accepted when:

* `agent-factory/` exists with API, UI, and Compose files copied from and
  adapted from the RAG blueprint;
* root `start_factory.sh` and `stop_factory.sh` exist and are executable;
* the factory builds the root A2A server Docker image;
* runtime environment generation uses the A2A server variables listed here;
* optional JWT configuration follows the RAG blueprint `IDCS_AUTH_CONFIG`
  approach;
* tests cover validation, command generation, IDCS helpers, ready script output,
  and A2A-specific endpoint URL derivation;
* tests cover the runtime A2A server `GET /health` endpoint;
* documentation describes the Hosted Deployment Factory workflow;
* relevant formatting, linting, unit testing, and coverage checks have been run
  or any inability to run them is reported.
