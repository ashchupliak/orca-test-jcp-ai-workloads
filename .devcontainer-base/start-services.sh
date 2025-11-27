#!/bin/bash
# This script is for manual service management if needed
set -e

echo "Starting unified service..."
java -jar /opt/unified-service/build/libs/unified-service.jar &

echo "Starting code-server..."
code-server --bind-addr 0.0.0.0:8080 --auth none --disable-telemetry /workspace &

wait
