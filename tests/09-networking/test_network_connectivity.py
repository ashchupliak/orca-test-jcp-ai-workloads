#!/usr/bin/env python3
"""
Network connectivity test.
Validates external network access from the environment.
"""

import sys
import subprocess
from pathlib import Path
import socket

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class NetworkConnectivityTest(BaseTest):
    """Test network connectivity."""

    def __init__(self):
        super().__init__("network_connectivity")

    def run(self):
        """Run network connectivity tests."""
        print("="*80)
        print("Network Connectivity Test")
        print("="*80)

        # Test DNS resolution
        self.test_dns_resolution()

        # Test external connectivity
        self.test_external_connectivity()

        # Test curl availability
        self.test_curl()

        # Test network tools
        self.test_network_tools()

        return self.result

    def test_dns_resolution(self):
        """Test DNS resolution."""
        try:
            # Try to resolve a common domain
            result = socket.gethostbyname("www.google.com")
            success = result is not None

            self.result.add_check(
                name="dns_resolution",
                passed=success,
                output=f"Resolved to {result}" if success else None
            )

        except Exception as e:
            self.result.add_check(
                name="dns_resolution",
                passed=False,
                error=f"DNS resolution error: {str(e)}"
            )

    def test_external_connectivity(self):
        """Test connectivity to external services."""
        try:
            # Try to connect to a common server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(("www.google.com", 80))
            sock.close()

            success = result == 0

            self.result.add_check(
                name="external_connectivity",
                passed=success,
                output="Can connect to external services" if success else None,
                error=f"Connection failed with code {result}" if not success else None
            )

        except Exception as e:
            self.result.add_check(
                name="external_connectivity",
                passed=False,
                error=f"Connectivity error: {str(e)}"
            )

    def test_curl(self):
        """Test curl command for HTTP requests."""
        try:
            # Check curl exists
            result = subprocess.run(
                ["which", "curl"],
                capture_output=True,
                text=True,
                timeout=5
            )

            curl_exists = result.returncode == 0

            if not curl_exists:
                self.result.add_check(
                    name="curl_availability",
                    passed=False,
                    error="curl command not found"
                )
                return

            # Try a simple HTTP request
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "https://www.google.com"],
                capture_output=True,
                text=True,
                timeout=10
            )

            http_code = result.stdout.strip()
            success = http_code in ["200", "301", "302"]

            self.result.add_check(
                name="curl_http_request",
                passed=success,
                output=f"HTTP status: {http_code}" if success else None,
                error=f"Unexpected HTTP code: {http_code}" if not success else None
            )

        except Exception as e:
            self.result.add_check(
                name="curl_http_request",
                passed=False,
                error=f"curl error: {str(e)}"
            )

    def test_network_tools(self):
        """Test network diagnostic tools."""
        tools = ["ping", "netstat", "ifconfig"]

        for tool in tools:
            try:
                result = subprocess.run(
                    ["which", tool],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                success = result.returncode == 0

                self.result.add_check(
                    name=f"tool_{tool}",
                    passed=success,
                    output=f"{tool} is available" if success else None,
                    error=f"{tool} not found" if not success else None
                )

            except Exception as e:
                self.result.add_check(
                    name=f"tool_{tool}",
                    passed=False,
                    error=f"Error checking {tool}: {str(e)}"
                )


if __name__ == "__main__":
    main_template(NetworkConnectivityTest)
