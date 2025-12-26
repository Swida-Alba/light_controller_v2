# Mock Arduino Simulator Guide

## Overview

The **Mock Arduino Simulator** (`mock_arduino.py`) allows you to test and validate light control protocols without physical Arduino hardware. It accurately simulates:

- PWM easing transitions with correct t ranges
- Channel monitoring output ($CHMON: format)
- Protocol validation with warnings and errors
- Custom easing functions

---

## Quick Start

```bash
# Basic simulation with plot
python mock_arduino.py protocol.txt --plot

# Save data and visualization
python mock_arduino.py protocol.txt --output data.csv --save-plot results.html

# Validate protocol only (no simulation)
python mock_arduino.py protocol.txt --validate

# Real-time simulation at 10x speed
python mock_arduino.py protocol.txt --realtime --speed 10

# Test custom functions (F mode)
python mock_arduino.py protocol.txt --custom-funcs light_controller_v2_2_arduino/custom_easing.h --plot
```

---

## Command Line Options

| Option | Description |
|--------|-------------|
| `protocol` | Protocol file to simulate (required) |
| `--output`, `-o` | Output CSV file for data logging |
| `--plot` | Show interactive Plotly visualization |
| `--save-plot FILE` | Save plot to HTML file |
| `--realtime` | Simulate in real-time |
| `--speed N` | Speed factor for realtime (default: 1.0) |
| `--step N` | Simulation time step in ms (default: 10) |
| `--print-interval N` | $CHMON print interval in ms (default: 100) |
| `--validate` | Validate protocol only, don't simulate |
| `--quiet`, `-q` | Suppress $CHMON output |
| `--custom-funcs FILE` | Load custom functions from header file (required for F mode) |

---

## Protocol Validation

The simulator validates your protocols and reports:

### Errors (Simulation stops)
- Missing PATTERN or CH specification
- Unknown custom function names (F mode)
- Invalid syntax
- **Hybrid protocols** - mixing RAMP and STATUS/TIME_MS in same line

### Warnings (Simulation continues)
- PWM values outside [0, 255] (auto-clipped)
- t range outside [0, 2]
- Direction mismatch (ascending PWM with descending t range)

### Example Output

```
Parsing protocol: my_protocol.txt
Found 3 pattern(s)
⚠️  Warning: Line 5: PWM value 300 outside [0,255], will be clipped
⚠️  Warning: Line 8: Mode 'I' with descending PWM (255→0) uses ascending t range [0,0.5]. 
    Consider using [1,1.5] for proper easing.

📋 Validation Summary: 0 errors, 2 warnings

Starting simulation...
```

---

## Direction-Aware t Ranges

The simulator automatically selects correct t ranges based on PWM direction:

| Mode | Ascending (start < end) | Descending (start > end) |
|------|-------------------------|--------------------------|
| **L** (Linear) | N/A | N/A |
| **C** (Cosine) | [0, 1] | [1, 2] |
| **I** (Ease-In) | [0, 0.5] | [1, 1.5] |
| **O** (Ease-Out) | [0.5, 1] | [1.5, 2] |
| **X** (Custom) | User-specified | User-specified |
| **F** (Function) | N/A (raw values) | N/A (raw values) |

### What "Direction Mismatch" Means

If you specify:
```
RAMP:(I:255,0,5000)  # Descending PWM (255→0)
```

The simulator will warn you that:
- Mode `I` with descending PWM should use t range [1, 1.5]
- But without explicit t range, ascending defaults [0, 0.5] might be used

**Solution:** Either let auto-selection handle it, or explicitly specify:
```
RAMP:(I:255,0,5000|1,1.5)  # Explicit descending t range
```

---

## Non-Monotonic t Ranges

### What Happens with t Ranges Crossing t=1?

The cosine function `f(t) = (1 - cos(πt)) / 2` has a **peak at t=1** where f(1)=1.

If you specify a t range that crosses t=1 (e.g., `[0.5, 2]`), the curve is **non-monotonic**:

```
t: 0.5 → 1.0 → 2.0
f: 0.5 → 1.0 → 0.0  (goes UP then DOWN)
```

### PWM Scaling for Non-Monotonic Ranges

PWM is calculated by **normalizing f(t)** to the range [f(t_start), f(t_end)]:

```
eased_progress = (f(t) - f(t_start)) / (f(t_end) - f(t_start))
PWM = start_pwm + eased_progress * (end_pwm - start_pwm)
```

**Example: t=[0.5, 2] with PWM 0→200**

| Progress | t | f(t) | eased_progress | PWM |
|----------|---|------|----------------|-----|
| 0.0 | 0.5 | 0.500 | 0.00 | 0 |
| 0.33 | 1.0 | 1.000 | **-1.00** | **-200** → clipped to **0** |
| 0.67 | 1.5 | 0.500 | 0.00 | 0 |
| 1.0 | 2.0 | 0.000 | 1.00 | 200 |

⚠️ **Warning**: This creates a **dip below the start value** before reaching the end!

### Scrutinization Warning

The simulator will warn you:

```
⚠️  Warning: Non-monotonic t range [0.5,2] crosses peak at t=1. 
    f(t) goes 0.500→1.000→0.000. 
    PWM will NOT be a smooth transition - consider splitting into two segments.
```

### How to Handle Non-Monotonic Effects

**Option 1: Split into two segments**
```
# Instead of: RAMP:(X:10000|0.5,2)
# Use:
RAMP:(X:5000|0.5,1),(X:5000|1,2)
```

**Option 2: Use custom functions**
```
# Define a function that handles the full curve
RAMP:(F:sine_wave,10000)
```

**Option 3: Accept the behavior**

Sometimes non-monotonic is what you want (e.g., breathing, pulses).

---

## X Mode: Raw Cosine Curve

**X mode uses `255 * f(t)` directly WITHOUT scaling.** PWM values are NOT needed.

### X Mode Format (Different from I/O/C!)

```txt
RAMP:(X:duration_ms|t_start,t_end);
```

### How X Mode Works

```
PWM = 255 * f(t) = 255 * (1 - cos(πt)) / 2

Where t = t_start + progress * (t_end - t_start)
```

### X Mode vs Other Modes

| Mode | Format | Calculation |
|------|--------|-------------|
| **L/C/I/O** | `(MODE:start,end,duration)` | Scaled easing between start/end PWM |
| **X** | `(X:duration\|t_start,t_end)` | `255 * f(t)` directly (no PWM params!) |
| **F** | `(F:func_name,duration)` | Custom function raw output |

### X Mode Examples

```txt
# Half-wave: 0→127.5 (only uses first half of curve)
RAMP:(X:5000|0,0.5);

# Full wave up: 0→255
RAMP:(X:5000|0,1);

# Full wave down: 255→0
RAMP:(X:5000|1,2);

# Full breathing cycle: 0→255→0
RAMP:(X:10000|0,2);
```

**Key Insight:** For X mode, the t range completely determines the PWM output. No PWM values needed or accepted!

---

## Custom Easing Functions (F Mode)

### Using Custom Functions in Protocols

```
# Format: (F:function_name,duration_ms)
PATTERN:1;CH:1;RAMP:(F:sine,5000);REPEATS:3
PATTERN:2;CH:1;RAMP:(F:heartbeat,2000);REPEATS:5
```

### Built-in Functions

The simulator includes these custom functions:

| Name | Description | Formula |
|------|-------------|---------|
| `sine` | Sine wave (non-monotonic) | `255 * sin(π * p)` |
| `triangle` | Triangle wave | `255 * 2 * abs(p - 0.5)` |
| `square` | Square wave | `255 if p >= 0.5 else 0` |
| `exponential` | Exponential growth | `255 * (e^p - 1) / (e - 1)` |
| `logarithmic` | Logarithmic growth | `255 * log(1 + p*(e-1)) / log(e)` |
| `bounce` | Bouncing decay | `255 * abs(sin(3πp) * (1-p))` |

### Using Custom Functions

```
# Protocol using custom function (F mode format: function_name,duration)
PATTERN:1;CH:1;RAMP:(F:sine_wave,5000);REPEATS:3
PATTERN:2;CH:1;RAMP:(F:bounce,3000);REPEATS:2
PATTERN:3;CH:1;RAMP:(F:heartbeat,2000),(F:breathing,4000);REPEATS:5
```

### Creating Your Own Functions

Edit the header file (`light_controller_v2_2_arduino/custom_easing.h`):

```c
// custom_easing.h
// Custom easing functions for Light Controller

// CUSTOM_FUNC: heartbeat
// PYTHON_EQUIV: lambda p: min(255, 255 * (math.exp(-20*(p-0.2)**2) + 0.6*math.exp(-20*(p-0.4)**2)))

float heartbeat(float progress) {
    // Heartbeat-like pattern (two quick pulses)
    float pulse1 = exp(-20.0 * pow(progress - 0.2, 2));
    float pulse2 = 0.6 * exp(-20.0 * pow(progress - 0.4, 2));
    return 255.0 * (pulse1 + pulse2);
}

// CUSTOM_FUNC: flicker
// PYTHON_EQUIV: lambda p: 127.5 + 127.5 * math.sin(p * math.pi * 20) * math.sin(p * math.pi * 7)

float flicker(float progress) {
    // Flickering effect
    return 127.5 + 127.5 * sin(progress * 3.14159265 * 20.0) * sin(progress * 3.14159265 * 7.0);
}
```

Load and use:

```bash
python mock_arduino.py protocol.txt --custom-funcs light_controller_v2_2_arduino/custom_easing.h --plot
```

### F Mode Format

```txt
RAMP:(F:function_name,duration_ms);
```

**Key Points:**
- **Only 2 parameters**: function name and duration
- **Progress = elapsed_time / duration** - converted externally
- **No PWM start/end values** - function determines the entire curve
- **Clipping done externally** - values outside [0,255] are auto-clipped

📖 **[F Mode Custom Functions Guide](F_MODE_CUSTOM_FUNCTIONS.md)** - Complete documentation

### Important Notes for Custom Functions

1. **No PWM scaling** - Custom functions output raw PWM values (0-255)
2. **Auto-clipping** - Values outside [0, 255] are automatically clipped
3. **Non-monotonic OK** - Unlike standard easing, custom functions can go up and down
4. **Progress range** - Input `p` goes from 0.0 to 1.0 over the duration

### Available Built-in Functions

| Function | Description |
|----------|-------------|
| `sine_wave` | Half sine: 0 → 255 → 0 |
| `double_sine` | Two bumps |
| `bounce` | Damped oscillation |
| `heartbeat` | Two quick pulses |
| `exp_decay` | Sharp start, gradual decay |
| `log_rise` | Slow start, accelerating |
| `step_50` | Step at 50% |
| `sawtooth` | 3 linear cycles |
| `breathing` | Smooth in-out |
| `flicker` | Random-like pattern |

---

## Output Formats

### CSV Output

```csv
time_ms,CH1,CH2,CH3,CH4,CH5,CH6,CH7,CH8
0,0,0,0,0,0,0,0,0
10,1,0,0,0,0,0,0,0
20,2,0,0,0,0,0,0,0
...
```

### Serial Monitor Format

```
$CHMON:CH1:128,CH2:255,CH3:0,CH4:192,CH5:0,CH6:0,CH7:0,CH8:0
```

---

## Examples

### 1. Validate Protocol

```bash
python mock_arduino.py examples/sunrise.txt --validate
```

### 2. Quick Visualization

```bash
python mock_arduino.py examples/breathing.txt --plot
```

### 3. Full Analysis

```bash
python mock_arduino.py examples/circadian.txt \
    --output circadian_data.csv \
    --save-plot circadian_analysis.html \
    --print-interval 1000
```

### 4. Real-time Preview (10x speed)

```bash
python mock_arduino.py examples/test.txt --realtime --speed 10
```

### 5. Custom Functions

```bash
python mock_arduino.py protocol.txt \
    --custom-funcs my_functions.h \
    --plot \
    --output custom_sim.csv
```

---

## Integration with Serial Monitor

The mock Arduino outputs the same `$CHMON:` format as the real Arduino. You can pipe its output to the serial monitor for testing:

```bash
# Terminal 1: Run mock Arduino with output
python mock_arduino.py protocol.txt --realtime --speed 1 2>&1 | tee mock_output.txt

# Terminal 2: In theory, you could pipe to serial_monitor.py
# (requires modification to accept stdin instead of serial port)
```

---

## Troubleshooting

### "No patterns found"

- Check protocol syntax
- Ensure PATTERN: and CH: are specified
- Look for typos in RAMP commands

### "Custom function not found"

- Check function name spelling
- Verify header file format
- Use `--custom-funcs` to load the file

### Plot not showing

- Install plotly: `pip install plotly`
- Use `--save-plot` instead to save HTML

### Simulation too slow

- Increase `--step` value (e.g., `--step 100`)
- Reduce protocol duration for testing
- Use `--quiet` to suppress console output

---

## API Usage (Python)

```python
from mock_arduino import MockArduino, ProtocolParser

# Parse protocol
parser = ProtocolParser(verbose=True)
patterns = parser.parse_file('protocol.txt')

# Check validation
is_valid, warnings, errors = parser.validate()
if not is_valid:
    print("Protocol has errors!")
    for e in errors:
        print(f"  {e}")

# Simulate
arduino = MockArduino(time_step_ms=10)
data = arduino.simulate_patterns(patterns)

# Save results
arduino.save_csv('output.csv')
arduino.plot(title="My Protocol", save_html='output.html')
```

---

## See Also

- [PWM & Ramp Control Guide](PWM_RAMP_CONTROL.md) - Easing formulas and modes
- [Serial Monitor Guide](SERIAL_MONITOR_GUIDE.md) - Real-time monitoring
- [Easing Curves Notebook](easing_curves_visualization.ipynb) - Interactive visualization
