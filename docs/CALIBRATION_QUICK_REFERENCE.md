# Calibration Methods - Quick Reference

## Choose Your Calibration Method

### 🏆 V2 (RECOMMENDED) - Most Accurate
```python
parser = LightControllerParser('protocol.xlsx', calibration_method='v2')
```
- **Duration**: 180 seconds (3 minutes)
- **Samples**: 9 measurements (20s intervals)
- **Accuracy**: Best (~1.001013)
- **Best for**: Production, accurate timing critical
- **Note**: Excludes t=0 initialization overhead

### ⚡ V1.1 (NEW) - Active Wait
```python
parser = LightControllerParser('protocol.xlsx', calibration_method='v1.1')
```
- **Duration**: ~150 seconds (2.5 minutes)
- **Samples**: 4 measurements [30,40,50,60]s
- **Accuracy**: Good (~1.001200)
- **Best for**: When you want V1 accuracy with better responsiveness
- **Note**: Python actively polls for response

### 📦 V1 (ORIGINAL) - Backward Compatible
```python
parser = LightControllerParser('protocol.xlsx', calibration_method='v1')
```
- **Duration**: ~150 seconds (2.5 minutes)
- **Samples**: 4 measurements [30,40,50,60]s
- **Accuracy**: Good (~1.001200)
- **Best for**: Backward compatibility, legacy systems
- **Note**: Uses dead sleep (less responsive)

---

## Full Workflow Example

```python
from light_controller_parser import LightControllerParser

# 1. Initialize parser with calibration method
parser = LightControllerParser(
    'examples/example_protocol.xlsx',
    pattern_length=2,
    calibration_method='v2'  # Choose: 'v1', 'v1.1', or 'v2'
)

# 2. Setup serial connection (includes pattern length validation)
parser.setup_serial(
    board_type='Arduino',
    baudrate=9600,
    verify_pattern_length=True  # Recommended: catches config issues early
)

# 3. Run calibration
calib_factor = parser.calibrate()
print(f"Calibration factor: {calib_factor:.6f}")

# 4. Generate and validate commands (includes pattern capacity check)
parser.generate_pattern_commands()  # Validates pattern count automatically
parser.generate_wait_commands()

# 5. Preview commands (optional)
parser.preview(show_wait=True, show_patterns=True, max_commands=10)

# 6. Send to Arduino
parser.send_commands()
```

---

## Pattern Capacity Validation

### Automatic Validation (Recommended)
Pattern count is automatically validated when you call `generate_pattern_commands()`:

```python
parser.setup_serial(verify_pattern_length=True)  # Gets Arduino config
parser.generate_pattern_commands()  # ← Validation happens here
```

### What It Checks
- ✅ Number of patterns per channel
- ✅ Compares against Arduino `MAX_PATTERN_NUM`
- ✅ Raises error before execution if capacity exceeded
- ✅ Shows which channels have problems

### Example Success Output
```
📊 Pattern count per channel:
   Channel 0: 4 patterns (Arduino max: 6) ✓
   Channel 1: 3 patterns (Arduino max: 6) ✓
```

### Example Failure Output
```
❌ ERROR: Pattern count exceeds Arduino capacity!
  Channel 0: 8 patterns (max: 6)
  
Solutions:
  1. Increase MAX_PATTERN_NUM in Arduino firmware to 8+
  2. Simplify the protocol (fewer patterns)
  3. Combine similar patterns
```

---

## Direct Function Usage

### Call Calibration Functions Directly
```python
from lcfunc import (
    CalibrateArduinoTime,           # V1
    CalibrateArduinoTime_v11,       # V1.1 (NEW)
    CalibrateArduinoTime_v2_improved  # V2 (UPDATED)
)

# V1 - Original method
result = CalibrateArduinoTime(ser, t_send=[30,40,50,60], use_v2=False)

# V1.1 - Active wait method
result = CalibrateArduinoTime_v11(ser, t_send=[30,40,50,60])

# V2 - Multi-timestamp method (improved)
result = CalibrateArduinoTime_v2_improved(ser, duration=180, num_samples=9)

# All return dict with:
#   - calib_factor: Calibration factor
#   - offset: Communication delay offset
#   - r_squared: Goodness of fit
#   - (plus method-specific data)
```

---

## Calibration Factor Interpretation

### What is a Calibration Factor?
The calibration factor corrects for clock speed differences between Python and Arduino.

**Formula**: `corrected_time = requested_time × calib_factor`

### Typical Values
- **1.001200**: Python runs ~0.12% faster than Arduino
  - Over 12 hours: 5.2 seconds error without calibration
  - Over 24 hours: 10.4 seconds error without calibration

- **1.000000**: No correction needed (perfect match)
  - ⚠️ Warning: Likely uncalibrated, not a real measurement

- **0.998800**: Python runs ~0.12% slower than Arduino
  - Over 12 hours: 5.2 seconds error in opposite direction

### Why All Methods Should Agree
All three methods measure the same thing (Python vs reference time), so factors should be within 0.1% of each other. If not:
- 🔴 Check for clock drift issues
- 🔴 Verify serial communication stability
- 🔴 Ensure Arduino isn't doing other tasks during calibration

---

## Common Issues & Solutions

### Issue: "Timeout waiting for response"
**Cause**: Arduino not responding to calibration command
**Solution**:
1. Check Arduino firmware has calibration handler
2. Verify serial connection is stable
3. Ensure baud rate matches (9600)
4. Check no other programs are using the port

### Issue: "Pattern count exceeds capacity"
**Cause**: Protocol has too many patterns for Arduino
**Solution**:
1. Increase `MAX_PATTERN_NUM` in Arduino firmware
2. Simplify protocol (reduce pattern complexity)
3. Use longer `pattern_length` to compress patterns

### Issue: "Pattern length mismatch"
**Cause**: Protocol needs more pattern length than Arduino supports
**Solution**:
1. Increase `PATTERN_LENGTH` in Arduino firmware
2. Re-upload firmware to Arduino
3. Run `setup_serial(verify_pattern_length=True)` to confirm

### Issue: Calibration factors differ between methods
**Cause**: System timing instability or communication issues
**Check**:
- Clock drift in system (use NTP sync)
- Serial buffer overflow (reduce baud rate)
- Arduino timing instability (check for interrupts)
- Consistent environment (no heavy CPU load during calibration)

---

## Performance Comparison

| Method | Duration | Samples | RMSE | Responsiveness | Accuracy |
|--------|----------|---------|------|----------------|----------|
| V1     | 150s     | 4       | 3-5ms| Low            | Good     |
| V1.1   | 150s     | 4       | 3-5ms| High           | Good     |
| V2     | 180s     | 9       | <2ms | Highest        | **Best** |

**Recommendation**: Use V2 unless you need shorter calibration time

---

## Testing Your Implementation

Run the comprehensive test suite:
```bash
python test_calibration_integration.py
```

This tests:
- ✅ All three calibration methods
- ✅ LightControllerParser integration
- ✅ Pattern capacity validation
- ✅ Calibration consistency (all methods agree)

Expected output:
```
✅ PASSED: Individual Functions
✅ PASSED: Parser Methods
✅ PASSED: Pattern Validation
✅ PASSED: Calibration Consistency

🎉 ALL TESTS PASSED!
```

---

## When to Recalibrate

Recalibrate when:
- 🔄 Arduino firmware updated
- 🔄 Different Arduino board used
- 🔄 Computer/OS updated (clock source may change)
- 🔄 Temperature changes significantly
- 🔄 Running long protocols (>24 hours)
- 🔄 Timing accuracy critical (< 1 second tolerance)

Don't need to recalibrate:
- ✅ Same hardware, same environment
- ✅ Short protocols (< 1 hour, drift negligible)
- ✅ Timing not critical (tolerance > 10 seconds)

---

## Advanced Usage

### Custom Test Times (V1/V1.1 only)
```python
parser.calibrate(t_send=[20, 30, 40, 50, 60, 70])  # More samples
parser.calibrate(t_send=[60, 120, 180])            # Longer intervals
```

### Custom V2 Duration
```python
from lcfunc import CalibrateArduinoTime_v2_improved
result = CalibrateArduinoTime_v2_improved(ser, duration=300, num_samples=15)
```

### Disable Countdown Timer
```python
result = CalibrateArduinoTime_v11(ser, use_countdown=False)
result = CalibrateArduinoTime_v2_improved(ser, use_countdown=False)
```

### Override Method at Runtime
```python
parser = LightControllerParser('protocol.xlsx', calibration_method='v1')
parser.setup_serial()
parser.calibrate(use_v2=True)  # Forces V2 despite initialization
```

---

## Need Help?

- 📖 Full documentation: `docs/CALIBRATION_INTEGRATION_SUMMARY.md`
- 🧪 Test suite: `test_calibration_integration.py`
- 🔬 Debug script: `debug_calibration_speed_test.py`
- 📝 Change log: `docs/CHANGELOG.md`

---

**Last Updated**: Implementation Complete
**Status**: ✅ Production Ready
**Backward Compatible**: ✅ Yes
