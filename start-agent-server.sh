#!/bin/bash
# Startup script for lightweight agent server

set -e

echo "🚀 Starting lightweight agent server..."
echo "   Workspace: ${WORKSPACE_ROOT:-/workspace/orca-test-jcp-ai-workloads}"
echo "   Port: 35697"
echo "   Log: /tmp/agent-server.log"

# Start the server
exec python /workspace/orca-test-jcp-ai-workloads/lightweight_agent_server.py \
  --port 35697 \
  --workspace "${WORKSPACE_ROOT:-/workspace/orca-test-jcp-ai-workloads}" \
  >> /tmp/agent-server.log 2>&1
