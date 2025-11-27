#!/bin/bash
# Universal startup script for all devcontainers
# Starts unified Node.js service (ports 8000, 8001) and IDE (8080)

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

# Step 1: Install Node.js dependencies for unified service
echo "[$(date)] Step 1: Installing unified service dependencies..." | tee -a "$LOG_FILE"
if [ -f "$WORKSPACE_DIR/common/unified-service/package.json" ]; then
    cd "$WORKSPACE_DIR/common/unified-service"
    if command -v npm &> /dev/null; then
        npm install --silent >> "$LOG_FILE" 2>&1 || echo "Warning: npm install failed" | tee -a "$LOG_FILE"
    else
        echo "WARNING: npm not found, cannot install dependencies" | tee -a "$LOG_FILE"
    fi
else
    echo "WARNING: unified-service/package.json not found" | tee -a "$LOG_FILE"
fi

# Step 2: Start unified Node.js service (ports 8000 and 8001)
echo "[$(date)] Step 2: Starting unified Node.js service..." | tee -a "$LOG_FILE"
if [ -f "$WORKSPACE_DIR/common/unified-service/server.js" ]; then
    cd "$WORKSPACE_DIR/common/unified-service"
    if command -v node &> /dev/null; then
        node server.js >> "$LOG_FILE" 2>&1 &
        SERVICE_PID=$!
        echo "[$(date)] Unified service started with PID $SERVICE_PID" | tee -a "$LOG_FILE"
    else
        echo "ERROR: Node.js not found, cannot start unified service" | tee -a "$LOG_FILE"
    fi
else
    echo "ERROR: unified-service/server.js not found" | tee -a "$LOG_FILE"
fi

# Wait for services to initialize
sleep 5

# Step 3: Start IDE (code-server) if installed
echo "[$(date)] Step 3: Checking for code-server..." | tee -a "$LOG_FILE"
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

# postStartCommand must exit cleanly - container is kept running by devcontainer
exit 0
