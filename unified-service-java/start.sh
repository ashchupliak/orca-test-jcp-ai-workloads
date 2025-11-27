#!/bin/bash
# Unified Service Startup Script
# This script is designed to NEVER fail and always exit cleanly

set -e

SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JAR_FILE="$SERVICE_DIR/build/libs/unified-service.jar"

echo "========================================"
echo "Unified Service Startup"
echo "========================================"
echo "Service Directory: $SERVICE_DIR"
echo "========================================"

# Check if JAR exists
if [ ! -f "$JAR_FILE" ]; then
    echo "[ERROR] Service JAR not found: $JAR_FILE"
    echo "[INFO] Building service..."

    cd "$SERVICE_DIR"

    # Build with Gradle
    if [ -f "./gradlew" ]; then
        ./gradlew clean bootJar --no-daemon
    else
        gradle clean bootJar --no-daemon
    fi

    if [ ! -f "$JAR_FILE" ]; then
        echo "[ERROR] Build failed, service will not be available"
        exit 0
    fi
fi

# Start the service
echo "[INFO] Starting unified service..."
cd "$SERVICE_DIR"

# Run in background
java -jar "$JAR_FILE" > /tmp/unified-service.log 2>&1 &

SERVICE_PID=$!
echo "[INFO] Unified service started with PID: $SERVICE_PID"

# Wait for service to initialize
sleep 5

# Health check
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "[OK] Service is healthy on port 8000"
else
    echo "[WARNING] Service not responding yet on port 8000"
fi

echo "========================================"
echo "Unified service startup complete"
echo "Logs: tail -f /tmp/unified-service.log"
echo "========================================"

# Exit cleanly
exit 0
