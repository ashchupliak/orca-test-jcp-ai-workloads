#!/bin/bash
set -e

IDE_PORT="${IDE_PORT:-8080}"
WORKSPACE="${WORKSPACE:-/workspaces/orca-test-jcp-ai-workloads}"

echo "[$(date)] Starting code-server on port $IDE_PORT in foreground..."

# Start code-server in foreground to keep container alive
exec code-server \
    --bind-addr "0.0.0.0:$IDE_PORT" \
    --auth none \
    --disable-telemetry \
    --disable-update-check \
    "$WORKSPACE"
