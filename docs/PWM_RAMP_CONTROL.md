# PWM and Ramp Intensity Control

## Overview

Light Controller v2.3 introduces **PWM intensity control**, **gradient/ramp transitions**, and **DAC output support** for smooth light intensity modulation. This enables:

- **Continuous intensity**: Values from 0% (OFF) to 100% (full brightness)
- **Smooth transitions**: Gradual ramps between intensity levels
- **Easing functions**: Linear, cosine, ease-in, ease-out for natural motion
- **Multi-segment ramps**: Combine multiple transitions in one pattern
- **Memory efficient**: Single RAMP command replaces hundreds of individual steps
- **Interactive visualization**: See easing curves in Jupyter notebook
- **DAC support**: True analog output via native DAC or MCP4728 I2C DAC (v2.3+)

> 📖 **Related Documentation**:
> - [Protocol Syntax Reference](PROTOCOL_SYNTAX_REFERENCE.md) - Detailed punctuation & format rules
> - [F Mode Custom Functions](F_MODE_CUSTOM_FUNCTIONS.md) - Custom function implementation
> - [Easing Curves Notebook](easing_curves_visualization.ipynb) - Interactive visualization
> - [Arduino Setup](ARDUINO_SETUP.md) - MCP4728 DAC wiring and installation

---

## Output Types

### PWM vs DAC Output

Light Controller v2.3 supports three output modes:

| Output Type    | Pin Range | Resolution      | Signal Type | Use Case                |
| -------------- | --------- | --------------- | ----------- | ----------------------- |
| **PWM**        | 0-99      | 8-bit (0-255)   | Pulsed      | LEDs, most applications |
| **Native DAC** | 100-101   | 12-bit (0-4095) | True analog | Due, Zero, R4 boards    |
| **MCP4728**    | 201-204   | 12-bit (0-4095) | True analog | I2C DAC module          |

### Normalized Values (0.0 - 1.0)

All protocols use **normalized values** (0.0 to 1.0) for portability:

| Protocol Value | Meaning     | PWM (8-bit) | DAC (12-bit) |
| -------------- | ----------- | ----------- | ------------ |
| `0.0`          | OFF (0%)    | 0           | 0            |
| `0.5`          | Half (50%)  | 127         | 2047         |
| `1.0`          | Full (100%) | 255         | 4095         |

The conversion to actual hardware values happens automatically:
- Python converts 0.0-1.0 → 0-255 (byte)
- Arduino scales to 0-4095 for 12-bit DAC outputs

---

## PWM Status Values

### Protocol Input (0.0 - 1.0 Float)

In protocol files, specify intensity as a **decimal between 0.0 and 1.0**:

| Value  | Meaning                  | Arduino PWM |
| ------ | ------------------------ | ----------- |
| `0.0`  | OFF (0%)                 | 0           |
| `0.5`  | Half brightness (50%)    | 127         |
| `1.0`  | Full brightness (100%)   | 255         |
| `0.25` | Quarter brightness (25%) | 63          |

### Automatic Conversion

The Python parser automatically converts:
- **0.0 - 1.0** (float) → **0 - 255** (Arduino PWM byte)
- **Legacy 0/1** (integer) → **0 or 255** (backward compatible)

---

## Protocol Format

### Basic PWM Status (Excel)

| Sections | CH1_status | CH1_time_sec |
| -------- | ---------- | ------------ |
| 0        | 0.0        | 5            |
| 1        | 0.5        | 10           |
| 2        | 1.0        | 10           |
| 3        | 0.0        | 5            |

### Basic PWM Status (TXT)

```txt
PATTERN:1;CH:1;STATUS:0,127,255,0;TIME_MS:5000,10000,10000,5000;REPEATS:1
```

Note: In TXT format, STATUS values can be 0-255 directly (already converted).

---

## RAMP Command (Gradient Transitions)

### The Problem with Traditional Approach

A gradient from 0% to 100% over 10 seconds with 100 steps would require:
- 100 status values
- 100 time values
- Exceeds `PATTERN_LENGTH` limit
- Excessive serial communication

### RAMP Solution

A single **RAMP specification** lets Arduino execute smooth transitions on-the-fly.

---

## Command Format (v2.2.3+)

### New Format (Recommended)

```txt
RAMP:(MODE:start,end,duration[|t_start,t_end]),(MODE:...);
```

**Parameters for L/C/I/O Modes:**
| Parameter  | Description                      | PWM Example | DAC Example |
| ---------- | -------------------------------- | ----------- | ----------- |
| `MODE`     | Easing mode (L/C/I/O)            | I           | I           |
| `start`    | Starting value (0-255 or 0-4095) | 0           | 0           |
| `end`      | Ending value (0-255 or 0-4095)   | 255         | 4095        |
| `duration` | Transition time in ms            | 10000       | 10000       |

**Note:** Values auto-scale based on pin type:
- PWM pins (0-99): Use 0-255 values
- Native DAC pins (100-101): Use 0-4095 values
- MCP4728 DAC pins (201-204): Use 0-4095 values

**Parameters for X Mode (different format!):**
| Parameter  | Description            | Example |
| ---------- | ---------------------- | ------- |
| `duration` | Transition time in ms  | 5000    |
| `t_start`  | Start of t range (0-2) | 0       |
| `t_end`    | End of t range (0-2)   | 1       |

**Parameters for F Mode (custom functions):**
| Parameter   | Description             | Example   |
| ----------- | ----------------------- | --------- |
| `func_name` | Name of custom function | heartbeat |
| `duration`  | Transition time in ms   | 2000      |

**Note:** Arduino performs smooth interpolation on-the-fly - no step count needed!

**Examples:**
```txt
# PWM channels (0-255)
# Linear ramp over 5 seconds (L mode)
RAMP:(L:0,255,5000);

# Ease-in over 3 seconds (I mode - scales to PWM range)
RAMP:(I:0,255,3000);

# Ease-in 50→200 range (same curve shape, different PWM output)
RAMP:(I:50,200,3000);

# DAC channels (0-4095) - MCP4728 or native DAC
# Linear ramp 0→4095 over 5 seconds
RAMP:(L:0,4095,5000);

# Ease-in over 3 seconds (full range)
RAMP:(I:0,4095,3000);

# Sub-range: ramp between 2000-2500 (useful for fine control)
RAMP:(L:2000,2500,5000);

# X mode: raw cosine curve (NO PWM values - t range determines output!)
RAMP:(X:5000|0,1);      # 5 seconds, Output: 0→max
RAMP:(X:5000|1,2);      # 5 seconds, Output: max→0
RAMP:(X:10000|0,2);     # 10 seconds breathing: 0→max→0

# Custom function (F mode) - see F_MODE_CUSTOM_FUNCTIONS.md for details
RAMP:(F:heartbeat,2000);
RAMP:(F:bounce,3000);
RAMP:(F:sine_wave,5000);

# Multi-segment breathing (PWM)
RAMP:(I:0,255,2000),(L:255,255,1000),(O:255,0,2000);

# Multi-segment breathing (DAC)
RAMP:(I:0,4095,2000),(L:4095,4095,1000),(O:4095,0,2000);
```

📖 **[F Mode Custom Functions Guide](F_MODE_CUSTOM_FUNCTIONS.md)** - Complete custom function documentation

### ⚠️ INVALID: Hybrid Protocols

**Do NOT mix RAMP and STATUS/TIME_MS in the same line:**
```txt
# INVALID - will cause error:
PATTERN:1;CH:1;RAMP:(I:0,200,5000);STATUS:200;TIME_MS:10000;REPEATS:1

# CORRECT - use L mode for constant sections:
PATTERN:1;CH:1;RAMP:(I:0,200,5000),(L:200,200,10000);REPEATS:1
```

### Legacy Format (Still Supported)

```txt
RAMP:<start>,<end>,<duration>,<steps>,<mode>
RAMP:<seg1>|<seg2>|<seg3>  # Multi-segment with | separator
```

---

## Easing Modes

### Unified Cosine Formula

All easing modes use the formula:

$$f(t) = \frac{1 - \cos(\pi \cdot t)}{2}$$

Where **t ∈ [0, 2]** produces a full cycle:
- **t = 0**: f(0) = 0 (start)
- **t = 1**: f(1) = 1 (peak)
- **t = 2**: f(2) = 0 (end)

### Mode t Ranges

The t parameter determines the portion of the cosine curve used:

| Mode         | Code | t Range (ascending) | t Range (descending) | Description                  |
| ------------ | ---- | ------------------- | -------------------- | ---------------------------- |
| **Linear**   | `L`  | N/A                 | N/A                  | Constant speed               |
| **Cosine**   | `C`  | [0, 1]              | [1, 2]               | Full S-curve, **PWM scaled** |
| **Ease-In**  | `I`  | [0, 0.5]            | [1, 1.5]             | Slow start, **PWM scaled**   |
| **Ease-Out** | `O`  | [0.5, 1]            | [1.5, 2]             | Fast start, **PWM scaled**   |
| **Custom**   | `X`  | [t_start, t_end]    | any range            | **Raw 255*f(t), NO scaling** |
| **Function** | `F`  | N/A                 | N/A                  | Custom function, raw output  |

### ⚠️ Important: X Mode Behavior

**X mode uses `PWM = 255 * f(t)` directly. The start_pwm and end_pwm values are IGNORED!**

This means the t range directly determines the PWM output:

```
# These all produce the same output (0 → 127.5):
RAMP:(X:0,255,5000|0,0.5)     # start/end PWM ignored!
RAMP:(X:100,200,5000|0,0.5)   # same output: 0 → 127.5
RAMP:(X:0,0,5000|0,0.5)       # same output: 0 → 127.5
```

Use X mode when you want direct control over the cosine curve portion.

### C, I, O Modes: PWM Scaling

For C, I, and O modes, the PWM range scales the curve portion to match start→end values:

```
# PWM 0→255 with ease-in shape
RAMP:(I:0,255,5000)

# PWM 50→200 with ease-in shape (same curve, different PWM range)
RAMP:(I:50,200,5000)
```

### Custom t Range Examples (X Mode)

| t Range  | f(t) Range | PWM Output  | Use Case                    |
| -------- | ---------- | ----------- | --------------------------- |
| [0, 0.5] | 0 → 0.5    | 0 → 127.5   | Half fade-in                |
| [0.5, 1] | 0.5 → 1    | 127.5 → 255 | Half fade-in (second half)  |
| [0, 1]   | 0 → 1      | 0 → 255     | Full fade-in                |
| [1, 1.5] | 1 → 0.5    | 255 → 127.5 | Half fade-out               |
| [1.5, 2] | 0.5 → 0    | 127.5 → 0   | Half fade-out (second half) |
| [1, 2]   | 1 → 0      | 255 → 0     | Full fade-out               |
| [0, 2]   | 0 → 1 → 0  | 0 → 255 → 0 | Breathing effect            |

### Visual Representation

```
PWM Value
    ^
255 |          ____C____          ____O____
    |       C/          \O      /           \L
    |     C/              \O   /              \
    |   C/                  \O/                \
    |  I                                     I  \
    | I                                       I  \
    |I___________           ___________         I\_______
  0 +-------------------------------------------------> Time
       Ease-In (I)    Linear (L)     Ease-Out (O)
```

---

## Interactive Visualization

See the easing curves and experiment with parameters:

📓 **[Easing Curves Jupyter Notebook](easing_curves_visualization.ipynb)**

The notebook includes:
- Interactive Plotly visualizations
- All easing modes compared
- PWM value calculations
- Custom t range explorer
- Breathing effect simulator
- Multi-segment examples

---

## Multi-Segment RAMP Examples

### Breathing Effect (Full Cosine Cycle)

```txt
# Using t=[0,2] for smooth 0→255→0 cycle
PATTERN:1;CH:1;RAMP:(X:0,255,2000|0,1),(X:255,0,2000|1,2);REPEATS:10
```

This creates:
1. **Segment 1**: 0→255 with ease-in (t: 0→1), 2 seconds
2. **Segment 2**: 255→0 with ease-out (t: 1→2), 2 seconds
3. Result: Smooth breathing, 4 seconds per cycle, 10 repetitions

### Fade-In, Hold, Fade-Out

```txt
PATTERN:1;CH:1;RAMP:(I:0,255,3000),(L:255,255,2000),(O:255,0,3000);REPEATS:1
```

### Sunrise Simulation

```txt
# 30-minute sunrise with ease-in (natural slow start)
PATTERN:1;CH:1;RAMP:(I:0,255,1800000);REPEATS:1

# Hold at full brightness for 2 hours
PATTERN:2;CH:1;STATUS:255;TIME_MS:7200000;REPEATS:1

# 15-minute sunset with ease-out (natural slow end)
PATTERN:3;CH:1;RAMP:(O:255,0,900000);REPEATS:1
```

---

## Python API

### Generate RAMP Command (New Format)

```python
from lcfunc import generate_ramp_segment_new, generate_ramp_command

# Single segment with new format
segment = generate_ramp_segment_new(
    easing='I',           # Mode: L/C/I/O/X
    start_pwm=0,          # Start value
    end_pwm=255,          # End value
    duration_ms=5000,     # Duration in ms
    t_start=0.0,          # Custom t start (optional)
    t_end=1.0             # Custom t end (optional)
)
# Returns: "(I:0,255,5000)"

# With custom t range
segment = generate_ramp_segment_new(
    easing='X', start_pwm=0, end_pwm=255,
    duration_ms=2000, t_start=0, t_end=2
)
# Returns: "(X:0,255,2000|0,2)"

# Full command with new format
cmd = generate_ramp_command(
    channel_num=1, pattern_num=1,
    start_pwm=0, end_pwm=255,
    duration_ms=10000, easing='C',
    new_format=True, repeats=1
)
# Returns: "PATTERN:1;CH:1;RAMP:(C:0,255,10000);REPEATS:1"
```

### Multi-Segment RAMP (New Format)

```python
from lcfunc import generate_multi_ramp_command

segments = [
    {'start_pwm': 0, 'end_pwm': 255, 'duration_ms': 3000, 'easing': 'I'},
    {'start_pwm': 255, 'end_pwm': 255, 'duration_ms': 2000, 'easing': 'L'},
    {'start_pwm': 255, 'end_pwm': 0, 'duration_ms': 3000, 'easing': 'O'}
]

cmd = generate_multi_ramp_command(
    channel_num=1, pattern_num=1,
    segments=segments,
    new_format=True, repeats=3
)
# Returns: "PATTERN:1;CH:1;RAMP:(I:0,255,3000),(L:255,255,2000),(O:255,0,3000);REPEATS:3"
```

### Breathing Effect Helper

```python
from lcfunc import create_breathing_ramp

cmd = create_breathing_ramp(
    channel_num=1, pattern_num=1,
    min_pwm=0, max_pwm=255,
    inhale_ms=2000, exhale_ms=2000,
    repeats=10
)
# Returns: "PATTERN:1;CH:1;RAMP:(X:0,255,2000|0,1),(X:255,0,2000|1,2);REPEATS:10"
```

### Calculate Eased Value (Preview)

```python
from lcfunc import calculate_eased_value

# Simulate easing for preview
for i in range(11):
    progress = i / 10.0
    
    # Linear
    linear = calculate_eased_value(progress, 0, 255, 'L')
    
    # Ease-in (t: 0→1)
    ease_in = calculate_eased_value(progress, 0, 255, 'I', t_start=0, t_end=1)
    
    # Ease-out (t: 1→2)
    ease_out = calculate_eased_value(progress, 0, 255, 'O', t_start=1, t_end=2)
    
    print(f"t={progress:.1f}: L={linear:.0f}, I={ease_in:.0f}, O={ease_out:.0f}")
```

---

## Arduino Command Format

### PWM Status Command

```
PATTERN:<n>;CH:<ch>;STATUS:<pwm1>,<pwm2>,...;TIME_MS:<t1>,<t2>,...;REPEATS:<r>
```

Where STATUS values are now **0-255** (not just 0/1).

### RAMP Command (New Format)

```
PATTERN:<n>;CH:<ch>;RAMP:(MODE:start,end,duration[,steps][|t_start,t_end]),...;REPEATS:<r>
```

**Examples:**
```
PATTERN:1;CH:1;RAMP:(L:0,255,5000);REPEATS:1
PATTERN:1;CH:1;RAMP:(I:0,255,3000),(O:255,0,3000);REPEATS:5
PATTERN:1;CH:1;RAMP:(X:0,255,2000|0,1),(X:255,0,2000|1,2);REPEATS:10
```

### Legacy Format (Backward Compatible)

```
PATTERN:<n>;CH:<ch>;RAMP:<start>,<end>,<duration>,<steps>,<mode>;REPEATS:<r>
PATTERN:<n>;CH:<ch>;RAMP:<seg1>|<seg2>|...;REPEATS:<r>
```

Each segment: `<start>,<end>,<duration>,<steps>,<mode>[,<t_start>,<t_end>]`

Arduino executes ramps internally using `analogWrite()` and timer interrupts.

---

## Implementation Details

### Arduino PWM Pins

On Arduino Due, PWM-capable pins:
- Pins 2-13: PWM capable (8-bit, 0-255)
- Default channel pins: 13, 12, 11, 10 (all PWM capable)

### Timing Accuracy

- RAMP transitions use `millis()` for timing
- PWM updates occur at calculated intervals: `duration_ms / steps`
- Minimum recommended step interval: 10ms (100 steps/second max)

### Memory Impact

- Single RAMP segment: ~20 bytes per pattern
- Multi-segment RAMP: ~14 bytes per segment (up to 4 segments)
- Equivalent discrete steps: ~8 bytes × N steps
- For 100-step gradient: 20 bytes vs 800+ bytes

### Maximum Segments

`MAX_RAMP_SEGMENTS = 4` per pattern (adjustable in firmware)

---

## Examples

### Sunrise Simulation (with Ease-In)

```txt
# 30-minute sunrise from 0% to 100% with ease-in (natural slow start)
PATTERN:1;CH:1;RAMP:(I:0,255,1800000);REPEATS:1

# Hold at full brightness for 2 hours
PATTERN:2;CH:1;STATUS:255;TIME_MS:7200000;REPEATS:1

# 15-minute sunset with ease-out (natural slow end)
PATTERN:3;CH:1;RAMP:(O:255,0,900000);REPEATS:1
```

### Breathing Effect (Full Cosine Cycle)

```txt
# Smooth breathing using t=[0,2] for complete 0→peak→0 cycle
# 10 cycles, each 4 seconds
PATTERN:1;CH:1;RAMP:(X:0,230,2000|0,1),(X:230,0,2000|1,2);REPEATS:10

START_TIME: {'CH1': 30}
```

### Multi-Phase Pattern

```txt
# Phase 1: Quick ease-in to 50%
# Phase 2: Slow linear ramp to 100%  
# Phase 3: Hold at 100%
# Phase 4: Ease-out back to 0%
PATTERN:1;CH:1;RAMP:(I:0,128,1000),(L:128,255,5000),(L:255,255,3000),(O:255,0,2000);REPEATS:1
```

### Multi-Channel Gradient (Excel)

| Sections | CH1_status | CH1_time_sec | CH1_ramp      | CH2_status | CH2_time_sec |
| -------- | ---------- | ------------ | ------------- | ---------- | ------------ |
| 0        | ramp       | 10           | 0.0→1.0,100,C | 0.0        | 10           |
| 1        | 1.0        | 10           |               | ramp       | 10           |
| 2        | ramp       | 10           | 1.0→0.0,100,C | 1.0        | 10           |

---

## HTML Visualization

The protocol visualizer now includes **intensity-time plots** using Plotly:

```bash
python viz_protocol_html.py examples/pwm_ramp_protocol.txt
```

Features:
- Interactive zoom and pan
- Shows PWM value (0-255) over time
- Displays all easing curves correctly
- Supports both RAMP and STATUS patterns
- Per-channel intensity plots

---

## STATUS vs RAMP Behavior

Understanding the difference between STATUS and RAMP is crucial for precise PWM control:

| Feature           | STATUS                               | RAMP                       |
| ----------------- | ------------------------------------ | -------------------------- |
| **Purpose**       | Simple ON/OFF control                | Smooth PWM transitions     |
| **Values**        | Binary: 0=OFF, any non-zero=ON (255) | Actual PWM: 0-255          |
| **Visualization** | Shown as 0 or 255                    | Shown as actual PWM values |
| **Use Case**      | Blinking, pulsing patterns           | Breathing, fading, dimming |

**Example - Constant 50% Brightness:**
```txt
# ❌ WRONG: STATUS:128 will be treated as ON (255), not 50%
PATTERN:1;CH:1;STATUS:128;TIME_MS:5000;REPEATS:1

# ✅ CORRECT: Use RAMP with constant level
PATTERN:1;CH:1;RAMP:(L:128,128,5000);REPEATS:1
```

---

## Backward Compatibility

- **Binary status (0/1)**: Still supported, mapped to 0/255
- **Intermediate status (1-254)**: Treated as ON (255) for visualization
- **Existing protocols**: Work unchanged
- **PULSE mode**: Compatible with PWM (pulses at specified intensity)
- **Legacy RAMP format**: `RAMP:start,end,duration,steps,mode` still supported

---

## Hardware Requirements

- **Arduino Due recommended**: Better PWM resolution and timing
- **PWM-capable pins**: Ensure channel pins support `analogWrite()`
- **LED driver**: Must accept PWM input (most LED drivers do)

---

## Version History

- **v2.2.1**: Initial PWM and RAMP support with linear interpolation
- **v2.2.2**: Added easing functions (cosine, ease-in, ease-out, custom) and multi-segment RAMP support
- **v2.2.3**: New parenthesized command format, unified cosine formula with t∈[0,2], Jupyter notebook visualization, HTML intensity plots
