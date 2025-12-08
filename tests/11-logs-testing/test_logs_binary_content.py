#!/usr/bin/env python3
"""
Advanced Test: Binary Content in Logs
This container outputs binary data mixed with text logs.
Tests handling of non-UTF-8 bytes and binary data that might
appear in logs from containers dealing with files, network data, etc.
"""
import sys
import time
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-BINARY]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started - binary content test")
    time.sleep(5)

    # Regular text log
    log_with_marker("Testing binary content handling")
    time.sleep(2)

    # Print some binary data (as hex representation)
    binary_data = bytes([0x00, 0x01, 0x02, 0x03, 0xFF, 0xFE, 0xFD])
    log_with_marker(f"Binary data (hex): {binary_data.hex()}")
    time.sleep(2)

    # Print base64 encoded binary (common in logs)
    import base64
    log_with_marker(f"Binary data (base64): {base64.b64encode(binary_data).decode('ascii')}")
    time.sleep(2)

    # Print escaped binary (how it might appear in debug logs)
    log_with_marker(f"Binary data (repr): {repr(binary_data)}")
    time.sleep(2)

    # Mix of printable and non-printable ASCII
    mixed = "Normal text \x00 \x01 \x02 more text \xFF"
    log_with_marker(f"Mixed content (repr): {repr(mixed)}")
    time.sleep(2)

    # URL-encoded binary-like content
    log_with_marker("URL-encoded: file%00name%FFtest%01data")
    time.sleep(2)

    # Hex dump style (common in packet/file dumps)
    log_with_marker("Hex dump:")
    log_with_marker("00000000: 4865 6c6c 6f20 576f 726c 6421 0a00 0102  Hello World!....")
    log_with_marker("00000010: ffff fefe fdfc fbfa f9f8 f7f6 f5f4 f3f2  ................")
    time.sleep(2)

    # Attempting to write actual binary bytes (will likely be escaped or cause encoding error)
    log_with_marker("About to test raw binary write")
    try:
        # Try writing raw bytes
        sys.stdout.buffer.write(b"[LOGS-TEST-BINARY] Raw binary: \x00\x01\x02\xFF\xFE\xFD\n")
        sys.stdout.buffer.flush()
        log_with_marker("Raw binary write succeeded")
    except Exception as e:
        log_with_marker(f"Raw binary write failed: {e}")
    time.sleep(2)

    # Test null bytes embedded in string
    log_with_marker("String with nulls: " + repr("before\x00middle\x00after"))
    time.sleep(2)

    # Test very long binary sequence
    long_binary = bytes(range(256))
    log_with_marker(f"All bytes 0-255 (hex): {long_binary.hex()}")
    time.sleep(2)

    log_with_marker("Binary content test completed")
    time.sleep(20)
    sys.exit(0)

if __name__ == "__main__":
    main()
