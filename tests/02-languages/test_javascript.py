#!/usr/bin/env python3
"""
JavaScript/Node.js development environment test.
Validates Node.js, npm, and npx toolchains.
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class JavaScriptTest(BaseTest):
    """Test JavaScript/Node.js development tools."""

    def __init__(self):
        super().__init__("javascript_development")

    def run(self):
        """Run JavaScript toolchain tests."""
        print("Testing JavaScript/Node.js development environment...")

        # Check Node.js
        self.check_command_exists("node", "Node.js")
        success, version = self.check_version("node")
        if success:
            self.result.set_metadata("node_version", version.strip())

        # Check npm
        if self.check_command_exists("npm", "npm"):
            success, version = self.check_version("npm")
            if success:
                self.result.set_metadata("npm_version", version.strip())

        # Check npx
        self.check_command_exists("npx", "npx")

        # Test Node.js execution
        test_code = 'console.log(JSON.stringify({message: "Node.js execution works!", version: process.version}));'

        result = subprocess.run(
            ["node", "-e", test_code],
            capture_output=True,
            text=True,
            timeout=10
        )

        success = result.returncode == 0 and "Node.js execution works!" in result.stdout

        self.result.add_check(
            name="nodejs_execution",
            passed=success,
            output=result.stdout.strip() if success else None,
            error=result.stderr if not success else None
        )

        return self.result


if __name__ == "__main__":
    main_template(JavaScriptTest)
