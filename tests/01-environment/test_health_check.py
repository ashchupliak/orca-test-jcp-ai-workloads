#!/usr/bin/env python3
"""
Basic environment health check test.
Validates that the devcontainer has essential system tools and proper configuration.
"""

import sys
from pathlib import Path

# Add parent directory to path to import common utilities
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.test_framework import BaseTest, main_template


class HealthCheckTest(BaseTest):
    """Test basic environment health."""

    def __init__(self):
        super().__init__("environment_health")

    def run(self):
        """Run health check tests."""
        print("Running environment health checks...")

        # Check essential system commands
        essential_commands = [
            ("bash", "Bash shell"),
            ("sh", "POSIX shell"),
            ("git", "Git version control"),
            ("curl", "HTTP client"),
            ("wget", "File downloader"),
            ("tar", "Archive tool"),
            ("gzip", "Compression tool"),
            ("unzip", "ZIP extractor"),
            ("make", "Build tool"),
            ("which", "Command locator")
        ]

        for cmd, name in essential_commands:
            self.check_command_exists(cmd, name)

        # Check environment variables
        import os
        env_vars = {
            "PATH": "System PATH",
            "HOME": "Home directory",
            "USER": "Username",
            "PWD": "Current working directory"
        }

        for var, description in env_vars.items():
            value = os.getenv(var)
            self.result.add_check(
                name=f"env_{var}",
                passed=value is not None,
                output=f"{var}={value[:50]}..." if value and len(value) > 50 else f"{var}={value}" if value else None,
                error=f"Environment variable {var} not set" if not value else None
            )

        # Check critical directories
        critical_dirs = [
            ("/workspace", "Workspace directory"),
            ("/tmp", "Temporary directory"),
            ("/usr/bin", "System binaries"),
            ("/usr/local/bin", "Local binaries")
        ]

        for dir_path, description in critical_dirs:
            self.check_file_exists(dir_path, description)

        # Check disk space
        success, output, error = self.run_command("df -h / | tail -1")
        if success:
            self.result.add_check(
                name="disk_space",
                passed=True,
                output=f"Disk usage: {output}"
            )
        else:
            self.result.add_check(
                name="disk_space",
                passed=False,
                error="Could not check disk space"
            )

        # Check memory
        success, output, error = self.run_command("free -h 2>/dev/null || vm_stat 2>/dev/null")
        if success:
            self.result.add_check(
                name="memory_check",
                passed=True,
                output=f"Memory info available"
            )

        # Set metadata
        self.result.set_metadata("environment", os.getenv("TEST_MODE", "unknown"))
        self.result.set_metadata("hostname", os.getenv("HOSTNAME", "unknown"))

        return self.result


if __name__ == "__main__":
    main_template(HealthCheckTest)
