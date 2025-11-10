# Protocol Examples Quick Reference Card

## File Selection Guide

| If you want... | Use this file | Run with |
|----------------|---------------|----------|
| Simple ON/OFF blink | `pattern_length_2_example.txt` | `python protocol_parser.py 2` |
| Excel 2-state patterns | `pattern_length_2_example.xlsx` | `python protocol_parser.py 2` |
| 4-phase sequences | `pattern_length_4_example.txt` | `python protocol_parser.py 4` |
| Excel 4-phase patterns | `pattern_length_4_example.xlsx` | `python protocol_parser.py 4` |
| Learn TXT syntax | `basic_protocol.txt` | `python protocol_parser.py` |
| Learn Excel format | `basic_protocol.xlsx` | `python protocol_parser.py` |
| Pulse examples | `pulse_protocol.txt/.xlsx` | `python protocol_parser.py` |
| Wait period demo | `wait_pulse_protocol.txt/.xlsx` | `python protocol_parser.py` |

## Pattern Length Decision Tree

```
┌─ Start: What's your protocol structure?
│
├─ Simple ON/OFF alternation?
│  └─ YES → Use pattern_length=2
│     └─ Files: pattern_length_2_example.*
│
├─ Has 4 distinct phases/steps?
│  └─ YES → Use pattern_length=4
│     └─ Files: pattern_length_4_example.*
│
├─ Has 8+ step cycles?
│  └─ YES → Use pattern_length=8 or higher
│     └─ Create custom protocol
│
└─ Irregular/random?
   └─ Use pattern_length=1 or 2
      └─ Won't compress well anyway
```

## Command Line Quick Reference

```bash
# Default (pattern_length=4)
python protocol_parser.py

# Optimal for 2-state patterns
python protocol_parser.py 2

# Optimal for 4-phase patterns
python protocol_parser.py 4

# Custom pattern length
python protocol_parser.py 8
```

## Expected Output Guide

### ✅ Success with Optimal Pattern Length

```
Compression efficiency analysis:
  pattern_length=2: 8 commands ← optimal ← given
  pattern_length=4: 16 commands

📏 Protocol pattern analysis:
   Required PATTERN_LENGTH: 2
   Arduino PATTERN_LENGTH:  2
   ✓ Verification passed
```

**Meaning:** Perfect! You're using the most efficient pattern_length.

### ⚠️ Success but Suboptimal

```
Compression efficiency analysis:
  pattern_length=2: 8 commands ← optimal
  pattern_length=4: 16 commands ← given

💡 Note: Given pattern_length=4 generates 16 commands
         Optimal pattern_length=2 generates 8 commands
         Using optimal would reduce commands by 50.0%
```

**Meaning:** Works, but consider switching to pattern_length=2 for better efficiency.

### ❌ Failure - Arduino Incompatible

```
📏 Protocol pattern analysis:
   Required PATTERN_LENGTH: 4
   Arduino PATTERN_LENGTH:  2

❌ ERROR: Pattern length exceeds Arduino capability!
```

**Solution:** Update Arduino firmware `PATTERN_LENGTH` constant to 4.

## File Format Quick Reference

### TXT Format

```txt
# Pattern command (2 elements)
PATTERN:1;CH:1;STATUS:1,0;TIME_MS:1000,2000;REPEATS:10;PULSE:T0pw0,T0pw0

# Pattern command (4 elements)
PATTERN:1;CH:1;STATUS:1,0,1,0;TIME_MS:500,500,1000,2000;REPEATS:5;PULSE:T200pw20,T0pw0,T1000pw100,T0pw0

# Start time
START_TIME: {'CH1': 10, 'CH2': '21:00:00'}

# Wait status
WAIT_STATUS: {'CH1': 1, 'CH2': 0}

# Calibration (1.000000 = uncalibrated, typical calibrated: 1.0 ± 0.01)
CALIBRATION_FACTOR: 1.000000
```

### Excel Format

**Sheet 1: protocol**
```
| CH1_status | CH1_time_sec | CH1_period | CH1_pulse_width | CH2_status | ... |
|------------|--------------|------------|-----------------|------------|-----|
|     1      |      1       |     0      |        0        |     1      | ... |
|     0      |      1       |     0      |        0        |     0      | ... |
```

**Sheet 2: start_time**
```
| Channel     | CH1      | CH2      | CH3      |
|-------------|----------|----------|----------|
| start_time  | 21:00:00 | 21:00:00 | 21:00:00 |
| wait_status |    1     |    1     |    0     |
```

**Sheet 3: calibration**
```
| calibration_factor |
|--------------------|
|      1.000000      |
```

## Compression Examples

### Pattern Length = 2

**Input:** 60 rows of [ON, OFF, ON, OFF, ...]  
**Output:** 1-3 commands  
**Compression:** ~95-98% reduction  
**Best for:** Simple blink, ON/OFF alternation

### Pattern Length = 4

**Input:** 80 rows of [Phase1, Phase2, Phase3, Phase4, ...]  
**Output:** 1-3 commands  
**Compression:** ~95-98% reduction  
**Best for:** Traffic lights, breathing, multi-phase

## Arduino Memory Usage

| pattern_length | Bytes per pattern | Max patterns (96KB RAM) |
|----------------|-------------------|------------------------|
| 1 | 16 bytes | ~600 |
| 2 | 32 bytes | ~300 |
| 4 | 64 bytes | ~150 |
| 8 | 128 bytes | ~75 |
| 16 | 256 bytes | ~37 |

## Common Patterns

### Blink (pattern_length=2)
```txt
PATTERN:1;CH:1;STATUS:1,0;TIME_MS:1000,1000;REPEATS:20;PULSE:T0pw0,T0pw0
```
Meaning: ON 1s, OFF 1s, repeat 20 times

### Fast Pulse Blink (pattern_length=2)
```txt
PATTERN:1;CH:1;STATUS:1,0;TIME_MS:5000,5000;REPEATS:10;PULSE:T1000pw100,T0pw0
```
Meaning: Pulse at 1Hz for 5s, OFF 5s, repeat 10 times

### 4-Phase Warning (pattern_length=4)
```txt
PATTERN:1;CH:1;STATUS:1,0,1,0;TIME_MS:500,500,1000,2000;REPEATS:10;PULSE:T200pw20,T0pw0,T1000pw100,T0pw0
```
Meaning: Fast pulse 0.5s, pause 0.5s, slow pulse 1s, rest 2s, repeat 10 times

### Traffic Light (pattern_length=4)
```txt
PATTERN:1;CH:1;STATUS:1,1,1,0;TIME_MS:5000,2000,5000,1000;REPEATS:8;PULSE:T0pw0,T500pw250,T0pw0,T0pw0
```
Meaning: Green 5s, yellow 2s (flashing), red 5s, off 1s, repeat 8 times

## Troubleshooting Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| "Pattern length exceeds Arduino" | Update Arduino PATTERN_LENGTH and re-upload |
| "Suboptimal pattern_length" | Try the recommended pattern_length value |
| Too many commands | Use larger pattern_length or simplify protocol |
| Arduino crashes | Check PATTERN_LENGTH matches commands |
| No compression | Protocol may be too irregular |
| Wrong timing | Check CALIBRATION_FACTOR |

## Testing Workflow

```bash
# 1. Choose example based on your pattern type
cd examples/

# 2. Preview first (without hardware)
python ../preview_protocol.py pattern_length_2_example.txt -c 1.00131 -n 10

# 3. Check compression efficiency
# (Output shows optimal pattern_length)

# 4. Run with correct pattern_length
python ../protocol_parser.py 2

# 5. Select the file

# 6. Verify Arduino compatibility
# (System checks PATTERN_LENGTH automatically)

# 7. Upload and execute
# (If verification passes)
```

## Key Files Summary

| File | Type | Rows/Patterns | pattern_length | Best Use |
|------|------|---------------|----------------|----------|
| pattern_length_2_example.txt | TXT | 8 patterns | 2 | Learn 2-element patterns |
| pattern_length_2_example.xlsx | Excel | 60 rows | 2 | Excel 2-state compression |
| pattern_length_4_example.txt | TXT | 8 patterns | 4 | Learn 4-element patterns |
| pattern_length_4_example.xlsx | Excel | 80 rows | 4 | Excel 4-phase compression |
| basic_protocol.txt | TXT | 6 patterns | 2 | TXT syntax reference |
| basic_protocol.xlsx | Excel | 7 rows | 2 | Excel format reference |
| pulse_protocol.txt | TXT | Various | 2 | Pulse parameter examples |
| wait_pulse_protocol.txt | TXT | Various | 2 | Wait behavior examples |

## Learning Path

1. **Start:** Read `basic_protocol.txt` - Learn TXT syntax
2. **Next:** Try `pattern_length_2_example.txt` - Understand compression
3. **Then:** Explore `pattern_length_4_example.txt` - See complex patterns
4. **Excel:** Compare `.txt` vs `.xlsx` versions
5. **Advanced:** Create your own protocols
6. **Reference:** Use `PATTERN_COMPRESSION_GUIDE.md` for deep dive

---

**Print this card for quick reference!**  
**Keep it handy when creating protocols.**
