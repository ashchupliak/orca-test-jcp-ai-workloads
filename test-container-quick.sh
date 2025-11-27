#!/bin/bash
# Quick test script using correct orca-server API

TOKEN="eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXNlcnZpY2UiLCJ1c2VySWQiOiJ0ZXN0LXVzZXItaWQiLCJ1c2VyTmFtZSI6InRlc3QtdXNlciIsImlhdCI6MTc1NzUxMTI2MiwiZXhwIjoyMDcyODcxMjYyfQ.MQmTOPiBp22WKL476tn8o_97RzgoQcxY_-Gj35_9zyNW_7A7Np7Rqc_9TUa_AZSOub5o3WvS6K-eGVy91iCnug"
API_URL="https://orca-server-nightly.labs.jb.gg/api/environments"
REPO_URL="https://github.com/ashchupliak/orca-test-jcp-ai-workloads"

CONTAINER=${1:-python}

case $CONTAINER in
    python) DEVCONTAINER_PATH=".devcontainer-python" ;;
    javascript) DEVCONTAINER_PATH=".devcontainer-javascript" ;;
    java) DEVCONTAINER_PATH=".devcontainer-java" ;;
    go) DEVCONTAINER_PATH=".devcontainer-go" ;;
    rust) DEVCONTAINER_PATH=".devcontainer-rust" ;;
    ruby) DEVCONTAINER_PATH=".devcontainer-ruby" ;;
    php) DEVCONTAINER_PATH=".devcontainer-php" ;;
    dotnet) DEVCONTAINER_PATH=".devcontainer-dotnet" ;;
    agents) DEVCONTAINER_PATH=".devcontainer-agents" ;;
    ai-tools) DEVCONTAINER_PATH=".devcontainer-ai-tools" ;;
    databases) DEVCONTAINER_PATH=".devcontainer-databases" ;;
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
    *) echo "Unknown container: $CONTAINER"; exit 1 ;;
esac

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Testing: $CONTAINER ($DEVCONTAINER_PATH)"
echo ""

# Create environment
echo "Creating environment..."
CREATE_RESPONSE=$(curl -s -X POST "$API_URL" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"definition\": {
            \"type\": \"devcontainer\",
            \"git\": {
                \"repositories\": [{
                    \"cloneUrl\": \"$REPO_URL\",
                    \"ref\": \"main\"
                }]
            },
            \"workspaceFolder\": \"orca-test-jcp-ai-workloads\",
            \"config\": {
                \"type\": \"path\",
                \"path\": \"$DEVCONTAINER_PATH/devcontainer.json\"
            }
        }
    }")

ENV_ID=$(echo "$CREATE_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$ENV_ID" ]; then
    echo "❌ Failed to create environment"
    echo "Response: $CREATE_RESPONSE"
    exit 1
fi

echo "✅ Environment created: $ENV_ID"

# Wait for RUNNING
echo "Waiting for RUNNING status..."
MAX_WAIT=600
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    STATUS_RESPONSE=$(curl -s "$API_URL/$ENV_ID" -H "Authorization: Bearer $TOKEN")

    STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)

    if [ "$STATUS" = "Running" ]; then
        echo "✅ Environment RUNNING (${ELAPSED}s)"
        break
    elif [ "$STATUS" = "Failed" ]; then
        echo "❌ Environment FAILED"
        echo "$STATUS_RESPONSE"
        exit 1
    fi

    if [ $((ELAPSED % 30)) -eq 0 ] && [ $ELAPSED -gt 0 ]; then
        echo "... waiting (${ELAPSED}s, status: $STATUS)"
    fi

    sleep 10
    ELAPSED=$((ELAPSED + 10))
done

if [ "$STATUS" != "Running" ]; then
    echo "❌ Timeout"
    exit 1
fi

# Get hostname
HOSTNAME=$(echo "$STATUS_RESPONSE" | grep -o '"hostname":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "Hostname: $HOSTNAME"

# Wait for services
echo "Waiting 30s for services..."
sleep 30

# Test endpoints
echo ""
echo "Testing endpoints..."

# Chat
echo "  Chat (8000):"
CHAT_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${HOSTNAME}:8000/health" --max-time 10)
if [ "$CHAT_CODE" = "200" ]; then
    CHAT_BODY=$(curl -s "http://${HOSTNAME}:8000/health")
    echo "    ✅ HTTP 200 - $CHAT_BODY"
else
    echo "    ❌ HTTP $CHAT_CODE"
fi

# Agent
echo "  Agent (8001):"
AGENT_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${HOSTNAME}:8001/agent/health" --max-time 10)
if [ "$AGENT_CODE" = "200" ]; then
    AGENT_BODY=$(curl -s "http://${HOSTNAME}:8001/agent/health")
    echo "    ✅ HTTP 200 - $AGENT_BODY"
else
    echo "    ❌ HTTP $AGENT_CODE"
fi

# IDE
echo "  IDE (8080):"
IDE_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${HOSTNAME}:8080" --max-time 10)
if [ "$IDE_CODE" = "200" ]; then
    echo "    ✅ HTTP 200 - http://${HOSTNAME}:8080"
else
    echo "    ❌ HTTP $IDE_CODE"
fi

echo ""
echo "Environment ID: $ENV_ID"
echo "To delete: curl -X DELETE $API_URL/$ENV_ID -H \"Authorization: Bearer \$TOKEN\""
