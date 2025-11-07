FROM mcr.microsoft.com/devcontainers/python:3.11

# Install Git feature manually since we're using Dockerfile now
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Pre-install Python dependencies
RUN pip install --no-cache-dir anthropic fastapi 'uvicorn[standard]' websockets
