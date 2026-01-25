# Arduino Setup Guide

Complete hardware setup guide for Arduino boards.

---

## ⚠️ Important: Board Selection

**For PWM/RAMP mode (smooth fading), Arduino UNO R4 Minima is strongly recommended.**

| Feature           | UNO R3             | UNO R4 Minima ⭐    | Mega 2560          | Due                  |
| ----------------- | ------------------ | ------------------ | ------------------ | -------------------- |
| **Processor**     | ATmega328P (8-bit) | RA4M1 (32-bit ARM) | ATmega2560 (8-bit) | SAM3X8E (32-bit ARM) |
| **Clock Speed**   | 16 MHz             | 48 MHz             | 16 MHz             | 84 MHz               |
| **SRAM**          | 2 KB               | **32 KB**          | 8 KB               | 96 KB                |
| **Flash**         | 32 KB              | 256 KB             | 256 KB             | 512 KB               |
| **I/O Voltage**   | **5V**             | **5V**             | **5V**             | ⚠️ 3.3V               |
| **Native DAC**    | ❌ No               | ✅ 1 ch (12-bit)    | ❌ No               | ✅ 2 ch (12-bit)      |
| **PWM_RAMP_MODE** | ❌ Insufficient     | ✅ Full             | ⚠️ Limited          | ✅ Full               |
| **PULSE_MODE**    | ⚠️ Very limited     | ✅ Full             | ✅ Yes              | ✅ Full               |

### Quick Recommendation

| Your Need                            | Recommended Board                   |
| ------------------------------------ | ----------------------------------- |
| **General use, most protocols**      | ⭐ **UNO R4 Minima** (32KB, 5V, DAC) |
| **Very complex protocols, dual DAC** | Arduino Due (96KB, 3.3V only)       |
| **Simple on/off patterns only**      | UNO R3 or Mega 2560                 |
| **Need many I/O pins**               | Mega 2560 (54 digital pins)         |

> 💡 **Why UNO R4 Minima?**
> - **32KB SRAM** is sufficient for most protocols (firmware uses ~12KB)
> - **5V output** works directly with most LEDs and components
> - **Built-in 12-bit DAC** for true analog output
> - **Lower cost** than Arduino Due

The firmware with PWM/RAMP enabled uses **~12 KB SRAM**, which exceeds Arduino Uno R3's 2 KB total. Use Arduino UNO R4 or Due for full functionality.

---

## Table of Contents

- [Supported Boards](#supported-boards)
- [Channel Configuration](#channel-configuration)
- [Hardware Requirements](#hardware-requirements)
- [Pin Assignments](#pin-assignments)
- [MCP4728 DAC Setup](#mcp4728-dac-setup)
- [Board-Specific Setup](#board-specific-setup)
- [Hardware Connections](#hardware-connections)
- [Verification](#verification)

---

## Supported Boards

### Arduino UNO R4 Minima ⭐ Recommended

**Specifications:**
- **MCU:** Renesas RA4M1 (32-bit ARM Cortex-M4)
- **Clock:** 48 MHz
- **SRAM:** 32 KB (firmware uses ~12 KB = 37.5%)
- **Flash:** 256 KB
- **EEPROM:** 8 KB
- **Operating Voltage:** **5V** (ideal for most projects)
- **Channels:** Up to 6 (CH1-CH6)
- **Pins:** Digital 2, 4, 6, 8, 10, 12
- **Native DAC:** ✅ 1 channel (A0/DAC) - 12-bit resolution, 0-5V output
- **USB:** USB-C connector

**Best for:**
- ✅ **PWM/RAMP mode** (smooth LED fading)
- ✅ **PULSE mode** support
- ✅ **5V output** - no level shifters needed
- ✅ **DAC output** (true analog 0-5V)
- ✅ Medium to complex protocols
- ✅ Cost-effective professional projects
- ✅ Drop-in replacement for UNO R3 (same form factor)

**Virtual Pin Mapping:**
```cpp
// Native DAC on UNO R4
const int channelPins[] = {2, 4, 100};  // PWM, PWM, Native DAC
// Pin 100 = DAC output on A0 (0-5V)
```

---

### Arduino Due

> ⚠️ **VOLTAGE WARNING:** Arduino Due operates at **3.3V logic levels**, NOT 5V!
> - All I/O pins output 3.3V (not 5V)
> - **DO NOT** connect 5V devices directly to Due pins
> - Native DAC outputs 0-3.3V (not 0-5V)
> - Use level shifters for 5V peripherals
> - Exceeding 3.3V on any pin can **permanently damage** the board

**Specifications:**
- **MCU:** Atmel SAM3X8E (32-bit ARM Cortex-M3)
- **Clock:** 84 MHz
- **SRAM:** 96 KB (firmware uses ~12.1 KB = 12.6%)
- **Flash:** 512 KB
- **Operating Voltage:** ⚠️ **3.3V only**
- **Channels:** Up to 8 (CH1-CH8)
- **Pins:** Digital 2, 4, 6, 8, 10, 12, A0, A1
- **Memory:** Large (4KB EEPROM equivalent in flash)
- **Max Patterns:** 10+ per channel
- **USB Ports:** Programming + Native
- **Native DAC:** 2 channels (DAC0, DAC1) - 12-bit resolution, ⚠️ 0-3.3V output

**Best for:**
- ✅ Very complex protocols with many patterns
- ✅ Dual DAC channels needed
- ✅ Maximum memory for long-running experiments
- ⚠️ Projects where 3.3V output is acceptable

**Important:** Two USB ports!
- **Programming Port:** For uploading sketch AND serial communication
- **Native Port:** Alternative for serial (doesn't reset on connection)

**When to choose Due over UNO R4:**
- Need more than 32KB SRAM for very complex protocols
- Need 2 independent DAC channels
- Already have 3.3V compatible hardware

---

### Arduino Uno R3 (Classic)

> ⚠️ **Warning:** Arduino Uno R3 has only 2 KB SRAM. The firmware with PWM_RAMP_MODE enabled requires ~12 KB SRAM and **will not work** on Arduino Uno R3.

**Specifications:**
- **MCU:** ATmega328P (8-bit AVR)
- **Clock:** 16 MHz
- **SRAM:** 2 KB (insufficient for PWM/RAMP mode)
- **Flash:** 32 KB
- **EEPROM:** 1 KB
- **Operating Voltage:** 5V
- **Channels:** 4 (CH1-CH4)
- **Pins:** Digital 2, 4, 6, 8
- **Max Commands:** ~200-300 (STATUS mode only)
- **Native DAC:** ❌ None

**Use only if:**
- Simple STATUS patterns (on/off only)
- PWM_RAMP_MODE = 0 in firmware
- PULSE_MODE_COMPILE = 0 in firmware
- Very limited pattern count

**To use with Uno R3, modify firmware:**
```cpp
#define PWM_RAMP_MODE_COMPILE 0  // Disable PWM ramp
#define PULSE_MODE_COMPILE 0     // Disable pulse mode
#define MAX_CHANNEL_NUM 3        // Reduce channels
#define PATTERN_LENGTH 2         // Minimize patterns
```

---

### Arduino Mega 2560

**Specifications:**
- **MCU:** ATmega2560 (8-bit AVR)
- **Clock:** 16 MHz
- **SRAM:** 8 KB (marginal for PWM/RAMP mode)
- **Flash:** 256 KB
- **EEPROM:** 4 KB
- **Operating Voltage:** **5V**
- **Channels:** 4-8 (depends on mode)
- **Pins:** 54 digital I/O (15 PWM capable), 16 analog inputs
- **Serial:** 4 hardware serial ports
- **Native DAC:** ❌ None

**Best for:**
- ⚠️ PWM/RAMP mode with reduced settings (8KB is marginal)
- ✅ Simple STATUS mode protocols
- ✅ Projects needing many I/O pins
- ✅ Multiple serial connections
- ✅ 5V output for most components

**To use Mega with PWM/RAMP mode:**
```cpp
#define MAX_CHANNEL_NUM 4        // Reduce channels to save memory
const int PATTERN_LENGTH = 2;    // Use smaller patterns
```

---

## Channel Configuration

The firmware now supports multiple **output types** per channel. Configure these at the top of the Arduino sketch:

### Output Type Definitions

| Type           | Code  | Resolution | Range  | Use Case                    |
| -------------- | ----- | ---------- | ------ | --------------------------- |
| **PWM**        | `'P'` | 8-bit      | 0-255  | Standard LED dimming        |
| **Native DAC** | `'D'` | 12-bit     | 0-4095 | True analog output (Due/R4) |
| **MCP4728**    | `'M'` | 12-bit     | 0-4095 | External I2C DAC            |
| **Binary**     | `'B'` | 1-bit      | 0/1    | On/off relays               |

### Configuration Example

```cpp
// Number of channels
const int MAX_CHANNEL_NUM = 4;

// Pin assignments per channel type:
// - For PWM ('P'): Arduino digital pin number
// - For Binary ('B'): Arduino digital pin number  
// - For Native DAC ('D'): 0 for DAC0, 1 for DAC1
// - For MCP4728 ('M'): 0-3 for channels A-D
const int channelPins[MAX_CHANNEL_NUM] = {11, 12, 0, 1};

// Channel output types
const char channelTypes[MAX_CHANNEL_NUM] = {'P', 'P', 'M', 'M'};
```

This configures:
- CH1: PWM on pin 11 (0-255)
- CH2: PWM on pin 12 (0-255)
- CH3: MCP4728 channel A (0-4095)
- CH4: MCP4728 channel B (0-4095)

### Value Auto-Conversion

The protocol automatically converts values based on channel type:

| Input Range            | PWM Output     | DAC Output      | Binary Output |
| ---------------------- | -------------- | --------------- | ------------- |
| `0.0-1.0` (normalized) | 0-255          | 0-4095          | 0 or 1        |
| `0-255` (8-bit)        | 0-255          | 0-4095 (scaled) | 0 or 1        |
| `0-4095` (12-bit)      | 0-255 (scaled) | 0-4095          | 0 or 1        |

Example: `STATUS:0.5` becomes:
- PWM channel: 127
- DAC channel: 2047
- Binary channel: 1

### Feature Comparison

| Feature         | UNO R3 | UNO R4 ⭐  | Mega 2560 | Due        |
| --------------- | ------ | --------- | --------- | ---------- |
| SRAM            | 2 KB   | **32 KB** | 8 KB      | 96 KB      |
| I/O Voltage     | 5V     | **5V**    | 5V        | ⚠️ 3.3V     |
| Channels        | 4      | 6         | 4-8       | 8          |
| PWM/RAMP Mode   | ❌ No   | ✅ Yes     | ⚠️ Limited | ✅ Yes      |
| PULSE Mode      | ❌ No   | ✅ Yes     | ⚠️ Limited | ✅ Yes      |
| Native DAC      | ❌ No   | 1 ch      | ❌ No      | 2 ch       |
| Max Patterns    | ~2-3   | ~6-8      | ~5-6      | 10+        |
| USB Ports       | 1      | 1         | 1         | 2          |
| Price           | $      | $$        | $$        | $$$        |
| **Recommended** | ❌      | ✅ Good    | ⚠️         | ✅ **Best** |

---

## Hardware Requirements

### Required Components

1. **Arduino Board**
   - **Due (recommended)** for full functionality
   - **Uno R4** for PWM/RAMP mode with single DAC
   - Mega for medium complexity
   - Uno R3 only for simple STATUS patterns (2KB SRAM limit)
   - USB cable (Type B for Uno R3/Mega, USB-C for Uno R4, Micro-B for Due)

2. **LEDs**
   - Standard LEDs (5mm or 3mm)
   - OR LED modules/strips
   - Current limit: See LED specifications

3. **Current-Limiting Resistors**
   - Value depends on LED voltage/current
   - Typical: 220Ω for 5V LEDs
   - Calculator: R = (5V - LED_voltage) / LED_current

4. **Power Supply**
   - USB power for Arduino (5V)
   - External power for high-current LEDs
   - Ensure adequate current capacity

5. **Breadboard/PCB** (optional)
   - For prototyping: Breadboard
   - For permanent: Custom PCB or perfboard

6. **Wires**
   - Jumper wires for breadboard
   - Solid core wire for permanent connections
   - Appropriate gauge for current

---

### Optional Components

**For Higher Power LEDs:**
- MOSFETs or transistors (e.g., 2N2222)
- Flyback diodes (for inductive loads)
- Heat sinks (for high-power applications)

**For Protection:**
- Fuse or current limiter
- Reverse polarity protection diode
- Voltage regulator (if needed)

**For Multiple LEDs:**
- LED driver ICs
- PWM amplifiers
- Constant current sources

---

## Pin Assignments

### Standard Pinout

| Channel | Pin       | Arduino Uno R3/R4 | Arduino Due | Arduino Mega |
| ------- | --------- | ----------------- | ----------- | ------------ |
| CH1     | Digital 2 | ✓                 | ✓           | ✓            |
| CH2     | Digital 4 | ✓                 | ✓           | ✓            |
| CH3     | Digital 6 | ✓                 | ✓           | ✓            |
| CH4     | Digital 8 | ✓                 | ✓           | ✓            |

**Note:** Pins are fixed in the Arduino sketch and cannot be changed without modifying the code.

---

### Pin Characteristics

**Digital Output Voltage Levels:**

| Board     | Logic HIGH | Logic LOW | Max Current/Pin |
| --------- | ---------- | --------- | --------------- |
| Uno R3/R4 | 5V         | 0V        | 20mA            |
| Mega      | 5V         | 0V        | 20mA            |
| Due       | **3.3V**   | 0V        | 15mA            |

> ⚠️ **Arduino Due 3.3V Warning:**
> - Due outputs **3.3V**, not 5V - LEDs may appear dimmer
> - Use appropriate resistor values for 3.3V (e.g., 100Ω-150Ω for standard LEDs)
> - Never connect 5V signals to Due input pins
> - DAC output range: 0-3.3V only

**Use resistors or transistors for higher currents.****

---

## Board-Specific Setup

### Arduino Uno R3/R4 Setup

#### 1. Install Arduino IDE
Download from: https://www.arduino.cc/en/software

#### 2. Connect Board
- Connect Uno to computer via USB
- Wait for driver installation (Windows)
- Note the COM port (Tools > Port)

#### 3. Upload Sketch
1. Open `light_controller_v2_arduino/light_controller_v2_arduino.ino`
2. Select board: Tools > Board > Arduino Uno (R3) or Arduino Uno R4 Minima/WiFi
3. Select port: Tools > Port > COM# (your port)
4. Click Upload (→ button)
5. Wait for "Done uploading"

#### 4. Verify Upload
- Open Serial Monitor (Ctrl+Shift+M)
- Set baud rate: 115200
- Should see: "Light Controller Ready"

---

### Arduino Due Setup

#### 1. Install Arduino IDE
Download from: https://www.arduino.cc/en/software

#### 2. Understand Dual USB Ports

**Programming Port (closer to power jack):**
- For uploading sketch
- For initial testing
- Standard USB-B connector

**Native USB Port (closer to reset button):**
- For running protocols
- For serial communication with Python
- Use this port with Light Controller V2.2

#### 3. Upload Sketch

**Using Programming Port:**
1. Connect Due to Programming Port
2. Open sketch in Arduino IDE
3. Select board: Tools > Board > Arduino Due (Programming Port)
4. Select port: Tools > Port > COM# (Programming)
5. Click Upload
6. Wait for "Done uploading"

#### 4. Switch to Native Port

**For running protocols:**
1. Disconnect USB from Programming Port
2. Connect USB to Native USB Port
3. Note the new COM port (Device Manager/System Info)
4. Use this port in Python script

#### 5. Verify Both Ports

**Programming Port test:**
- Open Serial Monitor
- Should see startup messages

**Native Port test:**
- Switch USB cable to Native Port
- Open Serial Monitor on new port
- Should see "Light Controller Ready"

---

### Arduino Mega Setup

#### 1. Install Arduino IDE
Download from: https://www.arduino.cc/en/software

#### 2. Connect Board
- Connect Mega to computer via USB
- Wait for driver installation (Windows)
- Note the COM port (Tools > Port)

#### 3. Upload Sketch
1. Open sketch in Arduino IDE
2. Select board: Tools > Board > Arduino Mega or Mega 2560
3. Select processor: Tools > Processor > ATmega2560
4. Select port: Tools > Port > COM# (your port)
5. Click Upload
6. Wait for "Done uploading"

#### 4. Verify Upload
- Open Serial Monitor
- Set baud rate: 115200
- Should see: "Light Controller Ready"

---

## Hardware Connections

### Basic LED Connection

**Simple Single LED:**

```
Arduino Pin (e.g., Digital 2)
    |
    +---- Resistor (220Ω) ---- LED Anode (+)
                                    |
                                LED Cathode (-)
                                    |
                                  GND
```

**Component values:**
- Resistor: (5V - LED_Vf) / LED_If
  - Example: (5V - 2V) / 20mA = 150Ω (use 220Ω)
- LED: Standard 5mm red/green/yellow

---

### Multiple LEDs (Same Channel)

**Series Connection:**
```
Pin → R → LED1 → LED2 → LED3 → GND
```
- Total voltage: Vf1 + Vf2 + Vf3 < 5V
- Same current through all LEDs
- One resistor for all

**Parallel Connection:**
```
         +→ R1 → LED1 →+
Pin →----+→ R2 → LED2 →+→ GND
         +→ R3 → LED3 →+
```
- Each LED needs its own resistor
- Total current = I1 + I2 + I3
- Check Arduino pin current limit (20mA)

---

### High-Power LED Connection

**Using Transistor (for >20mA):**

```
Arduino Pin
    |
    +---- 1kΩ Resistor ---- Transistor Base (2N2222)
                                  |
                            Transistor Emitter
                                  |
                                 GND

Transistor Collector
    |
LED Cathode (-)
    |
LED Anode (+)
    |
External Power Supply (+5V or more)
```

**Using MOSFET (for high current):**

```
Arduino Pin
    |
    +---- 1kΩ Resistor ---- MOSFET Gate (e.g., IRF520)
                                  |
                            MOSFET Source
                                  |
                                 GND

MOSFET Drain
    |
LED Cathode (-)
    |
LED Anode (+)
    |
External Power Supply (+)
```

**Important:**
- Always use current-limiting resistor with LEDs
- Match external supply voltage to LED requirements
- Ensure common ground between Arduino and external supply

---

### Complete 4-Channel Setup

```
CH1 (Pin 2) → R1 (220Ω) → LED1+ → LED1- → GND
CH2 (Pin 4) → R2 (220Ω) → LED2+ → LED2- → GND
CH3 (Pin 6) → R3 (220Ω) → LED3+ → LED3- → GND
CH4 (Pin 8) → R4 (220Ω) → LED4+ → LED4- → GND

Power: USB to Arduino
Ground: All LEDs to Arduino GND
```

**Breadboard layout:**
1. Place Arduino on breadboard
2. Connect each pin to resistor
3. Connect resistor to LED anode
4. Connect LED cathode to ground rail
5. Connect ground rail to Arduino GND

---

## Verification

### Visual Test

1. **Power LED:**
   - Arduino power LED should be ON
   - Indicates board is powered

2. **L LED (Pin 13):**
   - May blink during upload
   - Normal behavior

3. **TX/RX LEDs:**
   - Blink during serial communication
   - Indicates data transfer

---

### Serial Monitor Test

**Steps:**
1. Open Arduino IDE
2. Tools > Serial Monitor (or Ctrl+Shift+M)
3. Set baud rate: 115200
4. Should see: "Light Controller Ready"

**Expected output:**
```
Light Controller V2.2 Ready
Waiting for commands...
```

**If no output:**
- Check USB connection
- Verify COM port selection
- Re-upload sketch
- Check baud rate setting

---

### LED Test

**Manual test via Serial Monitor:**

**Turn on CH1:**
```
Send: CH1_ON
Expected: LED on Pin 2 turns ON
```

**Turn off CH1:**
```
Send: CH1_OFF
Expected: LED on Pin 2 turns OFF
```

**Test all channels:**
```
CH1_ON  → Pin 2 LED ON
CH2_ON  → Pin 4 LED ON
CH3_ON  → Pin 6 LED ON
CH4_ON  → Pin 8 LED ON

CH1_OFF → Pin 2 LED OFF
CH2_OFF → Pin 4 LED OFF
CH3_OFF → Pin 6 LED OFF
CH4_OFF → Pin 8 LED OFF
```

---

### Python Communication Test

**Quick test:**
```bash
cd /path/to/light_controller_v2.2
python -c "import serial; ser=serial.Serial('COM3', 115200, timeout=1); print(ser.readline()); ser.close()"
```

**Expected:** Should print Arduino startup message.

**If fails:**
- Check COM port (Device Manager/System Info)
- Ensure no other programs using port
- Close Arduino Serial Monitor
- Check Python serial library: `pip install pyserial`

---

### Full Protocol Test

**Quick test protocol** (save as `test.txt`):
```txt
# Quick test: 2 seconds ON, 2 seconds OFF, 3 repeats
PATTERN:1;CH:1;STATUS:1,0;TIME_S:2,2;REPEATS:3

START_TIME: {'CH1': 5}
```

**Run test:**
```bash
python lcfunc.py
# Select test.txt when prompted
# Select correct COM port
# Watch LED blink 3 times
```

**Expected behavior:**
- 5-second countdown
- CH1 LED: ON 2s, OFF 2s (repeat 3 times)
- "Protocol completed" message

---

## Troubleshooting

### Board Not Detected

**Symptoms:**
- No COM port in Arduino IDE
- Device Manager shows unknown device

**Solutions:**
1. Install/update USB drivers
2. Try different USB cable
3. Try different USB port
4. Restart computer
5. Check Arduino with another computer

---

### Upload Fails

**Symptoms:**
- Upload error in Arduino IDE
- "not in sync" error

**Solutions:**
1. Verify correct board selected
2. Verify correct port selected
3. Close Serial Monitor
4. Press Reset button before upload
5. Check USB cable quality

---

### No Serial Output

**Symptoms:**
- Serial Monitor shows nothing
- No "Ready" message

**Solutions:**
1. Check baud rate (must be 115200)
2. Verify correct port
3. Re-upload sketch
4. Try pressing Reset button
5. Check Serial Monitor settings (No line ending)

---

### LED Doesn't Light

**Symptoms:**
- LED not responding to commands
- No brightness change

**Check:**
1. **Polarity:** LED connected correctly? (Anode to pin, cathode to GND)
2. **Resistor:** Is resistor present and correct value?
3. **Wiring:** Solid connections? No loose wires?
4. **LED:** Test LED with known good circuit
5. **Pin:** Try different pin to test

---

### Due USB Port Confusion

**Symptom:**
- Works after upload, fails when running protocol

**Solution:**
- Upload via Programming Port
- Switch to Native USB Port for protocol
- Update COM port in Python script

---

## MCP4728 I2C DAC Setup (Optional)

The MCP4728 is a 4-channel 12-bit DAC (Digital-to-Analog Converter) that provides true analog voltage output instead of PWM. This is useful for applications requiring smooth analog signals without PWM noise.

### When to Use MCP4728

| Feature          | PWM (Standard)   | MCP4728 DAC               |
| ---------------- | ---------------- | ------------------------- |
| Output type      | PWM (pulsed)     | True analog               |
| Resolution       | 8-bit (0-255)    | 12-bit (0-4095)           |
| Filtering needed | Yes (for smooth) | No                        |
| Channels         | Up to 13 pins    | 4 channels                |
| Use case         | Most LEDs        | Analog control, precision |

**Use MCP4728 when you need:**
- Smooth analog voltage without PWM ripple
- Higher resolution (4096 steps vs 256)
- Precise voltage control (e.g., laser drivers, analog sensors)
- Interference-sensitive applications

---

### Hardware Requirements

1. **MCP4728 Module** (recommended: Adafruit MCP4728 Breakout)
2. **I2C Connection Wires** (4 wires: VCC, GND, SDA, SCL)
3. **Pull-up Resistors** (usually included on breakout boards)

---

### Wiring Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP4728 WIRING                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Arduino Due (3.3V)          MCP4728 Module               │
│   ┌─────────────┐             ┌─────────────┐              │
│   │             │             │             │              │
│   │  3.3V ──────┼─────────────┼── VCC       │              │
│   │             │             │             │              │
│   │  GND  ──────┼─────────────┼── GND       │              │
│   │             │             │             │              │
│   │  SDA (20) ──┼─────────────┼── SDA       │              │
│   │             │             │             │              │
│   │  SCL (21) ──┼─────────────┼── SCL       │              │
│   │             │             │             │              │
│   └─────────────┘             │  VA ────────┼── Output A   │
│                               │  VB ────────┼── Output B   │
│                               │  VC ────────┼── Output C   │
│                               │  VD ────────┼── Output D   │
│                               └─────────────┘              │
│                                                             │
│   Arduino Uno/Mega (5V)       MCP4728 Module               │
│   ┌─────────────┐             ┌─────────────┐              │
│   │             │             │             │              │
│   │  5V   ──────┼─────────────┼── VCC       │              │
│   │             │             │             │              │
│   │  GND  ──────┼─────────────┼── GND       │              │
│   │             │             │             │              │
│   │  A4 (SDA) ──┼─────────────┼── SDA       │              │
│   │             │             │             │              │
│   │  A5 (SCL) ──┼─────────────┼── SCL       │              │
│   │             │             │             │              │
│   └─────────────┘             └─────────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Pin Connection Table

| MCP4728 Pin | Arduino Due  | Arduino Uno R3/R4 | Arduino Mega |
| ----------- | ------------ | ----------------- | ------------ |
| VCC         | **3.3V** ⚠️   | 5V                | 5V           |
| GND         | GND          | GND               | GND          |
| SDA         | SDA (Pin 20) | A4                | SDA (Pin 20) |
| SCL         | SCL (Pin 21) | A5                | SCL (Pin 21) |
| LDAC        | GND (or NC)  | GND (or NC)       | GND (or NC)  |

> ⚠️ **IMPORTANT - Arduino Due Voltage:**
> - Arduino Due operates at **3.3V** - connect MCP4728 VCC to 3.3V pin
> - MCP4728 output voltage will be 0-3.3V (not 0-5V) when powered by Due
> - Do NOT connect MCP4728 to 5V when using Due - it may damage the I2C pins!

---

### Library Installation

**Method 1: Arduino IDE Library Manager (Recommended)**
1. Open Arduino IDE
2. Go to **Sketch → Include Library → Manage Libraries...**
3. Search for "Adafruit MCP4728"
4. Click **Install** on "Adafruit MCP4728" library
5. When prompted, also install "Adafruit BusIO"

**Method 2: PlatformIO**
```ini
lib_deps = 
    adafruit/Adafruit MCP4728@^1.0.0
    adafruit/Adafruit BusIO@^1.14.0
```

**Method 3: Manual Installation**
```bash
# Navigate to Arduino libraries folder
cd ~/Documents/Arduino/libraries

# Clone required libraries
git clone https://github.com/adafruit/Adafruit_MCP4728.git
git clone https://github.com/adafruit/Adafruit_BusIO.git
```

---

### Firmware Configuration

**Step 1:** Enable MCP4728 support in the Arduino sketch header:

```cpp
#define MCP4728_ENABLE 1  // Enable MCP4728 support
```

**Step 2:** Configure channel pins using virtual pin numbers (201-204):

```cpp
// Example: 2 MCP4728 channels + 2 PWM channels
const int MAX_CHANNEL_NUM = 4;
const int channelPins[MAX_CHANNEL_NUM] = {201, 202, 6, 8};
// CH1: MCP4728 Channel A (12-bit DAC)
// CH2: MCP4728 Channel B (12-bit DAC)
// CH3: PWM pin 6 (8-bit)
// CH4: PWM pin 8 (8-bit)
// Channel types auto-detected from pin numbers!
```

---

### Virtual Pin System

MCP4728 channels use virtual pin numbers 201-204:

| Virtual Pin | MCP4728 Channel | Output Voltage |
| ----------- | --------------- | -------------- |
| 201         | Channel A       | VA (0 to VCC)  |
| 202         | Channel B       | VB (0 to VCC)  |
| 203         | Channel C       | VC (0 to VCC)  |
| 204         | Channel D       | VD (0 to VCC)  |

**Output Voltage Range:**
- With 5V Arduino (Uno/Mega): 0-5V output
- With 3.3V Arduino (Due): 0-3.3V output

---

### Protocol Example

Test your MCP4728 setup with this protocol:

```txt
# MCP4728 Test Protocol - 12-bit DAC outputs
# Channel 1: MCP4728 A, Channel 2: MCP4728 B

# Smooth ramp using 12-bit values (0-4095)
PATTERN:1;CH:1;RAMP:(L:0,4095,5000),(L:4095,0,5000);REPEATS:2

# Step through voltage levels: 0V, 1.25V, 2.5V, 3.75V, 5V
PATTERN:1;CH:2;STATUS:0,1024,2048,3072,4095;TIME_MS:2000,2000,2000,2000,2000;REPEATS:1

START_TIME: {'CH1': 0, 'CH2': 0}
```

---

### Value Handling for MCP4728

The firmware uses the virtual pin system to auto-detect channel types:

| Protocol Value | MCP4728 Output (12-bit) | Notes                    |
| -------------- | ----------------------- | ------------------------ |
| `0.0` - `1.0`  | 0 - 4095                | Normalized (recommended) |
| `0` - `4095`   | 0 - 4095                | Direct 12-bit values     |
| `0` - `255`    | 0 - 255 ⚠️               | Works but low resolution |

> **Recommendation:** Use normalized values (0.0-1.0) or full 12-bit values (0-4095) for MCP4728 channels to take advantage of the higher resolution.

---

### I2C Scanner Test

If MCP4728 is not detected, run this I2C scanner sketch to verify connection:

```cpp
#include <Wire.h>

void setup() {
  Wire.begin();
  Serial.begin(115200);
  Serial.println("I2C Scanner");
}

void loop() {
  byte error, address;
  int nDevices = 0;
  
  Serial.println("Scanning...");
  
  for(address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    
    if (error == 0) {
      Serial.print("I2C device found at 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
      nDevices++;
    }
  }
  
  if (nDevices == 0)
    Serial.println("No I2C devices found!");
  else
    Serial.println("Done.");
    
  delay(5000);
}
```

**Expected output:** `I2C device found at 0x60` (MCP4728 default address)

---

### Troubleshooting MCP4728

**"MCP4728 not found" message:**
1. ✅ Check wiring (VCC, GND, SDA, SCL)
2. ✅ Verify power supply matches Arduino voltage (3.3V for Due, 5V for Uno)
3. ✅ Run I2C scanner to verify device detected at 0x60
4. ✅ Ensure Adafruit MCP4728 library is installed
5. ✅ Check for loose connections or damaged wires

**No output voltage:**
1. Verify LDAC pin is grounded or not used
2. Check output connections
3. Measure with multimeter

**Noisy output:**
1. Add decoupling capacitor (0.1µF) near VCC
2. Keep I2C wires short
3. Check grounding

---

## Native DAC Support (Arduino Due, Zero, R4)

Some Arduino boards have built-in DAC (Digital-to-Analog Converter) pins for true analog output.

### Supported Boards

| Board          | DAC Pins   | Resolution      | Voltage Range |
| -------------- | ---------- | --------------- | ------------- |
| Arduino Due    | DAC0, DAC1 | 12-bit (0-4095) | 0-3.3V        |
| Arduino Zero   | DAC0       | 10-bit (0-1023) | 0-3.3V        |
| Arduino Uno R4 | DAC        | 12-bit (0-4095) | 0-5V          |

### Virtual Pin Mapping

Native DAC pins use virtual pin numbers 100+:

| Virtual Pin | Real Pin | Board         |
| ----------- | -------- | ------------- |
| 100         | DAC0     | Due, Zero, R4 |
| 101         | DAC1     | Due only      |

### Protocol Usage

```cpp
// Use native DAC for channels 1-2, PWM for channel 3
const int channelPins[MAX_CHANNEL_NUM] = {100, 101, 13};
```

---

## See Also

- [Installation Guide](INSTALLATION.md) - Software setup
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues
- [Usage Guide](USAGE.md) - Running protocols

---

*Last Updated: January 24, 2026 (v2.3.2)*
