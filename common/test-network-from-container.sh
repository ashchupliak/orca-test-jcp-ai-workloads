#!/bin/bash
# Network Diagnostic Script - Run inside container to test connectivity
# This tests if the agent can reach external services (Grazie API, GitHub, etc.)

set -e

echo "=========================================="
echo "Container Network Diagnostics"
echo "=========================================="
echo "Hostname: $(hostname)"
echo "Container: ${CONTAINER_NAME:-unknown}"
echo "Date: $(date)"
echo ""

# Test 1: DNS Resolution
echo "[1/8] Testing DNS resolution..."
if nslookup google.com > /dev/null 2>&1; then
    echo "✓ DNS resolution works (google.com)"
else
    echo "✗ DNS resolution FAILED"
    echo "Details:"
    nslookup google.com 2>&1 || true
fi
echo ""

# Test 2: Basic Internet Connectivity
echo "[2/8] Testing basic internet connectivity..."
if curl -s --connect-timeout 5 https://google.com > /dev/null 2>&1; then
    echo "✓ Internet connectivity works"
else
    echo "✗ Internet connectivity FAILED"
    echo "Details:"
    curl -v --connect-timeout 5 https://google.com 2>&1 || true
fi
echo ""

# Test 3: Grazie API (Staging)
echo "[3/8] Testing Grazie API (Staging)..."
GRAZIE_URL="https://api.stgn.jetbrains.ai/user/v5/llm/anthropic/v1/messages"
GRAZIE_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" --connect-timeout 10 "$GRAZIE_URL" 2>&1 || echo "HTTP_CODE:000")
GRAZIE_CODE=$(echo "$GRAZIE_RESPONSE" | grep "HTTP_CODE" | cut -d':' -f2)

if [ "$GRAZIE_CODE" = "401" ] || [ "$GRAZIE_CODE" = "403" ] || [ "$GRAZIE_CODE" = "400" ]; then
    echo "✓ Grazie API reachable (HTTP $GRAZIE_CODE - auth required)"
elif [ "$GRAZIE_CODE" = "000" ]; then
    echo "✗ Grazie API UNREACHABLE (connection failed)"
    echo "Details:"
    curl -v --connect-timeout 10 "$GRAZIE_URL" 2>&1 | head -20 || true
else
    echo "⚠ Grazie API returned HTTP $GRAZIE_CODE"
fi
echo ""

# Test 4: GitHub Connectivity
echo "[4/8] Testing GitHub connectivity..."
if curl -s --connect-timeout 5 https://github.com > /dev/null 2>&1; then
    echo "✓ GitHub reachable"
else
    echo "✗ GitHub UNREACHABLE"
    echo "Details:"
    curl -v --connect-timeout 5 https://github.com 2>&1 | head -20 || true
fi
echo ""

# Test 5: GitHub API
echo "[5/8] Testing GitHub API..."
GITHUB_RESPONSE=$(curl -s --connect-timeout 5 https://api.github.com/zen 2>&1 || echo "FAILED")
if [ "$GITHUB_RESPONSE" != "FAILED" ]; then
    echo "✓ GitHub API works"
    echo "Response: $GITHUB_RESPONSE"
else
    echo "✗ GitHub API FAILED"
fi
echo ""

# Test 6: Git Clone Test (public repo)
echo "[6/8] Testing git clone..."
TEST_DIR="/tmp/test-git-clone-$$"
mkdir -p "$TEST_DIR"
if git clone --depth 1 https://github.com/torvalds/linux.git "$TEST_DIR/linux" > /dev/null 2>&1; then
    echo "✓ Git clone works"
    rm -rf "$TEST_DIR"
else
    echo "✗ Git clone FAILED"
    echo "Details:"
    git clone --depth 1 https://github.com/torvalds/linux.git "$TEST_DIR/linux" 2>&1 || true
    rm -rf "$TEST_DIR"
fi
echo ""

# Test 7: Check Environment Variables
echo "[7/8] Checking proxy environment variables..."
if [ -n "$HTTP_PROXY" ] || [ -n "$HTTPS_PROXY" ] || [ -n "$http_proxy" ] || [ -n "$https_proxy" ]; then
    echo "⚠ Proxy variables set:"
    [ -n "$HTTP_PROXY" ] && echo "  HTTP_PROXY=$HTTP_PROXY"
    [ -n "$HTTPS_PROXY" ] && echo "  HTTPS_PROXY=$HTTPS_PROXY"
    [ -n "$http_proxy" ] && echo "  http_proxy=$http_proxy"
    [ -n "$https_proxy" ] && echo "  https_proxy=$https_proxy"
    [ -n "$NO_PROXY" ] && echo "  NO_PROXY=$NO_PROXY"
else
    echo "✓ No proxy variables set"
fi
echo ""

# Test 8: Check /etc/resolv.conf
echo "[8/8] Checking DNS configuration..."
if [ -f /etc/resolv.conf ]; then
    echo "DNS servers:"
    cat /etc/resolv.conf | grep nameserver || echo "  No nameservers found"
else
    echo "✗ /etc/resolv.conf not found"
fi
echo ""

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "If any tests failed, the agent service will not be able to:"
echo "  - Reach Grazie API for Claude requests"
echo "  - Clone git repositories"
echo "  - Execute external commands"
echo ""
echo "Common issues:"
echo "  1. DNS not configured (check /etc/resolv.conf)"
echo "  2. Firewall blocking outbound connections"
echo "  3. Missing proxy configuration"
echo "  4. Network isolation in Kubernetes"
echo ""
echo "To fix:"
echo "  - Check compute/worker network policies"
echo "  - Verify container has internet access"
echo "  - Add proxy settings if required"
echo "=========================================="
