# Pulse Mode Warning Examples

## Warning When Pulse Enabled But Not Needed

### Scenario
- **Arduino:** PULSE_MODE_COMPILE = 1 (Pulse enabled)
- **Protocol:** No pulse parameters
- **Result:** Compatible but suboptimal

### Expected Console Output

\`\`\`
💾 Checking Arduino memory and pulse mode compatibility...
   Arduino Memory:
     Total:  96.0 KB
     Used:   88.0 KB (91.7%)
     Free:   8.0 KB

🔍 Pulse mode detection:
   Protocol uses pulse parameters: NO

🔍 Pulse Mode Compatibility Check:
   Protocol requires pulses: NO
   Arduino pulse mode:       ENABLED (compile-time)
   ✓ Compatible (Arduino pulse enabled but not needed)
   💡 Note: Protocol does NOT use pulse modulation
      Arduino has pulse mode ENABLED (~2.5KB memory used)
      Consider setting PULSE_MODE_COMPILE = 0 to save memory
\`\`\`

### What This Means

✅ **Your protocol WILL work** - No errors, fully compatible

⚠️ **But you're wasting memory:**
- Pulse arrays are allocated: **2,560 bytes (2.5KB)**
- These arrays are never used by the protocol
- Free RAM is lower than it needs to be

💡 **Recommendation:**
If this protocol never uses pulses, recompile with:
\`\`\`cpp
#define PULSE_MODE_COMPILE 0  // Disable pulse mode
\`\`\`

Benefits:
- Save 2,560 bytes of RAM
- More memory for other features
- Slightly faster compile time

---

## Error When Pulse Required But Disabled

### Scenario
- **Arduino:** PULSE_MODE_COMPILE = 0 (Pulse disabled)
- **Protocol:** Has pulse parameters (period, pulse_width, etc.)
- **Result:** INCOMPATIBLE

### Expected Console Output

\`\`\`
💾 Checking Arduino memory and pulse mode compatibility...
   Arduino Memory:
     Total:  96.0 KB
     Used:   85.5 KB (89.1%)
     Free:   10.5 KB

🔍 Pulse mode detection:
   Protocol uses pulse parameters: YES

🔍 Pulse Mode Compatibility Check:
   Protocol requires pulses: YES
   Arduino pulse mode:       DISABLED (compile-time)

======================================================================
❌ ERROR: Pulse Mode Incompatibility!
======================================================================
  Protocol REQUIRES pulse modulation
  But Arduino pulse mode is DISABLED

  Arduino firmware was compiled with PULSE_MODE_COMPILE = 0
  Pulse support is DISABLED at compile time.

  ⚠️  Solution: Recompile Arduino firmware with PULSE_MODE_COMPILE = 1
     Edit light_controller_v2_2_arduino.ino, change:
     #define PULSE_MODE_COMPILE 0  →  #define PULSE_MODE_COMPILE 1
     Then recompile and upload to Arduino.
======================================================================

Traceback (most recent call last):
  ...
ValueError: Pulse mode incompatibility: Protocol requires pulses but Arduino pulse mode is disabled.
\`\`\`

### What This Means

❌ **Your protocol WILL NOT work** - Hard error, must fix

**The Problem:**
- Protocol defines pulse parameters (T1000pw100, frequency, duty_cycle, etc.)
- Arduino was compiled without pulse array support
- Pulse parameters cannot be stored or executed

**The Solution:**
1. Open `light_controller_v2_2_arduino.ino`
2. Find the line: `#define PULSE_MODE_COMPILE 0`
3. Change to: `#define PULSE_MODE_COMPILE 1`
4. Recompile and upload to Arduino
5. Run your protocol again

---

## Perfect Match - No Pulse Needed, No Pulse Enabled

### Scenario
- **Arduino:** PULSE_MODE_COMPILE = 0 (Pulse disabled)
- **Protocol:** No pulse parameters
- **Result:** OPTIMAL

### Expected Console Output

\`\`\`
💾 Checking Arduino memory and pulse mode compatibility...
   Arduino Memory:
     Total:  96.0 KB
     Used:   85.5 KB (89.1%)
     Free:   10.5 KB

🔍 Pulse mode detection:
   Protocol uses pulse parameters: NO

🔍 Pulse Mode Compatibility Check:
   Protocol requires pulses: NO
   Arduino pulse mode:       DISABLED (compile-time)
   ✓ Compatible
\`\`\`

### What This Means

✅ **Perfect configuration!**
- Protocol doesn't need pulses
- Arduino doesn't allocate pulse arrays
- Maximum memory efficiency
- ~2.5KB more free RAM compared to pulse-enabled

---

## Perfect Match - Pulse Needed, Pulse Enabled

### Scenario
- **Arduino:** PULSE_MODE_COMPILE = 1 (Pulse enabled)
- **Protocol:** Has pulse parameters
- **Result:** OPTIMAL

### Expected Console Output

\`\`\`
💾 Checking Arduino memory and pulse mode compatibility...
   Arduino Memory:
     Total:  96.0 KB
     Used:   88.0 KB (91.7%)
     Free:   8.0 KB

🔍 Pulse mode detection:
   Protocol uses pulse parameters: YES

🔍 Pulse Mode Compatibility Check:
   Protocol requires pulses: YES
   Arduino pulse mode:       ENABLED (compile-time)
   ✓ Compatible
\`\`\`

### What This Means

✅ **Perfect configuration!**
- Protocol uses pulse modulation
- Arduino supports pulse arrays
- Full functionality available
- Memory usage is necessary and expected

---

## Summary Table

| Arduino Mode | Protocol Type | Output | Status |
|--------------|---------------|--------|--------|
| Disabled (0) | No Pulse | "✓ Compatible" | ✅ Perfect |
| Disabled (0) | Has Pulse | "❌ ERROR: Incompatibility" | ❌ Error |
| Enabled (1) | No Pulse | "✓ Compatible + 💡 Warning" | ⚠️ Works but wasteful |
| Enabled (1) | Has Pulse | "✓ Compatible" | ✅ Perfect |

## Color Coding

In terminal output:
- 🟢 Green text: Everything optimal
- 🟡 Yellow text: Warning, but will work
- 🔴 Red text: Error, won't work

## Testing These Scenarios

Use the test script:

\`\`\`bash
# Test all scenarios interactively
python test_pulse_compatibility.py --port /dev/cu.usbmodem14101

# Test automatically
python test_pulse_compatibility.py --port COM3 --auto
\`\`\`

Or manually:

\`\`\`python
from light_controller_parser import LightControllerParser

# Test no-pulse protocol
parser = LightControllerParser('examples/example_no_pulse_protocol.txt')
parser.setup_serial('Arduino', '/dev/cu.usbmodem14101')
# Watch for warnings or errors
parser.close()

# Test pulse protocol
parser = LightControllerParser('examples/pulse_protocol.txt')
parser.setup_serial('Arduino', '/dev/cu.usbmodem14101')
# Watch for warnings or errors
parser.close()
\`\`\`
