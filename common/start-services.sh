#!/bin/bash
# Start SSH and Chat services for Orca containers

set -e

echo "=== Orca Container Services Startup ==="
echo "Container: ${CONTAINER_NAME:-unknown}"
echo "Starting at: $(date)"

# Start SSH server (if not already running)
echo "Starting SSH server..."
sudo service ssh start || echo "SSH already running or not available"

# Set root password for SSH access
echo "root:root" | sudo chpasswd

# Install chat service dependencies
if [ ! -d "/workspace/common/chat-service" ]; then
    echo "ERROR: Chat service not found at /workspace/common/chat-service"
    echo "Make sure the workspace is mounted correctly"
else
    echo "Installing chat service dependencies..."
    cd /workspace/common/chat-service

    # Install Flask if not already installed
    pip3 install --quiet --no-cache-dir -r requirements.txt || echo "Flask already installed"

    # Start chat service in background
    echo "Starting chat service on port 8000..."
    nohup python3 app.py > /tmp/chat-service.log 2>&1 &
    CHAT_PID=$!
    echo "Chat service started with PID: $CHAT_PID"

    # Wait a moment and check if service is running
    sleep 2
    if ps -p $CHAT_PID > /dev/null; then
        echo "✓ Chat service is running"
        echo "  Check logs: tail -f /tmp/chat-service.log"
    else
        echo "✗ Chat service failed to start"
        echo "  Check logs: cat /tmp/chat-service.log"
    fi
fi

echo ""
echo "=== Services Status ==="
echo "SSH: $(service ssh status 2>&1 | head -1 || echo 'Not available')"
echo "Chat: http://localhost:8000/health"
echo ""
echo "=== Ready for connections ==="
echo "Terminal: ssh root@localhost (password: root)"
echo "Chat API: curl http://localhost:8000/chat"
echo "Logs: tail -f /tmp/chat-service.log"
echo ""

# Keep container running
exec "$@"
