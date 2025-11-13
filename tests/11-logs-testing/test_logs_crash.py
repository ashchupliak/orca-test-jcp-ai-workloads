#!/usr/bin/env python3
import sys
import os
import signal
import time
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-CRASH]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started")
    time.sleep(30)  # Give log-sender time to upload
    log_with_marker("Performing some operations before crash")
    time.sleep(10)
    log_with_marker("About to terminate with SIGTERM signal")
    sys.stdout.flush()
    sys.stderr.flush()
    time.sleep(5)  # Brief delay before crash

    os.kill(os.getpid(), signal.SIGTERM)

    log_with_marker("This should not appear")

if __name__ == "__main__":
    main()
