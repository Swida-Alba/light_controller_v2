# Features Guide

Complete guide to Light Controller V2.2 features and capabilities.

---

## Table of Contents

- [Core Features](#core-features)
- [Advanced Features](#advanced-features)
- [November 2025 Updates](#november-2025-updates)
- [Feature Details](#feature-details)
- [Feature Comparison](#feature-comparison)

---

## Core Features

### Multi-Channel Control

Control multiple independent LED channels simultaneously.

**Capabilities:**
- ✅ **6+ channels** on Arduino Uno
- ✅ **10+ channels** on Arduino Due/Mega
- ✅ **Independent timing** for each channel
- ✅ **Parallel execution** - all channels run simultaneously
- ✅ **Individual start times** - channels can start at different times

**Example:**
```
CH1: ON at 21:00, blinks for 30min
CH2: ON at 21:30, solid for 1hr
CH3: ON at 22:00, pulse pattern
```

---

### Automatic Calibration

Compensates for Arduino clock drift for precise timing.

**How It Works:**
1. Python sends test commands with known durations
2. Arduino executes and reports actual elapsed time
3. Program calculates calibration factor
4. All subsequent timings are corrected

**Benefits:**
- ✅ **Accurate timing** over long periods
- ✅ **One-time calibration** - factor saved for reuse
- ✅ **Automatic correction** - applied to all commands
- ✅ **Temperature compensation** - accounts for crystal drift

**Calibration Factor Example:**
```
Calibration Factor: 1.00131
Means: Arduino runs 0.131% slower than expected
All times multiplied by this factor
```

---

### Pattern Compression

Automatically detects and optimizes repeated sequences.

**Example:**
```
Original: ON 5s, OFF 5s (repeat 100 times) = 100 commands
Compressed: PATTERN with REPEATS=100 = 1 command
```

**Benefits:**
- ✅ **Memory efficient** - reduces Arduino memory usage
- ✅ **Faster upload** - fewer commands to send
- ✅ **Cleaner output** - easier to read command files

---

### Flexible Timing

Support for multiple time units across input formats.

**Supported Units:**
- **Seconds**: `s`, `sec`, `second`, `seconds` (all synonyms work!)
- **Minutes**: `m`, `min`, `minute`, `minutes` (all synonyms work!)
- **Hours**: `h`, `hr`, `hour`, `hours` (all synonyms work!)
- **Milliseconds**: `ms`, `msec`, `millisecond`, `milliseconds` (all synonyms work!)

💡 All time unit synonyms are automatically recognized - use whichever you prefer!

**Float Support:**
```
2.5 seconds = 2500ms
1.5 minutes = 90000ms
0.5 hours = 1800000ms
```

---

### Start Time Scheduling

Three flexible ways to schedule when channels start.

**1. Time-Only Format**
```
'21:00' or '21:00:30'
→ Today at 9:00 PM (or 9:00:30 PM)
```

**2. Full Datetime Format**
```
'2025-11-08 21:00:00'
→ November 8, 2025 at 9:00 PM
```

**3. Countdown Mode**
```
120 or 30.5
→ Start in 120 seconds (or 30.5 seconds)
```

**Use Cases:**
- Daily schedules: Use time-only
- Specific events: Use full datetime
- Quick testing: Use countdown

---

### Serial Communication

Robust protocol for Arduino communication.

**Features:**
- ✅ **Handshake protocol** - "Hello" → "Salve" verification
- ✅ **Error detection** - timeouts and retries
- ✅ **Multiple board types** - Uno, Due, Mega
- ✅ **Automatic port detection** - finds Arduino automatically
- ✅ **Baud rate: 9600** - reliable across all boards

---

## Advanced Features

### Pulse Frequency Control

Control LED behavior during ON states with precise pulsing.

**Capabilities:**
- **Frequency Range**: 0.01 Hz to 100 Hz
- **Pulse Width**: 1ms to period duration
- **Duty Cycle**: 0-100%
- **Memory Efficient**: Only ~960 bytes for 6 channels

**Use Cases:**
- **Breathing effect**: 0.5 Hz, 200ms pulse
- **Warning flash**: 2 Hz, 100ms pulse
- **Slow blink**: 1 Hz, 50ms pulse
- **Strobe**: 10 Hz, 10ms pulse

**4 Parameter Combinations:**

1. **Frequency + Pulse Width**
   ```
   frequency=1.0, pulse_width=100
   → 1 pulse/second, 100ms ON
   ```

2. **Frequency + Duty Cycle**
   ```
   frequency=2.0, duty_cycle=10%
   → 2 pulses/second, 10% duty cycle
   ```

3. **Period + Pulse Width**
   ```
   period=1000, pulse_width=200
   → 1000ms period, 200ms ON
   ```

4. **Period + Duty Cycle**
   ```
   period=500, duty_cycle=20
   → 500ms period, 20% ON time
   ```

---

### Wait Status Control

Define LED state during countdown before protocol starts.

**Options:**
- `wait_status=1`: LED ON during countdown
- `wait_status=0`: LED OFF during countdown

**With Pulse Support:**
```python
WAIT_PULSE: {
    'CH1': {'frequency': 0.5, 'pulse_width': 100}
}
# Channel 1 breathes slowly during wait
```

**Use Cases:**
- **Indicator**: ON during wait shows system is ready
- **Dark mode**: OFF during wait for nighttime setups
- **Breathing**: Pulse during wait for visual feedback

---

### Command Comments

Automatically generated human-readable descriptions.

**Example Output:**
```txt
PATTERN:1;CH:1;STATUS:0,1;TIME_MS:3000,3000;REPEATS:3;PULSE:T1000pw100,T1000pw100
# Pattern #1, Channel 1, Status: 0 → 1, Time: 3.0s → 3.0s, 3 cycles, Pulse: 1.00Hz DC=10.0% → 1.00Hz DC=10.0%
```

**Comment Includes:**
- Pattern number and type
- Channel number
- Status transitions
- Time in readable format (auto-converts ms to s/min/hr)
- Repeat count
- Pulse details with frequency and duty cycle

**Benefits:**
- ✅ **Debug friendly** - easy to understand what each command does
- ✅ **Documentation** - commands are self-documenting
- ✅ **Verification** - visually confirm protocol is correct

---

### Dual Start Time Formats

Excel protocols support two layout formats.

**Row-Based Format** (Best for ≤5 channels):
```
| Channel     | CH1   | CH2   | CH3   |
| ----------- | ----- | ----- | ----- |
| start_time  | 21:00 | 21:00 | 21:15 |
| wait_status | 1     | 0     | 1     |
```

**Column-Based Format** (Best for 5+ channels):
```
| Channels | Start_time | Wait_status |
| -------- | ---------- | ----------- |
| CH1      | 21:00      | 1           |
| CH2      | 21:00      | 0           |
| CH3      | 21:15      | 1           |
| CH4      | 21:15      | 0           |
| ...      | ...        | ...         |
```

**Auto-Detection:**
- Program automatically detects which format you're using
- No need to configure
- Mix and match between protocols

---

### Input Validation

Comprehensive error checking with clear messages.

**Validated Rules:**

1. **Pulse Width ≤ Period**
   ```
   ❌ pulse_width=1500ms, period=1000ms
   ✓ pulse_width=100ms, period=1000ms
   ```

2. **Duty Cycle 0-100%**
   ```
   ❌ duty_cycle=150%
   ✓ duty_cycle=10%
   ```

3. **Start Time Valid**
   ```
   ❌ Start time in the past
   ✓ Future time or countdown
   ```

4. **Channel Numbers Continuous**
   ```
   ❌ CH1, CH3, CH5 (missing CH2, CH4)
   ✓ CH1, CH2, CH3, CH4
   ```

**Error Messages:**
```
Invalid pulse parameters in CH1 row 5:
  period=1000 ms
  pulse_width=1500 ms
Pulse width cannot be larger than the period!
```

---

## November 2025 Updates

**Summary of v2.2.0 enhancements:**
- ✅ Duty cycle % sign support
- ✅ All 4 pulse combinations supported
- ✅ Descriptive command comments
- ✅ Column-based start time format
- ✅ **Flexible column naming (synonyms)**
- ✅ Enhanced validation with helpful error messages

---

### Duty Cycle % Sign Support

Accept multiple duty cycle formats - all equivalent:

```
For 10% duty cycle:
✓ 10          (integer)
✓ "10"        (string)
✓ "10%"       (with % sign)
✓ 0.1         (decimal)
✓ "0.1"       (string decimal)
✓ " 10% "     (with spaces - auto-trimmed)
```

**Benefits:**
- More intuitive - use % sign as expected
- Excel friendly - doesn't auto-format as percent
- Backward compatible - old formats still work

---

### All 4 Pulse Combinations

Support all possible pulse parameter combinations:

| Timing    | Width/Duty  | Example          |
| --------- | ----------- | ---------------- |
| Frequency | Pulse Width | `f=1.0, pw=100`  |
| Frequency | Duty Cycle  | `f=2.0, dc=10%`  |
| Period    | Pulse Width | `T=1000, pw=200` |
| Period    | Duty Cycle  | `T=500, dc=20`   |

**Automatic Conversion:**
- Program normalizes all formats internally
- Choose the most convenient format for your use case
- Mix formats between channels

---

### Descriptive Comments

Auto-generated comments with full details:

**Before (v2.1):**
```txt
PATTERN:1;CH:1;STATUS:0,1;TIME_MS:3000,3000;REPEATS:3
```

**After (v2.2):**
```txt
PATTERN:1;CH:1;STATUS:0,1;TIME_MS:3000,3000;REPEATS:3;PULSE:T1000pw100,T1000pw100
# Pattern #1, Channel 1, Status: 0 → 1, Time: 3.0s → 3.0s, 3 cycles, Pulse: 1.00Hz DC=10.0% → 1.00Hz DC=10.0%
```

---

### Column-Based Start Time

New vertical layout for protocols with many channels:

**Easier to:**
- Add/remove channels
- Read channel configurations
- Manage 10+ channels

**Still supports:**
- Original row-based format
- Auto-detection of format
- Both formats in different files

---

### Flexible Column Naming (Synonym Support)

**November 2025 Enhancement**

Multiple naming conventions automatically recognized:

**What it does:**
- Use short forms, full names, or alternatives
- All synonyms work identically
- Choose naming that makes sense to you

**Supported Synonyms:**

**Time Units:**
```
Seconds:      _s, _sec, _second, _seconds
Minutes:      _m, _min, _minute, _minutes  
Hours:        _h, _hr, _hour, _hours
Milliseconds: _ms, _msec, _millisecond, _milliseconds
```

**Pulse Parameters:**
```
Period:       period, T (capital!), cycle_time, cycletime
Pulse Width:  pulse_width, PW, pw, on_time, ontime
Duty Cycle:   duty_cycle, DC, dc, duty
Frequency:    frequency, freq, f, hz, Hz
```

**Examples (all equivalent):**
```excel
# Time columns
CH1_time_s       = CH1_time_sec      = CH1_time_seconds

# Frequency columns  
CH1_frequency    = CH1_freq          = CH1_f

# Pulse width columns
CH1_pulse_width  = CH1_PW            = CH1_on_time

# Period columns
CH1_period       = CH1_T             = CH1_cycle_time

# Duty cycle columns
CH1_duty_cycle   = CH1_DC            = CH1_duty
```

**Use Case:**
- Import existing protocols without renaming columns
- Use domain-specific terminology
- Shorter column names for compact sheets
- Clearer names for documentation

💡 **Tip**: Stick to one style per file for consistency!

---

### Comprehensive Validation

Enhanced error checking with specific messages:

**Validation Categories:**

1. **Pulse Parameters**
   - PW ≤ Period check
   - DC ≤ 100% check
   - Frequency > 0 check

2. **Time Parameters**
   - Positive values
   - Reasonable ranges
   - Unit conversion validity

3. **Channel Configuration**
   - Continuous numbering
   - Valid pin assignments
   - Memory limits

4. **Start Time**
   - Future times
   - Valid formats
   - All channels present

---

## Feature Comparison

### By Arduino Board

| Feature       | Uno      | Mega     | Due      |
| ------------- | -------- | -------- | -------- |
| Channels      | 6-8      | 10-15    | 15-20    |
| Flash Memory  | 32KB     | 256KB    | 512KB    |
| SRAM          | 2KB      | 8KB      | 96KB     |
| Max Patterns  | 10       | 20       | 50       |
| Pulse Control | ✓        | ✓        | ✓        |
| Upload Method | Standard | Standard | Special* |

*See [Arduino Due Setup](ARDUINO_DUE.md)

### By Protocol Format

| Feature          | Excel | Text |
| ---------------- | ----- | ---- |
| Visual Editing   | ✓     | -    |
| Comments         | -     | ✓    |
| Version Control  | -     | ✓    |
| Quick Edit       | ✓     | ✓    |
| Complex Logic    | ✓     | ✓    |
| Syntax Highlight | -     | ✓*   |

*With VS Code extension

---

## Feature Roadmap

### Planned Features

- 🔄 Web interface for protocol creation
- ✅ Real-time monitoring with dynamic Y-axis scaling
- ✅ PWM (0-255) and DAC (0-4095) support
- ✅ MCP4728 I2C DAC support (pins 201-204)
- ✅ Native DAC support (pins 100-101)
- 🔄 Pattern library/templates
- 🔄 Conditional logic (if/then)
- 🔄 External sensor input
- 🔄 WiFi/Bluetooth control

### Real-Time Monitoring (Implemented v2.3)

- **Dynamic Y-axis scaling** - Auto-adjusts to fit actual data values
- **Multiple value ranges**: Binary (0-1), PWM (0-255), DAC (0-4095)
- **Sub-range support**: DAC using only 2000-2500 zooms appropriately
- **Interactive HTML export** with range slider navigation
- **Console bars** adapt to detected value range

### Request Features

Have an idea? [Open an issue](https://github.com/Swida-Alba/light_controller_v2/issues) on GitHub!

---

## See Also

- [Usage Guide](USAGE.md) - How to use features
- [Protocol Formats](PROTOCOL_FORMATS.md) - Format specifications
- [Examples](EXAMPLES.md) - Feature demonstrations

---

*Last Updated: January 24, 2026*
