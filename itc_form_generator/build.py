#!/usr/bin/env python3
"""
ITC Form Generator — Build Script

Automates building for different distribution formats.

Usage:
    python build.py pip        # Build pip package (wheel + sdist)
    python build.py exe        # Build standalone executable (PyInstaller)
    python build.py docker     # Build Docker image
    python build.py all        # Build all formats
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

VERSION = "2.0.0"
PROJECT_DIR = Path(__file__).parent
DIST_DIR = PROJECT_DIR / "dist"


def build_pip():
    """Build pip-installable package."""
    print("\n📦 Building pip package...")

    # Clean previous builds
    for d in ['build', 'dist', '*.egg-info']:
        for p in PROJECT_DIR.glob(d):
            shutil.rmtree(p, ignore_errors=True)

    # Build wheel and sdist
    subprocess.run([sys.executable, "-m", "build"], check=True, cwd=PROJECT_DIR)

    print("✅ Pip package built!")
    print(f"   📁 dist/itc_form_generator-{VERSION}.tar.gz")
    print(f"   📁 dist/itc_form_generator-{VERSION}-py3-none-any.whl")
    print(f"\n   Install with: pip install dist/itc_form_generator-{VERSION}-py3-none-any.whl")


def build_exe():
    """Build standalone executable with PyInstaller."""
    print("\n🔨 Building standalone executable...")

    # Check PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # Run PyInstaller
    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "ITC_Form_Generator.spec",
        "--clean",
        "--noconfirm",
    ], check=True, cwd=PROJECT_DIR)

    print("✅ Executable built!")
    if sys.platform == 'win32':
        print(f"   📁 dist/ITC_Form_Generator/ITC_Form_Generator.exe")
    elif sys.platform == 'darwin':
        print(f"   📁 dist/ITC Form Generator.app")
    else:
        print(f"   📁 dist/ITC_Form_Generator/ITC_Form_Generator")


def build_docker():
    """Build Docker image."""
    print("\n🐳 Building Docker image...")

    subprocess.run([
        "docker", "build",
        "-t", f"itc-form-generator:{VERSION}",
        "-t", "itc-form-generator:latest",
        ".",
    ], check=True, cwd=PROJECT_DIR)

    print("✅ Docker image built!")
    print(f"   🐳 itc-form-generator:{VERSION}")
    print(f"\n   Run with: docker run -p 8080:8080 itc-form-generator:{VERSION}")
    print(f"   Or:       docker-compose up")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    target = sys.argv[1].lower()

    if target == 'pip':
        build_pip()
    elif target == 'exe':
        build_exe()
    elif target == 'docker':
        build_docker()
    elif target == 'all':
        build_pip()
        build_exe()
        build_docker()
    else:
        print(f"Unknown target: {target}")
        print("Valid targets: pip, exe, docker, all")
        sys.exit(1)


if __name__ == '__main__':
    main()

