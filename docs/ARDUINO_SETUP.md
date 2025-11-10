# Arduino Setup Guide

Complete hardware setup guide for Arduino boards.

---

## Table of Contents

- [Supported Boards](#supported-boards)
- [Hardware Requirements](#hardware-requirements)
- [Pin Assignments](#pin-assignments)
- [Board-Specific Setup](#board-specific-setup)
- [Hardware Connections](#hardware-connections)
- [Verification](#verification)

---

## Supported Boards

### Arduino Uno

**Specifications:**
- **Channels:** 4 (CH1-CH4)
- **Pins:** Digital 2, 4, 6, 8
- **Memory:** Limited (1KB EEPROM)
- **Max Commands:** ~200-300

**Best for:**
- Simple protocols
- Learning
- Budget projects
- Limited channel needs

---

### Arduino Due

**Specifications:**
- **Channels:** 4 (CH1-CH4)
- **Pins:** Digital 2, 4, 6, 8
- **Memory:** Large (4KB EEPROM)
- **Max Commands:** ~1000-1500
- **USB Ports:** Programming + Native

**Best for:**
- Complex protocols
- Long sequences
- Professional projects
- Maximum capability

**Important:** Two USB ports!
- **Programming Port:** For uploading sketch
- **Native Port:** For running protocol (serial communication)

---

### Arduino Mega

**Specifications:**
- **Channels:** 4 (CH1-CH4)
- **Pins:** Digital 2, 4, 6, 8
- **Memory:** Large (4KB EEPROM)
- **Max Commands:** ~400-600

**Best for:**
- Medium complexity
- Multiple projects
- Good balance
- Extended features

---

### Feature Comparison

| Feature | Uno | Due | Mega |
|---------|-----|-----|------|
| Channels | 4 | 4 | 4 |
| Memory | 1KB | 4KB | 4KB |
| Max Commands | ~200-300 | ~1000-1500 | ~400-600 |
| USB Ports | 1 | 2 | 1 |
| Best For | Simple | Complex | Medium |
| Price | $ | $$$ | $$ |

---

## Hardware Requirements

### Required Components

1. **Arduino Board**
   - Uno, Due, or Mega (see above)
   - USB cable (Type B for Uno/Mega, Micro-B for Due)

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

| Channel | Pin | Arduino Uno | Arduino Due | Arduino Mega |
|---------|-----|-------------|-------------|--------------|
| CH1 | Digital 2 | ✓ | ✓ | ✓ |
| CH2 | Digital 4 | ✓ | ✓ | ✓ |
| CH3 | Digital 6 | ✓ | ✓ | ✓ |
| CH4 | Digital 8 | ✓ | ✓ | ✓ |

**Note:** Pins are fixed in the Arduino sketch and cannot be changed without modifying the code.

---

### Pin Characteristics

**Digital Output:**
- Logic HIGH: 5V (Uno/Mega) or 3.3V (Due)
- Logic LOW: 0V
- Max current per pin: 20mA (Uno/Mega), 15mA (Due)
- **Important:** Do not exceed max current!

**Use resistors or transistors for higher currents.**

---

## Board-Specific Setup

### Arduino Uno Setup

#### 1. Install Arduino IDE
Download from: https://www.arduino.cc/en/software

#### 2. Connect Board
- Connect Uno to computer via USB
- Wait for driver installation (Windows)
- Note the COM port (Tools > Port)

#### 3. Upload Sketch
1. Open `light_controller_v2_arduino/light_controller_v2_arduino.ino`
2. Select board: Tools > Board > Arduino Uno
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

## See Also

- [Installation Guide](INSTALLATION.md) - Software setup
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues
- [Usage Guide](USAGE.md) - Running protocols

---

*Last Updated: November 8, 2025*
