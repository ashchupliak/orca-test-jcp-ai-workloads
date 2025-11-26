#!/bin/bash
# Start SSH, Chat, and Agent services for Orca containers
# This script ensures reliable service startup with health checks

set -e

# Lock file to prevent multiple instances
LOCK_FILE="/tmp/start-services.lock"
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        echo "Another instance is already running (PID: $LOCK_PID), exiting..."
        exit 0
    fi
fi
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

echo "=== Orca Container Services Startup ==="
echo "Container: ${CONTAINER_NAME:-unknown}"
echo "Starting at: $(date)"

# Function to check if service is healthy
is_healthy() {
    local port=$1
    curl -s -f "http://localhost:$port/health" > /dev/null 2>&1
}

# Function to kill process on a specific port
kill_port() {
    local port=$1
    echo "  Killing any process on port $port..."
    # Use fuser if available, otherwise try lsof
    if command -v fuser &> /dev/null; then
        fuser -k $port/tcp 2>/dev/null || true
    else
        # Fallback to lsof
        local pid=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$pid" ]; then
            echo "  Found PID $pid on port $port, killing..."
            kill -9 $pid 2>/dev/null || true
        fi
    fi
    # Give it a moment to release the port
    sleep 1
}

# Function to wait for a service to be healthy
wait_for_health() {
    local port=$1
    local name=$2
    local max_attempts=${3:-30}
    local attempt=1

    echo "Waiting for $name (port $port) to be healthy..."
    while [ $attempt -le $max_attempts ]; do
        if is_healthy "$port"; then
            echo "✓ $name is healthy (attempt $attempt)"
            return 0
        fi
        echo "  Waiting... (attempt $attempt/$max_attempts)"
        sleep 1
        attempt=$((attempt + 1))
    done

    echo "✗ $name failed to become healthy after $max_attempts attempts"
    return 1
}

# Function to start and monitor a service
start_service() {
    local service_dir=$1
    local service_name=$2
    local port=$3
    local log_file="/tmp/${service_name}.log"

    # Check if already healthy - don't restart if working
    if is_healthy "$port"; then
        echo "✓ $service_name already healthy on port $port, skipping restart"
        return 0
    fi

    if [ ! -d "$service_dir" ]; then
        echo "ERROR: $service_name not found at $service_dir"
        return 1
    fi

    echo "Installing $service_name dependencies..."
    cd "$service_dir"
    pip3 install --quiet --no-cache-dir -r requirements.txt 2>/dev/null || true

    echo "Starting $service_name on port $port..."

    # Kill any existing process on this port using proper port-based killing
    kill_port "$port"

    # Start the service
    nohup python3 app.py > "$log_file" 2>&1 &
    local pid=$!
    echo "$pid" > "/tmp/${service_name}.pid"

    # Wait for service to be healthy
    if wait_for_health "$port" "$service_name" 30; then
        echo "✓ $service_name started successfully (PID: $pid)"
        return 0
    else
        echo "✗ $service_name failed to start"
        echo "=== $service_name error log ==="
        cat "$log_file" 2>/dev/null || echo "No log file"
        echo "=== End of log ==="
        return 1
    fi
}

# Function to monitor and restart services
monitor_services() {
    while true; do
        # Check chat service
        if ! curl -s -f "http://localhost:8000/health" > /dev/null 2>&1; then
            echo "[$(date)] Chat service unhealthy, restarting..."
            start_service "/workspace/common/chat-service" "chat-service" 8000 || true
        fi

        # Check agent service
        if ! curl -s -f "http://localhost:8001/health" > /dev/null 2>&1; then
            echo "[$(date)] Agent service unhealthy, restarting..."
            start_service "/workspace/common/agent-service" "agent-service" 8001 || true
        fi

        sleep 30
    done
}

# Start SSH server (if not already running)
echo "Starting SSH server..."
sudo service ssh start 2>/dev/null || echo "SSH not available or already running"

# Set root password for SSH access
echo "root:root" | sudo chpasswd 2>/dev/null || true

# Start chat service
echo ""
echo "=== Starting Chat Service ==="
start_service "/workspace/common/chat-service" "chat-service" 8000 || echo "Warning: Chat service may not be available"

# Start agent service
echo ""
echo "=== Starting Agent Service ==="
start_service "/workspace/common/agent-service" "agent-service" 8001 || echo "Warning: Agent service may not be available"

echo ""
echo "=== Services Status ==="
echo "SSH: $(service ssh status 2>&1 | head -1 || echo 'Not available')"

# Final health check
if curl -s -f "http://localhost:8000/health" > /dev/null 2>&1; then
    echo "Chat Service (8000): ✓ Healthy"
else
    echo "Chat Service (8000): ✗ Unhealthy"
fi

if curl -s -f "http://localhost:8001/health" > /dev/null 2>&1; then
    echo "Agent Service (8001): ✓ Healthy"
else
    echo "Agent Service (8001): ✗ Unhealthy"
fi

echo ""
echo "=== Ready for connections ==="
echo "Terminal: ssh root@localhost (password: root)"
echo "Chat API: http://localhost:8000/health"
echo "Agent API: http://localhost:8001/health"
echo "Logs: tail -f /tmp/chat-service.log /tmp/agent-service.log"
echo ""

# Start background monitor for service health
echo "Starting service health monitor..."
monitor_services &
MONITOR_PID=$!
echo "Health monitor started (PID: $MONITOR_PID)"

# Keep container running
exec "$@"
