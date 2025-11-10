# Usage Guide

Complete guide to using Light Controller V2.2.

> 📚 **New to the system?** Start with the example files in [`examples/`](../examples/):
> - Review [`examples/README.md`](../examples/README.md) for a guided tour
> - Try `basic_protocol.txt` or `basic_protocol.xlsx` first
> - See working examples of all features with detailed comments

---

## Table of Contents

- [Basic Usage](#basic-usage)
- [Running the Program](#running-the-program)
- [Creating Protocols](#creating-protocols)
- [Advanced Usage](#advanced-usage)
- [Command-Line Options](#command-line-options)
- [Workflow Examples](#workflow-examples)

---

## Basic Usage

### Quick Start

1. **Prepare your protocol file**
   - Create Excel file (`.xlsx`) or Text file (`.txt`)
   - See [Protocol Formats](PROTOCOL_FORMATS.md) for details

2. **Connect Arduino**
   - Plug in via USB
   - Ensure sketch is uploaded
   - Check green LED on board

3. **Run the program**
   ```bash
   python protocol_parser.py
   ```

4. **Select protocol file**
   - Dialog window appears
   - Choose your protocol file
   - Click Open

5. **Wait for execution**
   - Program connects to Arduino
   - Calibrates (first run only)
   - Sends commands
   - Shows progress

---

## Running the Program

### Standard Execution

```bash
# Basic run
python protocol_parser.py

# With Python 3 explicitly
python3 protocol_parser.py

# From virtual environment
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate      # On Windows
python protocol_parser.py
```

### Program Flow

**Step 1: File Selection**
```
=== Light Controller V2.2 ===
Please select a protocol file...
[File dialog opens]
```

**Step 2: File Loading**
```
Loading protocol file: examples/protocol.xlsx
Found 3 channels: CH1, CH2, CH3
Total sections: 10
```

**Step 3: Arduino Connection**
```
Searching for Arduino...
Found Arduino on /dev/cu.usbmodem14101
Testing connection... OK
```

**Step 4: Calibration** (first run only)
```
No calibration factor found.
Running calibration (this takes ~2 minutes)...
Testing with delays: 40s, 60s, 80s, 100s
Calibration complete!
Factor: 1.00131
```

**Step 5: Command Generation**
```
Generating wait commands...
Generating pattern commands...
Total commands: 45
```

**Step 6: Command Execution**
```
Sending commands to Arduino...
Progress: [==========] 45/45 (100%)
All commands sent successfully!
```

**Step 7: Output File**
```
Saved to: protocol_commands_20251108151203.txt
Protocol execution started.
Press Ctrl+C to stop.
```

---

## Creating Protocols

### Excel Protocol

**Step 1: Create Workbook**
1. Open Excel/LibreOffice Calc/Google Sheets
2. Create new workbook
3. Save as `.xlsx` format

**Step 2: Create Protocol Sheet**
```
Sheet name: protocol
```

| step | CH1_status | CH1_time_sec | CH2_status | CH2_time_sec |
|------|------------|--------------|------------|--------------|
| 1    | 1          | 10           | 0          | 10           |
| 2    | 0          | 10           | 1          | 10           |

**Step 3: Create Start Time Sheet**
```
Sheet name: start_time
```

**Row format:**
| Channel | CH1   | CH2   |
|---------|-------|-------|
| start_time | 21:00 | 21:00 |
| wait_status | 1    | 0     |

**Or column format:**
| Channels | Start_time | Wait_status |
|----------|------------|-------------|
| CH1      | 21:00      | 1           |
| CH2      | 21:00      | 0           |

**Step 4: Add Calibration (Optional)**
```
Sheet name: calibration
```

| CALIBRATION_FACTOR |
|--------------------|
| 1.00131            |

**Step 5: Save and Run**
- Save file
- Run `python protocol_parser.py`
- Select your file

---

### Text Protocol

**Step 1: Create Text File**
```bash
# Create new file
touch my_protocol.txt
# Or use any text editor
```

**Step 2: Add Commands**
```txt
# My Light Protocol
# Author: Your Name
# Date: 2025-11-08

# Channel 1: Blink pattern
PATTERN:1;CH:1;STATUS:0,1;TIME_S:5,5;REPEATS:10

# Channel 2: Solid ON
PATTERN:1;CH:2;STATUS:1;TIME_M:30;REPEATS:1

# Start times
START_TIME: {
    'CH1': '21:00',
    'CH2': '21:30'
}

# Calibration (optional)
CALIBRATION_FACTOR: 1.00131
```

**Step 3: Validate Syntax**
- Check all semicolons present
- Verify quotes in START_TIME
- Ensure no typos in keywords

**Step 4: Run**
```bash
python protocol_parser.py
# Select my_protocol.txt
```

---

## Advanced Usage

### Using Output Files as Input

Output files can be reused as input:

```bash
# Generate output
python protocol_parser.py
# Select: protocol.xlsx
# Output: protocol_commands_20251108151203.txt

# Reuse output as input
python protocol_parser.py
# Select: protocol_commands_20251108151203.txt
# Skip calibration (already has factor)
```

**Benefits:**
- Exact timing reproduction
- No calibration needed
- Faster execution
- Version control friendly

---

### Batch Processing

Process multiple protocols:

```python
import lcfunc

files = [
    'protocol1.xlsx',
    'protocol2.txt',
    'protocol3.xlsx'
]

for file in files:
    print(f"Processing {file}...")
    # Load protocol
    if file.endswith('.xlsx'):
        protocol, start_time, calib = lcfunc.ReadExcelFile(file)
    else:
        protocol, start_time, ws, wp, calib = lcfunc.ReadTxtFile(file)
    
    # Process...
    # (see API Reference for complete functions)
```

---

### Testing Protocols Without Arduino

Test protocol parsing without hardware:

```python
import lcfunc

# Load protocol
protocol_df, start_time_df, calib = lcfunc.ReadExcelFile('test.xlsx')

# Get channel info
channel_units, valid_channels = lcfunc.GetChannelInfo(protocol_df)

# Convert times
protocol_df = lcfunc.ConvertTimeToMillisecond(protocol_df, channel_units)

# Generate commands (without sending)
commands = lcfunc.GeneratePatternCommands(protocol_df)

# Inspect commands
for cmd in commands:
    print(cmd)
```

---

### Creating Executable

Package for distribution:

```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
python create_exe.py

# Output:
# - Windows: light_controller.exe
# - macOS: light_controller (app bundle)
# - Linux: light_controller (binary)
```

**Distribution:**
- No Python installation needed on target machine
- Includes all dependencies
- Single file for easy sharing

---

## Command-Line Options

### Environment Variables

Set custom paths:

```bash
# Custom port
export ARDUINO_PORT=/dev/ttyUSB0
python protocol_parser.py

# Custom baud rate
export ARDUINO_BAUD=115200
python protocol_parser.py
```

### Python Module Usage

Import as module:

```python
from protocol_parser import main
import sys

# Set file programmatically
sys.argv = ['protocol_parser.py']  # Avoid file dialog
# Then implement your custom file selection
```

---

## Workflow Examples

### Daily Schedule Workflow

**Scenario:** Turn lights ON at 7 AM, OFF at 10 PM daily

**Protocol (Excel):**

protocol sheet:
| step | CH1_status | CH1_time_hr |
|------|------------|-------------|
| 1    | 1          | 15          |
| 2    | 0          | 9           |

start_time sheet:
| Channels | Start_time | Wait_status |
|----------|------------|-------------|
| CH1      | 07:00      | 0           |

**Run once:**
```bash
python protocol_parser.py
# Select daily_schedule.xlsx
# Let it run indefinitely
```

**Result:**
- Lights ON 7 AM - 10 PM (15 hours)
- Lights OFF 10 PM - 7 AM (9 hours)
- Repeats automatically

---

### Experiment with Pulse Patterns

**Scenario:** Test different pulse frequencies

**Protocol (Text):**
```txt
# Test 1: Slow pulse
PATTERN:1;CH:1;STATUS:1;TIME_S:30;REPEATS:1;PULSE:f0.5pw200

# Test 2: Medium pulse
PATTERN:2;CH:1;STATUS:1;TIME_S:30;REPEATS:1;PULSE:f1pw100

# Test 3: Fast pulse
PATTERN:3;CH:1;STATUS:1;TIME_S:30;REPEATS:1;PULSE:f2pw50

# Start immediately
START_TIME: {'CH1': 5}
```

**Workflow:**
1. Run protocol
2. Observe 30s at each frequency
3. Modify values
4. Re-run immediately
5. Find optimal setting

---

### Multi-Day Event

**Scenario:** Lights for 3-day event with different schedules

**Day 1 (Setup Day):**
```
start_time: 2025-11-08 08:00:00
Pattern: Intermittent (30min ON, 30min OFF)
```

**Day 2 (Event Day):**
```
start_time: 2025-11-09 06:00:00
Pattern: Continuous ON (18 hours)
```

**Day 3 (Teardown):**
```
start_time: 2025-11-10 08:00:00
Pattern: Slow blink (visual indicator)
```

**Execution:**
```bash
# Day 1
python protocol_parser.py  # Select day1.xlsx

# Day 2 (next morning)
Ctrl+C to stop day1
python protocol_parser.py  # Select day2.xlsx

# Day 3 (next morning)
Ctrl+C to stop day2
python protocol_parser.py  # Select day3.xlsx
```

---

### Calibration Workflow

**First Time Setup:**
```bash
# Initial run
python protocol_parser.py
# Calibration runs (~2 min)
# Factor: 1.00131

# Output file contains:
# CALIBRATION_FACTOR: 1.00131
```

**Subsequent Runs:**

Option 1: Use output file
```bash
python protocol_parser.py
# Select: protocol_commands_20251108.txt
# Calibration skipped!
```

Option 2: Add to Excel
```
Sheet: calibration
Cell A1: CALIBRATION_FACTOR
Cell A2: 1.00131
```

Option 3: Add to TXT
```txt
CALIBRATION_FACTOR: 1.00131
# ... rest of protocol
```

---

## Tips and Best Practices

### Protocol Development

1. **Start Simple**
   - Test with 1 channel first
   - Add complexity gradually
   - Verify each addition

2. **Use Comments**
   - Document your intent
   - Note special configurations
   - Date your protocols

3. **Name Clearly**
   - `experiment1_pulse_test.xlsx`
   - `daily_schedule_v2.txt`
   - `calibration_2025_11_08.txt`

4. **Version Control**
   - Keep old versions
   - Use git for TXT protocols
   - Document changes

### Execution Tips

1. **Test First**
   - Use short durations for testing
   - Verify timing is correct
   - Then scale to full duration

2. **Monitor Initially**
   - Watch first few cycles
   - Check LEDs respond correctly
   - Verify timing accuracy

3. **Background Execution**
   ```bash
   # Run in background (Linux/Mac)
   nohup python protocol_parser.py &
   
   # Check status
   tail -f nohup.out
   ```

4. **Auto-Start**
   - Add to startup scripts
   - Use systemd (Linux)
   - Use Task Scheduler (Windows)
   - Use launchd (macOS)

---

## Troubleshooting Usage

### Protocol Not Loading

**Check:**
- File format (.xlsx or .txt)
- Sheet names (protocol, start_time)
- Column headers (CH1_status, CH1_time_sec)
- Syntax in TXT files

### Commands Not Executing

**Verify:**
- Arduino connected
- Sketch uploaded
- Serial Monitor closed
- Correct port selected

### Timing Inaccurate

**Solutions:**
- Re-run calibration
- Check calibration factor
- Verify Arduino not overloaded
- Test with shorter times first

---

## See Also

- [Protocol Formats](PROTOCOL_FORMATS.md) - Detailed format specifications
- [Examples](EXAMPLES.md) - Complete working examples
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

---

*Last Updated: November 8, 2025*
