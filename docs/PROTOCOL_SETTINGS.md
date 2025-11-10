# Protocol Settings Reference

Complete guide to all protocol settings and parameters.

---

## Table of Contents

- [Start Time Configuration](#start-time-configuration)
- [Calibration Settings](#calibration-settings)
- [Wait Status Control](#wait-status-control)
- [Pulse Parameters](#pulse-parameters)
- [Time Units](#time-units)
- [Advanced Settings](#advanced-settings)

---

## Start Time Configuration

### Overview

Control when each channel begins execution with flexible scheduling.

### Format Support

| Format | Example | Use Case |
|--------|---------|----------|
| Time only | `21:00` | Start today at specific time |
| Full datetime | `2025-11-08 21:00:00` | Schedule future date/time |
| Countdown | `120` | Start in N seconds |

---

### Time Only Format

**Syntax:** `HH:MM` or `HH:MM:SS`

**Examples:**
```
21:00       → Today at 9:00 PM
21:30:00    → Today at 9:30:00 PM
06:00       → Today at 6:00 AM (or tomorrow if past)
14:15:30    → Today at 2:15:30 PM
```

**Behavior:**
- If time has passed today, schedules for tomorrow
- 24-hour format (00:00 to 23:59)
- Seconds optional (defaults to :00)

---

### Full Datetime Format

**Syntax:** `YYYY-MM-DD HH:MM:SS`

**Examples:**
```
2025-11-08 21:00:00    → Nov 8, 2025 at 9 PM
2025-12-25 06:00:00    → Dec 25, 2025 at 6 AM
2026-01-01 00:00:00    → Jan 1, 2026 at midnight
```

**Use cases:**
- Future experiments
- Scheduled automation
- Specific date requirements
- Multi-day protocols

---

### Countdown Format

**Syntax:** `<seconds>` (integer or float)

**Examples:**
```
30      → Start in 30 seconds
120     → Start in 2 minutes
3600    → Start in 1 hour
30.5    → Start in 30.5 seconds
```

**Benefits:**
- Immediate scheduling
- Quick testing
- Relative timing
- No clock dependency

---

### Excel Configuration

#### Row Format (≤5 channels)

```
| Channel    | CH1   | CH2      | CH3           |
|------------|-------|----------|---------------|
| start_time | 21:00 | 120      | 2025-11-09... |
```

#### Column Format (5+ channels)

```
| Channels | Start_time          | 
|----------|---------------------|
| CH1      | 21:00               |
| CH2      | 120                 |
| CH3      | 2025-11-09 06:00:00 |
```

---

### Text Configuration

**Syntax:**
```txt
START_TIME: {
    'CH1': '<time>',
    'CH2': <countdown>,
    'CH3': '<datetime>'
}
```

**Example:**
```txt
START_TIME: {
    'CH1': '21:00',
    'CH2': 120,
    'CH3': '2025-11-09 06:00:00'
}
```

---

### Multi-Channel Timing

**Synchronized start:**
```txt
START_TIME: {
    'CH1': '21:00',
    'CH2': '21:00',
    'CH3': '21:00'
}
```

**Staggered start:**
```txt
START_TIME: {
    'CH1': '21:00',       # Start first
    'CH2': '21:15',       # Start 15 min later
    'CH3': '21:30'        # Start 30 min later
}
```

**Mixed timing:**
```txt
START_TIME: {
    'CH1': '21:00',       # Specific time
    'CH2': 60,            # 1 minute from now
    'CH3': 120            # 2 minutes from now
}
```

---

## Calibration Settings

### Overview

Calibration compensates for timing drift in the Arduino's internal clock.

### How It Works

1. **Calibration Phase** (2 minutes):
   - Measures actual Arduino timing
   - Calculates correction factor
   - Typically: 1.00000 to 1.00200

2. **Application**:
   - All timing commands multiplied by factor
   - Maintains accuracy over long runs
   - One-time calculation per session

### Calibration Factor

**Format:** `CALIBRATION_FACTOR: <value>`

**Range:** 0.99 to 1.02 (typically ~1.001)

**Examples:**
```
1.00131   → Arduino 0.131% slower
0.99923   → Arduino 0.077% faster
1.00000   → Perfect timing (rare)
```

---

### Excel Configuration

Create a sheet named `calibration`:

```
| CALIBRATION_FACTOR |
|--------------------|
| 1.00131            |
```

---

### Text Configuration

**Syntax:**
```txt
CALIBRATION_FACTOR: <value>
```

**Example:**
```txt
# Reuse calibration from previous run
CALIBRATION_FACTOR: 1.00131
```

---

### Getting Calibration Factor

**From output file:**
```
protocol_commands_20251108210000.txt
```

Look for line:
```
CALIBRATION_FACTOR: 1.00131
```

**Copy value to next protocol** to skip 2-minute calibration.

---

### When to Recalibrate

**Recalibrate if:**
- Different Arduino board
- Temperature change >10°C
- After firmware update
- Long time since last calibration
- Timing seems off

**Reuse factor if:**
- Same Arduino board
- Same environment
- Recent calibration (<1 week)
- Timing still accurate

---

## Wait Status Control

### Overview

Controls LED behavior during countdown to start time.

### Values

| Value | Behavior | Use Case |
|-------|----------|----------|
| `1` | LED ON during wait | Visual ready indicator |
| `0` | LED OFF during wait | Dark mode before start |

---

### Excel Configuration

#### Row Format

```
| Channel     | CH1 | CH2 | CH3 |
|-------------|-----|-----|-----|
| start_time  | ... | ... | ... |
| wait_status | 1   | 0   | 1   |
```

#### Column Format

```
| Channels | Start_time | Wait_status |
|----------|------------|-------------|
| CH1      | 21:00      | 1           |
| CH2      | 21:00      | 0           |
| CH3      | 21:15      | 1           |
```

---

### Text Configuration

**Syntax:**
```txt
WAIT_STATUS: {
    'CH1': 1,
    'CH2': 0,
    'CH3': 1
}
```

**Example:**
```txt
START_TIME: {
    'CH1': 120,
    'CH2': 120
}

WAIT_STATUS: {
    'CH1': 1,    # ON during countdown
    'CH2': 0     # OFF during countdown
}
```

---

### Use Cases

**Visual feedback:**
```txt
# CH1 shows system is ready and counting down
WAIT_STATUS: {'CH1': 1, 'CH2': 0, 'CH3': 0}
```

**Dark mode:**
```txt
# All channels off until start
WAIT_STATUS: {'CH1': 0, 'CH2': 0, 'CH3': 0}
```

**Channel identification:**
```txt
# Each channel lights up during its countdown
WAIT_STATUS: {'CH1': 1, 'CH2': 1, 'CH3': 1}
```

---

### Wait Pulse (Advanced)

Add pulse effect during wait period.

**Text format:**
```txt
WAIT_PULSE: {
    'CH1': {'frequency': 0.5, 'pulse_width': 100},
    'CH2': {'frequency': 1.0, 'pulse_width': 50}
}
```

**Effect:** Breathing or blinking during countdown.

---

## Pulse Parameters

### Overview

Control LED pulsing (blinking/breathing) during ON states.

### Parameter Combinations

Four valid combinations:

| Combination | Parameters | Best For |
|-------------|------------|----------|
| 1 | Frequency + Pulse Width | Precise timing control |
| 2 | Frequency + Duty Cycle | Percentage-based brightness |
| 3 | Period + Pulse Width | Direct period control |
| 4 | Period + Duty Cycle | Period + percentage |

---

### Frequency Parameter

**Name:** `CH[N]_frequency` (Excel) or `f<value>` (Text)

**Column Name Synonyms (Excel):**
- `CH1_frequency` ← Standard
- `CH1_freq` ← Short
- `CH1_frq` ← Alternative
- `CH1_f` ← Shortest
- `CH1_hz`, `CH1_Hz` ← Unit-based names (synonyms, NOT suffixes!)

⚠️ **Important**: `hz`/`Hz` are COLUMN NAME synonyms. Don't use them as unit suffixes!
```
✓ CH1_frequency    → Values always in Hz (e.g., 1.0, 2.5)
✓ CH1_Hz           → Same (Hz is a NAME synonym)
✗ CH1_frequency_Hz → WRONG! Don't add Hz as suffix
```

**Units:** Hz (cycles per second) - always, no suffix needed or allowed

**Range:** 0.01 to 100 Hz

**Special values:**
- `0` = No pulsing (solid state)
- `0.5` = Slow breathing (2 sec cycle)
- `1.0` = Standard blink (1 sec cycle)
- `2.0` = Fast blink (0.5 sec cycle)
- `10.0` = Strobe effect

**Examples:**
```
0.5 Hz  → 2000ms period (slow)
1.0 Hz  → 1000ms period (normal)
2.0 Hz  → 500ms period (fast)
10.0 Hz → 100ms period (strobe)
```

---

### Pulse Width Parameter

**Name:** `CH[N]_pulse_width` (Excel) or `pw<value>` (Text)

**Column Name Synonyms (Excel):**
- `CH1_pulse_width` ← Standard
- `CH1_pulsewidth` ← No underscore
- `CH1_PW` ← Short (uppercase)
- `CH1_pw` ← Short (lowercase)
- `CH1_on_time` ← Descriptive
- `CH1_ontime` ← No underscore

**Units:** Milliseconds by default

**Can add time unit suffix:**
```
CH1_pulse_width     → Values in milliseconds (default)
CH1_pulse_width_ms  → Values in milliseconds (explicit)
CH1_PW_s            → Values in seconds
CH1_on_time_ms      → Values in milliseconds
```

**Values**: Enter duration in the specified unit (e.g., `100` for 100ms, or `0.1` for 0.1s if using `_s` suffix)

**Range:** 1 to period duration

**Constraint:** pulse_width ≤ period (1000 / frequency)

**Examples:**
```
50ms with 1Hz (1000ms period) → 5% duty cycle
100ms with 1Hz               → 10% duty cycle
500ms with 1Hz               → 50% duty cycle
```

---

### Period Parameter

**Name:** `CH[N]_period` (Excel)

**Column Name Synonyms (Excel):**
- `CH1_period` ← Standard
- `CH1_T` ← Short (capital T only!)
- `CH1_cycle_time` ← Descriptive
- `CH1_cycletime` ← No underscore

⚠️ **Important**: Use capital `T` not lowercase `t` (lowercase is ambiguous with "time")

**Units:** Milliseconds by default

**Can add time unit suffix:**
```
CH1_period     → Values in milliseconds (default)
CH1_period_ms  → Values in milliseconds (explicit)
CH1_T_s        → Values in seconds
CH1_T_ms       → Values in milliseconds
```

**Values**: Enter duration in the specified unit (e.g., `1000` for 1000ms, or `1` for 1s if using `_s` suffix)

**Relationship:** period = 1000 / frequency

**Examples:**
```
2000ms period = 0.5 Hz
1000ms period = 1.0 Hz
500ms period = 2.0 Hz
100ms period = 10.0 Hz
```

---

### Duty Cycle Parameter

**Name:** `CH[N]_duty_cycle` (Excel)

**Column Name Synonyms (Excel):**
- `CH1_duty_cycle` ← Standard
- `CH1_dutycycle` ← No underscore
- `CH1_DC` ← Short (uppercase)
- `CH1_dc` ← Short (lowercase)
- `CH1_duty` ← Shortest

**Units:** Percentage (0-100%) - always, no suffix needed or allowed

⚠️ **Important**: Don't add `_%` suffix!
```
✓ CH1_duty_cycle   → Values in % (e.g., 10, "50%", 0.25)
✓ CH1_DC           → Same (synonym)
✗ CH1_duty_cycle_% → WRONG! Don't add % as suffix
```

**Accepted formats:**
- Integer: `10` → 10%
- String: `"10"` → 10%
- With percent: `"10%"` → 10%
- Decimal: `0.1` → 10%
- String decimal: `"0.1"` → 10%

**Examples:**
```
10%  → Light on 10% of cycle
50%  → Light on 50% of cycle
100% → Light on full cycle (solid)
5%   → Very brief flash
```

---

### Excel Pulse Configuration

**Option 1: Frequency + Pulse Width**
```
| CH1_status | CH1_time_ms | CH1_frequency | CH1_pulse_width |
|------------|-------------|---------------|-----------------|
| 1          | 10000       | 1.0           | 100             |
```

**Option 2: Frequency + Duty Cycle**
```
| CH1_status | CH1_time_ms | CH1_frequency | CH1_duty_cycle |
|------------|-------------|---------------|----------------|
| 1          | 10000       | 2.0           | 10%            |
```

**Option 3: Period + Pulse Width**
```
| CH1_status | CH1_time_ms | CH1_period | CH1_pulse_width |
|------------|-------------|------------|-----------------|
| 1          | 10000       | 1000       | 200             |
```

**Option 4: Period + Duty Cycle**
```
| CH1_status | CH1_time_ms | CH1_period | CH1_duty_cycle |
|------------|-------------|------------|----------------|
| 1          | 10000       | 500        | 20             |
```

---

### Text Pulse Configuration

**Syntax:** `PULSE:f<freq>pw<width>,f<freq>pw<width>`

**Pattern:** One pulse spec per status state, comma-separated

**Examples:**

**No pulse OFF, pulse ON:**
```txt
PATTERN:1;CH:1;STATUS:0,1;TIME_S:10,10;REPEATS:5;PULSE:f0pw0,f1pw50
```

**Breathing effect:**
```txt
PATTERN:1;CH:1;STATUS:1;TIME_S:60;REPEATS:1;PULSE:f0.5pw200
```

**Fast strobe:**
```txt
PATTERN:1;CH:1;STATUS:1;TIME_S:10;REPEATS:10;PULSE:f10pw10
```

**Different pulses per state:**
```txt
PATTERN:1;CH:1;STATUS:0,1;TIME_S:5,5;REPEATS:20;PULSE:f0.5pw100,f2pw50
```

---

### Common Pulse Patterns

**Breathing (slow):**
```
Frequency: 0.5 Hz
Pulse Width: 200ms
Effect: Gentle fade in/out
```

**Standard blink:**
```
Frequency: 1.0 Hz
Pulse Width: 50-100ms
Effect: Clear on/off
```

**Fast blink:**
```
Frequency: 2-5 Hz
Pulse Width: 20-50ms
Effect: Rapid flashing
```

**Strobe:**
```
Frequency: 10+ Hz
Pulse Width: 10ms
Effect: Brief intense flashes
```

---

## Time Units

### Overview

Time unit suffixes specify what unit the VALUES in a column use. The suffix goes in the column NAME.

**Supported for:**
- Main time column: `CH1_time_[unit]`
- Period column: `CH1_period_[unit]`, `CH1_T_[unit]`
- Pulse width column: `CH1_pulse_width_[unit]`, `CH1_PW_[unit]`

**NOT supported for:**
- Frequency (always Hz)
- Duty cycle (always %)

---

### Supported Units

| Unit | Suffixes (All Synonyms Accepted) | Example | How to Use |
|------|----------------------------------|---------|------------|
| Seconds | `_s`, `_sec`, `_second`, `_seconds` | `CH1_time_s` | Enter `10` for 10 seconds |
| Minutes | `_m`, `_min`, `_minute`, `_minutes` | `CH1_time_m` | Enter `5` for 5 minutes |
| Hours | `_h`, `_hr`, `_hour`, `_hours` | `CH1_time_h` | Enter `2` for 2 hours |
| Milliseconds | `_ms`, `_msec`, `_millisecond`, `_milliseconds` | `CH1_time_ms` | Enter `500` for 500ms |

💡 **Unit suffixes tell the system how to interpret numbers** - they go in column names, not cell values!

---

### Excel Column Naming

**Format:** `CH[N]_time_[unit]`

**How it works**: The unit suffix in the column name tells the system what unit your values are in.

**Examples (all synonyms work):**
```
# Seconds - enter values like 10, 5, 30 (meaning seconds)
CH1_time_s       → Column for times in seconds
CH1_time_sec     → Same (synonym)
CH1_time_second  → Same (synonym)
CH1_time_seconds → Same (synonym)

# Minutes - enter values like 5, 10, 30 (meaning minutes)
CH2_time_m       → Column for times in minutes
CH2_time_min     → Same (synonym)
CH2_time_minute  → Same (synonym)
CH2_time_minutes → Same (synonym)

# Hours - enter values like 1, 2, 8 (meaning hours)
CH3_time_h       → Column for times in hours
CH3_time_hr      → Same (synonym)
CH3_time_hour    → Same (synonym)
CH3_time_hours   → Same (synonym)

# Milliseconds - enter values like 100, 500, 1000 (meaning ms)
CH4_time_ms      → Column for times in milliseconds
CH4_time_msec    → Same (synonym)
CH4_time_millisecond  → Same (synonym)
CH4_time_milliseconds → Same (synonym)
```

**Example Excel sheet:**
```
| Sections | CH1_status | CH1_time_s | CH2_status | CH2_time_min |
|----------|------------|------------|------------|--------------|
| 0        | 1          | 10         | 0          | 5            |
| 1        | 0          | 5          | 1          | 10           |
```
In this example:
- CH1: 10 means 10 **seconds** (because column is `CH1_time_s`)
- CH2: 5 means 5 **minutes** (because column is `CH2_time_min`)

💡 **The unit is in the column NAME, values are just numbers!**

---

### Text Time Units

**Format:** `TIME_<UNIT>:<values>`

**Examples:**
```txt
TIME_S:10      → 10 seconds
TIME_M:5       → 5 minutes
TIME_H:2       → 2 hours
TIME_MS:500    → 500 milliseconds
```

---

### Mixing Units

**Excel:** Each channel can use different units
```
| CH1_time_sec | CH2_time_min | CH3_time_hr |
|--------------|--------------|-------------|
| 30           | 5            | 2           |
```

**Text:** Each pattern uses one unit
```txt
PATTERN:1;CH:1;STATUS:1;TIME_S:30;REPEATS:1
PATTERN:2;CH:2;STATUS:1;TIME_M:5;REPEATS:1
PATTERN:3;CH:3;STATUS:1;TIME_H:2;REPEATS:1
```

---

### Float Values

All time units support decimal values:

```
10.5 seconds
2.5 minutes
1.5 hours
500.5 milliseconds
```

**Excel:**
```
| CH1_time_sec |
|--------------|
| 10.5         |
```

**Text:**
```txt
TIME_S:10.5
```

---

## Advanced Settings

### Synonym Support Reference

The system automatically recognizes multiple naming conventions. Use whichever you prefer!

⚠️ **Key Distinction:**
- **Parameter name synonyms** = Different names for the same thing (e.g., `freq`, `frequency`, `Hz`)
- **Time unit suffixes** = Tell what unit values are in (e.g., `_s`, `_ms`, `_hr`)

---

#### Complete Synonym List

**Time Unit Suffixes (for time, period, pulse_width columns ONLY):**
```
Seconds:      _s, _sec, _second, _seconds
Minutes:      _m, _min, _minute, _minutes
Hours:        _h, _hr, _hour, _hours
Milliseconds: _ms, _msec, _millisecond, _milliseconds
```

**Parameter Name Synonyms (column identifiers):**
```
Period:       period, T (capital only!), cycle_time, cycletime
Pulse Width:  pulse_width, pulsewidth, PW, pw, on_time, ontime
Duty Cycle:   duty_cycle, dutycycle, DC, dc, duty
Frequency:    frequency, freq, frq, f, hz, Hz
```

---

#### How Synonyms Work

**Parameter name synonyms** - these are INTERCHANGEABLE:
```
CH1_frequency = CH1_freq = CH1_f = CH1_Hz
(All mean the same parameter, values always in Hz)
```

**Time unit suffixes** - these specify VALUE units:
```
CH1_period_ms   → Enter values in milliseconds (e.g., 1000)
CH1_T_s         → Enter values in seconds (e.g., 1.0)
CH1_PW_ms       → Enter values in milliseconds (e.g., 100)
```

**Combining both**:
```
CH1_pulse_width_s   → "pulse_width" is parameter, "_s" is unit
CH1_PW_ms           → "PW" is synonym for pulse_width, "_ms" is unit
CH1_T_hr            → "T" is synonym for period, "_hr" is unit
```

---

#### What Works Where

**Time unit suffixes work for:**
```
✓ CH1_time_s          → Main time column
✓ CH1_period_ms       → Period parameter
✓ CH1_T_s             → Period (T is synonym)
✓ CH1_pulse_width_ms  → Pulse width parameter
✓ CH1_PW_s            → Pulse width (PW is synonym)
✗ CH1_frequency_Hz    → WRONG! Frequency doesn't use suffixes
✗ CH1_duty_cycle_%    → WRONG! Duty cycle doesn't use suffixes
```

**Why? Because:**
- Frequency is ALWAYS in Hz (no other unit makes sense)
- Duty cycle is ALWAYS in % (no other unit makes sense)
- Time/period/pulse_width CAN be in different units (ms, s, min, hr)

---

#### Synonym Usage Examples

**Time column examples (all equivalent):**
```
CH1_time_s
CH1_time_sec
CH1_time_second
CH1_time_seconds
```

**Parameter name examples (different parameters):**
```
# Period - can add time unit
CH1_period      → Values in ms (default)
CH1_T           → Same (T is synonym for period)
CH1_period_s    → Values in seconds
CH1_T_ms        → Values in milliseconds

# Pulse Width - can add time unit  
CH1_pulse_width → Values in ms (default)
CH1_PW          → Same (PW is synonym)
CH1_PW_s        → Values in seconds
CH1_on_time_ms  → Values in milliseconds

# Duty Cycle - NO time unit (always %)
CH1_duty_cycle  → Values in % (always)
CH1_DC          → Same (DC is synonym)

# Frequency - NO time unit (always Hz)
CH1_frequency   → Values in Hz (always)
CH1_freq        → Same (synonym)
CH1_f           → Same (synonym)
CH1_Hz          → Same (Hz is a NAME synonym, not a unit!)
```

---

#### Mixed Synonym Example

**All these Excel sheets are valid:**

**Style 1: Full names with explicit units**
```
| CH1_status | CH1_time_seconds | CH1_frequency | CH1_pulse_width_ms |
```

**Style 2: Short names**
```
| CH1_status | CH1_time_s | CH1_f | CH1_PW |
```

**Style 3: Alternative names with units**
```
| CH1_status | CH1_time_sec | CH1_freq | CH1_on_time_ms |
```

**Style 4: Mixed (also valid!)**
```
| CH1_status | CH1_time_s | CH1_frequency | CH1_PW_ms |
```

💡 **Best Practice**: Use one consistent style per file for readability.

---

#### Case Sensitivity Notes

**Case-insensitive (work in any case):**
- Time units: `_s`, `_S`, `_Sec`, `_SEC` all work
- Pulse parameters: `frequency`, `Frequency`, `FREQUENCY` all work
- Most synonyms: `pw`, `PW`, `Pw` all work

**Case-sensitive exceptions:**
- `T` must be capital (lowercase `t` rejected as ambiguous)
- This is the only case-sensitive synonym

**Why `T` must be capital:**
```
❌ CH1_t      → Ambiguous (time? period?)
✓ CH1_T      → Clear (period)
✓ CH1_period → Also clear
```

---

### Pattern Compression

**Automatic:** Detects repeated patterns in commands.

**Example:**
```
Original: ON 1s, OFF 1s, ON 1s, OFF 1s... (100 times)
Compressed: ON 1s, OFF 1s, REPEAT 100
```

**Benefits:**
- Reduces memory usage
- Faster upload to Arduino
- Clearer command output

**Configuration:** Automatic, no settings required.

---

### Custom Time Base

**Default:** 10ms tick resolution

**Impact:**
- Minimum command duration: 10ms
- Timing precision: ±10ms
- Memory efficiency balance

**Not user-configurable** (firmware constant).

---

### Memory Limits

**Arduino Uno:**
- Max commands: ~200-300
- EEPROM: 1KB for patterns
- Recommendation: Use pattern compression

**Arduino Due:**
- Max commands: ~1000-1500
- EEPROM: 4KB for patterns
- Better for complex protocols

**Arduino Mega:**
- Max commands: ~400-600
- EEPROM: 4KB for patterns
- Good balance

---

### Validation Settings

**Automatic validation:**
- ✓ Time unit consistency
- ✓ Pulse parameter validity
- ✓ Channel number continuity
- ✓ Duty cycle range (0-100%)
- ✓ Status values (0 or 1)
- ✓ Start time format

**Error handling:**
- Clear error messages
- Line/column identification (Excel)
- Command number (Text)
- Suggested fixes

---

## See Also

- [Protocol Formats](PROTOCOL_FORMATS.md) - Format specifications
- [Templates](TEMPLATES.md) - Example configurations
- [Usage Guide](USAGE.md) - How to apply settings

---

*Last Updated: November 8, 2025*
