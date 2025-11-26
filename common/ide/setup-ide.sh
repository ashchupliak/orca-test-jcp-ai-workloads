#!/bin/bash
set -e

echo "[$(date)] Setting up IDE (code-server)..."

CODE_SERVER_VERSION="${CODE_SERVER_VERSION:-4.96.2}"
ARCH=$(dpkg --print-architecture)

# Download and install code-server
curl -fsSL "https://github.com/coder/code-server/releases/download/v${CODE_SERVER_VERSION}/code-server_${CODE_SERVER_VERSION}_${ARCH}.deb" -o /tmp/code-server.deb
sudo dpkg -i /tmp/code-server.deb || sudo apt-get install -f -y
rm /tmp/code-server.deb

# Configure code-server
mkdir -p ~/.config/code-server
cat > ~/.config/code-server/config.yaml << 'YAML_EOF'
bind-addr: 0.0.0.0:8080
auth: none
cert: false
disable-telemetry: true
disable-update-check: true
YAML_EOF

# Install extensions if specified
if [ -n "$IDE_EXTENSIONS" ]; then
    IFS=',' read -ra EXTENSIONS <<< "$IDE_EXTENSIONS"
    for ext in "${EXTENSIONS[@]}"; do
        echo "[$(date)] Installing extension: $ext"
        code-server --install-extension "$ext" || true
    done
fi

echo "[$(date)] IDE setup complete"
