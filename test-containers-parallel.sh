#!/bin/bash
# Test containers in parallel batches via facade API

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
    "lightweight:.devcontainer-lightweight-agent"
    "logs:.devcontainer-logs-testing"
    "mcp:.devcontainer-mcp"
    "override:.devcontainer-config-override"
    "override-alt:.devcontainer-config-override-alt"
    "base:.devcontainer-base"
    "default:.devcontainer"
)

mkdir -p test-results
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="test-results/$TIMESTAMP"
mkdir -p "$RESULTS_DIR"

echo "========================================"
echo "Testing Containers in Parallel Batches"
echo "========================================"
echo "Total containers: ${#CONTAINERS[@]}"
echo "Results directory: $RESULTS_DIR"
echo ""

# Test a single container
test_container() {
    local name=$1
    local path=$2
    local result_file="$RESULTS_DIR/${name}.log"

    {
        echo "========================================="
        echo "Testing: $name"
        echo "Path: $path"
        echo "Started: $(date)"
        echo "========================================="

        # Create environment
        echo "Creating environment..."
        CREATE_RESPONSE=$(curl -s -X POST "$FACADE_API/environments" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"name\": \"test-${name}-${TIMESTAMP}\",
                \"repositoryUrl\": \"$REPO_URL\",
                \"devcontainerPath\": \"$path\"
            }")

        ENV_ID=$(echo "$CREATE_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

        if [ -z "$ENV_ID" ]; then
            echo "❌ Failed to create environment"
            echo "Response: $CREATE_RESPONSE"
            echo "RESULT: FAILED"
            return 1
        fi

        echo "✅ Environment created: $ENV_ID"

        # Wait for RUNNING (max 10 minutes)
        echo "Waiting for RUNNING status..."
        local max_wait=600
        local elapsed=0
        local status=""

        while [ $elapsed -lt $max_wait ]; do
            STATUS_RESPONSE=$(curl -s -X GET "$FACADE_API/environments/$ENV_ID" \
                -H "Authorization: Bearer $TOKEN")

            status=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)

            if [ "$status" = "RUNNING" ]; then
                echo "✅ Environment RUNNING (took ${elapsed}s)"
                break
            elif [ "$status" = "FAILED" ] || [ "$status" = "STOPPED" ]; then
                echo "❌ Environment $status"
                echo "Response: $STATUS_RESPONSE"
                curl -s -X DELETE "$FACADE_API/environments/$ENV_ID" -H "Authorization: Bearer $TOKEN" > /dev/null
                echo "RESULT: FAILED"
                return 1
            fi

            if [ $((elapsed % 30)) -eq 0 ] && [ $elapsed -gt 0 ]; then
                echo "... waiting (${elapsed}s, status: $status)"
            fi

            sleep 10
            elapsed=$((elapsed + 10))
        done

        if [ "$status" != "RUNNING" ]; then
            echo "❌ Timeout waiting for RUNNING"
            curl -s -X DELETE "$FACADE_API/environments/$ENV_ID" -H "Authorization: Bearer $TOKEN" > /dev/null
            echo "RESULT: FAILED"
            return 1
        fi

        # Get hostname
        HOSTNAME=$(echo "$STATUS_RESPONSE" | grep -o '"hostname":"[^"]*"' | head -1 | cut -d'"' -f4)

        if [ -z "$HOSTNAME" ]; then
            echo "❌ Failed to get hostname"
            curl -s -X DELETE "$FACADE_API/environments/$ENV_ID" -H "Authorization: Bearer $TOKEN" > /dev/null
            echo "RESULT: FAILED"
            return 1
        fi

        echo "Hostname: $HOSTNAME"
        echo "Waiting 30s for services to fully start..."
        sleep 30

        # Test endpoints
        local all_passed=true

        echo ""
        echo "Testing endpoints..."

        # Chat endpoint
        echo "  Testing http://${HOSTNAME}:8000/health"
        CHAT_RESP=$(curl -s -w "\n%{http_code}" "http://${HOSTNAME}:8000/health" --max-time 10)
        CHAT_CODE=$(echo "$CHAT_RESP" | tail -1)
        CHAT_BODY=$(echo "$CHAT_RESP" | head -n -1)

        if [ "$CHAT_CODE" = "200" ]; then
            echo "    ✅ HTTP 200 - $CHAT_BODY"
        else
            echo "    ❌ HTTP $CHAT_CODE"
            all_passed=false
        fi

        # Agent endpoint
        echo "  Testing http://${HOSTNAME}:8001/agent/health"
        AGENT_RESP=$(curl -s -w "\n%{http_code}" "http://${HOSTNAME}:8001/agent/health" --max-time 10)
        AGENT_CODE=$(echo "$AGENT_RESP" | tail -1)
        AGENT_BODY=$(echo "$AGENT_RESP" | head -n -1)

        if [ "$AGENT_CODE" = "200" ]; then
            echo "    ✅ HTTP 200 - $AGENT_BODY"
        else
            echo "    ❌ HTTP $AGENT_CODE"
            all_passed=false
        fi

        # IDE endpoint
        echo "  Testing http://${HOSTNAME}:8080"
        IDE_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${HOSTNAME}:8080" --max-time 10)

        if [ "$IDE_CODE" = "200" ]; then
            echo "    ✅ HTTP 200 (IDE accessible)"
        else
            echo "    ❌ HTTP $IDE_CODE"
            all_passed=false
        fi

        # Cleanup
        echo ""
        echo "Deleting environment..."
        curl -s -X DELETE "$FACADE_API/environments/$ENV_ID" -H "Authorization: Bearer $TOKEN" > /dev/null

        echo "Completed: $(date)"

        if [ "$all_passed" = true ]; then
            echo "RESULT: PASSED ✅"
            return 0
        else
            echo "RESULT: FAILED ❌"
            return 1
        fi
    } > "$result_file" 2>&1

    # Return the result
    if grep -q "RESULT: PASSED" "$result_file"; then
        return 0
    else
        return 1
    fi
}

# Test containers in batches of 4
BATCH_SIZE=4
total=${#CONTAINERS[@]}
batch_num=1

for ((i=0; i<$total; i+=$BATCH_SIZE)); do
    echo ""
    echo "========================================="
    echo "Batch $batch_num (containers $((i+1))-$((i+BATCH_SIZE > total ? total : i+BATCH_SIZE)) of $total)"
    echo "========================================="

    batch_pids=()
    batch_names=()

    # Start batch
    for ((j=i; j<i+BATCH_SIZE && j<total; j++)); do
        IFS=':' read -r name path <<< "${CONTAINERS[$j]}"
        echo "Starting test for: $name"

        test_container "$name" "$path" &
        batch_pids+=($!)
        batch_names+=("$name")
    done

    # Wait for batch to complete
    echo ""
    echo "Waiting for batch to complete..."
    for idx in "${!batch_pids[@]}"; do
        pid=${batch_pids[$idx]}
        name=${batch_names[$idx]}

        wait $pid
        if [ $? -eq 0 ]; then
            echo "  ✅ $name completed successfully"
        else
            echo "  ❌ $name failed"
        fi
    done

    batch_num=$((batch_num + 1))
    echo ""
    echo "Batch completed. Waiting 10s before next batch..."
    sleep 10
done

# Collect results
echo ""
echo "========================================"
echo "FINAL SUMMARY"
echo "========================================"

PASSED=0
FAILED=0

for container in "${CONTAINERS[@]}"; do
    IFS=':' read -r name path <<< "$container"
    result_file="$RESULTS_DIR/${name}.log"

    if [ -f "$result_file" ]; then
        if grep -q "RESULT: PASSED" "$result_file"; then
            echo "✅ $name"
            PASSED=$((PASSED + 1))
        else
            echo "❌ $name"
            FAILED=$((FAILED + 1))
        fi
    else
        echo "❓ $name (no result file)"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "Total: $total"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""
echo "Detailed logs: $RESULTS_DIR/"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "✅ ALL CONTAINERS PASSED!"
    exit 0
else
    echo ""
    echo "❌ SOME CONTAINERS FAILED"
    echo "Check individual logs in $RESULTS_DIR/ for details"
    exit 1
fi
