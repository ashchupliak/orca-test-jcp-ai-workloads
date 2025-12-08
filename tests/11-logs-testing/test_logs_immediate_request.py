#!/usr/bin/env python3
"""
Timing Test: Immediate Request
This container has a long startup delay before producing logs.
Tests behavior when logs are requested immediately after job starts,
but logs aren't available yet in S3.
"""
import sys
import time
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-IMMEDIATE]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    # Long delay before producing any logs (simulates slow startup)
    # This allows the client to request logs before they're available
    time.sleep(90)  # 90 seconds delay

    log_with_marker("Container finally started after delay")
    time.sleep(10)

    log_with_marker("Performing operation")
    time.sleep(10)

    log_with_marker("Operation completed")
    time.sleep(20)

    log_with_marker("Container exiting")
    time.sleep(20)
    sys.exit(0)

if __name__ == "__main__":
    main()
