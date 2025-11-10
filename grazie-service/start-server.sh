#!/bin/bash
# Startup script for Grazie chat server

echo "Starting Grazie chat server on port 8000..."

cd /workspace/grazie-service

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Installing/updating dependencies..."
./venv/bin/pip install -q -r requirements.txt

# Start Flask server in the background
echo "Starting Flask server..."
./venv/bin/python3 -m flask --app app run --host 0.0.0.0 --port 8000 &

echo "Flask server started! Chat endpoint available at http://localhost:8000/chat"
echo "Container will stay running..."

# Keep container alive
tail -f /dev/null
