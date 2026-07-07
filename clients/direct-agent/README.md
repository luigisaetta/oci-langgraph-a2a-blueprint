# Direct Agent CLI Client

This client invokes the sample LangGraph agent directly from the command line.

It does not use A2A, HTTP, or Server-Sent Events. It is a local development client that shows the agent's internal streaming progress before the A2A server wrapper is introduced.

## Setup

Activate the project Conda environment:

```bash
conda activate oci-langgraph-a2a-blueprint
```

Install the project package in editable mode from the repository root:

```bash
python -m pip install --no-deps -e .
```

This makes the `src/` package importable without setting `PYTHONPATH`.

Copy the sample environment file and set the LLM API key before running the
client:

```bash
cp env.sample .env
# Edit .env and set AGENT_LLM_API_KEY.
```

## Basic Usage

```bash
python -m oci_langgraph_a2a_blueprint.clients.direct_agent_cli "hello from the client"
```

You can also use the console command installed by the project:

```bash
direct-agent-cli "hello from the client"
```

The client prints one line for each streamed event and then prints the final output.

## Fast Demo

Use `--sleep-seconds 0` to avoid waiting for the simulated step delay:

```bash
python -m oci_langgraph_a2a_blueprint.clients.direct_agent_cli "quick demo" --sleep-seconds 0
```

Expected output shape:

```text
step_completed: step1 - step1 completed
step_completed: step2 - step2 completed
step_completed: step3 - step3 completed
agent_completed: agent completed
Final output: step3 processed: <LLM answer for "quick demo">
```

## Show State Snapshots

Use `--show-state` to print the current agent state after each streamed event:

```bash
python -m oci_langgraph_a2a_blueprint.clients.direct_agent_cli "inspect state" --sleep-seconds 0 --show-state
```

## Enable Step Logs

Use `--log-level INFO` to show the start and completion logs emitted by each step:

```bash
python -m oci_langgraph_a2a_blueprint.clients.direct_agent_cli "show logs" --sleep-seconds 0 --log-level INFO
```

## Options

```text
input_text              Text input passed to the sample LangGraph agent.
--sleep-seconds FLOAT   Simulated work duration for each step. Defaults to 1.0.
--log-level LEVEL       Python logging level. Defaults to WARNING.
--show-state            Print the current state snapshot after each event.
```
