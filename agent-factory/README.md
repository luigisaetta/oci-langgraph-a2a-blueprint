# Agent Factory

Agent Factory is the guided deployment application for publishing this
repository's A2A server Docker image to OCI Enterprise AI Hosted Applications.

It contains:

- `api`: FastAPI backend for validation, run tracking, command planning, OCIR
  checks, IDCS token checks, and live deployment orchestration.
- `ui`: Next.js UI for collecting deployment inputs, running dry checks, and
  showing deployment progress.

## Local Development

Start the API:

```bash
PYTHONPATH=agent-factory/api uvicorn agent_factory_api.app:app --host 0.0.0.0 --port 8081
```

Start the UI:

```bash
cd agent-factory/ui
npm run dev
```

Then open:

```text
http://localhost:3100
```

## Docker Compose

The Agent Factory API container uses the host Docker daemon to validate OCIR
credentials, build the root A2A server image from `Dockerfile`, and push it to
OCI Container Registry. Make sure Docker is running on the host before starting
Agent Factory.

Start the Agent Factory deployment from the repository root:

```bash
./start_factory.sh --build
```

Stop only the Agent Factory services:

```bash
./stop_factory.sh
```

The local endpoints are:

```text
Agent Factory API: http://localhost:8081/factory/health
Agent Factory UI:  http://localhost:3100
```

## Deployment Inputs

Required values include:

- OCI compartment name or OCID.
- OCI region.
- Hosted Application name.
- Hosted Deployment name.
- OCI Generative AI model id for the sample A2A agent.
- `AGENT_LLM_API_KEY` value for the hosted A2A server.
- OCIR username and auth token/password.
- OCIR repository name and non-`latest` image tag.

Optional JWT protection uses OCI IAM Identity Domains. When enabled, provide
the Identity Domain URL, audience claim, scope claim, confidential application
client ID, and confidential application secret. The factory validates the token
settings without returning the access token.

Dry runs validate inputs and generate command plans without creating OCI
resources. Non-dry-run deployments build and push the A2A server image, create
or reuse the Hosted Application, create a Hosted Deployment, and validate the
hosted `/health` endpoint.

After a successful live deployment, the UI outputs include the Hosted
Application invoke base URL plus ready-to-use health, Agent Card, and
`/message:stream` URLs.
