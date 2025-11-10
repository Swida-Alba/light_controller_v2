# Backward Compatibility Guide

**Last Updated**: November 10, 2025  
**Version**: Light Controller v2.2+

## Overview

The automatic calibration database system is **fully backward compatible** with existing workflows and protocol files. This document explains how the system handles different scenarios.

---

## Calibration Factor Handling Priority

The system uses a **three-tier priority** for calibration factors:

### Priority 1: Protocol File (Highest)
If `CALIBRATION_FACTOR` is specified in protocol file → **Use it directly**

### Priority 2: Automatic Calibration
If connected to Arduino and no factor in file → **Auto-calibrate with database**

### Priority 3: Default (Fallback)
If no connection and no factor in file → **Use 1.0 (uncalibrated)**

---

## Scenario Breakdown

### Scenario 1: Protocol with CALIBRATION_FACTOR

**TXT Protocol:**
```txt
CALIBRATION_FACTOR: 1.000131

PATTERN:1;CH:1;STATUS:0,1;TIME_MS:1000,1000;REPEATS:10
START_TIME: {'CH1': '21:00'}
```

**Excel Protocol:**
- Has `calibration` sheet with factor value

**Behavior:**
```python
parser = LightControllerParser('protocol.txt')
parser.execute()
```

✅ **Result:**
- Uses `1.000131` from protocol file
- **No automatic calibration**
- **No database check**
- Directly applies the specified factor to timing

**Console Output:**
```
Reading TXT protocol file...
Calibration Factor: 1.000131
Time Correction: 5.65 sec per 12 hours
✓ Using calibration factor from protocol file
```

---

### Scenario 2: Protocol WITHOUT CALIBRATION_FACTOR (Serial Connected)

**TXT Protocol:**
```txt
PATTERN:1;CH:1;STATUS:0,1;TIME_MS:1000,1000;REPEATS:10
START_TIME: {'CH1': '21:00'}
```

**Behavior:**
```python
parser = LightControllerParser('protocol.txt')
parser.execute()  # Serial connection active
```

✅ **Result:**
- Checks calibration database for this Arduino
- If found → Asks to use stored calibration
- If not found → Runs new calibration (300s)
- Saves new calibration to database

**Console Output (First Time):**
```
======================================================================
No existing calibration found for this Arduino
======================================================================
Board ID: 0852420f343bb48d
Port: /dev/cu.usbmodem1101
Description: Arduino Due

A new calibration will be performed.
======================================================================

[Calibration runs for 300s...]

✓ Calibration saved for this Arduino
Calibration factor: 1.000131
This calibration will be automatically used next time.
```

**Console Output (Next Time):**
```
======================================================================
✓ Found existing calibration for this Arduino
======================================================================
Board ID: 0852420f343bb48d
Calibration factor: 1.000131
Last calibrated: 2025-11-10 14:30:00
======================================================================

Use existing calibration? (Y/n/recalibrate): Y

✓ Using stored calibration factor: 1.000131
```

---

### Scenario 3: Protocol WITHOUT CALIBRATION_FACTOR (No Serial)

**Behavior:**
```python
parser = LightControllerParser('protocol.txt')
parser.execute()  # No serial connection
```

⚠️ **Result:**
- Cannot calibrate (no Arduino connection)
- Uses default factor: `1.0`
- Shows warning about uncalibrated time

**Console Output:**
```
Reading TXT protocol file...

======================================================================
⚠️  WARNING: Calibration factor is 1.000000
======================================================================
This indicates UNCALIBRATED time.
The protocol will use Arduino's internal timer without correction.

For accurate timing:
  1. Run a calibration protocol first
  2. Note the calibration factor (typically 1.0 ± 0.01)
  3. Update CALIBRATION_FACTOR in your protocol file

To calibrate: Use the calibrate() method with serial connection
======================================================================

Calibration Factor: 1.00000
Time Correction: 0.00 sec per 12 hours
```

---

### Scenario 4: Manual Calibration Override

**Old Way (Still Works):**
```python
parser = LightControllerParser('protocol.txt')
parser.calib_factor = 1.000131  # Manual override
parser.execute()
```

✅ **Result:**
- Uses manually set factor `1.000131`
- Skips automatic calibration
- Does not check database

---

### Scenario 5: Force Recalibration

**Force new calibration even if stored:**
```python
parser = LightControllerParser('protocol.txt')
parser.calibrate(force_recalibrate=True)
parser.execute()
```

✅ **Result:**
- Ignores stored calibration
- Runs new calibration (300s)
- Overwrites database entry with new value

---

## Code Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ parser.execute()                                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Parse Protocol File                                         │
│ - ReadTxtFile() or ReadExcelFile()                          │
│ - Extracts CALIBRATION_FACTOR if present                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Is CALIBRATION_FACTOR in protocol file?                    │
└─────────────────────────────────────────────────────────────┘
          ↓ YES                              ↓ NO
┌──────────────────────┐        ┌──────────────────────────────┐
│ Use protocol factor  │        │ Is serial connection active? │
│ ✓ Skip calibration   │        └──────────────────────────────┘
│ ✓ Skip database      │                ↓ YES         ↓ NO
└──────────────────────┘        ┌─────────────┐  ┌──────────┐
                                │ calibrate() │  │ Use 1.0  │
                                └─────────────┘  │ ⚠️ Warn  │
                                       ↓         └──────────┘
                        ┌──────────────────────────┐
                        │ Check database for board │
                        └──────────────────────────┘
                                ↓ Found    ↓ Not Found
                        ┌──────────┐  ┌──────────────┐
                        │ Use      │  │ Run new      │
                        │ stored   │  │ calibration  │
                        └──────────┘  │ Save to DB   │
                                      └──────────────┘
```

---

## Implementation Details

### In `ReadTxtFile()` (lcfunc.py)

```python
elif line.startswith('CALIBRATION_FACTOR:'):
    line_no_space = line.replace(' ', '')
    calib_str = line_no_space.split('CALIBRATION_FACTOR:', 1)[1].strip()
    if calib_str:
        try:
            calib_factor = float(calib_str)
        except ValueError:
            print(f"Warning: Invalid CALIBRATION_FACTOR. Will calibrate automatically.")
            calib_factor = None
    else:
        calib_factor = None
```

**Returns:** `calib_factor` (float or None)

### In `parse_txt_protocol()` (light_controller_parser.py)

```python
# Read from protocol file
self.calib_factor = ReadTxtFile(self.protocol_file)[4]

# If factor is 1.0, show warning
if self.calib_factor is not None and abs(self.calib_factor - 1.0) < 1e-9:
    print('⚠️  WARNING: Calibration factor is 1.000000')
    # ... show calibration instructions
```

### In `generate_pattern_commands()` (light_controller_parser.py)

```python
# Calibrate if serial connection is active and no factor from file
if self.ser:
    self.calibrate()  # Only runs if self.calib_factor is None

# Apply calibration (uses factor from file OR calibration)
self.cmd_patterns = ApplyCalibrationToTxtCommands(commands, self.calib_factor)
```

### In `calibrate()` (light_controller_parser.py)

```python
def calibrate(self, ...):
    if self.calib_factor is None:  # Only calibrate if not already set
        # Use automatic calibration with database
        self.calib_factor, result = auto_calibrate_arduino(self.ser, ...)
    return self.calib_factor
```

---

## Backward Compatibility Features

### ✅ Protocol Files Unchanged

**Old protocol files work as-is:**
- TXT files with `CALIBRATION_FACTOR:` → Use specified value
- TXT files without → Auto-calibrate
- Excel files with `calibration` sheet → Use specified value
- Excel files without → Auto-calibrate

### ✅ Manual Factor Setting

**Old code patterns still work:**
```python
# Method 1: Set before parsing
parser = LightControllerParser('protocol.txt')
parser.calib_factor = 1.000131
parser.execute()

# Method 2: Set in protocol file
# CALIBRATION_FACTOR: 1.000131
```

### ✅ No Breaking Changes

**Existing workflows unchanged:**
- `parser.execute()` works exactly as before
- `parser.calibrate()` works exactly as before
- All return values and interfaces preserved

### ✅ Opt-In Automatic System

**Automatic calibration is opt-in:**
- Only activates when:
  1. No `CALIBRATION_FACTOR` in protocol file
  2. Serial connection active
  3. `calibrate()` not manually called with factor

---

## Migration Examples

### Example 1: Keep Using Protocol Files

**Before (v2.1):**
```txt
CALIBRATION_FACTOR: 1.000131
PATTERN:1;CH:1;STATUS:0,1;TIME_MS:1000,1000;REPEATS:10
```

**After (v2.2+):**
```txt
CALIBRATION_FACTOR: 1.000131  # ← Still works!
PATTERN:1;CH:1;STATUS:0,1;TIME_MS:1000,1000;REPEATS:10
```

✅ **No changes needed**

### Example 2: Switch to Automatic

**Before (v2.1):**
```txt
CALIBRATION_FACTOR: 1.000131  # ← Manually noted and typed
PATTERN:1;CH:1;STATUS:0,1;TIME_MS:1000,1000;REPEATS:10
```

**After (v2.2+):**
```txt
# CALIBRATION_FACTOR: 1.000131  ← Comment out or delete
PATTERN:1;CH:1;STATUS:0,1;TIME_MS:1000,1000;REPEATS:10
```

✅ **System automatically uses database**

### Example 3: Mixed Approach

**Use automatic for most, manual for specific protocols:**

```python
# Protocol 1: Use automatic (database)
parser1 = LightControllerParser('protocol1.txt')  # No CALIBRATION_FACTOR
parser1.execute()  # Uses database

# Protocol 2: Use specific factor
parser2 = LightControllerParser('protocol2.txt')  # Has CALIBRATION_FACTOR: 1.000200
parser2.execute()  # Uses 1.000200 from file

# Protocol 3: Manual override
parser3 = LightControllerParser('protocol3.txt')
parser3.calib_factor = 1.000150  # Override
parser3.execute()  # Uses 1.000150
```

---

## Frequently Asked Questions

### Q: Will my old protocol files stop working?

**A:** No! All existing protocol files work exactly as before. If they have `CALIBRATION_FACTOR`, it's used. If not, the system auto-calibrates (or warns if no serial connection).

### Q: Do I need to delete CALIBRATION_FACTOR from my files?

**A:** No, you can keep it. The system respects protocol file values as the highest priority.

### Q: Can I mix manual and automatic calibration?

**A:** Yes! Use `CALIBRATION_FACTOR` in protocols where you want specific values, and omit it where you want automatic calibration.

### Q: What if I move my Arduino to a different USB port?

**A:** 
- **Genuine Arduino** (with serial number): Database still recognizes it ✓
- **Clone Arduino** (without serial number): May be seen as new board, needs recalibration

### Q: Can I disable the automatic calibration?

**A:** Yes, in three ways:
1. Always include `CALIBRATION_FACTOR` in protocol files
2. Manually set `parser.calib_factor = 1.0` before execute
3. Run without serial connection (uses 1.0 as default)

### Q: What happens if I have different calibrations for same board?

**A:** Database stores one calibration per board. If you want different factors:
- Use `CALIBRATION_FACTOR` in protocol file (overrides database)
- Or use `force_recalibrate=True` to update database

### Q: Does this work with preview mode?

**A:** Yes! Preview mode (`parser.preview()`) uses calibration factor from:
1. Protocol file (if specified)
2. Database (if connected and no file value)
3. 1.0 default (if no connection)

---

## Compatibility Matrix

| Scenario | Protocol Has Factor | Serial Connected | Behavior |
|----------|-------------------|------------------|----------|
| 1 | ✓ Yes | ✓ Yes | Use protocol factor, skip calibration |
| 2 | ✓ Yes | ✗ No | Use protocol factor, skip calibration |
| 3 | ✗ No | ✓ Yes | Auto-calibrate with database |
| 4 | ✗ No | ✗ No | Use 1.0, show warning |
| 5 | ✓ Yes + Manual Set | Any | Use manual set value |
| 6 | ✗ No + Manual Set | Any | Use manual set value |

---

## Summary

**The automatic calibration system is fully backward compatible:**

✅ Old protocol files work unchanged  
✅ Old code patterns work unchanged  
✅ Manual calibration still supported  
✅ No breaking changes to API  
✅ Opt-in automatic features  
✅ Database is transparent to existing workflows  

**Users can:**
- Keep using old workflows (nothing breaks)
- Gradually adopt automatic calibration
- Mix manual and automatic approaches
- Override automatic behavior anytime

The system enhances functionality without removing any existing features! 🎉
