#!/usr/bin/env python3
"""
Common test framework utilities for devcontainer testing.
Provides base classes and utilities for all test categories.
"""

import json
import sys
import subprocess
import time
import socket
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Callable
from datetime import datetime
from urllib.request import urlopen
from urllib.error import URLError


class TestResult:
    """Represents the result of a test execution."""

    def __init__(self, test_type: str):
        self.test_type = test_type
        self.status = "success"
        self.start_time = datetime.now()
        self.checks = []
        self.metadata = {}
        self.performance_metrics = {}
        self.validations = {}

    def add_check(self, name: str, passed: bool, output: Optional[str] = None, error: Optional[str] = None):
        """Add a check result."""
        self.checks.append({
            "name": name,
            "passed": passed,
            "output": output,
            "error": error
        })
        if not passed:
            self.status = "failed"

    def set_metadata(self, key: str, value: Any):
        """Set metadata key-value pair."""
        self.metadata[key] = value

    def add_performance_metric(self, key: str, value: float):
        """Add a performance metric (e.g., execution time, build time)."""
        self.performance_metrics[key] = value

    def add_validation(self, key: str, value: Any):
        """Add a validation result (e.g., HTTP status, test pass rate)."""
        self.validations[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        result_dict = {
            "status": self.status,
            "test_type": self.test_type,
            "checks": self.checks,
            "metadata": self.metadata,
            "timestamp": self.start_time.isoformat(),
            "duration_seconds": duration,
            "passed_checks": sum(1 for c in self.checks if c["passed"]),
            "total_checks": len(self.checks)
        }

        # Add performance metrics if any were recorded
        if self.performance_metrics:
            result_dict["performance_metrics"] = self.performance_metrics

        # Add validations if any were recorded
        if self.validations:
            result_dict["validations"] = self.validations

        return result_dict


class BaseTest:
    """Base class for all test categories."""

    def __init__(self, test_type: str):
        self.test_type = test_type
        self.result = TestResult(test_type)

    def run_command(self, cmd: str, check: bool = True, timeout: int = 300) -> Tuple[bool, str, str]:
        """
        Run a shell command and return success status, stdout, and stderr.

        Args:
            cmd: Command to execute
            check: If True, only check if command succeeds. If False, return full output.
            timeout: Command timeout in seconds (default: 300s for long-running builds)

        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)

    def check_command_exists(self, command: str, name: Optional[str] = None) -> bool:
        """Check if a command exists in PATH."""
        check_name = name or command
        success, output, error = self.run_command(f"command -v {command}")
        self.result.add_check(
            name=f"{check_name}_installed",
            passed=success,
            output=output if success else None,
            error=error if not success else None
        )
        return success

    def check_version(self, command: str, name: Optional[str] = None) -> Tuple[bool, str]:
        """Check command version."""
        check_name = name or command
        success, output, error = self.run_command(f"{command} --version")

        if not success:
            # Try -version flag
            success, output, error = self.run_command(f"{command} -version")

        version_output = output if success else error
        self.result.add_check(
            name=f"{check_name}_version",
            passed=success,
            output=version_output[:200] if version_output else None,
            error=error[:200] if not success else None
        )
        return success, version_output

    def check_file_exists(self, file_path: str, name: Optional[str] = None) -> bool:
        """Check if a file or directory exists."""
        check_name = name or f"file_{Path(file_path).name}"
        exists = Path(file_path).exists()
        self.result.add_check(
            name=check_name,
            passed=exists,
            output=f"Found: {file_path}" if exists else None,
            error=f"Not found: {file_path}" if not exists else None
        )
        return exists

    def measure_time(self, label: str, func: Callable, *args, **kwargs) -> Tuple[Any, float]:
        """
        Measure execution time of a function.

        Args:
            label: Label for the performance metric
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Tuple of (function result, execution time in seconds)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        self.result.add_performance_metric(label, round(duration, 2))
        return result, duration

    def validate_output(self, output: str, patterns: List[str], name: str) -> bool:
        """
        Validate output contains expected patterns.

        Args:
            output: Output string to validate
            patterns: List of regex patterns to match
            name: Name for the check

        Returns:
            True if all patterns match, False otherwise
        """
        all_matched = True
        matched_patterns = []
        missing_patterns = []

        for pattern in patterns:
            if re.search(pattern, output, re.MULTILINE):
                matched_patterns.append(pattern)
            else:
                missing_patterns.append(pattern)
                all_matched = False

        self.result.add_check(
            name=name,
            passed=all_matched,
            output=f"Matched: {len(matched_patterns)}/{len(patterns)} patterns",
            error=f"Missing patterns: {missing_patterns}" if not all_matched else None
        )

        return all_matched

    def check_http_endpoint(self, url: str, expected_status: int = 200,
                           timeout: int = 10, name: Optional[str] = None) -> Tuple[bool, Optional[int]]:
        """
        Test HTTP endpoint availability and status.

        Args:
            url: URL to test
            expected_status: Expected HTTP status code
            timeout: Request timeout in seconds
            name: Name for the check

        Returns:
            Tuple of (success, actual_status_code)
        """
        check_name = name or f"http_endpoint_{url}"

        try:
            response = urlopen(url, timeout=timeout)
            status_code = response.getcode()
            success = status_code == expected_status

            self.result.add_check(
                name=check_name,
                passed=success,
                output=f"Status: {status_code}",
                error=f"Expected {expected_status}, got {status_code}" if not success else None
            )
            self.result.add_validation(f"{check_name}_status", status_code)
            return success, status_code

        except URLError as e:
            self.result.add_check(
                name=check_name,
                passed=False,
                output=None,
                error=f"HTTP error: {str(e)}"
            )
            return False, None
        except Exception as e:
            self.result.add_check(
                name=check_name,
                passed=False,
                output=None,
                error=f"Error: {str(e)}"
            )
            return False, None

    def start_docker_service(self, image: str, name: str, ports: Dict[int, int] = None,
                            env: Dict[str, str] = None, detach: bool = True) -> Tuple[bool, str]:
        """
        Start a Docker container service.

        Args:
            image: Docker image name
            name: Container name
            ports: Port mapping {container_port: host_port}
            env: Environment variables
            detach: Run in detached mode

        Returns:
            Tuple of (success, container_id or error)
        """
        cmd_parts = ["docker", "run"]

        if detach:
            cmd_parts.append("-d")

        cmd_parts.extend(["--name", name])

        if ports:
            for container_port, host_port in ports.items():
                cmd_parts.extend(["-p", f"{host_port}:{container_port}"])

        if env:
            for key, value in env.items():
                cmd_parts.extend(["-e", f"{key}={value}"])

        cmd_parts.append(image)
        cmd = " ".join(cmd_parts)

        success, output, error = self.run_command(cmd)

        self.result.add_check(
            name=f"docker_start_{name}",
            passed=success,
            output=output[:100] if output else None,
            error=error if not success else None
        )

        return success, output if success else error

    def wait_for_service(self, host: str, port: int, timeout: int = 30,
                        service_name: Optional[str] = None) -> bool:
        """
        Wait for a service to become available on a specific port.

        Args:
            host: Hostname or IP address
            port: Port number
            timeout: Maximum time to wait in seconds
            service_name: Name of the service for check reporting

        Returns:
            True if service becomes available, False otherwise
        """
        check_name = service_name or f"service_{host}:{port}"
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                sock.close()

                if result == 0:
                    wait_time = round(time.time() - start_time, 2)
                    self.result.add_check(
                        name=f"{check_name}_ready",
                        passed=True,
                        output=f"Service ready after {wait_time}s"
                    )
                    self.result.add_performance_metric(f"{check_name}_startup_time", wait_time)
                    return True

            except socket.error:
                pass

            time.sleep(0.5)

        self.result.add_check(
            name=f"{check_name}_ready",
            passed=False,
            error=f"Service not available after {timeout}s"
        )
        return False

    def run(self) -> TestResult:
        """Run the test. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement run()")

    def save_results(self, output_file: str):
        """Save test results to JSON file."""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(self.result.to_dict(), f, indent=2)

    def print_results(self):
        """Print test results to stdout."""
        print(json.dumps(self.result.to_dict(), indent=2))

    def get_exit_code(self) -> int:
        """Get exit code based on test status."""
        return 0 if self.result.status == "success" else 1


def main_template(test_class):
    """
    Template main function for test scripts.

    Usage:
        if __name__ == "__main__":
            main_template(MyTestClass)
    """
    import argparse

    parser = argparse.ArgumentParser(description=f"Run {test_class.__name__}")
    parser.add_argument('--output', type=str, help='Output file path for JSON results')
    args = parser.parse_args()

    # Run the test
    test = test_class()
    test.run()

    # Save or print results
    if args.output:
        test.save_results(args.output)

    test.print_results()

    # Exit with appropriate code
    sys.exit(test.get_exit_code())
