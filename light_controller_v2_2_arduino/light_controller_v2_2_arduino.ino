const int MAX_CHANNEL_NUM = 3;
const int MAX_PATTERN_NUM = 10;
const int PATTERN_LENGTH = 2;

const int channelPins[MAX_CHANNEL_NUM] = {13,12,11};

//* =====================================================================
//* CUSTOM EASING FUNCTIONS
//* =====================================================================
//* Include custom easing functions for F mode (heartbeat, bounce, etc.)
//* Edit custom_easing.h to add your own functions.
//* See custom_easing.h for documentation on creating custom functions.
//* =====================================================================

#include "custom_easing.h"

//* =====================================================================
//* FUNCTION DISPATCHER (for F mode)
//* =====================================================================
//* Maps function names to implementations. Edit function_dispatcher.h 
//* to add new function mappings. Much easier than editing this file!
//* =====================================================================

#include "function_dispatcher.h"

//* =====================================================================
//* PULSE MODE CONFIGURATION (Compile-Time Only)
//* =====================================================================
//* Set this to 0 before uploading if your protocols NEVER use pulses.
//* This will save ~2.5KB of SRAM by not allocating pulse arrays.
//* 
//* Options:
//*   1 = ENABLE  - Pulse arrays allocated, full pulse support (default)
//*   0 = DISABLE - Pulse arrays NOT allocated, memory optimized
//* 
//* IMPORTANT: You must recompile and upload firmware to change this setting.
//* =====================================================================

#define PULSE_MODE_COMPILE 1  // 0=Disable, 1=Enable

//* =====================================================================
//* PWM/RAMP MODE CONFIGURATION
//* =====================================================================
//* Enable PWM intensity control (0-255) and RAMP gradient transitions.
//* When enabled:
//*   - STATUS values can be 0-255 (not just 0/1)
//*   - RAMP command allows smooth intensity transitions
//*   - Uses analogWrite() instead of digitalWrite()
//* =====================================================================

#define PWM_RAMP_MODE 1        // 0=Disable (binary ON/OFF), 1=Enable (PWM intensity)
#define MAX_RAMP_SEGMENTS  4   // Max segments in a combined RAMP

//* =====================================================================
//* RAMP EASING MODES
//* =====================================================================
//* Linear:     f(t) = t                    (constant speed)
//* Cosine:     f(t) = (1 - cos(t*π)) / 2   (ease-in-out, smooth S-curve)
//* Ease-In:    f(t) = (1 - cos(t*π/2))     (slow start, fast end, 0→π/2)
//* Ease-Out:   f(t) = sin(t*π/2)           (fast start, slow end)
//* Custom:     f(t) = (1 - cos(t_start + t*(t_end-t_start))) / 2
//* =====================================================================

#define RAMP_MODE_LINEAR   0   // Linear interpolation
#define RAMP_MODE_COSINE   1   // Full cosine (ease-in-out, 0→π)
#define RAMP_MODE_EASE_IN  2   // Cosine ease-in only (0→π/2)
#define RAMP_MODE_EASE_OUT 3   // Cosine ease-out only (π/2→π)
#define RAMP_MODE_CUSTOM   4   // Custom t range
#define RAMP_MODE_FUNC     5   // Custom function (F mode)


#if PULSE_MODE_COMPILE == 1
  const bool PULSE_MODE_ENABLED = true;
#else
  const bool PULSE_MODE_ENABLED = false;
#endif

#if PWM_RAMP_MODE == 1
  const bool PWM_RAMP_ENABLED = true;
#else
  const bool PWM_RAMP_ENABLED = false;
#endif

//* RAMP segment structure (for one part of a gradient)
struct RampSegment {
    byte start_pwm;           //* Starting PWM value (0-255)
    byte end_pwm;             //* Ending PWM value (0-255)
    unsigned long duration_ms; //* Segment duration in milliseconds
    byte easing_mode;         //* RAMP_MODE_LINEAR, COSINE, EASE_IN, EASE_OUT, CUSTOM, FUNC
    float t_start;            //* Custom easing: start angle (radians, default 0)
    float t_end;              //* Custom easing: end angle (radians, default PI)
    char func_name[16];       //* F mode: custom function name (max 15 chars + null)
};

//* RAMP pattern structure (supports multiple segments)
struct RampPattern {
    RampSegment segments[MAX_RAMP_SEGMENTS];  //* Array of ramp segments
    int num_segments;                         //* Number of active segments
    unsigned long total_duration_ms;          //* Sum of all segment durations
    bool active;                              //* Whether this pattern is a RAMP
};

struct CompressedPattern {
    byte status[MAX_PATTERN_NUM][PATTERN_LENGTH];  //* Now 0-255 for PWM intensity
    unsigned long time_ms[MAX_PATTERN_NUM][PATTERN_LENGTH];
    
#if PULSE_MODE_COMPILE == 1
    //* Pulse parameters - only compiled if pulse mode enabled
    unsigned long period[MAX_PATTERN_NUM][PATTERN_LENGTH];  //* Pulse period in milliseconds (0 means no pulsing)
    unsigned long pulse_width[MAX_PATTERN_NUM][PATTERN_LENGTH];  //* Pulse width in milliseconds
#endif

#if PWM_RAMP_MODE == 1
    //* RAMP parameters - one per pattern (RAMP patterns have pattern_length=1)
    RampPattern ramp[MAX_PATTERN_NUM];
#endif
    
    int repeats[MAX_PATTERN_NUM];
    int pattern_length[MAX_PATTERN_NUM];  //* Actual pattern length for each pattern (<=PATTERN_LENGTH)
    int pattern_num;  //* Number of patterns saved for this channel
};

CompressedPattern channelPatterns[MAX_CHANNEL_NUM];

bool patternsReceived = false;
bool allChannelsCompleted = false;

//* State variables for pattern execution
int repeatCounters[MAX_CHANNEL_NUM][MAX_PATTERN_NUM] = {{0}};
int patternIndices[MAX_CHANNEL_NUM][MAX_PATTERN_NUM] = {{0}};
int patternSequence[MAX_CHANNEL_NUM] = {0};
unsigned long nextEventTime[MAX_CHANNEL_NUM] = {0};
bool channelActive[MAX_CHANNEL_NUM] = {false};

#if PULSE_MODE_COMPILE >= 1
//* State variables for pulsing - only compiled if pulse mode enabled
bool pulseState[MAX_CHANNEL_NUM] = {false};  //* Current pulse state (HIGH or LOW)
unsigned long nextPulseTime[MAX_CHANNEL_NUM] = {0};  //* Next time to toggle pulse
#endif

#if PWM_RAMP_MODE == 1
//* State variables for RAMP execution (time-based, no steps)
unsigned long rampStartTime[MAX_CHANNEL_NUM] = {0};    //* When current ramp started
int rampCurrentSegment[MAX_CHANNEL_NUM] = {0};         //* Current segment index
byte currentPwmValue[MAX_CHANNEL_NUM] = {0};           //* Current PWM output value
unsigned long lastRampUpdate[MAX_CHANNEL_NUM] = {0};   //* Last PWM update time (for rate limiting)
#endif

//* =====================================================================
//* CHANNEL MONITOR - Real-time PWM value tracking
//* =====================================================================
//* Tracks current PWM values for all channels and outputs them to serial
//* at configurable intervals for monitoring and logging
//* =====================================================================

unsigned long lastMonitorPrintTime = 0;
unsigned long monitorPrintStep = 100;  //* Print interval in milliseconds (default 100ms)

//* Function prototypes
void initChannelMonitor(unsigned long print_step_ms);
void updateChannelMonitor();
void printChannelValues();

void read_serial_command(bool &wait_for_command);
void parse_pattern(String command);
void parse_ramp_pattern(String command);  //* Parse RAMP commands
void initializePatterns();
void executePatterns();
void executeRamp(int ch);  //* Execute RAMP interpolation (time-based)
byte calculateEasedValue(float progress, byte start_pwm, byte end_pwm, byte easing_mode, float t_start, float t_end);  //* Calculate eased PWM value
//* dispatchCustomFunction is now defined in function_dispatcher.h
void setChannelOutput(int ch, byte pwmValue);  //* Set channel output (PWM or digital)
void parseByteArray(String data, byte arr[], int &actualLength);
void parseULongArray(String data, unsigned long arr[], int &actualLength);
void calibrate_time(String command);
void calibrate_time_v11(String command);  //* V1.1 calibration method
void calibrate_timestamps(String command);  //* New v2 calibration method
int getFreeRAM();
void reportMemoryInfo();

void setup() {
    Serial.begin(9600);
    
    // For Arduino Due Native USB port, wait longer for connection
    // This is critical when using the Native USB port instead of Programming port
    unsigned long startTime = millis();
    while (!Serial && (millis() - startTime < 5000)) {
        ; // Wait for serial port to connect, but timeout after 5 seconds
    }
    
    // Additional delay for USB enumeration
    delay(2000);

    // Initialize channel pins as outputs and set them to LOW
    for (int i = 0; i < MAX_CHANNEL_NUM; i++) {
        pinMode(channelPins[i], OUTPUT);
        digitalWrite(channelPins[i], LOW);
        channelPatterns[i].pattern_num = 0;
        
#if PWM_RAMP_MODE == 1
        //* Initialize RAMP state variables
        rampStartTime[i] = 0;
        rampCurrentSegment[i] = 0;
        currentPwmValue[i] = 0;
        lastRampUpdate[i] = 0;
#endif
        
        //* Initialize pattern lengths to 0 and pulse parameters if pulse mode enabled
        for (int j = 0; j < MAX_PATTERN_NUM; j++) {
            channelPatterns[i].pattern_length[j] = 0;  //* Initialize actual pattern length
#if PULSE_MODE_COMPILE >= 1
            if (PULSE_MODE_ENABLED) {
                for (int k = 0; k < PATTERN_LENGTH; k++) {
                    channelPatterns[i].period[j][k] = 0;
                    channelPatterns[i].pulse_width[j][k] = 0;
                }
            }
#endif
#if PWM_RAMP_MODE == 1
            //* Initialize RAMP pattern data
            channelPatterns[i].ramp[j].active = false;
            channelPatterns[i].ramp[j].num_segments = 0;
            channelPatterns[i].ramp[j].total_duration_ms = 0;
            for (int k = 0; k < MAX_RAMP_SEGMENTS; k++) {
                channelPatterns[i].ramp[j].segments[k].start_pwm = 0;
                channelPatterns[i].ramp[j].segments[k].end_pwm = 0;
                channelPatterns[i].ramp[j].segments[k].duration_ms = 0;
                channelPatterns[i].ramp[j].segments[k].easing_mode = RAMP_MODE_LINEAR;
                channelPatterns[i].ramp[j].segments[k].t_start = 0.0;
                channelPatterns[i].ramp[j].segments[k].t_end = 3.14159265;  //* PI
                channelPatterns[i].ramp[j].segments[k].func_name[0] = '\0';  //* Empty function name
            }
#endif
        }
    }

    //* Wait for patterns to be received
    bool wait_for_command = true;
    while (wait_for_command) {
        read_serial_command(wait_for_command);
    }

    //* Initialize patterns after receiving them
    initializePatterns();
}

void loop() {
    if (patternsReceived && !allChannelsCompleted) {
        executePatterns();
        
        //* Update and print channel monitor values
        updateChannelMonitor();
        
        if (allChannelsCompleted) {
            //* All patterns have been executed; terminate the program
            while (true) {
                //* Program halted
            }
        }
    }
}


void read_serial_command(bool &wait_for_command) {
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        command.trim();  //* Remove whitespace and carriage return characters
        if (command.startsWith("PATTERN:")) {
            //* Check if it's a RAMP pattern
#if PWM_RAMP_MODE == 1
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
            //* Respond with greeting and configuration
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
            Serial.println(PWM_RAMP_ENABLED ? "1" : "0");
        }
        else if (command == "GET_MEMORY") {
            //* Report memory information
            reportMemoryInfo();
        }
        else if (command.startsWith("calibrate_timestamps_")) {
            //* V2 calibration: calibrate_timestamps_{duration}_{num_samples}
            //* Example: calibrate_timestamps_60_10
            calibrate_timestamps(command);
        }
        else if (command.startsWith("calibrate_v11_")) {
            //* V1.1 calibration: calibrate_v11_{milliseconds}
            //* Example: calibrate_v11_40000
            //* Same as V1 but explicitly labeled for Python's active-wait implementation
            calibrate_time_v11(command);
        }
        else if (command.startsWith("calibrate_")) { 
            //* V1 calibration: calibrate_{milliseconds}
            //* Example: calibrate_40000
            calibrate_time(command);
        }
        else {
            Serial.print("Invalid command:");
            Serial.println(command);
        }
    }
}

void parse_pattern(String command) {
    //* Expected command format:
    //* "PATTERN:n;CH:n;STATUS:s1,s2;TIME_MS:t1,t2;REPEATS:r" or
    //* "PATTERN:n;CH:n;STATUS:s1,s2;TIME_MS:t1,t2;REPEATS:r;PULSE:T1000pw50,T500pw100"

    //* Parse PATTERN number (Starts from 0)
    int patternIndexStart = command.indexOf("PATTERN:") + 8;
    int patternIndexEnd = command.indexOf(';', patternIndexStart);
    int patternNum = command.substring(patternIndexStart, patternIndexEnd).toInt(); //* Pattern starts from 0, for 0 is the waiting pattern

    //* Parse CH number (Starts from 1)
    int chIndexStart = command.indexOf("CH:") + 3;
    int chIndexEnd = command.indexOf(';', chIndexStart);
    int channel = command.substring(chIndexStart, chIndexEnd).toInt() - 1; //* Zero-based index, CH starts from 1

    if (channel >= 0 && channel < MAX_CHANNEL_NUM && patternNum >= 0 && patternNum < MAX_PATTERN_NUM) {
        CompressedPattern &p = channelPatterns[channel];

        //* Parse STATUS and track actual length
        int statusIndexStart = command.indexOf("STATUS:") + 7;
        int statusIndexEnd = command.indexOf(';', statusIndexStart);
        String statusStr = command.substring(statusIndexStart, statusIndexEnd);
        int statusLength = 0;
        parseByteArray(statusStr, p.status[patternNum], statusLength);

        //* Parse TIME_MS and track actual length
        int timeIndexStart = command.indexOf("TIME_MS:") + 8;
        int timeIndexEnd = command.indexOf(';', timeIndexStart);
        String timeStr = command.substring(timeIndexStart, timeIndexEnd);
        int timeLength = 0;
        parseULongArray(timeStr, p.time_ms[patternNum], timeLength);
        
        //* Validate that STATUS and TIME_MS have the same length
        if (statusLength != timeLength) {
            Serial.print("Error: STATUS and TIME_MS length mismatch in pattern ");
            Serial.print(patternNum);
            Serial.print(" for channel ");
            Serial.print(channel + 1);
            Serial.print(" (STATUS=");
            Serial.print(statusLength);
            Serial.print(", TIME_MS=");
            Serial.print(timeLength);
            Serial.println(")");
            //* Use minimum length to prevent undefined behavior
            p.pattern_length[patternNum] = min(statusLength, timeLength);
        } else {
            //* Store the actual pattern length for this pattern
            p.pattern_length[patternNum] = statusLength;
        }
        
        //* Validate pattern length doesn't exceed PATTERN_LENGTH
        if (p.pattern_length[patternNum] > PATTERN_LENGTH) {
            Serial.print("Warning: Pattern length (");
            Serial.print(p.pattern_length[patternNum]);
            Serial.print(") exceeds PATTERN_LENGTH (");
            Serial.print(PATTERN_LENGTH);
            Serial.println("). Truncated.");
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

        //* Parse PULSE (optional) - only if pulse mode is enabled
#if PULSE_MODE_COMPILE >= 1
        if (PULSE_MODE_ENABLED) {
            int pulseIndexStart = command.indexOf("PULSE:");
            if (pulseIndexStart != -1) {
                pulseIndexStart += 6;
                String pulseStr = command.substring(pulseIndexStart);
                pulseStr.trim();
                
                //* Check if PULSE is empty (e.g., "PULSE:" or "PULSE:\n")
                if (pulseStr.length() == 0) {
                    //* Empty PULSE parameter, initialize to 0 (no pulsing)
                    for (int i = 0; i < PATTERN_LENGTH; i++) {
                        p.period[patternNum][i] = 0;
                        p.pulse_width[patternNum][i] = 0;
                    }
                } else {
                //* Parse pulse string format: T1000pw50,T500pw100
                int index = 0;
                int lastIndex = 0;
                pulseStr += ','; //* Add a comma at the end

                while (true) {
                    int commaIndex = pulseStr.indexOf(',', lastIndex);
                    if (commaIndex == -1 || index >= PATTERN_LENGTH) break;
                    
                    String pulseItem = pulseStr.substring(lastIndex, commaIndex);
                    pulseItem.trim(); //* Remove any whitespace
                    
                    //* Parse T[period]pw[width]
                    int tIndex = pulseItem.indexOf('T');
                    int pwIndex = pulseItem.indexOf("pw");
                    
                    if (pulseItem.length() == 0) {
                        //* Empty item (e.g., trailing comma), default to 0
                        p.period[patternNum][index] = 0;
                        p.pulse_width[patternNum][index] = 0;
                    } else if (tIndex == -1 || pwIndex == -1 || pwIndex <= tIndex) {
                        //* Malformed format - send error message
                        Serial.print("Error: Invalid PULSE format '");
                        Serial.print(pulseItem);
                        Serial.print("' in command. Expected format: T[period]pw[width] (e.g., T1000pw50)");
                        Serial.println();
                        //* Default to 0 but user should fix the command
                        p.period[patternNum][index] = 0;
                        p.pulse_width[patternNum][index] = 0;
                    } else {
                        String periodStr = pulseItem.substring(tIndex + 1, pwIndex);
                        String pwStr = pulseItem.substring(pwIndex + 2);
                        
                        //* Validate that we got some values
                        if (periodStr.length() == 0 || pwStr.length() == 0) {
                            Serial.print("Error: Incomplete PULSE format '");
                            Serial.print(pulseItem);
                            Serial.print("'. Expected: T[period]pw[width] (e.g., T1000pw50)");
                            Serial.println();
                            p.period[patternNum][index] = 0;
                            p.pulse_width[patternNum][index] = 0;
                        } else {
                            p.period[patternNum][index] = periodStr.toInt();
                            p.pulse_width[patternNum][index] = pwStr.toInt();
                        }
                    }
                    
                    index++;
                    lastIndex = commaIndex + 1;
                }
                
                //* Fill remaining indices with 0 if not enough pulse values provided
                while (index < PATTERN_LENGTH) {
                    p.period[patternNum][index] = 0;
                    p.pulse_width[patternNum][index] = 0;
                    index++;
                }
            }
            } else {
                //* No PULSE parameter, initialize to 0
                for (int i = 0; i < PATTERN_LENGTH; i++) {
                    p.period[patternNum][i] = 0;
                    p.pulse_width[patternNum][i] = 0;
                }
            }
        }
#endif
        //* If pulse mode not enabled or not compiled in, skip pulse parsing entirely

        //* Update pattern_num
        if (patternNum + 1 > p.pattern_num) {
            p.pattern_num = patternNum + 1;
        }

        //* Initialize the channel as active
        channelActive[channel] = true;
    }
}

void initializePatterns() {
    unsigned long currentTime = millis();

    for (int ch = 0; ch < MAX_CHANNEL_NUM; ch++) {
        CompressedPattern &p = channelPatterns[ch];

        if (channelActive[ch] && p.pattern_num > 0) {
            //* Initialize indices and counters
            patternSequence[ch] = 0;
            patternIndices[ch][patternSequence[ch]] = 0;
            repeatCounters[ch][patternSequence[ch]] = 0;

            //* Set initial status (now 0-255 for PWM)
            byte status = p.status[patternSequence[ch]][0];
            
#if PWM_RAMP_MODE == 1
            //* Check if this is a RAMP pattern
            if (PWM_RAMP_ENABLED && p.ramp[patternSequence[ch]].active) {
                //* Initialize RAMP execution
                rampStartTime[ch] = currentTime;
                rampCurrentSegment[ch] = 0;
                setChannelOutput(ch, p.ramp[patternSequence[ch]].segments[0].start_pwm);
            } else
#endif
            //* Check if pulsing is needed (only if pulse mode enabled)
#if PULSE_MODE_COMPILE >= 1
            if (PULSE_MODE_ENABLED) {
                unsigned long period = p.period[patternSequence[ch]][0];
                unsigned long pw = p.pulse_width[patternSequence[ch]][0];
                
                if (status > 0 && period > 0 && pw > 0) {
                    //* Start with pulse HIGH (at PWM intensity)
                    pulseState[ch] = true;
#if PWM_RAMP_MODE == 1
                    setChannelOutput(ch, status);  //* Use PWM value
#else
                    digitalWrite(channelPins[ch], HIGH);
#endif
                    //* Schedule next pulse toggle (after pulse width)
                    nextPulseTime[ch] = currentTime + pw;
                } else {
                    //* No pulsing, just set status (PWM or digital)
#if PWM_RAMP_MODE == 1
                    setChannelOutput(ch, status);
#else
                    digitalWrite(channelPins[ch], status ? HIGH : LOW);
#endif
                    pulseState[ch] = false;
                    nextPulseTime[ch] = 0;
                }
            } else
#endif
            {
                //* Pulse mode disabled or not compiled, just set status
#if PWM_RAMP_MODE == 1
                setChannelOutput(ch, status);
#else
                digitalWrite(channelPins[ch], status ? HIGH : LOW);
#endif
#if PULSE_MODE_COMPILE >= 1
                pulseState[ch] = false;
                nextPulseTime[ch] = 0;
#endif
            }

            //* Schedule next event time
            nextEventTime[ch] = currentTime + p.time_ms[patternSequence[ch]][0];
        } else {
            //* Channel is inactive
            channelActive[ch] = false;
            setChannelOutput(ch, 0);  //* Set to OFF
#if PULSE_MODE_COMPILE >= 1
            pulseState[ch] = false;
            nextPulseTime[ch] = 0;
#endif
        }
    }
}

void executePatterns() {
    unsigned long currentTime = millis();

    bool anyChannelActive = false;

    //* Execute patterns for each channel
    for (int ch = 0; ch < MAX_CHANNEL_NUM; ch++) {
        if (channelActive[ch]) {
            anyChannelActive = true;
            CompressedPattern &p = channelPatterns[ch];
            
            int seq = patternSequence[ch];
            int idx = patternIndices[ch][seq];
            int actualPatternLength = p.pattern_length[seq];  //* Use actual pattern length, not PATTERN_LENGTH
            
#if PWM_RAMP_MODE == 1
            //* Handle RAMP execution if active
            if (PWM_RAMP_ENABLED && p.ramp[seq].active) {
                executeRamp(ch);
            }
#endif
            
            //* Handle pulsing if pulse mode enabled
#if PULSE_MODE_COMPILE >= 1
            if (PULSE_MODE_ENABLED) {
                byte currentStatus = p.status[seq][idx];
                unsigned long currentPeriod = p.period[seq][idx];
                unsigned long currentPW = p.pulse_width[seq][idx];
                
                //* Check if we need to toggle pulse (only for non-RAMP patterns)
#if PWM_RAMP_MODE == 1
                bool isRampPattern = p.ramp[seq].active;
#else
                bool isRampPattern = false;
#endif
                if (!isRampPattern && currentStatus > 0 && currentPeriod > 0 && currentPW > 0 && nextPulseTime[ch] > 0) {
                    if (currentTime >= nextPulseTime[ch]) {
                        //* Toggle pulse state
                        pulseState[ch] = !pulseState[ch];
#if PWM_RAMP_MODE == 1
                        setChannelOutput(ch, pulseState[ch] ? currentStatus : 0);
#else
                        digitalWrite(channelPins[ch], pulseState[ch] ? HIGH : LOW);
#endif
                        
                        //* Calculate next pulse toggle time
                        if (pulseState[ch]) {
                            //* Just turned ON, schedule turn OFF after pulse width
                            nextPulseTime[ch] = currentTime + currentPW;
                        } else {
                            //* Just turned OFF, schedule turn ON after off-time
                            //* Off time = period - pulse_width
                            unsigned long offTime = currentPeriod - currentPW;
                            if (offTime < 1) offTime = 1; //* Minimum 1ms off time
                            nextPulseTime[ch] = currentTime + offTime;
                        }
                    }
                }
            }
#endif

            //* Check if it's time to move to next pattern event
            if (currentTime >= nextEventTime[ch]) { //* Time to execute the next event
                //* Move to the next index in the current pattern
                idx++;

                //* Use actual pattern length instead of PATTERN_LENGTH constant
                if (idx >= actualPatternLength) {
                    idx = 0;
                    repeatCounters[ch][seq]++;

                    if (repeatCounters[ch][seq] >= p.repeats[seq]) {
                        //* Move to the next pattern
                        seq++;
                        if (seq >= p.pattern_num) {
                            //* No more patterns, deactivate channel
                            channelActive[ch] = false;
                            setChannelOutput(ch, 0);  //* Set to OFF
#if PULSE_MODE_COMPILE >= 1
                            pulseState[ch] = false;
                            nextPulseTime[ch] = 0;
#endif
                            continue;
                        } else {
                            //* Reset counters for the new pattern
                            repeatCounters[ch][seq] = 0;
                            idx = 0;
                            actualPatternLength = p.pattern_length[seq];  //* Update for new pattern
                        }
                    }
                }

                //* Update indices
                patternSequence[ch] = seq;
                patternIndices[ch][seq] = idx;

#if PWM_RAMP_MODE == 1
                //* Check if new pattern is a RAMP
                if (PWM_RAMP_ENABLED && p.ramp[seq].active) {
                    //* Initialize new RAMP execution
                    rampStartTime[ch] = currentTime;
                    rampCurrentSegment[ch] = 0;
                    setChannelOutput(ch, p.ramp[seq].segments[0].start_pwm);
                    //* Schedule next event time (end of ramp)
                    nextEventTime[ch] = currentTime + p.ramp[seq].total_duration_ms;
                    continue;  //* Skip normal status handling
                }
#endif

                //* Set the new status (now supports 0-255 PWM values)
                byte status = p.status[seq][idx];
                
#if PULSE_MODE_COMPILE >= 1
                unsigned long period = p.period[seq][idx];
                unsigned long pw = p.pulse_width[seq][idx];
                
                //* Check if new status requires pulsing
                if (status > 0 && period > 0 && pw > 0) {
                    //* Start pulsing: begin with HIGH (at PWM intensity)
                    pulseState[ch] = true;
#if PWM_RAMP_MODE == 1
                    setChannelOutput(ch, status);
#else
                    digitalWrite(channelPins[ch], HIGH);
#endif
                    //* Schedule next pulse toggle
                    nextPulseTime[ch] = currentTime + pw;
                } else {
                    //* No pulsing, just set status
#if PWM_RAMP_MODE == 1
                    setChannelOutput(ch, status);
#else
                    digitalWrite(channelPins[ch], status ? HIGH : LOW);
#endif
                    pulseState[ch] = false;
                    nextPulseTime[ch] = 0;
                }
#else
                //* Pulse mode not compiled, just set status
#if PWM_RAMP_MODE == 1
                setChannelOutput(ch, status);
#else
                digitalWrite(channelPins[ch], status ? HIGH : LOW);
#endif
#endif

                //* Schedule the next event time
                nextEventTime[ch] = currentTime + p.time_ms[seq][idx];
            }
        }
    }

    if (!anyChannelActive) {
        //* All channels have completed their patterns
        allChannelsCompleted = true;
    }
}

void parseByteArray(String data, byte arr[], int &actualLength) {
    int index = 0;
    int lastIndex = 0;
    data.trim();
    data += ','; //* Add a comma at the end

    while (true) {
        int commaIndex = data.indexOf(',', lastIndex);
        if (commaIndex == -1 || index >= PATTERN_LENGTH) break;
        String value = data.substring(lastIndex, commaIndex);
        arr[index++] = (byte)value.toInt();
        lastIndex = commaIndex + 1;
    }
    actualLength = index;  //* Store actual number of elements parsed
}

void parseULongArray(String data, unsigned long arr[], int &actualLength) {
    int index = 0;
    int lastIndex = 0;
    data.trim();
    data += ','; //* Add a comma at the end

    while (true) {
        int commaIndex = data.indexOf(',', lastIndex);
        if (commaIndex == -1 || index >= PATTERN_LENGTH) break;
        String value = data.substring(lastIndex, commaIndex);
        arr[index++] = value.toInt();
        lastIndex = commaIndex + 1;
    }
    actualLength = index;  //* Store actual number of elements parsed
}

//* =====================================================================
//* PWM AND RAMP FUNCTIONS
//* =====================================================================

//* Clip PWM value to valid range [0, 255]
//* Use this for ALL custom functions to ensure safe output
byte clipPWM(float value) {
    if (value < 0.0) return 0;
    if (value > 255.0) return 255;
    return (byte)value;
}

void setChannelOutput(int ch, byte pwmValue) {
    //* Set channel output - uses analogWrite for PWM mode, digitalWrite for binary
#if PWM_RAMP_MODE == 1
    if (PWM_RAMP_ENABLED) {
        analogWrite(channelPins[ch], pwmValue);
        currentPwmValue[ch] = pwmValue;
    } else {
        digitalWrite(channelPins[ch], pwmValue > 127 ? HIGH : LOW);
    }
#else
    digitalWrite(channelPins[ch], pwmValue > 127 ? HIGH : LOW);
#endif
}

#if PWM_RAMP_MODE == 1

//* =====================================================================
//* EASING CALCULATION FUNCTION
//* =====================================================================
//* Universal cosine-based easing using f(t) = (1 - cos(π*t)) / 2
//* where t is mapped to a selectable range [t_start, t_end] within [0, 2]
//*
//* The full cosine period t ∈ [0, 2] produces:
//*   t=0: f(0) = (1 - cos(0)) / 2 = 0
//*   t=1: f(1) = (1 - cos(π)) / 2 = 1  (peak)
//*   t=2: f(2) = (1 - cos(2π)) / 2 = 0
//*
//* t range selections:
//*   [0, 2]: Full ease-in-out cycle (0 → 1 → 0)
//*   [0, 1]: Ease-in only (0 → 1), slow start, fast end
//*   [1, 2]: Ease-out only (1 → 0), fast start, slow end
//*   [0, 0.5]: Partial ease-in (0 → 0.5), very slow start
//*   [0.5, 1]: Partial ease-in (0.5 → 1), accelerating
//*   [1, 1.5]: Partial ease-out (1 → 0.5), decelerating
//*   [1.5, 2]: Partial ease-out (0.5 → 0), very slow end
//*
//* progress: 0.0 to 1.0 (elapsed proportion of segment duration)
//* Returns: PWM value interpolated between start_pwm and end_pwm

byte calculateEasedValue(float progress, byte start_pwm, byte end_pwm, byte easing_mode, float t_start, float t_end) {
    float easedProgress;
    
    switch (easing_mode) {
        case RAMP_MODE_LINEAR:
            //* L mode: f(t') = t' (linear, no easing)
            easedProgress = progress;
            break;
            
        case RAMP_MODE_COSINE:
            //* C mode: t ∈ [0, 1] → ease-in (slow start, fast end)
            //* f(t) = (1 - cos(π * t)) / 2, maps progress to [0, 1]
            {
                float t = progress * 1.0;  //* t_start=0, t_end=1
                easedProgress = (1.0 - cos(3.14159265 * t)) / 2.0;
            }
            break;
            
        case RAMP_MODE_EASE_IN:
            //* I mode: t ∈ [0, 1] → ease-in (identical to C for 0→1 transition)
            //* Slow start, fast end
            {
                float t = progress * 1.0;
                easedProgress = (1.0 - cos(3.14159265 * t)) / 2.0;
            }
            break;
            
        case RAMP_MODE_EASE_OUT:
            //* O mode: t ∈ [1, 2] → ease-out (fast start, slow end)
            //* Maps progress [0,1] to t [1,2], output goes 1→0, then we invert
            {
                float t = 1.0 + progress * 1.0;  //* t goes from 1 to 2
                float f_t = (1.0 - cos(3.14159265 * t)) / 2.0;  //* goes 1→0
                easedProgress = 1.0 - f_t;  //* Invert so we get 0→1 with ease-out shape
            }
            break;
            
        case RAMP_MODE_CUSTOM:
            //* X mode: Raw f(t) * 255 - NO SCALING
            //* Maps progress [0,1] to t [t_start, t_end], returns 255 * f(t)
            //* This means start_pwm and end_pwm are IGNORED for X mode!
            //* 
            //* Examples:
            //*   t: 0→0.5   → PWM: 0→127.5 (ascending, ease-in shape)
            //*   t: 0.5→1   → PWM: 127.5→255 (ascending, ease-out shape)
            //*   t: 1→1.5   → PWM: 255→127.5 (DESCENDING!)
            //*   t: 1.5→2   → PWM: 127.5→0 (DESCENDING!)
            //*   t: 0→2     → PWM: 0→255→0 (full breathing cycle)
            {
                float t = t_start + progress * (t_end - t_start);
                float f_t = (1.0 - cos(3.14159265 * t)) / 2.0;
                return clipPWM(255.0 * f_t);  //* Direct return, ignore start/end PWM
            }
            break;
            
        default:
            easedProgress = progress;
            break;
    }
    
    //* Clamp progress to 0-1
    if (easedProgress < 0.0) easedProgress = 0.0;
    if (easedProgress > 1.0) easedProgress = 1.0;
    
    //* Calculate final PWM value and clip to [0, 255]
    float pwmFloat = (float)start_pwm + easedProgress * (float)(end_pwm - start_pwm);
    
    return clipPWM(pwmFloat);
}

void parse_ramp_pattern(String command) {
    //* Parse RAMP command format (supports multiple segments):
    //* 
    //* STANDARD MODES - format: (<mode>:<start>,<end>,<duration>)
    //*   L = Linear (constant speed)
    //*   C = Cosine (smooth S-curve, ease-in-out)
    //*   I = Ease-In (slow start, fast end)
    //*   O = Ease-Out (fast start, slow end)
    //*   X = Custom t range (specify t_start,t_end after |)
    //*
    //* F MODE (Custom Functions) - format: (F:<func_name>,<duration>)
    //*   Uses custom functions from custom_easing.h
    //*   Only 2 parameters: function name and duration
    //*   No start/end PWM - function determines the full curve
    //*
    //* Examples:
    //*   PATTERN:1;CH:1;RAMP:(L:0,255,10000);REPEATS:1
    //*   PATTERN:1;CH:1;RAMP:(C:0,255,5000),(C:255,0,5000);REPEATS:3
    //*   PATTERN:1;CH:1;RAMP:(X:0,255,10000|0,1);REPEATS:1
    //*   PATTERN:1;CH:1;RAMP:(F:heartbeat,2000);REPEATS:10
    //*   PATTERN:1;CH:1;RAMP:(F:sine_wave,5000),(F:bounce,3000);REPEATS:5
    //*
    //* Legacy format (backward compatible, steps parameter ignored):
    //*   PATTERN:1;CH:1;RAMP:0,255,10000,100,L;REPEATS:1
    
    //* Parse PATTERN number
    int patternIndexStart = command.indexOf("PATTERN:") + 8;
    int patternIndexEnd = command.indexOf(';', patternIndexStart);
    int patternNum = command.substring(patternIndexStart, patternIndexEnd).toInt();
    
    //* Parse CH number
    int chIndexStart = command.indexOf("CH:") + 3;
    int chIndexEnd = command.indexOf(';', chIndexStart);
    int channel = command.substring(chIndexStart, chIndexEnd).toInt() - 1;
    
    if (channel >= 0 && channel < MAX_CHANNEL_NUM && patternNum >= 0 && patternNum < MAX_PATTERN_NUM) {
        CompressedPattern &p = channelPatterns[channel];
        RampPattern &ramp = p.ramp[patternNum];
        
        //* Parse RAMP parameters
        int rampIndexStart = command.indexOf("RAMP:") + 5;
        int rampIndexEnd = command.indexOf(';', rampIndexStart);
        String rampStr;
        if (rampIndexEnd == -1) {
            rampStr = command.substring(rampIndexStart);
        } else {
            rampStr = command.substring(rampIndexStart, rampIndexEnd);
        }
        rampStr.trim();
        
        //* Initialize ramp
        ramp.num_segments = 0;
        ramp.total_duration_ms = 0;
        ramp.active = false;
        
        //* Check if new format (starts with parenthesis)
        bool newFormat = (rampStr.charAt(0) == '(');
        
        int segIndex = 0;
        
        if (newFormat) {
            //* New format: (L:0,255,1000),(X:0,255,10000|1,2)
            int pos = 0;
            while (pos < rampStr.length() && segIndex < MAX_RAMP_SEGMENTS) {
                //* Find opening parenthesis
                int openParen = rampStr.indexOf('(', pos);
                if (openParen == -1) break;
                
                //* Find closing parenthesis
                int closeParen = rampStr.indexOf(')', openParen);
                if (closeParen == -1) break;
                
                //* Extract segment content between parentheses
                String segStr = rampStr.substring(openParen + 1, closeParen);
                segStr.trim();
                
                //* Parse mode (first character before colon)
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
                seg.func_name[0] = '\0';  //* Clear function name by default
                
                //* Set easing mode - check for F mode (custom function) first
                if (modeStr == "F" || modeStr == "5") {
                    seg.easing_mode = RAMP_MODE_FUNC;
                    //* F mode format: F:func_name,duration_ms
                    int firstComma = paramsStr.indexOf(',');
                    if (firstComma != -1) {
                        String funcName = paramsStr.substring(0, firstComma);
                        funcName.trim();
                        //* Copy function name (max 15 chars)
                        funcName.toCharArray(seg.func_name, 16);
                        seg.duration_ms = paramsStr.substring(firstComma + 1).toInt();
                        seg.start_pwm = 0;    //* Not used in F mode
                        seg.end_pwm = 255;    //* Not used in F mode
                        seg.t_start = 0.0;
                        seg.t_end = 1.0;
                        ramp.total_duration_ms += seg.duration_ms;
                        segIndex++;
                    }
                    pos = closeParen + 1;
                    continue;
                } else if (modeStr == "L" || modeStr == "0") {
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
                    //* Parse t_start,t_end
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
                    //* Default t range based on mode
                    if (seg.easing_mode == RAMP_MODE_EASE_OUT) {
                        seg.t_start = 1.0;
                        seg.t_end = 2.0;
                    } else {
                        seg.t_start = 0.0;
                        seg.t_end = 1.0;
                    }
                }
                
                //* Parse start,end,duration (steps are no longer used - time-based interpolation)
                int c1 = numParams.indexOf(',');
                int c2 = numParams.indexOf(',', c1 + 1);
                
                if (c1 != -1 && c2 != -1) {
                    seg.start_pwm = numParams.substring(0, c1).toInt();
                    seg.end_pwm = numParams.substring(c1 + 1, c2).toInt();
                    seg.duration_ms = numParams.substring(c2 + 1).toInt();
                    //* Ignore any 4th parameter (steps) for backward compatibility
                    
                    ramp.total_duration_ms += seg.duration_ms;
                    segIndex++;
                }
                
                pos = closeParen + 1;
            }
        } else {
            //* Legacy format: start,end,duration,steps,mode or start,end,duration,steps,mode|t_start,t_end
            //* Note: steps parameter is parsed for compatibility but ignored (time-based interpolation)
            int segStart = 0;
            int segEnd = 0;
            
            while (segIndex < MAX_RAMP_SEGMENTS) {
                //* Find segment separator (comma between segments, but not within)
                //* Legacy uses | for segment separation
                segEnd = rampStr.indexOf('|', segStart);
                
                //* Check if this | is for t_range or segment separator
                //* If there's a comma after the |, it might be t_range
                bool isTRange = false;
                if (segEnd != -1) {
                    int nextComma = rampStr.indexOf(',', segEnd);
                    int nextPipe = rampStr.indexOf('|', segEnd + 1);
                    if (nextComma != -1 && (nextPipe == -1 || nextComma < nextPipe)) {
                        //* This | is followed by comma before next |, likely t_range
                        //* Check if it looks like mode,t_start,t_end or just t_start,t_end
                        String afterPipe = rampStr.substring(segEnd + 1, nextPipe != -1 ? nextPipe : rampStr.length());
                        if (afterPipe.length() < 10) {  //* t_range is short
                            isTRange = true;
                            segEnd = nextPipe;  //* Move to actual segment separator
                        }
                    }
                }
                
                String segStr;
                if (segEnd == -1) {
                    segStr = rampStr.substring(segStart);
                } else {
                    segStr = rampStr.substring(segStart, segEnd);
                }
                segStr.trim();
                
                if (segStr.length() == 0) break;
                
                //* Parse segment: start,end,duration,steps[,mode[,t_start,t_end]] or with |t_start,t_end
                RampSegment &seg = ramp.segments[segIndex];
                seg.func_name[0] = '\0';  //* Clear function name
                
                //* Check for t_range with |
                int pipeInSeg = segStr.indexOf('|');
                String mainParams;
                if (pipeInSeg != -1) {
                    mainParams = segStr.substring(0, pipeInSeg);
                    String tRangeStr = segStr.substring(pipeInSeg + 1);
                    int tComma = tRangeStr.indexOf(',');
                    if (tComma != -1) {
                        seg.t_start = tRangeStr.substring(0, tComma).toFloat();
                        seg.t_end = tRangeStr.substring(tComma + 1).toFloat();
                    }
                } else {
                    mainParams = segStr;
                }
                
                int c1 = mainParams.indexOf(',');
                int c2 = mainParams.indexOf(',', c1 + 1);
                int c3 = mainParams.indexOf(',', c2 + 1);
                int c4 = mainParams.indexOf(',', c3 + 1);
                
                if (c1 == -1 || c2 == -1 || c3 == -1) {
                    Serial.print("Error: Invalid RAMP segment format: ");
                    Serial.println(segStr);
                    break;
                }
                
                seg.start_pwm = mainParams.substring(0, c1).toInt();
                seg.end_pwm = mainParams.substring(c1 + 1, c2).toInt();
                seg.duration_ms = mainParams.substring(c2 + 1, c3).toInt();
                //* Parse but ignore steps (4th param) - kept for backward compatibility
                
                if (c4 == -1) {
                    //* Legacy: start,end,duration,steps (no mode)
                    seg.easing_mode = RAMP_MODE_LINEAR;
                    if (pipeInSeg == -1) {
                        seg.t_start = 0.0;
                        seg.t_end = 1.0;
                    }
                } else {
                    //* Legacy: start,end,duration,steps,mode
                    String modeStr = mainParams.substring(c4 + 1);
                    
                    //* Check for additional t_range in comma format
                    int c5 = modeStr.indexOf(',');
                    if (c5 != -1) {
                        String actualMode = modeStr.substring(0, c5);
                        actualMode.trim();
                        modeStr = actualMode;
                        
                        String tParams = mainParams.substring(c4 + 1 + c5 + 1);
                        int tComma = tParams.indexOf(',');
                        if (tComma != -1 && pipeInSeg == -1) {
                            seg.t_start = tParams.substring(0, tComma).toFloat();
                            seg.t_end = tParams.substring(tComma + 1).toFloat();
                        }
                    }
                    
                    modeStr.trim();
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
                    
                    if (pipeInSeg == -1 && c5 == -1) {
                        if (seg.easing_mode == RAMP_MODE_EASE_OUT) {
                            seg.t_start = 1.0;
                            seg.t_end = 2.0;
                        } else {
                            seg.t_start = 0.0;
                            seg.t_end = 1.0;
                        }
                    }
                }
                
                ramp.total_duration_ms += seg.duration_ms;
                segIndex++;
                
                if (segEnd == -1) break;
                segStart = segEnd + 1;
            }
        }
        
        ramp.num_segments = segIndex;
        
        if (ramp.num_segments > 0) {
            ramp.active = true;
            
            //* Store total duration in time_ms for event scheduling
            p.time_ms[patternNum][0] = ramp.total_duration_ms;
            p.status[patternNum][0] = ramp.segments[0].start_pwm;
            p.pattern_length[patternNum] = 1;
        } else {
            Serial.print("Error: No valid segments in RAMP command: ");
            Serial.println(command);
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
        
        //* Update pattern_num
        if (patternNum + 1 > p.pattern_num) {
            p.pattern_num = patternNum + 1;
        }
        
        //* Initialize channel as active
        channelActive[channel] = true;
    }
}

void executeRamp(int ch) {
    //* Execute RAMP interpolation for a channel (multi-segment support)
    //* Called during executePatterns when a RAMP pattern is active
    
    CompressedPattern &p = channelPatterns[ch];
    int seq = patternSequence[ch];
    
    if (!p.ramp[seq].active) return;
    
    RampPattern &ramp = p.ramp[seq];
    unsigned long currentTime = millis();
    unsigned long totalElapsed = currentTime - rampStartTime[ch];
    
    //* Rate-limit updates to ~50Hz (20ms minimum between updates)
    //* This reduces CPU load while maintaining smooth transitions
    if (currentTime - lastRampUpdate[ch] < 20) return;
    lastRampUpdate[ch] = currentTime;
    
    //* Find which segment we're in
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
    
    //* Check if segment changed
    if (segIdx != rampCurrentSegment[ch]) {
        rampCurrentSegment[ch] = segIdx;
    }
    
    RampSegment &seg = ramp.segments[segIdx];
    
    //* Calculate elapsed time within current segment
    unsigned long segmentElapsed = totalElapsed - segmentStartTime;
    if (segmentElapsed > seg.duration_ms) {
        segmentElapsed = seg.duration_ms;
    }
    
    //* Calculate progress (0.0 to 1.0) using direct time-based interpolation
    float progress = (float)segmentElapsed / (float)seg.duration_ms;
    if (progress > 1.0) progress = 1.0;
    if (progress < 0.0) progress = 0.0;
    
    byte pwmValue;
    
    //* Handle F mode (custom function) separately
    if (seg.easing_mode == RAMP_MODE_FUNC) {
        pwmValue = dispatchCustomFunction(seg.func_name, progress);
    } else {
        //* Calculate eased PWM value for L, C, I, O, X modes
        pwmValue = calculateEasedValue(
            progress,
            seg.start_pwm,
            seg.end_pwm,
            seg.easing_mode,
            seg.t_start,
            seg.t_end
        );
    }
    
    //* Only update hardware if PWM value changed
    if (pwmValue != currentPwmValue[ch]) {
        setChannelOutput(ch, pwmValue);
    }
}

//* =====================================================================
//* F MODE CUSTOM FUNCTION DISPATCHER
//* =====================================================================
//* The dispatchCustomFunction() is now defined in function_dispatcher.h
//* This makes it easier to add new custom functions without editing this file.
//*
//* TO ADD A NEW CUSTOM FUNCTION:
//* 1. Define your function in custom_easing.h
//* 2. Add the mapping in function_dispatcher.h FUNCTION_REGISTRY
//* 3. Recompile and upload
//*
//* Or simply edit 'myfunc' in custom_easing.h for quick experiments!
//* =====================================================================
#endif

//* =====================================================================
//* CALIBRATION FUNCTIONS
//* =====================================================================

void calibrate_time(String command) {
    //* Original v1 calibration method
    //* Kept for backward compatibility
    String timeStr = command.substring(10);
    unsigned long time = timeStr.toInt();
    unsigned long startTime = millis();
    unsigned long duration = 0;
    
    //* Improved: Use non-blocking wait instead of tight loop
    unsigned long targetTime = startTime + time;
    while (millis() < targetTime) {
        delayMicroseconds(100);  //* Prevents CPU-intensive tight loop
    }
    duration = millis() - startTime;
    
    Serial.print("calibration_");
    Serial.println(duration);
}

void calibrate_time_v11(String command) {
    //* V1.1 calibration method (active-wait variant)
    //* Same Arduino implementation as V1, but distinct command for Python's active polling
    //* Format: calibrate_v11_{milliseconds}
    //* Example: calibrate_v11_40000
    //*
    //* Arduino behavior is identical to V1 (waits then responds)
    //* Python difference: Uses active serial polling instead of dead sleep
    //* This gives more precise timing of when Arduino's response arrives
    String timeStr = command.substring(14);  //* Skip "calibrate_v11_"
    unsigned long time = timeStr.toInt();
    unsigned long startTime = millis();
    unsigned long duration = 0;
    
    //* Use non-blocking wait
    unsigned long targetTime = startTime + time;
    while (millis() < targetTime) {
        delayMicroseconds(100);  //* Prevents CPU-intensive tight loop
    }
    duration = millis() - startTime;
    
    //* Send response with v11 prefix for clarity
    Serial.print("calibration_v11_");
    Serial.println(duration);
}

void calibrate_timestamps(String command) {
    //* New v2 calibration method using multi-timestamp approach
    //* Format: calibrate_timestamps_{duration_sec}_{num_samples}
    //* Example: calibrate_timestamps_60_10
    //*
    //* This method is more accurate and faster than v1:
    //* - Single calibration run with multiple data points
    //* - Better statistical confidence through linear regression
    //* - Removes per-message serial overhead
    //* - Non-blocking implementation
    
    // Parse command: "calibrate_timestamps_{duration}_{num_samples}"
    int firstUnderscore = command.indexOf('_', 11);  //* After "calibrate_t"
    int secondUnderscore = command.indexOf('_', firstUnderscore + 1);
    
    if (firstUnderscore == -1 || secondUnderscore == -1) {
        Serial.println("ERROR: Invalid calibrate_timestamps format");
        return;
    }
    
    // Extract duration (in seconds) and number of samples
    String durationStr = command.substring(firstUnderscore + 1, secondUnderscore);
    String samplesStr = command.substring(secondUnderscore + 1);
    
    unsigned long durationSec = durationStr.toInt();
    int numSamples = samplesStr.toInt();
    
    // Validate parameters
    if (durationSec == 0 || numSamples == 0 || numSamples > 100) {
        Serial.println("ERROR: Invalid calibration parameters");
        return;
    }
    
    // Convert duration to milliseconds
    unsigned long durationMs = durationSec * 1000UL;
    unsigned long interval = durationMs / numSamples;
    
    unsigned long startTime = millis();
    
    // Send initial timestamp (t=0)
    Serial.print("calib_timestamp_");
    Serial.println(0);
    
    // Send timestamps at intervals
    for (int i = 1; i <= numSamples; i++) {
        unsigned long targetTime = startTime + (i * interval);
        
        // Non-blocking wait using millis()
        while (millis() < targetTime) {
            //* Small delay to avoid tight loop but maintain accuracy
            //* Using delayMicroseconds instead of delay for better precision
            if (targetTime - millis() > 10) {
                delay(5);  //* Long wait: use delay()
            } else {
                delayMicroseconds(100);  //* Near target: use microsecond precision
            }
        }
        
        // Calculate and send elapsed time
        unsigned long elapsed = millis() - startTime;
        Serial.print("calib_timestamp_");
        Serial.println(elapsed);
    }
}

//* =====================================================================
//* MEMORY REPORTING FUNCTIONS
//* =====================================================================

#ifdef __arm__
// For ARM-based Arduino (Due, Zero, etc.)
extern "C" char* sbrk(int incr);

int getFreeRAM() {
    char top;
    return &top - reinterpret_cast<char*>(sbrk(0));
}

#else
// For AVR-based Arduino (Uno, Mega, etc.)
int getFreeRAM() {
    extern int __heap_start, *__brkval;
    int v;
    return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
}
#endif

void reportMemoryInfo() {
    //* Report current memory usage
    int freeRAM = getFreeRAM();
    
    Serial.print("MEMORY;FREE:");
    Serial.print(freeRAM);
    
#ifdef ARDUINO_ARCH_SAM
    // Arduino Due has 96KB SRAM (98304 bytes)
    Serial.print(";TOTAL:98304");
#elif defined(ARDUINO_ARCH_SAMD)
    // Arduino Zero has 32KB SRAM
    Serial.print(";TOTAL:32768");
#elif defined(__AVR_ATmega2560__)
    // Arduino Mega has 8KB SRAM
    Serial.print(";TOTAL:8192");
#elif defined(__AVR_ATmega328P__)
    // Arduino Uno has 2KB SRAM
    Serial.print(";TOTAL:2048");
#else
    Serial.print(";TOTAL:unknown");
#endif
    
    Serial.print(";PULSE_MODE:");
#if PULSE_MODE_COMPILE == 2
    Serial.print(PULSE_MODE_ENABLED ? "1" : "0");
    Serial.print(";PULSE_COMPILE:dynamic");
#elif PULSE_MODE_COMPILE == 1
    Serial.print("1");
    Serial.print(";PULSE_COMPILE:always");
#else
    Serial.print("0");
    Serial.print(";PULSE_COMPILE:never");
#endif
    
    Serial.println();
}

//* =====================================================================
//* CHANNEL MONITOR FUNCTIONS - Real-time PWM tracking
//* =====================================================================

/**
 * Initialize the channel monitor with specified print interval
 * @param print_step_ms: Interval in milliseconds between serial prints (default 100)
 */
void initChannelMonitor(unsigned long print_step_ms) {
    monitorPrintStep = print_step_ms;
    lastMonitorPrintTime = millis();
}

/**
 * Update and print channel values if interval has elapsed
 * Call this function regularly in the main loop
 */
void updateChannelMonitor() {
    unsigned long currentTime = millis();
    
    if (currentTime - lastMonitorPrintTime >= monitorPrintStep) {
        printChannelValues();
        lastMonitorPrintTime = currentTime;
    }
}

/**
 * Print current PWM values for all channels to serial
 * Format: $CHMON:CH1:pwm1,CH2:pwm2,CH3:pwm3,CH4:pwm4\n
 * Can be parsed by serial monitor tool for live plotting
 */
void printChannelValues() {
    Serial.print("$CHMON:");
    for (int ch = 0; ch < MAX_CHANNEL_NUM; ch++) {
        if (ch > 0) Serial.print(",");
        Serial.print("CH");
        Serial.print(ch + 1);
        Serial.print(":");
        
#if PWM_RAMP_MODE == 1
        //* Print current PWM value if PWM mode enabled
        Serial.print(currentPwmValue[ch]);
#else
        //* Print 0 or 255 for binary mode
        Serial.print(channelActive[ch] ? 255 : 0);
#endif
    }
    Serial.println();
}

/**
 * Set the channel monitor print interval
 * @param print_step_ms: New interval in milliseconds
 */
void setMonitorPrintStep(unsigned long print_step_ms) {
    monitorPrintStep = print_step_ms;
}

