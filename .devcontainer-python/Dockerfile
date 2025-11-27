FROM mcr.microsoft.com/devcontainers/python:3.11

# Install Node.js, supervisor, and code-server dependencies
RUN apt-get update && apt-get install -y \
    supervisor \
    curl \
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

# Copy supervisor config
COPY common-config/supervisord.conf /etc/supervisor/conf.d/unified-service.conf

# Expose ports
EXPOSE 8000 8001 8080

# No CMD - devcontainer will handle lifecycle
