# Calibration Methods - User Guide

## Overview

The Light Controller system now supports two calibration methods:

1. **V2 (Recommended)** - Multi-timestamp method ⚡ Fast & Accurate
2. **V1 (Legacy)** - Original method 🐢 Slower but backward compatible

## Quick Comparison

| Feature | V2 (Improved) | V1 (Original) |
|---------|---------------|---------------|
| **Duration** | 60 seconds | 150 seconds |
| **Accuracy** | Higher (removes serial overhead) | Good |
| **Data points** | 11 timestamps | 3 intervals |
| **Diagnostics** | RMSE, max error, stability | R² only |
| **Speed** | ⚡ **2.5x faster** | Slower |
| **Status** | ✅ **Recommended** | Backward compatible |

## Using V2 Calibration (Recommended)

### Method 1: Using LightControllerParser

```python
from light_controller_parser import LightControllerParser

# Create parser and setup serial
parser = LightControllerParser('protocol.xlsx')
parser.setup_serial(board_type='Arduino', baudrate=9600)

# Calibrate using v2 method (default)
parser.calibrate(use_v2=True)  # 60 seconds, more accurate

# Or use v1 method for backward compatibility
# parser.calibrate(use_v2=False)  # 150 seconds, original method
```

### Method 2: Using lcfunc directly

```python
from lcfunc import CalibrateArduinoTime_v2, SetUpSerialPort

# Setup serial connection
ser = SetUpSerialPort(board_type='Arduino', baudrate=9600)

# Run v2 calibration
result = CalibrateArduinoTime_v2(ser, duration=60, num_samples=10)

# Access results
print(f"Calibration factor: {result['calib_factor']:.6f}")
print(f"RMSE: {result['rmse']*1000:.2f} ms")
print(f"Max error: {result['max_error']*1000:.2f} ms")
print(f"Timing stable: {result['timing_stable']}")
```

### Customizing V2 Calibration

```python
# Faster calibration (30 seconds, 5 samples)
result = CalibrateArduinoTime_v2(ser, duration=30, num_samples=5)

# More accurate calibration (120 seconds, 20 samples)
result = CalibrateArduinoTime_v2(ser, duration=120, num_samples=20)

# Without countdown timer
result = CalibrateArduinoTime_v2(ser, duration=60, num_samples=10, use_countdown=False)
```

## Using V1 Calibration (Legacy)

```python
from lcfunc import CalibrateArduinoTime

# Original method with default timing
result = CalibrateArduinoTime(ser, t_send=[40, 50, 60], use_v2=False)

# Custom timing intervals
result = CalibrateArduinoTime(ser, t_send=[30, 60, 90], use_v2=False)
```

## Understanding V2 Output

### Sample Output

```
======================================================================
Calibration Results (v2):
======================================================================
Calibration factor: 1.000131
Time offset: 0.052 seconds
R-squared: 0.999998
RMSE: 15.23 ms
Max error: 28.45 ms
Timing stable: ✓ Yes
Correction per 12 hours: 5.65 seconds
======================================================================
```

### Metrics Explained

- **Calibration factor**: Timing correction multiplier
  - `1.000131` means Arduino runs 0.0131% slower than system clock
  - Used to correct all time values in protocol

- **Time offset**: Communication overhead (typically 50-100ms)
  - Constant delay from serial communication
  - Removed from timing calculations

- **R-squared**: Goodness of linear fit (0-1)
  - Values > 0.999 indicate excellent timing consistency
  - Values < 0.99 suggest timing instability

- **RMSE**: Root Mean Square Error
  - Average timing deviation in milliseconds
  - Good: < 50ms, Excellent: < 20ms

- **Max error**: Largest timing deviation
  - Should be < 500ms for stable timing
  - Higher values indicate USB/system issues

- **Timing stable**: Overall stability assessment
  - ✓ Yes: Max error < 500ms (reliable)
  - ✗ No: High jitter detected (may need recalibration)

## Troubleshooting

### Warning: High timing jitter detected

```
⚠️  Warning: High timing jitter detected!
   Max error of 650ms exceeds 500ms threshold.
   Consider running calibration again or checking USB connection.
```

**Solutions:**
1. **Reconnect USB cable** - Try different USB port
2. **Close other applications** - Reduce CPU load
3. **Use USB 2.0 port** - Some USB 3.0 ports have higher latency
4. **Run longer calibration** - Use 120 seconds instead of 60
5. **Check power supply** - Ensure Arduino has stable power

### Arduino not responding

**Check:**
- Arduino is properly connected
- Correct serial port selected
- Arduino firmware uploaded correctly
- Board type matches (Arduino vs Arduino Due)

### Calibration factor seems wrong

**Typical values:**
- Normal range: 0.999 - 1.001 (±0.1%)
- Outside range: Check crystal oscillator or temperature

**If factor is exactly 1.000000:**
- Warning will appear (uncalibrated)
- Protocol uses Arduino timer without correction
- Run calibration before experiment

## Best Practices

### 1. When to Calibrate

✅ **Always calibrate before:**
- Important experiments requiring precise timing
- Long-duration protocols (hours/days)
- Temperature-sensitive applications

❌ **Can skip calibration for:**
- Quick tests or debugging
- Timing precision not critical (>1% tolerance)
- Using pre-calibrated factor from same setup

### 2. Calibration Frequency

- **Daily**: For critical experiments
- **Weekly**: For regular use
- **After changes**: New Arduino, USB port, or computer
- **Temperature change**: If environment varies >10°C

### 3. Environmental Factors

**Temperature**: Crystal frequency changes with temperature
- Store calibration factor if temperature stable
- Recalibrate if environment changes

**USB Connection**: Different ports may have different latency
- Use same USB port for calibration and experiment
- Avoid USB hubs if possible

## Advanced Usage

### Adaptive Calibration

```python
def smart_calibrate(ser):
    """Automatically use longer calibration if timing is unstable."""
    # Quick test
    result = CalibrateArduinoTime_v2(ser, duration=30, num_samples=5)
    
    if result['timing_stable']:
        return result
    else:
        print("⚠️ Timing unstable, running extended calibration...")
        return CalibrateArduinoTime_v2(ser, duration=120, num_samples=20)
```

### Calibration Caching

```python
import json
import time
import os

def get_or_calibrate(ser, cache_file='calibration_cache.json', max_age_hours=24):
    """Load cached calibration or run new calibration if expired."""
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cache = json.load(f)
        
        age_hours = (time.time() - cache['timestamp']) / 3600
        if age_hours < max_age_hours:
            print(f"Using cached calibration (age: {age_hours:.1f} hours)")
            return cache['calib_factor']
    
    # Run calibration
    print("Running new calibration...")
    result = CalibrateArduinoTime_v2(ser)
    
    # Cache result
    cache = {
        'calib_factor': result['calib_factor'],
        'timestamp': time.time(),
        'r_squared': result['r_squared'],
        'rmse': result['rmse'],
        'max_error': result['max_error']
    }
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)
    
    return result['calib_factor']
```

### Comparing Methods

```python
# Test both methods and compare
from test_calibration_methods import main

# Run comprehensive comparison
main()
```

## Migration from V1 to V2

### Code Changes

**Before (V1):**
```python
parser.calibrate()  # Uses v1 by default (old version)
```

**After (V2):**
```python
parser.calibrate(use_v2=True)  # Uses v2 (recommended)
```

### No Breaking Changes

- V1 method still available via `use_v2=False`
- Existing code continues to work
- Gradually migrate to v2 for better performance

### Backward Compatibility

The v2 method returns data compatible with v1:
```python
result = {
    'calib_factor': 1.000131,
    'cost': 0.052,  # 'offset' renamed to 'cost' for compatibility
    'r_squared': 0.999998,
    # Plus additional v2-specific metrics
    'rmse': 0.01523,
    'max_error': 0.02845,
    'timing_stable': True
}
```

## Technical Details

### V2 Method Overview

1. **Single command sent**: `calibrate_timestamps_60_10`
2. **Arduino reports timestamps**: 11 timestamps over 60 seconds
3. **Python records arrival times**: System clock when each timestamp received
4. **Linear regression**: Fit Arduino time vs Python time
5. **Quality metrics**: Calculate RMSE, max error, stability

### Why V2 is Better

**Problem with V1**: Each measurement includes serial overhead
```
Message 1: [send delay] + Arduino(40s) + [receive delay] = ~40.05s
Message 2: [send delay] + Arduino(50s) + [receive delay] = ~50.05s
Message 3: [send delay] + Arduino(60s) + [receive delay] = ~60.05s
```
Serial delays (~50ms) add noise to each measurement.

**Solution in V2**: One command, multiple timestamps
```
Send once: [send delay]
Timestamp 1: Arduino reports 0ms
Timestamp 2: Arduino reports 6000ms
...
Timestamp 11: Arduino reports 60000ms
Final: [receive delay]
```
Serial overhead only affects offset, not slope (calibration factor).

### Arduino Implementation

The v2 method uses non-blocking timing:
```cpp
// Instead of busy-wait loop:
while (duration < time) {
    duration = millis() - startTime;  // Wastes CPU
}

// V2 uses smart waiting:
while (millis() < targetTime) {
    if (targetTime - millis() > 10) {
        delay(5);  // Long wait: sleep
    } else {
        delayMicroseconds(100);  // Near target: precise timing
    }
}
```

Benefits:
- Lower CPU usage
- More consistent timing
- Can handle other tasks during calibration

## FAQ

**Q: Is v2 more accurate than v1?**
A: Yes, v2 removes per-message serial overhead and uses more data points.

**Q: Should I switch to v2 immediately?**
A: Recommended, but not required. V1 still works fine for most applications.

**Q: Can I use v1 and v2 on the same Arduino?**
A: Yes, both methods are supported simultaneously.

**Q: How much faster is v2?**
A: 2.5x faster (60s vs 150s default), with better accuracy.

**Q: What if I get timing instability warnings?**
A: Try longer calibration, different USB port, or reduce system load.

**Q: Does v2 require new Arduino firmware?**
A: Yes, upload the updated firmware. V1 continues to work if you don't update.

**Q: Can I revert to v1?**
A: Yes, use `calibrate(use_v2=False)` or keep old firmware.

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review Arduino serial monitor for error messages
3. Try `test_calibration_methods.py` to compare methods
4. Check `CALIBRATION_REVIEW.md` for technical details
