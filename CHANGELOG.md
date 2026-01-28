# Changelog

All notable changes to the Light Controller v2.3 project.

## [2.3.3] - 2026-01-29

### Binary Value Interpretation Fix
Fixed issue where integer 0/1 STATUS values were interpreted as literal intensity values
instead of binary HIGH/LOW (full intensity).

**Problem**: `STATUS:1,0` was being interpreted as PWM value 1 (nearly off) instead of 
full intensity (255 for PWM, 4095 for DAC).

**Solution**: Integer 0 and 1 are now treated as binary HIGH/LOW:
- `0` = OFF (value 0)
- `1` = ON (full intensity: 255 for PWM, 4095 for DAC)
- `2-255` = Actual PWM value (passed through)
- `256-4095` = Actual DAC value (capped to 255 for PWM channels)
- `0.0-1.0` (float) = Normalized value (scaled to channel max)

### Arduino Firmware Changes
- **`parseChannelValue()`**: Updated to treat integer 0/1 as binary HIGH/LOW
- **`convertToChannelResolution()`**: Updated with same binary interpretation for RAMP parsing

### Python Changes (viz_protocol_html.py)
- **`convert_binary_to_intensity()`**: New helper function for consistent value interpretation
- Fixed intensity chart generation to display correct values for binary 0/1
- RAMP segment start/end values now correctly interpret binary 0/1

### Backward Compatibility
- Existing protocols using `STATUS:1,0` now work correctly (full intensity on/off)
- Protocols using explicit values like `STATUS:255,0` continue to work unchanged
- Float normalized values like `STATUS:0.5,0.0` continue to work as expected

---

## [2.3.2] - 2026-01-24

### Virtual Pin System Restored
- **Virtual Pin Numbers**: Channel types auto-detected from pin numbers
  - `0-99`: PWM pins (use Arduino digital pin numbers)
  - `100-101`: Native DAC (100=DAC0, 101=DAC1 on Arduino Due)
  - `201-204`: MCP4728 I2C DAC (201=CH_A, 202=CH_B, 203=CH_C, 204=CH_D)
- **Auto-Detection**: `channelTypes[]` array populated automatically at startup based on pin numbers
- **Simplified Configuration**: Only need to set `channelPins[]` - types determined automatically

### Value Handling Rules (NO AUTO-SCALING)
- **Normalized Values (0.0-1.0)**: Scaled to channel's max value (255 for PWM, 4095 for DAC)
- **8-bit Values (0-255) on DAC**: Kept as-is with WARNING (low resolution)
- **12-bit Values (256-4095) on PWM**: CAPPED to 255 with WARNING
- **Values > 4095**: CAPPED to channel max with WARNING
- **Decimal on Binary Channel**: ERROR (illegal - use 0 or 1 only)

### Arduino Firmware Changes
- **`detectPinType()`**: Auto-detect channel type from virtual pin number
- **`isMCP4728Pin()` / `isNativeDACPin()`**: Helper functions for pin type checking
- **`getMCP4728Channel()` / `getNativeDACIndex()`**: Convert virtual pins to hardware indices
- **`parseChannelValue()`**: New validation function with proper warnings/errors
- **Removed explicit `channelTypes[]` const**: Now auto-populated in setup()

### Python Enhancements
- **`convert_status_to_channel_value()`**: Updated to NOT scale between resolutions
  - 8-bit values on 12-bit channels: WARNING (kept as-is)
  - 12-bit values on 8-bit channels: CAPPED with WARNING
  - Decimals on binary channels: ERROR
- **`warnings` parameter**: Collects warning messages for later display
- **Mock Arduino**: New `channel_pins` parameter for auto-detection of channel types

### Example Updates
- **mixed_channel_types.txt**: Updated comments to reflect no-scaling behavior
- **dac_output_demo.txt**: Updated to use proper 12-bit values and normalized values

### Hello Response Format
Arduino greeting includes auto-detected configuration:
```
Salve;...;CH_PINS:11,12,201,202;CH_TYPES:PPMM;CH_MAX:255,255,4095,4095
```

---

## [2.3.1] - 2026-01-24

### Added - DAC Output Support
- **MCP4728 I2C DAC**: 4-channel 12-bit DAC support (0-4095) via virtual pins 201-204
- **Native DAC Support**: Arduino Due (DAC0/DAC1), Zero (DAC0), Uno R4 (DAC) via pins 100-101
- **Automatic Scaling**: 8-bit internal values (0-255) auto-scale to 12-bit (0-4095) for DAC outputs
- **Virtual Pin System**: Pin numbers 0-99 for PWM, 100-199 for native DAC, 201-204 for MCP4728

### Added - Library Requirements
- **Adafruit MCP4728 Library**: Required for MCP4728 DAC support
- **Adafruit BusIO**: Dependency for I2C communication
- **Wire.h**: Standard Arduino I2C library (included)

### Arduino Firmware Changes
- **`MCP4728_ENABLE`**: Compile-time flag to enable/disable MCP4728 support (default: enabled)
- **`MCP4728_PIN_BASE`**: Virtual pin base for MCP4728 channels (default: 201)
- **`HAS_NATIVE_DAC`**: Board-specific detection for native DAC support
- **`setChannelOutput()`**: Unified function handles PWM, native DAC, and MCP4728 outputs
- **`pwmTo12bit()`**: Converts 8-bit values to 12-bit for DAC output
- **Hello Response**: Now includes MCP4728 status and DAC configuration

### Documentation
- **ARDUINO_SETUP.md**: New MCP4728 wiring, library installation, and troubleshooting sections
- **PWM_RAMP_CONTROL.md**: Updated with output types table and DAC information
- **examples/dac_output_demo.txt**: New example demonstrating MCP4728 usage

### Design Notes
- **Value Range**: Protocols continue using 0.0-1.0 normalized values (or legacy 0-255)
- **Conversion Strategy**: Python converts 0.0-1.0 → 0-255; Arduino scales to 12-bit at output
- **Memory Efficiency**: Internal storage remains byte (0-255) to minimize RAM usage
- **Backward Compatible**: Existing protocols work without modification

---

## [2.3.0] - 2025-12-26

### Hardware Testing
- **Arduino Due Verification**: Tested and verified full PWM/RAMP functionality on Arduino Due
- **Real-time Monitoring**: Added `--monitor` flag to protocol_parser.py for live channel value capture
- **$CHMON Integration**: Captured and validated PWM values during protocol execution
- **Calibration Verified**: Arduino Due calibration factor 0.999949 (0.0051% timing accuracy)

### Real-Time Monitoring Enhancements
- **Matplotlib-Based Visualization**: Replaced PyQtGraph with matplotlib for cross-platform portability
- **5-Minute Scrolling Window**: Real-time display shows moving 5-min window for protocols of any length
- **Extended Data Storage**: Stores up to 1 hour of data (36,000 points at 10Hz) for complete export
- **Plotly HTML Export**: Automatically saves interactive HTML chart with range slider when monitoring stops
- **Flexible CLI**: `--monitor` flag can now appear anywhere in command line (position-independent)
- **Dual Output Files**: Generates both `*_monitored.csv` and `*_monitored.html` on close

### Documentation
- **Arduino Due Recommended**: Updated ARDUINO_SETUP.md to strongly recommend Arduino Due for PWM/RAMP mode
- **Memory Requirements**: Documented that firmware uses ~12KB SRAM (Arduino Uno's 2KB insufficient)
- **Quick Start Updated**: README.md now includes memory warnings and board recommendations
- **Serial Monitor Guide Updated**: New features for 5-min window and Plotly HTML export
- Archived 29 outdated documentation files (reduced from 61 to 32 active docs)
- Created comprehensive doc archival system with README index
- Reorganized examples/ folder with dedicated subfolders

### Tools
- **compare_monitored_data.py**: New utility to compare captured PWM values against expected protocol
- **Protocol Parser CLI**: Added command-line arguments for port and protocol file
- **Non-interactive Mode**: Calibration auto-confirms stored values when stdin is not a tty

### Bug Fixes
- **viz_protocol_html.py**: Fixed ZeroDivisionError for RAMP patterns with empty time_ms
- **serial_monitor.py**: Fixed variable name bugs (`serial_conn` → `serial`, `disconnect` → `close`)
- **lcfunc.py**: SetUpSerialPort() now accepts explicit port parameter

### Examples
- **1min_test.txt**: New quick test protocol (60s, 2 channels, RAMP + blink)
- **5min_pwm_ramp_demo.txt**: Longer demo protocol with multiple pattern types
- Created `ramp_easing/` subfolder for RAMP and easing mode demonstrations
- Fixed obsolete PULSE syntax (trailing commas) in clean_protocol.txt and complete_protocol.txt
- Updated pwm_ramp_protocol.txt from legacy to v2.2.3+ parenthesized RAMP format
- Removed redundant Excel files from examples root
- Created comprehensive READMEs for all example subfolders

### Maintenance
- Updated all documentation to reference v2.3.0
- Cleaned up outdated version references
- Improved documentation discoverability

## [2.2.3] - 2025-12-25

### Added - New Command Format
- **Parenthesized Segments**: New cleaner format `(MODE:start,end,duration[,steps][|t_start,t_end])`
- **Auto Steps Calculation**: Steps are now optional and auto-calculated based on duration
- **Custom t Range**: Specify t range directly after `|` instead of extra parameters
- **Multi-Segment Clarity**: Segments separated by commas in parentheses: `(L:0,255,1000),(O:255,0,1000)`

### Added - Unified Cosine Formula
- **Single Formula**: `f(t) = (1 - cos(πt)) / 2` for all easing modes
- **Extended t Range**: Now t ∈ [0, 2] for complete cycle: 0→1→0
- **Mode t Mappings**:
  - Ease-In (I): t = [0, 1] → 0 to 1 (accelerating)
  - Ease-Out (O): t = [1, 2] → 1 to 0 (decelerating, inverted)
  - Full Cycle (X): t = [0, 2] → 0 to 1 to 0 (breathing)

### Added - Interactive Visualization
- **Jupyter Notebook**: `docs/easing_curves_visualization.ipynb` with Plotly charts
- **Mode Comparisons**: Side-by-side visualization of all easing modes
- **Custom t Range Explorer**: Interactive widget to experiment with t values
- **Multi-Segment Simulator**: Preview complex ramp patterns

### Added - HTML Intensity Plots
- **Plotly Integration**: viz_protocol_html.py now includes embedded Plotly charts
- **Intensity Timeline**: Per-channel PWM value over time visualization
- **RAMP Parsing**: Full support for new command format in visualizer
- **Interactive Charts**: Zoom, pan, and hover for detailed inspection

### Python API Updates
- **`calculate_eased_value()`**: Updated for unified formula with t_start/t_end
- **`generate_ramp_segment_new()`**: New function for parenthesized format
- **`create_breathing_ramp()`**: Helper for t=[0,2] breathing patterns
- **`new_format=True`**: Parameter on existing functions for new format output

### Documentation
- **Updated PWM_RAMP_CONTROL.md**: New format examples, formula explanation
- **Added easing_curves_visualization.ipynb**: Interactive Jupyter notebook

---

## [2.2.2] - 2025-06-06

### Added - Easing Functions for RAMP
- **Cosine Easing**: `f(t) = (1 - cos(πt)) / 2` for smooth S-curve transitions
- **Ease-In**: `f(t) = 1 - cos(πt/2)` for slow start, fast end
- **Ease-Out**: `f(t) = sin(πt/2)` for fast start, slow end  
- **Custom Easing**: Specify any portion of cosine curve with custom t range (radians)
- **Easing Mode Parameter**: Added optional mode to RAMP command: `RAMP:start,end,duration,steps,MODE`
  - `L` = Linear (default), `C` = Cosine, `I` = Ease-In, `O` = Ease-Out, `X` = Custom

### Added - Multi-Segment RAMP
- **Combined Segments**: Chain multiple ramp segments with `|` separator
- **Format**: `RAMP:seg1|seg2|seg3` where each segment = `start,end,duration,steps,mode`
- **MAX_RAMP_SEGMENTS**: Up to 4 segments per pattern
- **Seamless Transitions**: Arduino automatically handles segment transitions

### Added - Python Easing Utilities
- **`calculate_eased_value()`**: Preview eased PWM values in Python
- **`generate_ramp_segment()`**: Generate single segment strings
- **`generate_multi_ramp_command()`**: Generate multi-segment RAMP commands
- **`create_fade_in_out_ramp()`**: Convenience function for common fade patterns
- **`create_cosine_wave_ramp()`**: Convenience function for breathing effects

### Arduino Enhancements
- **`calculateEasedValue()`**: New function implementing all easing formulas
- **`RampSegment` struct**: New struct with easing parameters (easing_mode, t_start, t_end)
- **`RampPattern.segments[]`**: Array of segments for multi-segment support
- **`rampCurrentSegment[]`**: Track current segment per channel during execution

### Documentation
- **Updated PWM_RAMP_CONTROL.md**: Added easing functions and multi-segment documentation
- **Updated pwm_ramp_protocol.txt**: New examples with easing and multi-segment patterns

## [2.2.1] - 2024-12-25

### Added - PWM Intensity Control
- **PWM Status Values**: STATUS can now be 0-255 (not just 0/1) for variable light intensity
- **Float Input Support**: Protocol files accept 0.0-1.0 float values (auto-converted to 0-255)
- **Backward Compatible**: Legacy binary 0/1 values still work (mapped to 0/255)
- **`convert_status_to_pwm()`**: New utility function for consistent PWM conversion

### Added - RAMP Gradient Transitions
- **RAMP Command**: New command format `RAMP:<start>,<end>,<duration_ms>,<steps>` for smooth transitions
- **Arduino-Side Interpolation**: Ramps execute smoothly on Arduino without sending individual steps
- **Memory Efficient**: Single RAMP command replaces 100+ individual pattern steps
- **Auto-Step Calculation**: Default 1 step per 100ms if steps not specified

### Added - Arduino PWM Mode
- **PWM_RAMP_MODE**: Compile-time flag to enable PWM intensity control
- **`setChannelOutput()`**: New function using `analogWrite()` for PWM output
- **`executeRamp()`**: New function for smooth RAMP interpolation during execution
- **`parse_ramp_pattern()`**: New function to parse RAMP commands
- **Greeting Updated**: Hello response now reports `PWM_RAMP_MODE:1` capability

### Documentation
- **PWM_RAMP_CONTROL.md**: Comprehensive guide for PWM and RAMP features
- **pwm_ramp_protocol.txt**: Example protocol demonstrating new features

## [2.2.0] - 2024-12-12

### Fixed - Serial Communication
- **PULSE Command Truncation**: Fixed issue where long PULSE commands (e.g., `T986pw98,T0pw0`) were being truncated during serial transmission
- **Serial Buffer Sync**: Added `ser.flush()` after writing commands and `ser.reset_input_buffer()` before each command
- **Command Timing**: Added 50ms delay after flush to allow Arduino to receive complete commands
- **Arduino Serial Timeout**: Increased `Serial.setTimeout()` from default 1000ms to 2000ms for longer commands

### Fixed - Calibration System
- **Calibration Skip Issue**: Fixed bug where calibration was being skipped when database file was deleted
- **Auto-Calibrate Prompt**: Removed 'n' option from `auto_calibrate_arduino()` - calibration now mandatory when no stored calibration exists
- **Calibration Trigger**: `calibrate()` now properly triggers when factor equals 1.0 (uncalibrated default)

### Improved - Visualization
- **Uncalibrated Time Display**: Visualization now shows original Python/requested times instead of calibrated Arduino times
- **Per-Channel Left Time**: Added remaining time display for each channel in the monitor header
- **Per-Pattern Left Time**: Added remaining time display for each pattern section
- **Total Left Time**: Added overall remaining time in header after Upload Time / Elapsed
- **Channel Time Range**: Added Start → End times for each channel (excluding wait patterns)
- **Monitor Filename**: Changed output filename from `*_commands_*.html` to `*_monitor_*.html`

### Technical
- **PULSE Format**: Confirmed format is `T{period}pw{width}` (e.g., `T1000pw50` = 1Hz with 50ms pulse width)
- **Defensive Null Checks**: Added `calib_factor` None checks in `ApplyCalibrationToTxtCommands()`, `CorrectTime_dict()`, and `parse_txt_protocol()`

## [2.2.0] - 2025-11-08

### Added - HTML Visualization System
- **Real-Time Monitoring**: Browser-based interface with 1-second updates
- **Dual Time Tracking**: Separate Total Elapsed (global) and Protocol Elapsed (per-channel)
- **Smart Waiting Display**: Shows actual ON/OFF/PULSING status during wait periods
- **Pulse Info During Wait**: Displays frequency, period, pulse width, and duty cycle
- **JavaScript-Only Architecture**: All calculations in browser, no Python dependencies after generation
- **DOM Element Caching**: 60x performance improvement by caching DOM references
- **Enhanced Status Indicators**: Animated LEDs (green=ON, gray=OFF, orange=PULSING, blue=COMPLETED)
- **Timeline Position Tracking**: Red marker shows exact position in protocol
- **Pattern Highlighting**: Current pattern block highlighted with yellow border
- **Channel-Specific IDs**: Reliable element caching with `id="channel-{num}-section"`

### Added - General Features
- **Duty Cycle % Sign Support**: Accept `10%`, `"10%"`, `0.1`, `10` all as 10% duty cycle
- **Descriptive Command Comments**: Automatic annotation with frequency, duty cycle, and time information
- **Column-Based Start Time Format**: Vertical layout for protocols with many channels (auto-detected)
- **All 4 Pulse Combinations**: Support for F+PW, F+DC, T+PW, T+DC input formats
- **Comprehensive Validation**: PW ≤ Period, DC ≤ 100%, with clear error messages
- **Arduino Due Support**: Full compatibility with both Native USB and Programming ports

### Improved - HTML Visualization
- **Update Frequency**: Increased from 5 seconds to 1 second for smoother monitoring
- **Color Scheme**: Changed secondary text from #666 to #bbb for better readability
- **Protocol Elapsed Format**: Shows `--:--:--:--` during wait, then counts from `00:00:00:00`
- **Error Handling**: Defensive null checks prevent timer freezing
- **Type Safety**: Added `typeof` checks for pulse string validation
- **Performance**: Eliminated 60+ DOM queries per second with caching
- **Memory Usage**: Stable memory footprint with consistent low CPU
- **Load Time**: Reduced from 2-5 seconds to <0.1 seconds

### Improved - General
- Enhanced serial communication reliability (4-second uniform initialization)
- Better error messages with actionable guidance
- Improved documentation with consolidated README
- More example files demonstrating all features

### Fixed - HTML Visualization
- **Timer Freezing**: Fixed by adding null checks before accessing `channel[pos.current_pattern]`
- **Pulse String Type Error**: Changed from storing boolean to actual pulse string
- **Loading Delays**: Eliminated with DOM caching and JavaScript-only calculations
- **Position Marker Accuracy**: Bounds checking prevents out-of-range access

### Fixed - General
- Arduino Due greeting timeout issues
- Serial buffer handling for better reliability
- Input buffer reset before critical operations

### Documentation
- **[HTML Visualization Guide](docs/HTML_VISUALIZATION.md)**: Complete user guide with examples
- **[HTML Visualization Updates](docs/HTML_VISUALIZATION_UPDATES.md)**: Technical details of improvements
- Updated **README.md** with enhanced visualization features
- Added visualization section to Core Documentation table

## [2.1.0] - 2025-11-03

### Added
- **Text Protocol Support**: `.txt` files as alternative to Excel
- **Multiple Time Units**: `TIME_S`, `TIME_M`, `TIME_H`, `TIME_MS` support in TXT files
- **Flexible START_TIME Formats**: Datetime strings, time-only strings, or numeric countdown
- **Float Time Values**: Support for decimal values in all time units (e.g., `2.5`, `30.5`)
- **Comment Support**: Lines starting with `#` are ignored in TXT files
- **Space Tolerance**: Spaces in PATTERN commands automatically removed

### Enhanced
- **Time-only formats** (`HH:MM`) now use today's date instead of defaulting to 1900
- **Countdown mode** support for TXT files (consistent with Excel)
- **Robust calibration parsing**: Empty/invalid calibration triggers auto-calibration
- **Dynamic wait commands**: PATTERN:0 always regenerated based on current time

### Improved
- Code organization: Utility functions moved to `lcfunc.py`
- Better separation of concerns in `protocol_parser.py`
- Cleaner imports and more maintainable structure

### Fixed
- START_TIME parsing: Numeric countdown values now handled correctly
- Time-only format: `'15:30'` now uses today's date (not 1900-01-01)
- CALIBRATION_FACTOR edge cases: Empty values handled gracefully
- TypeError crashes from numeric START_TIME values

## [2.0.0] - Previous Version

### Features
- Excel protocol file support (`.xlsx`)
- Arduino serial communication
- Automatic time calibration
- Pattern compression and repeat detection
- Wait command generation
- Multi-channel support (6+ channels)
- Pulse frequency control
- Wait status control

---

## Migration Guide

### From v2.0 to v2.1
**No breaking changes**. All v2.0 Excel files continue to work without modification.

### From v2.1 to v2.2
**No breaking changes**. All v2.1 files continue to work. New features are optional enhancements.

---

## Version Compatibility

**Python Requirements:** Python 3.6+

**Arduino Requirements:** 
- Compatible with Arduino Uno, Due, Mega, and similar boards
- Configurable channel count (default: 6 channels)
- Memory-dependent pattern storage

---

## Future Roadmap

### Planned
- Web-based protocol editor
- Real-time monitoring dashboard
- Protocol validation tool
- Graphical timeline visualization

### Under Consideration
- YAML protocol format
- REST API for remote control
- Mobile app companion
- Cloud storage integration

---

**For detailed information, see [README.md](README.md)**
