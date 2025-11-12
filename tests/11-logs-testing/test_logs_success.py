#!/usr/bin/env python3
import sys
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-SUCCESS]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started")
    log_with_marker("Performing operation")
    log_with_marker("Operation completed successfully")
    log_with_marker("Container exiting with success")
    sys.exit(0)

if __name__ == "__main__":
    main()
