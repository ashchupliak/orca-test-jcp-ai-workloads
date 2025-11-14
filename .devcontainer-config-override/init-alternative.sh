#!/bin/bash

# This script runs after the container is created with ALTERNATIVE config
# It logs identifiable information that can be used to verify the correct config was used

echo "=========================================="
echo "CONFIG OVERRIDE TEST - Alternative Config"
echo "=========================================="
echo "CONFIG_SOURCE: ${CONFIG_SOURCE:-not-set}"
echo "CONFIG_TYPE: ${CONFIG_TYPE:-not-set}"
echo "CONTAINER_NAME: ${CONTAINER_NAME:-not-set}"
echo "TEST_MODE: ${TEST_MODE:-not-set}"
echo "ALTERNATIVE_CONFIG: ${ALTERNATIVE_CONFIG:-not-set}"
echo "=========================================="
echo "Container initialized successfully with ALTERNATIVE config"
echo "Python version: $(python --version 2>&1)"
echo "Current directory: $(pwd)"
echo "This is the ALTERNATIVE configuration!"
echo "=========================================="
echo "CONFIG_OVERRIDE_TEST: PASSED - Alternative config loaded"
echo "=========================================="
