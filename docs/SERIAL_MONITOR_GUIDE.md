# Serial Monitor Guide

## Overview

The Light Controller provides multiple tools for real-time monitoring of Arduino channel values during protocol execution:

1. **`--monitor` flag** (integrated with protocol_parser.py) - Recommended for most users
2. **`realtime_plot.py`** - Standalone matplotlib-based visualization
3. **`serial_monitor.py`** - Dash-based web visualization

**Features:**
- 📊 Real-time channel value display with visual bars
- 📈 Live graphical visualization (matplotlib or Plotly)
- 💾 Automatic CSV logging for data analysis
- 📄 **Interactive Plotly HTML export** for sharing and post-analysis
- 🔌 Automatic serial port detection
- ⚡ High-performance rendering (up to 10Hz)
- ⏱️ **5-minute scrolling display window** for long protocols (supports protocols up to days)
- 📐 **Dynamic Y-axis** - Auto-scales to fit actual data values

---

## Value Range Support

The monitoring tools automatically detect and adapt to different output types:

| Output Type | Value Range | Example Pins     | Description                      |
| ----------- | ----------- | ---------------- | -------------------------------- |
| **Binary**  | 0-1         | Digital pins     | ON/OFF only                      |
| **PWM**     | 0-255       | 3, 5, 6, 9...    | 8-bit PWM                        |
| **DAC**     | 0-4095      | 100-101, 201-204 | 12-bit DAC (MCP4728, native DAC) |

**Dynamic Y-axis Scaling:**
- Automatically adjusts Y-axis limits to fit actual data
- Works with sub-ranges (e.g., DAC using only 2000-2500)
- Adds 10% padding for visual clarity
- Reference lines update based on detected range

---

## Quick Start: Using --monitor Flag

The easiest way to monitor PWM values is with the `--monitor` flag:

```bash
python protocol_parser.py 2 /dev/cu.usbmodem1101 examples/1min_test.txt --monitor
```

This will:
1. Upload the protocol to Arduino
2. Open a real-time visualization window (if matplotlib installed)
3. Display a 5-minute scrolling window during execution
4. Save all data to a CSV file
5. **Generate an interactive Plotly HTML file** when monitoring stops

The `--monitor` flag can appear anywhere in the command:
```bash
python protocol_parser.py --monitor 2 /dev/cu.usbmodem1101 protocol.txt
```

**Output files generated:**
- `protocol_monitored.csv` - Raw data for analysis
- `protocol_monitored.html` - Interactive Plotly chart with range slider

---

## Installation

### Required (for any monitoring)

```bash
pip install pyserial
```

### Recommended (for graphical visualization)

```bash
pip install matplotlib
```

### Alternative (for web-based visualization)

```bash
pip install plotly dash
```

---

## Tools Overview

### 1. --monitor Flag (Recommended)

Built into `protocol_parser.py`. Automatically:
- Uses matplotlib if available (portable, cross-platform)
- Falls back to text-mode if matplotlib not installed
- Saves data to `*_monitored.csv`

```bash
# Full command with all options
python protocol_parser.py [pattern_length] [port] [protocol_file] --monitor

# Example
python protocol_parser.py 2 /dev/cu.usbmodem1101 examples/1min_test.txt --monitor
```

### 2. realtime_plot.py (Standalone)

Use for monitoring without running a protocol:

```bash
# Basic monitoring
python realtime_plot.py --port /dev/cu.usbmodem1101

# With CSV output
python realtime_plot.py --port COM3 --output data.csv

# With HTML output (Plotly interactive chart)
python realtime_plot.py --port /dev/cu.usbmodem1101 --output data.csv --html plot.html

# Specify number of channels
python realtime_plot.py --port /dev/ttyACM0 --channels 2
```

**Display Features:**
- 5-minute scrolling window during real-time display
- Stores up to 1 hour of data (36,000 points at 10Hz)
- Exports interactive Plotly HTML with range slider for navigation

### 3. serial_monitor.py (Web-based)

For web browser visualization:

```bash
python serial_monitor.py
python serial_monitor.py --port /dev/cu.usbmodem14301 --output data.csv
```

---

## Detailed Usage

### Basic Monitoring

```bash
python serial_monitor.py
```

Auto-detects Arduino serial port and displays live channel values.

### Specify Serial Port

```bash
python serial_monitor.py --port /dev/cu.usbmodem14301
# or on Windows:
python serial_monitor.py --port COM3
```

### Custom Baud Rate

```bash
python serial_monitor.py --baud 115200
```

### Log to CSV

```bash
python serial_monitor.py --output channel_data.csv
```

Saves timestamped channel values for later analysis.

### Generate Plot

```bash
python serial_monitor.py --plot
```

Displays interactive Plotly chart after monitoring stops.

### Save Plot to HTML

```bash
python serial_monitor.py --save-plot protocol_trace.html
```

Saves plot as standalone HTML file (useful for sharing).

### Combined Example

```bash
python serial_monitor.py --port /dev/cu.usbmodem14301 \
                         --baud 9600 \
                         --output data.csv \
                         --save-plot trace.html
```

---

## Output Format

### Console Display

Real-time bar chart with elapsed time (auto-scales to detected value range):

**PWM (0-255) Example:**
```
⏱️     5.2s | CH1: 128 [█████░░░░░] | CH2: 255 [██████████] | CH3:   0 [░░░░░░░░░░] | CH4: 192 [█████████░] |
```

**DAC (0-4095) Example:**
```
⏱️     5.2s | CH1: 2048[█████░░░░░] | CH2: 4095[██████████] | CH3:    0[░░░░░░░░░░] | CH4: 3072[█████████░] |
```

**Legend:**
- `█` = Value proportional to detected range (PWM or DAC)
- `░` = Remaining intensity range

### Serial Protocol

The monitor listens for Arduino messages in this format:

```
$CHMON:CH1:value1,CH2:value2,CH3:value3,CH4:value4
```

Example (PWM 0-255):
```
$CHMON:CH1:128,CH2:255,CH3:0,CH4:200
```

Example (DAC 0-4095):
```
$CHMON:CH1:2048,CH2:4095,CH3:0,CH4:3200
```

This format is generated by the Arduino channel monitor functions:
- `updateChannelMonitor()` - Called every loop
- `printChannelValues()` - Outputs channel data
- `initChannelMonitor(ms)` - Set print interval

**Note:** The Arduino automatically reports values in the native resolution:
- PWM pins (0-99): 0-255
- Native DAC pins (100-101): 0-4095
- MCP4728 DAC pins (201-204): 0-4095

---

## Arduino Setup

To enable serial monitoring on Arduino:

1. **Default behavior**: Channel values print every 100ms
2. **Custom interval**: Send command from Python
   ```python
   ser.write(b"MONITOR_INTERVAL:50\n")  # Print every 50ms
   ```

The Arduino sends `$CHMON:` messages during pattern execution.

---

## CSV Output Format

```csv
timestamp,time_ms,CH1,CH2,CH3,CH4
2025-12-26T14:23:45.123456,1023.4,0,255,128,64
2025-12-26T14:23:45.224456,1124.5,5,255,127,65
2025-12-26T14:23:45.325456,1225.6,10,255,126,66
```

**Columns:**
- `timestamp`: ISO 8601 datetime
- `time_ms`: Elapsed time in milliseconds
- `CH1-CH4`: Values for each channel (range depends on output type)
  - PWM channels: 0-255
  - DAC channels: 0-4095

---

## Plotly Visualization

### Features

- **Multi-channel view**: Each channel in separate subplot
- **Dynamic Y-axis**: Auto-scales to actual data range
  - Works for binary (0-1), PWM (0-255), or DAC (0-4095)
  - Zooms into sub-ranges (e.g., DAC using only 2000-2500)
- **Interactive controls**:
  - Zoom: Click and drag to zoom
  - Pan: Shift+drag to pan
  - Reset: Double-click to reset view
  - Hover: Show exact values on hover
- **Export**: Camera button to save as PNG

### Example Output

```
Light Controller - Real-time Channel Monitor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Channel 1 (DAC 0-4095) - Y-axis: 2000-2500
├─ Linear ramp 2000→2500 over 5s
├─ Hold at 2500 for 2s
└─ Linear ramp 2500→2000 over 3s

Channel 2 (PWM 0-255) - Y-axis: 0-260
├─ Linear ramp 0→255 over 5s
└─ Linear ramp 255→0 over 5s

... (etc for CH3, CH4)
```

---

## Troubleshooting

### Serial Port Not Found

**Error:** `No serial ports found!`

**Solution:**
1. Check USB cable connection
2. Verify Arduino is powered
3. Check Device Manager (Windows) or `ls /dev/tty*` (Linux/Mac) for ports
4. Explicitly specify port: `--port /dev/cu.usbmodem14301`

### Data Points Lost

**Issue:** Monitor skips some readings

**Causes:**
- Serial port buffer overflow (high data rate)
- USB latency spikes
- Low Arduino print interval

**Solutions:**
- Increase Arduino monitor print interval: `initChannelMonitor(200);` (200ms)
- Lower baud rate if possible
- Reduce max_points to reduce memory load

### Plotly Not Found

**Error:** `ModuleNotFoundError: No module named 'plotly'`

**Solution:**
```bash
pip install plotly
```

---

## Real-World Examples

### Monitor Sunrise Protocol

```bash
# Upload sunrise protocol to Arduino
python protocol_parser.py 2 /dev/cu.usbmodem14301 examples/sunrise_30min.txt

# In another terminal, monitor the execution
python serial_monitor.py --port /dev/cu.usbmodem14301 \
                         --output sunrise_trace.csv \
                         --save-plot sunrise_visualization.html
```

### Analyze Protocol Behavior

```bash
# Monitor and save data
python serial_monitor.py --output protocol_run.csv

# Analyze in Python
import pandas as pd
df = pd.read_csv('protocol_run.csv')

# Plot with matplotlib
df[['CH1', 'CH2', 'CH3', 'CH4']].plot()
```

### Quality Assurance Testing

```bash
# Test multiple boards with same protocol
for board in /dev/cu.usbmodem*; do
  echo "Testing $board..."
  python serial_monitor.py --port "$board" \
                           --output "test_$board.csv" \
                           --save-plot "test_$board.html"
done
```

---

## Integration with Protocol Parser

The protocol parser can automatically launch the monitor:

```python
from serial_monitor import SerialMonitor

# After running protocol
monitor = SerialMonitor(port='/dev/cu.usbmodem14301')
monitor.run()
monitor.plot_data(show=True)
```

---

## Performance Notes

### Memory Usage

- Display window: Shows last 5 minutes (3,000 points at 10Hz)
- Total storage: Up to 1 hour of data (36,000 points)
- Memory per channel: ~300KB for 1 hour of monitoring
- Example: Monitoring 4 channels × 36,000 points ≈ 1.2MB memory

### Long Protocol Support

For protocols lasting hours or days:
- Real-time display shows a 5-minute scrolling window
- All data is stored internally for complete CSV/HTML export
- Interactive Plotly HTML includes range slider to navigate entire timeline

### CPU Usage

- Plotting: ~50-100MB temporary memory during plot generation
- Display update: <1% CPU for console display
- Serial reading: <1% CPU for background monitoring

### Latency

- Serial read latency: ~10-50ms (depends on USB hub)
- Display update: ~500ms (configurable)
- Plotly rendering: 1-3s (depends on data points)

---

## See Also

- [PWM & Ramp Control Guide](PWM_RAMP_CONTROL.md)
- [Arduino Channel Monitor Setup](#) (in Arduino code)
- [Protocol Parser Documentation](../protocol_parser.py)
