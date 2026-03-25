#!/usr/bin/env python3
"""
Docker Build Validation Script

Validates that all files and dependencies are ready for Docker build.
Run this before deploying to Nest.
"""

import os
import sys

# Set up environment
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("=" * 60)
    print("  ITC Form Generator - Docker Build Validation")
    print("=" * 60)
    print()

    errors = []
    warnings = []

    # Check required files
    print("--- Required Files ---")
    required_files = [
        ("webapp.py", "Main web application"),
        ("Dockerfile", "Docker build instructions"),
        ("nest.json", "Nest configuration"),
        ("requirements.txt", "Python dependencies"),
        (".dockerignore", "Docker ignore rules"),
        ("src/itc_form_generator/__init__.py", "Package init"),
        ("src/itc_form_generator/parser.py", "SOO Parser"),
        ("src/itc_form_generator/models.py", "Data models"),
        ("src/itc_form_generator/form_generator.py", "Form generator"),
        ("src/itc_form_generator/exporter.py", "Excel/CSV exporter"),
        ("src/itc_form_generator/points_parser.py", "Points list parser"),
        ("src/itc_form_generator/pdf_parser.py", "PDF parser"),
        ("src/itc_form_generator/renderer.py", "HTML renderer"),
    ]

    for filepath, desc in required_files:
        if os.path.exists(filepath):
            print(f"[OK] {filepath}")
        else:
            print(f"[MISSING] {filepath} - {desc}")
            errors.append(f"Missing required file: {filepath}")

    print()

    # Check optional files
    print("--- Optional Files ---")
    optional_files = [
        ("sample_soo.md", "Sample SOO document"),
        ("sample_points_list.csv", "Sample points list"),
        ("launcher.py", "CLI launcher"),
        ("NEST_DEPLOYMENT.md", "Deployment guide"),
    ]

    for filepath, desc in optional_files:
        if os.path.exists(filepath):
            print(f"[OK] {filepath}")
        else:
            print(f"[SKIP] {filepath} - {desc}")

    print()

    # Check Python dependencies
    print("--- Python Dependencies ---")
    try:
        import pymupdf
        print("[OK] pymupdf (PDF support)")
    except ImportError:
        print("[WARN] pymupdf not installed - install with: pip install pymupdf")
        warnings.append("pymupdf not installed")

    try:
        import openpyxl
        print("[OK] openpyxl (Excel support)")
    except ImportError:
        print("[WARN] openpyxl not installed - install with: pip install openpyxl")
        warnings.append("openpyxl not installed")

    print()

    # Check app module imports
    print("--- App Module Imports ---")
    try:
        from itc_form_generator.parser import SOOParser
        from itc_form_generator.form_generator import FormGenerator
        from itc_form_generator.exporter import FormExporter
        from itc_form_generator.points_parser import PointsListParser
        from itc_form_generator.pdf_parser import PDFParser
        from itc_form_generator.renderer import HTMLRenderer
        print("[OK] All app modules import successfully")
    except Exception as e:
        print(f"[FAIL] Import error: {e}")
        errors.append(f"Module import failed: {e}")

    print()

    # Check webapp configuration
    print("--- Webapp Configuration ---")
    try:
        with open("webapp.py", "r", encoding="utf-8") as f:
            webapp_content = f.read()

        checks = [
            ("PORT env var", "PORT = int(os.environ.get"),
            ("HOSTNAME config", "HOSTNAME = os.environ.get"),
            ("/api/health endpoint", "/api/health"),
            ("Health check handler", "_serve_health_check"),
            ("JSON health response", '"status": "healthy"'),
        ]

        for name, pattern in checks:
            if pattern in webapp_content:
                print(f"[OK] {name}")
            else:
                print(f"[MISSING] {name}")
                errors.append(f"Webapp missing: {name}")
    except Exception as e:
        print(f"[FAIL] Could not read webapp.py: {e}")
        errors.append(f"Cannot read webapp.py: {e}")

    print()

    # Check Dockerfile
    print("--- Dockerfile Validation ---")
    try:
        with open("Dockerfile", "r", encoding="utf-8") as f:
            dockerfile_content = f.read()

        checks = [
            ("FROM python", "FROM python:"),
            ("WORKDIR /app", "WORKDIR /app"),
            ("COPY requirements", "COPY requirements.txt"),
            ("pip install", "pip install"),
            ("EXPOSE 3000", "EXPOSE 3000"),
            ("ENV PORT=3000", "ENV PORT=3000"),
            ("HEALTHCHECK", "HEALTHCHECK"),
            ("CMD python", "CMD ["),
        ]

        for name, pattern in checks:
            if pattern in dockerfile_content:
                print(f"[OK] {name}")
            else:
                print(f"[MISSING] {name}")
                errors.append(f"Dockerfile missing: {name}")
    except Exception as e:
        print(f"[FAIL] Could not read Dockerfile: {e}")
        errors.append(f"Cannot read Dockerfile: {e}")

    print()

    # Check nest.json
    print("--- nest.json Validation ---")
    try:
        import json
        with open("nest.json", "r", encoding="utf-8") as f:
            nest_config = json.load(f)

        required_keys = ["oncall", "framework", "container"]
        for key in required_keys:
            if key in nest_config:
                print(f"[OK] {key}: {nest_config[key]}")
            else:
                print(f"[MISSING] {key}")
                errors.append(f"nest.json missing: {key}")

        if nest_config.get("framework") != "custom":
            print("[WARN] framework should be 'custom' for Python apps")
            warnings.append("framework should be 'custom'")
    except Exception as e:
        print(f"[FAIL] Could not parse nest.json: {e}")
        errors.append(f"Invalid nest.json: {e}")

    print()

    # Summary
    print("=" * 60)
    if errors:
        print(f"  VALIDATION FAILED - {len(errors)} error(s)")
        print("=" * 60)
        for err in errors:
            print(f"  ERROR: {err}")
    elif warnings:
        print(f"  VALIDATION PASSED with {len(warnings)} warning(s)")
        print("=" * 60)
        for warn in warnings:
            print(f"  WARN: {warn}")
    else:
        print("  VALIDATION PASSED - Ready for Docker build!")
        print("=" * 60)

    print()
    print("Next steps:")
    print("  1. Copy files to OD: ~/fbsource/nest/apps/itc_form_generator/")
    print("  2. Build container: nest build")
    print("  3. Test locally: nest build --run")
    print("  4. Deploy: jf submit")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
