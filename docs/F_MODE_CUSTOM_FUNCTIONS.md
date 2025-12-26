# F Mode: Custom Easing Functions Guide

## Overview

**F Mode** (Function Mode) allows you to use custom easing functions beyond the built-in L, C, I, O, X modes. This enables complex non-monotonic patterns like heartbeat, bounce, flicker, and breathing effects.

**Version**: 2.2.3  
**Status**: Production Ready ✅

---

## Quick Start

### Protocol Usage

```txt
PATTERN:1;CH:1;RAMP:(F:sine_wave,5000);REPEATS:3
PATTERN:2;CH:1;RAMP:(F:heartbeat,2000);REPEATS:10
PATTERN:3;CH:1;RAMP:(F:bounce,3000),(F:breathing,4000);REPEATS:5
```

### Testing with Mock Arduino

```bash
# Simulate custom function protocol
python mock_arduino.py protocol.txt --custom-funcs light_controller_v2_2_arduino/custom_easing.h --plot

# Validate before uploading
python mock_arduino.py protocol.txt --validate
```

---

## F Mode Format

```txt
RAMP:(F:function_name,duration_ms);
```

| Parameter | Description | Example |
|-----------|-------------|---------|
| `function_name` | Name of custom function | `heartbeat` |
| `duration_ms` | Total duration in milliseconds | `5000` |

**Key Points:**
- ✅ **Only 2 parameters** - function name and duration
- ✅ **No PWM start/end values** - function determines the entire curve
- ✅ **Duration scales time to progress** - `progress = elapsed_time / duration`
- ✅ **Clipping done externally** - Arduino clips after function returns

---

## How Progress Works

All custom functions receive `progress` as a value between `[0, 1]`:

```
progress = elapsed_time / duration_ms
```

The conversion happens **outside** the function:

```python
# Time to progress conversion (done by simulator/Arduino)
progress = min(1.0, elapsed_time / duration_ms)  # [0, 1]

# Function call
pwm = custom_function(progress)  # Returns 0-255

# Clipping (done after function)
pwm = clip_pwm(pwm)  # Ensures 0 ≤ pwm ≤ 255
```

**Example Timeline:**
| Time (ms) | Duration | Progress | Function Output |
|-----------|----------|----------|-----------------|
| 0 | 5000 | 0.0 | `sine_wave(0.0)` = 0 |
| 1250 | 5000 | 0.25 | `sine_wave(0.25)` = 180 |
| 2500 | 5000 | 0.5 | `sine_wave(0.5)` = 255 |
| 3750 | 5000 | 0.75 | `sine_wave(0.75)` = 180 |
| 5000 | 5000 | 1.0 | `sine_wave(1.0)` = 0 |

---

## Available Built-in Functions

The following functions are defined in `light_controller_v2_2_arduino/custom_easing.h`:

| Function | Description | Output Shape |
|----------|-------------|--------------|
| `sine_wave` | Half sine wave | 0 → 255 → 0 |
| `double_sine` | Two bumps | 0 → 255 → 0 → 255 → 0 |
| `bounce` | Damped oscillation | Ball bounce effect |
| `heartbeat` | Two quick pulses | Lub-dub pattern |
| `exp_decay` | Sharp start, gradual decay | 255 → ~12 |
| `log_rise` | Slow start, accelerating | 0 → 255 |
| `step_50` | Step at 50% | 0 then 255 |
| `sawtooth` | 3 linear cycles | Repeating ramp |
| `breathing` | Smooth in-out | 0 → 255 → 0 |
| `flicker` | Random-like pattern | Irregular oscillation |
| `myfunc` | User-customizable placeholder | Edit to experiment! |

### Visual Gallery

See all functions visualized in the [Easing Curves Notebook](easing_curves_visualization.ipynb).

---

## Adding New Custom Functions

### Quick Method: Use `myfunc` (No Code Changes Needed!)

The simplest way to experiment with custom effects is to **edit the `myfunc` function** in `custom_easing.h`. It's already registered in the dispatcher, so:

1. **Edit** `myfunc()` in `custom_easing.h`:
```c
float myfunc(float progress) {
    // Change this formula to anything you want!
    return 255.0 * progress * progress;  // Example: quadratic ease-in
}
```

2. **Recompile and upload** the Arduino firmware.

3. **Use in protocol**:
```txt
PATTERN:1;CH:1;RAMP:(F:myfunc,3000);REPEATS:5
```

That's it! No need to modify any other files.

---

### Standard Method: Add Your Own Function

For a permanent function with a meaningful name:

#### Step 1: Edit custom_easing.h

Add your function to `light_controller_v2_2_arduino/custom_easing.h`:

```c
// =============================================================================
// MY CUSTOM FUNCTION - Description of effect
// =============================================================================
// CUSTOM_FUNC: my_function
// PYTHON_EQUIV: lambda p: 255 * (p ** 2)

float my_function(float progress) {
    // progress: 0.0 to 1.0
    // output: 0 to 255 (clipping done externally)
    return 255.0 * progress * progress;  // Quadratic ease-in
}
```

#### Step 2: Register in Function Dispatcher

**File:** `light_controller_v2_2_arduino/function_dispatcher.h`

Find the `FUNCTION_REGISTRY` array and add your function:

```cpp
const FunctionEntry FUNCTION_REGISTRY[] = {
    // ... existing functions ...
    {"flicker",     flicker},
    {"myfunc",      myfunc},
    
    // ADD YOUR FUNCTION HERE:
    {"my_function", my_function},  // ← Add this line!
};
```

#### Step 3: Recompile and Upload

Compile and upload the Arduino firmware. Your function is now available!

#### Step 4: Use in Protocol

```txt
PATTERN:1;CH:1;RAMP:(F:my_function,5000);REPEATS:3
```

### Availability Check

| Environment | Is New Function Available? |
|-------------|---------------------------|
| **Python Simulator** | ✅ **YES** - Immediately! |
| **Protocol Parsing** | ✅ **YES** - Parser reads header dynamically |
| **Arduino Hardware** | ✅ **YES** - After adding to function_dispatcher.h |

---

### Complete Example: Adding a "pulse_train" Function

**Step 1:** Add function to `custom_easing.h`:

```cpp
// =============================================================================
// PULSE TRAIN - Rapid on-off pulses
// =============================================================================
// CUSTOM_FUNC: pulse_train
// PYTHON_EQUIV: lambda p: 255 if (int(p * 10) % 2 == 0) else 0

float pulse_train(float progress) {
    int phase = (int)(progress * 10.0);
    return (phase % 2 == 0) ? 255.0 : 0.0;
}
```

**Step 2:** Add to registry in `function_dispatcher.h`:

```cpp
const FunctionEntry FUNCTION_REGISTRY[] = {
    // ... existing functions ...
    {"pulse_train", pulse_train},  // Add this line
};
```

**Step 3:** Recompile and upload Arduino firmware.

**Step 4:** Use in protocol:

```txt
PATTERN:1;CH:1;RAMP:(F:pulse_train,5000);REPEATS:3
```

### Why is this needed?

Arduino C++ compiles code at upload time. Unlike Python, it cannot dynamically discover functions at runtime. The dispatcher acts as a lookup table that maps function names (strings) to actual function pointers.

---

## F Mode vs Other Modes

| Mode | Format | Use Case |
|------|--------|----------|
| **L** | `(L:start,end,duration)` | Constant speed transitions |
| **I** | `(I:start,end,duration)` | Slow start, fast end |
| **O** | `(O:start,end,duration)` | Fast start, slow end |
| **C** | `(C:start,end,duration)` | Full S-curve |
| **X** | `(X:duration\|t_start,t_end)` | Raw cosine curve |
| **F** | `(F:func_name,duration)` | Custom function |

### When to Use F Mode

✅ **Use F Mode for:**
- Non-monotonic patterns (heartbeat, bounce, flicker)
- Complex waveforms that don't fit L/C/I/O
- Repeating patterns within a single segment (sawtooth, double_sine)
- Effects that need full control over the PWM curve

❌ **Don't use F Mode for:**
- Simple linear ramps (use L mode)
- Standard ease-in/out (use I, O, C modes)
- Raw cosine access (use X mode)

---

## Testing Custom Functions

### 1. Validate Protocol Syntax

```bash
python mock_arduino.py protocol.txt --validate --custom-funcs light_controller_v2_2_arduino/custom_easing.h
```

### 2. Simulate with Visualization

```bash
python mock_arduino.py protocol.txt --plot --custom-funcs light_controller_v2_2_arduino/custom_easing.h
```

### 3. Export Simulation Data

```bash
python mock_arduino.py protocol.txt --output simulation.csv --custom-funcs light_controller_v2_2_arduino/custom_easing.h
```

### 4. Interactive Notebook

Open `docs/easing_curves_visualization.ipynb` in Jupyter to see:
- All custom functions visualized
- Interactive Plotly charts
- Protocol examples

---

## Protocol Examples

### Simple Custom Function

```txt
PATTERN:1;CH:1;RAMP:(F:breathing,10000);REPEATS:5
START_TIME: {'CH1': 0}
```

### Multi-Function Sequence

```txt
PATTERN:1;CH:1;RAMP:(F:heartbeat,2000),(F:bounce,3000),(F:flicker,1000);REPEATS:3
START_TIME: {'CH1': 0}
```

### Mixed Modes

```txt
PATTERN:1;CH:1;RAMP:(I:0,255,5000),(F:breathing,10000),(O:255,0,5000);REPEATS:2
START_TIME: {'CH1': 0}
```

### Multi-Channel with Custom Functions

```txt
PATTERN:1;CH:1;RAMP:(F:heartbeat,2000);REPEATS:10
PATTERN:2;CH:2;RAMP:(F:breathing,5000);REPEATS:4
PATTERN:3;CH:3;RAMP:(F:flicker,1000);REPEATS:20
START_TIME: {'CH1': 0, 'CH2': 0, 'CH3': 0}
```

---

## Troubleshooting

### "Custom function 'xxx' not found"

**Cause:** Function name not in header file or built-in functions.

**Solution:**
1. Check spelling in protocol matches function name exactly
2. Ensure `--custom-funcs` flag points to correct header file
3. Verify function has `// CUSTOM_FUNC: name` comment

### Function returns values outside [0, 255]

**Not a problem!** Clipping is done automatically after the function returns.

### Function doesn't look right in simulation

1. Check `// PYTHON_EQUIV:` matches C++ implementation
2. Verify progress is used correctly (should be 0-1)
3. Check for math library imports in Python equivalent

---

## Related Documentation

- **[PWM & Ramp Control Guide](PWM_RAMP_CONTROL.md)** - All easing modes
- **[Easing Curves Notebook](easing_curves_visualization.ipynb)** - Interactive visualization
- **[Mock Arduino Guide](MOCK_ARDUINO_GUIDE.md)** - Protocol simulation
- **[custom_easing.h](../light_controller_v2_2_arduino/custom_easing.h)** - Function definitions

---

## Quick Reference

```txt
# F Mode Format
RAMP:(F:function_name,duration_ms);

# Available Functions
sine_wave, double_sine, bounce, heartbeat, exp_decay,
log_rise, step_50, sawtooth, breathing, flicker

# Test Command
python mock_arduino.py protocol.txt --custom-funcs light_controller_v2_2_arduino/custom_easing.h --plot

# Progress Formula
progress = elapsed_time / duration  # Range: [0, 1]
```

---

**Happy custom function creation! 🎨**
