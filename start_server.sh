#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SLEEP_SECONDS=${AGENT_STEP_SLEEP_SECONDS:-0}

usage() {
  cat <<'EOF'
Usage: ./start_server.sh [--sleep-seconds VALUE]

Start the Docker Compose A2A server.

Options:
  --sleep-seconds VALUE, -s VALUE
      Simulated duration for each sample LangGraph step.
      Defaults to AGENT_STEP_SLEEP_SECONDS or 0.
  --help, -h
      Show this help message.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --sleep-seconds|-s)
      if [ "$#" -lt 2 ]; then
        echo "Error: $1 requires a value." >&2
        exit 2
      fi
      SLEEP_SECONDS=$2
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

export AGENT_STEP_SLEEP_SECONDS=$SLEEP_SECONDS

cd "$SCRIPT_DIR"
docker compose up --build -d a2a-server
