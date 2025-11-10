# Arduino Pattern Length Safety Fix

## Overview

This document explains the safety fix implemented in the Arduino firmware to handle patterns whose actual pattern length is **less than** the `PATTERN_LENGTH` constant defined in the firmware.

## The Problem

### Original Behavior (UNSAFE)

Previously, the Arduino firmware had a hardcoded assumption:
- **Arduino Constant**: `const int PATTERN_LENGTH = 2;`
- **Pattern Execution**: Always iterated through exactly 2 elements
- **Issue**: If Python sent `pattern_length=1` (e.g., `STATUS:1;TIME_MS:5000`):
  ```
  Parsing: status[0] = 1, status[1] = 0 (uninitialized)
  Execution: Cycles through BOTH elements → unexpected behavior
  ```

### Example of Problem

**Python sends** (pattern_length=1):
```
PATTERN:1;CH:1;STATUS:1;TIME_MS:5000;REPEATS:10;PULSE:
```

**Arduino (PATTERN_LENGTH=2) previously would**:
1. Parse: `status[0] = 1`, `time_ms[0] = 5000`
2. **Bug**: `status[1]` and `time_ms[1]` remain at default values (0)
3. Execute: Cycles through index 0 → index 1 (unintended!)
4. Result: LED turns ON for 5000ms, then OFF for 0ms (instant) → 10 times

**Expected behavior**: LED should stay ON for 5000ms continuously, repeating 10 times.

## The Solution

### Structural Changes

1. **Added `pattern_length` field to `CompressedPattern` struct**:
   ```cpp
   struct CompressedPattern {
       byte status[MAX_PATTERN_NUM][PATTERN_LENGTH];
       unsigned long time_ms[MAX_PATTERN_NUM][PATTERN_LENGTH];
       // ... other fields ...
       int pattern_length[MAX_PATTERN_NUM];  // NEW: Actual length per pattern
       int pattern_num;
   };
   ```

2. **Enhanced parsing functions to track actual length**:
   ```cpp
   void parseByteArray(String data, byte arr[], int &actualLength);
   void parseULongArray(String data, unsigned long arr[], int &actualLength);
   ```
   - Both functions now return the actual number of elements parsed via reference parameter
   - Stops at comma boundaries OR `PATTERN_LENGTH` (whichever comes first)

3. **Validation during pattern parsing**:
   ```cpp
   // Parse STATUS and TIME_MS, track actual lengths
   parseByteArray(statusStr, p.status[patternNum], statusLength);
   parseULongArray(timeStr, p.time_ms[patternNum], timeLength);
   
   // Validate lengths match
   if (statusLength != timeLength) {
       Serial.println("Error: STATUS and TIME_MS length mismatch");
       p.pattern_length[patternNum] = min(statusLength, timeLength);
   } else {
       p.pattern_length[patternNum] = statusLength;
   }
   
   // Validate doesn't exceed PATTERN_LENGTH
   if (p.pattern_length[patternNum] > PATTERN_LENGTH) {
       Serial.println("Warning: Pattern length exceeds PATTERN_LENGTH. Truncated.");
       p.pattern_length[patternNum] = PATTERN_LENGTH;
   }
   ```

4. **Use actual pattern length in execution**:
   ```cpp
   void executePatterns() {
       // ...
       int actualPatternLength = p.pattern_length[seq];  // Use actual length
       
       if (idx >= actualPatternLength) {  // NOT: if (idx >= PATTERN_LENGTH)
           idx = 0;
           repeatCounters[ch][seq]++;
           // ...
       }
   }
   ```

### How It Works Now

**Python sends** (pattern_length=1):
```
PATTERN:1;CH:1;STATUS:1;TIME_MS:5000;REPEATS:10;PULSE:
```

**Arduino (PATTERN_LENGTH=2) now does**:
1. Parse: `status[0] = 1`, `time_ms[0] = 5000`
2. **Track**: `pattern_length[1] = 1` (actual length)
3. Execute: Cycles through **only index 0** (respects actual length)
4. Result: LED stays ON for 5000ms → repeat 10 times ✅

## Compatibility Matrix

| Python `pattern_length` | Arduino `PATTERN_LENGTH` | Behavior |
|------------------------|-------------------------|----------|
| 1 | 2 | ✅ Works safely (uses 1 element) |
| 2 | 2 | ✅ Optimal (perfect match) |
| 3 | 2 | ⚠️ Python verification fails (prevented) |
| 2 | 4 | ✅ Works safely (uses 2 elements) |
| 4 | 4 | ✅ Optimal (perfect match) |

## Error Detection

The Arduino firmware now reports the following errors:

### 1. **STATUS/TIME_MS Length Mismatch**
```
Error: STATUS and TIME_MS length mismatch in pattern 1 for channel 1 (STATUS=2, TIME_MS=3)
```
**Cause**: Malformed command with different array lengths  
**Action**: Uses minimum length to prevent crashes

### 2. **Pattern Length Exceeds PATTERN_LENGTH**
```
Warning: Pattern length (4) exceeds PATTERN_LENGTH (2). Truncated.
```
**Cause**: Python sent more elements than Arduino can handle  
**Action**: Truncates to `PATTERN_LENGTH` (should be caught by Python verification)

### 3. **Invalid PULSE Format**
```
Error: Invalid PULSE format 'T1000' in command. Expected format: T[period]pw[width] (e.g., T1000pw50)
```
**Cause**: Malformed pulse parameter  
**Action**: Defaults to no pulsing (0)

## Testing Recommendations

### Test Case 1: pattern_length=1 on PATTERN_LENGTH=2 Arduino
```python
# Python code
from light_controller_parser import LightControllerParser

parser = LightControllerParser("test.txt", pattern_length=1)
parser.setup_serial("/dev/cu.usbmodem21101", verify_pattern_length=False)
# Send: PATTERN:1;CH:1;STATUS:1;TIME_MS:5000;REPEATS:1;PULSE:
```

**Expected**: LED stays ON for 5000ms once  
**Previous**: LED would flicker (ON 5000ms, OFF 0ms)

### Test Case 2: pattern_length=2 with Different Patterns
```python
# Test alternating pattern (ON/OFF)
parser = LightControllerParser("test.txt", pattern_length=2)
# Send: PATTERN:1;CH:1;STATUS:1,0;TIME_MS:1000,2000;REPEATS:5;PULSE:,
```

**Expected**: LED ON 1000ms, OFF 2000ms, repeat 5 times  
**Result**: Works correctly (full pattern cycle)

### Test Case 3: Verification Prevents Mismatch
```python
# Try to send pattern_length=4 to PATTERN_LENGTH=2 Arduino
parser = LightControllerParser("test.txt", pattern_length=4)
parser.setup_serial("/dev/cu.usbmodem21101", verify_pattern_length=True)
```

**Expected**: Raises `ValueError` before sending any commands  
**Message**: "Pattern length mismatch: Arduino PATTERN_LENGTH=2, but pattern_length=4"

## Implementation Details

### Files Changed

1. **`light_controller_v2_2_arduino.ino`**:
   - Line 7: Added `pattern_length[MAX_PATTERN_NUM]` to struct
   - Line 57: Initialize `pattern_length` to 0
   - Lines 143-169: Enhanced validation during parsing
   - Lines 323-403: Use actual pattern length in execution
   - Lines 423-449: Modified parsing functions to return actual length

### Backward Compatibility

✅ **Fully backward compatible** with existing Python code:
- Old Python code sending `pattern_length=2` commands works unchanged
- New verification is **optional** (`verify_pattern_length=False` to disable)
- Old Arduino behavior preserved for matching pattern lengths

### Memory Impact

**Memory increase**: ~40 bytes
- `pattern_length[MAX_PATTERN_NUM]`: 10 patterns × 4 bytes/int = 40 bytes per channel
- Total for 8 channels: 320 bytes

**Arduino Due**: 96 KB SRAM → 0.3% increase ✅ Negligible

## Key Benefits

1. ✅ **Safety**: No undefined behavior when pattern_length < PATTERN_LENGTH
2. ✅ **Flexibility**: Supports variable pattern lengths per command
3. ✅ **Error Detection**: Reports mismatches and malformed commands
4. ✅ **Validation**: Length consistency checks prevent crashes
5. ✅ **Backward Compatible**: Existing protocols work unchanged

## Summary

The Arduino firmware now **safely handles patterns with any length ≤ PATTERN_LENGTH** by:
1. Tracking the actual pattern length from parsed commands
2. Using the actual length (not the constant) during pattern execution
3. Validating STATUS/TIME_MS array lengths match
4. Reporting errors for malformed commands

Combined with Python-side verification (see [PATTERN_LENGTH_VERIFICATION.md](PATTERN_LENGTH_VERIFICATION.md)), this provides a robust safety system for pattern compression.

---

**Related Documentation**:
- [Pattern Compression Guide](PATTERN_COMPRESSION_GUIDE.md) - Understanding pattern logic
- [Pattern Length Verification](PATTERN_LENGTH_VERIFICATION.md) - Python-Arduino verification
- [Implementation Guide](PATTERN_LENGTH_IMPLEMENTATION.md) - Technical implementation details
