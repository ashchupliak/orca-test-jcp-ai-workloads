#!/bin/bash
set -e

echo "=== AI Tools Setup Script ==="
echo "Setting up Claude Code and Codex CLI for JetBrains AI Platform"

# Get token from environment or use placeholder
GRAZIE_TOKEN="${GRAZIE_API_TOKEN:-YOUR_TOKEN_HERE}"
GRAZIE_ENV="${GRAZIE_ENVIRONMENT:-PREPROD}"

# Determine the base URL based on environment
if [ "$GRAZIE_ENV" = "PRODUCTION" ]; then
    BASE_URL="https://api.jetbrains.ai/user/v5/llm"
else
    BASE_URL="https://api-preprod.jetbrains.ai/user/v5/llm"
fi

echo "Environment: $GRAZIE_ENV"
echo "Base URL: $BASE_URL"

# === Setup Codex CLI ===
echo ""
echo "Configuring Codex CLI..."

mkdir -p ~/.codex

cat > ~/.codex/config.toml <<EOF
# Codex CLI Configuration for JetBrains AI Platform
# Token: Copy from https://platform.jetbrains.ai/

[model_providers.jbai]
name = "JetBrains AI"
base_url = "${BASE_URL}/openai/v1"
env_http_headers = { "Grazie-Authenticate-JWT" = "GRAZIE_API_TOKEN" }
wire_api = "responses"

[model_providers.jbai-anthropic]
name = "JetBrains AI (Anthropic)"
base_url = "${BASE_URL}/anthropic/v1"
env_http_headers = { "Grazie-Authenticate-JWT" = "GRAZIE_API_TOKEN" }
wire_api = "messages"
EOF

echo "✅ Codex CLI configured at ~/.codex/config.toml"

# === Install and Setup Claude Code ===
echo ""
echo "Installing Claude Code..."

# Install Claude Code via npm
if ! command -v claude &> /dev/null && ! command -v claude-code &> /dev/null; then
    npm install -g @anthropic-ai/claude-code 2>/dev/null || {
        echo "⚠️  Claude Code npm install failed, trying alternative..."
        # Alternative: install via npx or skip
        echo "   You can install manually: npm install -g @anthropic-ai/claude-code"
    }
fi

# Check if installation succeeded
if command -v claude &> /dev/null; then
    echo "✅ Claude Code installed (as 'claude')"
    CLAUDE_CMD="claude"
elif command -v claude-code &> /dev/null; then
    echo "✅ Claude Code installed (as 'claude-code')"
    CLAUDE_CMD="claude-code"
else
    echo "⚠️  Claude Code not found - helper script will fail until installed"
    CLAUDE_CMD="claude"  # Default, will error when used
fi

echo "Configuring Claude Code..."

mkdir -p ~/.config/claude-code

cat > ~/.config/claude-code/config.json <<EOF
{
  "apiKey": "use-grazie-token",
  "apiUrl": "${BASE_URL}/anthropic/v1",
  "defaultModel": "claude-3-5-sonnet-20241022",
  "customHeaders": {
    "Grazie-Authenticate-JWT": "${GRAZIE_TOKEN}"
  }
}
EOF

echo "✅ Claude Code configured at ~/.config/claude-code/config.json"

# === Create helper scripts ===
echo ""
echo "Creating helper scripts..."

# Codex helper script - write to temp file first, then move with sudo
cat > /tmp/codex-jb <<'EOF'
#!/bin/bash
# Wrapper for Codex CLI with JetBrains AI Platform
if [ -z "$GRAZIE_API_TOKEN" ]; then
    echo "ERROR: GRAZIE_API_TOKEN environment variable not set"
    echo "Get your token from: https://platform.jetbrains.ai/"
    echo ""
    echo "Usage:"
    echo "  export GRAZIE_API_TOKEN='your-token-here'"
    echo "  codex-jb <command>"
    exit 1
fi

exec codex -c model_provider=jbai "$@"
EOF
sudo mv /tmp/codex-jb /usr/local/bin/codex-jb
sudo chmod +x /usr/local/bin/codex-jb

echo "✅ Created helper script: codex-jb"

# Claude Code helper script - write to temp file first, then move with sudo
# Use local proxy to translate headers for Grazie API
cat > /tmp/claude-jb <<'WRAPPER_EOF'
#!/bin/bash
# Wrapper for Claude Code with JetBrains AI Platform (Grazie)
# Uses a local proxy to translate authentication headers

echo "[claude-jb] Starting wrapper..."

if [ -z "$GRAZIE_API_TOKEN" ]; then
    echo "ERROR: GRAZIE_API_TOKEN environment variable not set"
    echo "Get your token from: https://platform.jetbrains.ai/"
    echo ""
    echo "Usage:"
    echo "  export GRAZIE_API_TOKEN='your-token-here'"
    echo "  claude-jb <command>"
    exit 1
fi

GRAZIE_ENV="${GRAZIE_ENVIRONMENT:-PREPROD}"
echo "[claude-jb] Environment: $GRAZIE_ENV"

# Check if proxy is running, start if not
PROXY_PORT=8090
if ! curl -s "http://127.0.0.1:$PROXY_PORT/health" > /dev/null 2>&1; then
    echo "[claude-jb] Starting Grazie proxy on port $PROXY_PORT..."
    python3 /workspace/agent-service/grazie_proxy.py &
    PROXY_PID=$!
    sleep 2

    # Verify proxy started
    if ! curl -s "http://127.0.0.1:$PROXY_PORT/health" > /dev/null 2>&1; then
        echo "ERROR: Failed to start Grazie proxy"
        exit 1
    fi
    echo "[claude-jb] Proxy started (PID: $PROXY_PID)"
else
    echo "[claude-jb] Grazie proxy already running"
fi

# Find the actual claude command
CLAUDE_BIN=""
for cmd in claude claude-code; do
    if command -v $cmd &> /dev/null; then
        CLAUDE_BIN=$(command -v $cmd)
        break
    fi
done

if [ -z "$CLAUDE_BIN" ]; then
    echo "ERROR: Claude Code CLI not found"
    echo "Install with: npm install -g @anthropic-ai/claude-code"
    exit 1
fi

echo "[claude-jb] Using CLI: $CLAUDE_BIN"

# Point Claude Code to local proxy instead of direct Grazie API
export ANTHROPIC_API_KEY="$GRAZIE_API_TOKEN"
export ANTHROPIC_BASE_URL="http://127.0.0.1:$PROXY_PORT"

echo "[claude-jb] Proxy URL: $ANTHROPIC_BASE_URL"
echo "[claude-jb] Executing: $CLAUDE_BIN $@"

exec $CLAUDE_BIN "$@"
WRAPPER_EOF
sudo mv /tmp/claude-jb /usr/local/bin/claude-jb
sudo chmod +x /usr/local/bin/claude-jb

echo "✅ Created helper script: claude-jb"

# === Create README ===
cat > /workspace/AI_TOOLS_README.md <<'EOF'
# AI Tools Setup Guide

This devcontainer comes pre-configured with:
- **Codex CLI**: Command-line interface for AI-powered coding
- **Claude Code**: Anthropic's Claude for development tasks

Both tools are configured to use **JetBrains AI Platform** (Grazie).

## Getting Your Token

1. Visit https://platform.jetbrains.ai/
2. Click on your profile icon
3. Copy the Developer Token

## Quick Start

### Set Your Token (Required)
```bash
export GRAZIE_API_TOKEN='your-token-here'
export GRAZIE_ENVIRONMENT='PREPROD'  # or 'PRODUCTION'
```

### Using Codex CLI
```bash
# Use the JetBrains AI Platform provider
codex-jb "write a python function to calculate fibonacci"

# Or use codex directly
export GRAZIE_API_TOKEN='your-token'
codex -c model_provider=jbai "your prompt"
```

### Using Claude Code
```bash
# Use Claude Code with JetBrains AI Platform
claude-jb chat "write a hello world in rust"

# The helper script automatically updates the token
```

### Available Models

Through JetBrains AI Platform, you have access to:
- OpenAI models (GPT-4, GPT-3.5, etc.)
- Anthropic Claude models (Claude 3.5 Sonnet, etc.)
- Other supported providers

### Configuration Files

- Codex: `~/.codex/config.toml`
- Claude Code: `~/.config/claude-code/config.json`

### Testing Your Setup

```bash
# Test Codex
codex-jb "say hello"

# Test token validation
curl -H "Grazie-Authenticate-JWT: $GRAZIE_API_TOKEN" \
     https://api-preprod.jetbrains.ai/user/v5/llm/openai/v1/models
```

### Environment Variables

- `GRAZIE_API_TOKEN`: Your JetBrains AI Platform token (required)
- `GRAZIE_ENVIRONMENT`: Either `PREPROD` or `PRODUCTION` (default: PREPROD)

### Troubleshooting

**Token not set error:**
```bash
export GRAZIE_API_TOKEN='your-token-here'
```

**Wrong environment:**
```bash
export GRAZIE_ENVIRONMENT='PRODUCTION'
# Re-run setup-ai-tools.sh to regenerate configs
```

**Check configuration:**
```bash
cat ~/.codex/config.toml
cat ~/.config/claude-code/config.json
```

## Examples

### Codex Examples
```bash
# Generate code
codex-jb "write a REST API in Python using Flask"

# Debug code
codex-jb "why is this function failing: $(cat buggy_code.py)"

# Refactor
codex-jb "refactor this to be more pythonic: $(cat old_code.py)"
```

### Claude Code Examples
```bash
# Interactive chat
claude-jb chat

# One-off command
claude-jb "explain this code: $(cat complex_code.py)"
```

## References

- Codex CLI: https://github.com/microsoft/codex-cli
- JetBrains AI Platform: https://platform.jetbrains.ai/
- Grazie OpenAI Proxy: https://api.jetbrains.ai/user/v5/llm/openai/v1/chat/completions
EOF

echo "✅ Created AI_TOOLS_README.md"

# === Install Python dependencies for services ===
echo ""
echo "Installing Python dependencies for services..."

# Install dependencies for grazie-service
cd /workspace/grazie-service
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
./venv/bin/pip install -r requirements.txt --quiet 2>/dev/null || pip install flask flask-cors --quiet

# Install dependencies for agent-service
cd /workspace/agent-service
pip install -r requirements.txt --quiet 2>/dev/null || pip install flask flask-cors --quiet

echo "✅ Python dependencies installed"

# === Start services ===
echo ""
echo "Starting web services..."

# Start grazie-service on port 8000 in background
cd /workspace/grazie-service
(./venv/bin/python run_web_app.py 2>&1 | while read line; do echo "[grazie] $line"; done) &

# Start agent-service on port 8001 in background
cd /workspace/agent-service
(python run_agent_service.py 2>&1 | while read line; do echo "[agent] $line"; done) &

echo "✅ Services starting..."
echo "   - Grazie Chat: http://localhost:8000"
echo "   - Agent API:   http://localhost:8001"

# === Print summary ===
echo ""
echo "==================================="
echo "✅ AI Tools Setup Complete!"
echo "==================================="
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Set your token:"
echo "   export GRAZIE_API_TOKEN='your-token-here'"
echo ""
echo "2. Test Codex:"
echo "   codex-jb 'say hello'"
echo ""
echo "3. Read the guide:"
echo "   cat /workspace/AI_TOOLS_README.md"
echo ""
echo "Get your token from: https://platform.jetbrains.ai/"
echo ""
