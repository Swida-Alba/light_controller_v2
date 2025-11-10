# Automatic Calibration Management

**Feature added**: November 10, 2025  
**Version**: Light Controller v2.2+

## Overview

The automatic calibration management system eliminates the need for manual calibration factor input by automatically storing and retrieving calibration data for each Arduino board.

### Key Features

✅ **Automatic Arduino identification** - Each board gets a unique ID  
✅ **Database storage** - Calibrations saved to `calibration_database.json`  
✅ **Auto-retrieval** - Stored calibrations automatically loaded  
✅ **3-month expiration** - Automatic recalibration every 90 days  
✅ **No manual input** - Never type calibration factors again  
✅ **Multi-board support** - Different calibrations for different boards  
✅ **Database management** - View, export, and delete calibrations

### Why 3-Month Expiration?

Calibrations expire after **90 days (3 months)** to maintain timing accuracy:

**Crystal Oscillator Aging:**
- Crystals drift ±1-5 ppm per year
- Over 3 months: ~0.25-1.25 ppm drift
- Accumulated error can reach 1-4 seconds over 12 hours

**Temperature Effects:**
- Room temperature variations cause frequency drift
- Operating temperature (Arduino self-heating) adds variation
- Effects accumulate over time

**Component Aging:**
- Load capacitance changes with component aging
- Long-term protocols require fresh calibration
- Ensures <1 second error over extended runs

**Automatic Handling:**
- System automatically checks calibration age
- If >90 days: prompts for recalibration
- Shows: "⚠️ CALIBRATION EXPIRED - Recalibration Required"
- New calibration updates timestamp in database

---

## How It Works

### 1. Arduino Identification

The system creates a unique ID for each Arduino using:
- **Serial number** (if available) - Most reliable
- **VID:PID + Port** (if no serial number) - For clone boards
- **Port + Description** (fallback) - For basic identification

### 2. Automatic Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Connect Arduino                                          │
│    ↓                                                        │
│ 2. Get unique ID from board                                │
│    ↓                                                        │
│ 3. Check calibration_database.json                         │
│    ├─ Not found → Perform new calibration                  │
│    │              ↓                                         │
│    │              Save to database with timestamp           │
│    │                                                        │
│    ├─ Found but EXPIRED (>90 days)                         │
│    │   ↓                                                    │
│    │   Show expiration warning                             │
│    │   ↓                                                    │
│    │   Perform new calibration                             │
│    │   ↓                                                    │
│    │   Update database with new timestamp                  │
│    │                                                        │
│    └─ Found and VALID (<90 days) → Use stored calibration ✓│
└─────────────────────────────────────────────────────────────┘
```

### 3. Database Structure

The calibration database (`calibration_database.json`) stores:

```json
{
  "a1b2c3d4e5f6g7h8": {
    "calib_factor": 1.000131,
    "offset": 0.123,
    "r_squared": 0.999998,
    "method": "v2",
    "timestamp": "2025-11-10 14:30:00",
    "board_info": {
      "port": "/dev/cu.usbmodem14101",
      "description": "Arduino Due",
      "manufacturer": "Arduino LLC",
      "serial_number": "95439313538351F01192"
    }
  }
}
```

---

## Usage

### Basic Usage (Automatic)

```python
from light_controller_parser import LightControllerParser

# Create parser with calibration method preference
parser = LightControllerParser('protocol.xlsx', calibration_method='v2')

# Calibrate - automatically uses stored calibration if exists
calib_factor = parser.calibrate()

# If no stored calibration:
#   1. System will detect this is first time for this Arduino
#   2. Runs new calibration (300 seconds)
#   3. Saves to database automatically
#
# If stored calibration exists:
#   1. System shows stored calibration info
#   2. Asks: "Use existing calibration? (Y/n/recalibrate)"
#   3. Uses stored value if confirmed

# Execute protocol with calibrated timing
parser.execute()
```

### Force Recalibration

```python
# Force new calibration even if one exists
calib_factor = parser.calibrate(force_recalibrate=True)
```

### Different Calibration Methods

```python
# V1 method (300s total, 4 measurements)
parser = LightControllerParser('protocol.xlsx', calibration_method='v1')
parser.calibrate()

# V1.1 method (300s total, 4 measurements, active polling)
parser = LightControllerParser('protocol.xlsx', calibration_method='v1.1')
parser.calibrate()

# V2 method (300s, 10 samples)
parser = LightControllerParser('protocol.xlsx', calibration_method='v2')
parser.calibrate()

# V2 improved method (300s, 9 samples, excludes t=0)
parser = LightControllerParser('protocol.xlsx', calibration_method='v2_improved')
parser.calibrate()
```

---

## Database Management

### Using the Management Utility

```bash
# List all stored calibrations
python utils/manage_calibrations.py list

# Test Arduino connection and show ID
python utils/manage_calibrations.py test

# Export database to text file
python utils/manage_calibrations.py export

# Delete a calibration
python utils/manage_calibrations.py delete
```

### Programmatic Management

```python
from lcfunc import (
    list_all_calibrations,
    delete_calibration,
    get_arduino_unique_id,
    load_calibration_database,
    save_calibration_database
)

# List all calibrations
list_all_calibrations()

# Get Arduino ID from serial connection
unique_id, board_info = get_arduino_unique_id(ser)
print(f"Board ID: {unique_id}")
print(f"Port: {board_info['port']}")

# Load database
db = load_calibration_database()
print(f"Total boards: {len(db)}")

# Delete specific calibration
delete_calibration(board_id='a1b2c3d4e5f6g7h8')
```

---

## Example Session

### First Time Calibration

```
$ python protocol_parser.py

Searching for Arduino...
✓ Arduino Due found on /dev/cu.usbmodem14101

======================================================================
Arduino Calibration Manager
======================================================================
Method: V2
Mode: Auto (use stored if available)
======================================================================

======================================================================
No existing calibration found for this Arduino
======================================================================
Board ID: a1b2c3d4e5f6g7h8
Port: /dev/cu.usbmodem14101
Description: Arduino Due
Serial Number: 95439313538351F01192

A new calibration will be performed.
======================================================================

======================================================================
Performing Calibration (Method: V2)
======================================================================

Calibrating Arduino time (v2 - multi-timestamp method)...
Duration: 300s with 10 samples

Collecting 11 timestamps...
  Sample 1/11: Arduino=0ms, Python=0.000s
  Sample 4/11: Arduino=90000ms, Python=90.123s
  ...

======================================================================
Calibration Results (v2):
======================================================================
Calibration factor: 1.000131
Time offset: 0.123 seconds
R-squared: 0.999998
RMSE: 12.34 ms
Max error: 45.67 ms
Timing stable: ✓ Yes
Correction per 12 hours: 5.65 seconds
======================================================================

✓ Calibration database saved to: calibration_database.json

======================================================================
✓ Calibration saved for this Arduino
======================================================================
Board ID: a1b2c3d4e5f6g7h8
Calibration factor: 1.000131
This calibration will be automatically used next time.
======================================================================

✓ Calibration factor: 1.000131
  Correction: 5.65 seconds per 12 hours.
```

### Next Time (Automatic)

```
$ python protocol_parser.py

Searching for Arduino...
✓ Arduino Due found on /dev/cu.usbmodem14101

======================================================================
✓ Found existing calibration for this Arduino
======================================================================
Board ID: a1b2c3d4e5f6g7h8
Port: /dev/cu.usbmodem14101
Description: Arduino Due
Serial Number: 95439313538351F01192

Calibration factor: 1.000131
Last calibrated: 2025-11-10 14:30:00
Age: 15 days (0.5 months) - Valid ✓
Method: v2
R-squared: 0.999998
======================================================================

Use existing calibration? (Y/n/recalibrate): Y

✓ Using stored calibration factor: 1.000131

✓ Calibration factor: 1.000131
  Correction: 5.65 seconds per 12 hours.
```

### After 3 Months (Expired - Auto Recalibration)

```
$ python protocol_parser.py

Searching for Arduino...
✓ Arduino Due found on /dev/cu.usbmodem14101

======================================================================
⚠️  CALIBRATION EXPIRED - Recalibration Required
======================================================================
Board ID: a1b2c3d4e5f6g7h8
Port: /dev/cu.usbmodem14101
Description: Arduino Due
Serial Number: 95439313538351F01192

Old calibration factor: 1.000131
Calibration date: 2025-11-10 14:30:00
Age: 95 days (3.1 months)

WHY RECALIBRATE?
  • Crystal oscillators drift over time (±1-5 ppm/year)
  • Temperature effects accumulate
  • Component aging affects timing accuracy
  • Recommended: Recalibrate every 3 months for precision

Calibration expired. A new calibration is required.
======================================================================

======================================================================
Performing Calibration (Method: V2)
======================================================================

Calibrating Arduino time (v2 - multi-timestamp method)...
[... calibration process ...]

======================================================================
✓ Calibration saved for this Arduino
======================================================================
Board ID: a1b2c3d4e5f6g7h8
Calibration factor: 1.000145
This calibration will be automatically used next time.
======================================================================

Note: New calibration factor (1.000145) differs from old (1.000131)
This 0.014% change demonstrates crystal aging over 3 months.
```

---

## Multiple Arduinos

The system automatically handles multiple Arduino boards:

```python
# Arduino #1 (Due)
parser1 = LightControllerParser('protocol1.xlsx')
parser1.calibrate()  # Uses calibration for Arduino Due

# Disconnect, then connect Arduino #2 (Uno)

# Arduino #2 (Uno)
parser2 = LightControllerParser('protocol2.xlsx')
parser2.calibrate()  # Uses different calibration for Arduino Uno
```

Each board maintains its own calibration in the database.

---

## Database Location

Default: `calibration_database.json` in the project root directory

You can specify a different location:

```python
from lcfunc import auto_calibrate_arduino

# Custom database path
calib_factor, result = auto_calibrate_arduino(
    ser, 
    method='v2',
    db_path='/path/to/my_calibrations.json'
)
```

---

## Migration from Manual Calibration

### Old Way (Manual)

```python
# Had to manually note and input calibration factor
CALIBRATION_FACTOR: 1.000131

# Or in code:
calib_factor = 1.000131  # From previous calibration
parser.calib_factor = calib_factor
```

### New Way (Automatic)

```python
# Just call calibrate() - system handles everything
parser.calibrate()

# First time: Runs calibration and saves
# Next time: Uses saved calibration automatically
```

### Backward Compatibility

The system is fully backward compatible:

```python
# Still works if you have CALIBRATION_FACTOR in TXT protocol
# System will use it if present

# Still works if you manually set calib_factor
parser.calib_factor = 1.000131
parser.execute()  # Will use manual factor
```

---

## Benefits

### For Users
- ✅ No more manual calibration factor management
- ✅ No more typing long decimal numbers
- ✅ Automatic board recognition
- ✅ Always uses correct calibration for each board
- ✅ One-time calibration per board

### For Multi-Board Setups
- ✅ Each board has its own calibration
- ✅ No confusion between boards
- ✅ Automatic selection when switching boards
- ✅ Easy to manage multiple setups

### For Shared Computers
- ✅ Calibrations persist across sessions
- ✅ Multiple users can benefit from same calibrations
- ✅ Easy to export/import database

---

## Troubleshooting

### Database Not Found

If `calibration_database.json` doesn't exist, it's created automatically on first calibration.

### Calibration Not Recognized

**Possible causes:**
1. Arduino moved to different USB port
2. Using clone board without serial number
3. Database file missing

**Solution:**
```python
# Force recalibration
parser.calibrate(force_recalibrate=True)
```

### Multiple Boards Show Same ID

For clone boards without serial numbers, the ID is based on port location. If you:
- Move the board to a different port, it gets a new ID
- Use multiple identical clone boards on same port, they share calibration

**Workaround**: Keep clone boards on consistent ports

### Database Corruption

```bash
# Backup database first
cp calibration_database.json calibration_database.backup.json

# View contents
python utils/manage_calibrations.py export

# If corrupted, delete and recalibrate
rm calibration_database.json
python protocol_parser.py  # Will create new database
```

---

## API Reference

### Main Functions

#### `auto_calibrate_arduino(ser, method='v2', force_recalibrate=False, db_path='calibration_database.json')`

Automatically manage Arduino calibration.

**Parameters:**
- `ser`: Serial connection object
- `method`: Calibration method ('v1', 'v1.1', 'v2', 'v2_improved')
- `force_recalibrate`: Force new calibration (default: False)
- `db_path`: Database file path

**Returns:**
- `calib_factor` (float): Calibration factor
- `result` (dict): Full calibration results

#### `get_arduino_unique_id(ser)`

Get unique identifier for Arduino board.

**Returns:**
- `unique_id` (str): 16-character hash
- `board_info` (dict): Board information

#### `load_calibration_database(db_path='calibration_database.json')`

Load calibration database.

**Returns:**
- `dict`: Database contents

#### `save_calibration_database(db, db_path='calibration_database.json')`

Save calibration database.

#### `list_all_calibrations(db_path='calibration_database.json')`

Print all stored calibrations.

#### `delete_calibration(board_id=None, db_path='calibration_database.json')`

Delete a calibration from database.

---

## Related Documentation

- **[Calibration Guide](CALIBRATION_GUIDE.md)** - Detailed calibration methods
- **[Calibration Integration](CALIBRATION_INTEGRATION_SUMMARY.md)** - V1 vs V1.1 vs V2
- **[Calibration Quick Reference](CALIBRATION_QUICK_REFERENCE.md)** - Quick method comparison

---

## Technical Details

### Unique ID Generation

The system uses a priority-based approach to create unique identifiers:

**Priority 1: Serial Number (Best)** ★★★★★
```python
unique_id = hash(serial_number)
```
- Most reliable method
- Consistent across different USB ports
- Consistent across different computers
- Available on genuine Arduino boards

**Priority 2: VID:PID + Location (Good)** ★★★★☆
```python
unique_id = hash(f"{vid}:{pid}:{location}")
```
- Good for clone boards without serial numbers
- Consistent across reboots
- Uses USB hub location (e.g., "0-1.1")

**Priority 3: VID:PID + Port (OK)** ★★★☆☆
```python
unique_id = hash(f"{vid}:{pid}:{port}")
```
- For boards without serial number or location
- Changes if USB port changes
- Port normalized: COM3 = COM3 (Windows), /dev/cu.* (macOS), /dev/tty* (Linux)

**Priority 4: Port + Description (Fallback)** ★★☆☆☆
```python
unique_id = hash(f"{port}:{description}")
```
- Least reliable
- Changes with port
- Used only when other methods fail

**Platform-Specific Handling:**
- **Windows 10/11**: COM port names normalized to uppercase (COM3, COM10)
- **macOS**: Uses /dev/cu.* ports for consistency
- **Linux**: Handles /dev/ttyUSB*, /dev/ttyACM* ports

MD5 hash is used to create consistent 16-character IDs.

### Cross-Platform Compatibility

✅ **Windows 10/11**
- COM port detection and handling
- Case-insensitive port matching (COM3 = com3)
- Normalized uppercase for consistency
- Works with all Arduino USB chipsets (FTDI, CH340, CP210x)

✅ **macOS**
- /dev/cu.* and /dev/tty.* port handling
- Native USB and USB-to-Serial adapters
- Apple Silicon (M1/M2) and Intel Macs

✅ **Linux**
- /dev/ttyUSB* (USB-to-Serial) support
- /dev/ttyACM* (CDC/ACM devices) support
- Major distributions (Ubuntu, Debian, Fedora, etc.)

### Database Schema

```json
{
  "<board_id>": {
    "calib_factor": float,      // Required
    "offset": float,             // Time offset in seconds
    "r_squared": float,          // Goodness of fit
    "method": string,            // v1, v1.1, v2, v2_improved
    "timestamp": string,         // ISO format
    "board_info": {
      "port": string,
      "description": string,
      "manufacturer": string,
      "serial_number": string or null
    }
  }
}
```

---

## Changelog

### November 10, 2025
- ✅ Initial implementation
- ✅ Automatic board identification
- ✅ JSON database storage
- ✅ Integration with all calibration methods (V1, V1.1, V2, V2_improved)
- ✅ Management utility (`manage_calibrations.py`)
- ✅ Full backward compatibility
- ✅ Updated default calibration duration to 300s for all methods
