#!/bin/bash
# Update all devcontainers to include chat and terminal support

set -e

echo "Updating all devcontainers with chat and terminal support..."

DEVCONTAINERS=(
  ".devcontainer"
  ".devcontainer-agents"
  ".devcontainer-databases"
  ".devcontainer-docker"
  ".devcontainer-dotnet"
  ".devcontainer-git"
  ".devcontainer-go"
  ".devcontainer-java"
  ".devcontainer-mcp"
  ".devcontainer-php"
  ".devcontainer-ruby"
  ".devcontainer-rust"
)

for DC in "${DEVCONTAINERS[@]}"; do
  CONFIG_FILE="$DC/devcontainer.json"

  if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Skipping $DC - config file not found"
    continue
  fi

  echo "Processing $DC..."

  # Extract container name from directory
  CONTAINER_NAME=$(echo "$DC" | sed 's/\.devcontainer-//g' | sed 's/\.devcontainer/default/g')

  # Check if already updated
  if grep -q "postStartCommand" "$CONFIG_FILE"; then
    echo "  Already has postStartCommand, skipping..."
    continue
  fi

  # Create backup
  cp "$CONFIG_FILE" "$CONFIG_FILE.bak"

  # Use Python to update the JSON properly
  python3 << EOF
import json
import sys

try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)

    # Add CONTAINER_NAME to remoteEnv
    if 'remoteEnv' not in config:
        config['remoteEnv'] = {}
    config['remoteEnv']['CONTAINER_NAME'] = '$CONTAINER_NAME'

    # Add postStartCommand
    config['postStartCommand'] = '/workspace/common/start-services.sh sleep infinity &'

    # Add forwardPorts
    if 'forwardPorts' not in config:
        config['forwardPorts'] = [8000]
    elif 8000 not in config['forwardPorts']:
        config['forwardPorts'].append(8000)

    # Write back
    with open('$CONFIG_FILE', 'w') as f:
        json.dump(config, f, indent=2)
        f.write('\n')

    print('  ✓ Updated')
    sys.exit(0)
except Exception as e:
    print(f'  ✗ Error: {e}', file=sys.stderr)
    sys.exit(1)
EOF

  if [[ $? -ne 0 ]]; then
    echo "  Restoring backup..."
    mv "$CONFIG_FILE.bak" "$CONFIG_FILE"
  else
    rm "$CONFIG_FILE.bak"
  fi
done

echo ""
echo "✓ All devcontainers updated!"
echo ""
echo "Note: grazie and lightweight-agent already have custom setups"
echo "To test: Create an environment with any container and verify:"
echo "  - SSH: ssh root@host (password: root)"
echo "  - Chat: curl http://localhost:8000/health"
