# Light Controller V2.2

A flexible Arduino-based light control system with **native pulsing support**, **pattern compression**, **automatic calibration management**, precise timing control, and pulse frequency modulation.

**Version**: 2.2.1  
**Last Updated**: November 10, 2025  
**Status**: Production Ready ✅

---

## 📑 Table of Contents

- [What's New in v2.2](#-whats-new-in-v22) - Latest features including automatic calibration
- [Quick Start](#-quick-start) - Get running in 10 minutes
- [Key Features](#-key-features) - What it can do
- [Examples](#-examples) - Ready-to-use protocols (automatic vs preset calibration)
- [Documentation Index](#-documentation-index) - 50+ organized guides
- [Protocol File Format](#-protocol-file-format) - Syntax reference
- [Project Structure](#-project-structure) - File organization
- [Need Help?](#-need-help) - Support resources

---

## 🎯 What's New in v2.2

### ✨ Automatic Calibration System (NEW!)
- **🤖 Board identification** - Unique ID per Arduino (serial number/VID:PID)
- **💾 Database storage** - Calibrations saved to `calibration_database.json`
- **♻️ Auto-retrieval** - Stored calibrations automatically loaded
- **⏰ 3-month expiration** - Auto-recalibration every 90 days for accuracy
- **🔧 Multi-board support** - Different calibrations for different boards
- **📊 Database management** - View, export, delete calibrations

**Why 3 months?** Crystal oscillators drift ±1-5 ppm/year. Over 3 months, this accumulates to 0.25-1.25 ppm drift, potentially causing 1-4 seconds error over 12-hour protocols. Regular recalibration ensures <1 second timing accuracy.

📖 **[Automatic Calibration Guide](docs/AUTO_CALIBRATION_DATABASE.md)** - Complete system documentation  
📖 **[Backward Compatibility](docs/BACKWARD_COMPATIBILITY.md)** - How old protocols still work

### Pattern-Based Compression System
- **Automatic pattern detection** - Reduces hundreds of commands to just a few
- **Compression ratios up to 37:1** - 97%+ reduction in transmitted data
- **pattern_length parameter** - Optimize for 2-element (default) or 4-element patterns
- **Efficiency analysis** - System recommends optimal pattern_length

📖 **[Pattern Compression Guide](docs/PATTERN_COMPRESSION_GUIDE.md)** - Complete compression details

### Automatic Verification
- **Arduino compatibility checking** - Prevents pattern_length mismatches
- **Early error detection** - Catches issues before execution
- **Clear error messages** - Tells you exactly how to fix problems

### Enhanced Architecture
- **Class-based design** - `LightControllerParser` class for reusability
- **70% smaller entry point** - `protocol_parser.py` now just 49 lines
- **Command preview** - Test protocols without hardware

📖 **[Refactoring Guide](docs/REFACTORING_GUIDE.md)** - Architecture details

---

## 🚀 Quick Start

### 1. Installation
```bash
# Clone repository
git clone https://github.com/Swida-Alba/light_controller_v2.git
cd light_controller_v2.2

# Install Python dependencies
pip install -r requirements.txt
```

📖 **[Full Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions

### 2. Upload Arduino Firmware

1. Open `light_controller_v2_arduino/light_controller_v2_arduino.ino` in Arduino IDE
2. Configure settings (if needed):
   ```cpp
   const int PATTERN_LENGTH = 2;     // 2, 4, 8, etc. (must match Python)
   #define PULSE_MODE_COMPILE 1      // 1=Enable pulses, 0=Disable (saves ~2.5KB)
   ```
3. Select your board: Tools → Board → Arduino Uno/Due/Mega
4. Select port: Tools → Port → (your Arduino port)
5. Click Upload

📖 **[Arduino Setup Guide](docs/ARDUINO_SETUP.md)** - Board-specific instructions  
📖 **[Firmware Update Guide](docs/FIRMWARE_UPDATE_INSTRUCTIONS.md)** - Updating existing firmware

### 3. Run Your First Protocol

**Option A: Try Automatic Calibration (Recommended)**
```bash
python protocol_parser.py 2 /dev/cu.usbmodem14301 examples/auto_calibration/simple_blink_example.txt
```

First time:
```
Identifying Arduino board...
Board ID: 0852420f343bb48d
No calibration found. Calibrate now? (Y/n): y
[Calibration proceeds for ~5 minutes]
✓ Calibration saved: 1.025847
```

Future runs:
```
✓ Found calibration: 1.025847
Age: 15 days (0.5 months) - Valid ✓
[Uses stored calibration automatically]
```

**Option B: Use Preset Calibration (Legacy)**
```bash
python protocol_parser.py 2 /dev/cu.usbmodem14301 examples/preset_calibration/simple_blink_example.txt
```

Shows warning about manual CALIBRATION_FACTOR, but still works!

📖 **[Usage Guide](docs/USAGE.md)** - Complete usage instructions  
📖 **[Examples Guide](examples/README.md)** - All example protocols explained

### 4. View Real-Time Monitoring (Automatic!)

After execution starts, an interactive HTML visualization automatically opens showing:
- 🔴 **Real-time status** updates every second
- 💡 **LED indicators** (ON/OFF/PULSING/WAITING/COMPLETED)
- 📊 **Timeline view** with current position marker
- ⏱️ **Time tracking** (upload time, total elapsed, protocol elapsed per channel)

📖 **[HTML Visualization Guide](docs/HTML_VISUALIZATION.md)** - Complete visualization features

### 5. Manage Calibrations

```bash
# View all calibrations with age and expiration status
python utils/manage_calibrations.py list

# Test board identification
python test_board_info.py

# Export calibrations
python utils/manage_calibrations.py export backup.txt

# Delete specific calibration
python utils/manage_calibrations.py delete <board_id>
```

📖 **[Database Management](docs/AUTO_CALIBRATION_DATABASE.md)** - Complete calibration system guide

---

## 🔑 Key Features

### Calibration & Timing
- ✅ **Automatic calibration** - 🆕 Board-specific with 90-day expiration
- ✅ **Multi-board support** - 🆕 Different calibrations per Arduino
- ✅ **Precise timing** - Compensates for crystal oscillator variations
- ✅ **Flexible timing** - Milliseconds to hours
- ✅ **Start time scheduling** - Time-of-day or countdown

### Pattern & Compression
- ✅ **Pattern compression** - Up to 97% reduction in command count
- ✅ **Automatic verification** - Arduino compatibility checking
- ✅ **Efficiency analysis** - Optimal pattern_length recommendations

### Control & Monitoring
- ✅ **Multi-channel control** - Up to 8 channels
- ✅ **Native pulsing support** - Hardware PWM for frequency and duty cycle modulation
- ✅ **Real-time visualization** - 🎨 Interactive HTML with live status tracking
- ✅ **Auto-generated timelines** - Visual protocol representation

### Protocols & Formats
- ✅ **Multiple formats** - Excel and Text protocols
- ✅ **Command preview** - Test without hardware
- ✅ **Flexible protocols** - 🆕 Automatic or preset calibration

📖 **[Features Overview](docs/FEATURES.md)** - Complete feature list with examples

---

## 📂 Examples

The `examples/` folder contains ready-to-use protocol files demonstrating both calibration approaches:

### 🆕 Auto-Calibration Examples (Recommended)

Located in `examples/auto_calibration/` - Uses automatic calibration system:

| File | Format | Description | Pattern Length |
|------|--------|-------------|----------------|
| `simple_blink_example.txt` | TXT | Basic ON/OFF patterns | 2 |
| `simple_blink_example.xlsx` | Excel | Same as TXT (no calibration sheet) | 2 |
| `pulse_protocol.txt` | TXT | Multi-channel pulsed patterns | 4 |
| `pulse_protocol.xlsx` | Excel | Same as TXT | 4 |
| `multi_channel_pattern.txt` | TXT | Complex 4-element patterns | 4 |
| `multi_channel_pattern.xlsx` | Excel | Same as TXT | 4 |

**Key Feature:** No `CALIBRATION_FACTOR` (TXT) or no `calibration` sheet (Excel) = automatic calibration enabled!

📖 **[Auto-Calibration Examples Guide](examples/auto_calibration/README.md)**

### 🔧 Preset Calibration Examples (Legacy)

Located in `examples/preset_calibration/` - Uses manual CALIBRATION_FACTOR:

| File | Format | Description | Pattern Length |
|------|--------|-------------|----------------|
| `basic_protocol.txt/.xlsx` | Both | Simple channel control | 4 |
| `simple_blink_example.txt/.xlsx` | Both | ON/OFF blink patterns | 2 |
| `pulse_protocol.txt/.xlsx` | Both | Various pulsing effects | 4 |
| `wait_pulse_protocol.txt/.xlsx` | Both | Wait status with pulse | 4 |
| `pattern_length_4_example.txt/.xlsx` | Both | Complex 4-element patterns | 4 |
| `test_8_channels_pattern_length_4.txt` | TXT | All 8 channels | 4 |

**Contains:** Manual `CALIBRATION_FACTOR: 1.000000` in each protocol

⚠️ **Important:** Calibration factors are **board-specific**! Each Arduino has unique crystal oscillator characteristics. Using the wrong calibration factor can cause significant timing drift.

📖 **[Preset Calibration Examples Guide](examples/preset_calibration/README.md)** - Includes board-specific calibration explanation

### 📁 Root Examples

Additional examples in `examples/` root:

- `clean_protocol.txt` - Minimal template without comments
- `complete_protocol.txt` - Fully documented with all features

📖 **[Complete Examples Guide](examples/README.md)** - All examples explained  
📖 **[Quick Reference](examples/QUICK_REFERENCE.md)** - Fast example lookup

---

## 📚 Documentation Index

> **📖 [Complete Documentation Index & Navigation Guide](docs/DOCUMENTATION_INDEX.md)**  
> Comprehensive guide to all 50+ documentation files organized by topic, user journey, and task.

### Quick Navigation by Task

**New Users:**  
[Installation](docs/INSTALLATION.md) → [Arduino Setup](docs/ARDUINO_SETUP.md) → [Usage Guide](docs/USAGE.md) → [Examples](examples/auto_calibration/README.md)

**Create Protocol:**  
[Protocol Formats](docs/PROTOCOL_FORMATS.md) → [Templates](docs/TEMPLATES.md) → [Examples](examples/README.md)

**Optimize Performance:**  
[Pattern Compression](docs/PATTERN_COMPRESSION_GUIDE.md) → [Verification](docs/PATTERN_LENGTH_VERIFICATION.md)

**Calibration:**  
[Auto-Calibration Guide](docs/AUTO_CALIBRATION_DATABASE.md) → [Backward Compatibility](docs/BACKWARD_COMPATIBILITY.md) → [Calibration Methods](docs/CALIBRATION_GUIDE.md)

**Troubleshoot:**  
[Troubleshooting](docs/TROUBLESHOOTING.md) → [Common Issues](docs/BUGFIX_START_TIME.md)

**Develop:**  
[Refactoring Guide](docs/REFACTORING_GUIDE.md) → [Folder Structure](docs/FOLDER_STRUCTURE.md)

<details>
<summary><b>📑 Expand Full Documentation Categories</b></summary>

### 🚀 Getting Started
- **[Installation Guide](docs/INSTALLATION.md)** - Complete setup
- **[Arduino Setup](docs/ARDUINO_SETUP.md)** - Hardware configuration
- **[Usage Guide](docs/USAGE.md)** - Basic and advanced usage
- **[Quick Start Examples](examples/README.md)** - Ready-to-use protocols

### ⏱️ Calibration System (NEW!)
- **[Automatic Calibration Database](docs/AUTO_CALIBRATION_DATABASE.md)** - Complete system guide
- **[Backward Compatibility](docs/BACKWARD_COMPATIBILITY.md)** - How old protocols work
- **[Calibration Guide](docs/CALIBRATION_GUIDE.md)** - Understanding timing calibration
- **[Calibration Methods](docs/CALIBRATION_INTEGRATION_SUMMARY.md)** - V1, V1.1, V2 comparison
- **[Calibration Quick Reference](docs/CALIBRATION_QUICK_REFERENCE.md)** - Quick lookup

### 📖 Core Documentation
- **[Features Overview](docs/FEATURES.md)** - Complete feature list
- **[Protocol Formats](docs/PROTOCOL_FORMATS.md)** - Excel & Text specifications
- **[Protocol Settings](docs/PROTOCOL_SETTINGS.md)** - Configuration parameters
- **[Templates](docs/TEMPLATES.md)** - Ready-to-use templates
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues

### 🎯 Pattern Compression
- **[Pattern Compression Guide](docs/PATTERN_COMPRESSION_GUIDE.md)** - How it works
- **[Pattern Length Verification](docs/PATTERN_LENGTH_VERIFICATION.md)** - Compatibility checking
- **[Pattern Length Implementation](docs/PATTERN_LENGTH_IMPLEMENTATION.md)** - Technical details

### 🎨 Visualization & Monitoring
- **[HTML Visualization](docs/HTML_VISUALIZATION.md)** - Real-time monitoring
- **[Visualization Guide](docs/VISUALIZATION_GUIDE.md)** - Complete features
- **[Command Preview](docs/PREVIEW_GUIDE.md)** - Test without hardware

### 💾 Memory & Pulse Mode
- **[Compile-Time Pulse Memory](docs/COMPILE_TIME_PULSE_MEMORY_FINAL.md)** - Pulse configuration
- **[Pulse Period vs Section Time](docs/PULSE_PERIOD_VS_SECTION_TIME.md)** - ⚠️ **IMPORTANT**
- **[Memory Reporting](docs/MEMORY_REPORTING_AND_COMPATIBILITY.md)** - Usage and compatibility

### 🏗️ Architecture & Development
- **[Refactoring Guide](docs/REFACTORING_GUIDE.md)** - Class-based architecture
- **[Folder Structure](docs/FOLDER_STRUCTURE.md)** - Project organization
- **[Build Instructions](docs/BUILD_INSTRUCTIONS.md)** - Creating executables
- **[Utility Scripts](utils/README.md)** - Development tools

</details>

---

## 📄 Protocol File Format

**Supported Formats:**
- **Text (.txt)** - Version control friendly, command syntax
- **Excel (.xlsx)** - Visual editing with spreadsheet interface

### Calibration Options

**Automatic Calibration (Recommended):**
```txt
# TXT: Simply omit CALIBRATION_FACTOR line
PATTERN:1;CH:1;STATUS:1,0;TIME_MS:1000,1000;REPEATS:10
START_TIME: {'CH1': 0}

# Excel: Omit 'calibration' sheet
# System automatically identifies Arduino and applies stored calibration
```

**Preset Calibration (Legacy):**
```txt
# TXT: Include CALIBRATION_FACTOR
PATTERN:1;CH:1;STATUS:1,0;TIME_MS:1000,1000;REPEATS:10
START_TIME: {'CH1': 0}
CALIBRATION_FACTOR: 1.025847  # Board-specific value!

# Excel: Include 'calibration' sheet with factor
```

⚠️ **Important:** Calibration factors are board-specific. Each Arduino has unique crystal oscillator characteristics due to manufacturing tolerances, temperature effects, and component aging. Never copy calibration factors between different boards!

### Text Format (.txt)

#### Required Parameters

**PATTERN commands** (at least one per channel):
```txt
PATTERN:<id>;CH:<channel>;STATUS:<states>;TIME_MS:<durations>;REPEATS:<count>;PULSE:<optional>
```

**START_TIME** (for all channels):
```txt
START_TIME: {'CH1': '21:00', 'CH2': 60, 'CH3': '2025-11-08 21:00:00'}
```

#### Optional Parameters

**WAIT_STATUS, WAIT_PULSE, CALIBRATION_FACTOR** (see docs for details)

📖 **[Complete Protocol Syntax](docs/PROTOCOL_FORMATS.md)**  
📖 **[Protocol Settings Guide](docs/PROTOCOL_SETTINGS.md)**  
📖 **[Templates](docs/TEMPLATES.md)**

---

## 📁 Project Structure

```
light_controller_v2.2/
├── protocol_parser.py           # Main execution script
├── preview_protocol.py          # Preview without Arduino
├── viz_protocol_html.py         # HTML visualization generator
├── light_controller_parser.py   # Core parser class
├── lcfunc.py                    # Utility functions
├── test_board_info.py           # 🆕 Arduino board identification test
├── calibration_database.json    # 🆕 Stored calibrations (auto-generated)
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── CHANGELOG.md                 # Version history
│
├── examples/                    # Example protocol files
│   ├── auto_calibration/        # 🆕 Automatic calibration examples
│   │   ├── README.md            # Auto-calibration guide
│   │   ├── simple_blink_example.txt/.xlsx
│   │   ├── pulse_protocol.txt/.xlsx
│   │   ├── multi_channel_pattern.txt/.xlsx
│   │   └── create_excel_examples.py  # Script to generate Excel examples
│   │
│   ├── preset_calibration/      # 🆕 Manual calibration examples (legacy)
│   │   ├── README.md            # Preset calibration guide
│   │   ├── simple_blink_example.txt/.xlsx
│   │   ├── pulse_protocol.txt/.xlsx
│   │   ├── basic_protocol.txt/.xlsx
│   │   ├── wait_pulse_protocol.txt/.xlsx
│   │   └── ... (more examples)
│   │
│   ├── README.md                # Complete examples guide
│   ├── QUICK_REFERENCE.md       # Quick lookup
│   ├── clean_protocol.txt       # Minimal template
│   └── complete_protocol.txt    # Fully documented example
│
├── docs/                        # Documentation (50+ guides)
│   ├── DOCUMENTATION_INDEX.md   # 📖 Complete navigation guide
│   ├── AUTO_CALIBRATION_DATABASE.md  # 🆕 Calibration system
│   ├── BACKWARD_COMPATIBILITY.md     # 🆕 Legacy protocol support
│   ├── PATTERN_COMPRESSION_GUIDE.md  # Optimization
│   ├── HTML_VISUALIZATION.md    # Real-time monitoring
│   └── ... (40+ more guides)
│
├── utils/                       # Utility & development tools
│   ├── manage_calibrations.py   # 🆕 Calibration database manager
│   ├── debug_calibration_speed_test.py
│   ├── verify_pattern_length_fix.py
│   └── README.md
│
└── light_controller_v2_arduino/ # Arduino firmware
    └── light_controller_v2_arduino.ino
```

**🆕 New in v2.2.1:**
- `calibration_database.json` - Auto-generated calibration storage
- `examples/auto_calibration/` - Automatic calibration examples
- `examples/preset_calibration/` - Legacy manual calibration examples
- `test_board_info.py` - Arduino identification testing
- `utils/manage_calibrations.py` - Database management utility
- `docs/AUTO_CALIBRATION_DATABASE.md` - Complete calibration guide
- `docs/BACKWARD_COMPATIBILITY.md` - Legacy protocol compatibility

---

## 🆘 Need Help?

### Quick Links by Topic

| Topic | Documentation |
|-------|---------------|
| **Setup** | [Installation](docs/INSTALLATION.md) → [Arduino Setup](docs/ARDUINO_SETUP.md) |
| **Calibration** | [Auto-Calibration](docs/AUTO_CALIBRATION_DATABASE.md) → [Backward Compatibility](docs/BACKWARD_COMPATIBILITY.md) |
| **Creating Protocols** | [Protocol Formats](docs/PROTOCOL_FORMATS.md) → [Templates](docs/TEMPLATES.md) → [Examples](examples/README.md) |
| **Optimization** | [Pattern Compression](docs/PATTERN_COMPRESSION_GUIDE.md) → [Verification](docs/PATTERN_LENGTH_VERIFICATION.md) |
| **Timing Issues** | [Calibration Guide](docs/CALIBRATION_GUIDE.md) → [Calibration Methods](docs/CALIBRATION_INTEGRATION_SUMMARY.md) |
| **Pulse Control** | [Pulse Period vs Section Time](docs/PULSE_PERIOD_VS_SECTION_TIME.md) → [Pulse Memory](docs/COMPILE_TIME_PULSE_MEMORY_FINAL.md) |
| **Visualization** | [HTML Visualization](docs/HTML_VISUALIZATION.md) → [Realtime Features](docs/REALTIME_VISUALIZATION.md) |
| **Development** | [Refactoring Guide](docs/REFACTORING_GUIDE.md) → [Folder Structure](docs/FOLDER_STRUCTURE.md) |
| **Troubleshooting** | [Troubleshooting Guide](docs/TROUBLESHOOTING.md) → [Common Bugs](docs/BUGFIX_START_TIME.md) |

### Support Resources

- 📖 **[Documentation Index](docs/DOCUMENTATION_INDEX.md)** - Complete navigation to all 50+ guides
- 📁 **[Documentation Folder](docs/)** - Browse all guides by category
- 🐛 **[GitHub Issues](https://github.com/Swida-Alba/light_controller_v2/issues)** - Report bugs or request features
- 💡 **[Examples](examples/)** - Ready-to-use protocol templates
- 🔧 **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

---

## 📊 Project Status

**Version**: 2.2.1  
**Status**: Production Ready ✅  
**Tested**: Python 3.6-3.13, Arduino Uno/Due/Mega  
**License**: [MIT](LICENSE)

### Version History

- **v2.2.1** (Nov 10, 2025) - Automatic calibration system with 3-month expiration, examples reorganization
- **v2.2.0** (Nov 8, 2025) - Pattern compression, auto-verification, real-time visualization
- **v2.1.0** (Nov 3, 2025) - Text protocol support, multiple time units
- **v2.0.0** - Initial release

📖 **[Complete Changelog](CHANGELOG.md)**

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Read the [Documentation Index](docs/DOCUMENTATION_INDEX.md)
2. Review [Folder Structure](docs/FOLDER_STRUCTURE.md)
3. Understand [Refactoring Guide](docs/REFACTORING_GUIDE.md)
4. Submit pull requests with clear descriptions

---

## 🙏 Acknowledgments

Built with:
- **Python** - Protocol parsing and serial communication
- **Arduino** - Hardware control
- **NumPy** - Data processing
- **Pandas** - Protocol parsing (Excel)
- **PySerial** - Serial communication
- **openpyxl** - Excel file handling

---

**Happy light controlling! 💡**

*Need calibration help? See [Automatic Calibration Guide](docs/AUTO_CALIBRATION_DATABASE.md)*  
*Want to understand why calibration factors are board-specific? See [Preset Calibration Examples](examples/preset_calibration/README.md)*
