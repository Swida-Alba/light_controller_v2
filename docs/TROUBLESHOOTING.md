# Troubleshooting Guide

Solutions for common issues with Light Controller V2.2.

---

## Table of Contents

- [Installation Issues](#installation-issues)
- [Arduino Connection Issues](#arduino-connection-issues)
- [Protocol File Issues](#protocol-file-issues)
- [Timing Issues](#timing-issues)
- [LED/Hardware Issues](#ledhardware-issues)
- [Software Errors](#software-errors)

---

## Installation Issues

### Python Not Found

**Symptom:**
```bash
python: command not found
```

**Solutions:**

**macOS/Linux:**
```bash
# Try python3 instead
python3 lcfunc.py

# Check if Python installed
which python3

# Install if missing (macOS)
brew install python3

# Install if missing (Linux)
sudo apt-get install python3
```

**Windows:**
```bash
# Try py instead
py lcfunc.py

# Check if Python installed
py --version

# Reinstall Python with "Add to PATH" checked
```

---

### Package Installation Fails

**Symptom:**
```bash
ERROR: Could not find a version that satisfies the requirement...
```

**Solutions:**

**Check Python version:**
```bash
python --version  # Must be 3.8+
```

**Upgrade pip:**
```bash
pip install --upgrade pip
```

**Install packages one by one:**
```bash
pip install pandas
pip install openpyxl
pip install pyserial
```

**Use requirements.txt:**
```bash
pip install -r requirements.txt
```

**Try with user flag:**
```bash
pip install --user -r requirements.txt
```

---

### Permission Denied (Linux/macOS)

**Symptom:**
```bash
Permission denied: '/dev/ttyACM0'
```

**Solutions:**

**Add user to dialout group:**
```bash
sudo usermod -a -G dialout $USER
# Logout and login for changes to take effect
```

**Temporary fix:**
```bash
sudo chmod 666 /dev/ttyACM0
# Must repeat after each restart
```

**Verify groups:**
```bash
groups  # Should show dialout
```

---

### pyserial vs serial Conflict

**Symptom:**
```python
AttributeError: module 'serial' has no attribute 'Serial'
```

**Solution:**

**Uninstall wrong package:**
```bash
pip uninstall serial
pip uninstall pyserial

# Reinstall correct package
pip install pyserial
```

**Verify:**
```python
python -c "import serial; print(serial.__version__)"
# Should print version number (e.g., 3.5)
```

---

## Arduino Connection Issues

### COM Port Not Found

**Symptom:**
```
Error: Could not find Arduino on any port
```

**Solutions:**

**1. Find correct port:**

**Windows:**
- Open Device Manager
- Look under "Ports (COM & LPT)"
- Note COM number (e.g., COM3)

**macOS:**
```bash
ls /dev/tty.*
# Look for /dev/tty.usbmodem* or /dev/tty.usbserial*
```

**Linux:**
```bash
ls /dev/ttyACM* /dev/ttyUSB*
# Usually /dev/ttyACM0 or /dev/ttyUSB0
```

**2. Verify connection:**
- Check USB cable (try different cable)
- Try different USB port
- Check Arduino power LED is ON
- Close other programs using port (Arduino IDE Serial Monitor)

**3. Update drivers (Windows):**
- Install Arduino IDE (includes drivers)
- Manual driver: https://www.arduino.cc/en/Guide/DriverInstallation

---

### Arduino Due Port Confusion

**Symptom:**
- Works in Arduino IDE, fails with Python
- "Port busy" error

**Solution:**

**Arduino Due has TWO USB ports:**

1. **Programming Port** (near power jack):
   - For uploading sketch
   - For Arduino IDE Serial Monitor

2. **Native USB Port** (near reset button):
   - **USE THIS for Light Controller V2.2**
   - For protocol execution
   - Different COM port number

**Steps:**
1. Upload sketch via Programming Port
2. Disconnect USB
3. Connect to Native USB Port
4. Note new COM port
5. Use this port in Python script

---

### Port Busy/In Use

**Symptom:**
```
SerialException: Port COM3 in use
```

**Solutions:**

**Close other programs:**
- Arduino IDE Serial Monitor
- Serial terminal programs (PuTTY, CoolTerm, etc.)
- Other Python scripts

**Kill processes (if needed):**

**Windows:**
```bash
# Find process using port
netstat -ano | findstr :COM3

# Kill process (replace PID)
taskkill /PID <process_id> /F
```

**macOS/Linux:**
```bash
# Find process
lsof | grep tty

# Kill process
kill <process_id>
```

**Restart system:**
- Last resort if port stuck

---

### Communication Timeout

**Symptom:**
```
Timeout: No response from Arduino
```

**Solutions:**

**1. Check baud rate:**
- Arduino sketch: 115200
- Python script: 115200
- Must match exactly

**2. Reset Arduino:**
- Press reset button
- Wait 2 seconds
- Try again

**3. Re-upload sketch:**
- Open Arduino IDE
- Upload sketch again
- Verify in Serial Monitor

**4. Check USB cable:**
- Some cables are power-only (no data)
- Use cable that came with Arduino
- Try different cable

---

## Protocol File Issues

### Excel File Not Found

**Symptom:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'protocol.xlsx'
```

**Solutions:**

**1. Check file path:**
```bash
# Use absolute path
/Users/username/Documents/protocol.xlsx

# Or run from same directory as file
cd /Users/username/Documents
python lcfunc.py
```

**2. Check file extension:**
- Must be `.xlsx` (not `.xls`)
- Use "Save As" > Excel Workbook (.xlsx)

**3. Verify file exists:**
```bash
# macOS/Linux
ls -la protocol.xlsx

# Windows
dir protocol.xlsx
```

---

### Missing Required Sheet

**Symptom:**
```
Error: 'protocol' sheet not found in Excel file
```

**Solutions:**

**1. Check sheet names:**
- Required: `protocol` (lowercase)
- Required: `start_time` (lowercase)
- Optional: `calibration` (lowercase)

**2. Rename sheets:**
- Right-click sheet tab → Rename
- Type exact name (case-sensitive)

**3. Verify sheet exists:**
- Open Excel file
- Check tabs at bottom
- Add missing sheets if needed

---

### Invalid Column Names

**Symptom:**
```
Error: No columns matching 'CH1_status' pattern found
```

**Solutions:**

**1. Check column names:**
```
Required pattern: CH[N]_status, CH[N]_time_[unit]
Valid: CH1_status, CH1_time_sec
Invalid: CH 1_status, CH1_Status, CH1-status
```

**2. Common mistakes:**
- Spaces in names: `CH1 _status` → `CH1_status`
- Wrong case: `CH1_Status` → `CH1_status`
- Missing underscore: `CH1status` → `CH1_status`

**3. Check channel numbers:**
- Must start at 1: CH1, CH2, CH3...
- Must be continuous (no gaps)
- Cannot skip numbers

---

### Invalid Time Unit

**Symptom:**
```
Error: Time unit 'seconds' not recognized
```

**Solutions:**

**Valid time unit suffixes:**
- Seconds: `_s`, `_sec`
- Minutes: `_m`, `_min`
- Hours: `_h`, `_hr`, `_hour`
- Milliseconds: `_ms`, `_msec`

**Examples:**
```
✓ CH1_time_sec
✓ CH1_time_s
✓ CH2_time_min
✓ CH3_time_hr
✗ CH1_time_seconds (wrong)
✗ CH1_time_second (wrong)
```

---

### Text File Parse Error

**Symptom:**
```
Error: Invalid PATTERN command format
```

**Solutions:**

**1. Check syntax:**
```txt
✓ PATTERN:1;CH:1;STATUS:1;TIME_S:10;REPEATS:5
✗ PATTERN 1;CH:1;STATUS:1;TIME_S:10;REPEATS:5  (missing colon)
✗ PATTERN:1,CH:1,STATUS:1,TIME_S:10,REPEATS:5  (wrong separator)
```

**2. Check spacing:**
```txt
✓ PATTERN:1;CH:1;STATUS:1;TIME_S:10;REPEATS:5
✗ PATTERN: 1; CH: 1; STATUS: 1 (extra spaces)
```

**3. Check quotes:**
```txt
✓ START_TIME: {'CH1': '21:00'}
✗ START_TIME: {"CH1": "21:00"}  (wrong quotes)
✗ START_TIME: {CH1: 21:00}      (missing quotes)
```

---

### Pulse Parameter Conflict

**Symptom:**
```
Error: Cannot use both frequency and period
```

**Solutions:**

**Use ONE combination only:**

**Option 1:** Frequency + Pulse Width ✓
**Option 2:** Frequency + Duty Cycle ✓
**Option 3:** Period + Pulse Width ✓
**Option 4:** Period + Duty Cycle ✓

**Invalid combinations:**
```
✗ Frequency + Period (both specified)
✗ Pulse Width + Duty Cycle (both specified)
✗ All four parameters (conflict)
```

**Fix:** Remove conflicting columns/parameters.

---

## Timing Issues

### Commands Execute Too Fast/Slow

**Symptom:**
- Expected 10 seconds, took 9.9 or 10.1 seconds
- Long protocols drift over time

**Solutions:**

**1. Use calibration:**
```txt
# Add calibration factor from previous run
CALIBRATION_FACTOR: 1.00131
```

**2. Re-run calibration:**
- Remove calibration factor
- Let program calibrate (2 minutes)
- Improves accuracy

**3. Check environment:**
- Temperature affects Arduino timing
- Re-calibrate if environment changes significantly

---

### Start Time Not Working

**Symptom:**
- Protocol doesn't start at specified time
- Starts immediately instead

**Solutions:**

**1. Check time format:**
```txt
✓ '21:00'           (time only)
✓ '21:00:00'        (with seconds)
✓ '2025-11-08 21:00:00'  (full datetime)
✗ 21:00             (missing quotes)
✗ '9:00 PM'         (not 24-hour format)
```

**2. Check if time already passed:**
- If current time > start time, waits until tomorrow
- Use full datetime to specify exact date

**3. Use countdown for testing:**
```txt
START_TIME: {'CH1': 60}  # Start in 60 seconds
```

---

### Calibration Takes Too Long

**Symptom:**
- 2-minute calibration every time
- Want to skip calibration

**Solution:**

**Reuse calibration factor:**

1. Run protocol once with calibration
2. Check output file: `protocol_commands_YYYYMMDDHHMMSS.txt`
3. Find line: `CALIBRATION_FACTOR: 1.00131`
4. Add to next protocol:

**Excel:** Add `calibration` sheet with value

**Text:**
```txt
CALIBRATION_FACTOR: 1.00131
```

**Note:** Only reuse if:
- Same Arduino board
- Same environment
- Recent calibration (<1 week)

---

## LED/Hardware Issues

### LED Doesn't Turn On

**Symptoms:**
- LED stays off when should be on
- No light from LED

**Check:**

**1. Polarity:**
```
✓ Anode (+) to Arduino pin (through resistor)
  Cathode (-) to GND
✗ Reversed connection (LED won't light)
```

**2. Resistor:**
- Resistor present? (Required!)
- Correct value? (220Ω typical)
- Calculate: R = (5V - LED_Vf) / LED_If

**3. Wiring:**
- Solid connections?
- Breadboard contact good?
- No loose wires?

**4. LED:**
- Test LED with battery + resistor
- May be burned out
- Try known-good LED

**5. Arduino pin:**
- Try different channel/pin
- Pin may be damaged

---

### LED Always On

**Symptom:**
- LED stays on, doesn't respond to commands
- Can't turn off

**Solutions:**

**1. Check wiring:**
- LED connected to correct pin?
- Not connected to 5V or 3.3V directly?

**2. Check sketch:**
- Re-upload Arduino sketch
- Verify correct channel assignments

**3. Test command:**
```
Open Serial Monitor
Send: CH1_OFF
Check: LED should turn off
```

**4. Pin may be stuck HIGH:**
- Try different pin/channel
- Reset Arduino

---

### LED Dim or Flickering

**Symptom:**
- LED very dim
- Flickers randomly

**Solutions:**

**1. Resistor value too high:**
- Calculate correct resistor
- Try lower value (e.g., 220Ω → 150Ω)
- Don't go below minimum!

**2. Power supply issue:**
- USB cable poor quality
- Try different USB port
- Try powered USB hub
- Use external power supply

**3. Loose connection:**
- Check all wire connections
- Re-seat wires in breadboard
- Solder connections if permanent

**4. LED voltage drop:**
- Some LEDs (white, blue) need >3V
- May not work well on Arduino
- Use transistor + external supply

---

### Pulse Not Visible

**Symptom:**
- LED set to pulse, but looks solid

**Solutions:**

**1. Frequency too high:**
```
> 20 Hz appears continuous to human eye
Try: 0.5-2 Hz for visible pulsing
```

**2. Pulse width too long:**
```
If duty cycle near 100%, looks solid
Try: 10-50% duty cycle
```

**3. Check pulse parameters:**

**Excel:**
```
| CH1_frequency | CH1_pulse_width |
|---------------|-----------------|
| 1.0           | 100             |
```

**Text:**
```txt
PULSE:f1pw100
```

**4. Verify command sent:**
- Check output file
- Should see PULSE commands with correct parameters

---

### Multiple LEDs Not Working

**Symptom:**
- Some LEDs work, others don't
- Inconsistent behavior

**Check:**

**1. Current limit:**
- Each Arduino pin: max 20mA
- Multiple LEDs in parallel exceed limit
- **Solution:** Use transistor/MOSFET per LED

**2. Total Arduino current:**
- Uno: 200mA total
- Due: 130mA total
- **Solution:** External power supply

**3. Shared ground:**
- All LEDs must share GND with Arduino
- Check ground connections

**4. Per-LED resistors:**
- Each LED needs its own resistor
- Even in parallel configuration

---

## Software Errors

### Import Error: No module named 'pandas'

**Symptom:**
```python
ImportError: No module named 'pandas'
```

**Solution:**
```bash
pip install pandas openpyxl pyserial
```

---

### Encoding Error (Text Files)

**Symptom:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte...
```

**Solutions:**

**1. Save file as UTF-8:**
- In text editor: File > Save As
- Encoding: UTF-8 (no BOM)

**2. Check for special characters:**
- Remove non-ASCII characters
- Use plain ASCII for commands
- Comments can have UTF-8

---

### Memory Error (Large Protocols)

**Symptom:**
```
MemoryError: Unable to allocate array
Error: Too many commands for Arduino memory
```

**Solutions:**

**1. Use pattern compression:**
- Automatic in Light Controller
- Reduces repetitive commands

**2. Reduce protocol complexity:**
- Fewer repeats
- Longer time steps
- Fewer state changes

**3. Upgrade Arduino:**
- Uno: ~200-300 commands
- Mega: ~400-600 commands
- Due: ~1000-1500 commands

---

### Command Line Errors

**Symptom:**
```bash
python: can't open file 'lcfunc.py': [Errno 2] No such file or directory
```

**Solutions:**

**1. Check current directory:**
```bash
pwd  # Show current directory
ls   # List files (should see lcfunc.py)
```

**2. Change to correct directory:**
```bash
cd /path/to/light_controller_v2.2
python lcfunc.py
```

**3. Use absolute path:**
```bash
python /path/to/light_controller_v2.2/lcfunc.py
```

---

### Executable Doesn't Run (PyInstaller)

**Symptom:**
- Created .exe doesn't start
- Crashes immediately

**Solutions:**

**1. Run from command line to see errors:**
```bash
# Windows
cmd
cd path\to\exe
light_controller.exe

# macOS
./light_controller
```

**2. Check dependencies:**
```bash
# Recreate with all dependencies
pyinstaller --onefile --add-data "examples:examples" lcfunc.py
```

**3. Antivirus blocking:**
- Some antivirus blocks PyInstaller executables
- Add exception or disable temporarily

**4. Run as administrator (Windows):**
- Right-click > Run as administrator

---

## Getting Help

### Collecting Diagnostic Information

When asking for help, provide:

**1. System info:**
```bash
python --version
pip list | grep -E "pandas|pyserial|openpyxl"
```

**2. Arduino info:**
- Board model (Uno/Due/Mega)
- Arduino IDE version
- COM port

**3. Error messages:**
- Full error message (copy/paste)
- Line number if provided

**4. Protocol file:**
- Sample of Excel/Text protocol
- Number of channels, patterns

**5. What you tried:**
- Steps to reproduce issue
- Solutions already attempted

---

### Resources

**Documentation:**
- [Installation Guide](INSTALLATION.md)
- [Usage Guide](USAGE.md)
- [Arduino Setup](ARDUINO_SETUP.md)
- [Protocol Formats](PROTOCOL_FORMATS.md)

**Examples:**
- `examples/` folder in repository
- Template files for common scenarios

**Community:**
- GitHub Issues: Report bugs
- GitHub Discussions: Ask questions

---

## Still Having Issues?

**Create detailed bug report:**

1. **Title:** Brief description
2. **Environment:**
   - OS (Windows/macOS/Linux)
   - Python version
   - Arduino model
3. **Steps to reproduce:**
   - Exact commands run
   - Files used
4. **Expected vs actual:**
   - What should happen
   - What actually happens
5. **Error messages:**
   - Full text (copy/paste)
6. **Attempted solutions:**
   - What you tried
   - Results

**Submit on GitHub:**
- https://github.com/username/light_controller_v2.2/issues

---

*Last Updated: November 8, 2025*
