#!/bin/bash
set -e

echo "==================================="
echo "Starting Grazie Services"
echo "==================================="

# Install dependencies for grazie-service
cd /workspace/grazie-service
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Installing grazie-service dependencies..."
./venv/bin/pip install -r requirements.txt --quiet

# Install dependencies for agent-service
cd /workspace/agent-service
echo "Installing agent-service dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "==================================="
echo "Starting services..."
echo "==================================="

# Start grazie-service on port 8000 in background
echo "Starting grazie-service on port 8000..."
cd /workspace/grazie-service
./venv/bin/python run_web_app.py &

# Start agent-service on port 8001 in background
echo "Starting agent-service on port 8001..."
cd /workspace/agent-service
python run_agent_service.py &

echo ""
echo "==================================="
echo "Services started:"
echo "  - Grazie Chat: http://localhost:8000"
echo "  - Agent API:   http://localhost:8001"
echo "==================================="

# Keep container running
wait
