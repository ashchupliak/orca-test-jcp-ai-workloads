#!/usr/bin/env python3
"""
Git operations test.
Validates git commands and basic repository operations.
"""

import sys
import subprocess
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class GitOperationsTest(BaseTest):
    """Test Git operations and workflows."""

    def __init__(self):
        super().__init__("git_operations")

    def run(self):
        """Run Git operation tests."""
        print("Testing Git operations...")

        # Check Git
        self.check_command_exists("git", "Git")
        success, version = self.check_version("git")
        if success:
            self.result.set_metadata("git_version", version.split('\n')[0])

        # Check git config
        success, user_name, _ = self.run_command("git config --global user.name || echo 'not set'")
        success, user_email, _ = self.run_command("git config --global user.email || echo 'not set'")

        self.result.add_check(
            name="git_config",
            passed=True,  # Just informational
            output=f"User: {user_name}, Email: {user_email}"
        )

        # Test git init and basic operations
        self.test_git_repository_operations()

        return self.result

    def test_git_repository_operations(self):
        """Test creating and using a git repository."""
        temp_dir = None

        try:
            # Create temporary directory
            temp_dir = Path(tempfile.mkdtemp(prefix="git_test_"))

            # Initialize repository
            result = subprocess.run(
                ["git", "init"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                self.result.add_check(
                    name="git_init",
                    passed=False,
                    error=f"Git init failed: {result.stderr}"
                )
                return

            self.result.add_check(
                name="git_init",
                passed=True,
                output="Git repository initialized"
            )

            # Create a test file
            test_file = temp_dir / "test.txt"
            test_file.write_text("Hello from Git test!")

            # Add file
            result = subprocess.run(
                ["git", "add", "test.txt"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            self.result.add_check(
                name="git_add",
                passed=result.returncode == 0,
                output="File staged successfully" if result.returncode == 0 else None,
                error=result.stderr if result.returncode != 0 else None
            )

            # Commit file
            result = subprocess.run(
                ["git", "commit", "-m", "Test commit"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            self.result.add_check(
                name="git_commit",
                passed=result.returncode == 0,
                output="Commit created successfully" if result.returncode == 0 else None,
                error=result.stderr if result.returncode != 0 else None
            )

            # Check log
            result = subprocess.run(
                ["git", "log", "--oneline"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            self.result.add_check(
                name="git_log",
                passed=result.returncode == 0 and "Test commit" in result.stdout,
                output=result.stdout.strip() if result.returncode == 0 else None,
                error=result.stderr if result.returncode != 0 else None
            )

        except Exception as e:
            self.result.add_check(
                name="git_operations",
                passed=False,
                error=f"Error during Git test: {str(e)}"
            )
        finally:
            # Cleanup
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main_template(GitOperationsTest)
