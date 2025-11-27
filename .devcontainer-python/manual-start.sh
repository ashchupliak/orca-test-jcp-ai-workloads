#!/bin/bash
# Manual startup script - run this after container is created
# Usage: bash /workspaces/orca-test-jcp-ai-workloads/.devcontainer-python/manual-start.sh

set -e

WORKSPACE_DIR="/workspaces/orca-test-jcp-ai-workloads"

echo "=========================================="
echo "Starting Services Manually"
echo "=========================================="

# Start agent and chat services
if [ -f "$WORKSPACE_DIR/common/start-services.sh" ]; then
    echo "Starting agent and chat services..."
    bash "$WORKSPACE_DIR/common/start-services.sh" &
    echo "Started agent/chat services (PID: $!)"
else
    echo "ERROR: start-services.sh not found at $WORKSPACE_DIR/common/start-services.sh"
fi

# Start IDE (code-server)
if [ -f "$WORKSPACE_DIR/.devcontainer-python/start-ide.sh" ]; then
    echo "Starting IDE (code-server)..."
    bash "$WORKSPACE_DIR/.devcontainer-python/start-ide.sh" &
    echo "Started IDE (PID: $!)"
else
    echo "WARNING: start-ide.sh not found"
fi

echo ""
echo "Waiting 10 seconds for services to start..."
sleep 10

echo ""
echo "=========================================="
echo "Service Status"
echo "=========================================="

# Check agent service
if curl -s -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "✓ Agent service (port 8001) is healthy"
else
    echo "✗ Agent service (port 8001) not responding"
fi

# Check chat service
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Chat service (port 8000) is healthy"
else
    echo "✗ Chat service (port 8000) not responding"
fi

# Check IDE
if curl -s -f http://localhost:8080/healthz > /dev/null 2>&1; then
    echo "✓ IDE (port 8080) is healthy"
else
    echo "✗ IDE (port 8080) not responding"
fi

echo ""
echo "=========================================="
echo "Services Started!"
echo "=========================================="
echo "  Agent API: http://localhost:8001/health"
echo "  Chat API: http://localhost:8000/health"
echo "  IDE: http://localhost:8080"
echo ""
