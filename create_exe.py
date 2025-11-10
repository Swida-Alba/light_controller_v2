"""
Create executable for Light Controller v2.2

This script uses PyInstaller to create a standalone executable that includes
all dependencies (pandas, numpy, pyserial, openpyxl, tkinter).

Usage:
    python create_exe.py

Output:
    - dist/protocol_parser.exe (Windows)
    - dist/protocol_parser (macOS/Linux)
"""

import os
import sys
import subprocess
import platform

def check_dependencies():
    """Check and install required dependencies."""
    dependencies = ['pyinstaller', 'pandas', 'numpy', 'pyserial', 'openpyxl']
    
    print("Checking dependencies...")
    for package in dependencies:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} not found. Installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to install {package}: {e}")
                return False
    
    print("\nAll dependencies satisfied!\n")
    return True

def create_executable(script_name='protocol_parser.py'):
    """
    Create standalone executable using PyInstaller.
    
    Args:
        script_name: Name of the Python script to compile (default: protocol_parser.py)
    """
    
    # Check if script exists
    if not os.path.exists(script_name):
        print(f"Error: {script_name} not found in current directory!")
        return False
    
    # Get additional files that need to be included
    additional_files = []
    
    # Include lcfunc.py and light_controller_parser.py
    if os.path.exists('lcfunc.py'):
        additional_files.append('lcfunc.py')
    if os.path.exists('light_controller_parser.py'):
        additional_files.append('light_controller_parser.py')
    
    # Build PyInstaller command
    command = [
        'pyinstaller',
        '--onefile',                    # Create single executable
        '--windowed',                   # No console window (remove for debugging)
        '--name=LightController',       # Executable name
        '--clean',                      # Clean cache before building
    ]
    
    # Add hidden imports for all dependencies
    hidden_imports = [
        'pandas',
        'numpy',
        'serial',
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.cell._writer',
        'tkinter',
        'tkinter.filedialog',
        'ast',
        'datetime',
        're',
        'time',
        'math',
    ]
    
    for module in hidden_imports:
        command.extend(['--hidden-import', module])
    
    # Add additional Python files as data
    for file in additional_files:
        command.extend(['--add-data', f'{file}{os.pathsep}.'])
    
    # Add icon if exists (optional)
    if os.path.exists('icon.ico'):
        command.extend(['--icon', 'icon.ico'])
    
    # Add the main script
    command.append(script_name)
    
    # Print command for debugging
    print("Running PyInstaller with command:")
    print(' '.join(command))
    print()
    
    # Run PyInstaller
    try:
        result = subprocess.run(command, check=True)
        
        # Success message
        system = platform.system()
        if system == "Windows":
            executable_path = os.path.join('dist', 'LightController.exe')
        else:
            executable_path = os.path.join('dist', 'LightController')
        
        print("\n" + "="*60)
        print("✓ Executable created successfully!")
        print("="*60)
        print(f"\nLocation: {os.path.abspath(executable_path)}")
        print(f"\nTo run:")
        if system == "Windows":
            print(f"  {executable_path}")
        else:
            print(f"  ./{executable_path}")
        print("\nNote: Executable includes all dependencies (pandas, numpy, pyserial, openpyxl)")
        print("="*60)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error creating executable: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed: pip install -r requirements.txt")
        print("2. Try removing --windowed flag for console output")
        print("3. Check build/warnings.txt for details")
        return False

def clean_build_files():
    """Clean up PyInstaller build files."""
    import shutil
    
    dirs_to_remove = ['build', '__pycache__']
    files_to_remove = ['LightController.spec']
    
    print("\nCleaning build files...")
    for dirname in dirs_to_remove:
        if os.path.exists(dirname):
            shutil.rmtree(dirname)
            print(f"  Removed {dirname}/")
    
    for filename in files_to_remove:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"  Removed {filename}")
    
    print("✓ Build files cleaned\n")

if __name__ == "__main__":
    print("="*60)
    print("Light Controller v2.2 - Executable Builder")
    print("="*60)
    print()
    
    # Check Python version
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required!")
        sys.exit(1)
    
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print()
    
    # Check and install dependencies
    if not check_dependencies():
        print("\nFailed to install dependencies. Exiting.")
        sys.exit(1)
    
    # Create executable
    script_name = 'protocol_parser.py'
    success = create_executable(script_name)
    
    # Clean up build files (optional)
    if success:
        response = input("\nClean up build files? (y/n): ")
        if response.lower() == 'y':
            clean_build_files()
    
    sys.exit(0 if success else 1)
