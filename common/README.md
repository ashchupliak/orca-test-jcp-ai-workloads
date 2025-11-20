# Orca Common Services

This directory contains shared services that all Orca AI workload containers use.

## Services Included

### 1. Chat Service (`chat-service/`)
A universal Flask-based HTTP API that provides:
- `/chat` - Simple echo chat endpoint
- `/api/chat` - Grazie-compatible chat endpoint
- `/health` and `/api/health` - Health check endpoints
- `/api/models` - Mock models endpoint
- `/api/validate_token` - Mock token validation

### 2. Startup Script (`start-services.sh`)
Automatically starts:
- SSH server (for terminal access)
- Chat service (for chat functionality)

Sets up SSH with `root`/`root` credentials for development/testing.

## Integration with DevContainers

To add chat and terminal support to a devcontainer:

### Option 1: Using postStartCommand (Simplest)

Update your `devcontainer.json`:

```json
{
  "name": "Your Container",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "postStartCommand": "/workspace/common/start-services.sh sleep infinity",
  "forwardPorts": [8000],
  "remoteEnv": {
    "CONTAINER_NAME": "your-container-name"
  }
}
```

### Option 2: Using Dockerfile (More Control)

Create a `Dockerfile`:

```dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.11

# Install chat service dependencies
WORKDIR /workspace/common/chat-service
COPY common/chat-service/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy startup script
COPY common/start-services.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/start-services.sh

CMD ["/usr/local/bin/start-services.sh", "sleep", "infinity"]
```

### Option 3: Using Docker Compose (Full Setup)

Create a `docker-compose.yml`:

```yaml
services:
  app:
    build:
      context: ..
      dockerfile: .devcontainer-yourname/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ..:/workspace:cached
    command: /workspace/common/start-services.sh sleep infinity
    environment:
      CONTAINER_NAME: your-container-name
```

## Testing the Services

Once the container is running:

```bash
# Test SSH
ssh root@container-host -p 22
# Password: root

# Test chat service
curl http://localhost:8000/health
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'

# View logs
tail -f /tmp/chat-service.log
```

## Environment Variables

- `CONTAINER_NAME` - Name to identify the container in logs/responses
- `CHAT_PORT` - Port for chat service (default: 8000)

## Requirements

- Python 3.x
- Flask 3.0.0
- SSH server (included in Microsoft devcontainer images)

## Notes

- SSH credentials (`root`/`root`) are for development/testing only
- Chat service stores conversations in memory (resets on restart)
- All containers expose port 8000 for chat functionality
- SSH is available on port 22 for terminal access
