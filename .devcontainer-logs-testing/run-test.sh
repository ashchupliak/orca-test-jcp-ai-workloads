#!/bin/bash
# Test runner script for logs testing
# This script runs the test specified by TEST_SCRIPT environment variable
# The output goes to stdout/stderr which will be captured by orca-worker logs

set -e

# Default delay before starting the test (allows container to fully initialize)
STARTUP_DELAY="${STARTUP_DELAY:-5}"

echo "[TEST-RUNNER] Starting test runner..."
echo "[TEST-RUNNER] Waiting ${STARTUP_DELAY} seconds for container initialization..."
sleep "$STARTUP_DELAY"

# Check if TEST_SCRIPT is set, default to success test
if [ -z "$TEST_SCRIPT" ]; then
    echo "[TEST-RUNNER] TEST_SCRIPT not set, using default: test_logs_success.py"
    TEST_SCRIPT="test_logs_success.py"
fi

# Full path to test script - try workspace mount first, fallback to built-in tests
if [ -f "/workspaces/orca-test-jcp-ai-workloads/tests/11-logs-testing/$TEST_SCRIPT" ]; then
    TEST_PATH="/workspaces/orca-test-jcp-ai-workloads/tests/11-logs-testing/$TEST_SCRIPT"
elif [ -f "/opt/logs-testing/tests/$TEST_SCRIPT" ]; then
    TEST_PATH="/opt/logs-testing/tests/$TEST_SCRIPT"
else
    echo "[TEST-RUNNER] ERROR: Test script not found: $TEST_SCRIPT"
    echo "[TEST-RUNNER] Checked locations:"
    echo "  - /workspaces/orca-test-jcp-ai-workloads/tests/11-logs-testing/$TEST_SCRIPT"
    echo "  - /opt/logs-testing/tests/$TEST_SCRIPT"
    echo "[TEST-RUNNER] Available test scripts:"
    ls -la /opt/logs-testing/tests/test_logs_*.py 2>/dev/null || echo "  (tests not found)"
    exit 1
fi

echo "[TEST-RUNNER] Running test: $TEST_SCRIPT"
echo "[TEST-RUNNER] Full path: $TEST_PATH"
echo "[TEST-RUNNER] ============================================"

# Run the test script - output goes to stdout/stderr
python3 "$TEST_PATH"
EXIT_CODE=$?

echo "[TEST-RUNNER] ============================================"
echo "[TEST-RUNNER] Test completed with exit code: $EXIT_CODE"

exit $EXIT_CODE
