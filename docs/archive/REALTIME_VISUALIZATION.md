# Real-Time Protocol Visualization Guide

## Overview

Light Controller v2.2 now features **automatic real-time HTML visualization** that opens when you run or preview protocols. The visualization provides live status tracking with animated indicators and a current position marker.

## Features

### 🔴 Live Status Panel

Shows the current state of all channels in real-time:

- **Animated LED indicators** - Pulsing lights show active states
- **Status labels** - ON █ / OFF ░ / PULSING ≈ / COMPLETED ✓
- **Pattern/Cycle tracking** - Shows which pattern and cycle is running
- **Elapsed time** - Time since protocol started

### 📊 Interactive Timeline

Visual representation of your protocol:

- **Color-coded states**
  - 🟢 Green = LED ON (solid)
  - ⬜ Gray = LED OFF
  - 🟡 Orange = LED PULSING (PWM)
  
- **Current position marker** (🔴 Red line)
  - Shows exactly where you are in the timeline
  - Updates automatically every 5 seconds
  - Moves through each pattern and cycle

- **Pattern details**
  - Duration and timing information
  - State transitions
  - Pulse effect indicators
  - Repeat counts

### ⏱️ Timing Information

- **Start time** - When the protocol began
- **Elapsed time** - Time since start
- **Pattern duration** - How long each pattern runs
- **Total duration** - Complete protocol length

## Automatic Generation

The visualization is automatically created when you:

### 1. Preview a Protocol

```bash
python preview_protocol.py examples/simple_blink_example.txt
```

**Result:** 
- Commands preview in terminal
- HTML visualization opens in browser
- Shows protocol structure (no timing marker)

### 2. Execute a Protocol

```bash
python protocol_parser.py
# Select your protocol file
```

**Result:**
- Protocol runs on Arduino
- HTML visualization opens with **real-time status**
- Red marker shows current position
- Auto-refreshes every 5 seconds

## Manual Generation

You can also manually create visualizations:

### With Start Time (Real-time Tracking)

```bash
python viz_protocol_html.py commands.txt --start-time "2025-11-08 20:30:00"
```

### Without Start Time (Structure Only)

```bash
python viz_protocol_html.py commands.txt
```

### Custom Output Name

```bash
python viz_protocol_html.py commands.txt --output my_protocol
```

## Understanding the Visualization

### Status Panel

```
🔴 LIVE STATUS - 2025-11-08 20:35:42

Started: 2025-11-08 20:30:00      Elapsed: 5.70min

┌─────────────────────┐
│   Channel 1         │
│   ● ON █           │  ← Animated green LED
│   Pattern: 2        │
│   Cycle: 3          │
│   Elapsed: 5.70min  │
└─────────────────────┘
```

**LED Colors:**
- 🟢 Green pulsing = Currently ON
- ⬜ Gray static = Currently OFF
- 🟡 Orange pulsing = PWM pulsing active
- 🟢 Green static = Completed successfully

### Timeline View

```
Pattern 1                                    ▶ CURRENT
────────────────────────────────────────────
Time: 0ms → 10.00s
Duration: 10.00s
States: [1, 0]
Times: ['1.00s', '1.00s']
Repeats: 5x

Visual:
Cycle 1: |██████████████░░░░░░░░░░|
              ↑ Red marker shows current position
Cycle 2: |██████████████░░░░░░░░░░|
Cycle 3: |██████████████░░░░░░░░░░|
... (2 more cycles)
```

**Markers:**
- **▶ CURRENT** badge = This pattern is currently running
- **Red vertical line** = Exact position in the cycle
- **Red dot** = Current time marker

### Pattern Block Highlighting

- **Normal patterns**: White background with purple left border
- **Current pattern**: Pink background with red left border
- **Completed patterns**: No special highlighting

## Auto-Refresh Behavior

The HTML page automatically refreshes every 5 seconds to update:

1. Current time display
2. Elapsed time
3. Channel status indicators
4. Position marker on timeline
5. Pattern/cycle information

**Note:** The page will continue auto-refreshing until you close it or the protocol completes.

## Use Cases

### 1. Protocol Monitoring

Watch your protocol run in real-time:

```bash
python protocol_parser.py
# Select protocol
# Browser opens showing live status
# Leave it open to monitor progress
```

**Benefits:**
- See which channels are active
- Verify timing is correct
- Catch issues immediately
- Know when protocol completes

### 2. Pre-Execution Review

Check protocol before running:

```bash
python preview_protocol.py my_protocol.txt
# Browser opens showing structure
# Review patterns and timing
# No current position marker (not running yet)
```

**Benefits:**
- Verify protocol looks correct
- Check pattern durations
- Understand channel coordination
- Spot potential issues

### 3. Documentation

Generate visual documentation:

```bash
# Generate visualization without running
python viz_protocol_html.py commands.txt -o experiment_20251108
# Share experiment_20251108.html with team
```

**Benefits:**
- Share protocol designs
- Document experiments
- Training materials
- Publication figures

### 4. Debugging

Troubleshoot timing issues:

```bash
# Run protocol with visualization
python protocol_parser.py
# Watch the current position marker
# Verify it matches expected behavior
```

**Benefits:**
- Visual timing verification
- Pattern transition checking
- Pulse effect confirmation
- Channel synchronization validation

## Customization

### Change Refresh Rate

Edit `viz_protocol_html.py`:

```javascript
// Change from 5000 (5 seconds) to desired milliseconds
setTimeout(() => {
    location.reload();
}, 5000);  // ← Modify this value
```

### Disable Auto-Refresh

Remove or comment out the auto-refresh script in the generated HTML:

```javascript
// Comment this out to disable auto-refresh
/*
setTimeout(() => {
    location.reload();
}, 5000);
*/
```

### Custom Styling

The HTML includes embedded CSS. You can modify colors, sizes, and layout by editing the `<style>` section in `viz_protocol_html.py`.

## Tips and Tricks

### 1. Keep Browser Open

Leave the visualization browser window open while your protocol runs to continuously monitor status.

### 2. Multiple Monitors

Put the visualization on a second monitor while controlling the experiment on your main screen.

### 3. Screenshot Documentation

Take screenshots at key moments for documentation:
- Protocol start
- Mid-execution
- Completion

### 4. Share Links

The HTML file is standalone - you can share it via email or file sharing and it will work on any computer with a web browser.

### 5. Archive Experiments

Save visualization HTML files with descriptive names:
```bash
python viz_protocol_html.py commands.txt -o "experiment_2025-11-08_trial3"
```

## Troubleshooting

### Visualization Doesn't Open

**Problem:** Browser doesn't open automatically

**Solutions:**
1. Manually open the HTML file from the project directory
2. Look for: `*_visualization.html`
3. Check console output for the file path

### Wrong Time Displayed

**Problem:** Start time doesn't match actual start

**Solution:**
- The start time is set when protocol execution begins
- If you started the protocol at a different time, manually generate visualization:
  ```bash
  python viz_protocol_html.py commands.txt --start-time "YYYY-MM-DD HH:MM:SS"
  ```

### Page Not Refreshing

**Problem:** Status doesn't update

**Solutions:**
1. Check browser console for JavaScript errors
2. Manually refresh with F5 or Cmd+R
3. Ensure JavaScript is enabled in browser

### Position Marker Not Visible

**Problem:** Can't see the red marker

**Solutions:**
1. Check if protocol has actually started
2. Verify start time is correct
3. If protocol completed, marker won't show

### Browser Shows Old Data

**Problem:** Page shows outdated information

**Solution:**
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (macOS)
- Or clear browser cache

## Technical Details

### File Generation

**When previewing:**
- Input: Protocol file (.txt or .xlsx)
- Output: `{protocol_name}_visualization.html`
- Start time: Not set (structure only)

**When executing:**
- Input: Protocol file + Arduino connection
- Output: `{protocol_name}_commands_TIMESTAMP.txt` → `{protocol_name}_visualization.html`
- Start time: Automatically set to execution time

### Position Calculation

The visualization calculates current position by:

1. Recording protocol start time
2. Getting current time
3. Calculating elapsed milliseconds
4. Walking through patterns to find current position:
   - Which pattern is active
   - Which cycle within that pattern
   - Which state within that cycle
   - How far into that state

### Auto-Refresh Mechanism

Uses JavaScript `setTimeout` to reload page every 5 seconds:
- Preserves all settings and start time
- Recalculates current position
- Updates all indicators and markers
- Maintains scroll position

## Examples

### Example 1: Simple Blink Protocol

```bash
python preview_protocol.py examples/simple_blink_example.txt
```

**Shows:**
- 4 channels
- Wait patterns (Pattern 0)
- Main patterns with blink sequences
- Pulse effects on some channels
- No timing marker (preview mode)

### Example 2: Running Protocol with Status

```bash
python protocol_parser.py
# Select: examples/pulse_protocol.txt
```

**Shows:**
- Real-time channel status
- Animated pulsing indicators
- Red marker moving through timeline
- Pattern transitions
- Auto-updates every 5 seconds

### Example 3: Custom Visualization

```bash
# Run protocol
python protocol_parser.py
# Get commands file (e.g., pulse_protocol_commands_20251108203000.txt)

# Create custom visualization with specific start time
python viz_protocol_html.py pulse_protocol_commands_20251108203000.txt \
  --start-time "2025-11-08 20:30:00" \
  --output pulse_experiment_trial1
```

**Result:** `pulse_experiment_trial1.html` with accurate timing

## Integration with Workflow

### Recommended Workflow

1. **Create protocol** - Write .txt or .xlsx file
2. **Preview** - Check structure
   ```bash
   python preview_protocol.py my_protocol.txt
   ```
   - Review visualization in browser
   - Verify patterns and timing
   
3. **Execute** - Run on Arduino
   ```bash
   python protocol_parser.py
   ```
   - Visualization opens automatically
   - Monitor real-time status
   - Watch progress through timeline
   
4. **Document** - Save visualization for records

### Automation Script Example

```bash
#!/bin/bash
# Run protocol and save visualization

PROTOCOL="experiments/trial_protocol.txt"
OUTPUT_DIR="results/$(date +%Y%m%d)"

mkdir -p "$OUTPUT_DIR"

# Run protocol
python protocol_parser.py "$PROTOCOL"

# Copy visualization to results
cp *_visualization.html "$OUTPUT_DIR/"

echo "Experiment complete. Results in $OUTPUT_DIR"
```

## Related Documentation

- [VISUALIZATION_QUICKSTART.md](VISUALIZATION_QUICKSTART.md) - Quick reference for visualization basics
- [USAGE.md](USAGE.md) - Complete usage instructions
- [PROTOCOL_FORMATS.md](PROTOCOL_FORMATS.md) - Protocol file format reference

---

**Version**: 2.2.0  
**Last Updated**: November 8, 2025  
**Status**: Production Ready ✅  
**Feature**: Real-Time Visualization 🔴
