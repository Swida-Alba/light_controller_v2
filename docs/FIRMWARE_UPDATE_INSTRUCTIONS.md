# Arduino Firmware Update Required for V2 Calibration

## Issue

Your Arduino currently responds with `"calibration_0"` (V1 format) instead of `"calib_timestamp_0"` (V2 format). This means the V2 calibration function is not yet on your Arduino.

## Error You Saw

```
Warning: Unexpected response during calibration: "calibration_0"
TimeoutError: Calibration timeout waiting for timestamp 2/11
```

## Solution: Upload Updated Firmware

### Step 1: Open Arduino IDE

Open the firmware file:
```
/Users/apple/Documents/GitHub/light_controller_v2.2/light_controller_v2_2_arduino/light_controller_v2_2_arduino.ino
```

### Step 2: Verify V2 Function Exists

Check that the file contains the `calibrate_timestamps()` function around line 490. You should see:

```arduino
void calibrate_timestamps(String command) {
    // Parse command: "calibrate_timestamps_{duration}_{num_samples}"
    ...
    for (int i = 1; i <= numSamples; i++) {
        unsigned long targetTime = startTime + (i * interval);
        ...
        Serial.print("calib_timestamp_");
        Serial.println(elapsed);
    }
}
```

### Step 3: Upload to Arduino

1. Select your board: **Tools > Board > Arduino Due (Programming Port)**
2. Select your port: **Tools > Port > /dev/cu.usbmodem1101**
3. Click **Upload** button or **Sketch > Upload**
4. Wait for "Done uploading" message

### Step 4: Test V2 Calibration

Run the comparison test again:
```bash
conda activate pyarduino
python test_calibration_comparison.py
```

## Temporary Solution: Use V1 Only

If you want to test calibration now without updating firmware:

```bash
python test_v1_calibration_only.py
```

This will only test V1 calibration (which works with your current firmware).

## How to Verify Firmware Version

After uploading, when you connect to Arduino, it should show:

**Old firmware (V1 only):**
```
Arduino: Salve!
```

**New firmware (V1 + V2):**
```
Arduino: Salve!
Arduino Configuration:
  PATTERN_LENGTH: 4
  MAX_PATTERN_NUM: 10
  MAX_CHANNEL_NUM: 8
```

The greeting format is the same, but the new firmware will respond correctly to both:
- `calibrate_40000` → sends `"calibration_40000"` (V1)
- `calibrate_timestamps_60_10` → sends `"calib_timestamp_0"`, `"calib_timestamp_6000"`, etc. (V2)

## What Changed in the Firmware

The updated firmware adds:

1. **New function** `calibrate_timestamps()` (lines 490-550)
2. **Updated command parser** to route `calibrate_timestamps_*` commands (lines 117-123)
3. **Non-blocking delays** in both V1 and V2 calibration

All your existing protocols will continue to work - the firmware is backward compatible!

## Current Test Results

From your V1 test:
- ✅ **Calibration factor**: 1.00009
- ✅ **Drift**: 4.03 seconds per 12 hours
- ✅ **Pattern length check**: Working correctly (warning instead of error)

This is a good baseline to compare V2 against once you upload the firmware!
