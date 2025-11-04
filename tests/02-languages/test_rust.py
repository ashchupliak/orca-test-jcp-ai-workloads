#!/usr/bin/env python3
"""
Rust development environment test.
Validates Rust toolchain, cargo, and compilation.
"""

import sys
import subprocess
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class RustTest(BaseTest):
    """Test Rust development tools."""

    def __init__(self):
        super().__init__("rust_development")

    def run(self):
        """Run Rust toolchain tests."""
        print("="*80)
        print("Rust Development Environment Test")
        print("="*80)

        # Check rustc
        self.check_command_exists("rustc", "Rust compiler")
        success, version = self.check_version("rustc")
        if success:
            self.result.set_metadata("rustc_version", version.split('\n')[0])

        # Check cargo
        if self.check_command_exists("cargo", "Cargo"):
            success, version = self.check_version("cargo")
            if success:
                self.result.set_metadata("cargo_version", version.split('\n')[0])

        # Check rustup
        self.check_command_exists("rustup", "Rustup")

        # Compile and run a simple Rust program
        self.compile_and_run_rust()

        # Test cargo project
        self.test_cargo_project()

        return self.result

    def compile_and_run_rust(self):
        """Compile and run a simple Rust program."""
        test_code = '''fn main() {
    let result = add(2, 2);
    println!("Rust compilation and execution works! 2 + 2 = {}", result);
}

fn add(a: i32, b: i32) -> i32 {
    a + b
}
'''

        test_file = Path("/tmp/hello.rs")

        try:
            # Write test file
            test_file.write_text(test_code)

            # Compile
            compile_result = subprocess.run(
                ["rustc", str(test_file), "-o", "/tmp/hello_rust"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if compile_result.returncode != 0:
                self.result.add_check(
                    name="rust_compilation",
                    passed=False,
                    error=f"Compilation failed: {compile_result.stderr}"
                )
                return

            self.result.add_check(
                name="rust_compilation",
                passed=True,
                output="Rust code compiled successfully"
            )

            # Run
            run_result = subprocess.run(
                ["/tmp/hello_rust"],
                capture_output=True,
                text=True,
                timeout=30
            )

            expected_output = "Rust compilation and execution works!"
            success = run_result.returncode == 0 and expected_output in run_result.stdout

            self.result.add_check(
                name="rust_execution",
                passed=success,
                output=run_result.stdout.strip() if success else None,
                error=run_result.stderr if not success else None
            )

        except Exception as e:
            self.result.add_check(
                name="rust_compilation_execution",
                passed=False,
                error=f"Error during Rust test: {str(e)}"
            )
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
            binary_path = Path("/tmp/hello_rust")
            if binary_path.exists():
                binary_path.unlink()

    def test_cargo_project(self):
        """Test cargo project creation and build."""
        temp_dir = None

        try:
            # Create temporary directory
            temp_dir = Path(tempfile.mkdtemp(prefix="cargo_test_"))

            # Create new cargo project
            new_result = subprocess.run(
                ["cargo", "new", "hello", "--bin"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            project_dir = temp_dir / "hello"
            success = new_result.returncode == 0 and project_dir.exists()

            self.result.add_check(
                name="cargo_new",
                passed=success,
                output="Cargo project created" if success else None,
                error=new_result.stderr if not success else None
            )

            if not success:
                return

            # Build the project
            build_result = subprocess.run(
                ["cargo", "build"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=120
            )

            success = build_result.returncode == 0

            self.result.add_check(
                name="cargo_build",
                passed=success,
                output="Cargo build successful" if success else None,
                error=build_result.stderr if not success else None
            )

        except Exception as e:
            self.result.add_check(
                name="cargo_project",
                passed=False,
                error=f"Error during cargo test: {str(e)}"
            )
        finally:
            # Cleanup
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main_template(RustTest)
