#!/bin/bash
# Bulletproof startup script for unified service
# This script is designed to NEVER fail

set -e

# Detect workspace directory
if [ -d "/workspaces/orca-test-jcp-ai-workloads/common" ]; then
    WORKSPACE="/workspaces/orca-test-jcp-ai-workloads"
elif [ -d "/workspace/common" ]; then
    WORKSPACE="/workspace"
else
    echo "[WARNING] Cannot find workspace with common folder, using /workspace"
    WORKSPACE="/workspace"
fi

export WORKSPACE_ROOT="$WORKSPACE"

SERVICE_DIR="$WORKSPACE/common/unified-service"

echo "========================================"
echo "Unified Service Startup"
echo "========================================"
echo "Workspace: $WORKSPACE"
echo "Service: $SERVICE_DIR"
echo "========================================"

# Check if service directory exists
if [ ! -d "$SERVICE_DIR" ]; then
    echo "[ERROR] Service directory not found: $SERVICE_DIR"
    echo "[INFO] Services will not be available"
    exit 0  # Exit gracefully
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found"
    echo "[INFO] Services will not be available"
    exit 0  # Exit gracefully
fi

# Install dependencies if requirements.txt exists
if [ -f "$SERVICE_DIR/requirements.txt" ]; then
    echo "[INFO] Installing Python dependencies..."
    python3 -m pip install --quiet --no-cache-dir -r "$SERVICE_DIR/requirements.txt" 2>&1 | grep -v "Requirement already satisfied" || true
fi

# Start the unified service
echo "[INFO] Starting unified service..."
cd "$SERVICE_DIR"

# Run in background, but don't use nohup to avoid blocking postStartCommand
python3 app.py > /tmp/unified-service.log 2>&1 &

SERVICE_PID=$!
echo "[INFO] Unified service started with PID: $SERVICE_PID"

# Wait a moment for services to initialize
sleep 3

# Quick health check
echo "[INFO] Performing health checks..."

if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "[OK] Chat service (8000) is healthy"
else
    echo "[WARNING] Chat service (8000) not responding yet"
fi

if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
    echo "[OK] Agent service (8001) is healthy"
else
    echo "[WARNING] Agent service (8001) not responding yet"
fi

if curl -sf http://localhost:8080/healthz > /dev/null 2>&1; then
    echo "[OK] IDE service (8080) is healthy"
else
    echo "[INFO] IDE service (8080) starting (may take 30-60s)"
fi

echo "========================================"
echo "Unified service startup complete"
echo "Logs: tail -f /tmp/unified-service.log"
echo "========================================"

# Exit cleanly so postStartCommand completes
exit 0
