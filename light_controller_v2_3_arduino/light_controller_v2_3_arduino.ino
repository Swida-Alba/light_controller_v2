//* =====================================================================
//* LIGHT CONTROLLER V2.3.2 - Arduino Firmware
//* =====================================================================
//* Supports: PWM pins, Native DAC (100-101), MCP4728 I2C DAC (201-204)
//* Channel types auto-detected from pin numbers.
//* =====================================================================

//* =====================================================================
//*                    USER CONFIGURATION SECTION
//* =====================================================================
//* Modify these settings to match your hardware setup.
//* =====================================================================

//* ---------------------------------------------------------------------
//* CHANNEL CONFIGURATION - VIRTUAL PIN SYSTEM
//* ---------------------------------------------------------------------
//* Pin Number Ranges (channel type auto-detected):
//*   0-99:     PWM pins (use actual Arduino digital pin numbers)
//*   100-101:  Native DAC (100=DAC0, 101=DAC1) - Due, Zero, Uno R4
//*   201-204:  MCP4728 I2C DAC (201=CH_A, 202=CH_B, 203=CH_C, 204=CH_D)
//*
//* Example configurations:
//*   {11, 12, 13, 10}       - 4 PWM channels on pins 11,12,13,10
//*   {11, 12, 201, 202}     - 2 PWM + 2 MCP4728 channels
//*   {100, 101, 201, 202}   - 2 Native DAC + 2 MCP4728 channels
//*   {11, 100, 201, 202}    - 1 PWM + 1 Native DAC + 2 MCP4728
//* ---------------------------------------------------------------------

const int MAX_CHANNEL_NUM = 4;              //* Total number of channels
const int MAX_PATTERN_NUM = 10;             //* Max patterns per channel
const int PATTERN_LENGTH = 4;               //* Max steps per pattern

//* Channel pin assignments (type auto-detected from virtual pin number)
const int channelPins[MAX_CHANNEL_NUM] = {201, 202, 203, 204};  //* Example: 4 MCP4728 channels

//* Virtual pin constants
#define NATIVE_DAC_PIN_BASE 100   //* 100=DAC0, 101=DAC1
#define MCP4728_PIN_BASE    201   //* 201-204 = MCP4728 channels A-D

//* ---------------------------------------------------------------------
//* FEATURE ENABLE/DISABLE
//* ---------------------------------------------------------------------

#define PULSE_MODE_ENABLE 1     //* 1=Enable pulse modulation, 0=Disable
#define PWM_RAMP_ENABLE 1       //* 1=Enable PWM/RAMP gradients, 0=Binary only
#define MCP4728_ENABLE 1        //* 1=Enable MCP4728 I2C DAC, 0=Disable
#define CHANNEL_MONITOR_ENABLE 1 //* 1=Enable real-time channel monitoring, 0=Disable

//* ---------------------------------------------------------------------
//* RAMP CONFIGURATION
//* ---------------------------------------------------------------------

#define MAX_RAMP_SEGMENTS 4     //* Max segments in a combined RAMP command

//* ---------------------------------------------------------------------
//* SERIAL COMMUNICATION
//* ---------------------------------------------------------------------

#define SERIAL_BAUD_RATE 9600   //* Baud rate for serial communication
#define SERIAL_TIMEOUT_MS 5000  //* Timeout waiting for serial connection

//* ---------------------------------------------------------------------
//* MONITOR CONFIGURATION
//* ---------------------------------------------------------------------

#define DEFAULT_MONITOR_STEP_MS 100  //* Default interval for channel value printing

//* =====================================================================
//*                    END OF USER CONFIGURATION
//* =====================================================================

//* ---------------------------------------------------------------------
//* OUTPUT TYPE CONSTANTS
//* ---------------------------------------------------------------------

//* Channel types will be auto-detected in setup() from pin numbers
char channelTypes[MAX_CHANNEL_NUM];  //* Populated at startup

#define OUTPUT_TYPE_PWM     'P'   //* 8-bit PWM (0-255)
#define OUTPUT_TYPE_DAC     'D'   //* 12-bit Native DAC (0-4095)
#define OUTPUT_TYPE_MCP4728 'M'   //* 12-bit MCP4728 DAC (0-4095)
#define OUTPUT_TYPE_BINARY  'B'   //* Binary (0 or 1)

//* Output resolution constants
#define RESOLUTION_BINARY 1       //* 0 or 1
#define RESOLUTION_8BIT   255     //* 0-255
#define RESOLUTION_12BIT  4095    //* 0-4095

//* ---------------------------------------------------------------------
//* RAMP EASING MODE CONSTANTS
//* ---------------------------------------------------------------------
#define RAMP_MODE_LINEAR   0   //* Linear interpolation
#define RAMP_MODE_COSINE   1   //* Full cosine (ease-in-out)
#define RAMP_MODE_EASE_IN  2   //* Cosine ease-in only
#define RAMP_MODE_EASE_OUT 3   //* Cosine ease-out only
#define RAMP_MODE_CUSTOM   4   //* Custom t range
#define RAMP_MODE_FUNC     5   //* Custom function (F mode)

//* ---------------------------------------------------------------------
//* LIBRARY INCLUDES
//* ---------------------------------------------------------------------

#if MCP4728_ENABLE == 1
  #include <Adafruit_MCP4728.h>
  #include <Wire.h>
  Adafruit_MCP4728 mcp4728;
  bool mcp4728_initialized = false;
#endif

#include "custom_easing.h"
#include "function_dispatcher.h"

//* ---------------------------------------------------------------------
//* BOARD-SPECIFIC NATIVE DAC DETECTION
//* ---------------------------------------------------------------------

#ifdef ARDUINO_ARCH_SAM
  #define HAS_NATIVE_DAC 1
  #define NATIVE_DAC_COUNT 2
  const int NATIVE_DAC_PINS[] = {DAC0, DAC1};
#elif defined(ARDUINO_ARCH_SAMD)
  #define HAS_NATIVE_DAC 1
  #define NATIVE_DAC_COUNT 1
  const int NATIVE_DAC_PINS[] = {DAC0};
#elif defined(ARDUINO_ARCH_RENESAS)
  #define HAS_NATIVE_DAC 1
  #define NATIVE_DAC_COUNT 1
  const int NATIVE_DAC_PINS[] = {DAC};
#else
  #define HAS_NATIVE_DAC 0
  #define NATIVE_DAC_COUNT 0
  const int NATIVE_DAC_PINS[] = {};
#endif

//* ---------------------------------------------------------------------
//* COMPILE-TIME FEATURE FLAGS
//* ---------------------------------------------------------------------

#if PULSE_MODE_ENABLE == 1
  const bool PULSE_MODE_ENABLED = true;
#else
  const bool PULSE_MODE_ENABLED = false;
#endif

#if PWM_RAMP_ENABLE == 1
  const bool PWM_RAMP_ENABLED = true;
#else
  const bool PWM_RAMP_ENABLED = false;
#endif

//* ---------------------------------------------------------------------
//* DATA STRUCTURES
//* ---------------------------------------------------------------------

//* RAMP segment structure (for one part of a gradient)
struct RampSegment {
    uint16_t start_value;      //* Starting value (resolution depends on channel type)
    uint16_t end_value;        //* Ending value
    unsigned long duration_ms; //* Segment duration in milliseconds
    byte easing_mode;          //* RAMP_MODE_LINEAR, COSINE, etc.
    float t_start;             //* Custom easing: start parameter
    float t_end;               //* Custom easing: end parameter
    char func_name[16];        //* F mode: custom function name
};

//* RAMP pattern structure
struct RampPattern {
    RampSegment segments[MAX_RAMP_SEGMENTS];
    int num_segments;
    unsigned long total_duration_ms;
    bool active;
};

//* Compressed pattern structure - uses uint16_t for 12-bit DAC support
struct CompressedPattern {
    uint16_t status[MAX_PATTERN_NUM][PATTERN_LENGTH];  //* 0-4095 for DAC, 0-255 for PWM
    unsigned long time_ms[MAX_PATTERN_NUM][PATTERN_LENGTH];
    
#if PULSE_MODE_ENABLE == 1
    unsigned long period[MAX_PATTERN_NUM][PATTERN_LENGTH];
    unsigned long pulse_width[MAX_PATTERN_NUM][PATTERN_LENGTH];
#endif

#if PWM_RAMP_ENABLE == 1
    RampPattern ramp[MAX_PATTERN_NUM];
#endif
    
    int repeats[MAX_PATTERN_NUM];
    int pattern_length[MAX_PATTERN_NUM];
    int pattern_num;
};

CompressedPattern channelPatterns[MAX_CHANNEL_NUM];

//* ---------------------------------------------------------------------
//* STATE VARIABLES
//* ---------------------------------------------------------------------

bool patternsReceived = false;
bool allChannelsCompleted = false;

int repeatCounters[MAX_CHANNEL_NUM][MAX_PATTERN_NUM] = {{0}};
int patternIndices[MAX_CHANNEL_NUM][MAX_PATTERN_NUM] = {{0}};
int patternSequence[MAX_CHANNEL_NUM] = {0};
unsigned long nextEventTime[MAX_CHANNEL_NUM] = {0};
bool channelActive[MAX_CHANNEL_NUM] = {false};
bool channelLoop[MAX_CHANNEL_NUM] = {false};  //* LOOP mode: true = repeat forever

#if PULSE_MODE_ENABLE == 1
bool pulseState[MAX_CHANNEL_NUM] = {false};
unsigned long nextPulseTime[MAX_CHANNEL_NUM] = {0};
#endif

#if PWM_RAMP_ENABLE == 1
unsigned long rampStartTime[MAX_CHANNEL_NUM] = {0};
int rampCurrentSegment[MAX_CHANNEL_NUM] = {0};
uint16_t currentOutputValue[MAX_CHANNEL_NUM] = {0};  //* Current output (0-4095 or 0-255)
unsigned long lastRampUpdate[MAX_CHANNEL_NUM] = {0};
#endif

#if CHANNEL_MONITOR_ENABLE == 1
unsigned long lastMonitorPrintTime = 0;
unsigned long monitorPrintStep = DEFAULT_MONITOR_STEP_MS;
bool monitorEnabled = true;  //* Can be toggled at runtime via MONITOR_ENABLE command
#endif

//* ---------------------------------------------------------------------
//* FUNCTION PROTOTYPES
//* ---------------------------------------------------------------------

void read_serial_command(bool &wait_for_command);
void parse_pattern(String command);
void parse_ramp_pattern(String command);
void initializePatterns();
void executePatterns();
void executeRamp(int ch);
uint16_t calculateEasedValue(float progress, uint16_t start_val, uint16_t end_val, 
                              byte easing_mode, float t_start, float t_end, int ch);
void setChannelOutput(int ch, uint16_t value);
uint16_t getChannelMaxValue(int ch);
char getChannelType(int ch);
void parseUInt16Array(String data, uint16_t arr[], int &actualLength, int ch);
void parseULongArray(String data, unsigned long arr[], int &actualLength);
void calibrate_time(String command);
void calibrate_time_v11(String command);
void calibrate_timestamps(String command);
int getFreeRAM();
void reportMemoryInfo();
void reportChannelConfig();
void updateChannelMonitor();
void printChannelValues();
void setMonitorPrintStep(unsigned long step_ms);
void setMonitorEnabled(bool enabled);

//* ---------------------------------------------------------------------
//* HELPER FUNCTIONS - VIRTUAL PIN DETECTION
//* ---------------------------------------------------------------------

//* Auto-detect channel type from virtual pin number
char detectPinType(int pin) {
    if (pin >= MCP4728_PIN_BASE && pin <= MCP4728_PIN_BASE + 3) {
        return OUTPUT_TYPE_MCP4728;  //* 201-204 = MCP4728
    }
    if (pin >= NATIVE_DAC_PIN_BASE && pin <= NATIVE_DAC_PIN_BASE + 1) {
        return OUTPUT_TYPE_DAC;      //* 100-101 = Native DAC
    }
    return OUTPUT_TYPE_PWM;          //* 0-99 = PWM (default)
}

//* Check if pin is MCP4728 DAC
bool isMCP4728Pin(int pin) {
    return (pin >= MCP4728_PIN_BASE && pin <= MCP4728_PIN_BASE + 3);
}

//* Check if pin is Native DAC
bool isNativeDACPin(int pin) {
    return (pin >= NATIVE_DAC_PIN_BASE && pin <= NATIVE_DAC_PIN_BASE + 1);
}

//* Get MCP4728 channel index from virtual pin number (201->0, 202->1, etc.)
int getMCP4728Channel(int pin) {
    return pin - MCP4728_PIN_BASE;
}

//* Get Native DAC index from virtual pin number (100->0, 101->1)
int getNativeDACIndex(int pin) {
    return pin - NATIVE_DAC_PIN_BASE;
}

//* ---------------------------------------------------------------------
//* HELPER FUNCTIONS - CHANNEL PROPERTIES
//* ---------------------------------------------------------------------

//* Get the maximum value for a channel based on its type
uint16_t getChannelMaxValue(int ch) {
    if (ch < 0 || ch >= MAX_CHANNEL_NUM) return RESOLUTION_8BIT;
    
    char type = channelTypes[ch];
    switch (type) {
        case OUTPUT_TYPE_BINARY:  return RESOLUTION_BINARY;
        case OUTPUT_TYPE_PWM:     return RESOLUTION_8BIT;
        case OUTPUT_TYPE_DAC:     return RESOLUTION_12BIT;
        case OUTPUT_TYPE_MCP4728: return RESOLUTION_12BIT;
        default:                  return RESOLUTION_8BIT;
    }
}

//* Get the channel type
char getChannelType(int ch) {
    if (ch < 0 || ch >= MAX_CHANNEL_NUM) return OUTPUT_TYPE_PWM;
    return channelTypes[ch];
}

//* Check if a channel is 12-bit (DAC)
bool is12BitChannel(int ch) {
    char type = getChannelType(ch);
    return (type == OUTPUT_TYPE_DAC || type == OUTPUT_TYPE_MCP4728);
}

//* Clip value to channel's valid range
uint16_t clipToChannelRange(uint16_t value, int ch) {
    uint16_t maxVal = getChannelMaxValue(ch);
    if (value > maxVal) return maxVal;
    return value;
}

//* Parse and validate a value for a channel
//* Input formats:
//*   0.0-1.0: Normalized - scale to channel's max
//*   Integer 0 or 1: Binary HIGH/LOW - 0 stays 0, 1 becomes max (255 or 4095)
//*   Integer 2-255: 8-bit value - keep as-is
//*   Integer 256-4095: 12-bit value - clip if on 8-bit channel
//*   >4095: Clip to max
uint16_t parseChannelValue(String valueStr, int ch, bool &hasError) {
    hasError = false;
    uint16_t maxVal = getChannelMaxValue(ch);
    bool is12Bit = is12BitChannel(ch);
    
    //* Check for decimal point
    bool hasDecimal = (valueStr.indexOf('.') != -1);
    float value = valueStr.toFloat();
    
    //* Normalized value (0.0-1.0) - scale to channel max
    if (hasDecimal && value >= 0.0f && value <= 1.0f) {
        return (uint16_t)(value * maxVal);
    }
    
    //* Decimal not in 0-1 range - ERROR
    if (hasDecimal) {
        Serial.print("ERR:DECIMAL_NOT_NORMALIZED CH");
        Serial.print(ch + 1);
        Serial.print(" val=");
        Serial.println(valueStr);
        hasError = true;
        return 0;
    }
    
    //* Integer values
    int intValue = (int)value;
    
    //* Special case: Integer 0 or 1 treated as binary HIGH/LOW
    //* This ensures backward compatibility with protocols using 0,1 for OFF/ON
    //* 0 = OFF (value 0), 1 = ON (full intensity = maxVal)
    if (intValue == 0) {
        return 0;
    }
    if (intValue == 1) {
        return maxVal;  //* Full intensity: 255 for PWM, 4095 for DAC
    }
    
    //* 8-bit range (2-255) - accept as-is for any channel
    if (intValue <= 255) {
        return (uint16_t)intValue;
    }
    
    //* 12-bit range (256-4095)
    if (intValue <= 4095) {
        if (!is12Bit) {
            //* PWM channel: silently cap at 255
            return 255;
        }
        return (uint16_t)intValue;
    }
    
    //* Value > 4095: silently cap to channel max
    return maxVal;
}

//* Convert float value to channel resolution (for RAMP parsing)
//* Handles: 0.0-1.0 normalized, integer 0/1 as binary, 2-255 8-bit, 256-4095 12-bit
uint16_t convertToChannelResolution(float value, int ch) {
    uint16_t maxVal = getChannelMaxValue(ch);
    bool is12Bit = is12BitChannel(ch);
    
    //* Check for fractional part to determine if normalized
    bool hasFractionalPart = (value > 0.0f && value < 1.0f) || 
                              (value - (int)value != 0.0f);
    
    //* Normalized value (0.0-1.0 with decimal) - scale to channel max
    if (hasFractionalPart && value >= 0.0f && value <= 1.0f) {
        return (uint16_t)(value * maxVal);
    }
    
    //* Integer-like values
    int intValue = (int)value;
    
    //* Special case: Integer 0 or 1 treated as binary HIGH/LOW
    if (intValue == 0) {
        return 0;
    }
    if (intValue == 1) {
        return maxVal;  //* Full intensity: 255 for PWM, 4095 for DAC
    }
    
    //* 8-bit range (2-255) - accept as-is for any channel
    if (intValue <= 255) {
        return (uint16_t)intValue;
    }
    
    //* 12-bit range (256-4095)
    if (intValue <= 4095) {
        if (!is12Bit) {
            //* PWM channel: silently cap at 255
            return 255;
        }
        return (uint16_t)intValue;
    }
    
    //* Value > 4095: silently cap to channel max
    return maxVal;
}

//* ---------------------------------------------------------------------
//* OUTPUT FUNCTIONS
//* ---------------------------------------------------------------------

void setChannelOutput(int ch, uint16_t value) {
    if (ch < 0 || ch >= MAX_CHANNEL_NUM) return;
    
    int pin = channelPins[ch];
    char type = channelTypes[ch];
    
    //* Clip value to channel's valid range
    value = clipToChannelRange(value, ch);
    
#if PWM_RAMP_ENABLE == 1
    currentOutputValue[ch] = value;
#endif
    
    switch (type) {
        case OUTPUT_TYPE_BINARY:
            digitalWrite(pin, value > 0 ? HIGH : LOW);
            break;
            
        case OUTPUT_TYPE_PWM:
#if PWM_RAMP_ENABLE == 1
            if (PWM_RAMP_ENABLED) {
                analogWrite(pin, value);
            } else {
                digitalWrite(pin, value > 127 ? HIGH : LOW);
            }
#else
            digitalWrite(pin, value > 127 ? HIGH : LOW);
#endif
            break;
            
        case OUTPUT_TYPE_DAC:
#if HAS_NATIVE_DAC == 1
            {
                int dacIdx = getNativeDACIndex(pin);
                if (dacIdx >= 0 && dacIdx < NATIVE_DAC_COUNT) {
                    analogWrite(NATIVE_DAC_PINS[dacIdx], value);
                }
            }
#endif
            break;
            
        case OUTPUT_TYPE_MCP4728:
#if MCP4728_ENABLE == 1
            if (mcp4728_initialized) {
                int mcpCh = getMCP4728Channel(pin);
                if (mcpCh >= 0 && mcpCh <= 3) {
                    MCP4728_channel_t mcpChannel;
                    switch (mcpCh) {
                        case 0: mcpChannel = MCP4728_CHANNEL_A; break;
                        case 1: mcpChannel = MCP4728_CHANNEL_B; break;
                        case 2: mcpChannel = MCP4728_CHANNEL_C; break;
                        case 3: mcpChannel = MCP4728_CHANNEL_D; break;
                        default: mcpChannel = MCP4728_CHANNEL_A; break;
                    }
                    mcp4728.setChannelValue(mcpChannel, value);
                }
            }
#endif
            break;
    }
}

//* ---------------------------------------------------------------------
//* SETUP
//* ---------------------------------------------------------------------

void setup() {
    Serial.begin(SERIAL_BAUD_RATE);
    
    //* Wait for serial connection
    unsigned long startTime = millis();
    while (!Serial && (millis() - startTime < SERIAL_TIMEOUT_MS)) {
        ; //* Wait for serial port to connect
    }
    delay(2000);  //* Additional delay for USB enumeration
    
    Serial.println("BOOT:STARTING");  //* Debug: Indicate startup

    //* Auto-detect channel types from virtual pin numbers
    bool needsMCP4728 = false;
    for (int i = 0; i < MAX_CHANNEL_NUM; i++) {
        channelTypes[i] = detectPinType(channelPins[i]);
        if (channelTypes[i] == OUTPUT_TYPE_MCP4728) {
            needsMCP4728 = true;
        }
    }
    
    Serial.print("BOOT:CHANNELS=");
    for (int i = 0; i < MAX_CHANNEL_NUM; i++) {
        Serial.print(channelTypes[i]);
    }
    Serial.println();

#if MCP4728_ENABLE == 1
    if (needsMCP4728) {
        Serial.println("BOOT:MCP4728_INIT");
        Wire.begin();
        Wire.setClock(100000);  //* Standard I2C speed
        
        //* Try to initialize MCP4728 with timeout protection
        unsigned long initStart = millis();
        bool initSuccess = false;
        
        //* First, check if device is present on I2C bus
        Wire.beginTransmission(0x60);  //* MCP4728 default address
        byte i2cError = Wire.endTransmission();
        
        if (i2cError == 0) {
            Serial.println("BOOT:MCP4728_FOUND");
            if (mcp4728.begin()) {
                mcp4728_initialized = true;
                //* Initialize all channels to 0
                mcp4728.setChannelValue(MCP4728_CHANNEL_A, 0);
                mcp4728.setChannelValue(MCP4728_CHANNEL_B, 0);
                mcp4728.setChannelValue(MCP4728_CHANNEL_C, 0);
                mcp4728.setChannelValue(MCP4728_CHANNEL_D, 0);
                Serial.println("MCP4728:OK");
            } else {
                mcp4728_initialized = false;
                Serial.println("MCP4728:INIT_FAIL");
            }
        } else {
            mcp4728_initialized = false;
            Serial.print("MCP4728:NOT_FOUND(I2C_ERR=");
            Serial.print(i2cError);
            Serial.println(")");
        }
    }
#endif
    
    Serial.println("BOOT:INIT_CHANNELS");
    for (int i = 0; i < MAX_CHANNEL_NUM; i++) {
        char type = channelTypes[i];
        int pin = channelPins[i];
        
        if (type == OUTPUT_TYPE_PWM || type == OUTPUT_TYPE_BINARY) {
            pinMode(pin, OUTPUT);
            digitalWrite(pin, LOW);
        }
        //* DAC and MCP4728 are initialized by their respective libraries
        
        channelPatterns[i].pattern_num = 0;
        
#if PWM_RAMP_ENABLE == 1
        rampStartTime[i] = 0;
        rampCurrentSegment[i] = 0;
        currentOutputValue[i] = 0;
        lastRampUpdate[i] = 0;
#endif
        
        //* Initialize pattern data
        for (int j = 0; j < MAX_PATTERN_NUM; j++) {
            channelPatterns[i].pattern_length[j] = 0;
#if PULSE_MODE_ENABLE == 1
            for (int k = 0; k < PATTERN_LENGTH; k++) {
                channelPatterns[i].period[j][k] = 0;
                channelPatterns[i].pulse_width[j][k] = 0;
            }
#endif
#if PWM_RAMP_ENABLE == 1
            channelPatterns[i].ramp[j].active = false;
            channelPatterns[i].ramp[j].num_segments = 0;
            channelPatterns[i].ramp[j].total_duration_ms = 0;
            for (int k = 0; k < MAX_RAMP_SEGMENTS; k++) {
                channelPatterns[i].ramp[j].segments[k].start_value = 0;
                channelPatterns[i].ramp[j].segments[k].end_value = 0;
                channelPatterns[i].ramp[j].segments[k].duration_ms = 0;
                channelPatterns[i].ramp[j].segments[k].easing_mode = RAMP_MODE_LINEAR;
                channelPatterns[i].ramp[j].segments[k].t_start = 0.0;
                channelPatterns[i].ramp[j].segments[k].t_end = 3.14159265;
                channelPatterns[i].ramp[j].segments[k].func_name[0] = '\0';
            }
#endif
        }
    }

    Serial.println("BOOT:READY");  //* Debug: Indicate ready for commands
    
    //* Wait for commands
    bool wait_for_command = true;
    while (wait_for_command) {
        read_serial_command(wait_for_command);
    }

    initializePatterns();
}

//* ---------------------------------------------------------------------
//* MAIN LOOP
//* ---------------------------------------------------------------------

void loop() {
    if (patternsReceived && !allChannelsCompleted) {
        executePatterns();
        
#if CHANNEL_MONITOR_ENABLE == 1
        updateChannelMonitor();
#endif
        
        //* Check for runtime serial commands (e.g., MONITOR_ENABLE:0)
        processRuntimeCommands();
        
        if (allChannelsCompleted) {
            while (true) { /* Program halted */ }
        }
    }
}

//* Process serial commands during pattern execution (limited set)
void processRuntimeCommands() {
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        
        if (command.startsWith("MONITOR_ENABLE:")) {
            int val = command.substring(15).toInt();
            setMonitorEnabled(val == 1);
            Serial.print("MONITOR_ENABLE:");
            Serial.println(val == 1 ? "1" : "0");
        }
        else if (command.startsWith("MONITOR_STEP:")) {
            int stepStart = 13;
            unsigned long step_ms = command.substring(stepStart).toInt();
            if (step_ms >= 10 && step_ms <= 10000) {
                setMonitorPrintStep(step_ms);
                Serial.print("MONITOR_STEP:");
                Serial.println(step_ms);
            }
        }
        //* Ignore other commands during execution
    }
}

//* ---------------------------------------------------------------------
//* SERIAL COMMAND PROCESSING
//* ---------------------------------------------------------------------

void read_serial_command(bool &wait_for_command) {
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        
        if (command.startsWith("PATTERN:")) {
#if PWM_RAMP_ENABLE == 1
            if (command.indexOf("RAMP:") != -1) {
                parse_ramp_pattern(command);
            } else {
                parse_pattern(command);
            }
#else
            parse_pattern(command);
#endif
            Serial.println(command);
        } 
        else if (command == "Bye") {
            Serial.println("Arrivederci");
            wait_for_command = false;
            patternsReceived = true;
        }
        else if (command.startsWith("Hello")) {
            //* Respond with full configuration
            Serial.print("Salve;PATTERN_LENGTH:");
            Serial.print(PATTERN_LENGTH);
            Serial.print(";MAX_PATTERN_NUM:");
            Serial.print(MAX_PATTERN_NUM);
            Serial.print(";MAX_CHANNEL_NUM:");
            Serial.print(MAX_CHANNEL_NUM);
            Serial.print(";MAX_RAMP_SEGMENTS:");
            Serial.print(MAX_RAMP_SEGMENTS);
            Serial.print(";PULSE_MODE:");
            Serial.print(PULSE_MODE_ENABLED ? "1" : "0");
            Serial.print(";PWM_RAMP_MODE:");
            Serial.print(PWM_RAMP_ENABLED ? "1" : "0");
#if MCP4728_ENABLE == 1
            Serial.print(";MCP4728:");
            Serial.print(mcp4728_initialized ? "1" : "0");
#endif
#if HAS_NATIVE_DAC == 1
            Serial.print(";NATIVE_DAC:");
            Serial.print(NATIVE_DAC_COUNT);
#endif
            //* Report channel types and max values
            Serial.print(";CH_TYPES:");
            for (int i = 0; i < MAX_CHANNEL_NUM; i++) {
                Serial.print(channelTypes[i]);
            }
            Serial.print(";CH_MAX:");
            for (int i = 0; i < MAX_CHANNEL_NUM; i++) {
                if (i > 0) Serial.print(",");
                Serial.print(getChannelMaxValue(i));
            }
            Serial.println();
        }
        else if (command == "GET_CHANNELS") {
            reportChannelConfig();
        }
        else if (command == "GET_MEMORY") {
            reportMemoryInfo();
        }
        else if (command.startsWith("calibrate_timestamps_")) {
            calibrate_timestamps(command);
        }
        else if (command.startsWith("calibrate_v11_")) {
            calibrate_time_v11(command);
        }
        else if (command.startsWith("calibrate_")) { 
            calibrate_time(command);
        }
        else if (command.startsWith("MONITOR_STEP:")) {
            int stepStart = command.indexOf("MONITOR_STEP:") + 13;
            unsigned long step_ms = command.substring(stepStart).toInt();
            if (step_ms >= 10 && step_ms <= 10000) {
                setMonitorPrintStep(step_ms);
                Serial.print("MONITOR_STEP:");
                Serial.println(step_ms);
            } else {
                Serial.println("ERR:MONITOR_STEP range 10-10000ms");
            }
        }
        else if (command.startsWith("MONITOR_ENABLE:")) {
            int val = command.substring(15).toInt();
            setMonitorEnabled(val == 1);
            Serial.print("MONITOR_ENABLE:");
            Serial.println(val == 1 ? "1" : "0");
        }
        else if (command.startsWith("LOOP:")) {
            //* Parse LOOP command: LOOP:CH:1:VALUE:1 (channel 1, loop=1)
            //* or LOOP:CH:2:VALUE:0 (channel 2, no loop)
            int chStart = command.indexOf("CH:") + 3;
            int chEnd = command.indexOf(":VALUE:");
            int valStart = command.indexOf("VALUE:") + 6;
            
            if (chStart > 3 && chEnd > chStart && valStart > 6) {
                int ch = command.substring(chStart, chEnd).toInt() - 1;  //* Convert to 0-based
                int loopVal = command.substring(valStart).toInt();
                
                if (ch >= 0 && ch < MAX_CHANNEL_NUM) {
                    channelLoop[ch] = (loopVal == 1);
                    Serial.print("LOOP:CH:");
                    Serial.print(ch + 1);
                    Serial.print(":VALUE:");
                    Serial.println(loopVal);
                } else {
                    Serial.println("ERR:LOOP invalid channel");
                }
            } else {
                Serial.println("ERR:LOOP format");
            }
        }
        else {
            Serial.print("ERR:Unknown command:");
            Serial.println(command);
        }
    }
}

//* Report detailed channel configuration
void reportChannelConfig() {
    Serial.println("CHANNEL_CONFIG:");
    for (int i = 0; i < MAX_CHANNEL_NUM; i++) {
        Serial.print("CH");
        Serial.print(i + 1);
        Serial.print(":pin=");
        Serial.print(channelPins[i]);
        Serial.print(",type=");
        Serial.print(channelTypes[i]);
        Serial.print(",max=");
        Serial.print(getChannelMaxValue(i));
        Serial.print(",bits=");
        uint16_t maxVal = getChannelMaxValue(i);
        if (maxVal == 1) Serial.print("1");
        else if (maxVal == 255) Serial.print("8");
        else if (maxVal == 4095) Serial.print("12");
        Serial.println();
    }
}

//* ---------------------------------------------------------------------
//* PATTERN PARSING
//* ---------------------------------------------------------------------

void parse_pattern(String command) {
    //* Parse PATTERN number
    int patternIndexStart = command.indexOf("PATTERN:") + 8;
    int patternIndexEnd = command.indexOf(';', patternIndexStart);
    int patternNum = command.substring(patternIndexStart, patternIndexEnd).toInt();

    //* Parse CH number (1-based in protocol)
    int chIndexStart = command.indexOf("CH:") + 3;
    int chIndexEnd = command.indexOf(';', chIndexStart);
    int channel = command.substring(chIndexStart, chIndexEnd).toInt() - 1;

    if (channel >= 0 && channel < MAX_CHANNEL_NUM && patternNum >= 0 && patternNum < MAX_PATTERN_NUM) {
        CompressedPattern &p = channelPatterns[channel];

        //* Parse STATUS with channel-aware conversion
        int statusIndexStart = command.indexOf("STATUS:") + 7;
        int statusIndexEnd = command.indexOf(';', statusIndexStart);
        String statusStr = command.substring(statusIndexStart, statusIndexEnd);
        int statusLength = 0;
        parseUInt16Array(statusStr, p.status[patternNum], statusLength, channel);

        //* Parse TIME_MS
        int timeIndexStart = command.indexOf("TIME_MS:") + 8;
        int timeIndexEnd = command.indexOf(';', timeIndexStart);
        String timeStr = command.substring(timeIndexStart, timeIndexEnd);
        int timeLength = 0;
        parseULongArray(timeStr, p.time_ms[patternNum], timeLength);
        
        //* Validate lengths
        if (statusLength != timeLength) {
            Serial.print("ERR:LENGTH_MISMATCH CH");
            Serial.print(channel + 1);
            Serial.print(" STATUS=");
            Serial.print(statusLength);
            Serial.print(" TIME=");
            Serial.println(timeLength);
            p.pattern_length[patternNum] = min(statusLength, timeLength);
        } else {
            p.pattern_length[patternNum] = statusLength;
        }
        
        //* Silently truncate pattern if exceeds PATTERN_LENGTH
        if (p.pattern_length[patternNum] > PATTERN_LENGTH) {
            p.pattern_length[patternNum] = PATTERN_LENGTH;
        }

        //* Parse REPEATS
        int repeatsIndexStart = command.indexOf("REPEATS:") + 8;
        int repeatsIndexEnd = command.indexOf(';', repeatsIndexStart);
        String repeatsStr;
        if (repeatsIndexEnd == -1) {
            repeatsStr = command.substring(repeatsIndexStart);
        } else {
            repeatsStr = command.substring(repeatsIndexStart, repeatsIndexEnd);
        }
        p.repeats[patternNum] = repeatsStr.toInt();

        //* Parse PULSE (if enabled)
#if PULSE_MODE_ENABLE == 1
        int pulseIndexStart = command.indexOf("PULSE:");
        if (pulseIndexStart != -1) {
            pulseIndexStart += 6;
            String pulseStr = command.substring(pulseIndexStart);
            pulseStr.trim();
            
            if (pulseStr.length() == 0) {
                for (int i = 0; i < PATTERN_LENGTH; i++) {
                    p.period[patternNum][i] = 0;
                    p.pulse_width[patternNum][i] = 0;
                }
            } else {
                int index = 0;
                int lastIndex = 0;
                pulseStr += ',';

                while (true) {
                    int commaIndex = pulseStr.indexOf(',', lastIndex);
                    if (commaIndex == -1 || index >= PATTERN_LENGTH) break;
                    
                    String pulseItem = pulseStr.substring(lastIndex, commaIndex);
                    pulseItem.trim();
                    
                    int tIndex = pulseItem.indexOf('T');
                    int pwIndex = pulseItem.indexOf("pw");
                    
                    if (pulseItem.length() == 0 || tIndex == -1 || pwIndex == -1) {
                        p.period[patternNum][index] = 0;
                        p.pulse_width[patternNum][index] = 0;
                    } else {
                        p.period[patternNum][index] = pulseItem.substring(tIndex + 1, pwIndex).toInt();
                        p.pulse_width[patternNum][index] = pulseItem.substring(pwIndex + 2).toInt();
                    }
                    
                    index++;
                    lastIndex = commaIndex + 1;
                }
                
                while (index < PATTERN_LENGTH) {
                    p.period[patternNum][index] = 0;
                    p.pulse_width[patternNum][index] = 0;
                    index++;
                }
            }
        } else {
            for (int i = 0; i < PATTERN_LENGTH; i++) {
                p.period[patternNum][i] = 0;
                p.pulse_width[patternNum][i] = 0;
            }
        }
#endif

        if (patternNum + 1 > p.pattern_num) {
            p.pattern_num = patternNum + 1;
        }

        channelActive[channel] = true;
    } else {
        Serial.print("ERR:INVALID_CHANNEL_OR_PATTERN CH=");
        Serial.print(channel + 1);
        Serial.print(" PATTERN=");
        Serial.println(patternNum);
    }
}

//* Parse array with channel-aware value conversion
void parseUInt16Array(String data, uint16_t arr[], int &actualLength, int ch) {
    int index = 0;
    int lastIndex = 0;
    data.trim();
    data += ',';

    while (true) {
        int commaIndex = data.indexOf(',', lastIndex);
        if (commaIndex == -1 || index >= PATTERN_LENGTH) break;
        
        String valueStr = data.substring(lastIndex, commaIndex);
        valueStr.trim();
        
        //* Use the new validation function (NO SCALING - just validate and warn)
        bool hasError = false;
        uint16_t converted = parseChannelValue(valueStr, ch, hasError);
        
        //* If error, still store 0 and continue
        arr[index++] = converted;
        lastIndex = commaIndex + 1;
    }
    actualLength = index;
}

void parseULongArray(String data, unsigned long arr[], int &actualLength) {
    int index = 0;
    int lastIndex = 0;
    data.trim();
    data += ',';

    while (true) {
        int commaIndex = data.indexOf(',', lastIndex);
        if (commaIndex == -1 || index >= PATTERN_LENGTH) break;
        String value = data.substring(lastIndex, commaIndex);
        arr[index++] = value.toInt();
        lastIndex = commaIndex + 1;
    }
    actualLength = index;
}

//* ---------------------------------------------------------------------
//* RAMP PATTERN PARSING
//* ---------------------------------------------------------------------

#if PWM_RAMP_ENABLE == 1
void parse_ramp_pattern(String command) {
    int patternIndexStart = command.indexOf("PATTERN:") + 8;
    int patternIndexEnd = command.indexOf(';', patternIndexStart);
    int patternNum = command.substring(patternIndexStart, patternIndexEnd).toInt();
    
    int chIndexStart = command.indexOf("CH:") + 3;
    int chIndexEnd = command.indexOf(';', chIndexStart);
    int channel = command.substring(chIndexStart, chIndexEnd).toInt() - 1;
    
    if (channel >= 0 && channel < MAX_CHANNEL_NUM && patternNum >= 0 && patternNum < MAX_PATTERN_NUM) {
        CompressedPattern &p = channelPatterns[channel];
        RampPattern &ramp = p.ramp[patternNum];
        
        uint16_t maxVal = getChannelMaxValue(channel);
        
        int rampIndexStart = command.indexOf("RAMP:") + 5;
        int rampIndexEnd = command.indexOf(';', rampIndexStart);
        String rampStr;
        if (rampIndexEnd == -1) {
            rampStr = command.substring(rampIndexStart);
        } else {
            rampStr = command.substring(rampIndexStart, rampIndexEnd);
        }
        rampStr.trim();
        
        ramp.num_segments = 0;
        ramp.total_duration_ms = 0;
        ramp.active = false;
        
        bool newFormat = (rampStr.charAt(0) == '(');
        int segIndex = 0;
        
        if (newFormat) {
            int pos = 0;
            while (pos < rampStr.length() && segIndex < MAX_RAMP_SEGMENTS) {
                int openParen = rampStr.indexOf('(', pos);
                if (openParen == -1) break;
                
                int closeParen = rampStr.indexOf(')', openParen);
                if (closeParen == -1) break;
                
                String segStr = rampStr.substring(openParen + 1, closeParen);
                segStr.trim();
                
                int colonPos = segStr.indexOf(':');
                if (colonPos == -1) {
                    pos = closeParen + 1;
                    continue;
                }
                
                String modeStr = segStr.substring(0, colonPos);
                modeStr.trim();
                String paramsStr = segStr.substring(colonPos + 1);
                paramsStr.trim();
                
                RampSegment &seg = ramp.segments[segIndex];
                seg.func_name[0] = '\0';
                
                //* F mode (custom function)
                if (modeStr == "F" || modeStr == "5") {
                    seg.easing_mode = RAMP_MODE_FUNC;
                    int firstComma = paramsStr.indexOf(',');
                    if (firstComma != -1) {
                        String funcName = paramsStr.substring(0, firstComma);
                        funcName.trim();
                        funcName.toCharArray(seg.func_name, 16);
                        seg.duration_ms = paramsStr.substring(firstComma + 1).toInt();
                        seg.start_value = 0;
                        seg.end_value = maxVal;
                        seg.t_start = 0.0;
                        seg.t_end = 1.0;
                        ramp.total_duration_ms += seg.duration_ms;
                        segIndex++;
                    }
                    pos = closeParen + 1;
                    continue;
                }
                
                //* Set easing mode
                if (modeStr == "L" || modeStr == "0") {
                    seg.easing_mode = RAMP_MODE_LINEAR;
                } else if (modeStr == "C" || modeStr == "1") {
                    seg.easing_mode = RAMP_MODE_COSINE;
                } else if (modeStr == "I" || modeStr == "2") {
                    seg.easing_mode = RAMP_MODE_EASE_IN;
                } else if (modeStr == "O" || modeStr == "3") {
                    seg.easing_mode = RAMP_MODE_EASE_OUT;
                } else if (modeStr == "X" || modeStr == "4") {
                    seg.easing_mode = RAMP_MODE_CUSTOM;
                } else {
                    seg.easing_mode = RAMP_MODE_LINEAR;
                }
                
                //* Check for t range (after |)
                int pipePos = paramsStr.indexOf('|');
                String numParams;
                if (pipePos != -1) {
                    numParams = paramsStr.substring(0, pipePos);
                    String tRangeStr = paramsStr.substring(pipePos + 1);
                    int tComma = tRangeStr.indexOf(',');
                    if (tComma != -1) {
                        seg.t_start = tRangeStr.substring(0, tComma).toFloat();
                        seg.t_end = tRangeStr.substring(tComma + 1).toFloat();
                    } else {
                        seg.t_start = 0.0;
                        seg.t_end = 1.0;
                    }
                } else {
                    numParams = paramsStr;
                    seg.t_start = (seg.easing_mode == RAMP_MODE_EASE_OUT) ? 1.0 : 0.0;
                    seg.t_end = (seg.easing_mode == RAMP_MODE_EASE_OUT) ? 2.0 : 1.0;
                }
                
                //* Parse start,end,duration
                int c1 = numParams.indexOf(',');
                int c2 = numParams.indexOf(',', c1 + 1);
                
                if (c1 != -1 && c2 != -1) {
                    float startVal = numParams.substring(0, c1).toFloat();
                    float endVal = numParams.substring(c1 + 1, c2).toFloat();
                    seg.duration_ms = numParams.substring(c2 + 1).toInt();
                    
                    //* Convert values to channel resolution
                    seg.start_value = convertToChannelResolution(startVal, channel);
                    seg.end_value = convertToChannelResolution(endVal, channel);
                    
                    ramp.total_duration_ms += seg.duration_ms;
                    segIndex++;
                }
                
                pos = closeParen + 1;
            }
        }
        
        ramp.num_segments = segIndex;
        
        if (ramp.num_segments > 0) {
            ramp.active = true;
            p.time_ms[patternNum][0] = ramp.total_duration_ms;
            p.status[patternNum][0] = ramp.segments[0].start_value;
            p.pattern_length[patternNum] = 1;
        } else {
            Serial.print("ERR:NO_VALID_RAMP_SEGMENTS CH");
            Serial.println(channel + 1);
        }
        
        //* Parse REPEATS
        int repeatsIndexStart = command.indexOf("REPEATS:") + 8;
        if (repeatsIndexStart > 7) {
            int repeatsIndexEnd = command.indexOf(';', repeatsIndexStart);
            String repeatsStr;
            if (repeatsIndexEnd == -1) {
                repeatsStr = command.substring(repeatsIndexStart);
            } else {
                repeatsStr = command.substring(repeatsIndexStart, repeatsIndexEnd);
            }
            p.repeats[patternNum] = repeatsStr.toInt();
        } else {
            p.repeats[patternNum] = 1;
        }
        
        if (patternNum + 1 > p.pattern_num) {
            p.pattern_num = patternNum + 1;
        }
        
        channelActive[channel] = true;
    }
}
#endif

//* ---------------------------------------------------------------------
//* PATTERN INITIALIZATION
//* ---------------------------------------------------------------------

void initializePatterns() {
    unsigned long currentTime = millis();

    for (int ch = 0; ch < MAX_CHANNEL_NUM; ch++) {
        CompressedPattern &p = channelPatterns[ch];

        if (channelActive[ch] && p.pattern_num > 0) {
            patternSequence[ch] = 0;
            patternIndices[ch][patternSequence[ch]] = 0;
            repeatCounters[ch][patternSequence[ch]] = 0;

            uint16_t status = p.status[patternSequence[ch]][0];
            
#if PWM_RAMP_ENABLE == 1
            if (PWM_RAMP_ENABLED && p.ramp[patternSequence[ch]].active) {
                rampStartTime[ch] = currentTime;
                rampCurrentSegment[ch] = 0;
                setChannelOutput(ch, p.ramp[patternSequence[ch]].segments[0].start_value);
            } else
#endif
#if PULSE_MODE_ENABLE == 1
            if (PULSE_MODE_ENABLED) {
                unsigned long period = p.period[patternSequence[ch]][0];
                unsigned long pw = p.pulse_width[patternSequence[ch]][0];
                
                if (status > 0 && period > 0 && pw > 0) {
                    pulseState[ch] = true;
                    setChannelOutput(ch, status);
                    nextPulseTime[ch] = currentTime + pw;
                } else {
                    setChannelOutput(ch, status);
                    pulseState[ch] = false;
                    nextPulseTime[ch] = 0;
                }
            } else
#endif
            {
                setChannelOutput(ch, status);
#if PULSE_MODE_ENABLE == 1
                pulseState[ch] = false;
                nextPulseTime[ch] = 0;
#endif
            }

            nextEventTime[ch] = currentTime + p.time_ms[patternSequence[ch]][0];
        } else {
            channelActive[ch] = false;
            setChannelOutput(ch, 0);
#if PULSE_MODE_ENABLE == 1
            pulseState[ch] = false;
            nextPulseTime[ch] = 0;
#endif
        }
    }
}

//* ---------------------------------------------------------------------
//* PATTERN EXECUTION
//* ---------------------------------------------------------------------

void executePatterns() {
    unsigned long currentTime = millis();
    bool anyChannelActive = false;

    for (int ch = 0; ch < MAX_CHANNEL_NUM; ch++) {
        if (channelActive[ch]) {
            anyChannelActive = true;
            CompressedPattern &p = channelPatterns[ch];
            
            int seq = patternSequence[ch];
            int idx = patternIndices[ch][seq];
            int actualPatternLength = p.pattern_length[seq];
            
#if PWM_RAMP_ENABLE == 1
            if (PWM_RAMP_ENABLED && p.ramp[seq].active) {
                executeRamp(ch);
            }
#endif
            
#if PULSE_MODE_ENABLE == 1
            if (PULSE_MODE_ENABLED) {
                uint16_t currentStatus = p.status[seq][idx];
                unsigned long currentPeriod = p.period[seq][idx];
                unsigned long currentPW = p.pulse_width[seq][idx];
                
#if PWM_RAMP_ENABLE == 1
                bool isRampPattern = p.ramp[seq].active;
#else
                bool isRampPattern = false;
#endif
                if (!isRampPattern && currentStatus > 0 && currentPeriod > 0 && currentPW > 0 && nextPulseTime[ch] > 0) {
                    if (currentTime >= nextPulseTime[ch]) {
                        pulseState[ch] = !pulseState[ch];
                        setChannelOutput(ch, pulseState[ch] ? currentStatus : 0);
                        
                        if (pulseState[ch]) {
                            nextPulseTime[ch] = currentTime + currentPW;
                        } else {
                            unsigned long offTime = currentPeriod - currentPW;
                            if (offTime < 1) offTime = 1;
                            nextPulseTime[ch] = currentTime + offTime;
                        }
                    }
                }
            }
#endif

            if (currentTime >= nextEventTime[ch]) {
                idx++;

                if (idx >= actualPatternLength) {
                    idx = 0;
                    repeatCounters[ch][seq]++;

                    if (repeatCounters[ch][seq] >= p.repeats[seq]) {
                        seq++;
                        if (seq >= p.pattern_num) {
                            //* All patterns completed - check if LOOP is enabled
                            if (channelLoop[ch]) {
                                //* LOOP enabled - restart from pattern 1 (skip wait pattern 0)
                                //* Pattern 0 is the initial wait/countdown, only runs once
                                seq = (p.pattern_num > 1) ? 1 : 0;  //* Start from pattern 1 if exists
                                idx = 0;
                                for (int pi = 0; pi < MAX_PATTERN_NUM; pi++) {
                                    repeatCounters[ch][pi] = 0;
                                    patternIndices[ch][pi] = 0;
                                }
                                patternSequence[ch] = seq;
                                actualPatternLength = p.pattern_length[seq];
                                //* Continue to set up pattern below
                            } else {
                                //* No LOOP - deactivate channel
                                channelActive[ch] = false;
                                setChannelOutput(ch, 0);
#if PULSE_MODE_ENABLE == 1
                                pulseState[ch] = false;
                                nextPulseTime[ch] = 0;
#endif
                                continue;
                            }
                        } else {
                            repeatCounters[ch][seq] = 0;
                            idx = 0;
                            actualPatternLength = p.pattern_length[seq];
                        }
                    }
                }

                patternSequence[ch] = seq;
                patternIndices[ch][seq] = idx;

#if PWM_RAMP_ENABLE == 1
                if (PWM_RAMP_ENABLED && p.ramp[seq].active) {
                    rampStartTime[ch] = currentTime;
                    rampCurrentSegment[ch] = 0;
                    setChannelOutput(ch, p.ramp[seq].segments[0].start_value);
                    nextEventTime[ch] = currentTime + p.ramp[seq].total_duration_ms;
                    continue;
                }
#endif

                uint16_t status = p.status[seq][idx];
                
#if PULSE_MODE_ENABLE == 1
                unsigned long period = p.period[seq][idx];
                unsigned long pw = p.pulse_width[seq][idx];
                
                if (status > 0 && period > 0 && pw > 0) {
                    pulseState[ch] = true;
                    setChannelOutput(ch, status);
                    nextPulseTime[ch] = currentTime + pw;
                } else {
                    setChannelOutput(ch, status);
                    pulseState[ch] = false;
                    nextPulseTime[ch] = 0;
                }
#else
                setChannelOutput(ch, status);
#endif

                nextEventTime[ch] = currentTime + p.time_ms[seq][idx];
            }
        }
    }

    if (!anyChannelActive) {
        allChannelsCompleted = true;
    }
}

//* ---------------------------------------------------------------------
//* RAMP EXECUTION
//* ---------------------------------------------------------------------

#if PWM_RAMP_ENABLE == 1
uint16_t clipValue(float value, int ch) {
    if (value < 0.0) return 0;
    uint16_t maxVal = getChannelMaxValue(ch);
    if (value > maxVal) return maxVal;
    return (uint16_t)value;
}

uint16_t calculateEasedValue(float progress, uint16_t start_val, uint16_t end_val, 
                              byte easing_mode, float t_start, float t_end, int ch) {
    float easedProgress;
    uint16_t maxVal = getChannelMaxValue(ch);
    
    switch (easing_mode) {
        case RAMP_MODE_LINEAR:
            easedProgress = progress;
            break;
            
        case RAMP_MODE_COSINE:
        case RAMP_MODE_EASE_IN:
            {
                float t = progress * 1.0;
                easedProgress = (1.0 - cos(3.14159265 * t)) / 2.0;
            }
            break;
            
        case RAMP_MODE_EASE_OUT:
            {
                float t = 1.0 + progress * 1.0;
                float f_t = (1.0 - cos(3.14159265 * t)) / 2.0;
                easedProgress = 1.0 - f_t;
            }
            break;
            
        case RAMP_MODE_CUSTOM:
            {
                float t = t_start + progress * (t_end - t_start);
                float f_t = (1.0 - cos(3.14159265 * t)) / 2.0;
                return clipValue(maxVal * f_t, ch);
            }
            break;
            
        default:
            easedProgress = progress;
            break;
    }
    
    if (easedProgress < 0.0) easedProgress = 0.0;
    if (easedProgress > 1.0) easedProgress = 1.0;
    
    float valueFloat = (float)start_val + easedProgress * (float)(end_val - start_val);
    return clipValue(valueFloat, ch);
}

void executeRamp(int ch) {
    CompressedPattern &p = channelPatterns[ch];
    int seq = patternSequence[ch];
    
    if (!p.ramp[seq].active) return;
    
    RampPattern &ramp = p.ramp[seq];
    unsigned long currentTime = millis();
    unsigned long totalElapsed = currentTime - rampStartTime[ch];
    
    if (currentTime - lastRampUpdate[ch] < 20) return;
    lastRampUpdate[ch] = currentTime;
    
    unsigned long segmentStartTime = 0;
    int segIdx = 0;
    
    for (int i = 0; i < ramp.num_segments; i++) {
        unsigned long segmentEndTime = segmentStartTime + ramp.segments[i].duration_ms;
        if (totalElapsed < segmentEndTime || i == ramp.num_segments - 1) {
            segIdx = i;
            break;
        }
        segmentStartTime = segmentEndTime;
    }
    
    if (segIdx != rampCurrentSegment[ch]) {
        rampCurrentSegment[ch] = segIdx;
    }
    
    RampSegment &seg = ramp.segments[segIdx];
    
    unsigned long segmentElapsed = totalElapsed - segmentStartTime;
    if (segmentElapsed > seg.duration_ms) {
        segmentElapsed = seg.duration_ms;
    }
    
    float progress = (float)segmentElapsed / (float)seg.duration_ms;
    if (progress > 1.0) progress = 1.0;
    if (progress < 0.0) progress = 0.0;
    
    uint16_t outputValue;
    
    if (seg.easing_mode == RAMP_MODE_FUNC) {
        //* Custom function returns 0-255, scale to channel resolution
        byte funcResult = dispatchCustomFunction(seg.func_name, progress);
        uint16_t maxVal = getChannelMaxValue(ch);
        if (maxVal == RESOLUTION_12BIT) {
            outputValue = (uint16_t)((funcResult / 255.0f) * 4095.0f);
        } else {
            outputValue = funcResult;
        }
    } else {
        outputValue = calculateEasedValue(
            progress,
            seg.start_value,
            seg.end_value,
            seg.easing_mode,
            seg.t_start,
            seg.t_end,
            ch
        );
    }
    
    if (outputValue != currentOutputValue[ch]) {
        setChannelOutput(ch, outputValue);
    }
}
#endif

//* ---------------------------------------------------------------------
//* CALIBRATION FUNCTIONS
//* ---------------------------------------------------------------------

void calibrate_time(String command) {
    String timeStr = command.substring(10);
    unsigned long time = timeStr.toInt();
    unsigned long startTime = millis();
    
    unsigned long targetTime = startTime + time;
    while (millis() < targetTime) {
        delayMicroseconds(100);
    }
    unsigned long duration = millis() - startTime;
    
    Serial.print("calibration_");
    Serial.println(duration);
}

void calibrate_time_v11(String command) {
    String timeStr = command.substring(14);
    unsigned long time = timeStr.toInt();
    unsigned long startTime = millis();
    
    unsigned long targetTime = startTime + time;
    while (millis() < targetTime) {
        delayMicroseconds(100);
    }
    unsigned long duration = millis() - startTime;
    
    Serial.print("calibration_v11_");
    Serial.println(duration);
}

void calibrate_timestamps(String command) {
    int firstUnderscore = command.indexOf('_', 11);
    int secondUnderscore = command.indexOf('_', firstUnderscore + 1);
    
    if (firstUnderscore == -1 || secondUnderscore == -1) {
        Serial.println("ERR:Invalid calibrate_timestamps format");
        return;
    }
    
    String durationStr = command.substring(firstUnderscore + 1, secondUnderscore);
    String samplesStr = command.substring(secondUnderscore + 1);
    
    unsigned long durationSec = durationStr.toInt();
    int numSamples = samplesStr.toInt();
    
    if (durationSec == 0 || numSamples == 0 || numSamples > 100) {
        Serial.println("ERR:Invalid calibration parameters");
        return;
    }
    
    unsigned long durationMs = durationSec * 1000UL;
    unsigned long interval = durationMs / numSamples;
    
    unsigned long startTime = millis();
    
    Serial.print("calib_timestamp_");
    Serial.println(0);
    
    for (int i = 1; i <= numSamples; i++) {
        unsigned long targetTime = startTime + (i * interval);
        
        while (millis() < targetTime) {
            if (targetTime - millis() > 10) {
                delay(5);
            } else {
                delayMicroseconds(100);
            }
        }
        
        unsigned long elapsed = millis() - startTime;
        Serial.print("calib_timestamp_");
        Serial.println(elapsed);
    }
}

//* ---------------------------------------------------------------------
//* MEMORY REPORTING
//* ---------------------------------------------------------------------

#ifdef __arm__
extern "C" char* sbrk(int incr);
int getFreeRAM() {
    char top;
    return &top - reinterpret_cast<char*>(sbrk(0));
}
#else
int getFreeRAM() {
    extern int __heap_start, *__brkval;
    int v;
    return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
}
#endif

void reportMemoryInfo() {
    int freeRAM = getFreeRAM();
    
    Serial.print("MEMORY;FREE:");
    Serial.print(freeRAM);
    
#ifdef ARDUINO_ARCH_SAM
    Serial.print(";TOTAL:98304");
#elif defined(ARDUINO_ARCH_SAMD)
    Serial.print(";TOTAL:32768");
#elif defined(__AVR_ATmega2560__)
    Serial.print(";TOTAL:8192");
#elif defined(__AVR_ATmega328P__)
    Serial.print(";TOTAL:2048");
#else
    Serial.print(";TOTAL:unknown");
#endif
    
    Serial.print(";PULSE_MODE:");
    Serial.print(PULSE_MODE_ENABLED ? "1" : "0");
    Serial.print(";PWM_RAMP:");
    Serial.println(PWM_RAMP_ENABLED ? "1" : "0");
}

//* ---------------------------------------------------------------------
//* CHANNEL MONITOR
//* ---------------------------------------------------------------------

#if CHANNEL_MONITOR_ENABLE == 1
void updateChannelMonitor() {
    if (!monitorEnabled) return;  //* Skip if monitoring disabled
    
    unsigned long currentTime = millis();
    
    if (currentTime - lastMonitorPrintTime >= monitorPrintStep) {
        printChannelValues();
        lastMonitorPrintTime = currentTime;
    }
}

void printChannelValues() {
    Serial.print("$CHMON:");
    for (int ch = 0; ch < MAX_CHANNEL_NUM; ch++) {
        if (ch > 0) Serial.print(",");
        Serial.print("CH");
        Serial.print(ch + 1);
        Serial.print(":");
        
#if PWM_RAMP_ENABLE == 1
        Serial.print(currentOutputValue[ch]);
#else
        Serial.print(channelActive[ch] ? getChannelMaxValue(ch) : 0);
#endif
    }
    Serial.println();
}

void setMonitorPrintStep(unsigned long step_ms) {
    monitorPrintStep = step_ms;
}

void setMonitorEnabled(bool enabled) {
    monitorEnabled = enabled;
}
#else
void updateChannelMonitor() {}
void printChannelValues() {}
void setMonitorPrintStep(unsigned long step_ms) {}
void setMonitorEnabled(bool enabled) {}
#endif
