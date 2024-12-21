import os
import sys
import subprocess

def create_executable(script_name):
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller is not installed. Installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Run PyInstaller to create the executable
    command = f'pyinstaller --onefile {script_name}'
    subprocess.run(command, shell=True)

if __name__ == "__main__":
    script_name = 'protocol_parser.py'
    create_executable(script_name)