# Calibration Method Selection Guide

## Overview

The Light Controller now supports two calibration methods:

- **V2 (Multi-Timestamp)**: New improved method - faster and more accurate
- **V1 (Original)**: Original method - for backward compatibility

## Quick Start

### Using in Code

```python
from light_controller_parser import LightControllerParser

# Use V2 method (recommended - default)
parser = LightControllerParser('protocol.xlsx', calibration_method='v2')
parser.setup_serial()
parser.parse_and_execute()

# Use V1 method (original)
parser = LightControllerParser('protocol.xlsx', calibration_method='v1')
parser.setup_serial()
parser.parse_and_execute()
```

### Testing Both Methods

To compare both methods on your hardware:

```bash
python test_calibration_comparison.py
```

This script will:
1. Run V1 calibration
2. Run V2 calibration
3. Compare the results (factor, time, accuracy)

## Method Comparison

| Feature | V1 (Original) | V2 (Multi-Timestamp) |
|---------|---------------|----------------------|
| **Duration** | ~150 seconds | ~60 seconds |
| **Speed** | Slower | **2.5× faster** |
| **Data Points** | 3-4 intervals | 10+ timestamps |
| **Accuracy** | Good | **Better** |
| **Serial Overhead** | Included in each measurement | Only affects offset |
| **Statistics** | R² only | R², RMSE, max error, stability |
| **Implementation** | Busy-wait delays | Non-blocking delays |

## When to Use Each Method

### Use V2 (Recommended)
- ✅ For all new protocols
- ✅ When you want faster calibration
- ✅ When you need detailed quality metrics
- ✅ For long-running experiments (better accuracy matters)

### Use V1 (Legacy)
- Use when you need exact backward compatibility
- Use if you're comparing with old data
- Use for troubleshooting V2 implementation

## Example: Manual Calibration

You can also manually trigger calibration:

```python
# Create parser
parser = LightControllerParser('protocol.xlsx', calibration_method='v2')
parser.setup_serial()

# Run calibration explicitly
calib_factor = parser.calibrate()
print(f"Calibration factor: {calib_factor}")

# Continue with protocol execution
parser.parse_and_execute()
```

## Example: Override Method per Call

```python
# Initialize with V2 as default
parser = LightControllerParser('protocol.xlsx', calibration_method='v2')
parser.setup_serial()

# But use V1 for this specific calibration
calib_factor = parser.calibrate(use_v2=False)
```

## Arduino Firmware Requirements

The V2 method requires the updated Arduino firmware that includes the `calibrate_timestamps()` function. Make sure you've uploaded the latest `light_controller_v2_2_arduino.ino` to your Arduino.

### Checking Arduino Version

The greeting message will show the firmware capabilities:
```
LIGHT_CONTROLLER: Arduino Uno [8 channels] (v2.2)
```

## Troubleshooting

### V2 Times Out
- Ensure you have the latest Arduino firmware uploaded
- Check USB connection stability
- Try V1 method as fallback

### Different Results Between Methods
- Small differences (< 0.1%) are normal due to timing jitter
- Larger differences may indicate USB connection issues
- Run calibration multiple times and average the results

### Best Practices
1. Run calibration in a stable environment (no heavy CPU load)
2. Use USB ports directly on computer (avoid hubs if possible)
3. Close other programs that might use serial ports
4. For critical experiments, run calibration multiple times and verify consistency

## Technical Details

### V1 Algorithm
1. Send command: `calibrate_40000` (wait 40s)
2. Python measures elapsed time
3. Repeat for 60s, 80s, 100s
4. Linear regression: `python_time = factor × requested_time + offset`

### V2 Algorithm
1. Send command: `calibrate_timestamps_60_10`
2. Arduino sends 11 timestamps over 60 seconds
3. Python records when each arrives
4. Linear regression: `python_time = factor × arduino_time + offset`
5. Calculate RMSE, max error, stability metrics

### Key Advantage of V2
Serial communication latency affects each V1 measurement (50ms × 4 = 200ms overhead). In V2, latency only affects the offset, not the slope (calibration factor), resulting in more accurate measurements.

## Migration Path

If you're currently using V1 and want to switch to V2:

1. **Upload new Arduino firmware** (if not done already)
2. **Test V2 works**: Run `test_calibration_comparison.py`
3. **Verify results match**: Both methods should give similar factors (< 0.1% difference)
4. **Update your code**: Change `calibration_method='v1'` to `calibration_method='v2'`
5. **Enjoy faster calibration!**

## Questions?

- Check `CALIBRATION_REVIEW.md` for technical analysis
- Check `CALIBRATION_GUIDE.md` for detailed user guide
- Compare methods using `test_calibration_comparison.py`
