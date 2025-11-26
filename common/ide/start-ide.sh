#!/bin/bash
set -e

IDE_PORT="${IDE_PORT:-8080}"
WORKSPACE="${WORKSPACE:-/workspaces/orca-test-jcp-ai-workloads}"

echo "[$(date)] Starting code-server on port $IDE_PORT..."

# Start code-server in background
nohup code-server \
    --bind-addr "0.0.0.0:$IDE_PORT" \
    --auth none \
    --disable-telemetry \
    --disable-update-check \
    "$WORKSPACE" > /tmp/code-server.log 2>&1 &

CODE_SERVER_PID=$!
echo "[$(date)] code-server started with PID $CODE_SERVER_PID"

# Wait for health check
for i in {1..30}; do
    if curl -s "http://localhost:$IDE_PORT/healthz" > /dev/null 2>&1; then
        echo "[$(date)] code-server is ready!"
        exit 0
    fi
    sleep 1
done

echo "[$(date)] WARNING: code-server health check timeout"
