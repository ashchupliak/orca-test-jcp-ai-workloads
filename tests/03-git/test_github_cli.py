#!/usr/bin/env python3
"""
GitHub CLI test.
Validates gh CLI installation and basic functionality.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class GitHubCLITest(BaseTest):
    """Test GitHub CLI (gh) functionality."""

    def __init__(self):
        super().__init__("github_cli")

    def run(self):
        """Run GitHub CLI tests."""
        print("Testing GitHub CLI...")

        # Check gh CLI
        if not self.check_command_exists("gh", "GitHub CLI"):
            return self.result

        success, version = self.check_version("gh")
        if success:
            self.result.set_metadata("gh_version", version.split('\n')[0])

        # Check gh auth status (may not be authenticated in test environment)
        success, output, error = self.run_command("gh auth status")
        self.result.add_check(
            name="gh_auth_status",
            passed=True,  # Don't fail on auth - just informational
            output=f"Auth status: {'Authenticated' if success else 'Not authenticated (expected in test)'}"
        )

        # Test gh help commands
        commands_to_test = [
            ("gh pr --help", "PR commands"),
            ("gh issue --help", "Issue commands"),
            ("gh repo --help", "Repo commands"),
        ]

        for cmd, description in commands_to_test:
            success, _, _ = self.run_command(cmd)
            self.result.add_check(
                name=f"gh_command_{description.lower().replace(' ', '_')}",
                passed=success,
                output=f"{description} available" if success else None
            )

        return self.result


if __name__ == "__main__":
    main_template(GitHubCLITest)
