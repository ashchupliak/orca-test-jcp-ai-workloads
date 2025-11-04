#!/usr/bin/env python3
"""
Python development environment test.
Validates Python, pip, and virtualenv toolchains.
"""

import sys
import subprocess
from pathlib import Path

# Add parent directory to path to import common utilities
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.test_framework import BaseTest, main_template


class PythonTest(BaseTest):
    """Test Python development tools."""

    def __init__(self):
        super().__init__("python_development")

    def run(self):
        """Run Python toolchain tests."""
        print("Testing Python development environment...")

        # Check Python 3
        self.check_command_exists("python3", "Python 3")
        success, version = self.check_version("python3")
        if success:
            self.result.set_metadata("python_version", version.split()[1] if len(version.split()) > 1 else version)

        # Check python symlink
        self.check_command_exists("python", "Python symlink")

        # Check pip
        if self.check_command_exists("pip3", "pip3"):
            success, version = self.check_version("pip3")
            if success:
                self.result.set_metadata("pip_version", version.split()[1] if 'pip' in version else version)

        # Check pip symlink
        self.check_command_exists("pip", "pip symlink")

        # Check virtualenv/venv
        success, _, _ = self.run_command("python3 -m venv --help")
        self.result.add_check(
            name="venv_module",
            passed=success,
            output="Python venv module is available" if success else None,
            error="Python venv module not found" if not success else None
        )

        # Test Python script execution
        self.test_python_execution()

        # Test package installation (non-destructive)
        self.test_package_availability()

        return self.result

    def test_python_execution(self):
        """Test executing a Python script."""
        test_code = '''import sys
import json

data = {
    "message": "Python execution works!",
    "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
}
print(json.dumps(data))
'''

        test_file = Path("/tmp/test_python_execution.py")

        try:
            test_file.write_text(test_code)

            result = subprocess.run(
                ["python3", str(test_file)],
                capture_output=True,
                text=True,
                timeout=10
            )

            success = result.returncode == 0 and "Python execution works!" in result.stdout

            self.result.add_check(
                name="python_execution",
                passed=success,
                output=result.stdout.strip() if success else None,
                error=result.stderr if not success else None
            )

        except Exception as e:
            self.result.add_check(
                name="python_execution",
                passed=False,
                error=f"Error during Python test: {str(e)}"
            )
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_package_availability(self):
        """Test that common Python packages can be imported."""
        packages = [
            ("json", "JSON module"),
            ("os", "OS module"),
            ("sys", "Sys module"),
            ("pathlib", "Pathlib module"),
            ("subprocess", "Subprocess module"),
        ]

        for package, description in packages:
            result = subprocess.run(
                ["python3", "-c", f"import {package}"],
                capture_output=True,
                text=True,
                timeout=5
            )

            self.result.add_check(
                name=f"import_{package}",
                passed=result.returncode == 0,
                output=f"{description} available" if result.returncode == 0 else None,
                error=result.stderr if result.returncode != 0 else None
            )


if __name__ == "__main__":
    main_template(PythonTest)
