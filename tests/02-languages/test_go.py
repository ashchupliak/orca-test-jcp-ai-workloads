#!/usr/bin/env python3
"""
Go development environment test.
Validates Go toolchain, compilation, and module management.
"""

import sys
import subprocess
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class GoTest(BaseTest):
    """Test Go development tools."""

    def __init__(self):
        super().__init__("go_development")

    def run(self):
        """Run Go toolchain tests."""
        print("="*80)
        print("Go Development Environment Test")
        print("="*80)

        # Check Go
        self.check_command_exists("go", "Go")
        success, version = self.check_version("go")
        if success:
            # Extract Go version
            for line in version.split('\n'):
                if 'go version' in line.lower():
                    self.result.set_metadata("go_version", line.strip())
                    break

        # Check GOPATH
        import os
        go_path = os.getenv("GOPATH")
        self.result.add_check(
            name="GOPATH_set",
            passed=go_path is not None,
            output=f"GOPATH={go_path}" if go_path else None,
            error="GOPATH environment variable not set" if not go_path else None
        )

        # Compile and run a simple Go program
        self.compile_and_run_go()

        # Test go mod
        self.test_go_modules()

        return self.result

    def compile_and_run_go(self):
        """Compile and run a simple Go program."""
        test_code = '''package main

import "fmt"

func main() {
    result := add(2, 2)
    fmt.Printf("Go compilation and execution works! 2 + 2 = %d\\n", result)
}

func add(a, b int) int {
    return a + b
}
'''

        temp_dir = None

        try:
            # Create temporary directory
            temp_dir = Path(tempfile.mkdtemp(prefix="go_test_"))
            test_file = temp_dir / "main.go"
            test_file.write_text(test_code)

            # Compile
            compile_result = subprocess.run(
                ["go", "build", "-o", str(temp_dir / "hello"), str(test_file)],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            if compile_result.returncode != 0:
                self.result.add_check(
                    name="go_compilation",
                    passed=False,
                    error=f"Compilation failed: {compile_result.stderr}"
                )
                return

            self.result.add_check(
                name="go_compilation",
                passed=True,
                output="Go code compiled successfully"
            )

            # Run
            binary_path = temp_dir / "hello"
            run_result = subprocess.run(
                [str(binary_path)],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            expected_output = "Go compilation and execution works!"
            success = run_result.returncode == 0 and expected_output in run_result.stdout

            self.result.add_check(
                name="go_execution",
                passed=success,
                output=run_result.stdout.strip() if success else None,
                error=run_result.stderr if not success else None
            )

        except Exception as e:
            self.result.add_check(
                name="go_compilation_execution",
                passed=False,
                error=f"Error during Go test: {str(e)}"
            )
        finally:
            # Cleanup
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def test_go_modules(self):
        """Test Go modules functionality."""
        temp_dir = None

        try:
            # Create temporary directory
            temp_dir = Path(tempfile.mkdtemp(prefix="go_mod_test_"))

            # Initialize module
            init_result = subprocess.run(
                ["go", "mod", "init", "example.com/test"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            success = init_result.returncode == 0 and (temp_dir / "go.mod").exists()

            self.result.add_check(
                name="go_mod_init",
                passed=success,
                output="go.mod created successfully" if success else None,
                error=init_result.stderr if not success else None
            )

        except Exception as e:
            self.result.add_check(
                name="go_mod_init",
                passed=False,
                error=f"Error during go mod test: {str(e)}"
            )
        finally:
            # Cleanup
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main_template(GoTest)
