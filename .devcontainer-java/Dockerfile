FROM mcr.microsoft.com/devcontainers/java:21

# Install supervisor and curl
RUN apt-get update && apt-get install -y \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

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
