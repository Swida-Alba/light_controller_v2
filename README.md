# Light Controller V2

## Overview
This project uses an Arduino sketch (`light_controller_v2.ino`) and a Python program (`protocol_parser.py`) to control light channels according to a defined schedule. It supports serial communication, channel pattern commands, and adjustable timing through a calibration factor. The `protocol_parser.py` program reads a schedule from an Excel file and sends commands to the Arduino board to control the light channels. You can find the example Excel file as `protocol.xlsx`.

## Dependencies
- Arduino IDE (or `arduino-cli`) to upload the `.ino` sketch to your board. You can download the Arduino IDE [here](https://www.arduino.cc/en/software).
- Python 3.6+ on your machine.
- Listed in `requirements.txt`:  
  - `numpy`  
  - `pandas`  
  - `pyserial`  
  - `openpyxl`  
  - `tk`

## Installation
1. Clone or download this repository.  
2. Install the dependencies by running the `setup.py` script.  
```bash
python setup.py install
```

## Usage of the Arduino sketch
1. Open the `light_controller_v2.ino` sketch in the Arduino IDE.
2. Modify the `MAX_CHANNEL_NUM` and `MAX_PATTERN_NUM` constants according to your setup, as far as it does not exceed the memory of your board.
3. Modify the `channelPins` array to match your `MAX_CHANNEL_NUM` and set the pins you are using. Defaultly, it is set to use pins 2 to 7.
4. Select the board and port in the Arduino IDE > Tools.
5. Upload the sketch to your board.

## Usage of the Python program
1. After installing the dependencies, run the `protocol_parser.py` program and select a ```.xlsx``` protocol file.
2. In some cases, you can use the `create_exe.py` script to create an encapsulated `.exe` file from the Python program, so you can run it without Python installed on your other machines. Please note that the `create_exe.py` creates a `.exe` file only if you run it on a Windows machine. If you run it on an MacOS, it will create an compatitable executable file for MacOS.
```bash
python create_exe.py
```

## Protocol file format
The protocol file should be a ```.xlsx``` file with the following format:
- It contains at least two sheets: `protocol` and `start_time`. If provided, a third sheet `calibration` can be used to set the `calibration factor`, which is the ratio of the arduino time to the real time.
- The `protocol` sheet should look like this:

  - | Sections | CH1_status | CH1_time_hr | CH2_status | CH2_time_ms | CH3_status | CH3_time_sec |
    |----------|------------|--------------|------------|-------------|------------|--------------|
    | 0        | 1          | 2            | 0          | 720         | 0          | 1            | 
    | 1        | 0          | 0.5          | 1          | 720         | 1          | 1            | 
    | 2        | 1          | 2            | 0          | 720         | 0          | 1            | 
    | 3        | 0          | 0.5          | 1          | 720         | 1          | 1            | 
    | 4        | 1          | 2            | 0          | 720         | 0          | 1            | 
    | 5        | 0          | 0.5          | 1          | 720         | 1          | 1            | 
    | ...      | ...        | ..           | ...        | ...         | ...        | ...          | 

  - Each row represents a section of the protocol. The first column is the section number, and the following columns are the status and time of each channel. The status is either 0 or 1, 0 for LED OFF and 1 for LED ON. The time can be a integer or a float number, and it is the time that the channel status should be kept. 
  - The time unit is set after the `CHx_time_` column name, which can be `s` (`sec`,`second`,`seconds`), `ms`(`msec`,`millisecond`,`milliseconds`), `m` (`min`,`minute`,`minutes`), `h` (`hr`,`hour`,`hours`). The time unit can not be omitted.
  - The channel number should be continuous from 1 and should not exceed the `MAX_CHANNEL_NUM` defined in the Arduino sketch.

- The `start_time` sheet should look like this:

  - | Channel    | CH1   | CH2   | CH3              |
    |------------|-------|-------|------------------|
    | start_time | 21:00 | 21:00 | 2024-12-24 21:00 |
    | wait_status| 1     | 0     | 0                |

  - The first row is the start time of the protocol. The time format can be `HH:MM:SS`, `HH:MM`, `YYYY-MM-DD HH:MM`, or `YYYY-MM-DD HH:MM:SS`. If the time format is `HH:MM:SS` or `HH:MM`, the date will be set to the current date. Please note that the time should be in 24-hour format and should not be earlier than the current time.
  - The second row is the wait status of each channel. If the wait status is 1, the channel will be turned on until the start time. If the wait status is 0, the channel will be turned off until the start time. 
  - The channel number should be consisent with the `protocol` sheet.

- The `calibration` sheet should look like this:
  - | CALIBRATION_FACTOR |
    |--------------------|
    | 1.000116           |
  - after run once, the program will create a `<protocol_filename>_commands_<timestamp>.txt` file in the same directory as the protocol file. In this file, you'll find the `CALIBRATION_FACTOR`. You can copy it to the protocol file `calibration` sheet to use it in the next runs. If not provided, the program will calibrate the time by itself, but it will take a few minutes each time you run the program.
