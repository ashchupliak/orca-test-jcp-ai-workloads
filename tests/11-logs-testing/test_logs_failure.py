#!/usr/bin/env python3
import sys
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-FAILURE]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started")
    log_with_marker("Performing operation")
    log_with_marker("ERROR: Operation failed with critical error")
    log_with_marker("Container exiting with failure")
    sys.exit(1)

if __name__ == "__main__":
    main()
