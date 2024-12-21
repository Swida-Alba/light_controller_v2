const int MAX_CHANNEL_NUM = 6;
const int MAX_PATTERN_NUM = 10;
const int PATTERN_LENGTH = 2;

const int channelPins[MAX_CHANNEL_NUM] = {2,3,4,5,6,7};

struct CompressedPattern {
    byte status[MAX_PATTERN_NUM][PATTERN_LENGTH];
    unsigned long time_ms[MAX_PATTERN_NUM][PATTERN_LENGTH];
    int repeats[MAX_PATTERN_NUM];
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

void read_serial_command(bool &wait_for_command);
void parse_pattern(String command);
void initializePatterns();
void executePatterns();
void parseByteArray(String data, byte arr[]);
void parseULongArray(String data, unsigned long arr[]);
void calibrate_time(String command);

void setup() {
    Serial.begin(9600);
    while (!Serial) {
        ; //* Wait for serial port to connect. Needed for native USB port only
    }

    //* Initialize channel pins as outputs and set them to LOW
    for (int i = 0; i < MAX_CHANNEL_NUM; i++) {
        pinMode(channelPins[i], OUTPUT);
        digitalWrite(channelPins[i], LOW);
        channelPatterns[i].pattern_num = 0;
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
            Serial.println("Salve");
        }
        else if (command.startsWith("calibrate_")) { 
            //* calibrate command is as "calibrate_" + timeStr, where timeStr is time for several chars representing milliseconds
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
    //* "PATTERN:n;CH:n;STATUS:s1,s2;TIME_MS:t1,t2;REPEATS:r"

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

        //* Parse STATUS
        int statusIndexStart = command.indexOf("STATUS:") + 7;
        int statusIndexEnd = command.indexOf(';', statusIndexStart);
        String statusStr = command.substring(statusIndexStart, statusIndexEnd);
        parseByteArray(statusStr, p.status[patternNum]);

        //* Parse TIME_MS
        int timeIndexStart = command.indexOf("TIME_MS:") + 8;
        int timeIndexEnd = command.indexOf(';', timeIndexStart);
        String timeStr = command.substring(timeIndexStart, timeIndexEnd);
        parseULongArray(timeStr, p.time_ms[patternNum]);

        //* Parse REPEATS
        int repeatsIndexStart = command.indexOf("REPEATS:") + 8;
        String repeatsStr = command.substring(repeatsIndexStart);
        p.repeats[patternNum] = repeatsStr.toInt();

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
            digitalWrite(channelPins[ch], status ? HIGH : LOW);

            //* Schedule next event time
            nextEventTime[ch] = currentTime + p.time_ms[patternSequence[ch]][0];
        } else {
            //* Channel is inactive
            channelActive[ch] = false;
            digitalWrite(channelPins[ch], LOW);
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

            if (currentTime >= nextEventTime[ch]) { //* Time to execute the next event
                int seq = patternSequence[ch];
                int idx = patternIndices[ch][seq];

                //* Move to the next index in the current pattern
                idx++;

                if (idx >= PATTERN_LENGTH) {
                    idx = 0;
                    repeatCounters[ch][seq]++;

                    if (repeatCounters[ch][seq] >= p.repeats[seq]) {
                        //* Move to the next pattern
                        seq++;
                        if (seq >= p.pattern_num) {
                            //* No more patterns, deactivate channel
                            channelActive[ch] = false;
                            digitalWrite(channelPins[ch], LOW);  //* Set status to LOW forever
                            continue;
                        } else {
                            //* Reset counters for the new pattern
                            repeatCounters[ch][seq] = 0;
                            idx = 0;
                        }
                    }
                }

                //* Update indices
                patternSequence[ch] = seq;
                patternIndices[ch][seq] = idx;

                //* Set the new status
                byte status = p.status[seq][idx];
                digitalWrite(channelPins[ch], status ? HIGH : LOW);

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

void parseByteArray(String data, byte arr[]) {
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
}

void parseULongArray(String data, unsigned long arr[]) {
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
}

void calibrate_time(String command) {
    String timeStr = command.substring(10);
    unsigned long time = timeStr.toInt();
    unsigned long startTime = millis();
    unsigned long duration = 0;
    while (duration < time) {
        duration = millis() - startTime;
    }
    Serial.print("calibration_");
    Serial.println(duration);
}
