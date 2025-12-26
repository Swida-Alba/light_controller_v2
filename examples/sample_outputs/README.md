# Sample Output Files

This folder contains pre-generated HTML visualization examples that demonstrate the Light Controller's visualization capabilities.

## Files

| File | Description |
|------|-------------|
| `1min_test_expected.html` | Simple 1-minute protocol with ON/OFF and RAMP patterns |
| `5min_pwm_ramp_demo_simulation.html` | 5-minute demo showing PWM ramp capabilities |
| `pwm_ramp_protocol.html` | PWM ramp protocol visualization |
| `test_ramp_visualization.html` | Comprehensive ramp easing mode tests |

## Viewing

Open any HTML file in a web browser to view the interactive visualization:
- Real-time status indicator
- Channel timelines with square waves and gradients
- Intensity plots for PWM/RAMP patterns
- Click to jump to specific positions

## Regenerating

To regenerate visualizations from protocol files:
```bash
python viz_protocol_html.py examples/1min_test.txt -o examples/sample_outputs/1min_test.html
```
