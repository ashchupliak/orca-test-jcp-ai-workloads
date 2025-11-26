#!/bin/bash
# Keep container alive and monitor code-server

echo "[$(date)] Keep-alive script started"

# Function to check if code-server is running
check_code_server() {
    if pgrep -f "code-server" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Keep container alive indefinitely
while true; do
    if check_code_server; then
        echo "[$(date)] code-server is running (PID: $(pgrep -f code-server))"
    else
        echo "[$(date)] WARNING: code-server is not running"
    fi

    # Sleep for 60 seconds
    sleep 60
done
