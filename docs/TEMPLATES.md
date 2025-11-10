# Protocol Templates

Ready-to-use templates for common lighting scenarios.

> 💡 **Looking for complete working examples?** Check out the [`examples/`](../examples/) folder for fully documented protocol files you can use directly:
> - **`basic_protocol.txt`** / **`basic_protocol.xlsx`** - Fundamental features
> - **`pulse_protocol.txt`** / **`pulse_protocol.xlsx`** - Pulsing effects
> - **`wait_pulse_protocol.txt`** / **`wait_pulse_protocol.xlsx`** - Wait period control
> - **`start_time_format_examples.xlsx`** - All start time formats
>
> See [`examples/README.md`](../examples/README.md) for detailed descriptions.

---

## Table of Contents

- [Basic Templates](#basic-templates)
- [Pulse Effect Templates](#pulse-effect-templates)
- [Complex Schedule Templates](#complex-schedule-templates)
- [Experimental Templates](#experimental-templates)
- [Custom Template Guide](#custom-template-guide)

---

## Basic Templates

### Simple ON/OFF

**Use case:** Basic fixed schedule

**Excel format:**

Sheet: `protocol`
```
| Sections | CH1_status | CH1_time_hour |
|----------|------------|---------------|
| 0        | 1          | 8             |
| 1        | 0          | 16            |
```

Sheet: `start_time`
```
| Channel    | CH1   |
|------------|-------|
| start_time | 06:00 |
```

**Text format:**
```txt
# Simple 8-hour ON, 16-hour OFF
PATTERN:1;CH:1;STATUS:1;TIME_H:8;REPEATS:1
PATTERN:2;CH:1;STATUS:0;TIME_H:16;REPEATS:1

START_TIME: {'CH1': '06:00'}
```

**Result:** LED on 6 AM - 2 PM, off 2 PM - 6 AM (next day)

---

### Standard Blink

**Use case:** Simple periodic blinking

**Excel format:**

Sheet: `protocol`
```
| Sections | CH1_status | CH1_time_sec |
|----------|------------|--------------|
| 0        | 0          | 1            |
| 1        | 1          | 1            |
```

Sheet: `start_time`
```
| Channel    | CH1 |
|------------|-----|
| start_time | 60  |
```

**Text format:**
```txt
# 1 second OFF, 1 second ON, repeat 1800 times (1 hour)
PATTERN:1;CH:1;STATUS:0,1;TIME_S:1,1;REPEATS:1800

START_TIME: {'CH1': 60}
```

**Result:** Alternates OFF/ON every second for 1 hour

---

### Multi-Channel Synchronized

**Use case:** Multiple channels starting together

**Excel format:**

Sheet: `protocol`
```
| Sections | CH1_status | CH1_time_min | CH2_status | CH2_time_min | CH3_status | CH3_time_min |
|----------|------------|--------------|------------|--------------|------------|--------------|
| 0        | 1          | 30           | 1          | 30           | 1          | 30           |
| 1        | 0          | 30           | 0          | 30           | 0          | 30           |
```

Sheet: `start_time`
```
| Channels | Start_time | Wait_status |
|----------|------------|-------------|
| CH1      | 20:00      | 1           |
| CH2      | 20:00      | 0           |
| CH3      | 20:00      | 0           |
```

**Text format:**
```txt
# All channels: 30 min ON, 30 min OFF, repeat 12 times (12 hours)
PATTERN:1;CH:1;STATUS:1,0;TIME_M:30,30;REPEATS:12
PATTERN:1;CH:2;STATUS:1,0;TIME_M:30,30;REPEATS:12
PATTERN:1;CH:3;STATUS:1,0;TIME_M:30,30;REPEATS:12

START_TIME: {
    'CH1': '20:00',
    'CH2': '20:00',
    'CH3': '20:00'
}

WAIT_STATUS: {
    'CH1': 1,
    'CH2': 0,
    'CH3': 0
}
```

**Result:** All channels synchronized 30 min ON/OFF cycles starting at 8 PM

---

### Staggered Start

**Use case:** Channels starting at different times

**Excel format:**

Sheet: `protocol`
```
| Sections | CH1_status | CH1_time_min | CH2_status | CH2_time_min |
|----------|------------|--------------|------------|--------------|
| 0        | 1          | 60           | 1          | 60           |
```

Sheet: `start_time`
```
| Channels | Start_time | Wait_status |
|----------|------------|-------------|
| CH1      | 20:00      | 1           |
| CH2      | 20:30      | 1           |
```

**Text format:**
```txt
# Channel 1: Solid ON for 1 hour
PATTERN:1;CH:1;STATUS:1;TIME_H:1;REPEATS:1

# Channel 2: Solid ON for 1 hour (starts 30 min later)
PATTERN:1;CH:2;STATUS:1;TIME_H:1;REPEATS:1

START_TIME: {
    'CH1': '20:00',
    'CH2': '20:30'
}

WAIT_STATUS: {
    'CH1': 1,
    'CH2': 1
}
```

**Result:** CH1 starts at 8 PM, CH2 starts at 8:30 PM

---

## Pulse Effect Templates

### Breathing Effect

**Use case:** Gentle pulsing light (meditation, ambiance)

**Excel format:**

Sheet: `protocol`
```
| Sections | CH1_status | CH1_time_min | CH1_frequency | CH1_pulse_width |
|----------|------------|--------------|---------------|-----------------|
| 0        | 1          | 10           | 0.5           | 200             |
```

Sheet: `start_time`
```
| Channel    | CH1 |
|------------|-----|
| start_time | 60  |
```

**Text format:**
```txt
# Breathing effect: 0.5 Hz (2 sec period = 2000ms), 200ms pulse
PATTERN:1;CH:1;STATUS:1;TIME_M:10;REPEATS:1;PULSE:T2000pw200

START_TIME: {'CH1': 60}
```

**Result:** Gentle breathing effect for 10 minutes

---

### Standard Pulse Blink

**Use case:** Visible blinking indicator

**Excel format:**

Sheet: `protocol`
```
| Sections | CH1_status | CH1_time_sec | CH1_frequency | CH1_duty_cycle |
|----------|------------|--------------|---------------|----------------|
| 0        | 0          | 5            | 0             | 0              |
| 1        | 1          | 5            | 1.0           | 10%            |
```

Sheet: `start_time`
```
| Channel    | CH1   |
|------------|-------|
| start_time | 21:00 |
```

**Text format:**
```txt
**Text format:**
```txt
# Simple 1Hz blink: 5 seconds OFF, 5 seconds ON (1Hz pulse, 100ms width)
PATTERN:1;CH:1;STATUS:0,1;TIME_S:5,5;REPEATS:60;PULSE:T0pw0,T1000pw100

START_TIME: {'CH1': '21:00'}
```
```

**Result:** 5s off, 5s blinking (1Hz), repeat for 10 minutes

---

### Fast Strobe

**Use case:** Attention-grabbing effect

**Excel format:**

Sheet: `protocol`
```
| Sections | CH1_status | CH1_time_sec | CH1_frequency | CH1_pulse_width |
|----------|------------|--------------|---------------|-----------------|
| 0        | 1          | 10           | 10.0          | 10              |
```

Sheet: `start_time`
```
| Channel    | CH1 |
|------------|-----|
| start_time | 5   |
```

**Text format:**
```txt
**Text format:**
```txt
# Strobe effect: 10Hz (100ms period), 10ms pulse width
PATTERN:1;CH:1;STATUS:1;TIME_S:10;REPEATS:1;PULSE:T100pw10

START_TIME: {'CH1': 0}
```
```

**Result:** Rapid strobe effect for 10 seconds

---

### Variable Pulse Rate

**Use case:** Different pulse rates in sequence

**Excel format:**

Sheet: `protocol`
```
| Sections | CH1_status | CH1_time_sec | CH1_frequency | CH1_pulse_width |
|----------|------------|--------------|---------------|-----------------|
| 0        | 1          | 30           | 0.5           | 200             |
| 1        | 1          | 30           | 1.0           | 100             |
| 2        | 1          | 30           | 2.0           | 50              |
```

Sheet: `start_time`
```
| Channel    | CH1 |
|------------|-----|
| start_time | 10  |
```

**Text format:**
```txt
**Text format:**
```txt
# Slow breathing (0.5 Hz = 2000ms period)
PATTERN:1;CH:1;STATUS:1;TIME_S:30;REPEATS:1;PULSE:T2000pw200

# Normal pulse (1 Hz = 1000ms period)
PATTERN:2;CH:1;STATUS:1;TIME_S:30;REPEATS:1;PULSE:T1000pw100

# Fast flash (2 Hz = 500ms period)
PATTERN:3;CH:1;STATUS:1;TIME_S:30;REPEATS:1;PULSE:T500pw50

START_TIME: {'CH1': 0}
```
```

**Result:** Progressively faster blinking over 90 seconds

---

## Complex Schedule Templates

### Day/Night Cycle

**Use case:** Circadian rhythm simulation

**Excel format:**

Sheet: `protocol`
```
| Sections | CH1_status | CH1_time_hour | CH1_frequency | CH1_pulse_width |
|----------|------------|---------------|---------------|-----------------|
| 0        | 0          | 8             | 0             | 0               |
| 1        | 1          | 0.5           | 0.5           | 200             |
| 2        | 1          | 12            | 0             | 0               |
| 3        | 1          | 0.5           | 0.5           | 200             |
| 4        | 0          | 3             | 0             | 0               |
```

Sheet: `start_time`
```
| Channel    | CH1   |
|------------|-------|
| start_time | 22:00 |
```

**Text format:**
```txt
# Night: 8 hours OFF
PATTERN:1;CH:1;STATUS:0;TIME_H:8;REPEATS:1

# Dawn: 30 min gradual wake (breathing)
PATTERN:2;CH:1;STATUS:1;TIME_M:30;REPEATS:1;PULSE:f0.5pw200

# Day: 12 hours solid ON
PATTERN:3;CH:1;STATUS:1;TIME_H:12;REPEATS:1

# Dusk: 30 min gradual sleep (breathing)
PATTERN:4;CH:1;STATUS:1;TIME_M:30;REPEATS:1;PULSE:f0.5pw200

# Evening: 3 hours OFF
PATTERN:5;CH:1;STATUS:0;TIME_H:3;REPEATS:1

START_TIME: {'CH1': '22:00'}
```

**Result:** 24-hour cycle with dawn/dusk simulation

---

### Work Schedule

**Use case:** Office hours automation

**Excel format:**

Sheet: `protocol`
```
| Sections | CH1_status | CH1_time_hour | CH2_status | CH2_time_hour |
|----------|------------|---------------|------------|---------------|
| 0        | 1          | 8             | 0          | 8             |
| 1        | 0          | 1             | 1          | 1             |
| 2        | 1          | 7             | 0          | 7             |
| 3        | 0          | 8             | 0          | 8             |
```

Sheet: `start_time`
```
| Channels | Start_time |
|----------|------------|
| CH1      | 08:00      |
| CH2      | 08:00      |
```

**Text format:**
```txt
# Main lights: 8 hours ON
PATTERN:1;CH:1;STATUS:1;TIME_H:8;REPEATS:1

# Lunch break: Both OFF for 1 hour
PATTERN:2;CH:1;STATUS:0;TIME_H:1;REPEATS:1
PATTERN:2;CH:2;STATUS:0;TIME_H:1;REPEATS:1

# Afternoon: CH1 ON, CH2 ON for 7 hours
PATTERN:3;CH:1;STATUS:1;TIME_H:7;REPEATS:1
PATTERN:3;CH:2;STATUS:1;TIME_H:7;REPEATS:1

# Evening: All OFF
PATTERN:4;CH:1;STATUS:0;TIME_H:8;REPEATS:1
PATTERN:4;CH:2;STATUS:0;TIME_H:8;REPEATS:1

START_TIME: {
    'CH1': '08:00',
    'CH2': '08:00'
}
```

**Result:** Work hours (8 AM - 5 PM) with lunch break

---

### Interval Training

**Use case:** Timed intervals with rest periods

**Excel format:**

Sheet: `protocol`
```
| Sections | CH1_status | CH1_time_sec | CH2_status | CH2_time_sec |
|----------|------------|--------------|------------|--------------|
| 0        | 1          | 30           | 0          | 30           |
| 1        | 0          | 15           | 1          | 15           |
```

Sheet: `start_time`
```
| Channels | Start_time | Wait_status |
|----------|------------|-------------|
| CH1      | 30         | 1           |
| CH2      | 30         | 0           |
```

**Text format:**
```txt
# CH1 (work): 30s ON, 15s OFF, repeat 20 times (15 min)
PATTERN:1;CH:1;STATUS:1,0;TIME_S:30,15;REPEATS:20

# CH2 (rest): 30s OFF, 15s ON, repeat 20 times (15 min)
PATTERN:1;CH:2;STATUS:0,1;TIME_S:30,15;REPEATS:20

START_TIME: {
    'CH1': 30,
    'CH2': 30
}

WAIT_STATUS: {
    'CH1': 1,
    'CH2': 0
}
```

**Result:** Alternating 30s work / 15s rest intervals

---

## Experimental Templates

### Plant Growth Protocol

**Use case:** Controlled light cycles for plant research

**Text format:**
```txt
# ===============================================
# Plant Growth Experiment - 16/8 Light Cycle
# Red: 660nm (CH1), Blue: 450nm (CH2)
# ===============================================

# Red channel: 16 hours ON (dawn simulation + day + dusk)
# Dawn: 30 min breathing (gradual wake)
PATTERN:1;CH:1;STATUS:1;TIME_M:30;REPEATS:1;PULSE:f0.5pw200

# Day: 15 hours solid ON
PATTERN:2;CH:1;STATUS:1;TIME_H:15;REPEATS:1

# Dusk: 30 min breathing (gradual sleep)
PATTERN:3;CH:1;STATUS:1;TIME_M:30;REPEATS:1;PULSE:f0.5pw200

# Night: 8 hours OFF
PATTERN:4;CH:1;STATUS:0;TIME_H:8;REPEATS:1

# Blue channel: 12 hours ON (mid-day peak)
# Morning OFF: 2 hours
PATTERN:1;CH:2;STATUS:0;TIME_H:2;REPEATS:1

# Day ON: 12 hours
PATTERN:2;CH:2;STATUS:1;TIME_H:12;REPEATS:1

# Evening OFF: 10 hours
PATTERN:3;CH:2;STATUS:0;TIME_H:10;REPEATS:1

START_TIME: {
    'CH1': '06:00',
    'CH2': '06:00'
}

WAIT_STATUS: {
    'CH1': 0,
    'CH2': 0
}
```

**Result:** Simulated natural light cycle for plants

---

### Stress Test Protocol

**Use case:** Testing system reliability with rapid changes

**Text format:**
```txt
# ===============================================
# Stress Test: Rapid Channel Switching
# Tests: Timing accuracy, memory, stability
# ===============================================

# All channels: 100ms ON, 100ms OFF, 1000 repeats
PATTERN:1;CH:1;STATUS:1,0;TIME_MS:100,100;REPEATS:1000
PATTERN:1;CH:2;STATUS:0,1;TIME_MS:100,100;REPEATS:1000
PATTERN:1;CH:3;STATUS:1,0;TIME_MS:100,100;REPEATS:1000

START_TIME: {
    'CH1': 5,
    'CH2': 5,
    'CH3': 5
}

CALIBRATION_FACTOR: 1.00131
```

**Result:** 3.3 minutes of rapid switching for testing

---

### Multi-Phase Experiment

**Use case:** Complex experimental protocol with multiple phases

**Text format:**
```txt
# ===============================================
# Multi-Phase Behavioral Experiment
# Phase 1: Habituation (30 min)
# Phase 2: Stimulus (15 min)
# Phase 3: Recovery (30 min)
# ===============================================

# Channel 1: White light (baseline/recovery)
# Phase 1: Habituation - Solid ON 30 min
PATTERN:1;CH:1;STATUS:1;TIME_M:30;REPEATS:1

# Phase 2: Stimulus OFF (CH2 takes over)
PATTERN:2;CH:1;STATUS:0;TIME_M:15;REPEATS:1

# Phase 3: Recovery - Solid ON 30 min
PATTERN:3;CH:1;STATUS:1;TIME_M:30;REPEATS:1

# Channel 2: Stimulus light (pulsed)
# Phase 1: OFF during habituation
PATTERN:1;CH:2;STATUS:0;TIME_M:30;REPEATS:1

# Phase 2: Pulsed stimulus (2 Hz, 10% duty)
PATTERN:2;CH:2;STATUS:1;TIME_M:15;REPEATS:1;PULSE:f2pw50

# Phase 3: OFF during recovery
PATTERN:3;CH:2;STATUS:0;TIME_M:30;REPEATS:1

START_TIME: {
    'CH1': '14:00',
    'CH2': '14:00'
}

WAIT_STATUS: {
    'CH1': 1,
    'CH2': 0
}

CALIBRATION_FACTOR: 1.00131
```

**Result:** 75-minute controlled experiment with distinct phases

---

## Custom Template Guide

### Template Structure

1. **Header** (optional but recommended):
   ```txt
   # ==========================================
   # Template Name
   # Description
   # Author/Date
   # ==========================================
   ```

2. **Parameters** (document key values):
   ```txt
   # CHANNELS: 3
   # DURATION: 2 hours
   # START: 20:00
   # FEATURES: Pulse, calibration
   ```

3. **Channel definitions** (one per channel):
   ```txt
   # Channel 1: Main light
   PATTERN:1;CH:1;STATUS:...
   
   # Channel 2: Indicator
   PATTERN:1;CH:2;STATUS:...
   ```

4. **Configuration**:
   ```txt
   START_TIME: {...}
   WAIT_STATUS: {...}
   CALIBRATION_FACTOR: ...
   ```

---

### Template Checklist

**Before creating custom template:**

- [ ] Define clear purpose/use case
- [ ] Determine number of channels needed
- [ ] Calculate total duration
- [ ] Choose appropriate time units
- [ ] Decide on pulse effects (if any)
- [ ] Set start times per channel
- [ ] Configure wait status
- [ ] Add calibration factor (if reusing)
- [ ] Test with short duration first
- [ ] Document all parameters
- [ ] Add comments for clarity

---

### Testing Templates

**Quick test strategy:**

1. **Scale down time:** Test with seconds instead of hours
   ```txt
   # Production: 1 hour
   TIME_H:1
   
   # Testing: 10 seconds
   TIME_S:10
   ```

2. **Reduce repeats:** Test with fewer cycles
   ```txt
   # Production: 100 repeats
   REPEATS:100
   
   # Testing: 3 repeats
   REPEATS:3
   ```

3. **Use countdown start:** Immediate start for testing
   ```txt
   # Production: Scheduled time
   START_TIME: {'CH1': '21:00'}
   
   # Testing: Start in 5 seconds
   START_TIME: {'CH1': 5}
   ```

---

### Saving Templates

**Organization:**
```
protocols/
  ├── templates/
  │   ├── basic_onoff.txt
  │   ├── breathing_effect.txt
  │   ├── day_night_cycle.txt
  │   └── plant_growth.txt
  ├── experiments/
  │   ├── exp001_pilot.txt
  │   ├── exp002_main.txt
  │   └── ...
  └── production/
      ├── daily_schedule.txt
      └── ...
```

**Naming convention:**
```
<category>_<description>_<version>.txt

Examples:
basic_blink_v1.txt
pulse_breathing_v2.txt
experiment_plant_v3.txt
```

---

## See Also

- [Protocol Formats](PROTOCOL_FORMATS.md) - Format specifications
- [Protocol Settings](PROTOCOL_SETTINGS.md) - Parameter details
- [Usage Guide](USAGE.md) - How to use templates

---

*Last Updated: November 8, 2025*
