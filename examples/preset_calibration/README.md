# Preset Calibration Examples

This folder contains protocol examples using the **legacy manual calibration approach** with `CALIBRATION_FACTOR` specified directly in protocol files.

## ⚠️ Legacy Approach - Backward Compatible

These examples demonstrate the **old style** of calibration management where you manually specify the calibration factor in each protocol file:

```
CALIBRATION_FACTOR: 1.000000
```

### When to Use This Approach

✅ **Use manual CALIBRATION_FACTOR when:**
- Working with shared protocol files that must work on any Arduino without database
- Protocols designed for specific pre-calibrated hardware setups
- Distributing protocols to users without access to calibration database
- Reproducing exact experiments with known calibration factors
- Backward compatibility with older protocol files

❌ **Avoid manual CALIBRATION_FACTOR when:**
- Working with multiple Arduino boards regularly
- Developing new protocols (use auto-calibration instead)
- You want simplified workflow without manual tracking

## ⚠️ IMPORTANT: Calibration Factors are Board-Specific

**Each Arduino board requires its own unique calibration factor.**

### Why Calibration is Board-Specific

Even "identical" Arduino boards from the same manufacturer have different timing characteristics due to:

1. **Crystal Oscillator Tolerances**
   - Standard crystals: ±50-100 ppm (parts per million) tolerance
   - For a 16 MHz crystal: ±800-1600 Hz variation
   - Real-world measurement: 0.1-1.0% timing difference between boards

2. **Temperature-Dependent Drift**
   - Crystal frequency changes with temperature (~±30 ppm/°C)
   - Room temperature variations (20-25°C) cause measurable drift
   - Operating temperature (Arduino self-heating) adds additional variation

3. **Manufacturing Variations**
   - Crystal load capacitance varies between boards
   - PCB trace capacitance affects oscillator frequency
   - Component tolerances in oscillator circuit

4. **Component Aging**
   - Crystals age over time (typically +1 to +5 ppm per year)
   - Long-term protocols may require recalibration

5. **Clone vs. Genuine Arduino**
   - Clone boards may use different crystal specifications
   - Alternative oscillator circuits (e.g., ceramic resonators)
   - Can have >1% timing differences from genuine boards

### Real-World Example

**Board A (Genuine Arduino Due):**
- Measured timing: 59.987 seconds for 60-second wait
- Calibration factor: 1.000217 (Arduino slightly fast)

**Board B (Clone Arduino Due):**
- Measured timing: 60.045 seconds for 60-second wait
- Calibration factor: 0.999251 (Arduino slightly slow)

**Difference:** 0.097% timing error if using wrong calibration

Over a 10-hour protocol:
- Board A with Board B's calibration: **35 seconds error**
- Board B with Board A's calibration: **35 seconds error**

**⚠️ Using the wrong calibration factor can cause significant timing drift in long protocols!**

### Best Practices

✅ **Do:**
- Calibrate each Arduino board individually
- Store calibration factor with board label (e.g., "Arduino_Due_#1: 1.025847")
- Use consistent CALIBRATION_FACTOR in protocol file for specific board
- Recalibrate if board behavior changes or after firmware updates

❌ **Don't:**
- Copy calibration factors between different boards
- Assume "same model" boards have identical timing
- Use factory default (1.000000) for precision timing
- Share calibrated protocols without noting which board was used

### Why Manual CALIBRATION_FACTOR Can Be Problematic

The manual approach requires:
1. **Manual Tracking:** Maintain spreadsheet of board IDs and calibration factors
2. **Error-Prone:** Easy to use wrong factor with wrong board
3. **File Management:** Update all protocol files when switching boards
4. **Sharing Issues:** Recipients must recalibrate for their hardware

**Solution:** Use automatic calibration (see `auto_calibration/` folder) which:
- Automatically identifies each Arduino board
- Stores calibration per board in database
- Prevents using wrong calibration factor
- Eliminates manual tracking

## How Manual Calibration Works

1. **Calibrate Your Specific Arduino:**
   - Connect your Arduino to computer
   - Run calibration (takes ~5 minutes, default 300s)
   - Note the calibration factor (e.g., 1.025847)
   - **Label your Arduino board** with its ID and factor

2. **Add to Protocol File:**
   - Add `CALIBRATION_FACTOR: 1.025847` to your protocol file
   - **Document which board this protocol is calibrated for**
   - This factor is now locked to this protocol file

3. **Priority:**
   - When a protocol file contains `CALIBRATION_FACTOR`, it takes **highest priority**
   - Overrides automatic calibration database
   - Ensures consistent timing **only if used with the correct board**

4. **Backward Compatible:**
   - All existing protocol files with `CALIBRATION_FACTOR` continue to work
   - No migration needed unless you want to use automatic calibration

## Examples in This Folder

| File | Description | Pattern Length |
|------|-------------|----------------|
| `basic_protocol.txt` | Simple channel control examples | 4 |
| `simple_blink_example.txt` | ON/OFF blink patterns | 2 |
| `pulse_protocol.txt` | Pulsed light patterns (various frequencies) | 4 |
| `wait_pulse_protocol.txt` | Wait status with pulse during delays | 4 |
| `pattern_length_4_example.txt` | Complex 4-element patterns | 4 |
| `test_8_channels_pattern_length_4.txt` | All 8 channels with 4-element patterns | 4 |

*Note: Excel (.xlsx) versions are also available for each protocol.*

## ⚠️ Warning When Using These Files

When you run these protocol files, you'll see a warning message:

```
================================================================================
⚠️  OUTDATED PRACTICE DETECTED: Manual CALIBRATION_FACTOR in protocol file
================================================================================
Found: CALIBRATION_FACTOR: 1.000000

This protocol file uses the old manual calibration approach.
While this still works (backward compatible), consider upgrading to
automatic calibration for easier management:

BENEFITS OF AUTOMATIC CALIBRATION:
  • No manual calibration factor management
  • Automatic board identification (serial number/VID/PID)
  • Per-board calibration storage in database
  • Seamless multi-board support
  • Eliminates manual tracking errors
...
================================================================================
```

This is **informational only** - the protocol will still execute correctly using the specified calibration factor.

## Migrating to Automatic Calibration

To upgrade these protocols to use automatic calibration:

1. **Remove the CALIBRATION_FACTOR line:**
   ```diff
   - CALIBRATION_FACTOR: 1.000000
   ```

2. **Save to auto_calibration/ folder** (optional, for organization)

3. **Run the protocol:**
   ```bash
   python protocol_parser.py 4 /dev/cu.usbmodem14301 protocol.txt
   ```

4. **Calibrate when prompted** (first time only):
   ```
   Arduino not calibrated. Calibrate now? (Y/n): y
   ```

5. **Future runs** automatically use stored calibration - no prompts!

## Related Documentation

- **Automatic Calibration:** [../auto_calibration/README.md](../auto_calibration/README.md)
- **Complete Auto-Calibration Guide:** [../../docs/AUTO_CALIBRATION_DATABASE.md](../../docs/AUTO_CALIBRATION_DATABASE.md)
- **Backward Compatibility Details:** [../../docs/BACKWARD_COMPATIBILITY.md](../../docs/BACKWARD_COMPATIBILITY.md)
- **Protocol Format Reference:** [../QUICK_REFERENCE.md](../QUICK_REFERENCE.md)

## Support

For questions about calibration approaches or migration:
1. See [../../docs/BACKWARD_COMPATIBILITY.md](../../docs/BACKWARD_COMPATIBILITY.md) for detailed scenarios
2. Test board identification: `python test_board_info.py`
3. View stored calibrations: `python utils/manage_calibrations.py list`
