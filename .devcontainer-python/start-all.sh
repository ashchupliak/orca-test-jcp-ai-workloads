#!/bin/bash
# Unified startup script for Python devcontainer
# Starts agent service, chat service, and IDE (code-server)

set -e

WORKSPACE_DIR="/workspaces/orca-test-jcp-ai-workloads"
LOG_FILE="/tmp/container-startup.log"

echo "[$(date)] ========================================" | tee -a "$LOG_FILE"
echo "[$(date)] Starting Python container services..." | tee -a "$LOG_FILE"
echo "[$(date)] ========================================" | tee -a "$LOG_FILE"

# Step 1: Start agent and chat services
echo "[$(date)] Step 1: Starting agent and chat services..." | tee -a "$LOG_FILE"
if [ -f "$WORKSPACE_DIR/common/start-services.sh" ]; then
    bash "$WORKSPACE_DIR/common/start-services.sh" >> "$LOG_FILE" 2>&1 &
    SERVICES_PID=$!
    echo "[$(date)] Services started with PID $SERVICES_PID" | tee -a "$LOG_FILE"
else
    echo "[$(date)] WARNING: start-services.sh not found" | tee -a "$LOG_FILE"
fi

# Wait a moment for services to initialize
sleep 3

# Step 2: Start IDE (code-server)
echo "[$(date)] Step 2: Starting IDE (code-server)..." | tee -a "$LOG_FILE"
if [ -f "$WORKSPACE_DIR/.devcontainer-python/start-ide.sh" ]; then
    # Start IDE in background (it already has its own background handling)
    bash "$WORKSPACE_DIR/.devcontainer-python/start-ide.sh" >> "$LOG_FILE" 2>&1 &
    IDE_PID=$!
    echo "[$(date)] IDE started with PID $IDE_PID" | tee -a "$LOG_FILE"
else
    echo "[$(date)] WARNING: start-ide.sh not found" | tee -a "$LOG_FILE"
fi

# Wait for services to be ready
echo "[$(date)] Waiting for services to be ready..." | tee -a "$LOG_FILE"
sleep 5

# Health checks
echo "[$(date)] Running health checks..." | tee -a "$LOG_FILE"

# Check agent service (port 8001)
if curl -s -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "[$(date)] ✓ Agent service (port 8001) is healthy" | tee -a "$LOG_FILE"
else
    echo "[$(date)] ✗ Agent service (port 8001) not responding" | tee -a "$LOG_FILE"
fi

# Check chat service (port 8000)
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "[$(date)] ✓ Chat service (port 8000) is healthy" | tee -a "$LOG_FILE"
else
    echo "[$(date)] ✗ Chat service (port 8000) not responding" | tee -a "$LOG_FILE"
fi

# Check IDE (port 8080)
if curl -s -f http://localhost:8080/healthz > /dev/null 2>&1; then
    echo "[$(date)] ✓ IDE (port 8080) is healthy" | tee -a "$LOG_FILE"
else
    echo "[$(date)] ✗ IDE (port 8080) not responding" | tee -a "$LOG_FILE"
fi

echo "[$(date)] ========================================" | tee -a "$LOG_FILE"
echo "[$(date)] Container startup complete!" | tee -a "$LOG_FILE"
echo "[$(date)] ========================================" | tee -a "$LOG_FILE"
echo "[$(date)] Services:" | tee -a "$LOG_FILE"
echo "[$(date)]   - Agent API: http://localhost:8001/health" | tee -a "$LOG_FILE"
echo "[$(date)]   - Chat API: http://localhost:8000/health" | tee -a "$LOG_FILE"
echo "[$(date)]   - IDE: http://localhost:8080" | tee -a "$LOG_FILE"
echo "[$(date)] Logs: tail -f $LOG_FILE" | tee -a "$LOG_FILE"

# Keep running (tail -f will be handled by start-ide.sh)
