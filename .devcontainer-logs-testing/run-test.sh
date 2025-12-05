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

# Check if TEST_SCRIPT is set
if [ -z "$TEST_SCRIPT" ]; then
    echo "[TEST-RUNNER] ERROR: TEST_SCRIPT environment variable is not set"
    echo "[TEST-RUNNER] Available test scripts:"
    ls -la /workspaces/orca-test-jcp-ai-workloads/tests/11-logs-testing/test_logs_*.py 2>/dev/null || echo "  (tests not found - workspace may not be mounted)"
    echo "[TEST-RUNNER] Exiting without running tests"
    exit 0
fi

# Full path to test script
TEST_PATH="/workspaces/orca-test-jcp-ai-workloads/tests/11-logs-testing/$TEST_SCRIPT"

# Check if the test script exists
if [ ! -f "$TEST_PATH" ]; then
    echo "[TEST-RUNNER] ERROR: Test script not found: $TEST_PATH"
    echo "[TEST-RUNNER] Available test scripts:"
    ls -la /workspaces/orca-test-jcp-ai-workloads/tests/11-logs-testing/test_logs_*.py 2>/dev/null || echo "  (tests not found)"
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
