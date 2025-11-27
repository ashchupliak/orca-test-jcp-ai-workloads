#!/bin/bash
# Test all 22 containers via facade API

TOKEN="eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3MzI3MzEyOTgsImV4cCI6MTczNTMyMzI5OCwic3ViIjoiNjQ3ZDZkNGUtOTVjMS00NjMyLWIzYWEtZjk1MDg0ODdjMzRhIn0.Me4L8wAZ9DJPi8BzrOb03HtJU_OZqgsBi26esFZ_a-V9FswsIGXwrp5jPNOnKdlHhgLuF3mphBg-yxXJKTJCqw"
FACADE_API="https://orca-lab-dev.i.aws.intellij.net/api/facade/v1"
REPO_URL="https://github.com/ashchupliak/orca-test-jcp-ai-workloads"

CONTAINERS=(
    "python:.devcontainer-python"
    "javascript:.devcontainer-javascript"
    "java:.devcontainer-java"
    "go:.devcontainer-go"
    "rust:.devcontainer-rust"
    "ruby:.devcontainer-ruby"
    "php:.devcontainer-php"
    "dotnet:.devcontainer-dotnet"
    "agents:.devcontainer-agents"
    "ai-tools:.devcontainer-ai-tools"
    "databases:.devcontainer-databases"
    "docker:.devcontainer-docker"
    "git:.devcontainer-git"
    "grazie:.devcontainer-grazie"
    "ide-test:.devcontainer-ide-test"
    "lightweight-agent:.devcontainer-lightweight-agent"
    "logs-testing:.devcontainer-logs-testing"
    "mcp:.devcontainer-mcp"
    "config-override:.devcontainer-config-override"
    "config-override-alt:.devcontainer-config-override-alt"
    "base:.devcontainer-base"
    "default:.devcontainer"
)

echo "========================================"
echo "Testing All Containers via Facade"
echo "========================================"
echo "Total containers to test: ${#CONTAINERS[@]}"
echo ""

# Create results directory
mkdir -p test-results
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="test-results/test_results_${TIMESTAMP}.log"

echo "Test started at: $(date)" | tee "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

PASSED=0
FAILED=0
declare -A ENV_IDS

# Function to create environment
create_environment() {
    local name=$1
    local devcontainer_path=$2

    echo "Creating environment: $name (path: $devcontainer_path)" | tee -a "$RESULTS_FILE"

    RESPONSE=$(curl -s -X POST "$FACADE_API/environments" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"test-${name}-${TIMESTAMP}\",
            \"repositoryUrl\": \"$REPO_URL\",
            \"devcontainerPath\": \"$devcontainer_path\"
        }")

    ENV_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

    if [ -z "$ENV_ID" ]; then
        echo "  ❌ Failed to create environment" | tee -a "$RESULTS_FILE"
        echo "  Response: $RESPONSE" | tee -a "$RESULTS_FILE"
        return 1
    fi

    echo "  ✅ Environment created with ID: $ENV_ID" | tee -a "$RESULTS_FILE"
    ENV_IDS[$name]=$ENV_ID
    return 0
}

# Function to wait for environment to be running
wait_for_running() {
    local name=$1
    local env_id=${ENV_IDS[$name]}
    local max_wait=600  # 10 minutes
    local elapsed=0

    echo "  Waiting for environment to be RUNNING..." | tee -a "$RESULTS_FILE"

    while [ $elapsed -lt $max_wait ]; do
        STATUS_RESPONSE=$(curl -s -X GET "$FACADE_API/environments/$env_id" \
            -H "Authorization: Bearer $TOKEN")

        STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)

        if [ "$STATUS" = "RUNNING" ]; then
            echo "  ✅ Environment is RUNNING (took ${elapsed}s)" | tee -a "$RESULTS_FILE"
            return 0
        elif [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "STOPPED" ]; then
            echo "  ❌ Environment failed with status: $STATUS" | tee -a "$RESULTS_FILE"
            echo "  Response: $STATUS_RESPONSE" | tee -a "$RESULTS_FILE"
            return 1
        fi

        if [ $((elapsed % 30)) -eq 0 ]; then
            echo "  ... still waiting (${elapsed}s elapsed, status: $STATUS)" | tee -a "$RESULTS_FILE"
        fi

        sleep 10
        elapsed=$((elapsed + 10))
    done

    echo "  ❌ Timeout waiting for environment to be RUNNING" | tee -a "$RESULTS_FILE"
    return 1
}

# Function to get environment hostname
get_hostname() {
    local name=$1
    local env_id=${ENV_IDS[$name]}

    ENV_RESPONSE=$(curl -s -X GET "$FACADE_API/environments/$env_id" \
        -H "Authorization: Bearer $TOKEN")

    HOSTNAME=$(echo "$ENV_RESPONSE" | grep -o '"hostname":"[^"]*"' | head -1 | cut -d'"' -f4)

    if [ -z "$HOSTNAME" ]; then
        echo "  ❌ Failed to get hostname" | tee -a "$RESULTS_FILE"
        return 1
    fi

    echo "$HOSTNAME"
    return 0
}

# Function to test endpoints
test_endpoints() {
    local name=$1
    local hostname=$2

    echo "  Testing endpoints for $hostname..." | tee -a "$RESULTS_FILE"

    local all_passed=true

    # Test chat health endpoint (port 8000)
    echo "    Testing http://${hostname}:8000/health" | tee -a "$RESULTS_FILE"
    CHAT_RESPONSE=$(curl -s -w "\n%{http_code}" "http://${hostname}:8000/health" --max-time 10)
    CHAT_CODE=$(echo "$CHAT_RESPONSE" | tail -1)
    CHAT_BODY=$(echo "$CHAT_RESPONSE" | head -n -1)

    if [ "$CHAT_CODE" = "200" ]; then
        echo "      ✅ Chat endpoint: HTTP 200" | tee -a "$RESULTS_FILE"
        echo "      Response: $CHAT_BODY" | tee -a "$RESULTS_FILE"
    else
        echo "      ❌ Chat endpoint: HTTP $CHAT_CODE" | tee -a "$RESULTS_FILE"
        all_passed=false
    fi

    # Test agent health endpoint (port 8001)
    echo "    Testing http://${hostname}:8001/agent/health" | tee -a "$RESULTS_FILE"
    AGENT_RESPONSE=$(curl -s -w "\n%{http_code}" "http://${hostname}:8001/agent/health" --max-time 10)
    AGENT_CODE=$(echo "$AGENT_RESPONSE" | tail -1)
    AGENT_BODY=$(echo "$AGENT_RESPONSE" | head -n -1)

    if [ "$AGENT_CODE" = "200" ]; then
        echo "      ✅ Agent endpoint: HTTP 200" | tee -a "$RESULTS_FILE"
        echo "      Response: $AGENT_BODY" | tee -a "$RESULTS_FILE"
    else
        echo "      ❌ Agent endpoint: HTTP $AGENT_CODE" | tee -a "$RESULTS_FILE"
        all_passed=false
    fi

    # Test IDE endpoint (port 8080)
    echo "    Testing http://${hostname}:8080" | tee -a "$RESULTS_FILE"
    IDE_RESPONSE=$(curl -s -w "\n%{http_code}" "http://${hostname}:8080" --max-time 10)
    IDE_CODE=$(echo "$IDE_RESPONSE" | tail -1)

    if [ "$IDE_CODE" = "200" ]; then
        echo "      ✅ IDE endpoint: HTTP 200" | tee -a "$RESULTS_FILE"
    else
        echo "      ❌ IDE endpoint: HTTP $IDE_CODE" | tee -a "$RESULTS_FILE"
        all_passed=false
    fi

    if [ "$all_passed" = true ]; then
        return 0
    else
        return 1
    fi
}

# Function to delete environment
delete_environment() {
    local name=$1
    local env_id=${ENV_IDS[$name]}

    echo "  Deleting environment $env_id..." | tee -a "$RESULTS_FILE"

    curl -s -X DELETE "$FACADE_API/environments/$env_id" \
        -H "Authorization: Bearer $TOKEN" > /dev/null

    echo "  ✅ Environment deleted" | tee -a "$RESULTS_FILE"
}

# Main test loop
for container in "${CONTAINERS[@]}"; do
    IFS=':' read -r name path <<< "$container"

    echo "" | tee -a "$RESULTS_FILE"
    echo "========================================" | tee -a "$RESULTS_FILE"
    echo "Testing: $name" | tee -a "$RESULTS_FILE"
    echo "========================================" | tee -a "$RESULTS_FILE"

    # Create environment
    if ! create_environment "$name" "$path"; then
        echo "❌ $name: Failed to create environment" | tee -a "$RESULTS_FILE"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Wait for running
    if ! wait_for_running "$name"; then
        echo "❌ $name: Failed to reach RUNNING state" | tee -a "$RESULTS_FILE"
        FAILED=$((FAILED + 1))
        delete_environment "$name"
        continue
    fi

    # Get hostname
    HOSTNAME=$(get_hostname "$name")
    if [ $? -ne 0 ]; then
        echo "❌ $name: Failed to get hostname" | tee -a "$RESULTS_FILE"
        FAILED=$((FAILED + 1))
        delete_environment "$name"
        continue
    fi

    echo "  Hostname: $HOSTNAME" | tee -a "$RESULTS_FILE"

    # Wait a bit for services to fully start
    echo "  Waiting 30s for services to fully start..." | tee -a "$RESULTS_FILE"
    sleep 30

    # Test endpoints
    if test_endpoints "$name" "$HOSTNAME"; then
        echo "✅ $name: ALL TESTS PASSED" | tee -a "$RESULTS_FILE"
        PASSED=$((PASSED + 1))
    else
        echo "❌ $name: SOME TESTS FAILED" | tee -a "$RESULTS_FILE"
        FAILED=$((FAILED + 1))
    fi

    # Delete environment
    delete_environment "$name"

    # Small delay between tests
    sleep 5
done

# Print summary
echo "" | tee -a "$RESULTS_FILE"
echo "========================================" | tee -a "$RESULTS_FILE"
echo "TEST SUMMARY" | tee -a "$RESULTS_FILE"
echo "========================================" | tee -a "$RESULTS_FILE"
echo "Total containers tested: ${#CONTAINERS[@]}" | tee -a "$RESULTS_FILE"
echo "Passed: $PASSED" | tee -a "$RESULTS_FILE"
echo "Failed: $FAILED" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"
echo "Test completed at: $(date)" | tee -a "$RESULTS_FILE"
echo "Results saved to: $RESULTS_FILE" | tee -a "$RESULTS_FILE"

if [ $FAILED -eq 0 ]; then
    echo "" | tee -a "$RESULTS_FILE"
    echo "✅ ALL CONTAINERS PASSED!" | tee -a "$RESULTS_FILE"
    exit 0
else
    echo "" | tee -a "$RESULTS_FILE"
    echo "❌ SOME CONTAINERS FAILED" | tee -a "$RESULTS_FILE"
    exit 1
fi
