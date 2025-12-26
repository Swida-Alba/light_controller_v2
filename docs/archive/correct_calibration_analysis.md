# Correct Calibration Analysis

## V1 Method - Understanding the Measurement

### What V1 Actually Measures:

```python
t1 = time.time()  # Python records start
# ... Arduino waits X seconds on its clock ...
t2 = time.time()  # Python records when response received
t_feedback = t2 - t1  # Python's elapsed time
```

### Timeline with Fast Arduino Clock:

```
Request: "Wait 20s (on your clock)"

Arduino's perspective (fast clock):
- Starts at Arduino_time = 0
- Waits until Arduino_time = 20s
- Sends response
- Arduino thinks: I waited exactly 20s

Real time perspective:
- If Arduino clock is 1% FAST
- When Arduino's clock shows 20s, only 19.8s real time passed
- Python measures t2-t1 = 19.8s + serial_delay

Python measures: ~19.85s (19.8s + 0.05s serial)
```

### Linear Regression Eliminates Communication Delay:

Multiple measurements:
```
Requested   Python Measured   (includes ~50ms serial delay)
20s    →    19.85s
30s    →    29.75s  
40s    →    39.65s
```

Linear regression: `python_time = slope × requested + offset`
- Slope: 0.99 (clock is fast)
- Offset: 0.05s (communication delay, removed by regression)

**Result**: Python measures LESS time → Arduino clock is FASTER → factor < 1

---

## V2 Method - Understanding the Measurement

### What V2 Actually Measures:

```python
t_start = time.time()  # Python records start (when first msg arrives)

# Arduino sends: 0ms, 5000ms, 10000ms, 15000ms... (from its millis())
# Python records when each arrives

timestamp_1: arduino=0ms,     python=0s      (reference point)
timestamp_2: arduino=5000ms,  python=4.95s   (arrived earlier!)
timestamp_3: arduino=10000ms, python=9.90s
```

### If Arduino Clock is FAST:

```
Arduino thinks 5s passed (on its clock)
Real time: only 4.95s passed
Python measures from first message: 4.95s (minus serial delay variations)

Arduino reports: 5000ms
Python measures: ~4.95s
```

**Python time < Arduino time** → Arduino clock is FASTER

Linear regression: `arduino = slope × python + offset`
- If Arduino fast: arduino > python → slope > 1
- If Arduino slow: arduino < python → slope < 1

---

## The Key Insight

### Both methods compare the SAME thing through regression:

**V1**: Compares requested time (on Arduino clock) vs Python's measurement
- Regression eliminates communication delay
- If Arduino fast: Python measures less → factor < 1

**V2**: Compares Arduino's timestamps vs Python's timestamps  
- Regression eliminates communication delay
- If Arduino fast: Arduino reports more → slope > 1

### Why They Seem Opposite:

**V1 fits**: `python_time = factor × requested_arduino_time`
- Fast Arduino → factor < 1

**V2 fits**: `arduino_time = factor × python_time`
- Fast Arduino → factor > 1

**They are RECIPROCALS of each other!**
- V1: python = 0.99 × arduino
- V2: arduino = 1.01 × python
- 1/0.99 ≈ 1.01 ✓

---

## Correct Comparison Logic

### V1 Should Compare:
- X-axis: Requested time (what we asked Arduino to wait)
- Y-axis: Python measured time (how long it actually took)
- If Python < Requested → Arduino faster

### V2 Should Compare:
- X-axis: Python measured time (when messages arrived)
- Y-axis: Arduino reported time (what Arduino's clock said)
- If Arduino > Python → Arduino faster

### Both methods should give RECIPROCAL factors!

If V1 gives 0.999 (python = 0.999 × arduino):
- Arduino is slightly SLOW
- V2 should give 1.001 (arduino = 1.001 × python)

If V1 gives 1.001 (python = 1.001 × arduino):
- Arduino is slightly FAST
- V2 should give 0.999 (arduino = 0.999 × python)
