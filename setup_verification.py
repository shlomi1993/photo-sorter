#!/usr/bin/env python3
"""
Setup script for the Photo Sorting Tool.

This script helps set up the tool and verify that everything is working correctly.
"""

import subprocess
import sys

from pathlib import Path


def run_command(command, description=""):
    """
    Run a command and return success status.
    """
    print(f"{'Running: ' + description if description else 'Running:'} {' '.join(command)}")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("✓ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False


def check_python_version():
    """
    Check if Python version is 3.8 or higher.
    """
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (Requires Python 3.8+)")
        return False


def setup_virtual_environment():
    """
    Create and activate virtual environment.
    """
    venv_path = Path(".venv")

    if venv_path.exists():
        print("✓ Virtual environment already exists")
        return True

    print("Creating virtual environment...")
    return run_command([sys.executable, "-m", "venv", ".venv"], "Creating virtual environment")


def get_python_executable():
    """
    Get the path to the Python executable in the virtual environment.
    """
    venv_path = Path(".venv")

    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def install_dependencies():
    """
    Install required Python packages.
    """
    python_exe = get_python_executable()

    print("Installing dependencies...")
    success = run_command([str(python_exe), "-m", "pip", "install", "-r", "requirements.txt"],
                         "Installing from requirements.txt")

    if not success:
        print("Trying to install dependencies individually...")
        # Essential packages that should work on most systems
        essential_packages = [
            "Pillow>=10.0.0",
            "python-dateutil>=2.8.2",
            "colorama>=0.4.6",
            "mutagen>=1.47.0",
            "pyexiv2>=2.11.0"
        ]

        all_installed = True
        for package in essential_packages:
            all_installed = (
                run_command(
                    [str(python_exe), "-m", "pip", "install", package],
                    f"Installing {package}"
                )
                and all_installed
            )

        return all_installed

    return success


def test_installation():
    """
    Test that the installation is working.
    """
    python_exe = get_python_executable()

    print("Testing imports...")
    test_import = run_command([
        str(python_exe), "-c",
        "import pyexiv2; "
        "from colorama import Fore, init; init(); "
        "from photo_sorting import extract_date_from_directory, MetadataReader, MetadataWriter, setup_logger; "
        "print(f'{Fore.GREEN}pyexiv2, Colorama, and all package imports successful!')"
    ], "Testing imports")

    if test_import:
        print("✓ All imports working correctly")

    print("Running basic functionality test...")
    test_functionality = run_command([str(python_exe), "test_script.py"], "Running test script")

    return test_import and test_functionality


def create_example_command():
    """
    Create an example command for the user.
    """
    python_exe = get_python_executable()

    example_commands = [
        f"\n# Run with a real directory from your photo collection:",
        f'{python_exe} main.py --directory "/path/to/your/photos/YYYY.MM.DD - Event Name" --dry-run --verbose',
        f"\n# Run the test script to verify everything works:",
        f'{python_exe} test_script.py',
        f"\n# For help:",
        f'{python_exe} main.py --help'
    ]

    return "\n".join(example_commands)


def main():
    """
    Main setup function.
    """
    print("Photo Sorting Tool - Setup Script")
    print("=" * 40)

    # Check Python version
    if not check_python_version():
        print("\n❌ Setup failed: Python version too old")
        print("Please install Python 3.8 or higher and try again.")
        return False

    # Setup virtual environment
    if not setup_virtual_environment():
        print("\n❌ Setup failed: Could not create virtual environment")
        return False

    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed: Could not install dependencies")
        return False

    # Test installation
    print("\nTesting installation...")
    if not test_installation():
        print("\n⚠️  Setup completed but tests failed")
        print("The tool may work with limited functionality.")
    else:
        print("\n✅ Setup completed successfully!")

    # Show usage examples
    print("\nNext steps:")
    print(create_example_command())

    print(f"\n{'=' * 40}")
    print("Setup complete! You can now use the photo sorting tool.")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
