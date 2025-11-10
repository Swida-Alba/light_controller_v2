# Protocol Examples Directory

This directory contains example protocols demonstrating pattern-based compression with different `pattern_length` values.

## 📂 Directory Structure

This folder is now organized into two subdirectories demonstrating different calibration approaches:

### 🔧 **[preset_calibration/](preset_calibration/README.md)** - Legacy Manual Calibration
Examples using the **old style** manual `CALIBRATION_FACTOR` in protocol files.

**When to use:**
- Shared protocols that must work on any Arduino
- Pre-calibrated hardware setups
- Backward compatibility requirements

**Features:**
- Manual `CALIBRATION_FACTOR: 1.000000` in each protocol
- Highest priority (overrides automatic calibration)
- Fully backward compatible with existing protocols

### ✨ **[auto_calibration/](auto_calibration/README.md)** - Automatic Calibration (Recommended)
Examples using the **new automatic calibration system** without manual factors.

**When to use:**
- New protocols (recommended default)
- Multi-board workflows
- Simplified calibration management

**Features:**
- No `CALIBRATION_FACTOR` line needed (TXT) or no `calibration` sheet (Excel)
- Automatic Arduino identification (serial number/VID/PID)
- Per-board calibration storage in database
- One-time calibration per Arduino
- Seamless multi-board support

**Contents:**
- 3 TXT protocol examples
- 3 Excel protocol examples (matching TXT versions)
- Comprehensive README with usage guide

### 📚 **Root Directory**
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Protocol syntax reference
- **[README.md](README.md)** - This file (examples overview)
- **calibration_method_example.py** - Calibration method comparison script

---

## 🚀 Quick Start Guide

### First Time Users (Recommended: Automatic Calibration)

**TXT Format:**
```bash
# 1. Run an auto-calibration example
python protocol_parser.py 2 /dev/cu.usbmodem14301 examples/auto_calibration/simple_blink_example.txt

# 2. When prompted, calibrate (one-time setup per Arduino)
Arduino not calibrated. Calibrate now? (Y/n): y

# 3. Future runs are automatic - no prompts!
python protocol_parser.py 4 /dev/cu.usbmodem14301 examples/auto_calibration/pulse_protocol.txt
```

**Excel Format:**
```bash
# Excel works the same way - no 'calibration' sheet = auto-calibration
python protocol_parser.py 2 /dev/cu.usbmodem14301 examples/auto_calibration/simple_blink_example.xlsx

# First time: prompted to calibrate
# Future runs: automatic!
python protocol_parser.py 4 /dev/cu.usbmodem14301 examples/auto_calibration/pulse_protocol.xlsx
```

### Legacy Users (Manual Calibration)

```bash
# Run a preset calibration example (with manual CALIBRATION_FACTOR)
python protocol_parser.py 4 /dev/cu.usbmodem14301 examples/preset_calibration/basic_protocol.txt

# You'll see a warning about outdated practice (but it still works)
```

### Migrate from Legacy to Automatic

1. **Remove `CALIBRATION_FACTOR` line** from your protocol
2. **Run the protocol** - you'll be prompted to calibrate once
3. **Done!** Future runs use automatic calibration

See [auto_calibration/README.md](auto_calibration/README.md) for detailed migration guide.

---

## Understanding Pattern Compression

The Light Controller uses **pattern compression** to efficiently represent repetitive LED sequences. Instead of sending hundreds of individual state changes, it detects repeating patterns and sends them with a repeat count.

### Key Concept: pattern_length

**pattern_length** = Number of consecutive states grouped into a repeating pattern

- `pattern_length=2`: Best for simple ON/OFF alternations (most common)
- `pattern_length=4`: Best for 4-phase sequences (traffic lights, breathing effects)
- `pattern_length=8`: Best for complex 8-step cycles

## Example Files

### Pattern Length = 2 Examples (DEFAULT - Simple Patterns)

#### `pattern_length_2_example.txt`
- **Purpose**: Demonstrates optimal pattern_length=2 usage
- **Use case**: Simple blink patterns, ON/OFF alternations
- **Patterns**: 8 total (2 per channel × 4 channels)
- **Compression**: 252 state changes → 8 commands (96.8% reduction!)
- **Arduino RAM**: 256 bytes (minimal)

**Features demonstrated:**
- Simple blink patterns (ON 1s, OFF 1s)
- Asymmetric timing (ON 2s, OFF 0.5s)
- Pulsed patterns with 2-element structure
- Variable duty cycles
- Fast heartbeat sequences

**Usage:**
```bash
python protocol_parser.py 2
# Select: pattern_length_2_example.txt
```

#### `pattern_length_2_example.xlsx`
- **Purpose**: Excel version showing 2-element pattern compression
- **Structure**: 60 rows of data
- **Compression**: 60 rows → ~3 commands (one per channel)
- **Pattern**: Repeating [ON, OFF] cycle

**Excel sheets:**
- `protocol`: Time-series data with CH1/CH2/CH3 columns
- `start_time`: Start times and wait status for each channel
- `calibration`: Timing calibration factor

**Usage:**
```bash
python protocol_parser.py 2
# Select: pattern_length_2_example.xlsx
```

---

### Pattern Length = 4 Examples (Complex Multi-Phase)

#### `pattern_length_4_example.txt`
- **Purpose**: Demonstrates optimal pattern_length=4 usage
- **Use case**: Multi-phase sequences, complex patterns
- **Patterns**: 8 total (2 per channel × 4 channels)
- **Compression**: 296 state changes → 8 commands (97.3% reduction!)
- **Arduino RAM**: 512 bytes (still efficient)

**Features demonstrated:**
- 4-phase warning sequences (fast pulse → pause → slow pulse → rest)
- Traffic light simulation (green → yellow → red → off)
- Breathing effects (fade in → peak → fade out → rest)
- Morse code sequences (SOS pattern)
- Escalating intensity patterns

**Usage:**
```bash
python protocol_parser.py 4
# Select: pattern_length_4_example.txt
```

**⚠️ Requirements:** Arduino firmware must have `PATTERN_LENGTH >= 4`

#### `pattern_length_4_example.xlsx`
- **Purpose**: Excel version showing 4-element pattern compression
- **Structure**: 80 rows of data (20 cycles × 4 phases)
- **Compression**: 80 rows → ~3 commands (one per channel)
- **Pattern**: Repeating [Phase1, Phase2, Phase3, Phase4] cycle

**Excel sheets:**
- `protocol`: Time-series data with 4-phase repeating structure
- `start_time`: Start times and wait status for each channel
- `calibration`: Timing calibration factor

**Usage:**
```bash
python protocol_parser.py 4
# Select: pattern_length_4_example.xlsx
```

---

### Legacy Examples (Basic Demonstrations)

#### `basic_protocol.txt`
- Basic TXT protocol example with 3 channels
- No specific pattern_length optimization
- Good for learning TXT syntax

#### `basic_protocol.xlsx`
- Basic Excel protocol example
- Simple time-series format
- Good for learning Excel structure

#### `pulse_protocol.txt` / `pulse_protocol.xlsx`
- Demonstrates pulse parameter usage
- Shows T[period]pw[width] format
- Examples of PWM pulsing during LED states

#### `wait_pulse_protocol.txt` / `wait_pulse_protocol.xlsx`
- Demonstrates wait period configuration
- Shows LED behavior before pattern starts
- Wait pulse vs wait steady state

---

## How to Use Examples

### Step 1: Choose Your Pattern Length

**Use pattern_length=2 if:**
- ✓ Your protocol alternates between two states (ON/OFF)
- ✓ You want minimal Arduino memory usage
- ✓ You have simple blink or pulse patterns
- ✓ Arduino has PATTERN_LENGTH=2 (default)

**Use pattern_length=4 if:**
- ✓ Your protocol has 4-phase cycles
- ✓ You have complex multi-step sequences
- ✓ You want to capture complete patterns in one command
- ✓ Arduino has PATTERN_LENGTH=4 or higher

### Step 2: Run the Protocol

```bash
# With default pattern_length=4
python protocol_parser.py

# With explicit pattern_length=2
python protocol_parser.py 2

# With explicit pattern_length=4
python protocol_parser.py 4

# With custom pattern_length
python protocol_parser.py 8
```

### Step 3: Select Example File

When prompted, select one of the example files:
- `pattern_length_2_example.txt` or `.xlsx` → Use with `pattern_length=2`
- `pattern_length_4_example.txt` or `.xlsx` → Use with `pattern_length=4`

### Step 4: Review Output

The system will show:

```
Compression efficiency analysis:
  pattern_length=2: 8 commands ← optimal ← given
  pattern_length=4: 16 commands
  pattern_length=8: 32 commands

💡 Perfect match! pattern_length=2 is optimal for this protocol
```

### Step 5: Verify Arduino Compatibility

```
📏 Protocol pattern analysis:
   Required PATTERN_LENGTH: 2
   Arduino PATTERN_LENGTH:  2
   ✓ Verification passed
```

If verification fails, update Arduino firmware PATTERN_LENGTH constant.

---

## Compression Analysis Examples

### Example 1: pattern_length_2_example.txt

**Without compression:**
```
CH1 Pattern 1: 20 repeats × 2 states = 40 commands
CH1 Pattern 2: 10 repeats × 2 states = 20 commands
... (similar for CH2, CH3, CH4)
TOTAL: 252 individual state changes
```

**With pattern_length=2 compression:**
```
CH1: 2 patterns = 2 commands
CH2: 2 patterns = 2 commands
CH3: 2 patterns = 2 commands
CH4: 2 patterns = 2 commands
TOTAL: 8 commands
```

**Result:** 252 → 8 = **31.5:1 compression ratio** (96.8% reduction)

### Example 2: pattern_length_4_example.txt

**Without compression:**
```
CH1 Pattern 1: 10 repeats × 4 phases = 40 commands
CH1 Pattern 2: 5 repeats × 4 phases = 20 commands
... (similar for CH2, CH3, CH4)
TOTAL: 296 individual state changes
```

**With pattern_length=4 compression:**
```
CH1: 2 patterns = 2 commands
CH2: 2 patterns = 2 commands
CH3: 2 patterns = 2 commands
CH4: 2 patterns = 2 commands
TOTAL: 8 commands
```

**Result:** 296 → 8 = **37:1 compression ratio** (97.3% reduction)

### Comparison: pattern_length=2 vs pattern_length=4

For **pattern_length_4_example.txt**:

| pattern_length | Commands | Efficiency | Why |
|----------------|----------|------------|-----|
| 2 | 16 | 50% worse | Splits 4-phase patterns into 2×2-phase |
| 4 | 8 | **Optimal** ✓ | Captures natural 4-phase structure |
| 8 | 16 | 50% worse | Pattern doesn't naturally repeat in 8s |

**Lesson:** Match pattern_length to your protocol's natural cycle!

---

## Creating Your Own Examples

### For pattern_length=2 (Excel)

Create protocol with alternating rows:

```
Row | CH1_status | CH1_time_sec | CH1_period | CH1_pulse_width
----|------------|--------------|------------|----------------
 1  |     1      |      1       |     0      |       0
 2  |     0      |      1       |     0      |       0
 3  |     1      |      1       |     0      |       0
 4  |     0      |      1       |     0      |       0
... (repeat pattern)
```

This will compress perfectly with pattern_length=2.

### For pattern_length=4 (Excel)

Create protocol with 4-row repeating cycles:

```
Row | CH1_status | CH1_time_sec | CH1_period | CH1_pulse_width
----|------------|--------------|------------|----------------
 1  |     1      |     0.5      |    200     |      20         # Phase 1
 2  |     0      |     0.5      |      0     |       0         # Phase 2
 3  |     1      |      1       |   1000     |     100         # Phase 3
 4  |     0      |      2       |      0     |       0         # Phase 4
 5  |     1      |     0.5      |    200     |      20         # Repeat phase 1
 6  |     0      |     0.5      |      0     |       0         # Repeat phase 2
... (repeat 4-row cycle)
```

This will compress perfectly with pattern_length=4.

### For pattern_length=2 (TXT)

```txt
# Two-element pattern: ON then OFF
PATTERN:1;CH:1;STATUS:1,0;TIME_MS:1000,2000;REPEATS:20;PULSE:T0pw0,T0pw0
```

### For pattern_length=4 (TXT)

```txt
# Four-element pattern: Fast → Pause → Slow → Rest
PATTERN:1;CH:1;STATUS:1,0,1,0;TIME_MS:500,500,1000,2000;REPEATS:10;PULSE:T200pw20,T0pw0,T1000pw100,T0pw0
```

---

## Arduino Firmware Requirements

### For pattern_length=2 (Default)

```cpp
// In light_controller_v2_arduino.ino, line 3
const int PATTERN_LENGTH = 2;  // Works with most examples
```

**Memory per pattern:** 32 bytes  
**Max patterns supported:** ~300 (on Arduino Due)

### For pattern_length=4

```cpp
// In light_controller_v2_arduino.ino, line 3
const int PATTERN_LENGTH = 4;  // Required for 4-phase examples
```

**Memory per pattern:** 64 bytes  
**Max patterns supported:** ~150 (on Arduino Due)

### For pattern_length=8

```cpp
// In light_controller_v2_arduino.ino, line 3
const int PATTERN_LENGTH = 8;  // For complex sequences
```

**Memory per pattern:** 128 bytes  
**Max patterns supported:** ~75 (on Arduino Due)

---

## Troubleshooting

### Error: Pattern length exceeds Arduino capability

```
❌ ERROR: Pattern length exceeds Arduino capability!
  Protocol requires: 4
  Arduino supports:  2
```

**Solution:** Update Arduino firmware PATTERN_LENGTH to 4 or higher, then re-upload.

### Warning: Suboptimal pattern_length

```
💡 Note: Given pattern_length=4 generates 52 commands
         Optimal pattern_length=2 generates 45 commands
```

**Solution:** Consider using the recommended pattern_length for better efficiency.

### Too many commands generated

If you see hundreds of commands even with compression, your protocol may be:
- Too irregular (little repetition)
- Using wrong pattern_length
- Unnecessarily complex

**Solution:** Simplify protocol or increase pattern_length to match natural cycle.

---

## Best Practices

### ✅ Do's

1. **Match pattern_length to protocol structure**
   - 2-state alternation → pattern_length=2
   - 4-phase cycles → pattern_length=4

2. **Start with examples**
   - Modify existing examples rather than starting from scratch
   - Test with small protocols first

3. **Check compression efficiency**
   - System shows compression analysis automatically
   - Use optimal pattern_length when possible

4. **Update Arduino firmware**
   - Set PATTERN_LENGTH to match or exceed your needs
   - Re-upload firmware after changes

5. **Test before deployment**
   - Use preview mode to validate commands
   - Start with short protocols (1-2 minutes)

### ❌ Don'ts

1. **Don't ignore efficiency warnings**
   - System tells you the optimal pattern_length
   - Using suboptimal values wastes memory

2. **Don't use pattern_length > 8 without reason**
   - Very memory intensive
   - Rarely provides better compression

3. **Don't create irregular patterns**
   - Pattern compression only helps with repetition
   - Random sequences won't compress well

4. **Don't exceed Arduino limits**
   - Check PATTERN_LENGTH before running
   - Monitor memory usage for complex protocols

5. **Don't forget calibration**
   - Include calibration_factor in protocols
   - Test timing accuracy

---

## Additional Examples

### `clean_protocol.txt`
- **Purpose**: Minimal protocol without comments
- **Use case**: Template for quick protocol creation
- **Features**: All required parameters (PATTERN, START_TIME) and all optional parameters (WAIT_STATUS, WAIT_PULSE, CALIBRATION_FACTOR)
- **Format**: Clean, no comments, ready to modify

### `complete_protocol.txt`
- **Purpose**: Fully documented example showing all features
- **Use case**: Learning protocol syntax, understanding required vs optional parameters
- **Features**: Comprehensive comments explaining each section
- **Annotations**: Clear markers for REQUIRED vs OPTIONAL parameters

### `pulse_protocol.txt`
- **Purpose**: Demonstrates various pulsing patterns
- **Use case**: Learning pulse timing and frequency control
- **Features**: Progressive pulse speeds, different pulse effects
- **Note**: Shows correct pulse period ≤ section time relationship

### `wait_pulse_protocol.txt`
- **Purpose**: Demonstrates wait period features
- **Use case**: Learning countdown/wait behavior
- **Features**: WAIT_STATUS, WAIT_PULSE parameters in action

---

## Additional Resources

- **[PATTERN_COMPRESSION_GUIDE.md](../docs/PATTERN_COMPRESSION_GUIDE.md)** - Complete guide to pattern logic
- **[PATTERN_LENGTH_VERIFICATION.md](../docs/PATTERN_LENGTH_VERIFICATION.md)** - Verification system details
- **[PATTERN_LENGTH_IMPLEMENTATION.md](../docs/PATTERN_LENGTH_IMPLEMENTATION.md)** - Technical implementation
- **[PROTOCOL_FORMATS.md](../docs/PROTOCOL_FORMATS.md)** - Complete protocol syntax reference
- **[PULSE_PERIOD_VS_SECTION_TIME.md](../docs/PULSE_PERIOD_VS_SECTION_TIME.md)** - Understanding pulse timing

---

## Quick Start

```bash
# 1. Choose an example
cd examples

# 2. Run with appropriate pattern_length
python ../protocol_parser.py 2  # For pattern_length_2 examples
python ../protocol_parser.py 4  # For pattern_length_4 examples

# 3. Select the example file when prompted

# 4. Review compression analysis and verification results

# 5. Upload to Arduino if verification passes
```

---

**Last Updated:** November 8, 2025  
**Examples Version:** 2.0  
**Compatible with:** Light Controller v2.2+
