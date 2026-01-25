# Protocol Syntax Reference (v2.3.0)

A detailed technical reference for Light Controller protocol syntax, covering punctuation marks, format components, placeholders, and structure.

> ✅ **Syntax Validation**: Use `python syntax_check.py <protocol_file>` to validate syntax before running!

---

## Table of Contents

- [Protocol Syntax Reference (v2.3.0)](#protocol-syntax-reference-v230)
  - [Table of Contents](#table-of-contents)
  - [Document Purpose](#document-purpose)
  - [Protocol Structure Overview](#protocol-structure-overview)
    - [Text Protocol (.txt) Structure](#text-protocol-txt-structure)
    - [Excel Protocol (.xlsx) Structure](#excel-protocol-xlsx-structure)
  - [Punctuation \& Delimiter Reference](#punctuation--delimiter-reference)
    - [Semicolon `;` - Field Separator](#semicolon----field-separator)
    - [Colon `:` - Key-Value Separator](#colon----key-value-separator)
    - [Comma `,` - Value List Separator](#comma----value-list-separator)
    - [Parentheses `()` - RAMP Segment Delimiters](#parentheses----ramp-segment-delimiters)
    - [Pipe `|` - RAMP Option Separator](#pipe----ramp-option-separator)
    - [Curly Braces `{}` - Python Dictionary Blocks](#curly-braces----python-dictionary-blocks)
    - [Single Quotes `'` - String Keys in Dicts](#single-quotes----string-keys-in-dicts)
    - [Hash `#` - Comment Marker](#hash----comment-marker)
  - [Text Protocol Components](#text-protocol-components)
    - [PATTERN Command](#pattern-command)
    - [RAMP Command](#ramp-command)
    - [START\_TIME Block](#start_time-block)
    - [WAIT\_STATUS Block](#wait_status-block)
    - [WAIT\_PULSE Block](#wait_pulse-block)
    - [CALIBRATION\_FACTOR](#calibration_factor)
    - [Comments](#comments)
  - [Excel Protocol Components](#excel-protocol-components)
    - [Sheet Names](#sheet-names)
    - [Column Naming](#column-naming)
    - [Time Unit Suffixes](#time-unit-suffixes)
  - [RAMP Segment Syntax (Detailed)](#ramp-segment-syntax-detailed)
    - [L Mode (Linear)](#l-mode-linear)
    - [C Mode (Cosine)](#c-mode-cosine)
    - [I Mode (Ease-In)](#i-mode-ease-in)
    - [O Mode (Ease-Out)](#o-mode-ease-out)
    - [X Mode (Custom t-Range)](#x-mode-custom-t-range)
    - [F Mode (Custom Functions)](#f-mode-custom-functions)
  - [Placeholder Reference](#placeholder-reference)
    - [Pattern Command Placeholders](#pattern-command-placeholders)
    - [RAMP Placeholders](#ramp-placeholders)
    - [Time Placeholders](#time-placeholders)
    - [Pulse Placeholders](#pulse-placeholders)
  - [Examples with Annotations](#examples-with-annotations)
    - [Basic Pattern (Annotated)](#basic-pattern-annotated)
    - [Multi-Segment RAMP (Annotated)](#multi-segment-ramp-annotated)
    - [Complete Protocol (Annotated)](#complete-protocol-annotated)
  - [Quick Reference Card](#quick-reference-card)
    - [Punctuation Summary](#punctuation-summary)
    - [Mode Quick Reference](#mode-quick-reference)
  - [See Also](#see-also)
    - [Valid Protocol Examples](#valid-protocol-examples)

---

## Document Purpose

This reference provides:
- **Detailed syntax rules** for each protocol element
- **Punctuation mark meanings** and when to use each
- **Placeholder definitions** with valid values
- **Format validation rules** for error-free protocols

For conceptual overview, see [PROTOCOL_FORMATS.md](PROTOCOL_FORMATS.md).
For RAMP/easing details, see [PWM_RAMP_CONTROL.md](PWM_RAMP_CONTROL.md).

---

## Protocol Structure Overview

### Text Protocol (.txt) Structure

```txt
┌─────────────────────────────────────────────────────────────┐
│ # Comments (optional)                                       │
├─────────────────────────────────────────────────────────────┤
│ PATTERN commands (one or more)                              │
│   └── with optional RAMP or PULSE                           │
├─────────────────────────────────────────────────────────────┤
│ START_TIME block (required)                                 │
├─────────────────────────────────────────────────────────────┤
│ WAIT_STATUS block (optional)                                │
├─────────────────────────────────────────────────────────────┤
│ WAIT_PULSE block (optional)                                 │
├─────────────────────────────────────────────────────────────┤
│ LOOP block (optional)                                       │
├─────────────────────────────────────────────────────────────┤
│ CALIBRATION_FACTOR (optional)                               │
└─────────────────────────────────────────────────────────────┘
```

### Excel Protocol (.xlsx) Structure

```
┌─────────────────────────────────────────────────────────────┐
│ Sheet: "protocol" (required, lowercase!)                    │
│   └── Columns: Sections, CH[N]_status, CH[N]_time_[unit]    │
│   └── Optional: CH[N]_ramp, CH[N]_frequency, CH[N]_period   │
├─────────────────────────────────────────────────────────────┤
│ Sheet: "start_time" (required, lowercase!)                  │
│   └── Row-based: Channel | CH1 | CH2 | ...                  │
│   └── OR Column-based: Channels | Start_time | Wait_status  │
├─────────────────────────────────────────────────────────────┤
│ Sheet: "calibration" (optional, lowercase!)                 │
│   └── Single column: CALIBRATION_FACTOR                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Punctuation & Delimiter Reference

### Semicolon `;` - Field Separator

Separates major fields within a PATTERN command.

```txt
PATTERN:1 ; CH:1 ; STATUS:0,1 ; TIME_MS:5000,5000 ; REPEATS:10
         ↑      ↑             ↑                   ↑
    separators between major fields
```

**Usage:**
- Always between PATTERN, CH, STATUS/RAMP, TIME_*, REPEATS, PULSE
- No space required (but spaces are allowed)
- Must have exactly one `;` between each field

### Colon `:` - Key-Value Separator

Separates parameter name from its value(s).

```txt
PATTERN : 1    CH : 1    STATUS : 0,1    TIME_MS : 5000,5000
        ↑       ↑               ↑                ↑
    key:value pairs
```

**Usage:**
- Directly follows parameter name
- No space required (but spaces are allowed)
- Also used in time format: `21:00:30`

### Comma `,` - Value List Separator

Separates multiple values within a single parameter.

```txt
STATUS:0,1,0    TIME_MS:5000,10000,5000    RAMP:(I:0,255,3000),(O:255,0,3000)
       ↑ ↑             ↑      ↑                   ↑ ↑ ↑       ↑
   value separators within parameters
```

**Usage:**
- Between status values: `STATUS:0,1,0`
- Between time values: `TIME_MS:1000,2000,3000`
- Between PWM values in RAMP segment: `I:0,255,5000`
- Between RAMP segments: `(I:0,255,3000),(O:255,0,3000)`
- Between pulse parameters for multiple states

### Parentheses `()` - RAMP Segment Delimiters

Enclose each RAMP segment specification.

```txt
RAMP: ( I:0,255,3000 ) , ( L:255,255,1000 ) , ( O:255,0,3000 )
      ↑              ↑   ↑                ↑   ↑              ↑
      segment 1          segment 2            segment 3
```

**Usage:**
- Each RAMP segment must be wrapped in parentheses
- Multiple segments separated by commas
- Required for new format (v2.2.3+)

### Pipe `|` - RAMP Option Separator

Separates main parameters from optional t-range in X mode.

```txt
RAMP:(X:0,255,5000 | 0,1)    (X:0,255,5000 | 1,2)
                   ↑                       ↑
         t-range separator (t_start,t_end)
```

**Usage:**
- Only in X mode (custom t-range)
- Format: `(X:start,end,duration|t_start,t_end)`
- t_start and t_end are floats in range [0, 2]

### Curly Braces `{}` - Python Dictionary Blocks

Enclose START_TIME, WAIT_STATUS, WAIT_PULSE dictionaries.

```txt
START_TIME: {
    'CH1': '21:00',
    'CH2': 120
}
```

**Usage:**
- Must start with `{` and end with `}`
- Can span multiple lines
- Contains key-value pairs in Python dict format

### Single Quotes `'` - String Keys in Dicts

Wrap channel names and string values in dictionary blocks.

```txt
START_TIME: {
    'CH1': '21:00',     ← both key and string value in quotes
    'CH2': 120          ← key in quotes, numeric value without
}
```

**Usage:**
- Channel names: `'CH1'`, `'CH2'`
- Time strings: `'21:00'`, `'2025-01-01 06:00:00'`
- Numeric values (countdown) don't need quotes

### Hash `#` - Comment Marker

Starts a comment line (everything after is ignored).

```txt
# This entire line is a comment
PATTERN:1;CH:1;...  # Inline comment (NOT supported!)
```

**Usage:**
- Must be at start of line (after optional whitespace)
- Entire line is ignored
- Inline comments are NOT supported

---

## Text Protocol Components

### PATTERN Command

**Full Syntax:**
```
PATTERN:<id>;CH:<channel>;STATUS:<states>;TIME_<UNIT>:<durations>;REPEATS:<count>[;PULSE:<params>]
```

OR with RAMP:
```
PATTERN:<id>;CH:<channel>;RAMP:<segments>;REPEATS:<count>
```

**Field Breakdown:**

| Field   | Syntax                      | Description                 | Required |
| ------- | --------------------------- | --------------------------- | -------- |
| PATTERN | `PATTERN:<n>`               | Pattern ID, starts at 1     | Yes      |
| CH      | `CH:<n>`                    | Channel number, starts at 1 | Yes      |
| STATUS  | `STATUS:<v1>,<v2>,...`      | PWM values (0-255)          | Yes*     |
| RAMP    | `RAMP:<segments>`           | Gradient transitions        | Yes*     |
| TIME_*  | `TIME_<UNIT>:<t1>,<t2>,...` | Durations                   | Yes*     |
| REPEATS | `REPEATS:<n>`               | Repetition count            | Yes      |
| PULSE   | `PULSE:<params>`            | Pulse modulation            | No       |

*Either STATUS+TIME or RAMP required, not both.

**UNIT Options:**
| Unit         | Keyword   | Example        |
| ------------ | --------- | -------------- |
| Milliseconds | `TIME_MS` | `TIME_MS:5000` |
| Seconds      | `TIME_S`  | `TIME_S:5`     |
| Minutes      | `TIME_M`  | `TIME_M:1`     |
| Hours        | `TIME_H`  | `TIME_H:0.5`   |

**STATUS Values:**
| Value      | Meaning                                        | Output Range                |
| ---------- | ---------------------------------------------- | --------------------------- |
| `0`        | OFF (0% brightness)                            | 0                           |
| `1`        | **HIGH** (interpreted as max for channel type) | 255 (PWM) or 4095 (DAC)     |
| `0.0`      | Float: OFF (0% brightness)                     | 0                           |
| `1.0`      | **HIGH** (same as integer 1)                   | 255 (PWM) or 4095 (DAC)     |
| `0.0-1.0`  | Float: Scaled to channel max                   | 0-255 (PWM) or 0-4095 (DAC) |
| `2-255`    | Direct PWM value (8-bit)                       | For PWM channels            |
| `256-4095` | Direct DAC value (12-bit)                      | For DAC/MCP4728 channels    |

> **⚠️ IMPORTANT: Integer 1 and Float 1.0 as HIGH**
> 
> When a protocol uses only binary values `0` and `1` (or `0.0` and `1.0`) for STATUS:
> - **Integer `1`** is interpreted as **HIGH voltage (max)**: 255 for PWM, 4095 for DAC
> - **Float `1.0`** is **also** interpreted as **HIGH voltage (max)**
> - This allows simple ON/OFF control without knowing the channel type (PWM vs DAC)
> 
> For specific brightness levels, use explicit values like `STATUS:128` or `RAMP:(L:128,128,5000)`.

> **⚠️ STATUS vs RAMP for PWM/DAC Control:**
> - **STATUS** with values 0/1 is treated as **binary ON/OFF**
> - **RAMP** provides **actual PWM/DAC control** with smooth transitions
> - For precise brightness levels, use `RAMP:(L:128,128,5000)` instead of `STATUS:128`
> - In HTML visualization, STATUS patterns show the actual value provided

### RAMP Command

**Syntax:**
```
RAMP:(<mode>:<params>)[,(<mode>:<params>)...]
```

**Single Segment:**
```
RAMP:(I:0,255,5000)
      ↑  ↑ ↑   ↑
     mode│ │   └─ duration_ms
         │ └─ end_pwm
         └─ start_pwm
```

**Multiple Segments:**
```
RAMP:(I:0,255,3000),(L:255,255,1000),(O:255,0,3000)
      └─segment 1─┘ └──segment 2──┘ └─segment 3─┘
```

**X Mode with t-range:**
```
RAMP:(X:0,255,5000|0,1)
      ↑  ↑ ↑   ↑   ↑ ↑
      │  │ │   │   │ └─ t_end
      │  │ │   │   └─ t_start
      │  │ │   └─ duration_ms
      │  │ └─ end_pwm (ignored in X mode)
      │  └─ start_pwm (ignored in X mode)
      └─ mode
```

**F Mode with function name:**
```
RAMP:(F:heartbeat,2000)
      ↑  ↑         ↑
      │  │         └─ duration_ms
      │  └─ function_name
      └─ mode
```

### START_TIME Block

**Syntax:**
```txt
START_TIME: {
    '<channel>': <value>,
    ...
}
```

**Value Formats:**
| Format              | Example                 | Description           |
| ------------------- | ----------------------- | --------------------- |
| Time only           | `'21:00'`               | Today at 9 PM         |
| Time with seconds   | `'21:00:30'`            | Today at 9:00:30 PM   |
| Full datetime       | `'2025-01-15 21:00:00'` | Specific date & time  |
| Countdown (seconds) | `120`                   | Start in 2 minutes    |
| Countdown (float)   | `30.5`                  | Start in 30.5 seconds |

**Example:**
```txt
START_TIME: {
    'CH1': '21:00',
    'CH2': '2025-12-25 06:00:00',
    'CH3': 120,
    'CH4': 30.5
}
```

### WAIT_STATUS Block

**Syntax:**
```txt
WAIT_STATUS: {
    '<channel>': <0_or_1>,
    ...
}
```

**Values:**
- `0` = LED OFF during countdown (default)
- `1` = LED ON during countdown

**Example:**
```txt
WAIT_STATUS: {
    'CH1': 1,
    'CH2': 0
}
```

### WAIT_PULSE Block

**Syntax:**
```txt
WAIT_PULSE: {
    '<channel>': {'period': <ms>, 'pw': <ms>},
    ...
}
```

**Parameters:**
- `period`: Pulse cycle time in milliseconds
- `pw`: Pulse width (ON time) in milliseconds

**Example:**
```txt
WAIT_PULSE: {
    'CH1': {'period': 2000, 'pw': 100}
}
```

### LOOP Block

**Syntax:**
```txt
LOOP: {
    '<channel>': <0_or_1>,
    ...
}
```

**Values:**
- `0` = Stop after completing all patterns (default)
- `1` = Loop forever (restart patterns after completion)

**Example:**
```txt
LOOP: {
    'CH1': 1,
    'CH2': 0,
    'CH3': 1,
    'CH4': 0
}
```

> **💡 Use Case:** The LOOP block allows certain channels to continuously repeat their patterns
> while others execute once and stop. This is useful for creating ambient lighting effects
> that run indefinitely alongside scheduled events.

> **⚠️ Important:** When LOOP is enabled, the channel will **skip the wait pattern (pattern 0)** on restart.
> The wait/countdown pattern only executes once at the beginning of the protocol.
> On loop restart, execution resumes from pattern 1 (the first actual protocol pattern).

**Loop Behavior:**
1. **First execution**: Pattern 0 (wait/countdown) → Pattern 1 → Pattern 2 → ... → End
2. **Loop restart**: Skip Pattern 0 → Pattern 1 → Pattern 2 → ... → End
3. **Repeats indefinitely** until manually stopped

**Example with Wait:**
```txt
# Wait 60 seconds before starting, then loop the breathing pattern forever
WAIT_STATUS: {'CH1': 0}
START_TIME: {'CH1': 60}  # 60 second countdown

PATTERN:1;CH:1;RAMP:(C:0,255,5000);REPEATS:1  # Fade in
PATTERN:2;CH:1;RAMP:(C:255,0,5000);REPEATS:1  # Fade out

LOOP: {
    'CH1': 1
}
```

In this example:
- First cycle: Waits 60s → Fade in → Fade out
- Loop cycle: Fade in → Fade out (no wait)
- Continues indefinitely

### CALIBRATION_FACTOR

**Syntax:**
```txt
CALIBRATION_FACTOR: <float>
```

**Example:**
```txt
CALIBRATION_FACTOR: 1.00131
```

### Comments

**Syntax:**
```txt
# Comment text here
```

**Rules:**
- Must start with `#` (after optional whitespace)
- Everything after `#` is ignored
- Multi-line: each line needs its own `#`
- Inline comments NOT supported

---

## Excel Protocol Components

> ⚠️ **LIMITATION**: Excel format does **NOT** support RAMP mode.  
> Excel protocols only support STATUS/TIME patterns. For gradient/easing transitions, use Text format.

### Sheet Names

**⚠️ CRITICAL: Sheet names MUST be lowercase!**

| Sheet       | Name          | Required |
| ----------- | ------------- | -------- |
| Protocol    | `protocol`    | Yes      |
| Start Time  | `start_time`  | Yes      |
| Calibration | `calibration` | No       |

**❌ WRONG:** `Protocol`, `PROTOCOL`, `Start_Time`, `Calibration`
**✅ CORRECT:** `protocol`, `start_time`, `calibration`

### Column Naming

**Pattern:**
```
CH<N>_<parameter>[_<unit>]
```

**Components:**
| Part          | Description          | Example                  |
| ------------- | -------------------- | ------------------------ |
| `CH<N>`       | Channel number       | `CH1`, `CH2`, `CH3`      |
| `_`           | Underscore separator |                          |
| `<parameter>` | Parameter name       | `status`, `time`, `ramp` |
| `_<unit>`     | Optional time unit   | `_s`, `_ms`, `_min`      |

**Examples:**
```
CH1_status        ← Channel 1, status values
CH1_time_sec      ← Channel 1, time in seconds
CH2_time_ms       ← Channel 2, time in milliseconds
CH3_frequency     ← Channel 3, frequency (Hz)
CH1_ramp          ← Channel 1, ramp specification
```

### Time Unit Suffixes

**Apply to column names only:**

| Suffix         | Unit         | Example Column | Value `10` means |
| -------------- | ------------ | -------------- | ---------------- |
| `_ms`, `_msec` | Milliseconds | `CH1_time_ms`  | 10 ms            |
| `_s`, `_sec`   | Seconds      | `CH1_time_sec` | 10 seconds       |
| `_m`, `_min`   | Minutes      | `CH1_time_min` | 10 minutes       |
| `_h`, `_hr`    | Hours        | `CH1_time_hr`  | 10 hours         |

**Column name synonyms (all equivalent):**
```
CH1_time_s = CH1_time_sec = CH1_time_second = CH1_time_seconds
CH1_time_m = CH1_time_min = CH1_time_minute = CH1_time_minutes
CH1_time_h = CH1_time_hr = CH1_time_hour = CH1_time_hours
CH1_time_ms = CH1_time_msec = CH1_time_millisecond = CH1_time_milliseconds
```

---

## RAMP Segment Syntax (Detailed)

### L Mode (Linear)

**Syntax:** `(L:<start>,<end>,<duration>)`

**Parameters:**
| Name     | Type | Range | Description    |
| -------- | ---- | ----- | -------------- |
| start    | int  | 0-255 | Starting PWM   |
| end      | int  | 0-255 | Ending PWM     |
| duration | int  | >0    | Duration in ms |

**Examples:**
```txt
(L:0,255,5000)      # Linear 0→255 over 5 seconds
(L:255,255,2000)    # Hold at 255 for 2 seconds (constant)
(L:200,50,3000)     # Linear 200→50 (descending) over 3 seconds
```

### C Mode (Cosine)

**Syntax:** `(C:<start>,<end>,<duration>)`

**Behavior:** Uses f(t) = (1 - cos(πt)) / 2 over t∈[0,1], scaled to PWM range.

**Examples:**
```txt
(C:0,255,5000)      # Cosine ease-in 0→255 over 5 seconds
(C:255,0,5000)      # Cosine ease-out 255→0 over 5 seconds
(C:50,200,3000)     # Cosine 50→200 over 3 seconds
```

### I Mode (Ease-In)

**Syntax:** `(I:<start>,<end>,<duration>)`

**Behavior:** Slow start, accelerating end. Uses t∈[0,0.5] of cosine curve.

**Examples:**
```txt
(I:0,255,5000)      # Ease-in 0→255 (slow start)
(I:100,255,3000)    # Ease-in 100→255
```

### O Mode (Ease-Out)

**Syntax:** `(O:<start>,<end>,<duration>)`

**Behavior:** Fast start, decelerating end. Uses t∈[0.5,1] of cosine curve.

**Examples:**
```txt
(O:255,0,5000)      # Ease-out 255→0 (slow end)
(O:200,50,3000)     # Ease-out 200→50
```

### X Mode (Custom t-Range)

**Syntax:** `(X:<start>,<end>,<duration>|<t_start>,<t_end>)`

**⚠️ IMPORTANT:** In X mode, `start` and `end` PWM values are **IGNORED**! Output is `255 * f(t)`.

**t-Range → Output:**
| t_start | t_end | f(t) range | PWM output              |
| ------- | ----- | ---------- | ----------------------- |
| 0       | 1     | 0 → 1      | 0 → 255                 |
| 1       | 2     | 1 → 0      | 255 → 0                 |
| 0       | 2     | 0 → 1 → 0  | 0 → 255 → 0 (breathing) |
| 0       | 0.5   | 0 → 0.5    | 0 → 127.5               |
| 0.5     | 1     | 0.5 → 1    | 127.5 → 255             |

**Examples:**
```txt
(X:0,255,5000|0,1)      # Rise: 0→255 over 5 seconds
(X:0,255,5000|1,2)      # Fall: 255→0 over 5 seconds
(X:0,255,10000|0,2)     # Breathing: 0→255→0 over 10 seconds
```

### F Mode (Custom Functions)

**Syntax:** `(F:<func_name>,<duration>)`

**Built-in Functions:**
| Name        | Description                  |
| ----------- | ---------------------------- |
| `heartbeat` | Double-pulse heartbeat       |
| `bounce`    | Bounce effect                |
| `sine_wave` | Full sine wave               |
| `sawtooth`  | Linear ramp up, instant drop |
| `triangle`  | Linear ramp up and down      |
| `myfunc`    | User-defined placeholder     |

**Examples:**
```txt
(F:heartbeat,2000)      # Heartbeat over 2 seconds
(F:bounce,3000)         # Bounce over 3 seconds
(F:sine_wave,5000)      # Sine wave over 5 seconds
```

See [F_MODE_CUSTOM_FUNCTIONS.md](F_MODE_CUSTOM_FUNCTIONS.md) for custom function creation.

---

## Placeholder Reference

### Pattern Command Placeholders

| Placeholder   | Description    | Valid Values             | Default |
| ------------- | -------------- | ------------------------ | ------- |
| `<id>`        | Pattern number | 1, 2, 3, ...             | N/A     |
| `<channel>`   | Channel number | 1, 2, 3, ...             | N/A     |
| `<states>`    | PWM values     | 0-255, comma-separated   | N/A     |
| `<durations>` | Time values    | Positive integers/floats | N/A     |
| `<count>`     | Repeat count   | ≥1 integer               | N/A     |

### RAMP Placeholders

| Placeholder   | Description   | Valid Values            |
| ------------- | ------------- | ----------------------- |
| `<mode>`      | Easing mode   | L, C, I, O, X, F        |
| `<start>`     | Start PWM     | 0-255                   |
| `<end>`       | End PWM       | 0-255                   |
| `<duration>`  | Duration (ms) | >0 integer              |
| `<t_start>`   | t range start | 0.0-2.0 float           |
| `<t_end>`     | t range end   | 0.0-2.0 float           |
| `<func_name>` | Function name | heartbeat, bounce, etc. |

### Time Placeholders

| Placeholder   | Description      | Examples              |
| ------------- | ---------------- | --------------------- |
| `<time>`      | Time of day      | '21:00', '14:30:45'   |
| `<datetime>`  | Full date+time   | '2025-01-15 21:00:00' |
| `<countdown>` | Seconds from now | 120, 30.5             |

### Pulse Placeholders

| Placeholder | Description       | Valid Values |
| ----------- | ----------------- | ------------ |
| `<period>`  | Pulse period (ms) | 100-60000    |
| `<pw>`      | Pulse width (ms)  | 1 to period  |

---

## Examples with Annotations

### Basic Pattern (Annotated)

```txt
PATTERN:1;CH:1;STATUS:0,255;TIME_S:5,10;REPEATS:3
│       │ │  │ │      │ │   │      │ │  │       │
│       │ │  │ │      │ │   │      │ │  └───────┴─ repeat 3 times
│       │ │  │ │      │ │   │      │ └─ 10 seconds for STATUS:255
│       │ │  │ │      │ │   │      └─ 5 seconds for STATUS:0
│       │ │  │ │      │ │   └─ times in seconds
│       │ │  │ │      │ └─ second status: full brightness (255)
│       │ │  │ │      └─ first status: off (0)
│       │ │  │ └─ status values
│       │ │  └─ channel 1
│       │ └─ pattern ID
│       └─ pattern number 1
└─ pattern command
```

### Multi-Segment RAMP (Annotated)

```txt
RAMP:(I:0,255,3000),(L:255,255,1000),(O:255,0,3000)
│     │ │ │   │       │ │   │   │       │ │   │ │
│     │ │ │   │       │ │   │   │       │ │   │ └─ 3 second duration
│     │ │ │   │       │ │   │   │       │ │   └─ end at 0 (off)
│     │ │ │   │       │ │   │   │       │ └─ start at 255
│     │ │ │   │       │ │   │   │       └─ ease-out mode
│     │ │ │   │       │ │   │   └─ 1 second hold duration
│     │ │ │   │       │ │   └─ stay at 255
│     │ │ │   │       │ └─ start at 255
│     │ │ │   │       └─ linear mode (constant hold)
│     │ │ │   └─ 3 second duration
│     │ │ └─ end at 255 (full)
│     │ └─ start at 0 (off)
│     └─ ease-in mode
└─ RAMP command

Result: Slow fade-in (3s) → Hold bright (1s) → Slow fade-out (3s)
```

### Complete Protocol (Annotated)

```txt
# ===================================
# Daily Light Schedule - Lab Room
# ===================================

# Morning wake-up: Slow sunrise effect
PATTERN:1;CH:1;RAMP:(I:0,255,1800000);REPEATS:1
#                    ↑ 30-minute ease-in from 0 to full brightness

# Day: Full brightness for 8 hours
PATTERN:2;CH:1;STATUS:255;TIME_H:8;REPEATS:1
#              ↑ constant 255   ↑ 8 hours

# Evening: Gradual sunset
PATTERN:3;CH:1;RAMP:(O:255,0,900000);REPEATS:1
#                    ↑ 15-minute ease-out to off

# Night: Soft breathing indicator
PATTERN:4;CH:1;RAMP:(X:0,255,4000|0,1),(X:255,0,4000|1,2);REPEATS:100
#                    ↑ 4s rise            ↑ 4s fall
#                    ↑ breathing: 8 seconds per cycle, 100 cycles

# Start at 6 AM with visible countdown indicator
START_TIME: {
    'CH1': '06:00'
}

WAIT_STATUS: {
    'CH1': 1        # LED on during countdown
}

WAIT_PULSE: {
    'CH1': {'period': 2000, 'pw': 100}  # Slow blink during wait
}

CALIBRATION_FACTOR: 1.00131
```

---

## Quick Reference Card

### Punctuation Summary

| Symbol | Name         | Usage                       |
| ------ | ------------ | --------------------------- |
| `;`    | Semicolon    | Field separator in PATTERN  |
| `:`    | Colon        | Key-value separator         |
| `,`    | Comma        | Value list separator        |
| `()`   | Parentheses  | RAMP segment wrapper        |
| `\|`   | Pipe         | t-range separator in X mode |
| `{}`   | Curly braces | Dictionary block            |
| `'`    | Single quote | String key/value            |
| `#`    | Hash         | Comment marker              |

### Mode Quick Reference

| Mode | Syntax               | Curve Shape           |
| ---- | -------------------- | --------------------- |
| L    | `(L:start,end,dur)`  | Straight line         |
| C    | `(C:start,end,dur)`  | S-curve (full cosine) |
| I    | `(I:start,end,dur)`  | Slow start, fast end  |
| O    | `(O:start,end,dur)`  | Fast start, slow end  |
| X    | `(X:_,_,dur\|t0,t1)` | Custom cosine range   |
| F    | `(F:name,dur)`       | Custom function       |

---

## See Also

- [PROTOCOL_FORMATS.md](PROTOCOL_FORMATS.md) - Format overview and examples
- [PWM_RAMP_CONTROL.md](PWM_RAMP_CONTROL.md) - Easing and ramp details
- [F_MODE_CUSTOM_FUNCTIONS.md](F_MODE_CUSTOM_FUNCTIONS.md) - Custom function guide

---

## Syntax Validation

### Using syntax_check.py

Before running a protocol, validate it using the syntax checker:

```bash
# Basic validation
python syntax_check.py examples/1min_test.txt

# Strict mode (warnings = errors)
python syntax_check.py protocol.txt --strict

# Check multiple files
python syntax_check.py examples/*.txt

# Quiet mode (errors only)
python syntax_check.py protocol.txt --quiet
```

### Error Detection

The syntax checker validates:

| Check                 | Description                                      |
| --------------------- | ------------------------------------------------ |
| **Field names**       | Detects typos like `PATERN` → suggests `PATTERN` |
| **Required fields**   | Ensures PATTERN, CH, REPEATS present             |
| **RAMP syntax**       | Validates mode, parameters, t-range              |
| **PULSE format**      | Validates `T<period>pw<width>` format            |
| **Dictionary blocks** | START_TIME, WAIT_STATUS, WAIT_PULSE              |
| **Channel names**     | Validates CH1, CH2 format                        |
| **Value ranges**      | Warns for unusual values                         |

### Fuzzy Matching

The checker provides correction suggestions for typos:

```
Line 4 - Unknown command or block
  Content: PATERN:1;CH:1;STATUS:255,0;TIME_MS:1000,1000;REPEATS:5
  Did you mean:
    • PATTERN
```

### Programmatic Usage

```python
from syntax_check import check_protocol, ProtocolSyntaxChecker

# Simple check
is_valid, errors, warnings = check_protocol('protocol.txt')

# With checker instance
checker = ProtocolSyntaxChecker(strict_mode=True)
is_valid, errors, warnings = checker.check_file('protocol.txt')

# Check string content
is_valid, errors, warnings = checker.check_string(protocol_content)
```

### Valid Protocol Examples

| Folder                                                 | Description                         | Calibration |
| ------------------------------------------------------ | ----------------------------------- | ----------- |
| [auto_calibration/](../examples/auto_calibration/)     | **Recommended** - Modern protocols  | Automatic   |
| [preset_calibration/](../examples/preset_calibration/) | Legacy protocols with manual factor | Manual      |
| [ramp_easing/](../examples/ramp_easing/)               | RAMP mode demonstrations            | Various     |

---

*Last Updated: January 2025 | Light Controller v2.3.0*
