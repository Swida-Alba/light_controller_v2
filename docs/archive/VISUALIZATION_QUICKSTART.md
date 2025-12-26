# Protocol Visualization - Quick Guide

## Overview

The `viz_protocol.py` tool generates ASCII timeline visualizations of light control protocols, making it easy to understand timing, patterns, and effects before execution.

## Quick Start

```bash
# Step 1: Generate commands file
python preview_protocol.py examples/simple_blink_example.txt > preview_output.txt

# Step 2: Extract commands to a clean file
grep "^PATTERN:" preview_output.txt > commands.txt

# Or create manually with this format:
# CONFIG:PATTERN_LENGTH:2
# PATTERN:1;CH:1;STATUS:1,0;TIME_MS:1000,1000;REPEATS:10;PULSE:,

# Step 3: Visualize
python viz_protocol.py commands.txt
```

## What You Get

### Visual Timeline
```
CH1 TIMELINE
  Pattern 1
  ---------------------------------------------------------------------------- 
  Time: 0ms → 10.00s
  Duration: 10.00s
  States: [1, 0]
  Times: ['1.00s', '1.00s']
  Repeats: 10x
  
  Timeline:
  Cycle 1: |██████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|
  Cycle 2: |███████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|
  Cycle 3: |██████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|
  ... (7 more cycles)
  
  Legend: █ = ON | ░ = OFF | ≈ = PULSING
```

### Features

- **█ = LED ON** - Solid state
- **░ = LED OFF** - Off state  
- **≈ = PULSING** - PWM pulsing effect applied
- **Duration display** - Human-readable times (ms/s/min/hr)
- **Cycle visualization** - See repeating patterns
- **Summary statistics** - Total channels, patterns, duration

## Example Output

From the simple blink example:

```
CH2 TIMELINE
  Pattern 1
  ----------------------------------------------------------------------------
  Time: 9.99s → 1.50min
  Duration: 1.33min
  States: [1, 0]
  Times: ['4.99s', '4.99s']
  Repeats: 8x
  Pulse: True
  
  Timeline:
  Cycle 1: |≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|
  Cycle 2: |≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|
  Cycle 3: |≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|
  ... (5 more cycles)
  
  Legend: █ = ON | ░ = OFF | ≈ = PULSING
```

Shows Channel 2 pulsing for 5 seconds, then off for 5 seconds, repeated 8 times.

## Use Cases

### 1. Debug Timing Issues
See exactly when each LED turns on/off and for how long.

### 2. Verify Pattern Compression  
Check that compressed patterns match your intended design.

### 3. Understand Pulse Effects
See which states are pulsing vs solid ON.

### 4. Check Channel Synchronization
Compare timelines across channels to verify coordination.

### 5. Calculate Total Duration
Quickly see how long the entire protocol will run.

## Tips

- **Long protocols**: Output can be very long - redirect to file:
  ```bash
  python viz_protocol.py commands.txt > timeline.txt
  ```

- **Focus on one channel**: Filter the output:
  ```bash
  python viz_protocol.py commands.txt | grep -A50 "CH1 TIMELINE"
  ```

- **Compare protocols**: Generate timelines for different versions and diff them:
  ```bash
  python viz_protocol.py protocol_v1_commands.txt > v1_timeline.txt
  python viz_protocol.py protocol_v2_commands.txt > v2_timeline.txt
  diff v1_timeline.txt v2_timeline.txt
  ```

## Command Format

The visualizer expects commands in this format:

```
CONFIG:PATTERN_LENGTH:2
PATTERN:0;CH:1;STATUS:0,0;TIME_MS:5000,0;REPEATS:1
PATTERN:1;CH:1;STATUS:1,0;TIME_MS:1000,1000;REPEATS:10;PULSE:,
PATTERN:2;CH:2;STATUS:1,0;TIME_MS:500,500;REPEATS:20;PULSE:T100pw10,
```

- One command per line
- No comments or extra text
- PULSE field optional (use `,` for no pulse)
- CONFIG line optional (defaults to pattern_length=2)

## Related Tools

- `preview_protocol.py` - Generate commands from protocol files
- `protocol_parser.py` - Execute protocols on Arduino
- `examples/` - Sample protocol files

---

**Version**: 2.2.0  
**Last Updated**: November 8, 2025  
**Status**: Production Ready ✅
