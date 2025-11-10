# Light Controller v2.2 - Build Configuration

## Executable Creation

This directory contains scripts to create standalone executables for Light Controller v2.2.

### Requirements

- Python 3.6 or higher
- All dependencies from `requirements.txt`
- PyInstaller (will be auto-installed)

### Quick Start

```bash
# Create executable (includes all dependencies)
python create_exe.py

# Output will be in dist/ folder
# Windows: dist/LightController.exe
# macOS/Linux: dist/LightController
```

### What Gets Included

The executable includes:
- **Core modules**: `protocol_parser.py`, `light_controller_parser.py`, `lcfunc.py`
- **Dependencies**: pandas, numpy, pyserial, openpyxl, tkinter
- **All required Python libraries**

### Build Options

Edit `create_exe.py` to customize:

```python
# Show console window (useful for debugging)
command = [
    'pyinstaller',
    '--onefile',
    # '--windowed',  # Comment out to show console
    ...
]

# Add custom icon
if os.path.exists('icon.ico'):
    command.extend(['--icon', 'icon.ico'])

# Include example files
command.extend(['--add-data', 'examples{os.pathsep}examples'])
```

### Platform-Specific Notes

**Windows:**
- Creates `.exe` file
- May need to run as administrator
- Windows Defender may flag it (false positive)

**macOS:**
- Creates Unix executable
- May need to allow in Security & Privacy settings
- Run: `chmod +x dist/LightController`

**Linux:**
- Creates ELF executable
- Requires `python3-tk` package: `sudo apt install python3-tk`

### Troubleshooting

**"Module not found" error:**
```bash
# Install all dependencies first
pip install -r requirements.txt

# Then rebuild
python create_exe.py
```

**"DLL load failed" (Windows):**
- Install Visual C++ Redistributable
- Rebuild with Python 3.8+ (better compatibility)

**Executable too large:**
```bash
# Use UPX compression (optional)
pip install pyinstaller[encryption]
pyinstaller --onefile --upx-dir=/path/to/upx protocol_parser.py
```

**Import errors in built executable:**
- Check `build/warnings.txt`
- Add missing modules to `hidden_imports` list in `create_exe.py`

### Advanced: Manual PyInstaller

For more control, run PyInstaller directly:

```bash
# Basic build
pyinstaller --onefile protocol_parser.py

# With all hidden imports
pyinstaller --onefile \
  --hidden-import=pandas \
  --hidden-import=numpy \
  --hidden-import=serial \
  --hidden-import=openpyxl \
  --hidden-import=tkinter \
  --add-data="lcfunc.py:." \
  --add-data="light_controller_parser.py:." \
  --name=LightController \
  protocol_parser.py

# With compression (smaller file size)
pyinstaller --onefile --upx-dir=/usr/bin/upx protocol_parser.py

# Debug mode (keeps build files)
pyinstaller --onefile --debug=all protocol_parser.py
```

### File Structure After Build

```
light_controller_v2.2/
├── create_exe.py              # Build script
├── build/                     # Temporary build files (can delete)
│   └── LightController/
├── dist/                      # OUTPUT - Executable here!
│   └── LightController(.exe)  # ← Your standalone executable
├── LightController.spec       # PyInstaller spec file (can delete)
└── __pycache__/              # Python cache (can delete)
```

### Distribution

To distribute the executable:

1. **Package contents:**
   ```
   LightController/
   ├── LightController(.exe)  # The executable
   ├── examples/              # Example protocol files
   ├── README.txt             # Usage instructions
   └── docs/                  # Documentation (optional)
   ```

2. **Zip the folder:**
   ```bash
   # Windows
   Compress-Archive -Path LightController -DestinationPath LightController_v2.2_win64.zip
   
   # macOS/Linux
   zip -r LightController_v2.2_macos.zip LightController/
   ```

3. **Test on clean system:**
   - No Python installation required
   - Arduino drivers may still be needed
   - Antivirus software may need approval

### Performance

**Executable size:**
- Typical: 50-100 MB (includes Python interpreter + all libraries)
- With UPX compression: 30-60 MB

**Startup time:**
- First run: 2-5 seconds (unpacking)
- Subsequent runs: 1-2 seconds

**RAM usage:**
- Idle: ~50 MB
- Processing large Excel: 100-200 MB

### Security Notes

- Executable may be flagged by antivirus (false positive)
- To avoid: Sign executable with code signing certificate
- Windows SmartScreen: Users may need to click "More info" → "Run anyway"

### Updates

When updating the code:

1. Update source files (`protocol_parser.py`, etc.)
2. Test with `python protocol_parser.py`
3. Rebuild executable: `python create_exe.py`
4. Test executable in clean environment
5. Redistribute new version

---

**Need Help?**
- See [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- Check PyInstaller docs: https://pyinstaller.org
- Report issues: https://github.com/Swida-Alba/light_controller_v2/issues
