#!/usr/bin/env python3
import sys
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-LARGE-OUTPUT]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started - generating large output")

    total_lines = 10000
    lorem_ipsum = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."

    for i in range(total_lines):
        line_number = str(i + 1).zfill(5)
        log_with_marker(f"Line {line_number}/{total_lines}: {lorem_ipsum}")

    log_with_marker("Large output generation completed")
    log_with_marker("Container exiting")
    sys.exit(0)

if __name__ == "__main__":
    main()
