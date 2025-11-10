# Changelog

All notable changes to the Light Controller v2.2 project.

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
