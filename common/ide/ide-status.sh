#!/bin/bash
IDE_PORT="${IDE_PORT:-8080}"

echo "IDE Status Check:"
echo "  Process: $(pgrep -f code-server && echo 'Running ✓' || echo 'Not running ✗')"
echo "  Port: $(ss -tulpn 2>/dev/null | grep :$IDE_PORT && echo 'Listening ✓' || echo 'Not listening ✗')"
echo "  Health: $(curl -s http://localhost:$IDE_PORT/healthz && echo 'OK ✓' || echo 'Failed ✗')"
