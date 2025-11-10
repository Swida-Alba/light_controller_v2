# Protocol Formats

Complete specification of Excel and Text protocol formats.

---

## Table of Contents

- [Overview](#overview)
- [Excel Format](#excel-format)
- [Text Format](#text-format)
- [Format Comparison](#format-comparison)
- [Best Practices](#best-practices)

---

## Overview

Light Controller V2.2 supports two protocol formats:

| Format | Extension | Best For |
|--------|-----------|----------|
| Excel | `.xlsx` | Visual editing, spreadsheet users, complex schedules |
| Text | `.txt` | Version control, programmers, quick edits |

Both formats support all features including:
- Multi-channel control
- Pulse frequency modulation
- Flexible timing units
- Start time scheduling
- Calibration factors

---

## Excel Format

### Required Structure

Excel files **must** contain:
1. **protocol** sheet - defines channel patterns
2. **start_time** sheet - defines when to start

Optional:
3. **calibration** sheet - reuse calibration factor

---

### Protocol Sheet

Defines the light control patterns.

#### Basic Format

| Sections | CH1_status | CH1_time_sec | CH2_status | CH2_time_sec |
|----------|------------|--------------|------------|--------------|
| 0        | 1          | 10           | 0          | 10           |
| 1        | 0          | 10           | 1          | 10           |
| 2        | 1          | 10           | 0          | 10           |

#### Column Naming Convention

**Required pattern:**
```
CH[N]_status     - LED state (0=OFF, 1=ON)
CH[N]_time_[unit] - Duration
```

**Time unit suffixes (apply to column names only):**
- **Seconds**: `_s`, `_sec`, `_second`, `_seconds`
- **Minutes**: `_m`, `_min`, `_minute`, `_minutes`
- **Hours**: `_h`, `_hr`, `_hour`, `_hours`
- **Milliseconds**: `_ms`, `_msec`, `_millisecond`, `_milliseconds`

**Example:**
```
CH1_time_s       → Times in this column are in seconds
CH1_time_sec     → Same (synonym)
CH2_time_min     → Times in this column are in minutes
```

💡 **Important**: Unit suffixes only apply to column NAMES. The numbers in the cells stay as-is (e.g., if column is `CH1_time_s`, enter `10` for 10 seconds, not `10000`).

**Example:**
```
CH1_time_sec   - Channel 1, times in seconds (e.g., enter 10 for 10 seconds)
CH1_time_s     - Same as above (synonym)
CH2_time_min   - Channel 2, times in minutes (e.g., enter 5 for 5 minutes)
CH2_time_m     - Same as above (synonym)
CH3_time_hour  - Channel 3, times in hours (e.g., enter 2 for 2 hours)
CH3_time_hr    - Same as above (synonym)
CH3_time_h     - Same as above (synonym)
CH4_time_ms    - Channel 4, times in milliseconds (e.g., enter 500 for 500ms)
CH4_time_msec  - Same as above (synonym)
```

💡 **Unit suffixes tell the system how to interpret the numbers** - you enter values in that unit!

#### Channel Numbers

- Must start at 1
- Must be continuous: CH1, CH2, CH3... (no skipping)
- Order doesn't matter in columns
- Can mix time units per channel

**✅ Valid:**
```
CH1_status, CH1_time_sec, CH2_status, CH2_time_min, CH3_status, CH3_time_hr
```

**❌ Invalid:**
```
CH1_status, CH3_status  (missing CH2)
CH2_status, CH1_status  (doesn't start at 1)
```

#### Time Values

- **Integers**: `10`, `5`, `3600`
- **Floats**: `10.5`, `2.5`, `0.1`
- **Automatic conversion** to milliseconds internally

**Examples:**
```
10 seconds = 10000 ms
2.5 minutes = 150000 ms
1.5 hours = 5400000 ms
```

---

### Pulse Control Columns (Optional)

Add pulse parameters for each channel:

#### Option 1: Frequency + Pulse Width

| CH1_status | CH1_time_ms | CH1_frequency | CH1_pulse_width |
|------------|-------------|---------------|-----------------|
| 0          | 10000       | 0             | 0               |
| 1          | 10000       | 1.0           | 100             |

#### Option 2: Frequency + Duty Cycle

| CH1_status | CH1_time_ms | CH1_frequency | CH1_duty_cycle |
|------------|-------------|---------------|----------------|
| 0          | 10000       | 0             | 0              |
| 1          | 10000       | 2.0           | 10%            |

#### Option 3: Period + Pulse Width

| CH1_status | CH1_time_ms | CH1_period | CH1_pulse_width |
|------------|-------------|------------|-----------------|
| 0          | 10000       | 0          | 0               |
| 1          | 10000       | 1000       | 200             |

#### Option 4: Period + Duty Cycle

| CH1_status | CH1_time_ms | CH1_period | CH1_duty_cycle |
|------------|-------------|------------|----------------|
| 0          | 10000       | 0          | 0              |
| 1          | 10000       | 500        | 20             |

#### Pulse Column Details

**Frequency** (`CH[N]_frequency`):
- **Column name synonyms**: `frequency`, `freq`, `frq`, `f`, `hz`, `Hz`
- **Units**: Hz (always - no unit suffix needed!)
- **Range**: 0.01 to 100 Hz
- **Special value**: `0` = no pulsing (solid state)
- **Values**: Enter frequency directly (e.g., `1.0` for 1 Hz)

**Pulse Width** (`CH[N]_pulse_width`):
- **Column name synonyms**: `pulse_width`, `pulsewidth`, `PW`, `pw`, `on_time`, `ontime`
- **Units**: Milliseconds by default
- **Can add time suffix**: `CH1_pulse_width_ms`, `CH1_PW_s`, etc.
- **Range**: 1 to period duration
- **Constraint**: Must be ≤ period (1000/frequency)
- **Values**: Enter duration (e.g., `100` for 100ms if no suffix, `0.1` for 0.1 seconds if `_s` suffix)

**Period** (`CH[N]_period`):
- **Column name synonyms**: `period`, `T` (capital only), `cycle_time`, `cycletime`
- **Units**: Milliseconds by default
- **Can add time suffix**: `CH1_period_ms`, `CH1_T_s`, etc.
- **Alternative to frequency**: period = 1000 / frequency
- **Example**: 1000ms period = 1 Hz
- **Values**: Enter duration (e.g., `1000` for 1000ms if no suffix, `1` for 1 second if `_s` suffix)

**Duty Cycle** (`CH[N]_duty_cycle`):
- **Column name synonyms**: `duty_cycle`, `dutycycle`, `DC`, `dc`, `duty`
- **Units**: Percentage (always - no unit suffix needed!)
- **Multiple formats accepted**:
  - Integer: `10` → 10%
  - String: `"10"` → 10%
  - With percent: `"10%"` → 10%
  - Decimal: `0.1` → 10%
  - String decimal: `"0.1"` → 10%
- **Range**: 0 to 100%

---

**⚠️ Important Unit Rules:**

1. **Time suffixes** work ONLY for:
   - Main time column: `CH1_time_s`, `CH2_time_min`, etc.
   - Period column: `CH1_period_ms`, `CH1_T_s`, etc.
   - Pulse width column: `CH1_pulse_width_ms`, `CH1_PW_s`, etc.

2. **No time suffix** for:
   - Frequency (always Hz): `CH1_frequency`, `CH1_freq`, `CH1_f`
   - Duty cycle (always %): `CH1_duty_cycle`, `CH1_DC`

3. **Examples**:
   ```
   ✓ CH1_frequency       → Values are in Hz (e.g., 1.0, 2.5)
   ✓ CH1_f               → Same (synonym)
   ✓ CH1_period_ms       → Values are in milliseconds
   ✓ CH1_T_s             → Values are in seconds
   ✓ CH1_pulse_width     → Values are in milliseconds (default)
   ✓ CH1_PW_ms           → Values are in milliseconds
   ✗ CH1_frequency_Hz    → WRONG - don't add Hz suffix!
   ✗ CH1_duty_cycle_%    → WRONG - don't add % suffix!
   ```

💡 **Column name synonyms** (like `freq`, `Hz`, `PW`) are for naming, not units. **Time suffixes** (like `_s`, `_ms`) go after the parameter name to specify units.

---

### Start Time Sheet

Defines when each channel starts.

#### Format 1: Row-Based

Best for **≤5 channels**.

| Channel     | CH1      | CH2      | CH3      |
|-------------|----------|----------|----------|
| start_time  | 21:00    | 21:00    | 21:15    |
| wait_status | 1        | 0        | 1        |

#### Format 2: Column-Based

Best for **5+ channels**.

| Channels | Start_time | Wait_status |
|----------|------------|-------------|
| CH1      | 21:00      | 1           |
| CH2      | 21:00      | 0           |
| CH3      | 21:15      | 1           |
| CH4      | 21:15      | 0           |
| CH5      | 22:00      | 1           |

**Auto-detection:**
- Program automatically detects format
- No configuration needed
- Choose format that works best for you

#### Start Time Formats

**1. Time Only** (today at specified time)
```
21:00          → Today at 9:00 PM
21:00:30       → Today at 9:00:30 PM
14:30          → Today at 2:30 PM
```

**2. Full Datetime** (specific date and time)
```
2025-11-08 21:00:00     → Nov 8, 2025 at 9 PM
2025-12-25 06:00:00     → Dec 25, 2025 at 6 AM
2026-01-01 00:00:00     → Jan 1, 2026 at midnight
```

**3. Countdown** (seconds from now)
```
120     → Start in 120 seconds (2 minutes)
30.5    → Start in 30.5 seconds
300     → Start in 300 seconds (5 minutes)
```

#### Wait Status

Controls LED state during countdown:
- `1` = LED ON during wait
- `0` = LED OFF during wait

**Use cases:**
- `1`: Shows system is ready/waiting
- `0`: Dark mode before protocol starts

---

### Calibration Sheet (Optional)

Reuse calibration factor from previous runs.

| CALIBRATION_FACTOR |
|--------------------|
| 1.00131            |

**Where to get factor:**
- From output file: `protocol_commands_YYYYMMDDHHMMSS.txt`
- Look for line: `CALIBRATION_FACTOR: 1.00131`
- Copy value to this sheet

**Benefits:**
- Skip 2-minute calibration
- Consistent timing across runs
- Faster protocol startup

---

### Synonym Support

The system automatically recognizes **multiple naming conventions** for columns. Use whichever you prefer!

#### Time Unit Synonyms (for Column Names)

**These suffixes specify what unit the VALUES in that column use:**

**Seconds:**
- `CH1_time_s` → Values are in seconds (e.g., `10` = 10 seconds)
- `CH1_time_sec`
- `CH1_time_second`
- `CH1_time_seconds`

**Minutes:**
- `CH1_time_m` → Values are in minutes (e.g., `5` = 5 minutes)
- `CH1_time_min`
- `CH1_time_minute`
- `CH1_time_minutes`

**Hours:**
- `CH1_time_h` → Values are in hours (e.g., `2` = 2 hours)
- `CH1_time_hr`
- `CH1_time_hour`
- `CH1_time_hours`

**Milliseconds:**
- `CH1_time_ms` → Values are in milliseconds (e.g., `500` = 500ms)
- `CH1_time_msec`
- `CH1_time_millisecond`
- `CH1_time_milliseconds`

💡 **These unit suffixes work for**: `time`, `period`, and `pulse_width` columns only!

#### Parameter Name Synonyms (Column Identifiers)

**These are different NAMES for the same parameter:**

**Period synonyms (all equivalent):**
- `CH1_period` ← Standard
- `CH1_T` ← Short form (capital T only!)
- `CH1_cycle_time`
- `CH1_cycletime`

⚠️ **Note**: Use capital `T` not lowercase `t` (lowercase is ambiguous)

**Pulse Width synonyms (all equivalent):**
- `CH1_pulse_width` ← Standard
- `CH1_pulsewidth`
- `CH1_PW` ← Short form
- `CH1_pw`
- `CH1_on_time`
- `CH1_ontime`

**Duty Cycle synonyms (all equivalent):**
- `CH1_duty_cycle` ← Standard (values always in %)
- `CH1_dutycycle`
- `CH1_DC` ← Short form
- `CH1_dc`
- `CH1_duty`

**Frequency synonyms (all equivalent):**
- `CH1_frequency` ← Standard (values always in Hz)
- `CH1_freq`
- `CH1_frq`
- `CH1_f` ← Short form
- `CH1_hz` ← Unit-based name
- `CH1_Hz` ← Unit-based name

⚠️ **Note**: `hz`/`Hz` are column NAME synonyms, not unit suffixes! Frequency is ALWAYS in Hz.

#### Combining Synonyms and Units

**Valid combinations:**

```
# Parameter name + time unit suffix (for period/pulse_width)
CH1_period_ms        → Period values in milliseconds
CH1_T_s              → Period values in seconds (T is synonym for period)
CH1_pulse_width_ms   → Pulse width values in milliseconds
CH1_PW_s             → Pulse width values in seconds (PW is synonym)

# Parameter name only (no unit suffix)
CH1_frequency        → Frequency in Hz (always)
CH1_freq             → Same (synonym)
CH1_f                → Same (synonym)
CH1_Hz               → Same (Hz is a NAME synonym, not a suffix!)
CH1_duty_cycle       → Duty cycle in % (always)
CH1_DC               → Same (synonym)
```

**Invalid combinations:**

```
✗ CH1_frequency_Hz   → WRONG! Frequency doesn't take unit suffixes
✗ CH1_freq_Hz        → WRONG! Same reason
✗ CH1_Hz_Hz          → WRONG! Hz is already the parameter name
✗ CH1_duty_cycle_%   → WRONG! Duty cycle doesn't take unit suffixes
✗ CH1_DC_%           → WRONG! Same reason
```

#### Examples Using Synonyms

**All of these are valid and equivalent:**

```
# Using full names
| CH1_status | CH1_time_seconds | CH1_frequency | CH1_pulse_width |

# Using short forms
| CH1_status | CH1_time_s | CH1_freq | CH1_pw |

# Using alternative names
| CH1_status | CH1_time_sec | CH1_hz | CH1_on_time |

# Mixed (also valid!)
| CH1_status | CH1_time_s | CH1_frequency | CH1_PW |
```

**Pulse parameter examples:**

```
# Using period/pulse_width
| CH1_period | CH1_pulse_width |

# Using short forms
| CH1_T | CH1_PW |

# Using frequency/duty_cycle
| CH1_freq | CH1_DC |

# Mixed styles
| CH1_T | CH1_on_time |
```

💡 **Best Practice**: Choose one style and use it consistently within each file for readability.

---

### Complete Excel Example

**Sheet: protocol**

| step | CH1_status | CH1_time_sec | CH1_frequency | CH1_duty_cycle | CH2_status | CH2_time_min |
|------|------------|--------------|---------------|----------------|------------|--------------|
| 1    | 1          | 30           | 1.0           | 10%            | 0          | 30           |
| 2    | 0          | 30           | 0             | 0              | 1          | 30           |

**Sheet: start_time**

| Channels | Start_time | Wait_status |
|----------|------------|-------------|
| CH1      | 21:00      | 1           |
| CH2      | 21:00      | 0           |

**Sheet: calibration**

| CALIBRATION_FACTOR |
|--------------------|
| 1.00131            |

**Result:**
- CH1: ON with 1Hz blink (10% duty) for 30s, then OFF for 30s
- CH2: OFF for 30 min, then ON for 30 min
- Both start at 9 PM
- CH1 visible during wait (breathing), CH2 off

---

## Text Format

### Basic Structure

```txt
# Comment lines start with #
# Empty lines are ignored

# Pattern commands
PATTERN:<id>;CH:<channel>;STATUS:<states>;TIME_<UNIT>:<durations>;REPEATS:<count>

# Optional pulse parameters
PATTERN:<id>;CH:<channel>;STATUS:<states>;TIME_<UNIT>:<durations>;REPEATS:<count>;PULSE:<params>

# Start times
START_TIME: {
    'CH1': '<time>',
    'CH2': <countdown>
}

# Optional calibration
CALIBRATION_FACTOR: <factor>
```

---

### Command Syntax

#### PATTERN Command

**Format:**
```txt
PATTERN:<id>;CH:<channel>;STATUS:<states>;TIME_<UNIT>:<durations>;REPEATS:<count>
```

**Parameters:**

- `<id>`: Pattern number (1, 2, 3, ...)
- `<channel>`: Channel number (1, 2, 3, ...)
- `<states>`: LED states
  - Single: `0` or `1`
  - Multiple: `0,1` or `1,0` or `1,0,1`
- `<UNIT>`: Time unit
  - `S` → seconds
  - `M` → minutes  
  - `H` → hours
  - `MS` → milliseconds
- `<durations>`: Time values (comma-separated if multiple states)
  - Single: `10`
  - Multiple: `5,10` or `2,3,5`
  - Floats: `2.5,3.5`
- `<count>`: Number of repetitions

**Examples:**
```txt
# Simple: 10 seconds ON, repeat 5 times
PATTERN:1;CH:1;STATUS:1;TIME_S:10;REPEATS:5

# Blink: 5s OFF, 5s ON, repeat 10 times
PATTERN:1;CH:1;STATUS:0,1;TIME_S:5,5;REPEATS:10

# Multi-state: Complex pattern
PATTERN:1;CH:1;STATUS:0,1,0;TIME_S:2,5,3;REPEATS:20
```

---

### Pulse Parameters (Optional)

#### Pulse Syntax

**Format:**
```txt
PULSE:T<period>pw<pulse_width>,T<period>pw<pulse_width>
```

**Components:**
- `T<period>`: Period in milliseconds (T1000 = 1 second period = 1 Hz)
- `pw<width>`: Pulse width in milliseconds
- Comma-separated for multiple states

**Period to Frequency Conversion:**
- T1000 = 1000ms period = 1 Hz
- T2000 = 2000ms period = 0.5 Hz  
- T500 = 500ms period = 2 Hz
- T100 = 100ms period = 10 Hz

**Examples:**
```txt
# No pulse for OFF, 1Hz 50ms pulse for ON
PULSE:T0pw0,T1000pw50

# Breathing effect: 0.5Hz (2 second period), 200ms
PULSE:T0pw0,T2000pw200

# Fast strobe: 10Hz (100ms period), 10ms
PULSE:T0pw0,T100pw10

# 2Hz blink: 500ms period, 50ms pulse
PULSE:T0pw0,T500pw50
```

#### Common Patterns

```txt
# Slow breathing (0.5 Hz)
PULSE:T0pw0,T2000pw200

# Standard blink (1 Hz)
PULSE:T0pw0,T1000pw50

# Fast flash (5 Hz)
PULSE:T0pw0,T200pw20

# Strobe effect (10 Hz)
PULSE:T0pw0,T100pw10
```

---

### START_TIME Syntax

**Format:**
```txt
START_TIME: {
    'CH1': '<time>',
    'CH2': <countdown>,
    'CH3': '<datetime>'
}
```

**Required**: Yes (must specify start time for all channels)

**Examples:**

**Time only:**
```txt
START_TIME: {
    'CH1': '21:00',
    'CH2': '21:30:00'
}
```

**Full datetime:**
```txt
START_TIME: {
    'CH1': '2025-11-08 21:00:00',
    'CH2': '2025-11-09 06:00:00'
}
```

**Countdown:**
```txt
START_TIME: {
    'CH1': 120,
    'CH2': 30.5
}
```

**Mixed:**
```txt
START_TIME: {
    'CH1': '21:00',
    'CH2': 60,
    'CH3': '2025-12-25 00:00:00'
}
```

---

### WAIT_STATUS Syntax (Optional)

**Format:**
```txt
WAIT_STATUS: {
    'CH1': 1,
    'CH2': 0
}
```

**Required**: No (optional - default is 0/OFF for all channels)

**Description**: LED state during countdown/wait period before pattern starts

**Values**:
- `1` = LED ON during countdown
- `0` = LED OFF during countdown (default)

**Example**:
```txt
# CH1 visible during wait, CH2 dark during wait
WAIT_STATUS: {
    'CH1': 1,
    'CH2': 0
}
```

---

### WAIT_PULSE Syntax (Optional)

**Format:**
```txt
WAIT_PULSE: {
    'CH1': {'period': 2000, 'pw': 100},
    'CH2': {'period': 1000, 'pw': 50}
}
```

**Required**: No (optional - no pulsing during wait period by default)

**Description**: Pulse effect during countdown/wait period (only works if WAIT_STATUS is 1 for that channel)

**Parameters**:
- `period`: Pulse period in milliseconds (e.g., 2000 = 2-second period = 0.5 Hz)
- `pw`: Pulse width in milliseconds (time LED is ON per cycle)

**Period to Frequency Conversion**:
- `period: 1000` = 1000ms = 1 second = 1 Hz
- `period: 2000` = 2000ms = 2 seconds = 0.5 Hz
- `period: 500` = 500ms = 0.5 seconds = 2 Hz

**Example**:
```txt
# CH1 pulses slowly during wait (2s period = 0.5 Hz)
WAIT_STATUS: {
    'CH1': 1
}
WAIT_PULSE: {
    'CH1': {'period': 2000, 'pw': 100}
}
```

---

### CALIBRATION_FACTOR Syntax (Optional)

**Format:**
```txt
CALIBRATION_FACTOR: <factor>
```

**Required**: No (optional - default is 1.0 if not specified)

**Description**: Time correction factor from previous calibration run

**Value**: Floating-point number (typically 1.0 ± 0.01)

**Example**:
```txt
# Apply 0.131% time correction from calibration
CALIBRATION_FACTOR: 1.00131
```

**How to obtain**:
1. Run protocol once
2. System calculates calibration factor
3. Reuse factor in next run for accurate timing

**See**: [Calibration Guide](PROTOCOL_SETTINGS.md#calibration) for details

---

### Comments

**Format:**
```txt
# This is a comment
   # Indented comment also works
```

**Rules:**
- Line must start with `#` (after whitespace)
- Everything after `#` is ignored
- Empty lines are ignored
- Use for documentation

**Example:**
```txt
# ====================================
# Daily Light Schedule
# Author: John Doe
# Created: 2025-11-08
# ====================================

# Morning phase: Gentle wake-up
PATTERN:1;CH:1;STATUS:0,1;TIME_M:1,30;REPEATS:1;PULSE:T0pw0,T2000pw200

# Day phase: Full brightness
PATTERN:2;CH:1;STATUS:1;TIME_H:8;REPEATS:1

# Evening phase: Dim down
PATTERN:3;CH:1;STATUS:1,0;TIME_M:30,1;REPEATS:1;PULSE:T2000pw200,T0pw0
```

---

### Complete Text Example

```txt
# ====================================
# Test Protocol: Multi-Channel Pulse
# ====================================

# Channel 1: Slow breathing effect
# 10 seconds OFF, 10 seconds ON with breathing
# Repeat 20 times
PATTERN:1;CH:1;STATUS:0,1;TIME_S:10,10;REPEATS:20;PULSE:T0pw0,T2000pw200

# Channel 2: Fast blink
# 5 seconds OFF, 5 seconds ON with 2Hz blink
# Repeat 40 times
PATTERN:1;CH:2;STATUS:0,1;TIME_S:5,5;REPEATS:40;PULSE:T0pw0,T500pw100

# Channel 3: Solid ON for 1 hour
PATTERN:1;CH:3;STATUS:1;TIME_H:1;REPEATS:1

# Start times (REQUIRED)
START_TIME: {
    'CH1': '21:00',      # 9 PM
    'CH2': '21:00',      # 9 PM
    'CH3': 120           # 2 minutes from now
}

# Wait status (OPTIONAL - defaults to 0/OFF if not specified)
WAIT_STATUS: {
    'CH1': 1,
    'CH2': 0,
    'CH3': 0
}

# Wait pulse (OPTIONAL - only affects channels with WAIT_STATUS=1)
WAIT_PULSE: {
    'CH1': {'period': 2000, 'pw': 100}
}

# Calibration factor (OPTIONAL - defaults to 1.0 if not specified)
CALIBRATION_FACTOR: 1.00131
```

---

## Format Comparison

### Feature Support

| Feature | Excel | Text |
|---------|-------|------|
| Multi-channel | ✓ | ✓ |
| Time units | ✓ | ✓ |
| Pulse control | ✓ | ✓ |
| Start time formats | ✓ | ✓ |
| Wait status | ✓ | ✓ |
| Wait pulse | ✓ | ✓ |
| Calibration | ✓ | ✓ |
| Comments | - | ✓ |
| Visual editing | ✓ | - |
| Version control | - | ✓ |
| Syntax highlighting | - | ✓* |

*With VS Code extension

### Pros and Cons

**Excel Format:**

Pros:
- ✓ Visual spreadsheet interface
- ✓ Easy for non-programmers
- ✓ Cell formulas for calculations
- ✓ Copy/paste patterns easily
- ✓ Familiar to most users

Cons:
- ✗ Binary format (not git-friendly)
- ✗ Requires spreadsheet software
- ✗ Harder to diff/merge
- ✗ No comments support

**Text Format:**

Pros:
- ✓ Version control friendly
- ✓ Comments supported
- ✓ Any text editor works
- ✓ Easy to diff/merge
- ✓ Scriptable/programmable

Cons:
- ✗ Manual syntax (prone to typos)
- ✗ Less visual
- ✗ Requires syntax knowledge
- ✗ No formula support

---

## Best Practices

### Naming Conventions

**Excel files:**
```
daily_schedule.xlsx
experiment_pulse_v3.xlsx
2025-11-08_calibration.xlsx
```

**Text files:**
```
daily_schedule.txt
experiment_pulse_v3.txt
2025-11-08_calibration.txt
```

### Organization

**Directory structure:**
```
protocols/
  ├── daily/
  │   ├── monday.xlsx
  │   ├── tuesday.xlsx
  │   └── ...
  ├── experiments/
  │   ├── pulse_test_1.txt
  │   ├── pulse_test_2.txt
  │   └── ...
  └── calibrations/
      ├── uno_calib.txt
      └── due_calib.txt
```

### Version Control

**For Excel:**
- Keep copies with dates
- Export to CSV for diffing
- Document changes separately

**For Text:**
- Use git
- Meaningful commit messages
- Tag stable versions

```bash
git add protocols/*.txt
git commit -m "Add breathing effect to channel 1"
git tag -a v1.2 -m "Working pulse configuration"
```

### Documentation

**In Excel:**
- Use separate sheet for notes
- Add comments to cells
- Color-code sections

**In Text:**
- Use comment headers
- Document parameters
- Explain non-obvious logic

```txt
# =================================
# PROJECT: Plant Growth Experiment
# AUTHOR: Research Team
# DATE: 2025-11-08
# VERSION: 1.2
# =================================

# DESCRIPTION:
# 16-hour light cycle with gradual
# dawn/dusk simulation
# 
# CHANNELS:
#   CH1: Red spectrum (660nm)
#   CH2: Blue spectrum (450nm)
#   CH3: White background
# =================================
```

---

## See Also

- [Templates](TEMPLATES.md) - Ready-to-use protocol templates
- [Examples](EXAMPLES.md) - Complete working examples
- [Usage Guide](USAGE.md) - How to use protocols

---

*Last Updated: November 8, 2025*
