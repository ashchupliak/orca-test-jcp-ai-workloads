#!/usr/bin/env python3
"""
Java development environment test.
Validates Java, Maven, and Gradle toolchains.
"""

import sys
import subprocess
from pathlib import Path

# Add parent directory to path to import common utilities
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.test_framework import BaseTest, main_template


class JavaTest(BaseTest):
    """Test Java development tools."""

    def __init__(self):
        super().__init__("java_development")

    def run(self):
        """Run Java toolchain tests."""
        print("Testing Java development environment...")

        # Check Java
        self.check_command_exists("java", "Java runtime")
        success, version = self.check_version("java")
        if success:
            self.result.set_metadata("java_version", version.split('\n')[0])

        # Check javac
        self.check_command_exists("javac", "Java compiler")

        # Check Maven
        if self.check_command_exists("mvn", "Maven"):
            success, version = self.check_version("mvn")
            if success:
                self.result.set_metadata("maven_version", version.split('\n')[0])

        # Check Gradle
        gradle_exists = self.check_command_exists("gradle", "Gradle")
        if gradle_exists:
            success, version = self.check_version("gradle")
            if success:
                # Extract version line
                for line in version.split('\n'):
                    if 'Gradle' in line:
                        self.result.set_metadata("gradle_version", line.strip())
                        break

        # Check JAVA_HOME
        import os
        java_home = os.getenv("JAVA_HOME")
        self.result.add_check(
            name="JAVA_HOME_set",
            passed=java_home is not None,
            output=f"JAVA_HOME={java_home}" if java_home else None,
            error="JAVA_HOME environment variable not set" if not java_home else None
        )

        # Compile and run a simple Java program
        self.compile_and_run_java()

        return self.result

    def compile_and_run_java(self):
        """Compile and run a simple Java program."""
        test_code = '''public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Java compilation and execution works!");
    }
}'''

        test_file = Path("/tmp/HelloWorld.java")
        class_file = Path("/tmp/HelloWorld.class")

        try:
            # Write test file
            test_file.write_text(test_code)

            # Compile
            compile_result = subprocess.run(
                ["javac", str(test_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if compile_result.returncode != 0:
                self.result.add_check(
                    name="java_compilation",
                    passed=False,
                    error=f"Compilation failed: {compile_result.stderr}"
                )
                return

            self.result.add_check(
                name="java_compilation",
                passed=True,
                output="Java code compiled successfully"
            )

            # Run
            run_result = subprocess.run(
                ["java", "-cp", "/tmp", "HelloWorld"],
                capture_output=True,
                text=True,
                timeout=30
            )

            expected_output = "Java compilation and execution works!"
            success = run_result.returncode == 0 and expected_output in run_result.stdout

            self.result.add_check(
                name="java_execution",
                passed=success,
                output=run_result.stdout.strip() if success else None,
                error=run_result.stderr if not success else None
            )

        except Exception as e:
            self.result.add_check(
                name="java_compilation_execution",
                passed=False,
                error=f"Error during Java test: {str(e)}"
            )
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
            if class_file.exists():
                class_file.unlink()


if __name__ == "__main__":
    main_template(JavaTest)
