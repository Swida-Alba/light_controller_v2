# Pulse Period vs Section Time Behavior

## Overview

This document explains what happens when the **pulse period is longer than the section time** (`TIME_MS`) in a pattern command.

## Key Concept

**Section time controls when the pattern moves to the next element**, regardless of pulse cycle completion.

- **Section Time (`TIME_MS`)**: How long to stay on this pattern element
- **Pulse Period (`T` parameter)**: How long one complete ON/OFF pulse cycle takes
- **Independence**: Pulse timing and section timing run **independently**

## Example Problem

```
PATTERN:1;CH:1;STATUS:1,0;TIME_MS:30000,5000;REPEATS:2;PULSE:T50000pw500,T0pw0
```

**Parameters**:
- Element 1: 30,000ms section time, 50,000ms pulse period, 500ms pulse width
- Element 2: 5,000ms section time, no pulse

**What happens**:

```
Time (ms)    Event                        LED State
---------    -------------------------    ---------
0            Start Element 1              
0            Pulse starts (HIGH)          ON
500          Pulse width expires          OFF
             (Next pulse in 49,500ms...)  
30,000       SECTION TIME EXPIRES         
30,000       → Move to Element 2          OFF
35,000       Element 2 complete           
             Repeat pattern...            
```

**Result**: LED is only ON for 500ms out of 30,000ms! The pulse never completes its 50s cycle.

## Behavior Rules

### Rule 1: Section Time Takes Priority

**Section time (`TIME_MS`) always controls when to move to the next element**, even if a pulse cycle is incomplete.

```arduino
// Arduino execution logic (simplified)
if (currentTime >= nextEventTime[ch]) {
    // Move to next element (section time expired)
    idx++;
    // Pulse state is reset for new element
}
```

### Rule 2: Incomplete Pulse Cycles

If pulse period > section time:
- **Only partial pulse cycles execute**
- **Pulse resets** when moving to next element
- **No "carry-over"** of pulse state to next element

### Rule 3: Pulse Timing Within Section

During a section:
- **First pulse**: Starts immediately (HIGH)
- **Pulse width**: How long to stay HIGH
- **Off time**: `period - pulse_width` (how long to stay LOW)
- **Next pulse**: Starts after `off_time` expires
- **Repeats**: Until section time expires

## Practical Examples

### Example 1: Normal Case (Pulse Period < Section Time)

```
PATTERN:1;CH:1;STATUS:1;TIME_MS:10000;REPEATS:1;PULSE:T2000pw100
```

**Timeline**:
```
Time (ms)    Event                        LED State
---------    -------------------------    ---------
0            Pulse 1 starts               ON
100          Pulse 1 width expires        OFF
2000         Pulse 2 starts               ON
2100         Pulse 2 width expires        OFF
4000         Pulse 3 starts               ON
4100         Pulse 3 width expires        OFF
6000         Pulse 4 starts               ON
6100         Pulse 4 width expires        OFF
8000         Pulse 5 starts               ON
8100         Pulse 5 width expires        OFF
10000        SECTION ENDS (5 full cycles) OFF
```

**Result**: 5 complete pulse cycles within 10s section ✅

### Example 2: Problem Case (Pulse Period > Section Time)

```
PATTERN:1;CH:1;STATUS:1;TIME_MS:10000;REPEATS:1;PULSE:T50000pw500
```

**Timeline**:
```
Time (ms)    Event                        LED State
---------    -------------------------    ---------
0            Pulse 1 starts               ON
500          Pulse 1 width expires        OFF
10000        SECTION ENDS (incomplete!)   OFF
             (Next pulse would be at 50000ms, but section ends at 10000ms)
```

**Result**: Only 1 incomplete pulse cycle (ON 500ms, OFF 9500ms) ⚠️

### Example 3: Edge Case (Pulse Period = Section Time)

```
PATTERN:1;CH:1;STATUS:1;TIME_MS:10000;REPEATS:1;PULSE:T10000pw1000
```

**Timeline**:
```
Time (ms)    Event                        LED State
---------    -------------------------    ---------
0            Pulse 1 starts               ON
1000         Pulse 1 width expires        OFF
10000        SECTION ENDS + Next pulse    OFF/ON (transition)
```

**Result**: Exactly 1 complete pulse cycle ✅

## Best Practices

### ✅ DO: Pulse Period ≤ Section Time

**For predictable pulsing behavior**:
- Ensure `pulse_period ≤ TIME_MS`
- Allows complete pulse cycles within section
- Predictable number of pulses: `TIME_MS / pulse_period`

**Example** (Good):
```
# 10s section, 2s pulse → 5 complete pulses
PATTERN:1;CH:1;STATUS:1;TIME_MS:10000;REPEATS:1;PULSE:T2000pw100
```

### ✅ DO: Multiple Complete Cycles

**Calculate pulses per section**:
```python
section_time_ms = 10000
pulse_period_ms = 2000
complete_cycles = section_time_ms // pulse_period_ms  # = 5
```

### ✅ DO: Match Period to Section for Single Pulse

**For one complete pulse per section**:
```
# Exactly 1 pulse per 5s section
PATTERN:1;CH:1;STATUS:1;TIME_MS:5000;REPEATS:10;PULSE:T5000pw250
```

### ⚠️ AVOID: Pulse Period > Section Time

**This creates incomplete cycles**:
```
# BAD: 50s pulse period, 30s section
PATTERN:1;CH:1;STATUS:1;TIME_MS:30000;REPEATS:2;PULSE:T50000pw500
# Result: Only ON for 500ms, then OFF for 29,500ms (not pulsing!)
```

### ❌ DON'T: Expect Pulse Continuation Across Elements

**Pulse state does NOT carry over**:
```
# Element 1: Pulse cycle interrupted at 30s
PATTERN:1;CH:1;STATUS:1;TIME_MS:30000;REPEATS:1;PULSE:T50000pw500

# Element 2: Pulse resets (does NOT continue from Element 1)
PATTERN:2;CH:1;STATUS:1;TIME_MS:30000;REPEATS:1;PULSE:T50000pw500
```

## Correcting the pulse_protocol.txt Example

### Original (Problematic)

```
# Pattern 1: Very slow pulse (20s period) for 30s, then OFF for 5s, repeat 2x
PATTERN:1;CH:1;STATUS:1,0;TIME_MS:30000,5000;REPEATS:2;PULSE:T50000pw500,T0pw0
```

**Problem**: 50s pulse period > 30s section time → Only 1 incomplete pulse

### Option 1: Multiple Fast Pulses (Recommended)

**Make pulse period < section time for multiple complete cycles**:

```
# Pattern 1: Very slow pulse (5s period) for 30s, then OFF for 5s, repeat 2x
# Element 1: LED ON with slow pulse (0.2 Hz, 6 complete cycles)
# Element 2: LED OFF for rest period
PATTERN:1;CH:1;STATUS:1,0;TIME_MS:30000,5000;REPEATS:2;PULSE:T5000pw500,T0pw0
```

**Result**: 
- 30,000ms / 5,000ms = 6 complete pulse cycles
- Each pulse: ON 500ms, OFF 4,500ms
- Total: 6 pulses during 30s section ✅

### Option 2: Single Complete Pulse

**Make pulse period = section time for exactly 1 pulse**:

```
# Pattern 1: Single slow pulse (30s period) for 30s, then OFF for 5s, repeat 2x
# Element 1: LED ON with single pulse cycle (0.033 Hz, 1 complete cycle)
# Element 2: LED OFF for rest period
PATTERN:1;CH:1;STATUS:1,0;TIME_MS:30000,5000;REPEATS:2;PULSE:T30000pw500,T0pw0
```

**Result**:
- Exactly 1 complete pulse cycle
- Pulse: ON 500ms, OFF 29,500ms
- Total: 1 pulse during 30s section ✅

### Option 3: Longer Section Time

**Extend section time to accommodate pulse period**:

```
# Pattern 1: Very slow pulse (50s period) for 50s, then OFF for 5s, repeat 2x
# Element 1: LED ON with very slow pulse (0.02 Hz, 1 complete cycle)
# Element 2: LED OFF for rest period
PATTERN:1;CH:1;STATUS:1,0;TIME_MS:50000,5000;REPEATS:2;PULSE:T50000pw500,T0pw0
```

**Result**:
- 50,000ms / 50,000ms = 1 complete pulse cycle
- Pulse: ON 500ms, OFF 49,500ms
- Total: 1 pulse during 50s section ✅

## Calculation Formulas

### Complete Pulse Cycles per Section

```python
complete_cycles = TIME_MS // pulse_period

# Example:
TIME_MS = 30000  # 30s
pulse_period = 5000  # 5s
complete_cycles = 30000 // 5000  # = 6
```

### Pulse Frequency (Hz)

```python
frequency_hz = 1000 / pulse_period  # pulse_period in ms

# Example:
pulse_period = 5000  # 5s
frequency_hz = 1000 / 5000  # = 0.2 Hz (5 pulses per second)
```

### Duty Cycle (%)

```python
duty_cycle = (pulse_width / pulse_period) * 100

# Example:
pulse_width = 500  # 0.5s
pulse_period = 5000  # 5s
duty_cycle = (500 / 5000) * 100  # = 10%
```

## Summary

**Critical Rule**: **Pulse period should be ≤ section time** for predictable pulsing behavior.

| Relationship | Behavior | Use Case |
|--------------|----------|----------|
| `pulse_period < TIME_MS` | ✅ Multiple complete pulse cycles | Normal pulsing |
| `pulse_period = TIME_MS` | ✅ Exactly 1 complete pulse cycle | Single pulse per section |
| `pulse_period > TIME_MS` | ⚠️ Incomplete pulse cycle | **Avoid** (unpredictable) |

**When in doubt**:
1. Calculate: `complete_cycles = TIME_MS / pulse_period`
2. Ensure: `complete_cycles >= 1` (at least one full cycle)
3. Test: Verify LED behavior matches expectations

---

**Related Documentation**:
- [Pattern Compression Guide](PATTERN_COMPRESSION_GUIDE.md) - Pattern structure and logic
- [Protocol Guide](PROTOCOL.md) - Command format and parameters
- [Arduino Pattern Safety](ARDUINO_PATTERN_LENGTH_FIX.md) - Pattern length handling

**Last Updated**: November 8, 2025  
**Version**: v2.2.0
