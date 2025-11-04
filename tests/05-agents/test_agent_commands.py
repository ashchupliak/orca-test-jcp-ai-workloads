#!/usr/bin/env python3
"""
Agent command execution test.
Validates command execution that AI agents would perform.
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class AgentCommandsTest(BaseTest):
    """Test agent command execution."""

    def __init__(self):
        super().__init__("agent_commands")

    def run(self):
        """Run agent command tests."""
        print("="*80)
        print("Agent Command Execution Test")
        print("="*80)

        # Test shell commands
        self.test_shell_commands()

        # Test command output capture
        self.test_output_capture()

        # Test command chaining
        self.test_command_chaining()

        # Test environment variables in commands
        self.test_env_in_commands()

        return self.result

    def test_shell_commands(self):
        """Test executing shell commands."""
        try:
            result = subprocess.run(
                ["echo", "Agent command execution works"],
                capture_output=True,
                text=True,
                timeout=10
            )

            expected = "Agent command execution works"
            success = result.returncode == 0 and expected in result.stdout

            self.result.add_check(
                name="agent_shell_commands",
                passed=success,
                output=result.stdout.strip() if success else None
            )

        except Exception as e:
            self.result.add_check(
                name="agent_shell_commands",
                passed=False,
                error=f"Shell command error: {str(e)}"
            )

    def test_output_capture(self):
        """Test capturing command output."""
        try:
            result = subprocess.run(
                ["ls", "/tmp"],
                capture_output=True,
                text=True,
                timeout=10
            )

            success = result.returncode == 0 and len(result.stdout) > 0

            self.result.add_check(
                name="agent_output_capture",
                passed=success,
                output=f"Captured {len(result.stdout)} bytes" if success else None
            )

        except Exception as e:
            self.result.add_check(
                name="agent_output_capture",
                passed=False,
                error=f"Output capture error: {str(e)}"
            )

    def test_command_chaining(self):
        """Test chaining multiple commands."""
        try:
            # Create test file, read it, delete it
            commands = [
                ["echo", "test content", ">", "/tmp/agent_chain_test.txt"],
                ["cat", "/tmp/agent_chain_test.txt"],
                ["rm", "/tmp/agent_chain_test.txt"]
            ]

            # For simplicity, test a single command that does all
            result = subprocess.run(
                "echo 'chained commands work' > /tmp/agent_chain.txt && cat /tmp/agent_chain.txt && rm /tmp/agent_chain.txt",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )

            expected = "chained commands work"
            success = result.returncode == 0 and expected in result.stdout

            self.result.add_check(
                name="agent_command_chaining",
                passed=success,
                output=result.stdout.strip() if success else None
            )

        except Exception as e:
            self.result.add_check(
                name="agent_command_chaining",
                passed=False,
                error=f"Command chaining error: {str(e)}"
            )

    def test_env_in_commands(self):
        """Test using environment variables in commands."""
        try:
            import os
            os.environ["AGENT_TEST_VAR"] = "agent_value"

            result = subprocess.run(
                ["bash", "-c", "echo $AGENT_TEST_VAR"],
                capture_output=True,
                text=True,
                timeout=10
            )

            expected = "agent_value"
            success = result.returncode == 0 and expected in result.stdout

            self.result.add_check(
                name="agent_env_in_commands",
                passed=success,
                output=result.stdout.strip() if success else None
            )

        except Exception as e:
            self.result.add_check(
                name="agent_env_in_commands",
                passed=False,
                error=f"Env in commands error: {str(e)}"
            )


if __name__ == "__main__":
    main_template(AgentCommandsTest)
