FROM mcr.microsoft.com/devcontainers/python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    jq \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for Claude Code)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install pnpm globally
RUN npm install -g pnpm

# Install Codex CLI
RUN pip install --no-cache-dir codex-cli

# Install Claude Code (via npm)
RUN npm install -g @anthropic-ai/claude-code || echo "Claude Code installation skipped if not available"

# Install additional Python packages
RUN pip install --no-cache-dir \
    requests \
    flask \
    flask-cors \
    pytest \
    python-dotenv \
    rich

# Install code-server for IDE on port 8080
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Create workspace directory
WORKDIR /workspace

# Copy configuration scripts
COPY .devcontainer-ai-tools/setup-ai-tools.sh /usr/local/bin/setup-ai-tools.sh
RUN chmod +x /usr/local/bin/setup-ai-tools.sh

# Create default directories
RUN mkdir -p /root/.config/claude-code \
    && mkdir -p /root/.codex

# Set environment variables
ENV WORKSPACE_ROOT=/workspace
ENV PYTHONPATH=/workspace
