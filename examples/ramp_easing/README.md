# RAMP & Easing Mode Examples

This folder contains protocol examples demonstrating **RAMP mode** and various **easing functions** for smooth LED transitions.

## ⚠️ Important Note

**RAMP mode is only available in TXT protocol files.** Excel protocols do NOT support RAMP commands due to format limitations.

---

## Syntax Reference (v2.3.0)

```
# Single segment RAMP
PATTERN:1;CH:1;RAMP:(MODE:start,end,duration)

# Multi-segment RAMP (comma-separated inside parentheses)
PATTERN:1;CH:1;RAMP:(MODE1:s1,e1,d1),(MODE2:s2,e2,d2)

# With optional steps parameter
PATTERN:1;CH:1;RAMP:(MODE:start,end,duration,steps)
```

### Parameters:
| Parameter | Description | Range |
|-----------|-------------|-------|
| MODE | Easing mode (see below) | L, I, O, IO, E, EI, EIO, X, F |
| start | Starting PWM intensity | 0-255 |
| end | Ending PWM intensity | 0-255 |
| duration | Transition duration (ms) | Positive integer |
| steps | Number of steps (optional) | 1-255, default=100 |

---

## Available Easing Modes

| Mode | Name | Description |
|------|------|-------------|
| `L` | Linear | Constant rate of change |
| `I` | Ease In | Slow start, fast end |
| `O` | Ease Out | Fast start, slow end |
| `IO` | Ease In-Out | Slow start and end |
| `E` | Exponential | Strong acceleration |
| `EI` | Exponential In | Exponential slow start |
| `EIO` | Exponential In-Out | Symmetric exponential |
| `X` | Extended | Custom easing curve |
| `F` | Flicker | Random/natural variation |

---

## Files in This Folder

| File | Description |
|------|-------------|
| [pwm_ramp_protocol.txt](pwm_ramp_protocol.txt) | Basic PWM intensity demo with multi-segment RAMP |
| [comprehensive_easing_modes.txt](comprehensive_easing_modes.txt) | All easing modes demonstrated |
| [f_mode_demo.txt](f_mode_demo.txt) | Flicker mode examples |
| [x_mode_demo.txt](x_mode_demo.txt) | Extended easing mode examples |
| [test_ramp_visualization.txt](test_ramp_visualization.txt) | Test file for visualization |
| `*.html` | Generated visualization files |

---

## Quick Examples

### Smooth Fade In
```
PATTERN:1;CH:1;RAMP:(I:0,255,3000)
```

### Breathing Effect (Up and Down)
```
PATTERN:1;CH:1;RAMP:(IO:0,255,2000),(IO:255,0,2000)
```

### Candle Flicker
```
PATTERN:1;CH:1;RAMP:(F:100,200,5000)
```

---

## Generating Visualizations

```bash
python viz_protocol_html.py examples/ramp_easing/pwm_ramp_protocol.txt
```

This creates an HTML file showing the PWM waveform over time.

---

## See Also

- [PROTOCOL_SYNTAX_REFERENCE.md](../../docs/PROTOCOL_SYNTAX_REFERENCE.md) - Complete syntax guide
- [RAMP documentation](../../docs/FEATURES.md) - Feature details
