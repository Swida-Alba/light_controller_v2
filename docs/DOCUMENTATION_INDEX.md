# Documentation Index & Navigation Guide

**Light Controller V2.2** - Complete Documentation Map  
**Last Updated**: November 10, 2025

---

## 🗺️ How to Use This Guide

This index organizes all documentation by **user journey** and **topic**. Find what you need quickly:

- **New Users**: Start with 🚀 Getting Started
- **Creating Protocols**: See 📖 Core Documentation
- **Optimization**: See 🎯 Pattern Compression
- **Troubleshooting**: See 🐛 Bug Fixes & 🛠️ Troubleshooting
- **Developers**: See 🏗️ Architecture & Development

### 📊 Visual Navigation

**[→ See Documentation Flowchart](DOCUMENTATION_FLOWCHART.md)** for visual user journeys, decision trees, and learning paths!

### 📁 Project Organization

**[→ Project Organization Summary](PROJECT_ORGANIZATION.md)** - Complete overview of file structure, documentation system, and navigation methods (60+ docs organized)

---

## 🚀 Getting Started (New Users Start Here!)

### Essential First Steps

1. **[Installation Guide](INSTALLATION.md)** ⭐⭐⭐
   - Python environment setup
   - Arduino IDE installation
   - Dependency installation
   - Platform-specific instructions (Windows/Mac/Linux)

2. **[Arduino Setup](ARDUINO_SETUP.md)** ⭐⭐⭐
   - Hardware connection diagrams
   - Board selection (Uno/Due/Mega)
   - Upload instructions
   - PATTERN_LENGTH configuration
   - Serial port troubleshooting

3. **[Usage Guide](USAGE.md)** ⭐⭐⭐
   - Basic workflow
   - Command-line usage
   - Protocol execution
   - Output file interpretation

4. **[Quick Start Examples](../examples/README.md)** ⭐⭐⭐
   - Ready-to-use example files
   - Step-by-step walkthroughs
   - Expected results

### First Protocol Tutorial

**Path**: New User → First Success
```
1. Read: INSTALLATION.md (10 min)
2. Setup: Arduino hardware (15 min)
3. Try: examples/simple_blink_example.txt (5 min)
4. Read: PROTOCOL_FORMATS.md (15 min)
5. Create: Your first custom protocol (30 min)
```

---

## 📖 Core Documentation (Protocol Creation)

### Protocol Reference

| Document | Use When | Time to Read |
|----------|----------|--------------|
| **[Protocol Formats](PROTOCOL_FORMATS.md)** | Creating any protocol | 20 min |
| **[Protocol Settings](PROTOCOL_SETTINGS.md)** | Configuring timing & calibration | 15 min |
| **[Templates](TEMPLATES.md)** | Need a starting template | 5 min |
| **[Features Overview](FEATURES.md)** | Understanding all capabilities | 25 min |

### Protocol Format Deep Dive

**[Protocol Formats](PROTOCOL_FORMATS.md)** covers:
- Excel (.xlsx) format specification
- Text (.txt) command syntax
- PATTERN command structure
- START_TIME formats (time, datetime, countdown)
- Optional parameters (WAIT_STATUS, WAIT_PULSE, CALIBRATION_FACTOR)
- Time units (seconds, minutes, hours, milliseconds)
- Pulse parameters (frequency, period, pulse width, duty cycle)

**[Protocol Settings](PROTOCOL_SETTINGS.md)** covers:
- START_TIME detailed configuration
- CALIBRATION_FACTOR usage
- WAIT_STATUS (LED state during countdown)
- WAIT_PULSE (pulsing during wait)
- Parameter validation rules

### Template Selection Guide

**[Templates](TEMPLATES.md)** provides:
- Excel templates (basic, pulse, multi-channel)
- Text templates (minimal, complete, commented)
- Template selection flowchart
- Customization guidelines

---

## 🎯 Pattern Compression System (Optimization)

### Understanding Pattern Compression

**Learning Path**: Beginner → Expert
```
1. Read: PATTERN_COMPRESSION_GUIDE.md (30 min) - Core concepts
2. Read: PATTERN_LENGTH_VERIFICATION.md (10 min) - Safety features
3. Try: examples/pattern_length_4_example.txt (15 min)
4. Read: PATTERN_LENGTH_IMPLEMENTATION.md (20 min) - Advanced
```

| Document | Focus | Audience |
|----------|-------|----------|
| **[Pattern Compression Guide](PATTERN_COMPRESSION_GUIDE.md)** | How compression works, 97% reduction examples | All users |
| **[Pattern Length Verification](PATTERN_LENGTH_VERIFICATION.md)** | Automatic compatibility checking | All users |
| **[Arduino Pattern Length Fix](ARDUINO_PATTERN_LENGTH_FIX.md)** | Firmware safety mechanisms | Arduino devs |
| **[Pattern Length Implementation](PATTERN_LENGTH_IMPLEMENTATION.md)** | Technical implementation | Python devs |

### Pattern Compression Decision Tree

**Q: What pattern_length should I use?**

```
Simple ON/OFF alternating patterns?
  └→ YES: Use pattern_length=2 (default)
       Examples: Blinking, simple alternation
       Best compression ratio

Multi-phase sequences (3-4 steps)?
  └→ YES: Use pattern_length=4
       Examples: Traffic lights, breathing effects
       Better for complex patterns

Very complex patterns (5+ states)?
  └→ YES: Use pattern_length=8 or higher
       Examples: Complex animations
       May require Arduino firmware modification
```

### Arduino Configuration

**Before running complex protocols:**

1. Check your protocol's pattern complexity
2. Update Arduino `PATTERN_LENGTH` constant
3. Re-upload firmware
4. System will auto-verify compatibility

**See**: [Arduino Pattern Length Fix](ARDUINO_PATTERN_LENGTH_FIX.md)

---

## ⏱️ Timing & Calibration

### Calibration Overview

| Document | Coverage | When to Read |
|----------|----------|--------------|
| **[Calibration Guide](CALIBRATION_GUIDE.md)** | Basic calibration concepts | First time setup |
| **[Calibration Integration](CALIBRATION_INTEGRATION_SUMMARY.md)** | V1, V1.1, V2 methods detailed | Calibration issues |
| **[Calibration Quick Reference](CALIBRATION_QUICK_REFERENCE.md)** | Quick method comparison | Quick lookup |
| **[Calibration Method Usage](CALIBRATION_METHOD_USAGE.md)** | Method usage guidelines | Implementation |
| **[Calibration Review](CALIBRATION_REVIEW.md)** | Method comparison & review | Understanding differences |
| **[Calibration Logic Analysis](calibration_logic_analysis.md)** | Technical analysis | Deep dive |
| **[Correct Calibration Analysis](correct_calibration_analysis.md)** | Validation analysis | Troubleshooting |

### Calibration Method Selection

**Three methods available:**

1. **V2 (Recommended)** - Most accurate
   - Duration: 180 seconds
   - Samples: 9 measurements
   - Accuracy: ~1.001013
   - Best for: Production use

2. **V1.1 (New)** - Active wait
   - Duration: 150 seconds
   - Samples: 4 measurements
   - Accuracy: ~1.001200
   - Best for: Better responsiveness than V1

3. **V1 (Original)** - Backward compatible
   - Duration: 150 seconds
   - Samples: 4 measurements
   - Accuracy: ~1.001200
   - Best for: Legacy systems

**See**: [Calibration Quick Reference](CALIBRATION_QUICK_REFERENCE.md)

### Pulse Timing (IMPORTANT!)

**[Pulse Period vs Section Time](PULSE_PERIOD_VS_SECTION_TIME.md)** ⚠️

**Critical concepts:**
- Pulse period ≠ Section duration
- Period: Single pulse cycle time
- Section: How long pulsing continues
- Example: 1000ms period, 10000ms section = 10 pulses

**Common mistake**: Using period as section duration
**Result**: Only 1 pulse instead of multiple

---

## 🎨 Visualization & Monitoring

### Visualization Learning Path

```
1. Quick Start: VISUALIZATION_QUICKSTART.md (5 min)
2. Full Guide: HTML_VISUALIZATION.md (15 min)
3. Real-time: REALTIME_VISUALIZATION.md (10 min)
4. Advanced: VISUALIZATION_GUIDE.md (20 min)
```

| Document | Focus | Features Covered |
|----------|-------|------------------|
| **[HTML Visualization](HTML_VISUALIZATION.md)** | Main visualization guide | Live status, timelines, auto-open |
| **[Visualization Quick Start](VISUALIZATION_QUICKSTART.md)** | Get started fast | Essential features |
| **[Visualization Guide](VISUALIZATION_GUIDE.md)** | Complete features | All visualization capabilities |
| **[Realtime Visualization](REALTIME_VISUALIZATION.md)** | Real-time updates | Live monitoring details |
| **[Command Preview](PREVIEW_GUIDE.md)** | Testing without hardware | Preview mode |

### Visualization Features

**Auto-generated visualizations include:**
- 🔴 Real-time status indicators
- 📊 Interactive timeline view
- ⏱️ Dual time tracking (Total & Protocol elapsed)
- 🎯 Current position marker
- 💡 LED status animations (ON/OFF/PULSING/WAITING)
- 🎵 Pulse parameter display
- 🔄 Auto-refresh every second
- 📱 Responsive design

### Quick Commands

```bash
# Preview without Arduino
python preview_protocol.py examples/simple_blink_example.txt

# Execute and auto-open visualization
python protocol_parser.py
```

**Output files** (same location as protocol):
- `protocol_commands_TIMESTAMP.txt` - Command list
- `protocol_commands_TIMESTAMP.html` - Interactive visualization

**See**: [Output at Protocol Path](OUTPUT_AT_PROTOCOL_PATH.md)

---

## 💾 Memory & Pulse Mode

### Memory Management

| Document | Topic | When to Read |
|----------|-------|--------------|
| **[Compile-Time Pulse Memory](COMPILE_TIME_PULSE_MEMORY_FINAL.md)** | Pulse mode setup | Before using pulses |
| **[Memory Reporting](MEMORY_REPORTING_AND_COMPATIBILITY.md)** | Memory monitoring | Low memory warnings |
| **[Pulse Mode Compatibility](PULSE_MODE_COMPATIBILITY_MATRIX.md)** | Compatibility matrix | Planning protocols |

### Pulse Mode Configuration

**Compile-time setting** in Arduino firmware:
```cpp
#define PULSE_MODE_COMPILE 1  // 1=Enable, 0=Disable
```

**Memory savings**: ~2.5KB SRAM when disabled

**Decision guide:**
- Need pulses? → Set to 1
- Only ON/OFF? → Set to 0 (saves memory)

### Pulse Troubleshooting

| Document | Helps With |
|----------|------------|
| **[Pulse Mode Testing](PULSE_MODE_TESTING_GUIDE.md)** | Testing pulse configurations |
| **[Pulse Mode Warnings](PULSE_MODE_WARNING_EXAMPLES.md)** | Understanding warnings |
| **[Single Cycle Pulse Details](SINGLE_CYCLE_PULSE_DETAILS.md)** | Advanced pulse behavior |

---

## 🏗️ Architecture & Development

### For Developers

**Architecture overview:**

| Document | Audience | Content |
|----------|----------|---------|
| **[Refactoring Guide](REFACTORING_GUIDE.md)** | Python developers | Class-based architecture |
| **[Refactoring Summary](REFACTORING_SUMMARY.md)** | Migration guide | v2.1 → v2.2 changes |
| **[Folder Structure](FOLDER_STRUCTURE.md)** | Contributors | Project organization |
| **[Build Instructions](BUILD_INSTRUCTIONS.md)** | Distributors | Creating executables |
| **[Firmware Update Instructions](FIRMWARE_UPDATE_INSTRUCTIONS.md)** | Arduino devs | Updating firmware |
| **[Pattern Length Fix](PATTERN_LENGTH_FIX.md)** | Developers | Pattern fix details |

### Utility Tools

Development and debugging tools are in the `utils/` folder:

| Tool | Purpose |
|------|---------|
| **debug_calibration_speed_test.py** | Test all three calibration methods |
| **verify_pattern_length_fix.py** | Verify pattern compatibility |
| **calculate_pulse_memory.py** | Estimate SRAM usage |
| **analyze_results.py** | Analyze calibration results |
| **simple_build.py** | Simplified build script |

See [utils/README.md](../utils/README.md) for details.

### Architecture Changes (v2.2)

**New structure:**
- `protocol_parser.py` - Entry point (49 lines, 70% reduction)
- `light_controller_parser.py` - Core class module
- `lcfunc.py` - Utility functions

**Benefits:**
- Reusable code
- Better testability
- Cleaner separation

**See**: [Refactoring Guide](REFACTORING_GUIDE.md)

### Contributing

**Before contributing:**
1. Read: [Folder Structure](FOLDER_STRUCTURE.md)
2. Understand: [Refactoring Guide](REFACTORING_GUIDE.md)
3. Test: Run existing test scripts
4. Document: Update relevant docs

---

## 📈 Recent Updates & Improvements

### What's New?

**Latest updates organized by date:**

| Date | Document | Updates |
|------|----------|---------|
| Nov 8, 2025 | **[Improvements November 8](IMPROVEMENTS_NOVEMBER_8.md)** | Feature summary |
| Nov 8, 2025 | **[Output at Protocol Path](OUTPUT_AT_PROTOCOL_PATH.md)** | File organization |
| Recent | **[Enhanced Realtime Features](ENHANCED_REALTIME_FEATURES.md)** | Real-time viz |
| Recent | **[Auto Visualization](AUTO_VISUALIZATION_SUMMARY.md)** | Auto-open feature |
| Recent | **[HTML Viz Updates](HTML_VISUALIZATION_UPDATES.md)** | Viz improvements |
| Recent | **[JavaScript Updates](JAVASCRIPT_UPDATE_SUMMARY.md)** | JS optimizations |

### Feature Timeline

**v2.2.0 (Nov 8, 2025):**
- Pattern compression (up to 97% reduction)
- Auto-verification system
- Class-based architecture
- Command preview mode
- Real-time HTML visualization

**v2.1.0 (Nov 3, 2025):**
- Text protocol support
- Multiple time units
- Flexible start times

---

## 🐛 Bug Fixes & Troubleshooting

### Common Issues

**Start here**: [Troubleshooting Guide](TROUBLESHOOTING.md)

### Specific Bug Fixes

| Issue | Document | Fix Description |
|-------|----------|-----------------|
| Countdown display | **[Bugfix: Countdown Display](BUGFIX_COUNTDOWN_DISPLAY.md)** | Timer display corrections |
| Start time parsing | **[Bugfix: Start Time](BUGFIX_START_TIME.md)** | Time format handling |
| Arduino safety | **[Arduino Safety Summary](ARDUINO_SAFETY_SUMMARY.md)** | Memory safety improvements |
| File paths | **[Protocol Path Complete](IMPLEMENTATION_COMPLETE_PROTOCOL_PATH.md)** | Path handling |

### Troubleshooting by Category

**Connection issues:**
- Read: [Arduino Setup](ARDUINO_SETUP.md) - Serial port section
- Check: Cable, drivers, port selection

**Timing issues:**
- Read: [Calibration Guide](CALIBRATION_GUIDE.md)
- Try: Different calibration method
- Check: [Pulse Period vs Section Time](PULSE_PERIOD_VS_SECTION_TIME.md)

**Memory issues:**
- Read: [Memory Reporting](MEMORY_REPORTING_AND_COMPATIBILITY.md)
- Solution: Disable pulse mode if not needed
- Check: Protocol complexity

**Pattern issues:**
- Read: [Pattern Length Verification](PATTERN_LENGTH_VERIFICATION.md)
- Check: Arduino PATTERN_LENGTH setting
- Verify: Compatibility matrix

---

## 📊 Implementation & Technical Details

### Summary Documents

| Document | Purpose | Audience |
|----------|---------|----------|
| **[Success Summary](SUCCESS_SUMMARY.md)** | Project status | All users |
| **[Visualization Implementation](VISUALIZATION_IMPLEMENTATION.md)** | Viz technical details | Developers |
| **[Visualization Quick Card](VISUALIZATION_QUICK_CARD.md)** | Viz quick reference | All users |

### Protocol Path Implementation

| Document | Topic |
|----------|-------|
| **[Implementation Complete](IMPLEMENTATION_COMPLETE_PROTOCOL_PATH.md)** | Full implementation |
| **[Quick Reference](QUICK_REFERENCE_PROTOCOL_PATH.md)** | Quick lookup |
| **[Update Output Path](UPDATE_OUTPUT_AT_PROTOCOL_PATH.md)** | Update details |

---

## 📋 Examples & Templates

### Example Files

**See**: [Examples README](../examples/README.md)

**Categories:**
- Simple patterns (pattern_length=2)
- Complex patterns (pattern_length=4)
- Pulse examples
- Multi-channel examples
- Wait period examples

**Quick reference**: [Examples Quick Reference](../examples/QUICK_REFERENCE.md)

### Template Selection

**By protocol type:**
- Basic ON/OFF: `examples/simple_blink_example.txt`
- Pulses: `examples/pulse_protocol.txt`
- Complex: `examples/pattern_length_4_example.txt`
- Multi-channel: `examples/basic_protocol.txt`

---

## 🔍 Quick Lookup Tables

### By User Type

| User Type | Essential Reading | Priority Order |
|-----------|-------------------|----------------|
| **First-time user** | INSTALLATION.md, ARDUINO_SETUP.md, USAGE.md, examples/README.md | 1,2,3,4 |
| **Protocol creator** | PROTOCOL_FORMATS.md, PROTOCOL_SETTINGS.md, TEMPLATES.md | 1,2,3 |
| **Optimizer** | PATTERN_COMPRESSION_GUIDE.md, PATTERN_LENGTH_VERIFICATION.md | 1,2 |
| **Troubleshooter** | TROUBLESHOOTING.md, CALIBRATION_GUIDE.md | 1,2 |
| **Developer** | REFACTORING_GUIDE.md, FOLDER_STRUCTURE.md, PATTERN_LENGTH_IMPLEMENTATION.md | 1,2,3 |

### By Task

| Task | Documents Needed |
|------|------------------|
| **First setup** | INSTALLATION.md → ARDUINO_SETUP.md → examples/README.md |
| **Create Excel protocol** | PROTOCOL_FORMATS.md → TEMPLATES.md |
| **Create Text protocol** | PROTOCOL_FORMATS.md → examples/simple_blink_example.txt |
| **Use pulses** | PULSE_PERIOD_VS_SECTION_TIME.md → COMPILE_TIME_PULSE_MEMORY_FINAL.md |
| **Optimize protocol** | PATTERN_COMPRESSION_GUIDE.md → PATTERN_LENGTH_VERIFICATION.md |
| **Fix timing** | CALIBRATION_GUIDE.md → CALIBRATION_QUICK_REFERENCE.md |
| **Debug issues** | TROUBLESHOOTING.md → (specific bugfix docs) |
| **Visualize protocol** | HTML_VISUALIZATION.md → VISUALIZATION_QUICKSTART.md |

### By Reading Time

| Time Available | Document | Type |
|----------------|----------|------|
| **5 minutes** | VISUALIZATION_QUICKSTART.md, TEMPLATES.md, examples/QUICK_REFERENCE.md | Quick ref |
| **10 minutes** | CALIBRATION_QUICK_REFERENCE.md, PATTERN_LENGTH_VERIFICATION.md | Focused guide |
| **15 minutes** | PROTOCOL_SETTINGS.md, HTML_VISUALIZATION.md, ARDUINO_SETUP.md | Core guide |
| **20 minutes** | PROTOCOL_FORMATS.md, PATTERN_LENGTH_IMPLEMENTATION.md | Detailed guide |
| **30 minutes** | PATTERN_COMPRESSION_GUIDE.md, FEATURES.md | Comprehensive |

---

## 🆘 Help & Support

### Getting Help

**Step 1**: Check documentation index above  
**Step 2**: Read [Troubleshooting Guide](TROUBLESHOOTING.md)  
**Step 3**: Search closed GitHub issues  
**Step 4**: Create new GitHub issue

### Reporting Issues

**Include:**
1. What you tried to do
2. What happened instead
3. Error messages (full text)
4. Your setup (OS, Arduino board, Python version)
5. Protocol file (if relevant)

### Contact & Resources

- **GitHub Issues**: [Create Issue](https://github.com/Swida-Alba/light_controller_v2/issues)
- **Documentation**: This folder (`docs/`)
- **Examples**: `examples/` folder
- **Version History**: [Changelog](../CHANGELOG.md)

---

## 📖 Alphabetical Index

Complete alphabetical listing of all documentation:

<details>
<summary>Click to expand full alphabetical index</summary>

- [Arduino Pattern Length Fix](ARDUINO_PATTERN_LENGTH_FIX.md)
- [Arduino Safety Summary](ARDUINO_SAFETY_SUMMARY.md)
- [Arduino Setup](ARDUINO_SETUP.md)
- [Auto Visualization Summary](AUTO_VISUALIZATION_SUMMARY.md)
- [Build Instructions](BUILD_INSTRUCTIONS.md)
- [Bugfix: Countdown Display](BUGFIX_COUNTDOWN_DISPLAY.md)
- [Bugfix: Start Time](BUGFIX_START_TIME.md)
- [Calibration Guide](CALIBRATION_GUIDE.md)
- [Calibration Integration Summary](CALIBRATION_INTEGRATION_SUMMARY.md)
- [Calibration Logic Analysis](calibration_logic_analysis.md)
- [Calibration Method Usage](CALIBRATION_METHOD_USAGE.md)
- [Calibration Quick Reference](CALIBRATION_QUICK_REFERENCE.md)
- [Calibration Review](CALIBRATION_REVIEW.md)
- [Compile Time Pulse Memory Final](COMPILE_TIME_PULSE_MEMORY_FINAL.md)
- [Correct Calibration Analysis](correct_calibration_analysis.md)
- [Documentation Flowchart](DOCUMENTATION_FLOWCHART.md)
- [Enhanced Realtime Features](ENHANCED_REALTIME_FEATURES.md)
- [Examples Quick Reference](../examples/QUICK_REFERENCE.md)
- [Examples README](../examples/README.md)
- [Features Overview](FEATURES.md)
- [Firmware Update Instructions](FIRMWARE_UPDATE_INSTRUCTIONS.md)
- [Folder Reorganization](FOLDER_REORGANIZATION.md)
- [Folder Structure](FOLDER_STRUCTURE.md)
- [HTML Visualization](HTML_VISUALIZATION.md)
- [HTML Visualization Quick Reference](HTML_VISUALIZATION_QUICK_REFERENCE.md)
- [HTML Visualization Updates](HTML_VISUALIZATION_UPDATES.md)
- [Implementation Complete: Protocol Path](IMPLEMENTATION_COMPLETE_PROTOCOL_PATH.md)
- [Improvements November 8](IMPROVEMENTS_NOVEMBER_8.md)
- [Installation Guide](INSTALLATION.md)
- [JavaScript Update Summary](JAVASCRIPT_UPDATE_SUMMARY.md)
- [Memory Analysis](MEMORY_ANALYSIS.txt)
- [Memory Reporting and Compatibility](MEMORY_REPORTING_AND_COMPATIBILITY.md)
- [Output at Protocol Path](OUTPUT_AT_PROTOCOL_PATH.md)
- [Pattern Compression Guide](PATTERN_COMPRESSION_GUIDE.md)
- [Pattern Length Fix](PATTERN_LENGTH_FIX.md)
- [Pattern Length Implementation](PATTERN_LENGTH_IMPLEMENTATION.md)
- [Pattern Length Verification](PATTERN_LENGTH_VERIFICATION.md)
- [Preview Guide](PREVIEW_GUIDE.md)
- [Protocol Formats](PROTOCOL_FORMATS.md)
- [Protocol Settings](PROTOCOL_SETTINGS.md)
- [Pulse Mode Compatibility Matrix](PULSE_MODE_COMPATIBILITY_MATRIX.md)
- [Pulse Mode Testing Guide](PULSE_MODE_TESTING_GUIDE.md)
- [Pulse Mode Warning Examples](PULSE_MODE_WARNING_EXAMPLES.md)
- [Pulse Period vs Section Time](PULSE_PERIOD_VS_SECTION_TIME.md)
- [Quick Reference: Protocol Path](QUICK_REFERENCE_PROTOCOL_PATH.md)
- [Realtime JavaScript Update](REALTIME_JAVASCRIPT_UPDATE.md)
- [Realtime Visualization](REALTIME_VISUALIZATION.md)
- [Refactoring Guide](REFACTORING_GUIDE.md)
- [Refactoring Summary](REFACTORING_SUMMARY.md)
- [Single Cycle Pulse Details](SINGLE_CYCLE_PULSE_DETAILS.md)
- [Success Summary](SUCCESS_SUMMARY.md)
- [Templates](TEMPLATES.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Update Output at Protocol Path](UPDATE_OUTPUT_AT_PROTOCOL_PATH.md)
- [Usage Guide](USAGE.md)
- [Utils README](../utils/README.md)
- [Visualization Guide](VISUALIZATION_GUIDE.md)
- [Visualization Implementation](VISUALIZATION_IMPLEMENTATION.md)
- [Visualization Quick Card](VISUALIZATION_QUICK_CARD.md)
- [Visualization Quickstart](VISUALIZATION_QUICKSTART.md)

</details>

---

**Last Updated**: November 10, 2025  
**Total Documents**: 60+  
**Maintained By**: Light Controller V2.2 Team

---

**🚀 Ready to get started?** → [Installation Guide](INSTALLATION.md)  
**❓ Need help?** → [Troubleshooting](TROUBLESHOOTING.md)  
**📖 Want examples?** → [Examples README](../examples/README.md)
