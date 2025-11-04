#!/usr/bin/env python3
"""
Docker-in-Docker test.
Validates Docker socket access and basic Docker operations.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class DockerTest(BaseTest):
    """Test Docker-in-Docker functionality."""

    def __init__(self):
        super().__init__("docker_operations")

    def run(self):
        """Run Docker tests."""
        print("Testing Docker-in-Docker...")

        # Check Docker command
        if not self.check_command_exists("docker", "Docker CLI"):
            return self.result

        success, version = self.check_version("docker")
        if success:
            self.result.set_metadata("docker_version", version.split('\n')[0])

        # Check Docker socket
        socket_exists = self.check_file_exists("/var/run/docker.sock", "docker_socket")

        # Check Docker daemon connection
        success, output, error = self.run_command("docker info")
        self.result.add_check(
            name="docker_daemon_connection",
            passed=success,
            output="Docker daemon accessible" if success else None,
            error=f"Cannot connect to Docker daemon: {error}" if not success else None
        )

        # Test running a simple container
        if success:
            print("Testing Docker container execution...")
            success, output, error = self.run_command("docker run --rm hello-world")
            self.result.add_check(
                name="docker_run_container",
                passed=success and "Hello from Docker!" in output,
                output="Successfully ran test container" if success else None,
                error=error if not success else None
            )

        return self.result


if __name__ == "__main__":
    main_template(DockerTest)
