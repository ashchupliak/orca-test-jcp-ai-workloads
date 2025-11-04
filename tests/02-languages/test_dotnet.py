#!/usr/bin/env python3
"""
.NET/C# development environment test.
Validates .NET SDK, project creation, and build.
"""

import sys
import subprocess
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class DotNetTest(BaseTest):
    """Test .NET development tools."""

    def __init__(self):
        super().__init__("dotnet_development")

    def run(self):
        """Run .NET toolchain tests."""
        print("="*80)
        print(".NET Development Environment Test")
        print("="*80)

        # Check dotnet
        self.check_command_exists("dotnet", ".NET SDK")
        success, version = self.check_version("dotnet")
        if success:
            # Extract version from first line
            for line in version.split('\n'):
                if 'Version:' in line or line.strip().startswith(('6.', '7.', '8.')):
                    self.result.set_metadata("dotnet_version", line.strip())
                    break

        # Test .NET project creation and build
        self.test_dotnet_project()

        return self.result

    def test_dotnet_project(self):
        """Test .NET project creation, build, and run."""
        temp_dir = None

        try:
            # Create temporary directory
            temp_dir = Path(tempfile.mkdtemp(prefix="dotnet_test_"))

            # Create new console app
            new_result = subprocess.run(
                ["dotnet", "new", "console", "-n", "HelloApp", "-o", "HelloApp"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            project_dir = temp_dir / "HelloApp"
            success = new_result.returncode == 0 and project_dir.exists()

            self.result.add_check(
                name="dotnet_new_console",
                passed=success,
                output=".NET console project created" if success else None,
                error=new_result.stderr if not success else None
            )

            if not success:
                return

            # Modify Program.cs to have custom output
            program_file = project_dir / "Program.cs"
            custom_code = '''using System;

namespace HelloApp
{
    class Program
    {
        static void Main(string[] args)
        {
            int result = Add(2, 2);
            Console.WriteLine($".NET compilation and execution works! 2 + 2 = {result}");
        }

        static int Add(int a, int b)
        {
            return a + b;
        }
    }
}
'''
            program_file.write_text(custom_code)

            # Build the project
            build_result = subprocess.run(
                ["dotnet", "build"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=120
            )

            success = build_result.returncode == 0

            self.result.add_check(
                name="dotnet_build",
                passed=success,
                output="Project built successfully" if success else None,
                error=build_result.stderr if not success else None
            )

            if not success:
                return

            # Run the project
            run_result = subprocess.run(
                ["dotnet", "run"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            expected_output = ".NET compilation and execution works!"
            success = run_result.returncode == 0 and expected_output in run_result.stdout

            self.result.add_check(
                name="dotnet_run",
                passed=success,
                output=run_result.stdout.strip() if success else None,
                error=run_result.stderr if not success else None
            )

        except Exception as e:
            self.result.add_check(
                name="dotnet_project",
                passed=False,
                error=f"Error during .NET test: {str(e)}"
            )
        finally:
            # Cleanup
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main_template(DotNetTest)
