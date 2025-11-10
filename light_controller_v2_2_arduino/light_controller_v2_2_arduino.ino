const int MAX_CHANNEL_NUM = 4;
const int MAX_PATTERN_NUM = 3;
const int PATTERN_LENGTH = 2;

const int channelPins[MAX_CHANNEL_NUM] = {13,12,11,10};

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

#if PULSE_MODE_COMPILE == 1
  const bool PULSE_MODE_ENABLED = true;
#else
  const bool PULSE_MODE_ENABLED = false;
#endif

struct CompressedPattern {
    byte status[MAX_PATTERN_NUM][PATTERN_LENGTH];
    unsigned long time_ms[MAX_PATTERN_NUM][PATTERN_LENGTH];
    
#if PULSE_MODE_COMPILE == 1
    //* Pulse parameters - only compiled if pulse mode enabled
    unsigned long period[MAX_PATTERN_NUM][PATTERN_LENGTH];  //* Pulse period in milliseconds (0 means no pulsing)
    unsigned long pulse_width[MAX_PATTERN_NUM][PATTERN_LENGTH];  //* Pulse width in milliseconds
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

void read_serial_command(bool &wait_for_command);
void parse_pattern(String command);
void initializePatterns();
void executePatterns();
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
            parse_pattern(command);
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
            Serial.print(";PULSE_MODE:");
            Serial.println(PULSE_MODE_ENABLED ? "1" : "0");
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

            //* Set initial status
            byte status = p.status[patternSequence[ch]][0];
            
            //* Check if pulsing is needed (only if pulse mode enabled)
#if PULSE_MODE_COMPILE >= 1
            if (PULSE_MODE_ENABLED) {
                unsigned long period = p.period[patternSequence[ch]][0];
                unsigned long pw = p.pulse_width[patternSequence[ch]][0];
                
                if (status == 1 && period > 0 && pw > 0) {
                    //* Start with pulse HIGH
                    pulseState[ch] = true;
                    digitalWrite(channelPins[ch], HIGH);
                    //* Schedule next pulse toggle (after pulse width)
                    nextPulseTime[ch] = currentTime + pw;
                } else {
                    //* No pulsing, just set status
                    digitalWrite(channelPins[ch], status ? HIGH : LOW);
                    pulseState[ch] = false;
                    nextPulseTime[ch] = 0;
                }
            } else
#endif
            {
                //* Pulse mode disabled or not compiled, just set status
                digitalWrite(channelPins[ch], status ? HIGH : LOW);
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
            digitalWrite(channelPins[ch], LOW);
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
            
            //* Handle pulsing if pulse mode enabled
#if PULSE_MODE_COMPILE >= 1
            if (PULSE_MODE_ENABLED) {
                byte currentStatus = p.status[seq][idx];
                unsigned long currentPeriod = p.period[seq][idx];
                unsigned long currentPW = p.pulse_width[seq][idx];
                
                //* Check if we need to toggle pulse
                if (currentStatus == 1 && currentPeriod > 0 && currentPW > 0 && nextPulseTime[ch] > 0) {
                    if (currentTime >= nextPulseTime[ch]) {
                        //* Toggle pulse state
                        pulseState[ch] = !pulseState[ch];
                        digitalWrite(channelPins[ch], pulseState[ch] ? HIGH : LOW);
                        
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
                            digitalWrite(channelPins[ch], LOW);  //* Set status to LOW forever
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

                //* Set the new status
                byte status = p.status[seq][idx];
                
#if PULSE_MODE_COMPILE >= 1
                unsigned long period = p.period[seq][idx];
                unsigned long pw = p.pulse_width[seq][idx];
                
                //* Check if new status requires pulsing
                if (status == 1 && period > 0 && pw > 0) {
                    //* Start pulsing: begin with HIGH
                    pulseState[ch] = true;
                    digitalWrite(channelPins[ch], HIGH);
                    //* Schedule next pulse toggle
                    nextPulseTime[ch] = currentTime + pw;
                } else {
                    //* No pulsing, just set status
                    digitalWrite(channelPins[ch], status ? HIGH : LOW);
                    pulseState[ch] = false;
                    nextPulseTime[ch] = 0;
                }
#else
                //* Pulse mode not compiled, just set status
                digitalWrite(channelPins[ch], status ? HIGH : LOW);
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
