# Protocol Visualization Guide

## Overview

The Protocol Visualizer generates visual timeline representations of light control protocols with detailed annotations. It helps you understand and debug complex protocols before executing them.

## Quick Start

```bash
# Generate both text and HTML visualizations
python protocol_visualizer.py examples/simple_blink_example.txt

# Open the HTML file in your browser to see the interactive timeline
```

## Features

### 1. Visual Timelines
- **Per-channel visualization** - See each channel's behavior separately
- **Time markers** - Precise start/end times for each pattern
- **Duration display** - Human-readable durations (ms, s, min, hr)
- **Cycle representation** - Shows pattern repetition visually

### 2. State Representation

**Text Mode (ASCII):**
```
█ = LED ON (solid)
░ = LED OFF
≈ = LED PULSING
```

**HTML Mode (colored):**
- 🟢 Green gradient = ON
- ⬜ Gray = OFF
- 🟡 Yellow stripes = PULSING

### 3. Annotations and Notes
- Automatic note generation for pulse effects
- Pattern timing information
- Wait period indicators
- Channel statistics

### 4. Statistics
- Total channels and patterns
- Per-channel duration
- Pulse effect detection
- Compression information

## Usage

### Basic Usage

```bash
# Visualize a protocol file
python protocol_visualizer.py <protocol_file>

# Examples:
python protocol_visualizer.py examples/simple_blink_example.txt
python protocol_visualizer.py examples/pulse_protocol.txt
python protocol_visualizer.py protocol.xlsx
```

### Output Formats

```bash
# Text only (ASCII art)
python protocol_visualizer.py protocol.txt --format text

# HTML only (colored, interactive)
python protocol_visualizer.py protocol.txt --format html

# Both formats (default)
python protocol_visualizer.py protocol.txt --format both
```

### Custom Output Name

```bash
# Specify output filename (without extension)
python protocol_visualizer.py protocol.txt --output my_visualization

# Creates:
#   my_visualization.txt
#   my_visualization.html
```

### Pattern Length

```bash
# Specify pattern length for Excel files
python protocol_visualizer.py protocol.xlsx --pattern-length 4
```

## Output Examples

### Text Visualization

```
================================================================================
PROTOCOL TIMELINE VISUALIZATION
================================================================================
File: examples/simple_blink_example.txt
Pattern Length: 2
Date: 2025-11-08 14:30:00
================================================================================

START TIMES:
  CH1: 21:00 (wait: OFF)
  CH2: 60 (wait: ON)

================================================================================
CH1 TIMELINE
================================================================================

  Pattern 1
  ----------------------------------------------------------------------------
  Time: 0.000s → 10.000s
  Duration: 10.00s
  States: [1, 0]
  Times: ['1.00s', '1.00s']
  Repeats: 5x

  Timeline:
  Cycle 1: |█████████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|
  Cycle 2: |█████████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|
  ... (3 more cycles)
  
  Legend: █ = ON | ░ = OFF | ≈ = PULSING

  ============================================================================
  Total Duration: 10.00s
  ============================================================================
```

### HTML Visualization

The HTML output includes:
- **Color-coded timeline bars** - Hover to see duration
- **Interactive elements** - Click to expand/collapse
- **Gradient effects** - Beautiful visual representation
- **Responsive design** - Works on all screen sizes
- **Print-friendly** - Generate reports

## Use Cases

### 1. Protocol Debugging

Before running a protocol on hardware:

```bash
# Visualize to check timing
python protocol_visualizer.py my_protocol.txt

# Verify:
# - Patterns are correctly formed
# - Timing is as expected
# - Pulse effects are applied correctly
# - Wait periods are properly configured
```

### 2. Documentation

Generate visual documentation for protocols:

```bash
# Create HTML report
python protocol_visualizer.py experiment_protocol.xlsx --format html --output experiment_report

# Share the HTML file with team members
```

### 3. Protocol Comparison

Compare different protocol versions:

```bash
# Visualize both versions
python protocol_visualizer.py protocol_v1.txt --output v1
python protocol_visualizer.py protocol_v2.txt --output v2

# Compare the visualizations side-by-side
```

### 4. Teaching and Training

Use visualizations to explain protocols:

```bash
# Generate HTML with annotations
python protocol_visualizer.py training_example.txt --format html

# Open in browser for presentation
```

## Understanding the Visualization

### Timeline Segments

Each colored/shaded segment represents a state:
- **Width** = Duration (proportional to time)
- **Color/Pattern** = State (ON/OFF/PULSING)
- **Position** = Timing in sequence

### Pattern Cycles

Patterns repeat according to the REPEATS parameter:
- First cycle shown in detail
- Middle cycles summarized (if many)
- Last cycle shown for reference

### Notes Section

Automatically generated notes include:
- Pulse effect locations
- Special timing considerations
- Pattern anomalies (if any)

### Statistics

Summary information:
- **Total channels** - Number of active channels
- **Total patterns** - Sum of all patterns
- **Per-channel stats** - Duration and features
- **Pulse detection** - Which channels use pulse effects

## Tips and Tricks

### 1. Large Protocols

For very long protocols (many patterns):
- Use HTML format (better performance)
- Text format may be very long
- Consider visualizing one channel at a time

### 2. Excel Files

For Excel protocols:
- Visualization shows compressed patterns
- Match pattern_length to your protocol
- See compression efficiency in stats

### 3. Pulse Effects

Pulse patterns are shown with special indicators:
- Text: `≈` character
- HTML: Yellow striped pattern
- Hover (HTML) shows pulse parameters

### 4. Wait Periods

Wait periods (Pattern 0) are:
- Highlighted in yellow (HTML)
- Marked with ⏰ icon
- Show wait status (ON/OFF)

## Troubleshooting

### "File not found" Error

```bash
# Use absolute or relative path
python protocol_visualizer.py /full/path/to/protocol.txt

# Or from project directory
cd light_controller_v2.2
python protocol_visualizer.py examples/simple_blink_example.txt
```

### "Module not found" Error

```bash
# Install dependencies
pip install -r requirements.txt
```

### HTML Not Opening

```bash
# Manually open the HTML file
# Windows:
start visualization.html

# macOS:
open visualization.html

# Linux:
xdg-open visualization.html
```

### Visualization Looks Wrong

Check:
1. **Pattern length** - Use correct value with `--pattern-length`
2. **Protocol format** - Ensure protocol file is valid
3. **Browser compatibility** - Use modern browser for HTML

## Command-Line Reference

```bash
python protocol_visualizer.py [OPTIONS] protocol_file

Positional Arguments:
  protocol_file              Protocol file (.txt or .xlsx)

Optional Arguments:
  -h, --help                Show help message
  -f, --format FORMAT       Output format: text, html, or both (default: both)
  -o, --output OUTPUT       Output filename without extension
  -p, --pattern-length N    Pattern length for compression (default: 2)
```

## Examples

### Example 1: Simple Blink

```bash
python protocol_visualizer.py examples/simple_blink_example.txt
```

**Output:**
- `simple_blink_example_visualization.txt` - ASCII timeline
- `simple_blink_example_visualization.html` - Interactive timeline

### Example 2: Pulse Protocol

```bash
python protocol_visualizer.py examples/pulse_protocol.txt --format html
```

Shows pulse effects with striped patterns.

### Example 3: Complex Protocol

```bash
python protocol_visualizer.py examples/pattern_length_4_example.txt --pattern-length 4 --output complex_timeline
```

Handles 4-element patterns correctly.

### Example 4: Excel Protocol

```bash
python protocol_visualizer.py protocol.xlsx --format both --output report
```

Generates both formats for Excel protocols.

## Integration with Workflow

### Recommended Workflow

1. **Create protocol** - Write .txt or .xlsx file
2. **Visualize** - Check timing and patterns
   ```bash
   python protocol_visualizer.py my_protocol.txt
   ```
3. **Preview** - Test command generation
   ```bash
   python preview_protocol.py my_protocol.txt
   ```
4. **Execute** - Run on Arduino
   ```bash
   python protocol_parser.py
   ```

### Automation

Include in build scripts:

```bash
#!/bin/bash
# Generate visualizations for all protocols

for protocol in protocols/*.txt; do
    echo "Visualizing $protocol..."
    python protocol_visualizer.py "$protocol" --format html
done

echo "All visualizations complete!"
```

## Advanced Features

### Custom Styling (HTML)

Edit the CSS in `protocol_visualizer.py` to customize:
- Colors
- Fonts
- Layout
- Animation effects

### Batch Processing

```python
from protocol_visualizer import ProtocolVisualizer

protocols = ['protocol1.txt', 'protocol2.txt', 'protocol3.txt']

for protocol in protocols:
    viz = ProtocolVisualizer(protocol)
    viz.save_visualization(f"{protocol}_viz", format='html')
```

### API Usage

```python
from protocol_visualizer import ProtocolVisualizer

# Create visualizer
viz = ProtocolVisualizer('protocol.txt', pattern_length=2)

# Parse protocol
viz.parse_protocol()

# Generate text visualization
text_output = viz.generate_text_visualization()
print(text_output)

# Generate HTML visualization
html_output = viz.generate_html_visualization()

# Save to files
viz.save_visualization('output', format='both')
```

## Related Documentation

- [Pattern Compression Guide](PATTERN_COMPRESSION_GUIDE.md) - Understanding pattern logic
- [Protocol Formats Guide](PROTOCOL_FORMATS.md) - Protocol syntax reference
- [Usage Guide](USAGE.md) - Complete usage instructions
- [Preview Guide](PREVIEW_GUIDE.md) - Command preview without hardware

---

**Version**: 2.2.0  
**Last Updated**: November 8, 2025  
**Status**: Production Ready ✅
