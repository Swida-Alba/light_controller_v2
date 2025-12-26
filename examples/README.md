# Protocol Examples

This directory contains example protocols demonstrating various features of the Light Controller.

## 📂 Directory Structure

```
examples/
├── README.md                      # This file
├── QUICK_REFERENCE.md             # Protocol syntax cheat sheet
├── clean_protocol.txt             # Minimal example
├── complete_protocol.txt          # Full-featured example
├── calibration_method_example.py  # Calibration comparison script
│
├── auto_calibration/              # ✨ Recommended calibration (automatic)
├── preset_calibration/            # Legacy calibration (manual)
└── ramp_easing/                   # 🆕 RAMP & easing mode demos
```

---

## 📄 Root Directory Files

| File | Description |
|------|-------------|
| **[clean_protocol.txt](clean_protocol.txt)** | Minimal example - basic patterns only |
| **[complete_protocol.txt](complete_protocol.txt)** | Full example with all optional parameters documented |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Protocol syntax cheat sheet |

---

## 📁 Subfolders

### 🎨 [ramp_easing/](ramp_easing/README.md) - RAMP & Easing Modes

Examples demonstrating smooth LED transitions with various easing functions.

⚠️ **Note:** RAMP mode only works in TXT protocols (not Excel).

| File | Description |
|------|-------------|
| comprehensive_easing_modes.txt | All easing modes: L, I, O, IO, E, X, F |
| f_mode_demo.txt | Flicker mode examples |
| x_mode_demo.txt | Extended easing mode examples |
| pwm_ramp_protocol.txt | PWM intensity transitions |

---

### ✨ [auto_calibration/](auto_calibration/README.md) - Automatic Calibration (Recommended)

Examples using the **automatic calibration system** - no manual factors needed.

**When to use:**
- New protocols (recommended default)
- Multi-board workflows
- Simplified calibration management

**Features:**
- Automatic Arduino identification (serial number/VID/PID)
- Per-board calibration storage in database
- One-time calibration per Arduino

---

### 🔧 [preset_calibration/](preset_calibration/README.md) - Legacy Manual Calibration

Examples using the **old style** manual `CALIBRATION_FACTOR` in protocol files.

**When to use:**
- Shared protocols that must work on any Arduino
- Pre-calibrated hardware setups
- Backward compatibility requirements

---

## 🚀 Quick Start

### Run an Example

```bash
# TXT format
python protocol_parser.py 2 /dev/cu.usbmodem14301 examples/clean_protocol.txt

# Excel format (from auto_calibration/)
python protocol_parser.py 2 /dev/cu.usbmodem14301 examples/auto_calibration/simple_blink_example.xlsx
```

### First-Time Setup (Auto-Calibration)

```bash
# 1. Run any auto-calibration example
python protocol_parser.py 2 /dev/cu.usbmodem14301 examples/auto_calibration/simple_blink_example.txt

# 2. When prompted, calibrate (one-time per Arduino)
Arduino not calibrated. Calibrate now? (Y/n): y

# 3. Future runs are automatic!
```

### Visualize a Protocol

```bash
# Generate HTML visualization
python viz_protocol_html.py examples/ramp_easing/pwm_ramp_protocol.txt

# Preview without Arduino
python preview_protocol.py examples/complete_protocol.txt
```

---

## 📚 Additional Resources

- [PROTOCOL_SYNTAX_REFERENCE.md](../docs/PROTOCOL_SYNTAX_REFERENCE.md) - Complete syntax guide
- [CALIBRATION_GUIDE.md](../docs/CALIBRATION_GUIDE.md) - Calibration setup
- [FEATURES.md](../docs/FEATURES.md) - Feature documentation
- [TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md) - Common issues

---

**Compatible with:** Light Controller v2.3.0
