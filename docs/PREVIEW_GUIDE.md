# Command Preview Feature - Quick Guide

## Overview

The new **Command Preview** feature lets you see what commands will be generated from a protocol file **without connecting to Arduino hardware**. This is perfect for:

- ✅ **Validating** new protocol files before running
- ✅ **Testing** protocols without hardware
- ✅ **Debugging** command generation issues  
- ✅ **Learning** how protocols translate to commands
- ✅ **Sharing** protocol previews with colleagues

---

## Quick Start

### Method 1: Standalone Preview Script (Easiest)

```bash
# Interactive file picker
python preview_protocol.py

# Preview specific file
python preview_protocol.py examples/basic_protocol.txt

# Show only first 5 commands of each type
python preview_protocol.py examples/pulse_protocol.xlsx -n 5

# Use custom calibration factor
python preview_protocol.py protocol.txt -c 1.00131

# Preview and save to file
python preview_protocol.py protocol.xlsx -s
```

### Method 2: Programmatic Usage

```python
from light_controller_parser import LightControllerParser

# Quick preview
parser = LightControllerParser('protocol.xlsx')
preview_data = parser.preview_only(calib_factor=1.00131, max_commands=10)

# Or step-by-step
parser = LightControllerParser('protocol.txt')
parser.calib_factor = 1.00131
parser.generate_pattern_commands()
parser.generate_wait_commands()
preview_data = parser.preview(show_wait=True, show_patterns=True)
```

---

## Command Line Options

### `preview_protocol.py` Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `protocol_file` | | Path to protocol file | Interactive picker |
| `--calib` | `-c` | Calibration factor | 1.0 |
| `--max-commands` | `-n` | Max commands to show | All |
| `--save` | `-s` | Save commands to file | False |
| `--help` | `-h` | Show help message | |

---

## Examples

### Example 1: Basic Preview

```bash
$ python preview_protocol.py examples/basic_protocol.txt

======================================================================
                    COMMAND PREVIEW
======================================================================

Protocol File: basic_protocol.txt
File Type: .TXT
Channels: CH1, CH2, CH3 (3 total)
Calibration Factor: 1.00000
Time Correction: 0.00 sec per 12 hours

Start Times:
  CH1: 10 (wait: 1)
  CH2: 2025-11-08 23:59:00 (wait: 1)
  CH3: 30 (wait: 0)

----------------------------------------------------------------------
WAIT COMMANDS (3 total)
----------------------------------------------------------------------

[1] PATTERN:0;CH:1;STATUS:1,0;TIME_MS:10000,0;REPEATS:1;...
    # Wait pattern, Channel 1, Status: 1 → 0, Time: 10.0s → 0ms, 1 cycle

[2] PATTERN:0;CH:2;STATUS:1,0;TIME_MS:17022000,0;REPEATS:1;...
    # Wait pattern, Channel 2, Status: 1 → 0, Time: 4.7hr → 0ms, 1 cycle

[3] PATTERN:0;CH:3;STATUS:0,0;TIME_MS:30000,0;REPEATS:1
    # Wait pattern, Channel 3, Status: 0 → 0, Time: 30.0s → 0ms, 1 cycle

----------------------------------------------------------------------
PATTERN COMMANDS (6 total)
----------------------------------------------------------------------

[1] PATTERN:1;CH:1;STATUS:0,1;TIME_MS:5000,5000;REPEATS:10;PULSE:T0pw0,T1000pw100
    # Pattern #1, Channel 1, Status: 0 → 1, Time: 5.0s → 5.0s, 10 cycles
    # Pulse: No pulse → 1.00Hz DC=10.0%

... (5 more commands)

======================================================================
SUMMARY: 3 wait + 6 pattern = 9 total commands
======================================================================

✅ Preview completed successfully!

Quick Stats:
  • Channels: 3
  • Wait commands: 3
  • Pattern commands: 6
  • Total commands: 9
  • Calibration: 1.00000
```

### Example 2: Preview with Calibration

```bash
$ python preview_protocol.py protocol.xlsx -c 1.00131 -n 3

🔍 Previewing protocol: protocol.xlsx
----------------------------------------------------------------------

# Shows first 3 commands of each type with calibration applied
```

### Example 3: Preview and Save

```bash
$ python preview_protocol.py protocol.txt -s

# Generates preview AND saves commands to timestamped file:
# protocol_commands_20251108150230.txt
```

---

## Programmatic Usage

### Basic Preview

```python
from light_controller_parser import LightControllerParser

# Preview without hardware
parser = LightControllerParser('examples/basic_protocol.txt')
preview = parser.preview_only(calib_factor=1.00131)

# Access preview data
print(f"Total commands: {preview['total_wait'] + preview['total_patterns']}")
print(f"Channels: {preview['channels']}")
print(f"Wait commands: {preview['wait_commands']}")
print(f"Pattern commands: {preview['pattern_commands']}")
```

### Custom Display

```python
parser = LightControllerParser('protocol.xlsx')
parser.calib_factor = 1.00131
parser.generate_pattern_commands()
parser.generate_wait_commands()

# Custom preview options
preview = parser.preview(
    show_wait=True,        # Show wait commands
    show_patterns=True,    # Show pattern commands
    max_commands=5         # Limit to 5 commands per type
)
```

### Preview Then Execute

```python
# Preview first, then execute if looks good
parser = LightControllerParser('protocol.txt')

# 1. Preview without hardware
preview = parser.preview_only(calib_factor=1.00131)

# 2. User reviews preview...

# 3. If approved, execute with hardware
parser.setup_serial(board_type='Arduino', baudrate=9600)
parser.parse_and_execute()
parser.close()
```

---

## Use Cases

### 1. Protocol Validation

Before running a new protocol on expensive hardware:

```bash
python preview_protocol.py new_protocol.xlsx -c 1.00131
# Review output to ensure commands are correct
```

### 2. Teaching/Documentation

Generate command examples for documentation:

```bash
python preview_protocol.py example.txt -s
# Share the generated _commands_*.txt file
```

### 3. Debugging

When protocol doesn't work as expected:

```bash
python preview_protocol.py problem_protocol.xlsx -n 10
# Examine first 10 commands to identify issues
```

### 4. Batch Validation

Validate multiple protocols:

```python
from light_controller_parser import LightControllerParser

protocols = ['p1.xlsx', 'p2.txt', 'p3.xlsx']
for proto in protocols:
    parser = LightControllerParser(proto)
    try:
        preview = parser.preview_only(calib_factor=1.00131)
        print(f"✅ {proto}: {preview['total_patterns']} commands")
    except Exception as e:
        print(f"❌ {proto}: {e}")
```

---

## Preview Output Explained

### Header Section
- **Protocol File**: Source filename
- **File Type**: .TXT or .XLSX
- **Channels**: Active channels
- **Calibration Factor**: Time correction factor
- **Start Times**: When each channel starts

### Wait Commands (PATTERN:0)
Commands that make Arduino wait until start time:
- Shows countdown time for each channel
- Includes pulse parameters if wait_pulse configured

### Pattern Commands (PATTERN:1+)
Main protocol execution commands:
- Status changes (0=OFF, 1=ON)
- Timing for each transition
- Repeat counts
- Pulse modulation parameters

### Summary
- Total commands generated
- Breakdown by type

---

## Tips

1. **Use `-n` flag** when testing large protocols to avoid long output
2. **Save preview** with `-s` to share with team
3. **Always preview** new protocols before hardware execution
4. **Check calibration** factor - use `-c` to match your actual hardware
5. **Compare output** between TXT and Excel versions of same protocol

---

## See Also

- [Refactoring Guide](REFACTORING_GUIDE.md) - New architecture details
- [Protocol Formats](PROTOCOL_FORMATS.md) - File format specifications
- [Usage Guide](USAGE.md) - Complete usage documentation

---

**Feature Added**: November 8, 2025  
**Enabled by**: Class-based refactoring (v2.2)
