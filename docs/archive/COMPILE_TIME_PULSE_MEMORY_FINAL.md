# Compile-Time Pulse Memory Configuration - Final Simplified Version

## Overview

This document describes the **simplified compile-time only** pulse memory configuration system for the Arduino light controller. This replaces the previous dynamic detection system with a straightforward manual configuration approach.

## Key Concept

**The pulse arrays are either compiled into the firmware OR excluded completely at compile time.**

- No runtime detection
- No dynamic memory allocation
- User manually sets `PULSE_MODE_COMPILE` flag before compiling
- Memory savings: ~2.5KB when pulse mode disabled

## How It Works

### Arduino Firmware Configuration

Edit `light_controller_v2_2_arduino.ino`:

```cpp
//* ===== PULSE MODE CONFIGURATION =====
//* Set to 1 to enable pulse parameters (period, pulse_width)
//* Set to 0 to disable pulse parameters and save ~2.5KB memory
//* 
//* Change this BEFORE compiling and uploading firmware
#define PULSE_MODE_COMPILE 1  // 0=Disable pulses, 1=Enable pulses

#if PULSE_MODE_COMPILE == 1
    const bool PULSE_MODE_ENABLED = true;
#else
    const bool PULSE_MODE_ENABLED = false;
#endif
```

**Two Options:**
- **`PULSE_MODE_COMPILE = 0`**: Pulse arrays NOT compiled → Saves ~2.5KB memory
- **`PULSE_MODE_COMPILE = 1`**: Pulse arrays compiled → Full pulse support

### Struct Definition

```cpp
struct CompressedPattern {
    byte status[MAX_PATTERN_NUM][PATTERN_LENGTH];
    unsigned long time_ms[MAX_PATTERN_NUM][PATTERN_LENGTH];
    
#if PULSE_MODE_COMPILE == 1
    //* Pulse parameters - only compiled if pulse mode enabled
    unsigned long period[MAX_PATTERN_NUM][PATTERN_LENGTH];
    unsigned long pulse_width[MAX_PATTERN_NUM][PATTERN_LENGTH];
#endif
    
    int repeats[MAX_PATTERN_NUM];
    int pattern_length[MAX_PATTERN_NUM];
    int pattern_num;
};
```

**Result:**
- If `PULSE_MODE_COMPILE = 0`: `period[]` and `pulse_width[]` arrays **do not exist**
- If `PULSE_MODE_COMPILE = 1`: Arrays **are compiled in**

## Memory Savings Calculation

For Arduino Due with 8 channels, 10 patterns, pattern_length=4:

```
Pulse arrays size = 2 arrays × 4 bytes × 8 channels × 10 patterns × 4 steps
                  = 2 × 4 × 8 × 10 × 4
                  = 2,560 bytes (~2.5KB)
```

## Python Integration

### Memory Reporting

Python can query Arduino memory:

```python
from lcfunc import GetArduinoMemory

mem_info = GetArduinoMemory(ser)
print(f"Free RAM: {mem_info['free']} bytes")
print(f"Pulse mode: {'ENABLED' if mem_info['pulse_mode'] == 1 else 'DISABLED'}")
```

### Compatibility Checking

Python automatically checks if protocol requirements match Arduino configuration:

```python
from lcfunc import CheckPulseModeCompatibility, NormalizeSynonyms

# Detect if protocol uses pulse parameters
df_normalized = NormalizeSynonyms(protocol_df)
pulse_col_indicators = ['_period', '_pulse_width', '_frequency', '_duty_cycle']
protocol_requires_pulse = any(indicator in col for col in df_normalized.columns 
                              for indicator in pulse_col_indicators)

# Check compatibility
is_compatible = CheckPulseModeCompatibility(ser, protocol_requires_pulse)
```

### Error Handling

If protocol requires pulses but Arduino has `PULSE_MODE_COMPILE = 0`:

```
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
```

## Usage Workflow

### For Protocols WITHOUT Pulse Modulation

1. Edit Arduino firmware: Set `PULSE_MODE_COMPILE = 0`
2. Compile and upload firmware to Arduino
3. Run Python script with protocol
4. Python detects no pulse parameters → Compatible
5. **Benefit:** ~2.5KB more free RAM

### For Protocols WITH Pulse Modulation

1. Edit Arduino firmware: Set `PULSE_MODE_COMPILE = 1`
2. Compile and upload firmware to Arduino
3. Run Python script with protocol
4. Python detects pulse parameters → Compatible
5. **Benefit:** Full pulse support

### If Mismatch Occurs

Python will show error message with clear instructions:
- If protocol needs pulses: Recompile with `PULSE_MODE_COMPILE = 1`
- If protocol doesn't need pulses: Can optionally recompile with `PULSE_MODE_COMPILE = 0` to save memory

## Implementation Files

### Arduino Firmware
- **File:** `light_controller_v2_2_arduino/light_controller_v2_2_arduino.ino`
- **Key sections:**
  - Lines 7-14: `PULSE_MODE_COMPILE` definition
  - Lines 32-38: Conditional compilation of pulse arrays in struct
  - Lines 145-147: Hello response reports pulse mode
  - Lines 173-175: `GET_MEMORY` command handler
  - Lines 649-709: Memory reporting functions

### Python Code
- **File:** `lcfunc.py`
  - `GetArduinoMemory()`: Query Arduino memory and pulse mode (~line 1031)
  - `CheckPulseModeCompatibility()`: Verify protocol/Arduino compatibility (~line 1057)
  
- **File:** `light_controller_parser.py`
  - `setup_serial()`: Automatic pulse detection and compatibility checking (~line 147)

## Advantages of Simplified System

### ✅ What We Gained

1. **True Memory Savings**: Arrays actually not compiled when disabled
2. **Simplicity**: No complex dynamic detection system
3. **Clarity**: User explicitly sets compile flag before uploading
4. **No Runtime Overhead**: Everything determined at compile time
5. **Memory Reporting**: Arduino can still report free/used RAM
6. **Compatibility Checking**: Python warns about mismatches

### ❌ What We Removed

1. **Dynamic Detection**: No automatic runtime mode switching
2. **SET_PULSE_MODE Command**: No runtime configuration changes
3. **DetectPulseMode() Function**: Python no longer sends mode to Arduino
4. **SendPulseMode() Function**: No longer needed
5. **Complex 3-Mode System**: Simplified from (Never/Always/Dynamic) to (Disable/Enable)

## Why This Approach?

### The Problem with Dynamic Allocation

Arduino's static memory model means:
- Struct members are allocated at **compile time**
- Runtime flags can't change struct memory layout
- Even with `if (flag)` checks, memory is still reserved

### The Solution: Compile-Time Configuration

Using `#if PULSE_MODE_COMPILE` preprocessor directive:
- Arrays **physically excluded** from compiled binary when disabled
- True memory savings achieved
- Simple to understand and configure
- No complexity of runtime detection

## Migration from Old System

If you have code using the old dynamic system:

### Old Code (REMOVE):
```python
from lcfunc import DetectPulseMode, SendPulseMode

pulse_mode = DetectPulseMode(protocol_df)
SendPulseMode(ser, pulse_mode)
```

### New Code (USE):
```python
from lcfunc import CheckPulseModeCompatibility, NormalizeSynonyms

# Inline detection
df_normalized = NormalizeSynonyms(protocol_df)
pulse_col_indicators = ['_period', '_pulse_width', '_frequency', '_duty_cycle']
protocol_requires_pulse = any(indicator in col for col in df_normalized.columns 
                              for indicator in pulse_col_indicators)

# Check compatibility
is_compatible = CheckPulseModeCompatibility(ser, protocol_requires_pulse)
```

Or simply use `LightControllerParser` which handles this automatically:

```python
from light_controller_parser import LightControllerParser

parser = LightControllerParser(protocol_file='protocol.xlsx')
parser.setup_serial(board_type='Arduino', baudrate=9600)  # Auto-checks compatibility
parser.parse_and_execute()
parser.close()
```

## Testing

### Test Memory Reporting
```python
from lcfunc import GetArduinoMemory

mem_info = GetArduinoMemory(ser)
if mem_info:
    print(f"Total RAM: {mem_info['total']} bytes")
    print(f"Free RAM: {mem_info['free']} bytes")
    print(f"Used RAM: {mem_info['used']} bytes")
    print(f"Pulse mode: {mem_info['pulse_mode']}")
```

### Test Compatibility Checking
```python
# With protocol requiring pulses
is_compatible = CheckPulseModeCompatibility(ser, protocol_requires_pulse=True)

# With protocol not requiring pulses
is_compatible = CheckPulseModeCompatibility(ser, protocol_requires_pulse=False)
```

### Compare Memory Usage

1. Compile with `PULSE_MODE_COMPILE = 0`, upload, run `GET_MEMORY`
2. Compile with `PULSE_MODE_COMPILE = 1`, upload, run `GET_MEMORY`
3. Compare free RAM → Should see ~2.5KB difference

## Summary

**The system is now:**
- ✅ Simple: Two compile-time options (0 or 1)
- ✅ Clear: User manually configures before compiling
- ✅ Efficient: True memory savings when disabled
- ✅ Safe: Python checks compatibility and warns about mismatches
- ✅ Informative: Memory reporting shows actual RAM usage

**User workflow:**
1. Look at protocol → Uses pulses?
2. Set `PULSE_MODE_COMPILE` accordingly (0=No pulses, 1=Has pulses)
3. Compile and upload Arduino firmware
4. Run Python script → Automatic compatibility check
5. If mismatch → Clear error message with solution

This approach aligns with Arduino's compile-time memory model and provides the best balance of simplicity, efficiency, and safety.
