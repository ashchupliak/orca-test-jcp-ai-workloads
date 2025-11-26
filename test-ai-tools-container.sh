#!/bin/bash
# Test script for ai-tools container via facade API
# Usage: ./test-ai-tools-container.sh YOUR_JWT_TOKEN

set -e

TOKEN="${1:-}"
BASE_URL="https://orca-server-nightly.labs.jb.gg"
REPO_URL="https://github.com/ashchupliak/orca-test-jcp-ai-workloads"

if [ -z "$TOKEN" ]; then
    echo "Usage: $0 <JWT_TOKEN>"
    echo ""
    echo "Get your token from 1Password 'Spaceport tests' vault:"
    echo "  op://Spaceport tests/Toolbox Test Nightly Admin API Token/password"
    exit 1
fi

echo "=== Testing ai-tools Container via Facade ==="
echo "Base URL: $BASE_URL"
echo "Repository: $REPO_URL"
echo ""

# 1. Create environment
echo ">>> Creating ai-tools environment..."
CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/environments" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "definition": {
            "type": "devcontainer",
            "git": {
                "repositories": [{
                    "cloneUrl": "'"$REPO_URL"'",
                    "ref": "main"
                }]
            },
            "env": [],
            "workspaceFolder": "orca-test-jcp-ai-workloads",
            "config": {
                "type": "path",
                "path": "orca-test-jcp-ai-workloads/.devcontainer-ai-tools/devcontainer.json"
            }
        }
    }')

ENV_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')
if [ "$ENV_ID" == "null" ] || [ -z "$ENV_ID" ]; then
    echo "ERROR: Failed to create environment"
    echo "Response: $CREATE_RESPONSE"
    exit 1
fi

echo "Environment created: $ENV_ID"
echo ""

# 2. Wait for environment to start
echo ">>> Waiting for environment to start..."
MAX_WAIT=180
WAIT_COUNT=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    STATUS_RESPONSE=$(curl -s "$BASE_URL/api/environments/$ENV_ID" \
        -H "Authorization: Bearer $TOKEN")

    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
    echo "  Status: $STATUS (${WAIT_COUNT}s / ${MAX_WAIT}s)"

    if [ "$STATUS" == "RUNNING" ]; then
        echo "Environment is RUNNING!"
        break
    elif [ "$STATUS" == "STOPPED" ] || [ "$STATUS" == "ERROR" ]; then
        echo "ERROR: Environment failed to start (status: $STATUS)"
        echo ""
        echo "=== Getting logs ==="
        curl -s "$BASE_URL/api/environments/$ENV_ID/logs" \
            -H "Authorization: Bearer $TOKEN" | jq -r '.logs // .message // .'
        exit 1
    fi

    sleep 5
    WAIT_COUNT=$((WAIT_COUNT + 5))
done

if [ "$STATUS" != "RUNNING" ]; then
    echo "ERROR: Timeout waiting for environment to start"
    exit 1
fi

echo ""

# 3. Get environment details
echo ">>> Environment details:"
curl -s "$BASE_URL/api/environments/$ENV_ID" \
    -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

# 4. Get exposed ports info
echo ">>> Checking exposed ports:"
EXPOSED_PORTS=$(curl -s "$BASE_URL/api/environments/$ENV_ID" \
    -H "Authorization: Bearer $TOKEN" | jq -r '.exposedPorts // empty')
echo "$EXPOSED_PORTS"
echo ""

# 5. Get worker logs
echo ">>> Worker logs (last 50 lines):"
curl -s "$BASE_URL/api/environments/$ENV_ID/logs?tail=50" \
    -H "Authorization: Bearer $TOKEN" | jq -r '.logs[]? // .message // .'
echo ""

# 6. Test health endpoints via proxy (if available)
PROXY_HOST=$(curl -s "$BASE_URL/api/environments/$ENV_ID" \
    -H "Authorization: Bearer $TOKEN" | jq -r '.exposedPorts["8000"]?.host // empty')

if [ -n "$PROXY_HOST" ]; then
    echo ">>> Testing health endpoint on port 8000:"
    echo "   Proxy host: $PROXY_HOST"
    HEALTH_RESPONSE=$(curl -s "https://${PROXY_HOST}/health" 2>/dev/null || echo "Connection failed")
    echo "   Response: $HEALTH_RESPONSE"
    echo ""
fi

PROXY_HOST_8001=$(curl -s "$BASE_URL/api/environments/$ENV_ID" \
    -H "Authorization: Bearer $TOKEN" | jq -r '.exposedPorts["8001"]?.host // empty')

if [ -n "$PROXY_HOST_8001" ]; then
    echo ">>> Testing health endpoint on port 8001:"
    echo "   Proxy host: $PROXY_HOST_8001"
    HEALTH_RESPONSE=$(curl -s "https://${PROXY_HOST_8001}/health" 2>/dev/null || echo "Connection failed")
    echo "   Response: $HEALTH_RESPONSE"
    echo ""
fi

# 7. Cleanup - terminate environment
echo ">>> Terminating environment..."
curl -s -X POST "$BASE_URL/api/environments/$ENV_ID/terminate" \
    -H "Authorization: Bearer $TOKEN" | jq '.'

echo ""
echo "=== Test Complete ==="
echo "Environment ID: $ENV_ID"
echo ""
echo "To check logs again:"
echo "  curl -s '$BASE_URL/api/environments/$ENV_ID/logs' -H 'Authorization: Bearer \$TOKEN' | jq '.'"
