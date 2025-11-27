#!/bin/bash
set -e

echo "[$(date)] Starting code-server IDE..."

# Wait a moment for system to be ready
sleep 2

# Start code-server
code-server \
    --bind-addr 0.0.0.0:8080 \
    --auth none \
    --disable-telemetry \
    --disable-update-check \
    --disable-workspace-trust \
    /workspaces/orca-test-jcp-ai-workloads &

CODE_SERVER_PID=$!
echo "[$(date)] code-server started with PID $CODE_SERVER_PID"

# Wait for code-server to be ready
for i in {1..30}; do
    if curl -s http://localhost:8080/healthz > /dev/null 2>&1; then
        echo "[$(date)] code-server is ready and healthy!"
        break
    fi
    sleep 1
done

# Keep script running (container needs a foreground process)
tail -f /dev/null
