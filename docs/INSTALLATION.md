# Installation Guide

Complete installation instructions for Light Controller V2.2.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Software Installation](#software-installation)
- [Arduino Setup](#arduino-setup)
- [Python Environment](#python-environment)
- [Verification](#verification)
- [Troubleshooting Installation](#troubleshooting-installation)

---

## Prerequisites

### Required Hardware

- **Arduino Board**: Uno, Due, Mega, or compatible
- **USB Cable**: Type-A to Type-B (Uno/Mega) or Micro-USB (Due)
- **LEDs**: Compatible with your Arduino (3.3V or 5V depending on board)
- **Resistors**: 220Ω - 1kΩ (current-limiting for LEDs)
- **Computer**: Windows, macOS, or Linux

### Required Software

1. **Python 3.6 or higher**
   - Download: [python.org/downloads](https://www.python.org/downloads/)
   - Verify: `python --version` or `python3 --version`

2. **Arduino IDE** (optional but recommended)
   - Download: [arduino.cc/en/software](https://www.arduino.cc/en/software)
   - Alternative: arduino-cli for command-line operation

3. **Git** (optional, for cloning)
   - Download: [git-scm.com](https://git-scm.com/)

---

## Software Installation

### Option 1: Clone from GitHub

```bash
# Clone the repository
git clone https://github.com/Swida-Alba/light_controller_v2.git
cd light_controller_v2.2

# Install Python dependencies
pip install -r requirements.txt
```

### Option 2: Download ZIP

1. Download ZIP from GitHub repository
2. Extract to your desired location
3. Open terminal/command prompt in extracted folder
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Option 3: Using setup.py

```bash
# Install as package
python setup.py install

# Or install in development mode
python setup.py develop
```

---

## Arduino Setup

### Step 1: Open Arduino Sketch

1. Launch Arduino IDE
2. Open File → Open
3. Navigate to `light_controller_v2_2_arduino/light_controller_v2_2_arduino.ino`

### Step 2: Configure Sketch

Edit these constants according to your setup:

```cpp
// Maximum number of channels (must not exceed Arduino memory)
#define MAX_CHANNEL_NUM 6

// Maximum number of patterns
#define MAX_PATTERN_NUM 10

// Pin assignments (modify for your wiring)
int channelPins[] = {2, 3, 4, 5, 6, 7};
```

**Important Notes:**
- Arduino Uno: Recommended max 6-8 channels
- Arduino Due/Mega: Can handle more channels
- Pins 0-1 reserved for serial communication (don't use)

### Step 3: Select Board and Port

**Arduino Uno/Mega:**
1. Tools → Board → Arduino Uno (or Mega)
2. Tools → Port → Select your port
   - macOS: `/dev/cu.usbmodem*` or `/dev/cu.usbserial*`
   - Windows: `COM3`, `COM4`, etc.
   - Linux: `/dev/ttyUSB*` or `/dev/ttyACM*`

**Arduino Due:**
- See [Arduino Due Setup Guide](ARDUINO_DUE.md) for detailed instructions

### Step 4: Upload Sketch

1. Click **Upload** button (→) or Ctrl+U (Cmd+U on Mac)
2. Wait for "Done uploading" message
3. Check for errors in console

### Step 5: Verify Upload

1. Open Serial Monitor (Tools → Serial Monitor)
2. Set baud rate to **9600**
3. Type `Hello` and press Enter
4. You should see response: `Salve`

---

## Python Environment

### Virtual Environment (Recommended)

Create an isolated Python environment:

```bash
# Create virtual environment
python -m venv venv

# Activate on macOS/Linux
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Required Packages

The following packages will be installed:

- **pyserial**: Arduino serial communication
- **pandas**: Excel file processing
- **openpyxl**: Excel file reading/writing
- **numpy**: Numerical operations
- **xlrd**: Legacy Excel support (optional)

### Check Installation

```bash
# Verify packages
pip list | grep -E "(pyserial|pandas|openpyxl)"

# Or check individually
python -c "import serial; print('pyserial:', serial.__version__)"
python -c "import pandas; print('pandas:', pandas.__version__)"
python -c "import openpyxl; print('openpyxl:', openpyxl.__version__)"
```

---

## Verification

### Test 1: Serial Connection

```bash
python test_serial_connection.py
```

**Expected Output:**
```
Searching for Arduino...
Found Arduino on port: /dev/cu.usbmodem14101
Testing communication...
✓ Arduino responded correctly
✓ Connection test passed!
```

### Test 2: Protocol Parser

```bash
python protocol_parser.py
```

**Expected Behavior:**
1. File selection dialog appears
2. Select an example file from `examples/` folder
3. Program connects to Arduino
4. Calibration starts (first run only)
5. Commands sent to Arduino

### Test 3: Example Protocol

Use a test protocol:

```bash
# Copy example to working directory
cp examples/protocol.xlsx test_protocol.xlsx

# Run with test file
python protocol_parser.py
# Select test_protocol.xlsx when prompted
```

---

## Troubleshooting Installation

### Python Not Found

**Problem:** `python: command not found`

**Solutions:**
- Try `python3` instead of `python`
- Add Python to PATH:
  - Windows: System Properties → Environment Variables
  - macOS/Linux: Add to `.bashrc` or `.zshrc`
- Reinstall Python with "Add to PATH" option checked

### Pip Installation Fails

**Problem:** `pip install` fails with permission error

**Solutions:**
```bash
# Use --user flag
pip install --user -r requirements.txt

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Arduino Port Not Found

**Problem:** Arduino not showing in Tools → Port

**Solutions:**
1. Check USB cable (must be data cable, not charge-only)
2. Install Arduino drivers:
   - Windows: CH340 or FTDI drivers
   - macOS: Usually automatic
   - Linux: Add user to `dialout` group
3. Try different USB port
4. Restart Arduino IDE

### Serial Permission Denied (Linux)

**Problem:** `Permission denied: '/dev/ttyUSB0'`

**Solution:**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Log out and log back in, or:
newgrp dialout

# Verify
groups | grep dialout
```

### Upload Failed

**Problem:** `avrdude: stk500_recv(): programmer is not responding`

**Solutions:**
1. Press RESET button on Arduino
2. Close Serial Monitor before uploading
3. Select correct board type
4. Try different USB port
5. Check for conflicting software (Processing, PlatformIO)

### Package Conflicts

**Problem:** `ImportError` or version conflicts

**Solutions:**
```bash
# Create fresh virtual environment
python -m venv fresh_env
source fresh_env/bin/activate

# Install specific versions
pip install pyserial==3.5
pip install pandas==2.0.3
pip install openpyxl==3.1.2

# Or upgrade all
pip install --upgrade -r requirements.txt
```

### Arduino Due Upload Issues

**Problem:** Upload fails on Arduino Due

**Solution:**
- See detailed guide: [Arduino Due Setup](ARDUINO_DUE.md)
- Use Programming Port instead of Native USB
- Press RESET button at right time
- Check board selection in Tools menu

---

## Platform-Specific Notes

### macOS

- Serial ports: `/dev/cu.usbmodem*` or `/dev/cu.usbserial*`
- May need to allow Python in Security & Privacy settings
- Homebrew can help: `brew install python`

### Windows

- Serial ports: `COM3`, `COM4`, etc.
- May need CH340 drivers for clone boards
- Use PowerShell or Command Prompt
- Watch for antivirus blocking serial access

### Linux

- Serial ports: `/dev/ttyUSB*` or `/dev/ttyACM*`
- Add user to `dialout` group (see above)
- May need to install `python3-pip` separately
- Use `sudo` for system-wide installation

---

## Next Steps

After successful installation:

1. ✅ Read [Features Guide](FEATURES.md) to understand capabilities
2. ✅ Review [Usage Guide](USAGE.md) for operation instructions
3. ✅ Study [Protocol Formats](PROTOCOL_FORMATS.md) to create schedules
4. ✅ Check [Examples](EXAMPLES.md) for sample protocols

---

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/Swida-Alba/light_controller_v2/issues)
- **Documentation**: Check other docs in `docs/` folder
- **Examples**: See `examples/` folder for working protocols

---

*Last Updated: November 8, 2025*
