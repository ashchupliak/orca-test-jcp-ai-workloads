#!/usr/bin/env python3
import sys
import time
from datetime import datetime

def log_with_marker(message, stream=sys.stderr):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-STDERR]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started - all output to stderr")
    time.sleep(30)  # Give log-sender time to upload
    log_with_marker("WARNING: This is stderr output")
    time.sleep(10)
    log_with_marker("ERROR: This is an error message")
    time.sleep(10)
    log_with_marker("All messages go to stderr only")
    time.sleep(5)
    log_with_marker("Stderr test completed")
    time.sleep(5)
    log_with_marker("Container exiting")
    time.sleep(20)  # Final flush time
    sys.exit(0)

if __name__ == "__main__":
    main()
