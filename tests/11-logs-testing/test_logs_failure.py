#!/usr/bin/env python3
import sys
import time
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-FAILURE]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started")
    time.sleep(30)  # Give log-sender time to upload
    log_with_marker("Performing operation")
    time.sleep(10)
    log_with_marker("ERROR: Operation failed with critical error")
    time.sleep(10)
    log_with_marker("Container exiting with failure")
    time.sleep(20)  # Final flush time
    sys.exit(1)

if __name__ == "__main__":
    main()
