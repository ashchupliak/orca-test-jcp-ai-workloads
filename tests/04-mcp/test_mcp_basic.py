#!/usr/bin/env python3
"""
MCP (Model Context Protocol) basic test.
Validates that environment can support MCP server setup.
"""

import sys
import subprocess
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class MCPBasicTest(BaseTest):
    """Test MCP server setup capabilities."""

    def __init__(self):
        super().__init__("mcp_basic")

    def run(self):
        """Run MCP basic tests."""
        print("="*80)
        print("MCP Basic Setup Test")
        print("="*80)

        # Check Node.js (required for MCP servers)
        self.check_command_exists("node", "Node.js for MCP")

        # Check npm
        self.check_command_exists("npm", "npm for MCP packages")

        # Check that we can create MCP config structure
        self.test_mcp_config_structure()

        # Test MCP server requirements (filesystem, network)
        self.test_mcp_prerequisites()

        return self.result

    def test_mcp_config_structure(self):
        """Test creating MCP configuration structure."""
        try:
            # Create MCP config directory
            mcp_dir = Path("/tmp/mcp_test")
            mcp_dir.mkdir(exist_ok=True)

            # Create sample MCP config
            config = {
                "mcpServers": {
                    "filesystem": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
                    }
                }
            }

            config_file = mcp_dir / "mcp-config.json"
            config_file.write_text(json.dumps(config, indent=2))

            success = config_file.exists() and config_file.stat().st_size > 0

            self.result.add_check(
                name="mcp_config_creation",
                passed=success,
                output=f"MCP config created at {config_file}" if success else None,
                error="Failed to create MCP config" if not success else None
            )

            # Cleanup
            import shutil
            if mcp_dir.exists():
                shutil.rmtree(mcp_dir, ignore_errors=True)

        except Exception as e:
            self.result.add_check(
                name="mcp_config_creation",
                passed=False,
                error=f"Error creating MCP config: {str(e)}"
            )

    def test_mcp_prerequisites(self):
        """Test that MCP server prerequisites are available."""
        # Test filesystem access (needed for filesystem MCP server)
        try:
            test_dir = Path("/tmp/mcp_filesystem_test")
            test_dir.mkdir(exist_ok=True)

            test_file = test_dir / "test.txt"
            test_file.write_text("MCP filesystem test")

            can_read = test_file.read_text() == "MCP filesystem test"

            self.result.add_check(
                name="mcp_filesystem_access",
                passed=can_read,
                output="Filesystem read/write works for MCP" if can_read else None
            )

            # Cleanup
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir, ignore_errors=True)

        except Exception as e:
            self.result.add_check(
                name="mcp_filesystem_access",
                passed=False,
                error=f"Filesystem access error: {str(e)}"
            )


if __name__ == "__main__":
    main_template(MCPBasicTest)
