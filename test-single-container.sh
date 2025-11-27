#!/bin/bash
# Test a single container via facade API
# Usage: ./test-single-container.sh <container-name>
# Example: ./test-single-container.sh python

if [ $# -eq 0 ]; then
    echo "Usage: $0 <container-name>"
    echo "Available containers: python, javascript, java, go, rust, ruby, php, dotnet, agents, ai-tools, databases, docker, git, grazie, ide-test, lightweight, logs, mcp, override, override-alt, base, default"
    exit 1
fi

CONTAINER_NAME=$1
TOKEN="${ORCA_TOKEN:-eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3MzI3MzEyOTgsImV4cCI6MTczNTMyMzI5OCwic3ViIjoiNjQ3ZDZkNGUtOTVjMS00NjMyLWIzYWEtZjk1MDg0ODdjMzRhIn0.Me4L8wAZ9DJPi8BzrOb03HtJU_OZqgsBi26esFZ_a-V9FswsIGXwrp5jPNOnKdlHhgLuF3mphBg-yxXJKTJCqw}"
FACADE_API="https://orca-lab-dev.i.aws.intellij.net/api/facade/v1"
REPO_URL="https://github.com/ashchupliak/orca-test-jcp-ai-workloads"

# Map container names to devcontainer paths
case $CONTAINER_NAME in
    python) DEVCONTAINER_PATH=".devcontainer-python" ;;
    javascript|js) DEVCONTAINER_PATH=".devcontainer-javascript" ;;
    java) DEVCONTAINER_PATH=".devcontainer-java" ;;
    go|golang) DEVCONTAINER_PATH=".devcontainer-go" ;;
    rust) DEVCONTAINER_PATH=".devcontainer-rust" ;;
    ruby|rb) DEVCONTAINER_PATH=".devcontainer-ruby" ;;
    php) DEVCONTAINER_PATH=".devcontainer-php" ;;
    dotnet|csharp) DEVCONTAINER_PATH=".devcontainer-dotnet" ;;
    agents) DEVCONTAINER_PATH=".devcontainer-agents" ;;
    ai-tools) DEVCONTAINER_PATH=".devcontainer-ai-tools" ;;
    databases|db) DEVCONTAINER_PATH=".devcontainer-databases" ;;
    docker) DEVCONTAINER_PATH=".devcontainer-docker" ;;
    git) DEVCONTAINER_PATH=".devcontainer-git" ;;
    grazie) DEVCONTAINER_PATH=".devcontainer-grazie" ;;
    ide-test) DEVCONTAINER_PATH=".devcontainer-ide-test" ;;
    lightweight) DEVCONTAINER_PATH=".devcontainer-lightweight-agent" ;;
    logs) DEVCONTAINER_PATH=".devcontainer-logs-testing" ;;
    mcp) DEVCONTAINER_PATH=".devcontainer-mcp" ;;
    override) DEVCONTAINER_PATH=".devcontainer-config-override" ;;
    override-alt) DEVCONTAINER_PATH=".devcontainer-config-override-alt" ;;
    base) DEVCONTAINER_PATH=".devcontainer-base" ;;
    default) DEVCONTAINER_PATH=".devcontainer" ;;
    *)
        echo "Unknown container: $CONTAINER_NAME"
        exit 1
        ;;
esac

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ENV_NAME="test-${CONTAINER_NAME}-${TIMESTAMP}"

echo "========================================="
echo "Testing Container: $CONTAINER_NAME"
echo "========================================="
echo "Devcontainer path: $DEVCONTAINER_PATH"
echo "Environment name: $ENV_NAME"
echo ""

# Create environment
echo "Step 1: Creating environment..."
CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$FACADE_API/environments" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"$ENV_NAME\",
        \"repositoryUrl\": \"$REPO_URL\",
        \"devcontainerPath\": \"$DEVCONTAINER_PATH\"
    }")

HTTP_CODE=$(echo "$CREATE_RESPONSE" | tail -1)
RESPONSE_BODY=$(echo "$CREATE_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "201" ]; then
    echo "❌ Failed to create environment (HTTP $HTTP_CODE)"
    echo "Response: $RESPONSE_BODY"
    exit 1
fi

ENV_ID=$(echo "$RESPONSE_BODY" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$ENV_ID" ]; then
    echo "❌ Failed to extract environment ID"
    echo "Response: $RESPONSE_BODY"
    exit 1
fi

echo "✅ Environment created: $ENV_ID"
echo ""

# Wait for RUNNING
echo "Step 2: Waiting for RUNNING status..."
MAX_WAIT=600
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    STATUS_RESPONSE=$(curl -s "$FACADE_API/environments/$ENV_ID" \
        -H "Authorization: Bearer $TOKEN")

    STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
    HOSTNAME=$(echo "$STATUS_RESPONSE" | grep -o '"hostname":"[^"]*"' | head -1 | cut -d'"' -f4)

    if [ "$STATUS" = "RUNNING" ]; then
        echo "✅ Environment is RUNNING (took ${ELAPSED}s)"
        echo "Hostname: $HOSTNAME"
        break
    elif [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "STOPPED" ]; then
        echo "❌ Environment $STATUS"
        echo "Response: $STATUS_RESPONSE"
        curl -s -X DELETE "$FACADE_API/environments/$ENV_ID" -H "Authorization: Bearer $TOKEN" > /dev/null
        exit 1
    fi

    if [ $((ELAPSED % 30)) -eq 0 ] && [ $ELAPSED -gt 0 ]; then
        echo "... still waiting (${ELAPSED}s, status: $STATUS)"
    fi

    sleep 10
    ELAPSED=$((ELAPSED + 10))
done

if [ "$STATUS" != "RUNNING" ]; then
    echo "❌ Timeout waiting for RUNNING"
    curl -s -X DELETE "$FACADE_API/environments/$ENV_ID" -H "Authorization: Bearer $TOKEN" > /dev/null
    exit 1
fi

echo ""
echo "Step 3: Waiting for services to start (30s)..."
sleep 30

# Test endpoints
echo ""
echo "Step 4: Testing endpoints..."

ALL_PASSED=true

# Chat endpoint
echo "  Testing http://${HOSTNAME}:8000/health"
CHAT_RESP=$(curl -s -w "\n%{http_code}" "http://${HOSTNAME}:8000/health" --max-time 10)
CHAT_CODE=$(echo "$CHAT_RESP" | tail -1)
CHAT_BODY=$(echo "$CHAT_RESP" | head -n -1)

if [ "$CHAT_CODE" = "200" ]; then
    echo "    ✅ HTTP 200"
    echo "    Response: $CHAT_BODY"
else
    echo "    ❌ HTTP $CHAT_CODE"
    ALL_PASSED=false
fi

# Agent endpoint
echo "  Testing http://${HOSTNAME}:8001/agent/health"
AGENT_RESP=$(curl -s -w "\n%{http_code}" "http://${HOSTNAME}:8001/agent/health" --max-time 10)
AGENT_CODE=$(echo "$AGENT_RESP" | tail -1)
AGENT_BODY=$(echo "$AGENT_RESP" | head -n -1)

if [ "$AGENT_CODE" = "200" ]; then
    echo "    ✅ HTTP 200"
    echo "    Response: $AGENT_BODY"
else
    echo "    ❌ HTTP $AGENT_CODE"
    ALL_PASSED=false
fi

# IDE endpoint
echo "  Testing http://${HOSTNAME}:8080"
IDE_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${HOSTNAME}:8080" --max-time 10)

if [ "$IDE_CODE" = "200" ]; then
    echo "    ✅ HTTP 200 (IDE accessible)"
    echo "    URL: http://${HOSTNAME}:8080"
else
    echo "    ❌ HTTP $IDE_CODE"
    ALL_PASSED=false
fi

echo ""
echo "Step 5: Cleanup..."
read -p "Delete environment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    curl -s -X DELETE "$FACADE_API/environments/$ENV_ID" -H "Authorization: Bearer $TOKEN" > /dev/null
    echo "✅ Environment deleted"
else
    echo "Environment kept: $ENV_ID"
    echo "Hostname: $HOSTNAME"
    echo "To delete later: curl -X DELETE $FACADE_API/environments/$ENV_ID -H \"Authorization: Bearer \$TOKEN\""
fi

echo ""
echo "========================================="
if [ "$ALL_PASSED" = true ]; then
    echo "✅ ALL TESTS PASSED"
    exit 0
else
    echo "❌ SOME TESTS FAILED"
    exit 1
fi
