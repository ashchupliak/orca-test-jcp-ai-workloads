#!/bin/bash
# Quick startup script - just start services, no waiting
set -e

WORKSPACE_DIR="/workspaces/orca-test-jcp-ai-workloads"
LOG_FILE="/tmp/container-startup.log"

echo "[$(date)] Starting services..." > "$LOG_FILE"

# Start agent and chat services
if [ -f "$WORKSPACE_DIR/common/start-services.sh" ]; then
    bash "$WORKSPACE_DIR/common/start-services.sh" >> "$LOG_FILE" 2>&1 &
    echo "[$(date)] Started agent/chat services" >> "$LOG_FILE"
fi

# Start IDE (code-server)
if [ -f "$WORKSPACE_DIR/.devcontainer-python/start-ide.sh" ]; then
    bash "$WORKSPACE_DIR/.devcontainer-python/start-ide.sh" >> "$LOG_FILE" 2>&1 &
    echo "[$(date)] Started IDE" >> "$LOG_FILE"
fi

echo "[$(date)] Services starting in background. Check $LOG_FILE for details." >> "$LOG_FILE"
