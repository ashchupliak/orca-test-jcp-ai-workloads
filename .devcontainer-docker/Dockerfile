FROM mcr.microsoft.com/devcontainers/base:ubuntu

# Install Docker CLI and Java 21
RUN apt-get update && apt-get install -y \
    openjdk-21-jdk \
    gradle \
    supervisor \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Docker
RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && apt-get install -y docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

# Install code-server for IDE
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Copy and build unified service
COPY unified-service-java /opt/unified-service
WORKDIR /opt/unified-service
RUN ./gradlew clean bootJar --no-daemon || gradle clean bootJar --no-daemon

# Copy supervisor config
COPY common-config/supervisord.conf /etc/supervisor/conf.d/unified-service.conf

# Expose ports
EXPOSE 8000 8001 8080

# Start supervisor which will manage all services
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
