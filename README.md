# Light Controller V2.2

A flexible Arduino-based light control system with **PWM intensity control**, **smooth ramp transitions**, **easing functions**, **pattern compression**, **automatic calibration management**, precise timing control, and pulse frequency modulation.

**Version**: 2.3.0  
**Last Updated**: December 26, 2025  
**Status**: Production Ready ✅

---

## 📑 Table of Contents

- [What's New in v2.3.0](#-whats-new-in-v230) - PWM/RAMP enhancements and interactive visualization
- [What's New in v2.2](#-whats-new-in-v22) - Automatic calibration and pattern compression
- [Quick Start](#-quick-start) - Get running in 10 minutes
- [Key Features](#-key-features) - What it can do
- [Examples](#-examples) - Ready-to-use protocols (automatic vs preset calibration)
- [Documentation Index](#-documentation-index) - 50+ organized guides
- [Protocol File Format](#-protocol-file-format) - Syntax reference
- [Project Structure](#-project-structure) - File organization
- [Need Help?](#-need-help) - Support resources

---

## 🎯 What's New in v2.3.0

### Documentation & Examples (Dec 26, 2025)

- **Examples Reorganization**: Created dedicated `ramp_easing/` subfolder for RAMP/easing demos
- **Syntax Cleanup**: Fixed obsolete PULSE syntax (`PULSE:,` trailing commas) in example protocols
- **RAMP Format Updates**: Converted legacy RAMP format to v2.2.3+ parenthesized syntax
- **Documentation Archival**: Archived 29 outdated docs, reduced from 61 to 32 active files
- **Enhanced READMEs**: Comprehensive guides for each example subfolder

---

## Previous Releases

### v2.2.3 (Dec 26, 2025)

### 🌊 PWM & Ramp Enhancements
- **Unified Easing Formula** - Single cosine function `f(t) = (1 - cos(πt))/2` for all modes
- **Extended t Range** - Now supports t ∈ [0, 2] for complete breathing cycles
- **New Command Format** - Cleaner parenthesized syntax: `RAMP:(MODE:start,end,duration[|t_start,t_end])`
- **On-the-fly Interpolation** - Arduino performs smooth PWM transitions without pre-calculated steps
- **4 Easing Modes** with correct t ranges:
  - **Linear (L)**: Constant speed transitions
  - **Ease-In (I)**: Slow start, accelerating (ascending: t: 0→0.5, descending: t: 1→1.5)
  - **Ease-Out (O)**: Fast start, decelerating (ascending: t: 0.5→1, descending: t: 1.5→2)
  - **Cosine (C)**: Full S-curve (ascending: t: 0→1, descending: t: 1→2)
  - **Custom (X)**: Any t range for advanced control - `(X:duration|t_start,t_end)`
  - **Function (F)**: 🆕 Custom functions for complex effects - `(F:func_name,duration)`

📖 **[PWM & Ramp Control Guide](docs/PWM_RAMP_CONTROL.md)** - Complete easing documentation  
📖 **[F Mode Custom Functions](docs/F_MODE_CUSTOM_FUNCTIONS.md)** - Heartbeat, bounce, flicker & more 🆕

### 📊 Interactive Visualization
- **Jupyter Notebook** - Interactive Plotly charts with real easing curves
- **Protocol Examples** - Sunrise, breathing, circadian rhythm, multi-channel demos
- **HTML Visualizer** - Real-time intensity-time plots for all channels
- **Live Plotting** - See exactly what your protocol will do

📓 **[Easing Curves Notebook](docs/easing_curves_visualization.ipynb)** - Interactive visualization  
🌐 **[HTML Visualizer Guide](docs/HTML_VISUALIZATION.md)** - Protocol timeline visualization

### 🔌 Arduino Channel Monitor (NEW!)
- **Real-time PWM Tracking** - Array stores current values for all channels
- **Configurable Output** - Customizable print interval (default 100ms)
- **Serial Port Monitoring** - View live channel values via serial connection
- **Integration Ready** - Easy hooks for data logging and analysis

### 📈 Python Serial Monitor (NEW!)  
- **Live Data Stream** - Parse Arduino serial output in real-time
- **On-the-fly Plotting** - Visualize channel values as they execute
- **Connection Auto-detect** - Automatic COM port detection
- **Data Logging** - Optional CSV export of channel values

📊 **[Serial Monitor Guide](docs/SERIAL_MONITOR_GUIDE.md)** - Setup and usage instructions  
💻 **[serial_monitor.py](serial_monitor.py)** - Real-time visualization tool

### 🧪 Mock Arduino Simulator (NEW!)
- **Test Without Hardware** - Simulate protocols before uploading to Arduino
- **Protocol Validation** - Parse and verify protocol syntax
- **Visual Output** - Generate Plotly charts of simulated execution
- **CSV Export** - Save simulation data for analysis
- **Real-time Mode** - Watch simulated execution at adjustable speed

🤖 **[mock_arduino.py](mock_arduino.py)** - Protocol simulation tool

```bash
# Quick test:
python mock_arduino.py protocol.txt --plot --output data.csv
```

---

## 🎯 What's New in v2.2

### ✨ Automatic Calibration System
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

#### Prerequisites
- **Python 3.6+** (tested up to 3.13)
- **Arduino IDE** (for firmware upload)
- **Arduino Board**: 
  - ⭐ **Arduino Due** (recommended) - 96KB SRAM, full PWM/RAMP support
  - ⚠️ Arduino Mega - 8KB SRAM, limited PWM/RAMP
  - ❌ Arduino Uno - 2KB SRAM, **insufficient for PWM/RAMP mode**

> **⚠️ Memory Warning**: The firmware with PWM_RAMP_MODE enabled uses ~12KB SRAM. Arduino Uno (2KB) will not work with PWM/RAMP features. Use Arduino Due for full functionality.

#### Quick Install
```bash
# Clone repository
git clone https://github.com/Swida-Alba/light_controller_v2.git
cd light_controller_v2.2

# Install Python dependencies
pip install -r requirements.txt
```

#### Dependencies Installed
| Package | Purpose |
|---------|---------|
| `pyserial` | Arduino serial communication |
| `pandas` | Excel file parsing |
| `openpyxl` | Excel .xlsx support |
| `numpy` | Numerical calculations |
| `plotly` | Interactive visualizations (optional) |

#### Verify Installation
```bash
# Check Python packages
python -c "import serial, pandas, openpyxl, numpy; print('All dependencies OK!')"

# Test mock Arduino simulator (parses and validates protocol)
python mock_arduino.py examples/auto_calibration/simple_blink_example.txt --quiet
```

📖 **[Full Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions

### 2. Upload Arduino Firmware

1. Open `light_controller_v2_2_arduino/light_controller_v2_2_arduino.ino` in Arduino IDE
2. Configure settings (if needed):
   ```cpp
   const int PATTERN_LENGTH = 2;     // 2, 4, 8, etc. (must match Python)
   #define PULSE_MODE_COMPILE 1      // 1=Enable pulses, 0=Disable (saves ~2.5KB)
   #define PWM_RAMP_MODE_COMPILE 1   // 1=Enable smooth ramps, 0=Binary only
   ```
3. Select your board: 
   - **Arduino Due** (recommended): Tools → Board → Arduino SAM Boards → Arduino Due (Programming Port)
   - Arduino Mega: Tools → Board → Arduino AVR Boards → Arduino Mega
   - Arduino Uno (limited): Tools → Board → Arduino AVR Boards → Arduino Uno
4. Select port: Tools → Port → (your Arduino port)
5. Click Upload

📖 **[Arduino Setup Guide](docs/ARDUINO_SETUP.md)** - Board-specific instructions & memory requirements  
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

**PWM & Ramp (v2.3.0):**  
[PWM & Ramp Guide](docs/PWM_RAMP_CONTROL.md) → [Easing Curves Notebook](docs/easing_curves_visualization.ipynb) → [HTML Visualizer](docs/HTML_VISUALIZATION.md)

**Monitor Execution:**  
[Serial Monitor Guide](docs/SERIAL_MONITOR_GUIDE.md) → [Channel Monitoring](docs/SERIAL_MONITOR_GUIDE.md)

**Test & Simulate:**  
[Mock Arduino Guide](docs/MOCK_ARDUINO_GUIDE.md) → [Protocol Validation](docs/MOCK_ARDUINO_GUIDE.md#protocol-validation) → [F Mode Functions](docs/F_MODE_CUSTOM_FUNCTIONS.md)

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

### 💡 PWM & Ramp Control
- **[PWM & Ramp Control Guide](docs/PWM_RAMP_CONTROL.md)** - Complete easing and ramp documentation
- **[F Mode Custom Functions](docs/F_MODE_CUSTOM_FUNCTIONS.md)** - Heartbeat, bounce, flicker & more 🆕
- **[Easing Curves Interactive Notebook](docs/easing_curves_visualization.ipynb)** - Plotly visualizations with real examples
- **[HTML Protocol Visualizer](docs/HTML_VISUALIZATION.md)** - See your protocols with intensity plots
- **[Serial Monitor Guide](docs/SERIAL_MONITOR_GUIDE.md)** - Real-time channel value monitoring
- **[Mock Arduino Simulator](docs/MOCK_ARDUINO_GUIDE.md)** - Test protocols without hardware 🆕

### 🚀 Getting Started
- **[Installation Guide](docs/INSTALLATION.md)** - Complete setup
- **[Arduino Setup](docs/ARDUINO_SETUP.md)** - Hardware configuration
- **[Usage Guide](docs/USAGE.md)** - Basic and advanced usage
- **[Quick Start Examples](examples/README.md)** - Ready-to-use protocols

### ⏱️ Calibration System
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
└── light_controller_v2_2_arduino/ # Arduino firmware
    └── light_controller_v2_2_arduino.ino
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

**Version**: 2.2.3  
**Status**: Production Ready ✅  
**Tested**: Python 3.6-3.13, Arduino Uno/Due/Mega  
**License**: [MIT](LICENSE)

### Version History

- **v2.3.0** (Dec 26, 2025) - Documentation cleanup, examples reorganization, syntax updates
- **v2.2.3** (Dec 26, 2025) - PWM/RAMP enhancements, F mode custom functions, X mode format update, hybrid protocol validation, mock Arduino simulator
- **v2.2.2** (Dec 12, 2025) - Improved serial communication reliability for PULSE commands, fixed calibration skip issue
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
