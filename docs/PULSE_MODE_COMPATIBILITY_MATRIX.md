# Pulse Mode Compatibility Matrix

## Quick Reference

| Arduino Mode | Protocol Type | Result | Memory Impact | Message |
|--------------|--------------|--------|---------------|---------|
| **PULSE_MODE_COMPILE=0** | No Pulse | ✅ PASS | Optimized (-2.5KB) | "Compatible" |
| **PULSE_MODE_COMPILE=0** | Has Pulse | ❌ FAIL | N/A | "ERROR: Incompatibility" |
| **PULSE_MODE_COMPILE=1** | No Pulse | ⚠️ PASS | Wasted (+2.5KB) | "Compatible but not needed" |
| **PULSE_MODE_COMPILE=1** | Has Pulse | ✅ PASS | Required | "Compatible" |

## Decision Tree

```
Protocol has pulse columns?
│
├─ NO (no pulse columns)
│  │
│  └─ Arduino PULSE_MODE_COMPILE?
│     │
│     ├─ 0 (disabled) → ✅ OPTIMAL: Works, memory saved
│     └─ 1 (enabled)  → ⚠️ OK: Works, but wastes 2.5KB
│
└─ YES (has pulse columns)
   │
   └─ Arduino PULSE_MODE_COMPILE?
      │
      ├─ 0 (disabled) → ❌ ERROR: Won't work, must recompile
      └─ 1 (enabled)  → ✅ OPTIMAL: Works with full support
```

## Recommendation Logic

### If Your Protocol Never Uses Pulses
```cpp
#define PULSE_MODE_COMPILE 0  // ← Use this
```
- ✅ Saves 2,560 bytes of RAM
- ✅ Optimal for memory-constrained applications
- ✅ No functionality loss if pulses not needed

### If Your Protocol Sometimes Uses Pulses
```cpp
#define PULSE_MODE_COMPILE 1  // ← Use this
```
- ✅ Full pulse support available
- ⚠️ Uses 2,560 bytes extra RAM
- ✅ Compatible with all protocols

### If You Use Multiple Protocols
**Option A: Use PULSE_MODE_COMPILE=1 (Safest)**
- Works with all protocols
- Minor memory overhead

**Option B: Use PULSE_MODE_COMPILE=0 + Multiple Firmware Versions**
- Maintain two firmware versions
- Flash appropriate one for each protocol
- Maximum memory optimization

## Testing Checklist

- [ ] Test no-pulse protocol with PULSE_MODE_COMPILE=0 → Should PASS
- [ ] Test no-pulse protocol with PULSE_MODE_COMPILE=1 → Should PASS with warning
- [ ] Test pulse protocol with PULSE_MODE_COMPILE=0 → Should FAIL with error
- [ ] Test pulse protocol with PULSE_MODE_COMPILE=1 → Should PASS
- [ ] Verify memory difference is ~2.5KB between modes
- [ ] Verify warning message appears when pulse enabled but not needed
- [ ] Verify error message appears when pulse needed but disabled

## Common Questions

**Q: Will my no-pulse protocol break if I use PULSE_MODE_COMPILE=1?**  
A: No, it will work fine. You'll just use ~2.5KB more RAM.

**Q: Can I change pulse mode at runtime?**  
A: No, this is compile-time only. You must recompile and upload firmware to change.

**Q: How do I know what my current pulse mode is?**  
A: The Python script will report it during the "Arduino Memory" check.

**Q: What happens if I try to use pulses with PULSE_MODE_COMPILE=0?**  
A: Python will detect the incompatibility and show a clear error message with instructions.

**Q: Should I always use PULSE_MODE_COMPILE=1 to be safe?**  
A: If you have plenty of RAM (>20KB free), yes. If RAM is tight, use 0 for no-pulse protocols.

## Example Test Commands

```bash
# Interactive test (recommended for first time)
python test_pulse_compatibility.py --port /dev/cu.usbmodem14101

# Automated test
python test_pulse_compatibility.py --port COM3 --auto

# Test specific protocol
python -m light_controller_parser examples/example_no_pulse_protocol.txt --port /dev/cu.usbmodem14101
```

## Memory Calculation

For Arduino Due (96KB RAM) with typical configuration:
- MAX_CHANNEL_NUM = 8
- MAX_PATTERN_NUM = 10  
- PATTERN_LENGTH = 4

```
Pulse arrays size = 2 arrays × 4 bytes × 8 channels × 10 patterns × 4 steps
                  = 2 × 4 × 8 × 10 × 4
                  = 2,560 bytes
                  ≈ 2.5 KB
```

This is approximately **2.7% of total RAM** on Arduino Due.
