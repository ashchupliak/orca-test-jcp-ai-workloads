#!/usr/bin/env python3
"""
Common test framework utilities for devcontainer testing.
Provides base classes and utilities for all test categories.
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


class TestResult:
    """Represents the result of a test execution."""

    def __init__(self, test_type: str):
        self.test_type = test_type
        self.status = "success"
        self.start_time = datetime.now()
        self.checks = []
        self.metadata = {}

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        return {
            "status": self.status,
            "test_type": self.test_type,
            "checks": self.checks,
            "metadata": self.metadata,
            "timestamp": self.start_time.isoformat(),
            "duration_seconds": duration,
            "passed_checks": sum(1 for c in self.checks if c["passed"]),
            "total_checks": len(self.checks)
        }


class BaseTest:
    """Base class for all test categories."""

    def __init__(self, test_type: str):
        self.test_type = test_type
        self.result = TestResult(test_type)

    def run_command(self, cmd: str, check: bool = True) -> Tuple[bool, str, str]:
        """
        Run a shell command and return success status, stdout, and stderr.

        Args:
            cmd: Command to execute
            check: If True, only check if command succeeds. If False, return full output.

        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
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
