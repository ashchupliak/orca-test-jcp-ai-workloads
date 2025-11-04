#!/usr/bin/env python3
"""
Agent filesystem operations test.
Validates filesystem operations that AI agents would perform.
"""

import sys
import subprocess
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class AgentFilesystemTest(BaseTest):
    """Test agent filesystem operations."""

    def __init__(self):
        super().__init__("agent_filesystem")

    def run(self):
        """Run agent filesystem tests."""
        print("="*80)
        print("Agent Filesystem Operations Test")
        print("="*80)

        # Test file creation
        self.test_file_creation()

        # Test file reading
        self.test_file_reading()

        # Test file editing
        self.test_file_editing()

        # Test directory operations
        self.test_directory_operations()

        # Test file search
        self.test_file_search()

        return self.result

    def test_file_creation(self):
        """Test creating files (agent write operation)."""
        try:
            test_file = Path("/tmp/agent_test_file.txt")
            content = "This file was created by an AI agent"
            test_file.write_text(content)

            success = test_file.exists() and test_file.read_text() == content

            self.result.add_check(
                name="agent_file_creation",
                passed=success,
                output="Agent can create files" if success else None
            )

            # Cleanup
            if test_file.exists():
                test_file.unlink()

        except Exception as e:
            self.result.add_check(
                name="agent_file_creation",
                passed=False,
                error=f"File creation error: {str(e)}"
            )

    def test_file_reading(self):
        """Test reading files (agent read operation)."""
        try:
            test_file = Path("/tmp/agent_read_test.txt")
            content = "Agent reading test content"
            test_file.write_text(content)

            read_content = test_file.read_text()
            success = read_content == content

            self.result.add_check(
                name="agent_file_reading",
                passed=success,
                output="Agent can read files" if success else None
            )

            # Cleanup
            if test_file.exists():
                test_file.unlink()

        except Exception as e:
            self.result.add_check(
                name="agent_file_reading",
                passed=False,
                error=f"File reading error: {str(e)}"
            )

    def test_file_editing(self):
        """Test editing files (agent edit operation)."""
        try:
            test_file = Path("/tmp/agent_edit_test.txt")
            test_file.write_text("Original content")

            # Edit: replace content
            test_file.write_text("Edited content")

            success = test_file.read_text() == "Edited content"

            self.result.add_check(
                name="agent_file_editing",
                passed=success,
                output="Agent can edit files" if success else None
            )

            # Cleanup
            if test_file.exists():
                test_file.unlink()

        except Exception as e:
            self.result.add_check(
                name="agent_file_editing",
                passed=False,
                error=f"File editing error: {str(e)}"
            )

    def test_directory_operations(self):
        """Test directory operations (agent directory management)."""
        try:
            test_dir = Path("/tmp/agent_test_dir")
            test_dir.mkdir(exist_ok=True)

            # Create file in directory
            (test_dir / "file1.txt").write_text("content1")
            (test_dir / "file2.txt").write_text("content2")

            # List directory
            files = list(test_dir.glob("*.txt"))
            success = len(files) == 2

            self.result.add_check(
                name="agent_directory_ops",
                passed=success,
                output=f"Agent can manage directories ({len(files)} files)" if success else None
            )

            # Cleanup
            if test_dir.exists():
                shutil.rmtree(test_dir, ignore_errors=True)

        except Exception as e:
            self.result.add_check(
                name="agent_directory_ops",
                passed=False,
                error=f"Directory operation error: {str(e)}"
            )

    def test_file_search(self):
        """Test file search operations (agent file discovery)."""
        try:
            test_dir = Path("/tmp/agent_search_test")
            test_dir.mkdir(exist_ok=True)

            # Create files to search
            (test_dir / "test1.py").write_text("python code")
            (test_dir / "test2.js").write_text("javascript code")
            (test_dir / "readme.md").write_text("documentation")

            # Search for Python files
            py_files = list(test_dir.glob("*.py"))
            success = len(py_files) == 1 and py_files[0].name == "test1.py"

            self.result.add_check(
                name="agent_file_search",
                passed=success,
                output=f"Agent can search files (found {len(py_files)} .py files)" if success else None
            )

            # Cleanup
            if test_dir.exists():
                shutil.rmtree(test_dir, ignore_errors=True)

        except Exception as e:
            self.result.add_check(
                name="agent_file_search",
                passed=False,
                error=f"File search error: {str(e)}"
            )


if __name__ == "__main__":
    main_template(AgentFilesystemTest)
