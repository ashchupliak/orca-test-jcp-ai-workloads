#!/usr/bin/env python3
import sys
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-MIXED]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started - mixing stdout and stderr", sys.stdout)

    iterations = 10

    for i in range(iterations):
        log_with_marker(f"STDOUT message {i + 1}/{iterations}", sys.stdout)
        log_with_marker(f"STDERR message {i + 1}/{iterations}", sys.stderr)

    log_with_marker("Mixed output test completed", sys.stdout)
    log_with_marker("Container exiting", sys.stdout)
    sys.exit(0)

if __name__ == "__main__":
    main()
