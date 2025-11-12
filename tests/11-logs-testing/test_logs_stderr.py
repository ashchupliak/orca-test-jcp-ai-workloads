#!/usr/bin/env python3
import sys
from datetime import datetime

def log_with_marker(message, stream=sys.stderr):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-STDERR]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started - all output to stderr")
    log_with_marker("WARNING: This is stderr output")
    log_with_marker("ERROR: This is an error message")
    log_with_marker("All messages go to stderr only")
    log_with_marker("Stderr test completed")
    log_with_marker("Container exiting")
    sys.exit(0)

if __name__ == "__main__":
    main()
