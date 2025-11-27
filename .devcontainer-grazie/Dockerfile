FROM mcr.microsoft.com/devcontainers/python:3.11

# Install flask and flask-cors for common services
RUN pip install --no-cache-dir flask flask-cors requests pytest

# Install code-server for IDE on port 8080
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Install dependencies
WORKDIR /workspace/grazie-service
COPY grazie-service/requirements_webapp.txt ./
RUN pip install --no-cache-dir -r requirements_webapp.txt
