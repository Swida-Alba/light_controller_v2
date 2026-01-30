"""
Light Controller Parser - A class-based interface for parsing and executing LED control protocols.

This module provides a clean, object-oriented interface to replace the functional approach
in protocol_parser.py. It encapsulates all protocol parsing, validation, calibration,
and command generation logic.

Usage:
    # Command line:
    python light_controller_parser.py protocol.txt --live-plot
    python light_controller_parser.py --port /dev/cu.usbmodem14301 --live-plot
    
    # As a module:
    from light_controller_parser import LightControllerParser
    
    # Create parser instance
    parser = LightControllerParser(protocol_file='protocol.xlsx')
    
    # Setup serial connection
    parser.setup_serial(board_type='Arduino', baudrate=9600)
    
    # Parse and send commands
    parser.parse_and_execute()
    
    # Clean up
    parser.close()
"""

import os
import sys
import argparse
import datetime
import time
import threading
from collections import deque

# Import syntax checker for protocol validation
try:
    from syntax_check import ProtocolSyntaxChecker
    SYNTAX_CHECK_AVAILABLE = True
except ImportError:
    SYNTAX_CHECK_AVAILABLE = False
from lcfunc import *

# Try to import plotting libraries
try:
    from dash import Dash, dcc, html
    from dash.dependencies import Input, Output
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False


class LightControllerParser:
    """
    Main class for parsing LED control protocols and communicating with Arduino.
    
    Attributes:
        protocol_file (str): Path to the protocol file (.xlsx or .txt)
        ser: Serial connection object
        file_ext (str): File extension (.xlsx or .txt)
        calib_factor (float): Calibration factor for time correction
        valid_channels (list): List of valid channel names
        start_time (dict): Start times for each channel
        wait_status (dict): Wait status for each channel
        wait_pulse (dict): Optional pulse parameters during wait period
        cmd_patterns (list): Generated pattern commands
        cmd_wait (list): Generated wait commands
    """
    
    def __init__(self, protocol_file, pattern_length=2, calibration_method='v2'):
        """
        Initialize the parser with a protocol file.
        
        Args:
            protocol_file (str): Path to protocol file (.xlsx or .txt)
            pattern_length (int): Pattern length for Excel compression (default: 2)
            calibration_method (str): Calibration method to use (default: 'v2')
                Available methods:
                - 'v1': Original method
                        Arduino waits, Python measures with dead sleep
                        Test times: [30,40,50,60]s, Total: ~150s
                        Best for: Backward compatibility
                        
                - 'v11' or 'v1.1': V1.1 method (NEW)
                        Arduino waits, Python measures with active polling
                        Test times: [30,40,50,60]s, Total: ~150s
                        Best for: Better responsiveness than V1, same accuracy
                        
                - 'v2': Multi-timestamp method (RECOMMENDED)
                        Arduino sends periodic timestamps, Python records arrivals
                        Duration: 180s with 9 samples (20s intervals)
                        Excludes t=0 to avoid initialization overhead
                        Best for: Most accurate, faster than V1/V1.1
                        
        Example:
            # Use V2 (recommended, most accurate)
            parser = LightControllerParser('protocol.xlsx', calibration_method='v2')
            
            # Use V1.1 (new, active wait)
            parser = LightControllerParser('protocol.xlsx', calibration_method='v1.1')
            
            # Use V1 (backward compatible)
            parser = LightControllerParser('protocol.xlsx', calibration_method='v1')
        """
        self.protocol_file = protocol_file
        self.ser = None
        self.file_ext = os.path.splitext(protocol_file)[1].lower()
        self.pattern_length = pattern_length  # Store pattern_length for Excel compression
        self.calibration_method = calibration_method.lower()  # Store calibration method preference
        
        # Validate calibration method
        if self.calibration_method not in ['v1', 'v11', 'v1.1', 'v2', 'v2_improved']:
            raise ValueError(f'Invalid calibration method: {calibration_method}. Use "v1", "v11" (or "v1.1"), "v2", or "v2_improved".')
        
        # Normalize v1.1 notation
        if self.calibration_method in ['v11', 'v1.1']:
            self.calibration_method = 'v11'
        
        # Initialize attributes that will be set during parsing
        self.calib_factor = None
        self.valid_channels = []
        self.start_time = {}
        self.wait_status = {}
        self.wait_pulse = {}
        self.loop = {}  # Loop mode for each channel (0=no loop, 1=loop forever)
        self.cmd_patterns = []
        self.cmd_wait = []
        self.arduino_config = {}  # Arduino configuration from greeting
        
        # Validate file extension
        if self.file_ext not in ['.txt', '.xlsx']:
            raise ValueError(f'Unsupported file format: {self.file_ext}. Please use .xlsx or .txt files.')
        
        # Validate syntax for TXT files before parsing
        if self.file_ext == '.txt':
            self.validate_protocol()
    
    def validate_protocol(self, strict=True):
        """
        Validate protocol syntax before parsing.
        
        Uses the ProtocolSyntaxChecker to validate the protocol file for
        syntax errors, typos, and structural issues before parsing.
        
        Args:
            strict (bool): If True, raise exception on errors. If False, only warn.
            
        Raises:
            ValueError: If syntax errors found and strict=True
        """
        if not SYNTAX_CHECK_AVAILABLE:
            print('⚠️  Syntax checker not available (syntax_check.py not found)')
            print('   Skipping syntax validation...')
            return
        
        if self.file_ext != '.txt':
            # Only TXT files support full syntax validation currently
            return
        
        print('\n' + '='*60)
        print('🔍 Validating protocol syntax...')
        print('='*60)
        
        checker = ProtocolSyntaxChecker()
        is_valid, errors, warnings = checker.check_file(self.protocol_file)
        
        # Print warnings (always)
        if warnings:
            print(f'\n⚠️  Warnings ({len(warnings)}):')
            for warning in warnings:
                print(f'   • {warning}')
        
        # Print errors
        if errors:
            print(f'\n❌ Syntax Errors ({len(errors)}):')
            for error in errors:
                print(f'   • {error}')
            
            if strict:
                raise ValueError(
                    f'Protocol syntax validation failed with {len(errors)} error(s). '
                    f'Fix the errors above or run with syntax validation disabled.'
                )
            else:
                print('\n⚠️  Continuing despite errors (strict=False)...')
        else:
            print('\n✅ Protocol syntax is valid!')
        
        print('='*60 + '\n')
    
    def _detect_pattern_length_from_commands(self, commands):
        """
        Detect the maximum pattern length from generated commands.
        
        Args:
            commands (list): List of command strings
            
        Returns:
            int: Maximum pattern length detected (number of values in STATUS/TIME_MS arrays)
        """
        max_length = 0
        for cmd in commands:
            if 'STATUS:' in cmd:
                # Extract STATUS values between STATUS: and the next ;
                status_part = cmd.split('STATUS:')[1].split(';')[0]
                status_values = status_part.split(',')
                length = len(status_values)
                if length > max_length:
                    max_length = length
        return max_length
    
    def _detect_max_ramp_segments_from_commands(self, commands):
        """
        Detect the maximum number of RAMP segments from generated commands.
        
        Args:
            commands (list): List of command strings
            
        Returns:
            int: Maximum number of RAMP segments in any single command
        """
        import re
        max_segments = 0
        for cmd in commands:
            if 'RAMP:' in cmd:
                # Extract RAMP part: RAMP:(...),...,(...)
                ramp_match = re.search(r'RAMP:([^;]+)', cmd)
                if ramp_match:
                    ramp_str = ramp_match.group(1)
                    # Count segments by counting opening parentheses
                    segment_count = ramp_str.count('(')
                    if segment_count > max_segments:
                        max_segments = segment_count
        return max_segments
    
    def _evaluate_pattern_compression(self, df_ms, pattern_lengths=[2, 4, 8]):
        """
        Evaluate different pattern lengths and find the most efficient one.
        
        Args:
            df_ms: DataFrame with protocol data
            pattern_lengths (list): Pattern lengths to test
            
        Returns:
            dict: Results with pattern_length as key and total commands as value
        """
        from lcfunc import FindRepeatedPatterns, GeneratePatternCommands
        
        results = {}
        for pl in pattern_lengths:
            try:
                compressed = FindRepeatedPatterns(df_ms, pattern_length=pl)
                commands = GeneratePatternCommands(compressed)
                results[pl] = len(commands)
            except Exception as e:
                # Pattern length may not work for this protocol
                results[pl] = float('inf')
        
        return results
    
    def _load_protocol_for_inspection(self):
        """
        Load protocol file to inspect its structure (e.g., for pulse detection).
        This is a lightweight load that doesn't do full parsing.
        
        Returns:
            DataFrame: Protocol data (for Excel) or None (for TXT, which requires full parsing)
        """
        if self.file_ext == '.xlsx':
            # For Excel, we can load the protocol DataFrame directly
            df_protocol, _, _ = ReadExcelFile(self.protocol_file)
            return df_protocol
        else:
            # For TXT files, we need to check the raw commands
            # Read the file to check for pulse-related syntax
            try:
                with open(self.protocol_file, 'r') as f:
                    content = f.read()
                    # Check if file contains pulse syntax (T...pw... or PULSE: columns)
                    has_pulse_syntax = ('PULSE:' in content or 
                                       any(f'T{i}' in content and 'pw' in content for i in range(10)))
                    # Return a simple indicator
                    if has_pulse_syntax:
                        # Create a dummy DataFrame with pulse column to trigger detection
                        import pandas as pd
                        return pd.DataFrame({'dummy_period': [1]})
                    else:
                        return pd.DataFrame({'dummy': [1]})
            except Exception:
                # If we can't read, assume no pulses
                import pandas as pd
                return pd.DataFrame({'dummy': [1]})
    
    def setup_serial(self, board_type='Arduino', baudrate=9600, verify_pattern_length=True, port_override=None, skip_checks=False, **kwargs):
        """
        Setup serial connection to Arduino with optional pattern length verification.
        
        Args:
            board_type (str): Type of Arduino board
            baudrate (int): Serial baud rate
            verify_pattern_length (bool): Verify Arduino PATTERN_LENGTH matches protocol requirements (default: True)
            port_override (str): Optional specific serial port to use (auto-detect if None)
            skip_checks (bool): Skip memory and pulse mode compatibility checks (default: False)
            **kwargs: Additional serial port parameters
            
        Returns:
            bool: True if connection successful, False otherwise
            
        Raises:
            ValueError: If pattern length verification fails
        """
        # Handle port: use port_override if specified, otherwise use port from kwargs, otherwise auto-detect
        if port_override is not None:
            kwargs['port'] = port_override
        self.ser = SetUpSerialPort(board_type=board_type, baudrate=baudrate, **kwargs)
        if not self.ser:
            return False
        
        # Clear buffer
        ClearSerialBuffer(self.ser, print_flag=True)
        
        # Skip memory and pulse mode checks if requested
        if skip_checks:
            print("\n⚡ Skipping memory and pulse mode checks (--skip-check enabled)")
            print("   Use this when Arduino is stuck/unresponsive after a previous session")
            
            # Still need to send greeting and get basic config
            if verify_pattern_length:
                print("\n📏 Detecting pattern length from protocol...")
                self.generate_pattern_commands()
                max_pattern_length = self._detect_pattern_length_from_commands(self.cmd_patterns)
                max_ramp_segments = self._detect_max_ramp_segments_from_commands(self.cmd_patterns)
                
                # Send greeting without strict verification
                try:
                    arduino_config = SendGreeting(self.ser, expected_pattern_length=max_pattern_length,
                                                  expected_max_ramp_segments=max_ramp_segments if max_ramp_segments > 0 else None)
                    self.arduino_config = arduino_config
                except Exception as e:
                    print(f"\033[33m⚠️  Greeting warning (continuing anyway): {e}\033[0m")
                    self.arduino_config = {}
            else:
                try:
                    arduino_config = SendGreeting(self.ser)
                    self.arduino_config = arduino_config
                except Exception as e:
                    print(f"\033[33m⚠️  Greeting warning (continuing anyway): {e}\033[0m")
                    self.arduino_config = {}
            
            return True
        
        # Check memory and pulse mode compatibility
        print("\n💾 Checking Arduino memory and pulse mode compatibility...")
        mem_info = GetArduinoMemory(self.ser)
        
        if mem_info:
            free_mb = mem_info['free'] / 1024.0
            total_mb = mem_info['total'] / 1024.0
            used_mb = mem_info['used'] / 1024.0
            
            print(f"   Arduino Memory:")
            print(f"     Total:  {total_mb:.1f} KB")
            print(f"     Used:   {used_mb:.1f} KB ({mem_info['percent_used']:.1f}%)")
            print(f"     Free:   {free_mb:.1f} KB")
            
            # Warn if memory is low
            if free_mb < 10:
                print(f"   \033[31m⚠️  WARNING: Very low free memory ({free_mb:.1f} KB)!\033[0m")
                print(f"   \033[31m   Consider using PULSE_MODE_COMPILE = 0 to save ~2.5KB\033[0m")
            elif free_mb < 20:
                print(f"   \033[33m⚠️  Caution: Low free memory ({free_mb:.1f} KB)\033[0m")
        
        # Load protocol data for pulse detection (lightweight inspection)
        protocol_data = self._load_protocol_for_inspection()
        
        # Detect if protocol requires pulses by checking for pulse-related columns
        df_normalized = NormalizeSynonyms(protocol_data)
        pulse_col_indicators = ['_period', '_pulse_width', '_frequency', '_duty_cycle']
        protocol_requires_pulse = any(indicator in col for col in df_normalized.columns for indicator in pulse_col_indicators)
        
        print(f"\n🔍 Pulse mode detection:")
        print(f"   Protocol uses pulse parameters: {'YES' if protocol_requires_pulse else 'NO'}")
        
        # Verify pulse mode compatibility
        is_compatible = CheckPulseModeCompatibility(self.ser, protocol_requires_pulse)
        
        if not is_compatible:
            raise ValueError(
                "Pulse mode incompatibility: Protocol requires pulses but Arduino pulse mode is disabled. "
                "See error message above for solution."
            )
        
        # If verification is enabled, generate commands first to detect pattern length
        if verify_pattern_length:
            print("\n📏 Detecting pattern length from protocol...")
            self.generate_pattern_commands()
            
            # Detect maximum pattern length from commands
            max_pattern_length = self._detect_pattern_length_from_commands(self.cmd_patterns)
            
            # Detect maximum RAMP segments from commands
            max_ramp_segments = self._detect_max_ramp_segments_from_commands(self.cmd_patterns)
            
            # Check if we have any pattern or RAMP commands
            has_commands = max_pattern_length > 0 or max_ramp_segments > 0
            
            if has_commands:
                print(f"\n📏 Protocol pattern analysis:")
                if max_pattern_length > 0:
                    print(f"   Required PATTERN_LENGTH: {max_pattern_length}")
                if max_ramp_segments > 0:
                    print(f"   Required MAX_RAMP_SEGMENTS: {max_ramp_segments}")
                
                # Send greeting with pattern length verification
                arduino_config = SendGreeting(self.ser, expected_pattern_length=max_pattern_length,
                                              expected_max_ramp_segments=max_ramp_segments if max_ramp_segments > 0 else None)
                
                # Store arduino config for reference
                self.arduino_config = arduino_config
                
                # Get Arduino's PATTERN_LENGTH
                arduino_pl = arduino_config.get('pattern_length', 0)
                
                print(f"   Arduino PATTERN_LENGTH:  {arduino_pl}")
                
                # STRICT CHECK: Raise error if commands exceed Arduino capability
                if max_pattern_length > 0 and max_pattern_length > arduino_pl:
                    print(f"\n{'='*70}")
                    print("❌ ERROR: Pattern length exceeds Arduino capability!")
                    print(f"{'='*70}")
                    print(f"  Protocol requires: {max_pattern_length}")
                    print(f"  Arduino supports:  {arduino_pl}")
                    print(f"\nThe generated commands CANNOT be executed on this Arduino.")
                    print(f"Please update Arduino firmware PATTERN_LENGTH to {max_pattern_length} or higher.")
                    print(f"{'='*70}\n")
                    raise ValueError(
                        f"Pattern length mismatch: Protocol requires {max_pattern_length}, "
                        f"but Arduino only supports {arduino_pl}. "
                        f"Update Arduino PATTERN_LENGTH constant and re-upload firmware."
                    )
                
                # Check RAMP segments (already done in SendGreeting, but print confirmation)
                arduino_seg = arduino_config.get('max_ramp_segments', 0)
                if max_ramp_segments > 0 and arduino_seg > 0:
                    print(f"   Arduino MAX_RAMP_SEGMENTS: {arduino_seg}")
                
                print(f"   ✓ Verification passed\n")
            else:
                print("No pattern commands detected, skipping pattern length verification")
                SendGreeting(self.ser)
        else:
            # Just send greeting without verification
            SendGreeting(self.ser)
        
        return True
    
    def calibrate(self, t_send=None, use_v2=None, force_recalibrate=False):
        """
        Run Arduino time calibration with automatic database management.
        
        This method automatically:
        - Checks if calibration exists for this Arduino board
        - Uses stored calibration if available (unless forced)
        - Performs new calibration if needed
        - Saves calibration to database for future use
        
        Calibration Methods:
        - v1: Original method (Python measures Arduino wait time, dead sleep)
              Test times: [60,80,80,80]s, Total: 300s
              Best for: Backward compatibility
              
        - v11 (v1.1): V1.1 method (Python measures Arduino wait time, active polling)
                      Test times: [60,80,80,80]s, Total: 300s
                      Best for: Better responsiveness than V1, similar accuracy
               
        - v2: Multi-timestamp method (Arduino sends periodic timestamps)
              Duration: 300s with 10 samples (~30s intervals)
              Best for: Most accurate, excludes t=0 initialization overhead
              
        - v2_improved: Enhanced multi-timestamp method
                       Duration: 300s with 9 samples (~33s intervals)
                       Best for: Maximum accuracy with detailed diagnostics
        
        Args:
            t_send (list): DEPRECATED - kept for backward compatibility
            use_v2 (bool): DEPRECATED. Use calibration_method parameter during init instead.
                          If provided, overrides instance preference for backward compatibility.
            force_recalibrate (bool): Force new calibration even if stored one exists (default: False)
            
        Returns:
            float: Calibration factor (python_time / reference_time)
                   Factor > 1 means system is slower than reference
                   
        Example:
            # Use stored calibration automatically:
            parser = LightControllerParser('protocol.xlsx', calibration_method='v2')
            factor = parser.calibrate()  # Will use stored calibration if exists
            
            # Force new calibration:
            factor = parser.calibrate(force_recalibrate=True)
            
            # Or specify method during init:
            parser = LightControllerParser('protocol.xlsx', calibration_method='v1.1')
            factor = parser.calibrate()
        """
        # Run calibration if:
        # - calib_factor is None (not set)
        # - calib_factor is 1.0 (uncalibrated default)
        # - force_recalibrate is True
        needs_calibration = (
            self.calib_factor is None or 
            abs(self.calib_factor - 1.0) < 1e-9 or  # calib_factor == 1.0 (uncalibrated)
            force_recalibrate
        )
        
        if needs_calibration:
            from lcfunc import auto_calibrate_arduino
            
            # Determine which method to use
            if use_v2 is not None:
                # Backward compatibility: use_v2 parameter overrides instance preference
                method = 'v2' if use_v2 else 'v1'
            else:
                method = self.calibration_method
            
            # Normalize method name
            if method == 'v11':
                method = 'v1.1'
            
            print(f'\n{"="*70}')
            print(f'Arduino Calibration Manager')
            print(f'{"="*70}')
            print(f'Method: {method.upper()}')
            if force_recalibrate:
                print('Mode: Force recalibration')
            else:
                print('Mode: Auto (use stored if available)')
            print(f'{"="*70}\n')
            
            # Use automatic calibration management
            self.calib_factor, calibration_result = auto_calibrate_arduino(
                self.ser, 
                method=method,
                force_recalibrate=force_recalibrate
            )
        
        print(f'\n✓ Calibration factor: {self.calib_factor:.6f}')
        print(f'  Correction: {(self.calib_factor - 1) * 12 * 3600:.2f} seconds per 12 hours.\n')
        return self.calib_factor
    
    def parse_txt_protocol(self):
        """
        Parse TXT protocol file.
        
        Returns:
            tuple: (pattern_commands, start_time, wait_status, wait_pulse, loop, calib_factor)
        """
        print('Reading TXT protocol file...')
        # Read values from file into locals; do not unconditionally overwrite
        # an existing calibration factor (e.g. one provided by preview_only).
        cmd_patterns_raw, file_start_time, file_wait_status, file_wait_pulse, file_loop, file_calib = ReadTxtFile(self.protocol_file)

        # Accept file-provided start/wait/pulse/loop values
        self.start_time = file_start_time
        self.wait_status = file_wait_status
        self.wait_pulse = file_wait_pulse
        self.loop = file_loop

        # Only use file calibration if explicitly present; otherwise preserve
        # any existing self.calib_factor (set by preview_only or elsewhere).
        if file_calib is not None:
            self.calib_factor = file_calib
        else:
            if self.calib_factor is None:
                # Default to 1.0 (uncalibrated) if nothing has been set
                self.calib_factor = 1.0
        
        # Note: Calibration warning is deferred to after calibrate() is called
        # This allows auto-calibration lookup to happen first
        
        # Extract valid channels from start_time
        self.valid_channels = [ch for ch in self.start_time.keys() if self.start_time[ch] is not None]
        
        # Verify start time
        CheckStartTimeForChannels(self.start_time, self.valid_channels)
        
        # Print channel info
        for ch in self.valid_channels:
            pulse_info = ""
            if self.wait_pulse and ch in self.wait_pulse and self.wait_pulse[ch]:
                pulse_info = f", wait pulse: T{self.wait_pulse[ch]['period']}pw{self.wait_pulse[ch]['pw']}"
            print(f'{ch}: start time: {self.start_time[ch]}, wait status: {self.wait_status.get(ch, 0)}{pulse_info}.')
        
        # Filter out PATTERN:0 commands (will regenerate them)
        pattern_commands_raw = [cmd for cmd in cmd_patterns_raw if 'PATTERN:0;' not in cmd]
        
        # Convert TIME_S, TIME_M, TIME_H to TIME_MS
        pattern_commands_converted = ConvertTimeUnitsToMS(pattern_commands_raw)
        
        return pattern_commands_converted
    
    def parse_excel_protocol(self):
        """
        Parse Excel protocol file.
        
        Returns:
            tuple: (compressed_patterns, start_time, wait_status, calib_factor)
        """
        print('Reading Excel protocol file...')
        df_protocol, df_startTime, self.calib_factor = ReadExcelFile(self.protocol_file)
        
        # Note: Calibration warning is deferred to after calibrate() is called
        # This allows auto-calibration lookup to happen first
        
        channel_units, self.valid_channels = GetChannelInfo(df_protocol)
        self.start_time, self.wait_status = ReadStartTime(df_startTime)
        CheckStartTimeForChannels(self.start_time, self.valid_channels)
        df_ms = ConvertTimeToMillisecond(df_protocol, channel_units)
        
        # Print channel info
        for ch in self.valid_channels:
            print(f'{ch}: start time: {self.start_time[ch]}, wait status: {self.wait_status[ch]}.')
        
        return df_ms
    
    def _validate_pattern_capacity(self, commands):
        """
        Validate that the number of patterns per channel does not exceed Arduino capacity.
        
        Args:
            commands (list): List of command strings
            
        Raises:
            ValueError: If pattern count exceeds Arduino MAX_PATTERN_NUM for any channel
        """
        # Count patterns per channel
        pattern_count = {}
        
        for cmd in commands:
            # Pattern commands have format: CHANNEL:X;PATTERN_NUM:Y;...
            if 'PATTERN_NUM:' in cmd:
                # Extract channel number
                channel_match = cmd.split('CHANNEL:')
                if len(channel_match) > 1:
                    channel_str = channel_match[1].split(';')[0]
                    try:
                        channel = int(channel_str)
                        pattern_count[channel] = pattern_count.get(channel, 0) + 1
                    except ValueError:
                        pass
        
        if not pattern_count:
            # No patterns detected
            return
        
        # Get Arduino's MAX_PATTERN_NUM from config (if available)
        arduino_max_patterns = self.arduino_config.get('max_pattern_num', None)
        
        print(f"\n📊 Pattern count per channel:")
        for channel in sorted(pattern_count.keys()):
            count = pattern_count[channel]
            print(f"   Channel {channel}: {count} patterns", end='')
            
            if arduino_max_patterns is not None:
                print(f" (Arduino max: {arduino_max_patterns})", end='')
                if count > arduino_max_patterns:
                    print(" ❌ EXCEEDS LIMIT!")
                else:
                    print(" ✓")
            else:
                print(" (Arduino max: unknown)")
        
        # Strict validation if we know the Arduino limit
        if arduino_max_patterns is not None:
            exceeding_channels = {ch: count for ch, count in pattern_count.items() 
                                 if count > arduino_max_patterns}
            
            if exceeding_channels:
                print(f"\n{'='*70}")
                print("❌ ERROR: Pattern count exceeds Arduino capacity!")
                print(f"{'='*70}")
                for channel, count in exceeding_channels.items():
                    print(f"  Channel {channel}: {count} patterns (max: {arduino_max_patterns})")
                print(f"\nThe protocol CANNOT be executed on this Arduino.")
                print(f"Solutions:")
                print(f"  1. Increase MAX_PATTERN_NUM in Arduino firmware to {max(exceeding_channels.values())} or higher")
                print(f"  2. Simplify the protocol to use fewer patterns per channel")
                print(f"  3. Combine similar patterns or reduce pattern complexity")
                print(f"{'='*70}\n")
                raise ValueError(
                    f"Pattern count exceeds capacity: Channel(s) {list(exceeding_channels.keys())} "
                    f"require {max(exceeding_channels.values())} patterns, but Arduino only supports {arduino_max_patterns}. "
                    f"Update Arduino MAX_PATTERN_NUM constant and re-upload firmware."
                )
        else:
            print(f"\n   ⚠️  Note: Arduino MAX_PATTERN_NUM unknown (greeting didn't provide it)")
            print(f"   Cannot verify pattern capacity. Ensure patterns don't exceed Arduino limits.")

    def _warn_if_uncalibrated(self):
        """
        Issue a warning if calibration factor is still 1.0 after calibration lookup.
        This should be called AFTER calibrate() to allow auto-calibration lookup first.
        """
        if self.calib_factor is not None and abs(self.calib_factor - 1.0) < 1e-9:
            print('\n' + '='*70)
            print('⚠️  WARNING: Calibration factor is 1.000000')
            print('='*70)
            print('This indicates UNCALIBRATED time.')
            print('The protocol will use Arduino\'s internal timer without correction.')
            print('')
            print('For accurate timing:')
            print('  1. Run a calibration protocol first')
            print('  2. Note the calibration factor (typically 1.0 ± 0.01)')
            print('  3. Update CALIBRATION_FACTOR in your protocol file')
            print('')
            print('To calibrate: Use the calibrate() method with serial connection')
            print('='*70 + '\n')

    def _validate_value_ranges(self, commands):
        """
        Validate status values in commands against Arduino channel types.
        
        Warns about:
        - 8-bit values (2-255) used on 12-bit channels (low resolution)
        - Values >255 on 8-bit (PWM) channels (will be capped to 255)
        - Values >4095 on any channel (will be capped to channel max)
        
        Args:
            commands (list): List of command strings
        """
        import re
        
        # Get channel types from Arduino config
        channel_types = self.arduino_config.get('channel_types', '')
        if not channel_types:
            return  # Can't validate without channel type info
        
        low_resolution_warnings = []
        capping_warnings = []
        
        def check_value(val, ch_num, ch_type, context=""):
            """Check a single value and add appropriate warnings."""
            is_12bit = ch_type in ('D', 'M')  # DAC or MCP4728
            is_8bit = ch_type == 'P'  # PWM
            type_name = {'D': 'DAC', 'M': 'MCP4728', 'P': 'PWM', 'B': 'Binary'}.get(ch_type, ch_type)
            
            # Value > 4095: will be capped to channel max
            if val > 4095:
                max_val = 4095 if is_12bit else 255
                capping_warnings.append(
                    f"CH{ch_num} ({type_name}){context}: value {val} exceeds max, will be capped to {max_val}"
                )
            # Value 256-4095 on 8-bit channel: will be capped to 255
            elif val > 255 and is_8bit:
                capping_warnings.append(
                    f"CH{ch_num} ({type_name}/8-bit){context}: value {val} exceeds 255, will be capped to 255"
                )
            # Value 2-255 on 12-bit channel: low resolution warning
            elif 2 <= val <= 255 and is_12bit:
                low_resolution_warnings.append(
                    f"CH{ch_num} ({type_name}/12-bit){context}: value {val} is in 8-bit range. "
                    f"Use 0-4095 or 0.0-1.0 for full resolution."
                )
        
        for cmd in commands:
            # Parse channel number
            ch_match = re.search(r'CH:(\d+)', cmd)
            if not ch_match:
                continue
            ch_num = int(ch_match.group(1))
            ch_idx = ch_num - 1  # 0-based index
            
            if ch_idx >= len(channel_types):
                continue
            
            ch_type = channel_types[ch_idx]
            
            # Check STATUS values
            status_match = re.search(r'STATUS:([^;]+)', cmd)
            if status_match:
                status_str = status_match.group(1)
                for val_str in status_str.split(','):
                    val_str = val_str.strip()
                    if not val_str:
                        continue
                    
                    # Check if it's a normalized value (0.0-1.0)
                    if '.' in val_str:
                        try:
                            val = float(val_str)
                            if 0.0 <= val <= 1.0:
                                continue  # Normalized value is fine
                        except ValueError:
                            pass
                    
                    # Integer value check
                    try:
                        val = int(float(val_str))
                        check_value(val, ch_num, ch_type)
                    except ValueError:
                        pass
            
            # Check RAMP values
            ramp_match = re.search(r'RAMP:([^;]+)', cmd)
            if ramp_match:
                ramp_str = ramp_match.group(1)
                # Extract numeric values from ramp segments
                # Format: (L:0,255,10000) or (C:1200,1450,60000)
                segments = re.findall(r'\(([^)]+)\)', ramp_str)
                for seg in segments:
                    parts = seg.split(':')
                    if len(parts) >= 2:
                        params = parts[1].split('|')[0]  # Remove t_range if present
                        param_list = params.split(',')
                        if len(param_list) >= 2:
                            for val_str in param_list[:2]:  # start and end values
                                try:
                                    val = int(float(val_str))
                                    check_value(val, ch_num, ch_type, " RAMP")
                                except ValueError:
                                    pass
        
        # Print capping warnings (more serious - values will be changed)
        if capping_warnings:
            unique_capping = list(dict.fromkeys(capping_warnings))
            print(f"\n{'='*70}")
            print("⚠️  VALUE CAPPING WARNINGS")
            print(f"{'='*70}")
            for w in unique_capping[:10]:
                print(f"  • {w}")
            if len(unique_capping) > 10:
                print(f"  ... and {len(unique_capping) - 10} more warnings")
            print(f"\nNote: These values WILL BE CAPPED by Arduino to the channel's maximum.")
            print(f"      PWM (8-bit): max 255 | DAC/MCP4728 (12-bit): max 4095")
            print(f"{'='*70}\n")
        
        # Print low resolution warnings (informational)
        if low_resolution_warnings:
            unique_low_res = list(dict.fromkeys(low_resolution_warnings))
            print(f"\n{'='*70}")
            print("ℹ️  LOW RESOLUTION WARNINGS")
            print(f"{'='*70}")
            for w in unique_low_res[:10]:
                print(f"  • {w}")
            if len(unique_low_res) > 10:
                print(f"  ... and {len(unique_low_res) - 10} more warnings")
            print(f"\nNote: Values are accepted but may have lower resolution than expected.")
            print(f"      For 12-bit channels, use 0-4095 (integers) or 0.0-1.0 (normalized).")
            print(f"{'='*70}\n")

    def generate_pattern_commands(self):
        """
        Generate pattern commands based on file type.
        
        Returns:
            list: Generated pattern commands
        """
        if self.file_ext == '.txt':
            # Parse TXT file
            pattern_commands_converted = self.parse_txt_protocol()
            
            # Calibrate if serial connection is active
            if self.ser:
                self.calibrate()
            
            # Check for uncalibrated time AFTER calibrate() (which may load stored calibration)
            self._warn_if_uncalibrated()
            
            # Apply calibration to pattern commands
            self.cmd_patterns = ApplyCalibrationToTxtCommands(pattern_commands_converted, self.calib_factor)
            
        elif self.file_ext == '.xlsx':
            # Parse Excel file
            df_ms = self.parse_excel_protocol()
            
            # Calibrate if serial connection is active
            if self.ser:
                self.calibrate()
            
            # Check for uncalibrated time AFTER calibrate() (which may load stored calibration)
            self._warn_if_uncalibrated()
            
            # Evaluate compression efficiency for different pattern lengths
            print(f'\nEvaluating pattern compression efficiency...')
            test_lengths = [2, 4, 8] if self.pattern_length <= 8 else [2, 4, 8, self.pattern_length]
            compression_results = self._evaluate_pattern_compression(df_ms, pattern_lengths=test_lengths)
            
            # Find optimal pattern length
            valid_results = {pl: count for pl, count in compression_results.items() if count != float('inf')}
            optimal_pl = min(valid_results, key=valid_results.get) if valid_results else self.pattern_length
            
            print(f'Compression efficiency analysis:')
            for pl in sorted(compression_results.keys()):
                count = compression_results[pl]
                marker = ' ← optimal' if pl == optimal_pl else ''
                marker += ' ← given' if pl == self.pattern_length else ''
                if count == float('inf'):
                    print(f'  pattern_length={pl}: N/A (not compatible){marker}')
                else:
                    print(f'  pattern_length={pl}: {count} commands{marker}')
            
            # Compare given pattern_length with optimal
            if self.pattern_length != optimal_pl:
                print(f'\n💡 Note: Given pattern_length={self.pattern_length} generates {valid_results.get(self.pattern_length, "N/A")} commands')
                print(f'         Optimal pattern_length={optimal_pl} generates {valid_results[optimal_pl]} commands')
                if valid_results.get(self.pattern_length, float('inf')) > valid_results[optimal_pl]:
                    efficiency_loss = ((valid_results[self.pattern_length] - valid_results[optimal_pl]) / valid_results[optimal_pl]) * 100
                    print(f'         Using optimal would reduce commands by {efficiency_loss:.1f}%')
            
            # Correct time and compress patterns with given pattern_length
            df_corrected = CorrectTime(df_ms, self.calib_factor)
            compressed_patterns = FindRepeatedPatterns(df_corrected, pattern_length=self.pattern_length)
            self.cmd_patterns = GeneratePatternCommands(compressed_patterns)
        
        # Validate pattern count capacity (for both TXT and Excel)
        if self.cmd_patterns and self.arduino_config:
            self._validate_pattern_capacity(self.cmd_patterns)
            # Validate value ranges against channel types
            self._validate_value_ranges(self.cmd_patterns)
        
        return self.cmd_patterns
    
    def generate_wait_commands(self):
        """
        Generate wait commands based on start time and wait status.
        Uses channel types from Arduino configuration for proper value conversion.
        
        Returns:
            list: Generated wait commands
        """
        # Calculate countdown time
        time_countdown = CountDown(self.start_time)
        remaining_time_corrected = CorrectTime(time_countdown, self.calib_factor)
        
        # Get channel types and max values from Arduino config
        channel_types = self.arduino_config.get('channel_types', '')
        channel_max_values = self.arduino_config.get('channel_max_values', [])
        pwm_ramp_enabled = self.arduino_config.get('pwm_ramp_mode', True)
        
        # Generate wait commands with optional pulse support and channel-aware conversion
        wait_pulse_param = self.wait_pulse if self.wait_pulse else None
        self.cmd_wait = GenerateWaitCommands(
            self.wait_status, 
            remaining_time_corrected, 
            self.valid_channels, 
            wait_pulse_param,
            channel_types=channel_types,
            channel_max_values=channel_max_values,
            pwm_ramp_enabled=pwm_ramp_enabled
        )
        
        return self.cmd_wait
    
    def send_commands(self):
        """
        Send all commands to Arduino (pattern commands + wait commands + loop settings).
        
        Returns:
            bool: True if all commands sent successfully
        """
        if not self.ser:
            print("Error: Serial connection not established. Call setup_serial() first.")
            return False
        
        # Send pattern commands
        for cmd_t in self.cmd_patterns:
            SendCommand(self.ser, cmd_t)
        
        # Send wait commands
        for cmd_t in self.cmd_wait:
            SendCommand(self.ser, cmd_t)
        
        # Send LOOP commands if any channels have LOOP enabled
        if self.loop:
            for ch_name, loop_value in self.loop.items():
                if loop_value == 1:
                    # Extract channel number from 'CH1', 'CH2', etc.
                    ch_num = int(ch_name[2:]) if ch_name.startswith('CH') else int(ch_name)
                    loop_cmd = f"LOOP:CH:{ch_num}:VALUE:1\n"
                    SendCommand(self.ser, loop_cmd)
                    print(f"  🔄 LOOP enabled for {ch_name}")
        
        return True
    
    def get_channel_durations(self):
        """
        Calculate the total duration for each channel from pattern commands.
        This is used for LOOP tracking in the real-time monitor.
        
        Returns:
            dict: {'CH1': duration_ms, 'CH2': duration_ms, ...}
        """
        import re
        
        durations = {}
        for cmd in self.cmd_patterns:
            # Parse: PATTERN:1;CH:1;STATUS:0,1;TIME_MS:10000,10000;REPEATS:4
            # Or: PATTERN:1;CH:1;RAMP:(C:0,255,10000);REPEATS:1
            ch_match = re.search(r'CH:(\d+)', cmd)
            if not ch_match:
                continue
            
            ch_num = int(ch_match.group(1))
            ch_key = f'CH{ch_num}'
            
            if ch_key not in durations:
                durations[ch_key] = 0
            
            # Get repeats
            repeats_match = re.search(r'REPEATS:(\d+)', cmd)
            repeats = int(repeats_match.group(1)) if repeats_match else 1
            
            # Try to get TIME_MS
            time_match = re.search(r'TIME_MS:([\d,]+)', cmd)
            if time_match:
                times = [int(t) for t in time_match.group(1).split(',')]
                cycle_duration = sum(times)
                durations[ch_key] += cycle_duration * repeats
            else:
                # Try RAMP format: RAMP:(L:0,255,10000),(C:255,0,5000)
                ramp_match = re.search(r'RAMP:\(([^)]+)\)', cmd)
                if ramp_match:
                    # Find all ramp segments and sum their durations
                    ramp_str = cmd[cmd.find('RAMP:'):]
                    seg_pattern = re.findall(r'\(([^)]+)\)', ramp_str)
                    ramp_duration = 0
                    for seg_str in seg_pattern:
                        # Format: L:0,255,10000 or X:0,255,10000|0,2
                        parts = seg_str.split(':')
                        if len(parts) >= 2:
                            params = parts[1].split('|')[0]  # Remove t_range if present
                            param_parts = params.split(',')
                            if len(param_parts) >= 3:
                                ramp_duration += int(param_parts[2])  # duration is 3rd param
                    durations[ch_key] += ramp_duration * repeats
        
        return durations
    
    def preview(self, show_wait=True, show_patterns=True, max_commands=None):
        """
        Preview generated commands without sending to Arduino.
        Useful for validating protocols before hardware execution.
        
        Args:
            show_wait (bool): Show wait commands (default: True)
            show_patterns (bool): Show pattern commands (default: True)
            max_commands (int): Maximum commands to show (None = all)
            
        Returns:
            dict: Dictionary with 'wait_commands' and 'pattern_commands' lists
        """
        preview_data = {
            'wait_commands': [],
            'pattern_commands': [],
            'total_wait': len(self.cmd_wait),
            'total_patterns': len(self.cmd_patterns),
            'channels': self.valid_channels,
            'calib_factor': self.calib_factor
        }
        
        print('\n' + '='*70)
        print('                    COMMAND PREVIEW')
        print('='*70)
        print(f'\nProtocol File: {os.path.basename(self.protocol_file)}')
        print(f'File Type: {self.file_ext.upper()}')
        print(f'Channels: {", ".join(self.valid_channels)} ({len(self.valid_channels)} total)')
        print(f'Calibration Factor: {self.calib_factor:.5f}')
        print(f'Time Correction: {(self.calib_factor - 1) * 12 * 3600:.2f} sec per 12 hours')
        
        # Show start times
        print('\nStart Times:')
        for ch in self.valid_channels:
            time_val = self.start_time.get(ch)
            if isinstance(time_val, datetime.datetime):
                time_str = time_val.strftime('%Y-%m-%d %H:%M:%S')
            else:
                time_str = str(time_val)
            wait_stat = self.wait_status.get(ch, 0)
            print(f'  {ch}: {time_str} (wait: {wait_stat})')
        
        # Show wait commands
        if show_wait and self.cmd_wait:
            print('\n' + '-'*70)
            print(f'WAIT COMMANDS ({len(self.cmd_wait)} total)')
            print('-'*70)
            
            cmd_wait_commented = AddCommandDescriptions(self.cmd_wait)
            display_wait = cmd_wait_commented[:max_commands] if max_commands else cmd_wait_commented
            
            for i, cmd in enumerate(display_wait, 1):
                print(f'\n[{i}] {cmd.strip()}')
                preview_data['wait_commands'].append(cmd.strip())
            
            if max_commands and len(cmd_wait_commented) > max_commands:
                print(f'\n... and {len(cmd_wait_commented) - max_commands} more wait commands')
        
        # Show pattern commands
        if show_patterns and self.cmd_patterns:
            print('\n' + '-'*70)
            print(f'PATTERN COMMANDS ({len(self.cmd_patterns)} total)')
            print('-'*70)
            
            cmd_patterns_commented = AddCommandDescriptions(self.cmd_patterns)
            display_patterns = cmd_patterns_commented[:max_commands] if max_commands else cmd_patterns_commented
            
            for i, cmd in enumerate(display_patterns, 1):
                print(f'\n[{i}] {cmd.strip()}')
                preview_data['pattern_commands'].append(cmd.strip())
            
            if max_commands and len(cmd_patterns_commented) > max_commands:
                print(f'\n... and {len(cmd_patterns_commented) - max_commands} more pattern commands')
        
        print('\n' + '='*70)
        print(f'SUMMARY: {len(self.cmd_wait)} wait + {len(self.cmd_patterns)} pattern = {len(self.cmd_wait) + len(self.cmd_patterns)} total commands')
        print('='*70 + '\n')
        
        return preview_data
    
    def save_commands(self, output_dir=None):
        """
        Save all commands to a timestamped text file.
        
        Args:
            output_dir (str): Directory to save commands (default: same as protocol file)
            
        Returns:
            str: Path to saved commands file
        """
        protocol_path = os.path.abspath(self.protocol_file)
        protocol_name = os.path.basename(protocol_path)
        protocol_name_no_ext = os.path.splitext(protocol_name)[0]
        timestamp_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Determine output directory - default to same directory as protocol file
        if output_dir is None:
            output_dir = os.path.dirname(protocol_path)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Format start times
        start_time_str = {}
        for ch, t in self.start_time.items():
            if type(t) == datetime.datetime:
                start_time_str[ch] = t.strftime('%Y-%m-%d %H:%M:%S')
            else:
                start_time_str[ch] = str(t)
        
        # Add descriptive comments
        cmd_wait_commented = AddCommandDescriptions(self.cmd_wait)
        cmd_patterns_commented = AddCommandDescriptions(self.cmd_patterns)
        
        # Write to file
        commands_file = os.path.join(output_dir, f'{protocol_name_no_ext}_commands_{timestamp_str}.txt')
        with open(commands_file, 'w') as f:
            # Write header
            f.write('# ========================================\n')
            f.write('# Light Controller Command Log\n')
            f.write('# ========================================\n')
            f.write(f'# Protocol File: {protocol_name}\n')
            f.write(f'# Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'# Total Channels: {len(self.valid_channels)}\n')
            f.write(f'# Active Channels: {", ".join(self.valid_channels)}\n')
            f.write(f'# Calibration Factor: {self.calib_factor:.5f}\n')
            f.write(f'# Time Correction: {(self.calib_factor - 1) * 12 * 3600:.2f} seconds per 12 hours\n')
            
            # Write channel types (for visualization normalization)
            channel_types = self.arduino_config.get('channel_types', '')
            if channel_types:
                f.write(f'# Channel Types: {channel_types}\n')
            f.write('# ========================================\n')
            f.write('\n')
            
            # Write wait commands
            if cmd_wait_commented:
                f.write('# Wait Commands (countdown to start)\n')
                for cmd_t in cmd_wait_commented:
                    f.write(cmd_t)
                f.write('\n')
            
            # Write pattern commands
            if cmd_patterns_commented:
                f.write('# Pattern Commands (protocol execution)\n')
                for cmd_t in cmd_patterns_commented:
                    f.write(cmd_t)
                f.write('\n')
            
            # Write footer with execution info
            f.write('# ========================================\n')
            f.write('# Execution Info\n')
            f.write('# ========================================\n')
            for ch in self.valid_channels:
                f.write(f'# {ch} Start Time: {start_time_str.get(ch, "N/A")}\n')
                f.write(f'# {ch} Wait Status: {self.wait_status.get(ch, "N/A")}\n')
            
            # Write LOOP info (machine-readable format for viz_protocol_html.py)
            if self.loop:
                f.write(f'# LOOP: {self.loop}\n')
            f.write('# ========================================\n')
        
        print(f'Commands are written to {commands_file}.')
        return commands_file
    
    def parse_and_execute(self):
        """
        Complete workflow: parse protocol, generate commands, send to Arduino, and save.
        
        Returns:
            str: Path to saved commands file
        """
        # Generate pattern commands (skip if already generated during setup_serial)
        if not self.cmd_patterns:
            self.generate_pattern_commands()
        
        # Generate wait commands
        self.generate_wait_commands()
        
        # Send commands if serial connection is active
        if self.ser:
            self.send_commands()
        
        # Save commands
        commands_file = self.save_commands()
        
        return commands_file
    
    def preview_only(self, calib_factor=1.0, show_wait=True, show_patterns=True, max_commands=None):
        """
        Preview protocol without hardware connection.
        Perfect for testing and validating protocols.
        
        Args:
            calib_factor (float): Manual calibration factor (default: 1.0)
            show_wait (bool): Show wait commands (default: True)
            show_patterns (bool): Show pattern commands (default: True)
            max_commands (int): Maximum commands to show per type (None = all)
            
        Returns:
            dict: Preview data with commands and metadata
            
        Example:
            parser = LightControllerParser('protocol.xlsx')
            preview = parser.preview_only(calib_factor=1.00131, max_commands=5)
        """
        # Set calibration factor
        self.calib_factor = calib_factor
        
        # Generate commands without hardware
        self.generate_pattern_commands()
        self.generate_wait_commands()
        
        # Show preview
        preview_data = self.preview(show_wait=show_wait, show_patterns=show_patterns, max_commands=max_commands)
        
        return preview_data
    
    def start_live_monitor(self, update_interval_ms=100, max_points=500):
        """
        Start real-time live plotting dashboard to monitor channel values.
        
        This runs a Dash web server that displays real-time channel values
        as the protocol executes on the Arduino.
        
        Args:
            update_interval_ms: Refresh rate in milliseconds (default: 100ms = 10Hz)
            max_points: Maximum data points to display (default: 500)
        """
        if not DASH_AVAILABLE:
            print("❌ Dash not available for real-time plotting.")
            print("   Install with: pip install dash plotly")
            print("   Falling back to console-only mode...")
            return self._console_monitor()
        
        if not self.ser:
            print("❌ No serial connection available for monitoring")
            return
        
        print("\n" + "="*60)
        print("🚀 Starting REAL-TIME Live Plot Dashboard...")
        print("="*60)
        print(f"   Open your browser to: http://127.0.0.1:8050")
        print("   Press Ctrl+C to stop monitoring")
        print("="*60 + "\n")
        
        # Initialize monitoring data
        self._live_data_lock = threading.Lock()
        self._live_running = True
        self._max_live_points = max_points
        self._channel_data = {}
        self._data_points_received = 0
        self._monitor_start_time = time.time()
        
        # Channel max values from Arduino config
        self._channel_max_values = {}
        if self.arduino_config:
            ch_max_list = self.arduino_config.get('channel_max_values', [])
            for i, max_val in enumerate(ch_max_list, 1):
                self._channel_max_values[i] = max_val
        
        # Start serial reading in background thread
        serial_thread = threading.Thread(target=self._live_serial_reader, daemon=True)
        serial_thread.start()
        
        # Create Dash app
        app = Dash(__name__)
        
        app.layout = html.Div([
            html.H1("🌈 Light Controller - Real-Time Monitor", 
                    style={'textAlign': 'center', 'color': '#667eea'}),
            html.Div(id='status-bar', style={
                'textAlign': 'center', 
                'padding': '10px',
                'backgroundColor': '#f0f0f0',
                'marginBottom': '20px',
                'borderRadius': '5px'
            }),
            dcc.Graph(id='live-graph', style={'height': '70vh'}),
            dcc.Interval(
                id='interval-component',
                interval=update_interval_ms,
                n_intervals=0
            )
        ], style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'})
        
        @app.callback(
            [Output('live-graph', 'figure'),
             Output('status-bar', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_graph(n):
            with self._live_data_lock:
                data_copy = {ch: {'times': list(d['times']), 'values': list(d['values'])} 
                            for ch, d in self._channel_data.items()}
                points = self._data_points_received
            
            num_channels = len(data_copy) if data_copy else 4
            fig = make_subplots(
                rows=num_channels, cols=1,
                subplot_titles=[f"Channel {i}" for i in range(1, num_channels + 1)],
                shared_xaxes=True,
                vertical_spacing=0.08
            )
            
            colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe', '#43e97b']
            
            if data_copy:
                for idx, ch in enumerate(sorted(data_copy.keys()), 1):
                    d = data_copy[ch]
                    times = d['times'][-self._max_live_points:]
                    values = d['values'][-self._max_live_points:]
                    
                    # Get max value for this channel
                    max_val = self._channel_max_values.get(ch, 255)
                    
                    fig.add_trace(
                        go.Scatter(
                            x=times,
                            y=values,
                            name=f'Ch {ch}',
                            mode='lines',
                            fill='tozeroy',
                            line=dict(color=colors[(ch-1) % len(colors)], width=2)
                        ),
                        row=idx, col=1
                    )
                    fig.update_yaxes(range=[0, max_val * 1.05], row=idx, col=1)
            else:
                for idx in range(1, 5):
                    fig.add_trace(go.Scatter(x=[], y=[], name=f'Ch {idx}'), row=idx, col=1)
                    max_val = self._channel_max_values.get(idx, 255)
                    fig.update_yaxes(range=[0, max_val * 1.05], row=idx, col=1)
            
            fig.update_layout(
                hovermode='x unified',
                showlegend=False,
                margin=dict(l=60, r=30, t=40, b=40),
                paper_bgcolor='white',
                plot_bgcolor='#fafafa'
            )
            fig.update_xaxes(title_text="Time (seconds)", row=num_channels, col=1)
            
            elapsed = time.time() - self._monitor_start_time
            status = f"⏱️ Running for {elapsed:.1f}s | 📊 {points} data points | 🔄 Refresh: {update_interval_ms}ms"
            
            return fig, status
        
        try:
            # Open browser automatically
            import webbrowser
            webbrowser.open('http://127.0.0.1:8050')
            app.run(debug=False, use_reloader=False)
        except KeyboardInterrupt:
            print("\n⏹️  Stopping live monitor...")
        finally:
            self._live_running = False
            self._print_monitor_summary()
    
    def _live_serial_reader(self):
        """Background thread for reading serial data during live plotting."""
        while self._live_running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if not line:
                        continue
                    
                    # Parse $CHMON: messages
                    channel_values = self._parse_channel_monitor(line)
                    
                    if channel_values:
                        with self._live_data_lock:
                            self._update_monitor_data(channel_values)
                    else:
                        # Print non-channel messages (like Arrivederci)
                        if not line.startswith('$') and line:
                            print(f"  Arduino: {line}")
                else:
                    time.sleep(0.01)
            except Exception as e:
                if self._live_running:
                    pass  # Silently ignore errors during shutdown
                time.sleep(0.1)
    
    def _parse_channel_monitor(self, line):
        """
        Parse channel monitor message from Arduino.
        Format: $CHMON:CH1:pwm1,CH2:pwm2,CH3:pwm3,CH4:pwm4
        
        Returns: dict {channel_num: pwm_value} or None
        """
        if not line.startswith('$CHMON:'):
            return None
        
        try:
            data_str = line[7:]  # Remove '$CHMON:' prefix
            channels = {}
            
            for ch_data in data_str.split(','):
                parts = ch_data.split(':')
                if len(parts) == 2:
                    ch_name = parts[0]
                    pwm_value = int(parts[1])
                    ch_num = int(ch_name[2:])
                    channels[ch_num] = pwm_value
            
            return channels if channels else None
        except:
            return None
    
    def _update_monitor_data(self, channels):
        """Update stored channel data for live plotting."""
        elapsed_s = time.time() - self._monitor_start_time
        
        for ch_num, pwm_value in channels.items():
            if ch_num not in self._channel_data:
                self._channel_data[ch_num] = {'times': [], 'values': []}
            
            data = self._channel_data[ch_num]
            data['times'].append(elapsed_s)
            data['values'].append(pwm_value)
            
            # Limit data points
            if len(data['times']) > self._max_live_points * 2:
                data['times'] = data['times'][-self._max_live_points:]
                data['values'] = data['values'][-self._max_live_points:]
        
        self._data_points_received += 1
    
    def _console_monitor(self):
        """Fallback console-based monitoring when Dash is not available."""
        if not self.ser:
            print("❌ No serial connection available for monitoring")
            return
        
        print("\n📊 Console Monitoring (Ctrl+C to stop)...")
        print("   Install dash for graphical monitoring: pip install dash plotly\n")
        
        start_time = time.time()
        last_print = 0
        
        try:
            while True:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if line.startswith('$CHMON:'):
                        channels = self._parse_channel_monitor(line)
                        if channels and time.time() - last_print > 0.5:
                            elapsed = time.time() - start_time
                            status = f"⏱️ {elapsed:6.1f}s | "
                            for ch in sorted(channels.keys()):
                                pwm = channels[ch]
                                max_val = self._channel_max_values.get(ch, 255)
                                bar_len = int(pwm / max_val * 10)
                                bar = '█' * bar_len + '░' * (10 - bar_len)
                                status += f"CH{ch}: {pwm:4d} [{bar}] | "
                            print(status)
                            last_print = time.time()
                    elif not line.startswith('$') and line:
                        print(f"  Arduino: {line}")
                
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped")
    
    def _print_monitor_summary(self):
        """Print monitoring summary."""
        print(f"\n📊 Monitoring Summary:")
        print(f"   Data points received: {self._data_points_received}")
        print(f"   Total duration: {time.time() - self._monitor_start_time:.1f}s")
        print(f"   Channels monitored: {len(self._channel_data)}")
    
    def close(self):
        """
        Close serial connection and cleanup.
        """
        if self.ser:
            SayBye(self.ser)
            self.ser.close()
            self.ser = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __del__(self):
        """Destructor - ensure serial port is closed."""
        if self.ser:
            try:
                self.ser.close()
            except:
                pass


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Light Controller Protocol Parser - Upload and monitor LED control protocols',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                      # Interactive mode with file picker
  %(prog)s protocol.txt                         # Run protocol file
  %(prog)s protocol.txt --live-plot             # Run with real-time visualization
  %(prog)s protocol.txt --port /dev/cu.usbmodem14301 --live-plot
  %(prog)s protocol.txt -y                      # Auto-confirm prompts
  %(prog)s --port COM3 --baud 115200            # Specify port and baud rate
        """
    )
    
    parser.add_argument('protocol', nargs='?', default=None,
                        help='Protocol file (.txt or .xlsx). Opens file picker if not specified.')
    parser.add_argument('--port', '-p', default=None,
                        help='Serial port (auto-detect if not specified)')
    parser.add_argument('--baud', '-b', type=int, default=9600,
                        help='Baud rate (default: 9600)')
    parser.add_argument('--live-plot', action='store_true',
                        help='Enable real-time live plotting after uploading protocol')
    parser.add_argument('--refresh-rate', type=int, default=100,
                        help='Live plot refresh rate in ms (default: 100)')
    parser.add_argument('--no-monitor', action='store_true',
                        help='Skip monitoring after upload (just upload and exit)')
    parser.add_argument('--skip-check', action='store_true',
                        help='Skip memory and pulse mode compatibility checks (use when Arduino is stuck/unresponsive)')
    parser.add_argument('-y', '--yes', action='store_true',
                        help='Auto-confirm all prompts (non-interactive mode)')
    
    return parser.parse_args()


def main():
    """
    Main function with command-line argument support.
    Supports --live-plot for real-time visualization after uploading protocol.
    """
    args = parse_args()
    
    # Set auto-confirm mode via environment variable if -y/--yes is specified
    if args.yes:
        os.environ['LIGHT_CONTROLLER_AUTO_CONFIRM'] = '1'
    
    print('Welcome to use the light controller!')
    
    # Determine protocol file
    protocol_file = args.protocol
    if not protocol_file:
        import tkinter as tk
        from tkinter import filedialog
        
        print('Please select your protocol file...')
        root = tk.Tk()
        root.withdraw()
        protocol_file = filedialog.askopenfilename(
            title='Select the protocol file',
            filetypes=[('Protocol files', '*.xlsx *.txt'), ('Excel files', '*.xlsx'), ('Text files', '*.txt')]
        )
        
        if not protocol_file:
            print('No file selected. Exiting.')
            return
    
    try:
        # Create parser instance
        parser = LightControllerParser(protocol_file)
        
        # Setup serial connection with optional port override and skip checks
        if not parser.setup_serial(board_type='Arduino', baudrate=args.baud, 
                                    port_override=args.port, skip_checks=args.skip_check):
            raise ValueError('Serial port is not available.')
        
        # Parse and execute
        commands_file = parser.parse_and_execute()
        print(f'\nProtocol execution completed successfully!')
        print(f'Commands saved to: {commands_file}')
        
        # Live monitoring after upload
        if args.live_plot and not args.no_monitor:
            print('\nStarting live monitor...')
            parser.start_live_monitor(update_interval_ms=args.refresh_rate)
        elif not args.no_monitor:
            # Default: simple console monitoring until exit
            print('\n📊 Monitoring channel values (Ctrl+C or close terminal to exit)...')
            print('   Use --live-plot for graphical visualization')
            print('   Use --no-monitor to skip monitoring\n')
            
            # Initialize monitoring attributes
            parser._monitor_start_time = time.time()
            parser._channel_max_values = {}
            if parser.arduino_config:
                ch_max_list = parser.arduino_config.get('channel_max_values', [])
                for i, max_val in enumerate(ch_max_list, 1):
                    parser._channel_max_values[i] = max_val
            
            try:
                last_print = 0
                while True:
                    if parser.ser and parser.ser.in_waiting > 0:
                        line = parser.ser.readline().decode('utf-8', errors='ignore').strip()
                        
                        if line.startswith('$CHMON:'):
                            channels = parser._parse_channel_monitor(line)
                            if channels and time.time() - last_print > 0.3:
                                elapsed = time.time() - parser._monitor_start_time
                                status = f"⏱️ {elapsed:6.1f}s | "
                                for ch in sorted(channels.keys()):
                                    pwm = channels[ch]
                                    max_val = parser._channel_max_values.get(ch, 255)
                                    bar_len = int(pwm / max_val * 10)
                                    bar = '█' * bar_len + '░' * (10 - bar_len)
                                    status += f"CH{ch}: {pwm:4d} [{bar}] | "
                                print(status)
                                last_print = time.time()
                        elif line == 'Arrivederci':
                            print(f"  Arduino: {line}")
                            print("\n✓ Protocol execution completed on Arduino")
                            break
                        elif not line.startswith('$') and line:
                            print(f"  Arduino: {line}")
                    
                    time.sleep(0.01)
            except KeyboardInterrupt:
                print("\n⏹️  Monitoring stopped")
        
        # Cleanup
        if parser.ser:
            parser.ser.close()
            parser.ser = None
            print("✓ Serial connection closed")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'\nError: {e}\n')
        print('Program is terminated.')
    finally:
        try:
            input('\nPress <Enter> to exit: ')
        except (KeyboardInterrupt, EOFError):
            pass


if __name__ == '__main__':
    main()
