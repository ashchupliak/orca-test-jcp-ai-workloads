#!/usr/bin/env python3
"""
Edge Case Test: Extremely Large Logs
This container generates >100MB of output to test memory handling,
download timeouts, and streaming capabilities.
"""
import sys
import time
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-LARGE]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started - generating large log output")

    # Generate approximately 100MB of log data
    # Each line is ~200 bytes, so we need ~500,000 lines
    LINE_COUNT = 500_000
    BATCH_SIZE = 10_000

    for batch in range(LINE_COUNT // BATCH_SIZE):
        for i in range(BATCH_SIZE):
            line_num = batch * BATCH_SIZE + i
            # Generate a line with some variation to prevent compression
            padding = f"data_{line_num:08d}_" + ("x" * (100 + (line_num % 50)))
            log_with_marker(f"Line {line_num}: {padding}")

        # Brief pause every batch to allow log flushing
        if batch % 10 == 0:
            progress_pct = (batch * BATCH_SIZE * 100) // LINE_COUNT
            log_with_marker(f"Progress: {progress_pct}% ({batch * BATCH_SIZE} lines)")
            time.sleep(1)

    log_with_marker(f"Large log generation completed - {LINE_COUNT} lines written")
    time.sleep(30)  # Allow final upload
    sys.exit(0)

if __name__ == "__main__":
    main()
