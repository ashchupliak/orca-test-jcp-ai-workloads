FROM mcr.microsoft.com/devcontainers/python:3.11

# Install Git feature manually since we're using Dockerfile now
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Pre-install Python dependencies
# Note: flask and requests are required for chat-service and agent-service
RUN pip install --no-cache-dir anthropic fastapi 'uvicorn[standard]' websockets flask flask-cors requests pytest

# Install code-server for IDE on port 8080
RUN curl -fsSL https://code-server.dev/install.sh | sh
