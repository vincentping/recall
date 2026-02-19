#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Translation Build Script
Compiles all .ts translation source files to .qm binary files
"""

import os
import sys
import subprocess
from pathlib import Path

# Set console output encoding to UTF-8 (Windows compatibility)
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def get_project_root():
    """Get project root directory"""
    script_dir = Path(__file__).parent
    return script_dir.parent

def find_lrelease():
    """Find pyside6-lrelease executable"""
    project_root = get_project_root()

    # Windows path
    lrelease_exe = project_root / "env" / "Scripts" / "pyside6-lrelease.exe"
    if lrelease_exe.exists():
        return str(lrelease_exe)

    # Linux/Mac path
    lrelease_bin = project_root / "env" / "bin" / "pyside6-lrelease"
    if lrelease_bin.exists():
        return str(lrelease_bin)

    # Try system path
    try:
        result = subprocess.run(['pyside6-lrelease', '-version'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            return 'pyside6-lrelease'
    except FileNotFoundError:
        pass

    return None

def find_ts_files():
    """Find all .ts translation files"""
    project_root = get_project_root()
    translations_dir = project_root / "resources" / "translations"

    if not translations_dir.exists():
        print(f"Error: Translation directory not found: {translations_dir}")
        return []

    ts_files = list(translations_dir.glob("**/*.ts"))
    return ts_files

def compile_ts_file(lrelease_path, ts_file):
    """Compile a single .ts file to .qm file"""
    qm_file = ts_file.with_suffix('.qm')

    print(f"Compiling: {ts_file.name} -> {qm_file.name}")

    try:
        result = subprocess.run(
            [lrelease_path, str(ts_file), '-qm', str(qm_file)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"  ✅ Success: {qm_file.name}")
            return True
        else:
            print(f"  ❌ Failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("Qt Translation Build Script")
    print("=" * 60)

    # 1. Find lrelease tool
    lrelease_path = find_lrelease()
    if not lrelease_path:
        print("❌ Error: Cannot find pyside6-lrelease tool")
        print("Please ensure PySide6 is installed and virtual environment is activated")
        sys.exit(1)

    print(f"Using tool: {lrelease_path}\n")

    # 2. Find all .ts files
    ts_files = find_ts_files()
    if not ts_files:
        print("⚠️  Warning: No .ts files found")
        sys.exit(0)

    print(f"Found {len(ts_files)} translation file(s):\n")

    # 3. Compile each .ts file
    success_count = 0
    failed_count = 0

    for ts_file in ts_files:
        if compile_ts_file(lrelease_path, ts_file):
            success_count += 1
        else:
            failed_count += 1

    # 4. Display results
    print("\n" + "=" * 60)
    print(f"Build complete!")
    print(f"  Success: {success_count} file(s)")
    print(f"  Failed: {failed_count} file(s)")
    print("=" * 60)

    if failed_count > 0:
        sys.exit(1)

if __name__ == '__main__':
    main()
