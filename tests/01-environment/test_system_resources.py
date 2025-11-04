#!/usr/bin/env python3
"""
System resources test.
Validates CPU, memory, and disk resources in the devcontainer.
"""

import sys
import os
import psutil
from pathlib import Path

# Add parent directory to path to import common utilities
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.test_framework import BaseTest, main_template


class SystemResourcesTest(BaseTest):
    """Test system resources availability."""

    def __init__(self):
        super().__init__("system_resources")

    def run(self):
        """Run system resources tests."""
        print("Checking system resources...")

        # CPU information
        try:
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)

            self.result.add_check(
                name="cpu_available",
                passed=cpu_count > 0,
                output=f"CPU cores: {cpu_count}, Usage: {cpu_percent}%"
            )
            self.result.set_metadata("cpu_count", cpu_count)
            self.result.set_metadata("cpu_percent", cpu_percent)
        except Exception as e:
            self.result.add_check(
                name="cpu_available",
                passed=False,
                error=f"Could not check CPU: {str(e)}"
            )

        # Memory information
        try:
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024 ** 3)
            available_gb = memory.available / (1024 ** 3)
            percent_used = memory.percent

            self.result.add_check(
                name="memory_available",
                passed=available_gb > 0.5,  # At least 512MB available
                output=f"Total: {total_gb:.2f}GB, Available: {available_gb:.2f}GB, Used: {percent_used}%"
            )
            self.result.set_metadata("memory_total_gb", round(total_gb, 2))
            self.result.set_metadata("memory_available_gb", round(available_gb, 2))
            self.result.set_metadata("memory_percent", percent_used)
        except Exception as e:
            self.result.add_check(
                name="memory_available",
                passed=False,
                error=f"Could not check memory: {str(e)}"
            )

        # Disk space
        try:
            disk = psutil.disk_usage('/')
            total_gb = disk.total / (1024 ** 3)
            free_gb = disk.free / (1024 ** 3)
            percent_used = disk.percent

            self.result.add_check(
                name="disk_space",
                passed=free_gb > 1.0,  # At least 1GB free
                output=f"Total: {total_gb:.2f}GB, Free: {free_gb:.2f}GB, Used: {percent_used}%"
            )
            self.result.set_metadata("disk_total_gb", round(total_gb, 2))
            self.result.set_metadata("disk_free_gb", round(free_gb, 2))
            self.result.set_metadata("disk_percent", percent_used)
        except Exception as e:
            self.result.add_check(
                name="disk_space",
                passed=False,
                error=f"Could not check disk: {str(e)}"
            )

        # Check /tmp writability
        try:
            test_file = Path("/tmp/resource_test.txt")
            test_file.write_text("test")
            content = test_file.read_text()
            test_file.unlink()

            self.result.add_check(
                name="tmp_writable",
                passed=content == "test",
                output="/tmp directory is writable"
            )
        except Exception as e:
            self.result.add_check(
                name="tmp_writable",
                passed=False,
                error=f"Cannot write to /tmp: {str(e)}"
            )

        # Check /workspace writability
        try:
            test_file = Path("/workspace/resource_test.txt")
            test_file.write_text("test")
            content = test_file.read_text()
            test_file.unlink()

            self.result.add_check(
                name="workspace_writable",
                passed=content == "test",
                output="/workspace directory is writable"
            )
        except Exception as e:
            self.result.add_check(
                name="workspace_writable",
                passed=False,
                error=f"Cannot write to /workspace: {str(e)}"
            )

        return self.result


if __name__ == "__main__":
    main_template(SystemResourcesTest)
