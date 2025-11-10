# Pulse Mode Compatibility Testing Guide

## Overview

This guide explains how to test the compile-time pulse mode configuration system to ensure proper compatibility between Arduino firmware and protocol files.

## Test Scenarios

### Scenario 1: No-Pulse Protocol + Pulse Disabled (OPTIMAL)
- **Arduino:** `PULSE_MODE_COMPILE = 0`
- **Protocol:** No pulse columns
- **Expected Result:** ✅ PASS - Perfect match, memory optimized

### Scenario 2: No-Pulse Protocol + Pulse Enabled (COMPATIBLE)
- **Arduino:** `PULSE_MODE_COMPILE = 1`
- **Protocol:** No pulse columns
- **Expected Result:** ⚠️ PASS with Warning - Works but wastes ~2.5KB memory

### Scenario 3: Pulse Protocol + Pulse Disabled (INCOMPATIBLE)
- **Arduino:** `PULSE_MODE_COMPILE = 0`
- **Protocol:** Has pulse columns (period, pulse_width, frequency, duty_cycle)
- **Expected Result:** ❌ FAIL - Protocol requires pulses but Arduino doesn't support them

### Scenario 4: Pulse Protocol + Pulse Enabled (OPTIMAL)
- **Arduino:** `PULSE_MODE_COMPILE = 1`
- **Protocol:** Has pulse columns
- **Expected Result:** ✅ PASS - Perfect match, full pulse support

## Test Files

### Example Protocols

1. **`examples/example_no_pulse_protocol.txt`**
   - Simple LED on/off patterns
   - No pulse modulation
   - Tests basic compatibility

2. **`examples/example_protocol.txt`**
   - Includes pulse parameters
   - Tests pulse mode requirements

### Test Scripts

1. **`test_pulse_compatibility.py`**
   - Automated compatibility testing
   - Interactive mode with user prompts
   - Validates all scenarios

## Running Tests

### Interactive Mode (Recommended for First Time)

```bash
python test_pulse_compatibility.py --port /dev/cu.usbmodem14101
```

The script will:
1. Ask for your Arduino's `PULSE_MODE_COMPILE` setting (0 or 1)
2. Run tests for non-pulse protocol
3. Run tests for pulse protocol
4. Display compatibility results and warnings

### Automated Mode

```bash
python test_pulse_compatibility.py --port /dev/cu.usbmodem14101 --auto
```

Runs both tests automatically without prompts.

### Manual Testing

You can also test manually:

```python
from light_controller_parser import LightControllerParser

# Test with no-pulse protocol
parser = LightControllerParser(protocol_file='examples/example_no_pulse_protocol.txt')
parser.setup_serial(board_type='Arduino', com_port='/dev/cu.usbmodem14101')
parser.parse_and_execute()
parser.close()
```

## Expected Output Examples

### Scenario 1: No-Pulse + Pulse Disabled (OPTIMAL)

```
💾 Checking Arduino memory and pulse mode compatibility...
   Arduino Memory:
     Total:  96.0 KB
     Used:   85.5 KB (89.1%)
     Free:   10.5 KB

🔍 Pulse mode detection:
   Protocol uses pulse parameters: NO

🔍 Pulse Mode Compatibility Check:
   Protocol requires pulses: NO
   Arduino pulse mode:       DISABLED (compile-time)
   ✓ Compatible
```

### Scenario 2: No-Pulse + Pulse Enabled (WARNING)

```
💾 Checking Arduino memory and pulse mode compatibility...
   Arduino Memory:
     Total:  96.0 KB
     Used:   88.0 KB (91.7%)
     Free:   8.0 KB

🔍 Pulse mode detection:
   Protocol uses pulse parameters: NO

🔍 Pulse Mode Compatibility Check:
   Protocol requires pulses: NO
   Arduino pulse mode:       ENABLED (compile-time)
   ✓ Compatible (Arduino pulse enabled but not needed)
   💡 Note: Protocol does NOT use pulse modulation
      Arduino has pulse mode ENABLED (~2.5KB memory used)
      Consider setting PULSE_MODE_COMPILE = 0 to save memory
```

### Scenario 3: Pulse Protocol + Pulse Disabled (ERROR)

```
💾 Checking Arduino memory and pulse mode compatibility...
   Arduino Memory:
     Total:  96.0 KB
     Used:   85.5 KB (89.1%)
     Free:   10.5 KB

🔍 Pulse mode detection:
   Protocol uses pulse parameters: YES

🔍 Pulse Mode Compatibility Check:
   Protocol requires pulses: YES
   Arduino pulse mode:       DISABLED (compile-time)

======================================================================
❌ ERROR: Pulse Mode Incompatibility!
======================================================================
  Protocol REQUIRES pulse modulation
  But Arduino pulse mode is DISABLED

  Arduino firmware was compiled with PULSE_MODE_COMPILE = 0
  Pulse support is DISABLED at compile time.

  ⚠️  Solution: Recompile Arduino firmware with PULSE_MODE_COMPILE = 1
     Edit light_controller_v2_2_arduino.ino, change:
     #define PULSE_MODE_COMPILE 0  →  #define PULSE_MODE_COMPILE 1
     Then recompile and upload to Arduino.
======================================================================

ValueError: Pulse mode incompatibility: Protocol requires pulses but Arduino pulse mode is disabled.
```

### Scenario 4: Pulse Protocol + Pulse Enabled (OPTIMAL)

```
💾 Checking Arduino memory and pulse mode compatibility...
   Arduino Memory:
     Total:  96.0 KB
     Used:   88.0 KB (91.7%)
     Free:   8.0 KB

🔍 Pulse mode detection:
   Protocol uses pulse parameters: YES

🔍 Pulse Mode Compatibility Check:
   Protocol requires pulses: YES
   Arduino pulse mode:       ENABLED (compile-time)
   ✓ Compatible
```

## Step-by-Step Testing Procedure

### Test 1: Verify Pulse Disabled Mode

1. **Prepare Arduino:**
   ```cpp
   // In light_controller_v2_2_arduino.ino
   #define PULSE_MODE_COMPILE 0  // Disable pulse mode
   ```
   Compile and upload to Arduino.

2. **Test with no-pulse protocol:**
   ```bash
   python test_pulse_compatibility.py --port YOUR_PORT
   # Select 0 when asked for PULSE_MODE_COMPILE
   ```
   Expected: ✅ Test 1 PASS, ✅ Test 2 EXPECTED FAIL

3. **Verify memory savings:**
   - Note the free memory reported
   - Should have ~2.5KB more than pulse-enabled mode

### Test 2: Verify Pulse Enabled Mode

1. **Prepare Arduino:**
   ```cpp
   // In light_controller_v2_2_arduino.ino
   #define PULSE_MODE_COMPILE 1  // Enable pulse mode
   ```
   Compile and upload to Arduino.

2. **Test with both protocols:**
   ```bash
   python test_pulse_compatibility.py --port YOUR_PORT
   # Select 1 when asked for PULSE_MODE_COMPILE
   ```
   Expected: ✅ Test 1 PASS (with warning), ✅ Test 2 PASS

3. **Verify warning message:**
   - Should see warning about unused pulse memory
   - Should suggest setting PULSE_MODE_COMPILE = 0

### Test 3: Compare Memory Usage

1. **With Pulse Disabled (PULSE_MODE_COMPILE=0):**
   ```bash
   python -c "
   import serial
   from lcfunc import GetArduinoMemory
   ser = serial.Serial('YOUR_PORT', 9600, timeout=5)
   mem = GetArduinoMemory(ser)
   print(f'Free RAM: {mem[\"free\"]} bytes')
   ser.close()
   "
   ```

2. **With Pulse Enabled (PULSE_MODE_COMPILE=1):**
   ```bash
   # Recompile with PULSE_MODE_COMPILE=1, upload, then run same command
   ```

3. **Calculate difference:**
   - Difference should be approximately 2,560 bytes (~2.5KB)

## Troubleshooting

### Test Fails Unexpectedly

**Problem:** Test passes when it should fail, or vice versa.

**Solution:**
1. Verify Arduino firmware was actually updated (check upload confirmation)
2. Reset Arduino after uploading
3. Check serial port is correct
4. Verify protocol file has correct columns

### Warning Not Shown

**Problem:** No warning when using pulse-enabled with no-pulse protocol.

**Solution:**
1. Check that `CheckPulseModeCompatibility()` is being called
2. Verify `GetArduinoMemory()` returns valid data
3. Check Python code is up to date

### Memory Difference Not 2.5KB

**Problem:** Memory difference between modes is not ~2,560 bytes.

**Solution:**
1. Verify both tests use same protocol (same number of patterns)
2. Check MAX_PATTERN_NUM, MAX_CHANNEL_NUM, PATTERN_LENGTH values
3. Calculate expected size: `2 × 4 bytes × channels × patterns × length`

## Integration with CI/CD

You can integrate these tests into automated testing:

```bash
# Test script for CI/CD
#!/bin/bash

# Test with pulse disabled
python test_pulse_compatibility.py --port $ARDUINO_PORT --auto > test_results_disabled.log

# Flash firmware with pulse enabled (using arduino-cli or similar)
# arduino-cli compile --upload ...

# Test with pulse enabled
python test_pulse_compatibility.py --port $ARDUINO_PORT --auto > test_results_enabled.log

# Compare results
grep "TEST PASSED" test_results_*.log
```

## Summary

The test suite verifies:
- ✅ Non-pulse protocols work with both pulse modes
- ✅ Warnings shown when pulse enabled but not needed
- ✅ Errors raised when pulse required but disabled
- ✅ Memory reporting shows correct pulse mode status
- ✅ Memory savings achieved with PULSE_MODE_COMPILE=0

All tests should pass to ensure the compile-time pulse configuration system works correctly.
