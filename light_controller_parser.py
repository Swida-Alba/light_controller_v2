"""
Light Controller Parser - A class-based interface for parsing and executing LED control protocols.

This module provides a clean, object-oriented interface to replace the functional approach
in protocol_parser.py. It encapsulates all protocol parsing, validation, calibration,
and command generation logic.

Usage:
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
import datetime
from lcfunc import *


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
        self.cmd_patterns = []
        self.cmd_wait = []
        self.arduino_config = {}  # Arduino configuration from greeting
        
        # Validate file extension
        if self.file_ext not in ['.txt', '.xlsx']:
            raise ValueError(f'Unsupported file format: {self.file_ext}. Please use .xlsx or .txt files.')
    
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
    
    def setup_serial(self, board_type='Arduino', baudrate=9600, verify_pattern_length=True, **kwargs):
        """
        Setup serial connection to Arduino with optional pattern length verification.
        
        Args:
            board_type (str): Type of Arduino board
            baudrate (int): Serial baud rate
            verify_pattern_length (bool): Verify Arduino PATTERN_LENGTH matches protocol requirements (default: True)
            **kwargs: Additional serial port parameters
            
        Returns:
            bool: True if connection successful, False otherwise
            
        Raises:
            ValueError: If pattern length verification fails
        """
        self.ser = SetUpSerialPort(board_type=board_type, baudrate=baudrate, **kwargs)
        if not self.ser:
            return False
        
        # Clear buffer
        ClearSerialBuffer(self.ser, print_flag=True)
        
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
            
            if max_pattern_length > 0:
                print(f"\n📏 Protocol pattern analysis:")
                print(f"   Required PATTERN_LENGTH: {max_pattern_length}")
                
                # Send greeting with pattern length verification
                arduino_config = SendGreeting(self.ser, expected_pattern_length=max_pattern_length)
                
                # Store arduino config for reference
                self.arduino_config = arduino_config
                
                # Get Arduino's PATTERN_LENGTH
                arduino_pl = arduino_config.get('pattern_length', 0)
                
                print(f"   Arduino PATTERN_LENGTH:  {arduino_pl}")
                
                # STRICT CHECK: Raise error if commands exceed Arduino capability
                if max_pattern_length > arduino_pl:
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
        if self.calib_factor is None:
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
            tuple: (pattern_commands, start_time, wait_status, wait_pulse, calib_factor)
        """
        print('Reading TXT protocol file...')
        cmd_patterns_raw, self.start_time, self.wait_status, self.wait_pulse, self.calib_factor = ReadTxtFile(self.protocol_file)
        
        # Check for uncalibrated time and issue warning
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
        
        # Check for uncalibrated time and issue warning
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
            print('  3. Update the calibration sheet in your Excel file')
            print('')
            print('To calibrate: Use the calibrate() method with serial connection')
            print('='*70 + '\n')
        
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
            
            # Apply calibration to pattern commands
            self.cmd_patterns = ApplyCalibrationToTxtCommands(pattern_commands_converted, self.calib_factor)
            
        elif self.file_ext == '.xlsx':
            # Parse Excel file
            df_ms = self.parse_excel_protocol()
            
            # Calibrate if serial connection is active
            if self.ser:
                self.calibrate()
            
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
        
        return self.cmd_patterns
    
    def generate_wait_commands(self):
        """
        Generate wait commands based on start time and wait status.
        
        Returns:
            list: Generated wait commands
        """
        # Calculate countdown time
        time_countdown = CountDown(self.start_time)
        remaining_time_corrected = CorrectTime(time_countdown, self.calib_factor)
        
        # Generate wait commands with optional pulse support
        wait_pulse_param = self.wait_pulse if self.wait_pulse else None
        self.cmd_wait = GenerateWaitCommands(self.wait_status, remaining_time_corrected, 
                                            self.valid_channels, wait_pulse_param)
        
        return self.cmd_wait
    
    def send_commands(self):
        """
        Send all commands to Arduino (pattern commands + wait commands).
        
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
        
        return True
    
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
            
            # Write footer
            f.write('# ========================================\n')
            f.write('# Execution Info\n')
            f.write('# ========================================\n')
            for ch in self.valid_channels:
                f.write(f'# {ch} Start Time: {start_time_str.get(ch, "N/A")}\n')
                f.write(f'# {ch} Wait Status: {self.wait_status.get(ch, "N/A")}\n')
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


def main():
    """
    Main function demonstrating usage of LightControllerParser class.
    This replaces the complex main code in protocol_parser.py.
    """
    import tkinter as tk
    from tkinter import filedialog
    
    print('Welcome to use the light controller!')
    
    try:
        # Select protocol file
        print('Please select your protocol file...')
        protocol_file = filedialog.askopenfilename(
            title='Select the protocol file',
            filetypes=[('Protocol files', '*.xlsx *.txt'), ('Excel files', '*.xlsx'), ('Text files', '*.txt')]
        )
        
        if not protocol_file:
            print('No file selected. Exiting.')
            return
        
        # Create parser instance (using context manager for automatic cleanup)
        with LightControllerParser(protocol_file) as parser:
            # Setup serial connection
            if not parser.setup_serial(board_type='Arduino', baudrate=9600):
                raise ValueError('Serial port is not available.')
            
            # Parse and execute
            commands_file = parser.parse_and_execute()
            print(f'\nProtocol execution completed successfully!')
            print(f'Commands saved to: {commands_file}')
            
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
