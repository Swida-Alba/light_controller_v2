# Utilities and Development Tools

This folder contains utility scripts and development tools for the Light Controller V2.2 project.

## Scripts

### Calibration Management

- **`manage_calibrations.py`** - Manage Arduino calibration database
  - List all stored calibrations
  - Test Arduino connection and show unique ID
  - Export database to text file
  - Delete calibrations
  - See [Auto Calibration Database](../docs/AUTO_CALIBRATION_DATABASE.md) for details

### Analysis & Testing

- **`analyze_results.py`** - Analyze calibration and timing results
- **`calculate_pulse_memory.py`** - Calculate memory usage for pulse parameters
- **`debug_calibration_speed_test.py`** - Debug and test calibration methods (V1, V1.1, V2)
- **`verify_pattern_length_fix.py`** - Verify pattern length compatibility fixes

### Build Tools

- **`simple_build.py`** - Simplified build script for creating executables

## Usage

### Calibration Database Manager

```bash
# List all stored calibrations
python utils/manage_calibrations.py list

# Test Arduino connection and get board ID
python utils/manage_calibrations.py test

# Export database to readable text file
python utils/manage_calibrations.py export

# Delete a calibration from database
python utils/manage_calibrations.py delete

# Show help
python utils/manage_calibrations.py help
```

### Other Tools

These scripts are intended for:
- Development and debugging
- Performance analysis
- Verification testing
- Advanced troubleshooting

Most users won't need these scripts for normal operation. See the main [README.md](../README.md) for standard usage.

## For Developers

If you're contributing to the project or need to debug issues:

1. **Calibration Management**: Use `manage_calibrations.py` to view and manage stored Arduino calibrations
2. **Calibration Testing**: Use `debug_calibration_speed_test.py` to test all three calibration methods
3. **Memory Analysis**: Use `calculate_pulse_memory.py` to estimate SRAM usage
4. **Pattern Verification**: Use `verify_pattern_length_fix.py` to test pattern length fixes

For more information, see the [Development Documentation](../docs/REFACTORING_GUIDE.md).
