# IDE Test Container

Simple container for testing the IDE integration feature.

## Features
- Base Ubuntu image
- Node.js 20
- Git
- VS Code IDE (code-server) on port 8080

## Testing
1. Create environment with "IDE Test Environment" template
2. Wait for container to start (30-60 seconds)
3. Navigate to environment details page
4. Click "IDE" tab
5. IDE should load within 2-3 seconds

## Troubleshooting
```bash
# Check IDE status
bash /workspaces/orca-test-jcp-ai-workloads/common/ide/ide-status.sh

# View IDE logs
tail -f /tmp/code-server.log

# Restart IDE
pkill code-server
bash /workspaces/orca-test-jcp-ai-workloads/common/ide/start-ide.sh
```
