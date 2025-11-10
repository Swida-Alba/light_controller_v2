# Documentation Navigation Flowchart

**Light Controller V2.2** - Visual Guide to Documentation  
**Last Updated**: November 10, 2025

---

## 🗺️ Documentation Journey Map

```
                    ┌─────────────────────────────────────┐
                    │   LIGHT CONTROLLER V2.2 DOCS       │
                    │         START HERE                  │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────┴──────────────────┐
                    │                                 │
            ┌───────▼────────┐              ┌────────▼────────┐
            │  NEW USER?     │              │  EXISTING USER? │
            └───────┬────────┘              └────────┬────────┘
                    │                                │
        ┌───────────┴──────────┐        ┌───────────┴──────────────┐
        │                      │        │                           │
    ┌───▼───┐           ┌─────▼─────┐ ┌▼────────┐         ┌───────▼───────┐
    │ Setup │           │  Learn    │ │ Problem?│         │  Optimize?    │
    └───┬───┘           └─────┬─────┘ └┬────────┘         └───────┬───────┘
        │                     │        │                           │
        │                     │        │                           │
```

---

## 📊 User Journey Flowcharts

### Journey 1: New User → First Success

```
START
  │
  ├─► INSTALLATION.md (10 min)
  │   └─► Install Python, pip, Arduino IDE
  │
  ├─► ARDUINO_SETUP.md (15 min)
  │   └─► Upload firmware, configure PATTERN_LENGTH
  │
  ├─► examples/README.md (5 min)
  │   └─► Try simple_blink_example.txt
  │
  ├─► Execute: python protocol_parser.py
  │   └─► SUCCESS! ✅
  │
  ├─► PROTOCOL_FORMATS.md (15 min)
  │   └─► Learn syntax
  │
  └─► Create your first custom protocol
      └─► DONE! 🎉
```

**Time**: ~45 minutes to first success  
**Prerequisites**: Arduino board, USB cable, computer

---

### Journey 2: Protocol Creator → Custom Protocol

```
GOAL: Create custom protocol
  │
  ├─► PROTOCOL_FORMATS.md
  │   ├─► Excel format?
  │   │   └─► See Excel specification section
  │   └─► Text format?
  │       └─► See Text command syntax section
  │
  ├─► TEMPLATES.md
  │   └─► Choose template matching your needs
  │
  ├─► PROTOCOL_SETTINGS.md
  │   ├─► Set START_TIME
  │   ├─► Configure WAIT_STATUS (optional)
  │   └─► Add WAIT_PULSE (optional)
  │
  ├─► PULSE_PERIOD_VS_SECTION_TIME.md
  │   └─► IF using pulses (⚠️ IMPORTANT!)
  │
  ├─► Test: python preview_protocol.py my_protocol.txt
  │   └─► Review commands
  │
  └─► Execute: python protocol_parser.py
      └─► SUCCESS! ✅
```

**Time**: 30-60 minutes  
**Output**: Working custom protocol

---

### Journey 3: Optimizer → Maximum Compression

```
GOAL: Optimize existing protocol
  │
  ├─► PATTERN_COMPRESSION_GUIDE.md
  │   ├─► Understand pattern detection
  │   ├─► Learn about pattern_length parameter
  │   └─► See compression examples (up to 97%)
  │
  ├─► Analyze current protocol
  │   ├─► Simple ON/OFF patterns?
  │   │   └─► Use pattern_length=2 (default)
  │   └─► 4-phase sequences?
  │       └─► Use pattern_length=4
  │
  ├─► Update Arduino PATTERN_LENGTH
  │   └─► ARDUINO_PATTERN_LENGTH_FIX.md
  │       └─► Re-upload firmware
  │
  ├─► Run with optimized setting
  │   └─► python protocol_parser.py 4
  │
  └─► PATTERN_LENGTH_VERIFICATION.md
      └─► Auto-verification confirms compatibility ✅
```

**Result**: Fewer commands, faster upload, same behavior

---

### Journey 4: Troubleshooter → Problem Solved

```
PROBLEM?
  │
  ├─► TROUBLESHOOTING.md
  │   └─► Quick problem/solution table
  │
  ├─► Connection issues?
  │   └─► ARDUINO_SETUP.md
  │       ├─► Check serial port
  │       ├─► Verify baud rate (9600)
  │       └─► Try RESET button
  │
  ├─► Timing issues?
  │   ├─► CALIBRATION_GUIDE.md
  │   │   └─► Run calibration
  │   ├─► CALIBRATION_QUICK_REFERENCE.md
  │   │   └─► Try different method (V1/V1.1/V2)
  │   └─► PULSE_PERIOD_VS_SECTION_TIME.md
  │       └─► If using pulses ⚠️
  │
  ├─► Memory issues?
  │   └─► MEMORY_REPORTING_AND_COMPATIBILITY.md
  │       └─► COMPILE_TIME_PULSE_MEMORY_FINAL.md
  │           └─► Disable pulse mode if not needed
  │
  ├─► Pattern issues?
  │   ├─► PATTERN_LENGTH_VERIFICATION.md
  │   │   └─► Check Arduino PATTERN_LENGTH
  │   └─► PATTERN_COMPRESSION_GUIDE.md
  │       └─► Understand pattern requirements
  │
  └─► Check bugfix docs:
      ├─► BUGFIX_COUNTDOWN_DISPLAY.md
      ├─► BUGFIX_START_TIME.md
      └─► ARDUINO_SAFETY_SUMMARY.md
```

**Goal**: Identify and fix issue quickly

---

### Journey 5: Developer → Understanding Architecture

```
GOAL: Understand codebase
  │
  ├─► REFACTORING_GUIDE.md
  │   ├─► Class-based architecture
  │   ├─► protocol_parser.py (entry point)
  │   ├─► light_controller_parser.py (core class)
  │   └─► lcfunc.py (utilities)
  │
  ├─► FOLDER_STRUCTURE.md
  │   └─► Project organization
  │
  ├─► PATTERN_LENGTH_IMPLEMENTATION.md
  │   └─► Technical implementation details
  │
  ├─► CALIBRATION_INTEGRATION_SUMMARY.md
  │   └─► Calibration system internals
  │
  └─► VISUALIZATION_IMPLEMENTATION.md
      └─► HTML visualization technical details
```

**Audience**: Contributors, advanced users

---

## 🎯 Decision Trees

### Decision Tree: Which Documentation Do I Need?

```
What do you want to do?
│
├─► Set up for first time
│   └─► Read: INSTALLATION.md → ARDUINO_SETUP.md → examples/README.md
│
├─► Create a protocol
│   └─► Read: PROTOCOL_FORMATS.md → TEMPLATES.md
│
├─► Optimize protocol size
│   └─► Read: PATTERN_COMPRESSION_GUIDE.md → PATTERN_LENGTH_VERIFICATION.md
│
├─► Use pulses
│   └─► Read: PULSE_PERIOD_VS_SECTION_TIME.md → COMPILE_TIME_PULSE_MEMORY_FINAL.md
│
├─► Fix timing issues
│   └─► Read: CALIBRATION_GUIDE.md → CALIBRATION_QUICK_REFERENCE.md
│
├─► Monitor in real-time
│   └─► Read: HTML_VISUALIZATION.md → REALTIME_VISUALIZATION.md
│
├─► Understand architecture
│   └─► Read: REFACTORING_GUIDE.md → FOLDER_STRUCTURE.md
│
└─► Solve specific problem
    └─► Read: TROUBLESHOOTING.md → (specific bugfix docs)
```

---

### Decision Tree: Pattern Length Selection

```
What kind of pattern do you have?
│
├─► Simple ON/OFF alternating
│   └─► Use pattern_length=2 (default)
│       └─► Best compression ratio
│       └─► Examples: simple_blink_example.txt
│
├─► 4-phase sequences
│   └─► Use pattern_length=4
│       └─► Traffic lights, breathing effects
│       └─► Examples: pattern_length_4_example.txt
│
├─► Very complex (5+ phases)
│   └─► Use pattern_length=8+
│       └─► May need Arduino firmware update
│       └─► Read: ARDUINO_PATTERN_LENGTH_FIX.md
│
└─► Not sure?
    └─► Start with pattern_length=2
        └─► System will show efficiency analysis
        └─► Can adjust if needed
```

---

### Decision Tree: Calibration Method

```
Which calibration method should I use?
│
├─► Production use, need highest accuracy
│   └─► V2 (Recommended)
│       └─► 180s, 9 samples, most accurate
│       └─► Read: CALIBRATION_QUICK_REFERENCE.md
│
├─► Need faster calibration, good accuracy
│   └─► V1.1 (New)
│       └─► 150s, 4 samples, active wait
│       └─► Better than V1, same accuracy
│
├─► Backward compatibility
│   └─► V1 (Original)
│       └─► 150s, 4 samples, dead sleep
│       └─► Legacy systems
│
└─► Having calibration issues?
    └─► Read: CALIBRATION_INTEGRATION_SUMMARY.md
        └─► Detailed troubleshooting
```

---

## 📋 Quick Reference Matrix

### By Experience Level

| Level | Start Here | Then Read | Finally |
|-------|------------|-----------|---------|
| **Complete Beginner** | INSTALLATION.md | ARDUINO_SETUP.md | examples/README.md |
| **Basic User** | PROTOCOL_FORMATS.md | TEMPLATES.md | USAGE.md |
| **Intermediate** | PATTERN_COMPRESSION_GUIDE.md | CALIBRATION_GUIDE.md | HTML_VISUALIZATION.md |
| **Advanced** | REFACTORING_GUIDE.md | PATTERN_LENGTH_IMPLEMENTATION.md | CALIBRATION_INTEGRATION_SUMMARY.md |
| **Developer** | FOLDER_STRUCTURE.md | VISUALIZATION_IMPLEMENTATION.md | All implementation docs |

---

### By Time Available

| Time | Read This | Get This Done |
|------|-----------|---------------|
| **5 min** | TEMPLATES.md | Choose template |
| **10 min** | CALIBRATION_QUICK_REFERENCE.md | Understand calibration |
| **15 min** | ARDUINO_SETUP.md | Upload firmware |
| **20 min** | PROTOCOL_FORMATS.md | Understand syntax |
| **30 min** | PATTERN_COMPRESSION_GUIDE.md | Master optimization |
| **1 hour** | Complete new user journey | First successful protocol |

---

### By Problem Type

| Problem | Primary Doc | Supporting Docs |
|---------|-------------|-----------------|
| **Can't connect to Arduino** | ARDUINO_SETUP.md | TROUBLESHOOTING.md |
| **Timing is wrong** | CALIBRATION_GUIDE.md | CALIBRATION_QUICK_REFERENCE.md |
| **Pulses not working** | PULSE_PERIOD_VS_SECTION_TIME.md | COMPILE_TIME_PULSE_MEMORY_FINAL.md |
| **Pattern error** | PATTERN_LENGTH_VERIFICATION.md | ARDUINO_PATTERN_LENGTH_FIX.md |
| **Low memory** | MEMORY_REPORTING_AND_COMPATIBILITY.md | COMPILE_TIME_PULSE_MEMORY_FINAL.md |
| **Commands don't match protocol** | PATTERN_COMPRESSION_GUIDE.md | PREVIEW_GUIDE.md |

---

## 🔗 Documentation Dependencies

### Core Dependencies (Read First)

```
INSTALLATION.md
    └─► Prerequisites for everything

ARDUINO_SETUP.md
    └─► Required for hardware connection

PROTOCOL_FORMATS.md
    └─► Required for creating any protocol
```

### Feature Dependencies (Read When Needed)

```
Pattern Compression:
    PATTERN_COMPRESSION_GUIDE.md
        └─► PATTERN_LENGTH_VERIFICATION.md
            └─► ARDUINO_PATTERN_LENGTH_FIX.md

Pulse Control:
    PULSE_PERIOD_VS_SECTION_TIME.md ⚠️ IMPORTANT
        └─► COMPILE_TIME_PULSE_MEMORY_FINAL.md
            └─► PULSE_MODE_COMPATIBILITY_MATRIX.md

Calibration:
    CALIBRATION_GUIDE.md
        └─► CALIBRATION_QUICK_REFERENCE.md
            └─► CALIBRATION_INTEGRATION_SUMMARY.md (troubleshooting)

Visualization:
    HTML_VISUALIZATION.md
        └─► VISUALIZATION_QUICKSTART.md
            └─► REALTIME_VISUALIZATION.md
```

---

## 🎓 Learning Paths

### Path 1: Beginner to Proficient (3-4 hours)

```
Hour 1: Setup & First Protocol
    ├─► INSTALLATION.md (15 min)
    ├─► ARDUINO_SETUP.md (20 min)
    ├─► examples/README.md (10 min)
    └─► Try example (15 min)

Hour 2: Understanding Formats
    ├─► PROTOCOL_FORMATS.md (30 min)
    ├─► PROTOCOL_SETTINGS.md (15 min)
    └─► TEMPLATES.md (15 min)

Hour 3: Optimization & Features
    ├─► PATTERN_COMPRESSION_GUIDE.md (30 min)
    ├─► HTML_VISUALIZATION.md (15 min)
    └─► CALIBRATION_GUIDE.md (15 min)

Hour 4: Advanced Topics
    ├─► PULSE_PERIOD_VS_SECTION_TIME.md (20 min)
    ├─► PATTERN_LENGTH_VERIFICATION.md (15 min)
    └─► Practice custom protocols (25 min)
```

### Path 2: Quick Start (30 minutes)

```
Minutes 0-10: Setup
    └─► INSTALLATION.md (skim, focus on your OS)

Minutes 10-20: Hardware
    └─► ARDUINO_SETUP.md (focus on your board)

Minutes 20-25: Example
    └─► examples/README.md (run simple_blink_example.txt)

Minutes 25-30: Success!
    └─► Execute and see results
```

### Path 3: Advanced Features (2 hours)

```
Prerequisites: Completed beginner path

Part 1: Optimization (45 min)
    ├─► PATTERN_COMPRESSION_GUIDE.md (deep dive)
    ├─► PATTERN_LENGTH_IMPLEMENTATION.md
    └─► Optimize your protocols

Part 2: Calibration Mastery (30 min)
    ├─► CALIBRATION_INTEGRATION_SUMMARY.md
    ├─► CALIBRATION_QUICK_REFERENCE.md
    └─► Test all three methods

Part 3: Pulse Control (45 min)
    ├─► PULSE_PERIOD_VS_SECTION_TIME.md
    ├─► COMPILE_TIME_PULSE_MEMORY_FINAL.md
    ├─► PULSE_MODE_TESTING_GUIDE.md
    └─► Create pulse protocols
```

---

## 🚀 Quick Start Command Reference

```bash
# Complete beginner
README.md → INSTALLATION.md → ARDUINO_SETUP.md → examples/README.md

# Create Excel protocol
PROTOCOL_FORMATS.md → TEMPLATES.md → Edit in Excel → Execute

# Create Text protocol
PROTOCOL_FORMATS.md → examples/simple_blink_example.txt → Modify → Execute

# Optimize existing
PATTERN_COMPRESSION_GUIDE.md → Update pattern_length → Re-execute

# Fix timing
CALIBRATION_GUIDE.md → Run calibration → Execute

# Use pulses
PULSE_PERIOD_VS_SECTION_TIME.md → Update protocol → Execute

# Real-time monitoring
HTML_VISUALIZATION.md → Execute protocol → Watch browser
```

---

## 📍 You Are Here Maps

### Map: Where Am I in the Documentation?

```
IF you're reading about:
    - Installation/Setup → You're in: Getting Started
    - Protocol syntax → You're in: Core Documentation
    - Pattern compression → You're in: Optimization
    - Calibration → You're in: Timing & Accuracy
    - Visualization → You're in: Monitoring
    - Architecture → You're in: Development

NEXT STEPS:
    - Getting Started → Move to: Core Documentation
    - Core Documentation → Move to: Optimization
    - Optimization → Move to: Advanced Features
    - Any stage → Can jump to: Troubleshooting
```

---

## 🗂️ Complete Index

For alphabetical listing and categorical organization, see:
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Complete navigation guide
- **[README.md](../README.md)** - Project overview

---

**Last Updated**: November 10, 2025  
**Maintained By**: Light Controller V2.2 Team

Happy documenting! 📚
