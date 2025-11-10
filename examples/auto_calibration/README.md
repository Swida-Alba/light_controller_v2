# Automatic Calibration Examples

This folder contains protocol examples using the **new automatic calibration system** without manual `CALIBRATION_FACTOR` specification.

## ✨ Modern Approach - Recommended

These examples demonstrate the **new automatic calibration management** where the system handles calibration factors automatically based on Arduino board identification.

### Key Features

✅ **Automatic Board Identification:**
- Unique ID generated from serial number or VID:PID
- Works even when Arduino is plugged into different USB ports
- Supports both genuine Arduino boards and clones (CH340, CP210x, FTDI)

✅ **Persistent Calibration Database:**
- One-time calibration per Arduino board
- Stored in `calibration_database.json`
- Automatic retrieval on subsequent runs
- No manual tracking needed
- **Calibrations expire after 90 days (3 months)**

✅ **Simplified Workflow:**
- No `CALIBRATION_FACTOR` line in protocol files
- First run: prompted to calibrate (takes ~5 minutes)
- Future runs: automatic - no prompts!
- Seamless multi-board support
- Auto-recalibration every 3 months for accuracy

## How It Works

### First Time Setup (Per Arduino)

1. **Connect Arduino to computer**
2. **Run your protocol:**
   ```bash
   python protocol_parser.py 4 /dev/cu.usbmodem14301 auto_calibration/simple_blink_example.txt
   ```

3. **System identifies your board:**
   ```
   Identifying Arduino board...
   Board ID: 0852420f343bb48d
   Serial Number: 85937313737351D021D0
   VID:PID: 0x2341:0x003d
   Identification Method: Serial Number (★★★★★ Highest reliability)
   ```

4. **Prompted to calibrate (first time only):**
   ```
   Arduino 0852420f343bb48d not found in calibration database.
   Calibrate now? (Y/n): y
   Select calibration method:
     1. v1 (original, 300s)
     2. v1.1 (active wait, 300s)
     3. v2 (multi-timestamp, 300s)
     4. v2_improved (recommended, 300s)
   Choice (default: 4): 
   ```

5. **Calibration saved automatically:**
   ```
   Calibration completed: 1.025847
   Saved to database for future use.
   ```

### Subsequent Runs (Automatic)

```bash
python protocol_parser.py 4 /dev/cu.usbmodem14301 auto_calibration/simple_blink_example.txt
```

Output:
```
Identifying Arduino board...
Board ID: 0852420f343bb48d
Found calibration in database: 1.025847
Age: 15 days (0.5 months) - Valid ✓
Using automatic calibration for timing accuracy.
```

**No prompts! Just works.** ✨

### After 3 Months (Expired Calibration)

When calibration is >90 days old, automatic recalibration is triggered:

```bash
python protocol_parser.py 4 /dev/cu.usbmodem14301 auto_calibration/simple_blink_example.txt
```

Output:
```
Identifying Arduino board...
Board ID: 0852420f343bb48d

======================================================================
⚠️  CALIBRATION EXPIRED - Recalibration Required
======================================================================
Old calibration factor: 1.025847
Calibration date: 2025-08-10 14:30:00
Age: 92 days (3.0 months)

WHY RECALIBRATE?
  • Crystal oscillators drift over time (±1-5 ppm/year)
  • Temperature effects accumulate
  • Component aging affects timing accuracy
  • Recommended: Recalibrate every 3 months for precision

Calibration expired. A new calibration is required.
======================================================================

[Automatic recalibration proceeds...]

✓ New calibration: 1.025912
✓ Saved to database
```

**Why 3 months?** Crystal oscillators drift ~0.25-1.25 ppm over 3 months, which can accumulate to 1-4 seconds of error over 12-hour protocols. Regular recalibration ensures <1 second timing accuracy.

## Examples in This Folder

| File | Format | Description | Pattern Length | Highlights |
|------|--------|-------------|----------------|------------|
| `simple_blink_example.txt` | TXT | Basic ON/OFF patterns | 2 | Best for learning auto-calibration |
| `simple_blink_example.xlsx` | Excel | Same as TXT version | 2 | Excel format with info sheet |
| `pulse_protocol.txt` | TXT | Pulsed patterns with varying frequencies | 4 | Demonstrates pulse timing accuracy |
| `pulse_protocol.xlsx` | Excel | Same as TXT version | 4 | 4-channel pulse examples |
| `multi_channel_pattern.txt` | TXT | Complex multi-channel coordination | 4 | Shows auto-cal with 4-element patterns |
| `multi_channel_pattern.xlsx` | Excel | Same as TXT version | 4 | Includes board-specific calibration explanation |

### TXT vs Excel Formats

Both formats support automatic calibration:

**TXT Format:**
- No `CALIBRATION_FACTOR:` line = auto-calibration enabled
- Lightweight, easy to edit
- Good for version control

**Excel Format:**
- No `calibration` sheet = auto-calibration enabled
- Includes `info` sheet explaining automatic calibration
- Visual structure, easier for non-programmers
- Better for time-series data entry

### What's Different from Preset Examples?

**Preset Calibration (Old - TXT):**
```
CALIBRATION_FACTOR: 1.000000
```

**Preset Calibration (Old - Excel):**
- Has `calibration` sheet with manual factor

**Automatic Calibration (New - TXT):**
```
# NOTE: NO CALIBRATION_FACTOR NEEDED
# Calibration retrieved automatically from database
```

**Automatic Calibration (New - Excel):**
- NO `calibration` sheet included
- System detects absence and enables auto-calibration

That's it! The protocol files are **cleaner** and **easier to manage**.

## Database Management

### View Stored Calibrations

```bash
python utils/manage_calibrations.py list
```

Output shows calibration age and expiration status:
```
======================================================================
Stored Calibrations (2 boards)
======================================================================

1. Board ID: 0852420f343bb48d
   Port: /dev/cu.usbmodem14301
   Description: Arduino Due
   Serial Number: 85937313737351D021D0
   Calibration factor: 1.025847
   Method: v2_improved
   Last calibrated: 2025-08-15 14:32:10
   Age: 87 days (2.9 months) - ✓ Valid

2. Board ID: a1b2c3d4e5f6g7h8
   Port: /dev/cu.usbmodem14401
   Description: Arduino Uno
   Serial Number: 75937313737351A0B1C1
   Calibration factor: 0.998234
   Method: v2
   Last calibrated: 2025-07-01 10:15:00
   Age: 132 days (4.3 months) - ⚠️  EXPIRED (recalibration needed)

======================================================================
Summary: 1 valid, 1 expired (>90 days)

⚠️  1 board(s) need recalibration!
Crystal oscillators drift over time. Recalibrate every 3 months
for optimal timing accuracy.
======================================================================
```

The list command shows:
- **Age in days and months** for each calibration
- **Status**: ✓ Valid (<90 days) or ⚠️ EXPIRED (>90 days)
- **Summary** of valid vs expired calibrations
- **Warning** if any boards need recalibration

### Test Board Identification

```bash
python test_board_info.py
```

Shows your Arduino's unique ID, identification method, and reliability rating.

### Recalibrate an Arduino

Force recalibration even if already in database:

```bash
python protocol_parser.py 4 /dev/cu.usbmodem14301 protocol.txt --calibrate
```

Or use the management utility:

```bash
# Delete existing calibration (will prompt on next run)
python utils/manage_calibrations.py delete 0852420f343bb48d
```

## Multi-Board Support

The automatic system shines when working with multiple Arduino boards:

### Scenario: Two Arduino Boards

**Board 1:**
- Serial: 85937313737351D021D0
- Unique ID: 0852420f343bb48d
- Calibration: 1.025847

**Board 2:**
- Serial: 75937313737351A0B1C1
- Unique ID: a1b2c3d4e5f6g7h8
- Calibration: 0.998234

**Usage:**
```bash
# First time with Board 1
python protocol_parser.py 4 /dev/cu.usbmodem14301 protocol.txt
# → Prompted to calibrate Board 1 → 1.025847 saved

# First time with Board 2  
python protocol_parser.py 4 /dev/cu.usbmodem14401 protocol.txt
# → Prompted to calibrate Board 2 → 0.998234 saved

# Future runs - automatic!
python protocol_parser.py 4 /dev/cu.usbmodem14301 protocol.txt
# → Uses 1.025847 (Board 1 detected)

python protocol_parser.py 4 /dev/cu.usbmodem14401 protocol.txt
# → Uses 0.998234 (Board 2 detected)
```

**No manual tracking needed!** The system identifies which board is connected and uses the correct calibration.

## Board Identification Reliability

The system uses multiple methods to identify your Arduino, prioritized by reliability:

| Method | Reliability | Works For |
|--------|-------------|-----------|
| Serial Number | ★★★★★ (Highest) | Genuine Arduino boards |
| VID:PID + Location | ★★★★☆ (High) | Consistent USB port usage |
| VID:PID + Port Name | ★★★☆☆ (Medium) | Most scenarios |
| VID:PID Only | ★★☆☆☆ (Low) | Clone boards, last resort |

**Best Practice:** Use genuine Arduino boards for most reliable identification across USB port changes.

## Platform Support

Automatic calibration works on all platforms:

- **macOS:** `/dev/cu.usbmodem*`, `/dev/cu.usbserial*`
- **Linux:** `/dev/ttyACM*`, `/dev/ttyUSB*`
- **Windows:** `COM3`, `COM4`, etc. (case-insensitive)

Port names are normalized for consistency across platforms.

## Troubleshooting

### "Board not found in database" every time

**Cause:** Inconsistent board identification (clone boards with no serial number)

**Solutions:**
1. Use genuine Arduino board (recommended)
2. Always use same USB port (improves VID:PID+Location reliability)
3. Manually specify calibration in protocol file if needed (backward compatible)

### Database file location

Default: `calibration_database.json` in project root

To use custom location:
```python
from lcfunc import load_calibration_database

db = load_calibration_database('/custom/path/calibration_database.json')
```

### Reset all calibrations

```bash
# Backup first (optional)
python utils/manage_calibrations.py export calibrations_backup.txt

# Delete database file
rm calibration_database.json

# All boards will prompt for calibration on next run
```

## Migration from Preset Calibration

Have existing protocols with `CALIBRATION_FACTOR`? Easy to migrate:

### Step 1: Remove CALIBRATION_FACTOR line

**Before (preset_calibration/):**
```
PATTERN:1;CH:1;STATUS:1,0;TIME_MS:1000,1000;REPEATS:10;PULSE:T0pw0,T0pw0
CALIBRATION_FACTOR: 1.000000
```

**After (auto_calibration/):**
```
PATTERN:1;CH:1;STATUS:1,0;TIME_MS:1000,1000;REPEATS:10;PULSE:T0pw0,T0pw0
# Note: Using automatic calibration - no CALIBRATION_FACTOR needed
```

### Step 2: Run and calibrate

```bash
python protocol_parser.py 4 /dev/cu.usbmodem14301 protocol.txt
# Follow calibration prompts (one time)
```

### Step 3: Done!

Future runs are automatic. No more manual factor management!

## Related Documentation

- **Complete Auto-Calibration Guide:** [../../docs/AUTO_CALIBRATION_DATABASE.md](../../docs/AUTO_CALIBRATION_DATABASE.md)
- **Backward Compatibility:** [../../docs/BACKWARD_COMPATIBILITY.md](../../docs/BACKWARD_COMPATIBILITY.md)
- **Legacy Preset Approach:** [../preset_calibration/README.md](../preset_calibration/README.md)
- **Protocol Format Reference:** [../QUICK_REFERENCE.md](../QUICK_REFERENCE.md)

## Quick Reference

### Common Commands

**TXT Protocols:**
```bash
# Run protocol with auto-calibration
python protocol_parser.py 2 <port> auto_calibration/simple_blink_example.txt
python protocol_parser.py 4 <port> auto_calibration/pulse_protocol.txt
python protocol_parser.py 4 <port> auto_calibration/multi_channel_pattern.txt
```

**Excel Protocols:**
```bash
# Run Excel protocol with auto-calibration
python protocol_parser.py 2 <port> auto_calibration/simple_blink_example.xlsx
python protocol_parser.py 4 <port> auto_calibration/pulse_protocol.xlsx
python protocol_parser.py 4 <port> auto_calibration/multi_channel_pattern.xlsx
```

**Management Commands:**
```bash
# Force recalibration
python protocol_parser.py 4 <port> protocol.txt --calibrate

# View all calibrations
python utils/manage_calibrations.py list

# Test board identification
python test_board_info.py

# Export calibrations
python utils/manage_calibrations.py export backup.txt

# Delete specific calibration
python utils/manage_calibrations.py delete <board_id>
```

## Support

For questions or issues:
1. Check [../../docs/AUTO_CALIBRATION_DATABASE.md](../../docs/AUTO_CALIBRATION_DATABASE.md) for detailed documentation
2. Run `python test_board_info.py` to verify board identification
3. See [../../docs/BACKWARD_COMPATIBILITY.md](../../docs/BACKWARD_COMPATIBILITY.md) for compatibility scenarios

---

**Tip:** Start with `simple_blink_example.txt` to learn the automatic calibration workflow!
