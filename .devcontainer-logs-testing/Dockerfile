FROM mcr.microsoft.com/devcontainers/base:ubuntu

# Install Node.js, supervisor, python3, and dependencies
RUN apt-get update && apt-get install -y \
    supervisor \
    curl \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install code-server for IDE
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Copy unified service and install dependencies
COPY unified-service-node /opt/unified-service
WORKDIR /opt/unified-service
RUN npm install --production

# Copy logs-testing specific supervisor config and test runner
COPY .devcontainer-logs-testing/supervisord.conf /etc/supervisor/supervisord.conf
COPY .devcontainer-logs-testing/run-test.sh /opt/logs-testing/run-test.sh
RUN chmod +x /opt/logs-testing/run-test.sh

# Expose ports
EXPOSE 8000 8001 8080

# No CMD - devcontainer will handle lifecycle
