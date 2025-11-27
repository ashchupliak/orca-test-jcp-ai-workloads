#!/bin/bash
# Universal startup script for all devcontainers
# Starts chat service (8000), agent service (8001), and IDE (8080) if available

set -e

# Detect workspace path
if [ -d "/workspaces/orca-test-jcp-ai-workloads/common" ]; then
    WORKSPACE_DIR="/workspaces/orca-test-jcp-ai-workloads"
elif [ -d "/workspace/common" ]; then
    WORKSPACE_DIR="/workspace"
else
    echo "WARNING: Cannot find workspace directory with common folder"
    WORKSPACE_DIR="/workspace"
fi

LOG_FILE="/tmp/container-startup.log"

echo "[$(date)] ========================================" | tee -a "$LOG_FILE"
echo "[$(date)] Starting container services..." | tee -a "$LOG_FILE"
echo "[$(date)] Workspace: $WORKSPACE_DIR" | tee -a "$LOG_FILE"
echo "[$(date)] ========================================" | tee -a "$LOG_FILE"

# Step 1: Start chat and agent services
echo "[$(date)] Step 1: Starting chat and agent services..." | tee -a "$LOG_FILE"
if [ -f "$WORKSPACE_DIR/common/start-services.sh" ]; then
    bash "$WORKSPACE_DIR/common/start-services.sh" >> "$LOG_FILE" 2>&1 &
    SERVICES_PID=$!
    echo "[$(date)] Services started with PID $SERVICES_PID" | tee -a "$LOG_FILE"
else
    echo "[$(date)] WARNING: start-services.sh not found at $WORKSPACE_DIR/common/" | tee -a "$LOG_FILE"
fi

# Wait for services to initialize
sleep 5

# Step 2: Start IDE (code-server) if installed
echo "[$(date)] Step 2: Checking for code-server..." | tee -a "$LOG_FILE"
if command -v code-server &> /dev/null; then
    echo "[$(date)] Starting code-server IDE on port 8080..." | tee -a "$LOG_FILE"
    code-server \
        --bind-addr 0.0.0.0:8080 \
        --auth none \
        --disable-telemetry \
        --disable-update-check \
        --disable-workspace-trust \
        "$WORKSPACE_DIR" >> /tmp/code-server.log 2>&1 &
    CODE_SERVER_PID=$!
    echo "[$(date)] code-server started with PID $CODE_SERVER_PID" | tee -a "$LOG_FILE"

    # Wait for code-server to be ready
    for i in {1..30}; do
        if curl -s http://localhost:8080/healthz > /dev/null 2>&1; then
            echo "[$(date)] code-server is ready!" | tee -a "$LOG_FILE"
            break
        fi
        sleep 1
    done
else
    echo "[$(date)] code-server not installed, skipping IDE" | tee -a "$LOG_FILE"
fi

# Health checks
echo "[$(date)] Running health checks..." | tee -a "$LOG_FILE"

# Check chat service (port 8000)
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "[$(date)] ✓ Chat service (port 8000) is healthy" | tee -a "$LOG_FILE"
else
    echo "[$(date)] ✗ Chat service (port 8000) not responding" | tee -a "$LOG_FILE"
fi

# Check agent service (port 8001)
if curl -s -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "[$(date)] ✓ Agent service (port 8001) is healthy" | tee -a "$LOG_FILE"
else
    echo "[$(date)] ✗ Agent service (port 8001) not responding" | tee -a "$LOG_FILE"
fi

# Check IDE (port 8080)
if curl -s -f http://localhost:8080/healthz > /dev/null 2>&1; then
    echo "[$(date)] ✓ IDE (port 8080) is healthy" | tee -a "$LOG_FILE"
else
    echo "[$(date)] ✗ IDE (port 8080) not responding" | tee -a "$LOG_FILE"
fi

echo "[$(date)] ========================================" | tee -a "$LOG_FILE"
echo "[$(date)] Container startup complete!" | tee -a "$LOG_FILE"
echo "[$(date)] Logs: tail -f $LOG_FILE" | tee -a "$LOG_FILE"
echo "[$(date)] ========================================" | tee -a "$LOG_FILE"

# postStartCommand must exit cleanly - container is kept running by docker-compose or devcontainer
# Services are already running in the background
exit 0
