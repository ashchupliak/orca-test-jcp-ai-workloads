#!/usr/bin/env python3
"""
Environment variables and secrets management test.
Validates that environment variables are properly passed and accessible.
"""

import sys
import os
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class EnvVariablesTest(BaseTest):
    """Test environment variables and secrets management."""

    def __init__(self):
        super().__init__("env_variables")

    def run(self):
        """Run environment variables tests."""
        print("="*80)
        print("Environment Variables and Secrets Test")
        print("="*80)

        # Test reading environment variables
        self.test_env_variables()

        # Test custom environment variables
        self.test_custom_env_vars()

        # Test sensitive data handling
        self.test_sensitive_data()

        # Test environment variable in subprocesses
        self.test_env_in_subprocess()

        return self.result

    def test_env_variables(self):
        """Test reading standard environment variables."""
        try:
            # Check standard env vars
            home = os.getenv("HOME")
            user = os.getenv("USER")
            path = os.getenv("PATH")

            success = all([home, path])

            self.result.add_check(
                name="standard_env_vars",
                passed=success,
                output=f"HOME={home}, USER={user}" if success else None
            )

        except Exception as e:
            self.result.add_check(
                name="standard_env_vars",
                passed=False,
                error=f"Env var error: {str(e)}"
            )

    def test_custom_env_vars(self):
        """Test custom environment variables passed to environment."""
        try:
            # Check if TEST_TYPE was passed (from test orchestration)
            test_type = os.getenv("TEST_TYPE")

            # Check if GRAZIE_JWT_TOKEN was passed (for Grazie tests)
            grazie_token = os.getenv("GRAZIE_JWT_TOKEN")

            # At least one custom var should be present
            success = test_type is not None

            self.result.add_check(
                name="custom_env_vars",
                passed=success,
                output=f"TEST_TYPE={test_type}" if success else None,
                error="No custom environment variables found" if not success else None
            )

        except Exception as e:
            self.result.add_check(
                name="custom_env_vars",
                passed=False,
                error=f"Custom env var error: {str(e)}"
            )

    def test_sensitive_data(self):
        """Test handling of sensitive data (secrets)."""
        try:
            # Set a mock secret
            os.environ["SECRET_KEY"] = "test_secret_value_123"

            # Verify it's accessible
            secret = os.getenv("SECRET_KEY")
            success = secret == "test_secret_value_123"

            self.result.add_check(
                name="sensitive_data_handling",
                passed=success,
                output="Secrets can be stored and retrieved" if success else None
            )

            # Clean up
            if "SECRET_KEY" in os.environ:
                del os.environ["SECRET_KEY"]

        except Exception as e:
            self.result.add_check(
                name="sensitive_data_handling",
                passed=False,
                error=f"Sensitive data error: {str(e)}"
            )

    def test_env_in_subprocess(self):
        """Test that environment variables are available in subprocesses."""
        try:
            # Set a test variable
            os.environ["SUBPROCESS_TEST_VAR"] = "subprocess_value"

            # Run subprocess that uses the variable
            result = subprocess.run(
                ["bash", "-c", "echo $SUBPROCESS_TEST_VAR"],
                capture_output=True,
                text=True,
                timeout=10
            )

            expected = "subprocess_value"
            success = result.returncode == 0 and expected in result.stdout

            self.result.add_check(
                name="env_in_subprocess",
                passed=success,
                output=result.stdout.strip() if success else None
            )

            # Clean up
            if "SUBPROCESS_TEST_VAR" in os.environ:
                del os.environ["SUBPROCESS_TEST_VAR"]

        except Exception as e:
            self.result.add_check(
                name="env_in_subprocess",
                passed=False,
                error=f"Subprocess env error: {str(e)}"
            )


if __name__ == "__main__":
    main_template(EnvVariablesTest)
