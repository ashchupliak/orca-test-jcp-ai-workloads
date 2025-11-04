#!/bin/bash
# Install additional tools and dependencies for devcontainer testing

set -e

echo "Installing additional development tools..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt || echo "Warning: Could not install all Python dependencies"

# Install additional package managers
echo "Checking additional package managers..."

# Kotlin compiler (if needed)
if ! command -v kotlinc &> /dev/null; then
    echo "Note: Kotlin compiler not found. Install via SDKMAN if needed."
fi

# Additional database clients (best effort)
echo "Database clients will be checked during tests..."

# Make test scripts executable
echo "Making test scripts executable..."
find /workspace/tests -name "*.py" -type f -exec chmod +x {} \; || true

# Create output directory
mkdir -p /tmp/test-results

echo "Tool installation complete!"
