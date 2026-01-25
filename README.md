# Light Controller V2.3

A flexible Arduino-based light control system with PWM intensity control, smooth ramp transitions, easing functions, pattern looping, and DAC output support.

**Version**: 2.3.2  
**Status**: Production Ready ✅

---

## ⚡ Quick Start

### 1. Install

```bash
git clone https://github.com/Swida-Alba/light_controller_v2.git
cd light_controller_v2.3
pip install -r requirements.txt
```

### 2. Upload Arduino Firmware

Open `light_controller_v2_3_arduino/light_controller_v2_3_arduino.ino` in Arduino IDE → Select board (Due recommended) → Upload

### 3. Run a Protocol

```bash
python protocol_parser.py 2 /dev/cu.usbmodem14301 examples/auto_calibration/simple_blink_example.txt
```

📖 **[Detailed Installation Guide](docs/INSTALLATION.md)** | **[Arduino Setup](docs/ARDUINO_SETUP.md)**

---

## 🎯 Key Features

| Feature                    | Description                                                             |
| -------------------------- | ----------------------------------------------------------------------- |
| **Multi-Channel Control**  | Up to 8 independent channels with individual timing                     |
| **PWM & Ramp Transitions** | Smooth intensity fades with easing curves (linear, ease-in/out, cosine) |
| **Pattern Looping**        | Channels can loop indefinitely while others run once                    |
| **Automatic Calibration**  | Per-board timing calibration with 90-day expiration                     |
| **Pattern Compression**    | Up to 97% reduction in transmitted commands                             |
| **DAC Output**             | MCP4728 I2C DAC and native Arduino DAC support                          |
| **Real-Time Monitoring**   | Live HTML visualization and serial plotting                             |

---

## 📄 Protocol Example

```txt
# Simple breathing light that loops forever
PATTERN:1;CH:1;RAMP:(C:0,255,3000);REPEATS:1      # Fade in over 3 seconds
PATTERN:2;CH:1;RAMP:(C:255,0,3000);REPEATS:1      # Fade out over 3 seconds

START_TIME: {'CH1': 0}

LOOP: {
    'CH1': 1
}
```

📖 **[Protocol Syntax Reference](docs/PROTOCOL_SYNTAX_REFERENCE.md)** | **[Protocol Examples](examples/README.md)**

---

## 🔄 LOOP Feature

Channels with LOOP enabled will continuously repeat their patterns.

```txt
LOOP: {
    'CH1': 1,   # Loop forever
    'CH2': 0    # Run once
}
```

**Important:** When looping, the **wait/countdown pattern is skipped** on restart. The wait only executes once at the beginning.

| Execution    | Pattern Flow                                |
| ------------ | ------------------------------------------- |
| First run    | Wait → Pattern 1 → Pattern 2 → ... → End    |
| Loop restart | Pattern 1 → Pattern 2 → ... → End (no wait) |

📖 **[LOOP Documentation](docs/PROTOCOL_SYNTAX_REFERENCE.md#loop-block)**

---

## 🌊 PWM & Ramp Transitions

Create smooth intensity transitions with easing modes:

| Mode         | Syntax                             | Description              |
| ------------ | ---------------------------------- | ------------------------ |
| **Linear**   | `RAMP:(L:start,end,duration)`      | Constant speed           |
| **Ease-In**  | `RAMP:(I:start,end,duration)`      | Slow start, accelerate   |
| **Ease-Out** | `RAMP:(O:start,end,duration)`      | Fast start, decelerate   |
| **Cosine**   | `RAMP:(C:start,end,duration)`      | Full S-curve             |
| **Custom**   | `RAMP:(X:duration\|t_start,t_end)` | Any easing range         |
| **Function** | `RAMP:(F:func_name,duration)`      | Heartbeat, flicker, etc. |

📖 **[PWM & Ramp Guide](docs/PWM_RAMP_CONTROL.md)** | **[F Mode Custom Functions](docs/F_MODE_CUSTOM_FUNCTIONS.md)**

📓 **[Interactive Easing Curves Notebook](docs/easing_curves_visualization.ipynb)** - Visualize all easing modes with Plotly

---

## 📊 Monitoring & Visualization

### Real-Time HTML Visualization
Automatically opens when protocol runs - shows live status, timeline, and LED indicators.

```bash
python protocol_parser.py 2 /dev/cu.usbmodem14301 protocol.txt
# HTML visualization auto-opens in browser
```

### Serial Monitor with Plotting
```bash
python protocol_parser.py 2 /dev/cu.usbmodem14301 protocol.txt --monitor
# Opens matplotlib real-time plot + exports to Plotly HTML
```

### Mock Arduino (Test Without Hardware)
```bash
python mock_arduino.py examples/auto_calibration/simple_blink_example.txt --plot
```

📖 **[HTML Visualization Guide](docs/HTML_VISUALIZATION.md)** | **[Serial Monitor Guide](docs/SERIAL_MONITOR_GUIDE.md)** | **[Mock Arduino Guide](docs/MOCK_ARDUINO_GUIDE.md)**

---

## 📚 Documentation

### By Topic

| Topic                  | Guide                                                                                                                                         |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **Getting Started**    | [Installation](docs/INSTALLATION.md) → [Arduino Setup](docs/ARDUINO_SETUP.md) → [Usage](docs/USAGE.md)                                        |
| **Creating Protocols** | [Protocol Formats](docs/PROTOCOL_FORMATS.md) → [Syntax Reference](docs/PROTOCOL_SYNTAX_REFERENCE.md) → [Templates](docs/TEMPLATES.md)         |
| **PWM & Ramp**         | [PWM Guide](docs/PWM_RAMP_CONTROL.md) → [Easing Notebook](docs/easing_curves_visualization.ipynb) → [F Mode](docs/F_MODE_CUSTOM_FUNCTIONS.md) |
| **Calibration**        | [Auto-Calibration](docs/AUTO_CALIBRATION_DATABASE.md) → [Calibration Guide](docs/CALIBRATION_GUIDE.md)                                        |
| **Optimization**       | [Pattern Compression](docs/PATTERN_COMPRESSION_GUIDE.md)                                                                                      |
| **Troubleshooting**    | [Troubleshooting Guide](docs/TROUBLESHOOTING.md)                                                                                              |

### Full Index

📖 **[Complete Documentation Index](docs/DOCUMENTATION_INDEX.md)** - All 30+ guides organized by topic

---

## 📁 Project Structure

```
light_controller_v2.3/
├── protocol_parser.py              # Main execution script
├── light_controller_parser.py      # Core parser class
├── viz_protocol_html.py            # HTML visualization
├── realtime_plot.py                # Serial monitor plotting
├── mock_arduino.py                 # Protocol simulator
├── calibration_database.json       # Stored calibrations
│
├── examples/                       # Protocol examples
│   ├── auto_calibration/           # Automatic calibration (recommended)
│   ├── preset_calibration/         # Manual calibration (legacy)
│   └── ramp_easing/                # PWM/RAMP demonstrations
│
├── docs/                           # Documentation (30+ guides)
│   ├── easing_curves_visualization.ipynb  # Interactive notebook
│   └── ...
│
└── light_controller_v2_3_arduino/  # Arduino firmware
    └── light_controller_v2_3_arduino.ino
```

📖 **[Folder Structure](docs/FOLDER_STRUCTURE.md)**

---

## 🔧 Hardware Requirements

| Board              | SRAM  | Voltage | DAC         | PWM/RAMP Support | Recommendation             |
| ------------------ | ----- | ------- | ----------- | ---------------- | -------------------------- |
| **Arduino UNO R4** | 32 KB | **5V**  | ✅ 12-bit    | ✅ Full           | ⭐ **Recommended**          |
| Arduino Due        | 96 KB | 3.3V    | ✅ 12-bit x2 | ✅ Full           | Good for complex protocols |
| Arduino Mega 2560  | 8 KB  | 5V      | ❌ None      | ⚠️ Limited        | OK for simple protocols    |
| Arduino UNO R3     | 2 KB  | 5V      | ❌ None      | ❌ Insufficient   | Not recommended            |

### Board Selection Guide

- **UNO R4 MINIMA/WIFI** (⭐ Recommended): 32KB SRAM is sufficient for most protocols. **5V output** is ideal for driving LEDs and most components. Built-in 12-bit DAC for analog output.
- **Arduino Due**: 96KB SRAM for very complex protocols. ⚠️ **3.3V only** - may require level shifters for 5V components. Dual 12-bit DAC channels.

- **Arduino Mega 2560**: 8KB SRAM limits PWM/RAMP features to simple patterns. Good if you need many I/O pins. No native DAC.

- **Arduino UNO R3**: ❌ Not recommended - 2KB SRAM is insufficient for PWM/RAMP mode.

**Need more memory?** For protocols exceeding 32KB, use Arduino Due (96KB) or GIGA R1 WiFi (1MB).

**Optional:** MCP4728 I2C DAC module adds 4 additional 12-bit analog outputs (5V compatible)

📖 **[Arduino Setup & Memory](docs/ARDUINO_SETUP.md)**

---

## 📝 Recent Changes

- **v2.3.2** (Jan 24, 2026) - LOOP support with wait pattern skipping
- **v2.3.1** (Jan 24, 2026) - MCP4728 DAC support, native DAC support
- **v2.3.0** (Dec 26, 2025) - Real-time monitoring improvements, examples reorganization

📖 **[Full Changelog](CHANGELOG.md)**

---

## 📄 License

[MIT License](LICENSE)

---

**Happy light controlling! 💡**

---

<details>
<summary><b>📜 Previous Release Notes</b></summary>

## What's New in v2.3.1

### DAC Output Support (Jan 24, 2026)

- **MCP4728 I2C DAC**: True 12-bit analog output via 4-channel I2C DAC module
  - Virtual pins 201-204 map to MCP4728 channels A-D
  - Automatic scaling from 0-255 to 0-4095
  - See [Arduino Setup Guide](docs/ARDUINO_SETUP.md#mcp4728-i2c-dac-setup-optional) for wiring
  
- **Native DAC Support**: Built-in DAC on Arduino Due, Zero, and Uno R4
  - Virtual pins 100-101 for native DAC channels
  - Arduino Due: DAC0 and DAC1 (3.3V output)

---

## What's New in v2.3.0

### Real-Time Monitoring Improvements (Dec 26, 2025)

- **Matplotlib-Based Plotting**: Replaced PyQtGraph with matplotlib for better cross-platform portability
- **5-Minute Scrolling Window**: Real-time display shows moving 5-min window for protocols of any length
- **Extended Data Storage**: Stores up to 1 hour of data (36,000 points) for complete export
- **Plotly HTML Export**: Automatically saves interactive HTML chart with range slider when monitoring stops

---

## What's New in v2.2.3

### 🌊 PWM & Ramp Enhancements
- **Unified Easing Formula** - Single cosine function `f(t) = (1 - cos(πt))/2` for all modes
- **Extended t Range** - Now supports t ∈ [0, 2] for complete breathing cycles
- **New Command Format** - Cleaner parenthesized syntax: `RAMP:(MODE:start,end,duration[|t_start,t_end])`
- **On-the-fly Interpolation** - Arduino performs smooth PWM transitions without pre-calculated steps
- **Easing Modes**: Linear (L), Ease-In (I), Ease-Out (O), Cosine (C), Custom (X), Function (F)

### 📊 Interactive Visualization
- **Jupyter Notebook** - Interactive Plotly charts with real easing curves
- **HTML Visualizer** - Real-time intensity-time plots for all channels
- **Mock Arduino Simulator** - Test protocols without hardware

---

## What's New in v2.2

### ✨ Automatic Calibration System
- **🤖 Board identification** - Unique ID per Arduino (serial number/VID:PID)
- **💾 Database storage** - Calibrations saved to `calibration_database.json`
- **♻️ Auto-retrieval** - Stored calibrations automatically loaded
- **⏰ 3-month expiration** - Auto-recalibration every 90 days for accuracy

### Pattern-Based Compression System
- **Automatic pattern detection** - Reduces hundreds of commands to just a few
- **Compression ratios up to 37:1** - 97%+ reduction in transmitted data

</details>

