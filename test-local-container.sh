#!/bin/bash
# Local Container Test - Verify everything works BEFORE deploying to facade
# Tests: networking, code-server access, agent service access

set -e

echo "=========================================="
echo "Local Container Test"
echo "=========================================="
echo ""

# Cleanup previous test containers
echo "[Cleanup] Removing old test containers..."
docker rm -f orca-test-local 2>/dev/null || true
echo ""

# Step 1: Build and run Python devcontainer locally
echo "[1/7] Building Python devcontainer locally..."
cd "$(dirname "$0")"

CONTAINER_NAME="orca-test-local"
IMAGE_NAME="orca-test-python:local"

# Build from Python devcontainer
docker build -t "$IMAGE_NAME" \
  -f - . <<'DOCKERFILE'
FROM mcr.microsoft.com/devcontainers/python:3.11

# Install git
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# Copy workspace
WORKDIR /workspaces/orca-test-jcp-ai-workloads
COPY . .

# Install dependencies (same as postCreateCommand)
RUN pip install --no-cache-dir requests flask pytest flask-cors && \
    curl -fsSL https://code-server.dev/install.sh | sh

# Set environment variables
ENV PYTHONPATH=/workspaces/orca-test-jcp-ai-workloads
ENV TEST_MODE=devcontainer
ENV CONTAINER_NAME=python

# Expose ports
EXPOSE 8000 8001 8080

# Start services (same as postStartCommand)
CMD ["bash", "/workspaces/orca-test-jcp-ai-workloads/.devcontainer-python/start-all.sh"]
DOCKERFILE

echo "✓ Image built: $IMAGE_NAME"
echo ""

# Step 2: Run container with port mappings
echo "[2/7] Running container with port mappings..."
docker run -d \
  --name "$CONTAINER_NAME" \
  -p 18000:8000 \
  -p 18001:8001 \
  -p 18080:8080 \
  "$IMAGE_NAME"

echo "✓ Container started: $CONTAINER_NAME"
echo "  Ports: 18000 (chat), 18001 (agent), 18080 (IDE)"
echo ""

# Step 3: Wait for services to start
echo "[3/7] Waiting for services to start (60 seconds)..."
sleep 60
echo ""

# Step 4: Test external connectivity FROM INSIDE container
echo "[4/7] Testing external connectivity from inside container..."
echo ""

NETWORK_TEST=$(docker exec "$CONTAINER_NAME" bash -c '
echo "=== Network Tests ==="

# DNS
echo "[DNS] Testing nslookup google.com..."
if nslookup google.com > /dev/null 2>&1; then
  echo "✓ DNS works"
else
  echo "✗ DNS FAILED"
fi

# Internet
echo "[Internet] Testing curl https://google.com..."
if curl -s --connect-timeout 5 https://google.com > /dev/null 2>&1; then
  echo "✓ Internet works"
else
  echo "✗ Internet FAILED"
fi

# Grazie API
echo "[Grazie] Testing api.stgn.jetbrains.ai..."
RESPONSE=$(curl -s -w "\nHTTP:%{http_code}" --connect-timeout 10 https://api.stgn.jetbrains.ai/user/v5/llm/anthropic/v1/messages 2>&1 || echo "HTTP:000")
CODE=$(echo "$RESPONSE" | grep "HTTP:" | cut -d: -f2)
if [ "$CODE" = "401" ] || [ "$CODE" = "403" ] || [ "$CODE" = "400" ]; then
  echo "✓ Grazie API reachable (HTTP $CODE - auth required)"
elif [ "$CODE" = "000" ]; then
  echo "✗ Grazie API UNREACHABLE"
else
  echo "⚠ Grazie API returned HTTP $CODE"
fi

# GitHub
echo "[GitHub] Testing github.com..."
if curl -s --connect-timeout 5 https://github.com > /dev/null 2>&1; then
  echo "✓ GitHub reachable"
else
  echo "✗ GitHub FAILED"
fi

echo ""
')

echo "$NETWORK_TEST"

# Step 5: Test chat service FROM HOST
echo "[5/7] Testing chat service (port 8000) from host..."
CHAT_RESPONSE=$(curl -s --connect-timeout 5 http://localhost:18000/health 2>&1 || echo "FAILED")
if echo "$CHAT_RESPONSE" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
  echo "✓ Chat service reachable from host"
  echo "  Response: $(echo $CHAT_RESPONSE | jq -c .)"
else
  echo "✗ Chat service NOT reachable from host"
  echo "  Response: $CHAT_RESPONSE"
fi
echo ""

# Step 6: Test agent service FROM HOST
echo "[6/7] Testing agent service (port 8001) from host..."
AGENT_RESPONSE=$(curl -s --connect-timeout 5 http://localhost:18001/health 2>&1 || echo "FAILED")
if echo "$AGENT_RESPONSE" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
  echo "✓ Agent service reachable from host"
  echo "  Response: $(echo $AGENT_RESPONSE | jq -c .)"
else
  echo "✗ Agent service NOT reachable from host"
  echo "  Response: $AGENT_RESPONSE"
fi
echo ""

# Step 7: Test code-server FROM HOST
echo "[7/7] Testing code-server (port 8080) from host..."
IDE_RESPONSE=$(curl -s --connect-timeout 5 http://localhost:18080/healthz 2>&1 || echo "FAILED")
if echo "$IDE_RESPONSE" | grep -q "ok\|OK\|healthy" 2>/dev/null; then
  echo "✓ Code-server reachable from host"
  echo "  Response: $IDE_RESPONSE"
else
  echo "⚠ Code-server responded but may still be starting"
  echo "  Response: $IDE_RESPONSE"
  echo "  Try: open http://localhost:18080 in browser"
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "Services running in container: $CONTAINER_NAME"
echo ""
echo "Access from your machine:"
echo "  Chat:  http://localhost:18000/health"
echo "  Agent: http://localhost:18001/health"
echo "  IDE:   http://localhost:18080"
echo ""
echo "To check logs:"
echo "  docker logs $CONTAINER_NAME"
echo ""
echo "To exec into container:"
echo "  docker exec -it $CONTAINER_NAME bash"
echo ""
echo "To stop and remove:"
echo "  docker rm -f $CONTAINER_NAME"
echo ""
echo "=========================================="

# Keep container running for manual testing
echo ""
echo "Container is running. Press Ctrl+C to stop, or run:"
echo "  docker rm -f $CONTAINER_NAME"
echo ""
