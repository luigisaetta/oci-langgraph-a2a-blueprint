# LLM-backed Agent Step Specification

Date: 2026-07-07
Status: Draft

## Purpose

This specification defines the first real LLM-backed behavior in the sample
LangGraph agent.

The goal is to keep the blueprint simple while showing how a custom agent can
call an OCI-hosted OpenAI-compatible Responses API endpoint from one graph step.

## Scope

The sample agent must keep the existing three-step graph shape:

```text
step1 -> step2 -> step3
```

`step2` must call an LLM through the OpenAI Python library and the Responses
API. The LLM input must be the original user message sent to the agent, not the
intermediate `state1` value.

The Responses API integration must be isolated in a dedicated module under:

```text
src/oci_langgraph_a2a_blueprint/agent/
```

The graph, A2A framework, executor, server, and protocol contracts must remain
independent from OpenAI SDK details.

## Runtime Configuration

The LLM integration must read configuration from environment variables:

```text
AGENT_LLM_MODEL_ID       OCI OpenAI-compatible model id.
AGENT_LLM_API_KEY        OCI OpenAI-compatible API key.
AGENT_LLM_OCI_REGION     OCI region used to derive the default endpoint.
AGENT_LLM_BASE_URL       Optional explicit OpenAI-compatible endpoint.
```

The default model id must be:

```text
openai.gpt-5.5
```

If `AGENT_LLM_BASE_URL` is not provided, the integration must derive the OCI
OpenAI-compatible inference endpoint from `AGENT_LLM_OCI_REGION`:

```text
https://inference.generativeai.{region}.oci.oraclecloud.com/openai/v1
```

The default region is:

```text
us-chicago-1
```

`AGENT_LLM_API_KEY` is required for the default API-key mode. Unit tests must
avoid real network calls by injecting fake LLM responders.

## Environment Files

The repository must include:

```text
env.sample
```

with safe placeholder values and documentation for the LLM variables.

The local workspace may include:

```text
.env
```

with placeholder values only. `.env` must remain ignored by Git and must not
contain real secrets.

## LLM Client Behavior

The dedicated LLM module must:

* load `.env` values through `python-dotenv` for local development;
* build an OpenAI-compatible client with `base_url` and `api_key`;
* call `client.responses.create(model=model_id, input=input_text)`;
* return the response `output_text`;
* provide a small extraction fallback for response-like objects used in tests;
* raise clear `ValueError` exceptions when required configuration or response
  text is missing.

The OpenAI Python dependency must be added to the Python project and Conda
environment definitions.

## Agent Behavior

`Step2` must:

* receive an injected LLM responder;
* send `state["input_text"]` to the LLM responder;
* store the LLM answer in `state2`;
* preserve existing progress logging and progress state updates.

`Step1` and `Step3` may remain deterministic.

## Docker Compose

The Docker Compose deployment must pass the LLM environment variables into the
container. Secrets must still be supplied through local environment variables or
an ignored `.env` file, not committed to source control.

## Tests

Unit tests must cover:

* LLM settings defaults and overrides;
* missing API key validation;
* derived OCI base URL;
* Responses API invocation with model id and original user input;
* output text extraction;
* `Step2` storing the fake LLM answer in `state2`;
* full agent invocation and streaming with an injected fake LLM responder.

Tests must not make real OCI or OpenAI calls.

## Documentation

Runtime documentation must describe:

* required LLM environment variables;
* how to copy `env.sample` to `.env`;
* that `.env` is ignored and must not contain committed secrets;
* that unit tests use fake responders and do not call the real API.

## Acceptance Criteria

This specification is accepted when:

* `step2` calls an LLM responder with the original user input;
* the default runtime LLM responder uses the OpenAI Responses API;
* LLM configuration is read from environment variables and safe `.env` files;
* `openai` is declared as a runtime dependency;
* Docker Compose passes the LLM variables into the service;
* unit tests cover the new behavior without network calls;
* documentation and changelog are updated;
* formatting, linting, tests, and coverage checks pass.
