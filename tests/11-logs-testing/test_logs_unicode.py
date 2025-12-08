#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edge Case Test: Unicode and Special Characters
This container outputs various UTF-8 characters including emoji,
multi-byte characters, RTL text, and special symbols.
Tests proper encoding handling throughout the log pipeline.
"""
import sys
import time
from datetime import datetime

def log_with_marker(message, stream=sys.stdout):
    timestamp = datetime.utcnow().isoformat() + "Z"
    marker = "[LOGS-TEST-UNICODE]"
    output = f"{timestamp} {marker} {message}"
    print(output, file=stream, flush=True)

def main():
    log_with_marker("Container started - Unicode test")
    time.sleep(5)

    # Emoji and symbols
    log_with_marker("Testing emoji: 🚀 🎉 ✅ ❌ ⚠️ 🐍 🔥 💻 ⭐ 🌟")
    time.sleep(2)

    # Various languages
    log_with_marker("English: Hello World!")
    log_with_marker("Русский: Привет мир!")
    log_with_marker("日本語: こんにちは世界!")
    log_with_marker("العربية: مرحبا بالعالم")
    log_with_marker("עברית: שלום עולם")
    log_with_marker("中文: 你好世界")
    log_with_marker("한국어: 안녕하세요 세계")
    time.sleep(2)

    # Special characters and symbols
    log_with_marker("Math: ∑ ∫ √ ∞ ≈ ≠ ≤ ≥ π α β γ δ")
    log_with_marker("Currency: $ € £ ¥ ₹ ₽ ¢ ₿")
    log_with_marker("Arrows: → ← ↑ ↓ ↔ ↕ ⇒ ⇐ ⇔")
    log_with_marker("Box drawing: ┌─┐ │ │ └─┘ ┏━┓ ┃ ┃ ┗━┛")
    time.sleep(2)

    # Zero-width characters and combining marks
    log_with_marker("Combining marks: e\u0301 a\u0300 o\u0308 (é à ö)")
    log_with_marker("Zero-width: Hello\u200BWorld (zero-width space)")
    time.sleep(2)

    # Control pictures (visible representations)
    log_with_marker("Control pictures: ␀ ␁ ␂ ␃ ␄ ␅ ␆ ␇ ␈ ␉")
    time.sleep(2)

    # Mixed script (potential for rendering issues)
    log_with_marker("Mixed: English-日本語-العربية-Русский-🚀-emoji")
    time.sleep(2)

    # Very long Unicode string
    long_emoji = "🎉" * 100
    log_with_marker(f"Long emoji string: {long_emoji}")
    time.sleep(2)

    # Potential problematic characters
    log_with_marker("Quotes: \"double\" 'single' «guillemets» „German"")
    log_with_marker("Dashes: - – — ― (hyphen, en-dash, em-dash, horizontal bar)")
    log_with_marker("Spaces: [ ] [  ] [   ] (various space characters)")
    time.sleep(2)

    log_with_marker("Unicode test completed successfully ✅")
    time.sleep(20)
    sys.exit(0)

if __name__ == "__main__":
    main()
