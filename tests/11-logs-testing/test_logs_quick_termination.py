#!/usr/bin/env python3
"""
Timing Test: Quick Termination
This container starts and terminates very quickly (5 seconds).
Tests behavior when environment is terminated before logs can be uploaded,
or when the termination happens so fast that logs might be lost.
"""
import sys
import time
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-QUICK-TERM]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started")
    time.sleep(1)

    log_with_marker("Rapid execution - terminating quickly")
    time.sleep(1)

    log_with_marker("Container exiting immediately")
    time.sleep(1)

    # Exit quickly without giving much time for log upload
    sys.exit(0)

if __name__ == "__main__":
    main()
