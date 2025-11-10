# 📁 Folder Structure - Quick Reference

## Clean Organization

```
light_controller_v2.2/
│
├── 🐍 Core Python Files
│   ├── protocol_parser.py          # Main entry point
│   ├── preview_protocol.py         # Preview mode
│   ├── viz_protocol_html.py        # HTML visualizer
│   ├── light_controller_parser.py  # Core class
│   └── lcfunc.py                   # Utility functions
│
├── 🔧 Build & Setup
│   ├── create_exe.py               # Build executable
│   ├── simple_build.py             # Fallback builder
│   ├── requirements.txt            # Dependencies
│   └── setup.py                    # Package setup
│
├── 📚 Examples
│   └── examples/
│       ├── simple_blink_example.txt
│       ├── pattern_length_4_example.txt
│       └── pulse_protocol.txt
│
├── 📤 Output (auto-generated, git ignored)
│   └── output/
│       ├── commands/               # *.txt files
│       └── visualizations/         # *.html files
│
├── 💾 Archive (for saving important experiments)
│   └── archive/
│       └── experiments/
│
├── 📖 Documentation
│   └── docs/
│       ├── REALTIME_VISUALIZATION.md
│       ├── USAGE.md
│       └── ... (20+ guides)
│
└── 🔌 Arduino Firmware
    └── light_controller_v2_arduino/
        └── *.ino
```

## File Naming

### Commands Files
```
output/commands/{protocol}_commands_{timestamp}.txt
```
Example: `simple_blink_example_commands_20251108204423.txt`

### Visualization Files
```
output/visualizations/{protocol}_commands_{timestamp}.html
```
Example: `simple_blink_example_commands_20251108204423.html`

**Note:** Same timestamp = matching files! 🎯

## Git Tracking

### Tracked (in repository)
- ✅ Python source code
- ✅ Examples
- ✅ Documentation
- ✅ Arduino firmware
- ✅ Build scripts

### Ignored (not in repository)
- ❌ `output/` - Generated files
- ❌ `__pycache__/` - Python cache
- ❌ `.vscode/` - Editor settings
- ❌ `dist/` - Built executables

## Quick Operations

### Clean All Generated Files
```bash
rm -rf output/commands/* output/visualizations/*
```

### Archive Important Results
```bash
mkdir -p archive/experiments/my_experiment/
cp output/commands/protocol_*.txt archive/experiments/my_experiment/
cp output/visualizations/protocol_*.html archive/experiments/my_experiment/
```

### Find Recent Files
```bash
# Commands from last 24 hours
find output/commands/ -name "*.txt" -mtime -1

# Visualizations from last week
find output/visualizations/ -name "*.html" -mtime -7
```

## Before vs After

### Before Reorganization ❌
```
light_controller_v2.2/
├── protocol_visualizer.py         # Obsolete
├── protocol_visualizer_backup.py  # Backup
├── viz_protocol.py                 # Duplicate
├── lcfunc.py.backup               # Backup
├── simple_blink_commands.txt      # Scattered
└── various_visualization.html     # Unorganized
```
**Problems:**
- Backup files cluttering root
- Multiple visualizers
- Generated files scattered
- No clear organization

### After Reorganization ✅
```
light_controller_v2.2/
├── viz_protocol_html.py           # Single visualizer
├── lcfunc.py                      # Clean, no backups
│
├── output/                        # All generated files
│   ├── commands/
│   └── visualizations/
│
└── archive/                       # User's important results
```
**Benefits:**
- Clean root directory
- Organized outputs
- Easy to find files
- Clear structure

---

**Updated:** November 8, 2025  
**Version:** 2.2.0  
**Status:** ✅ Organized & Clean
