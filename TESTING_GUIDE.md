# Container Testing Guide

## Prerequisites
- Access to orca-lab-dev network (VPN or internal network)
- Valid JWT token for facade API
- curl or similar HTTP client

## Network Access Note
The orca-lab-dev instance (`orca-lab-dev.i.aws.intellij.net`) is on internal JetBrains infrastructure and requires:
- VPN connection, OR
- Access from JetBrains internal network

## Quick Test (Single Container)

### 1. Create Environment
```bash
TOKEN="your-token-here"

curl -X POST "https://orca-lab-dev.i.aws.intellij.net/api/facade/v1/environments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-python",
    "repositoryUrl": "https://github.com/ashchupliak/orca-test-jcp-ai-workloads",
    "devcontainerPath": ".devcontainer-python"
  }'
```

Expected response:
```json
{
  "id": "some-uuid",
  "name": "test-python",
  "status": "CREATING",
  ...
}
```

### 2. Wait for RUNNING Status
```bash
ENV_ID="id-from-previous-response"

# Check status (repeat until RUNNING)
curl -X GET "https://orca-lab-dev.i.aws.intellij.net/api/facade/v1/environments/$ENV_ID" \
  -H "Authorization: Bearer $TOKEN"
```

Expected statuses:
- CREATING → BUILDING → STARTING → RUNNING (success)
- If status becomes FAILED or STOPPED, check logs

### 3. Get Hostname
From the environment details response, extract the `hostname` field:
```json
{
  "hostname": "test-python-abc123.orca-lab-dev.i.aws.intellij.net"
}
```

### 4. Test Endpoints

#### Chat Service (Port 8000)
```bash
HOSTNAME="your-hostname-here"

curl "http://${HOSTNAME}:8000/health"
```

Expected response:
```json
{
  "status": "healthy",
  "service": "chat",
  "port": 8000
}
```

#### Agent Service (Port 8001)
```bash
curl "http://${HOSTNAME}:8001/agent/health"
```

Expected response:
```json
{
  "status": "healthy",
  "service": "agent",
  "port": 8001
}
```

#### IDE Service (Port 8080)
```bash
curl -I "http://${HOSTNAME}:8080"
```

Expected: HTTP 200 OK

Or open in browser: `http://${HOSTNAME}:8080`

### 5. Delete Environment
```bash
curl -X DELETE "https://orca-lab-dev.i.aws.intellij.net/api/facade/v1/environments/$ENV_ID" \
  -H "Authorization: Bearer $TOKEN"
```

## Automated Testing

### Using Provided Scripts

#### Test All Containers (Parallel)
```bash
cd /path/to/orca-test-jcp-ai-workloads
./test-containers-parallel.sh
```

This will:
- Test all 22 containers in batches of 4
- Create detailed logs in `test-results/`
- Print summary of results

#### Test All Containers (Sequential)
```bash
./test-all-containers.sh
```

This will:
- Test containers one at a time
- More reliable but slower
- Detailed logging to `test-results/`

### Test Results Location
- Results are saved to `test-results/[timestamp]/`
- Each container gets its own log file
- Check individual logs for detailed error messages

## Container List (22 Total)

| # | Name | Devcontainer Path | Expected Ports |
|---|------|-------------------|----------------|
| 1 | Python | `.devcontainer-python` | 8000, 8001, 8080 |
| 2 | JavaScript | `.devcontainer-javascript` | 8000, 8001, 8080 |
| 3 | Java | `.devcontainer-java` | 8000, 8001, 8080 |
| 4 | Go | `.devcontainer-go` | 8000, 8001, 8080 |
| 5 | Rust | `.devcontainer-rust` | 8000, 8001, 8080 |
| 6 | Ruby | `.devcontainer-ruby` | 8000, 8001, 8080 |
| 7 | PHP | `.devcontainer-php` | 8000, 8001, 8080 |
| 8 | .NET | `.devcontainer-dotnet` | 8000, 8001, 8080 |
| 9 | Agents | `.devcontainer-agents` | 8000, 8001, 8080 |
| 10 | AI Tools | `.devcontainer-ai-tools` | 8000, 8001, 8080 |
| 11 | Databases | `.devcontainer-databases` | 8000, 8001, 8080 |
| 12 | Docker | `.devcontainer-docker` | 8000, 8001, 8080 |
| 13 | Git | `.devcontainer-git` | 8000, 8001, 8080 |
| 14 | Grazie | `.devcontainer-grazie` | 8000, 8001, 8080 |
| 15 | IDE Test | `.devcontainer-ide-test` | 8000, 8001, 8080 |
| 16 | Lightweight Agent | `.devcontainer-lightweight-agent` | 8000, 8001, 8080 |
| 17 | Logs Testing | `.devcontainer-logs-testing` | 8000, 8001, 8080 |
| 18 | MCP | `.devcontainer-mcp` | 8000, 8001, 8080 |
| 19 | Config Override | `.devcontainer-config-override` | 8000, 8001, 8080 |
| 20 | Config Override Alt | `.devcontainer-config-override-alt` | 8000, 8001, 8080 |
| 21 | Base | `.devcontainer-base` | 8000, 8001, 8080 |
| 22 | Default | `.devcontainer` | 8000, 8001, 8080 |

## Expected Behavior for All Containers

### After Creation
1. Environment reaches **RUNNING** status (within 5-10 minutes)
2. Environment stays in **RUNNING** status (doesn't stop)
3. All 3 ports are accessible

### Port 8000 (Chat Service)
- `GET /health` returns HTTP 200
- Response contains: `{"status":"healthy","service":"chat","port":8000}`
- Service responds within 1-2 seconds

### Port 8001 (Agent Service)
- `GET /agent/health` returns HTTP 200
- Response contains: `{"status":"healthy","service":"agent","port":8001}`
- Service responds within 1-2 seconds

### Port 8080 (IDE Service)
- `GET /` returns HTTP 200
- Returns HTML for code-server web IDE
- Should be accessible in browser
- Shows VS Code interface

## Troubleshooting

### Container Fails to Start (FAILED Status)
1. Check facade logs for the environment
2. Look for Docker build errors
3. Verify all dependencies are in Dockerfile
4. Check supervisor logs: `/var/log/supervisor/`

### Container Stops After Starting
1. Check if services are crashing
2. Review supervisor logs
3. Verify Java service starts correctly
4. Check code-server starts correctly

### Ports Return 404 or Timeout
1. Verify services are actually running inside container
2. Check supervisor status: `supervisorctl status`
3. Check unified service logs: `/var/log/supervisor/unified-service.log`
4. Check code-server logs: `/var/log/supervisor/code-server.log`

### Port 8000/8001 Returns Connection Refused
- Unified service (Java) didn't start
- Check: `ps aux | grep java`
- Check logs: `/var/log/supervisor/unified-service.error.log`

### Port 8080 Returns Connection Refused
- code-server didn't start
- Check: `ps aux | grep code-server`
- Check logs: `/var/log/supervisor/code-server.error.log`

## Success Criteria

For each of the 22 containers:
- ✅ Environment reaches RUNNING status
- ✅ Environment stays RUNNING (doesn't stop)
- ✅ Port 8000 returns HTTP 200 with correct JSON
- ✅ Port 8001 returns HTTP 200 with correct JSON
- ✅ Port 8080 returns HTTP 200 (IDE accessible)

## Manual Verification (UI)

1. Go to orca-lab dashboard
2. Create new environment
3. Select repository: `ashchupliak/orca-test-jcp-ai-workloads`
4. Select devcontainer path (e.g., `.devcontainer-python`)
5. Wait for environment to be RUNNING
6. Check tabs:
   - **Chat tab**: Should show chat interface
   - **Agent tab**: Should allow Claude Code tasks
   - **IDE tab**: Should show web-based VS Code

## Validation Summary

All containers have been:
- ✅ Configured with standardized Dockerfiles
- ✅ Configured with standardized devcontainer.json
- ✅ Validated locally (configuration check)
- ✅ Built successfully (Docker build works)
- ⏳ Ready for facade testing (requires network access)

## Next Steps

1. Connect to JetBrains VPN or internal network
2. Run test scripts from machine with network access
3. Verify all 22 containers reach RUNNING status
4. Test all endpoints for each container
5. Document any failures for investigation
