#!/usr/bin/env python3
"""
Simple PyInstaller build script for Light Controller v2.2

This is a simplified version of create_exe.py with minimal dependencies checking.
Use this if create_exe.py has issues.

Usage:
    python simple_build.py
"""

import subprocess
import sys
import os

def main():
    print("="*60)
    print("Light Controller v2.2 - Simple Build")
    print("="*60)
    print()
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✓ PyInstaller found")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed")
    
    print()
    
    # Basic PyInstaller command
    command = [
        'pyinstaller',
        '--onefile',
        '--name=LightController',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=serial',
        '--hidden-import=openpyxl',
        '--hidden-import=tkinter',
        'protocol_parser.py'
    ]
    
    print("Building executable...")
    print("Command:", ' '.join(command))
    print()
    
    result = subprocess.run(command)
    
    if result.returncode == 0:
        print()
        print("="*60)
        print("✓ Build successful!")
        print("="*60)
        print()
        print("Executable location: dist/LightController")
        print()
    else:
        print()
        print("✗ Build failed!")
        print("Try: python create_exe.py (more detailed version)")
        sys.exit(1)

if __name__ == "__main__":
    main()
