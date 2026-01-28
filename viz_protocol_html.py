#!/usr/bin/env python
"""
HTML Protocol Visualizer with Real-Time Status Indicator

Generates interactive HTML visualization with current status overlay.
Shows where each channel is in the protocol timeline based on current time.

Usage:
    python viz_protocol_html.py commands.txt
    python viz_protocol_html.py commands.txt --start-time "2025-11-08 20:30:00"
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
import re


def safe_print(msg='', *args, **kwargs):
    """Print safely to consoles that can't encode certain Unicode characters.

    Tries a normal print first; on UnicodeEncodeError it encodes using the
    stdout encoding with 'replace' for unencodable chars and prints that.
    """
    try:
        print(msg, *args, **kwargs)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, 'encoding', None) or 'utf-8'
        try:
            b = msg.encode(enc, errors='replace')
            print(b.decode(enc), *args, **kwargs)
        except Exception:
            print(msg.encode('ascii', 'replace').decode('ascii'), *args, **kwargs)


def format_time(ms):
    """Convert milliseconds to DD:HH:mm:ss format."""
    total_seconds = int(ms / 1000)
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    return f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_pattern_states(pattern):
    """Format pattern states for display, handling RAMP patterns specially."""
    if pattern.get('is_ramp') and pattern.get('ramp_segments'):
        # Show RAMP segment info: mode:start→end
        segments = pattern['ramp_segments']
        parts = []
        for seg in segments:
            mode = seg.get('mode', 'L')
            start = seg.get('start_pwm', seg.get('start', 0))
            end = seg.get('end_pwm', seg.get('end', 255))
            parts.append(f"{mode}:{start}→{end}")
        return ', '.join(parts)
    else:
        # Regular STATUS pattern - show PWM values
        return str(pattern.get('status', []))


def format_pattern_times(pattern):
    """Format pattern times for display, handling RAMP patterns specially."""
    if pattern.get('is_ramp') and pattern.get('ramp_segments'):
        # Show RAMP segment durations
        segments = pattern['ramp_segments']
        times = []
        for seg in segments:
            duration = seg.get('duration_ms', seg.get('duration', 0))
            times.append(format_time(duration))
        return times
    else:
        # Regular STATUS pattern
        return [format_time(t) for t in pattern.get('time_ms_original', [])]


def format_section_time(ms):
    """Format time dynamically based on duration:
    - HH:mm:SS.sss if >= 1 hour
    - mm:SS.sss if >= 1 minute
    - SS.sss + unit if < 1 minute
    """
    total_seconds = ms / 1000.0
    
    if total_seconds >= 3600:  # >= 1 hour
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
    elif total_seconds >= 60:  # >= 1 minute
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:06.3f}"
    else:  # < 1 minute
        return f"{total_seconds:.3f}s"


def parse_commands(commands_file):
    """Parse commands file and extract pattern data, calibration factor, loop info, and channel types."""
    channels = {}
    calib_factor = 1.0  # Default calibration factor
    loop_info = {}  # LOOP settings per channel
    channel_types = ''  # Channel types string (e.g., 'MMMM' for 4 MCP4728 channels)
    
    with open(commands_file, 'r') as f:
        lines = f.readlines()
    
    # First, extract calibration factor, LOOP info, and channel types from header
    for line in lines:
        if line.startswith('# Calibration Factor:'):
            try:
                calib_factor = float(line.split(':')[1].strip())
            except (ValueError, IndexError):
                pass
        elif line.startswith('# LOOP:'):
            try:
                import ast
                loop_str = line.split('# LOOP:', 1)[1].strip()
                loop_info = ast.literal_eval(loop_str)
            except (ValueError, SyntaxError, IndexError):
                pass
        elif line.startswith('# Channel Types:'):
            try:
                channel_types = line.split(':', 1)[1].strip()
            except (IndexError):
                pass
    
    # Then parse commands
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('CONFIG'):
            continue
        
        if not line.startswith('PATTERN:'):
            continue
        
        # Parse command components
        ch_match = re.search(r'CH:(\d+)', line)
        if not ch_match:
            continue
        
        ch_num = int(ch_match.group(1))
        if ch_num not in channels:
            channels[ch_num] = []
        
        pattern_match = re.search(r'PATTERN:(\d+)', line)
        repeats_match = re.search(r'REPEATS:(\d+)', line)
        pulse_match = re.search(r'PULSE:([^;\n]*)', line)
        
        # Check for RAMP command (new format)
        ramp_match = re.search(r'RAMP:([^;]+)', line)
        # STATUS can include decimal values (0.2) for normalized values
        status_match = re.search(r'STATUS:([\d.,]+)', line)
        time_match = re.search(r'TIME_MS:([\d.,]+)', line)
        
        if not pattern_match or not repeats_match:
            continue
        
        pattern_num = int(pattern_match.group(1))
        repeats = int(repeats_match.group(1))
        
        pulse_str = pulse_match.group(1).strip() if pulse_match else ''
        has_pulse = pulse_str and pulse_str not in ['', ',']
        
        if ramp_match:
            # Parse RAMP command
            ramp_str = ramp_match.group(1).strip()
            ramp_data = parse_ramp_for_visualization(ramp_str)
            
            channels[ch_num].append({
                'pattern': pattern_num,
                'status': [0],  # Placeholder, actual values from ramp
                'time_ms': [ramp_data['total_duration_ms']],
                'time_ms_original': [ramp_data['total_duration_ms'] * calib_factor],
                'repeats': repeats,
                'pulse': pulse_str if has_pulse else None,
                'is_ramp': True,
                'ramp_segments': ramp_data['segments'],
                'ramp_total_duration': ramp_data['total_duration_ms']
            })
        elif status_match and time_match:
            # Standard STATUS/TIME_MS command - preserve original values (can be float like 1.0)
            status_str = status_match.group(1)
            status_list = []
            for s in status_str.split(','):
                s = s.strip()
                # Keep as float if it has decimal point, otherwise int
                if '.' in s:
                    status_list.append(float(s))
                else:
                    status_list.append(int(s))
            
            time_list = [float(t) for t in time_match.group(1).split(',')]
            
            channels[ch_num].append({
                'pattern': pattern_num,
                'status': status_list,
                'time_ms': time_list,
                # Recover requested (python) times from stored Arduino TIME_MS by multiplying
                # python_time = calib_factor * arduino_time
                'time_ms_original': [t * calib_factor for t in time_list],
                'repeats': repeats,
                'pulse': pulse_str if has_pulse else None,
                'is_ramp': False
            })
    
    # Convert loop_info keys from 'CH1' to 1 (int) to match channels dict
    loop_channels = {}
    for ch_name, loop_val in loop_info.items():
        if ch_name.startswith('CH'):
            ch_num = int(ch_name[2:])
            loop_channels[ch_num] = loop_val
    
    return channels, calib_factor, loop_channels, channel_types


def convert_binary_to_intensity(value, ch_max):
    """
    Convert a status value to actual intensity, treating integer 0/1 as binary HIGH/LOW.
    
    This matches the Arduino firmware behavior where:
    - Integer 0 = OFF (value 0)
    - Integer 1 = ON (full intensity = ch_max: 255 for PWM, 4095 for DAC)
    - Float 0.0-1.0 = Normalized (scaled to ch_max)
    - Integer 2-255 or 2-4095 = Actual intensity value
    
    Args:
        value: Raw status value (int or float)
        ch_max: Maximum value for the channel (255 for PWM, 4095 for DAC)
    
    Returns:
        int: Actual intensity value (0 to ch_max)
    """
    # Normalized float (0.0-1.0) with decimal point - scale to max
    if isinstance(value, float) and 0.0 <= value <= 1.0:
        # Check if it's truly normalized (has fractional part or is exactly 0.0/1.0)
        if value == 0.0:
            return 0
        elif value == 1.0:
            return ch_max
        else:  # Has fractional part like 0.5
            return int(round(value * ch_max))
    
    # Integer values
    int_value = int(value)
    
    # Binary HIGH/LOW: integer 0 or 1
    if int_value == 0:
        return 0
    if int_value == 1:
        return ch_max  # Full intensity
    
    # Actual intensity value (2 and above)
    return min(int_value, ch_max)


def get_channel_max_value(ch_num, channel_types):
    """
    Get the maximum value for a channel based on its type.
    
    Args:
        ch_num: Channel number (1-based)
        channel_types: String of channel types (e.g., 'MMMM', 'PPPP', 'PMMD')
    
    Returns:
        int: Maximum value (1 for Binary, 255 for PWM, 4095 for DAC/MCP4728)
    """
    if not channel_types or ch_num > len(channel_types):
        return 255  # Default to PWM
    
    ch_type = channel_types[ch_num - 1]  # 0-based index
    if ch_type == 'B':
        return 1
    elif ch_type in ('D', 'M'):
        return 4095
    else:  # 'P' or unknown
        return 255


def normalize_status_value(value, ch_num, channel_types):
    """
    Normalize a status value to 0.0-1.0 range based on channel type.
    
    Args:
        value: Raw status value (can be int or float 0.0-1.0)
        ch_num: Channel number (1-based)
        channel_types: String of channel types
    
    Returns:
        float: Normalized value 0.0-1.0
    """
    max_val = get_channel_max_value(ch_num, channel_types)
    
    # Already normalized (0.0-1.0 float)
    if isinstance(value, float) and 0.0 <= value <= 1.0:
        return value
    
    # Convert to normalized
    return min(1.0, value / max_val)


def denormalize_status_value(normalized_value, ch_num, channel_types):
    """
    Convert a normalized value (0.0-1.0) to the channel's actual range.
    
    Args:
        normalized_value: Value in 0.0-1.0 range
        ch_num: Channel number (1-based)
        channel_types: String of channel types
    
    Returns:
        int: Actual value in channel's range
    """
    max_val = get_channel_max_value(ch_num, channel_types)
    return int(round(normalized_value * max_val))


def parse_ramp_for_visualization(ramp_str):
    """
    Parse RAMP command string for visualization.
    
    Supports both old and new formats:
    - Old: 0,255,10000,100,L
    - New: (L:0,255,10000),(X:0,255,5000|0,2)
    
    Returns dict with segments info for plotting.
    """
    import math
    
    segments = []
    total_duration = 0
    
    # Check if new format (starts with parenthesis)
    if ramp_str.startswith('('):
        # New format: (L:0,255,1000),(X:0,255,10000|1,2)
        # Find all segments in parentheses
        seg_pattern = re.findall(r'\(([^)]+)\)', ramp_str)
        
        for seg_str in seg_pattern:
            # Parse mode:params
            colon_pos = seg_str.find(':')
            if colon_pos == -1:
                continue
            
            mode = seg_str[:colon_pos].strip()
            params_str = seg_str[colon_pos + 1:].strip()
            
            # Check for t_range (after |)
            t_start, t_end = 0.0, 1.0
            if '|' in params_str:
                params_str, t_range_str = params_str.split('|', 1)
                t_parts = t_range_str.split(',')
                if len(t_parts) >= 2:
                    t_start = float(t_parts[0])
                    t_end = float(t_parts[1])
            
            # Parse numeric params: start,end,duration[,steps]
            parts = params_str.split(',')
            if len(parts) >= 3:
                start_pwm = int(parts[0])
                end_pwm = int(parts[1])
                duration_ms = int(parts[2])
                steps = int(parts[3]) if len(parts) >= 4 else max(10, duration_ms // 50)
                
                # Set default t_range based on mode if not custom
                if mode in ['O', '3']:  # Ease-out
                    if t_start == 0.0 and t_end == 1.0:
                        t_start, t_end = 1.0, 2.0
                
                segments.append({
                    'mode': mode,
                    'start_pwm': start_pwm,
                    'end_pwm': end_pwm,
                    'duration_ms': duration_ms,
                    'steps': steps,
                    't_start': t_start,
                    't_end': t_end,
                    'offset_ms': total_duration
                })
                total_duration += duration_ms
    else:
        # Old format: start,end,duration,steps,mode or segments separated by |
        old_segments = ramp_str.split('|')
        
        for seg_str in old_segments:
            seg_str = seg_str.strip()
            if not seg_str:
                continue
            
            parts = seg_str.split(',')
            if len(parts) >= 4:
                start_pwm = int(parts[0])
                end_pwm = int(parts[1])
                duration_ms = int(parts[2])
                steps = int(parts[3])
                mode = parts[4].strip() if len(parts) >= 5 else 'L'
                
                # Check for t_range in remaining parts
                t_start, t_end = 0.0, 1.0
                if len(parts) >= 7:
                    t_start = float(parts[5])
                    t_end = float(parts[6])
                elif mode in ['O', '3']:
                    t_start, t_end = 1.0, 2.0
                
                segments.append({
                    'mode': mode,
                    'start_pwm': start_pwm,
                    'end_pwm': end_pwm,
                    'duration_ms': duration_ms,
                    'steps': steps,
                    't_start': t_start,
                    't_end': t_end,
                    'offset_ms': total_duration
                })
                total_duration += duration_ms
    
    return {
        'segments': segments,
        'total_duration_ms': total_duration
    }


def calculate_current_position(channels, start_time):
    """
    Calculate current position in protocol for each channel.
    
    Returns dict with channel positions:
    {
        channel_num: {
            'elapsed_ms': time since start,
            'current_pattern': pattern index,
            'current_cycle': cycle number,
            'current_state': state index,
            'state_elapsed_ms': time in current state,
            'status': 0 or 1 (OFF/ON),
            'is_pulsing': bool,
            'completed': bool
        }
    }
    """
    now = datetime.now()
    elapsed = (now - start_time).total_seconds() * 1000  # ms since start
    
    positions = {}
    
    for ch_num, patterns in channels.items():
        current_time = 0
        position = {
            'elapsed_ms': elapsed,
            'current_pattern': -1,
            'current_cycle': 0,
            'current_state': 0,
            'state_elapsed_ms': 0,
            'status': 0,
            'is_pulsing': False,
            'completed': False
        }
        
        # Find where we are in the timeline - use uncalibrated/original times
        for p_idx, pattern in enumerate(patterns):
            cycle_duration = sum(pattern['time_ms_original'])
            total_duration = cycle_duration * pattern['repeats']

            if current_time + total_duration > elapsed:
                # We're in this pattern
                position['current_pattern'] = p_idx
                time_in_pattern = elapsed - current_time

                # Find which cycle
                cycle_num = int(time_in_pattern / cycle_duration)
                position['current_cycle'] = cycle_num

                # Find which state within the cycle
                time_in_cycle = time_in_pattern % cycle_duration
                state_time = 0
                for s_idx, state_duration in enumerate(pattern['time_ms_original']):
                    if state_time + state_duration > time_in_cycle:
                        position['current_state'] = s_idx
                        position['state_elapsed_ms'] = time_in_cycle - state_time
                        position['status'] = pattern['status'][s_idx]
                        position['is_pulsing'] = pattern['pulse'] and position['status'] == 1
                        break
                    state_time += state_duration
                break

            current_time += total_duration
        else:
            # Completed all patterns
            position['completed'] = True
        
        positions[ch_num] = position
    
    return positions


def generate_html(channels, positions, output_file, upload_time=None, channel_start_times=None, loop_info=None, channel_types='', calib_factor=1.0):
    """Generate interactive HTML visualization with real-time status.
    
    All time calculations and position updates are done in JavaScript for independence.
    Python only provides the initial data structure and upload time.
    
    Args:
        channels: Dict of channel patterns
        positions: Not used anymore - kept for backwards compatibility
        output_file: Path to output HTML file
        upload_time: When commands were uploaded to Arduino
        channel_start_times: Dict of per-channel start times (for display only)
        loop_info: Dict of per-channel loop settings (0=no loop, 1=loop forever)
        channel_types: String of channel types (e.g., 'MMMM', 'PPPP')
        calib_factor: Calibration factor to convert real time to calibrated time
    """
    
    import json
    from datetime import datetime
    
    # Default loop_info to empty dict
    if loop_info is None:
        loop_info = {}
    
    # Get current time for initial display only
    now = datetime.now()
    
    # Prepare data for JavaScript - only static data
    channels_json = json.dumps(channels)
    loop_info_json = json.dumps(loop_info)
    channel_types_json = json.dumps(channel_types)
    
    # Prepare upload time for JavaScript
    if upload_time:
        upload_time_str = upload_time.strftime("%Y-%m-%d %H:%M:%S")
    else:
        upload_time_str = None
    
    # Convert channel_start_times to simple strings for display
    channel_start_times_display = {}
    if channel_start_times:
        for ch_num, start_time in channel_start_times.items():
            channel_start_times_display[ch_num] = start_time.strftime("%Y-%m-%d %H:%M:%S")
    
    channel_start_times_json = json.dumps(channel_start_times_display)
    
    # Build intensity data for plotting
    # Supports multiple value ranges: binary (0-1), PWM (0-255), DAC (0-4095)
    # For LOOP channels, skip pattern 0 (wait pattern) since Arduino skips it after first cycle
    channel_intensity_data = {}
    for ch_num, patterns in channels.items():
        segments = []
        # Check if this channel has LOOP enabled
        channel_has_loop = loop_info.get(ch_num, 0) == 1
        # Get channel max value for normalization
        ch_max = get_channel_max_value(ch_num, channel_types)
        for pattern in patterns:
            # Skip wait pattern (pattern 0) for LOOP channels in intensity timeline
            if channel_has_loop and pattern.get('pattern', -1) == 0:
                continue
            repeats = pattern.get('repeats', 1)
            pulse_str = pattern.get('pulse', None)
            
            if pattern.get('is_ramp') and pattern.get('ramp_segments'):
                # RAMP patterns: Convert values treating integer 0/1 as binary HIGH/LOW
                for _ in range(repeats):
                    for seg in pattern['ramp_segments']:
                        start_val = seg.get('start_pwm', seg.get('start', 0))
                        end_val = seg.get('end_pwm', seg.get('end', 255))
                        # Convert binary 0/1 to actual intensity
                        start_val = convert_binary_to_intensity(start_val, ch_max)
                        end_val = convert_binary_to_intensity(end_val, ch_max)
                        segments.append({
                            'start': start_val,
                            'end': end_val,
                            'duration': seg.get('duration_ms', seg.get('duration', 1000)),
                            'mode': seg.get('mode', 'L'),
                            't_start': seg.get('t_start', 0),
                            't_end': seg.get('t_end', 1),
                            'max_value': ch_max
                        })
            else:
                # STATUS patterns: Pass through actual values
                # Supports binary (0/1), PWM (0-255), or DAC (0-4095)
                # Normalized values (0.0-1.0) are converted to channel range
                # Parse pulse parameters if present: T{period}pw{width}
                pulse_params = []
                if pulse_str:
                    import re
                    pulse_parts = pulse_str.split(',')
                    for p in pulse_parts:
                        match = re.match(r'T(\d+)pw(\d+)', p.strip())
                        if match:
                            pulse_params.append({
                                'period': int(match.group(1)),
                                'width': int(match.group(2))
                            })
                        else:
                            pulse_params.append(None)  # No pulse for this status
                
                for _ in range(repeats):
                    for i, (status, time_ms) in enumerate(zip(pattern.get('status', [0]), pattern.get('time_ms_original', [1000]))):
                        # Convert status to actual intensity value
                        # Integer 0/1 treated as binary HIGH/LOW (0/max)
                        # Float 0.0-1.0 treated as normalized (scaled to max)
                        # Integer 2+ treated as actual intensity
                        value = convert_binary_to_intensity(status, ch_max)
                        
                        # Check if this status has pulse
                        pulse_param = pulse_params[i] if i < len(pulse_params) else None
                        
                        if value > 0 and pulse_param and pulse_param.get('period', 0) > 0:
                            # Generate pulse waveform segments
                            period_ms = pulse_param['period']
                            width_ms = pulse_param['width']
                            remaining_ms = time_ms
                            
                            while remaining_ms > 0:
                                # ON phase
                                on_duration = min(width_ms, remaining_ms)
                                if on_duration > 0:
                                    segments.append({
                                        'start': value, 'end': value,
                                        'duration': on_duration,
                                        'mode': 'L', 't_start': 0, 't_end': 1,
                                        'max_value': ch_max
                                    })
                                    remaining_ms -= on_duration
                                
                                # OFF phase
                                off_duration = min(period_ms - width_ms, remaining_ms)
                                if off_duration > 0:
                                    segments.append({
                                        'start': 0, 'end': 0,
                                        'duration': off_duration,
                                        'mode': 'L', 't_start': 0, 't_end': 1,
                                        'max_value': ch_max
                                    })
                                    remaining_ms -= off_duration
                        else:
                            # No pulse - constant level
                            segments.append({
                                'start': value,
                                'end': value,
                                'duration': time_ms,
                                'mode': 'L',
                                't_start': 0,
                                't_end': 1,
                                'max_value': ch_max
                            })
        
        if segments:
            channel_intensity_data[ch_num] = segments
    
    channel_intensity_json = json.dumps(channel_intensity_data)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Protocol Visualization - Light Controller v2.3</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 30px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 20px;
        }}
        
        .header h1 {{
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            color: #666;
            font-size: 1.2em;
        }}
        
        .status-panel {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        
        .status-panel h2 {{
            margin-bottom: 15px;
            font-size: 1.8em;
        }}
        
        .status-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-top: 15px;
        }}
        
        @media (max-width: 1200px) {{
            .status-grid {{
                grid-template-columns: repeat(3, 1fr);
            }}
        }}
        
        @media (max-width: 900px) {{
            .status-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        @media (max-width: 600px) {{
            .status-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .channel-status {{
            background: rgba(255,255,255,0.15);
            padding: 12px;
            border-radius: 8px;
            backdrop-filter: blur(10px);
            border: 2px solid rgba(255,255,255,0.3);
        }}
        
        .channel-status h3 {{
            font-size: 1.1em;
            margin-bottom: 8px;
        }}
        
        .status-indicator {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 6px 0;
        }}
        
        .status-led {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            box-shadow: 0 0 10px currentColor;
            animation: pulse 1s ease-in-out infinite;
        }}
        
        .status-led.on {{
            background: #00ff00;
            color: #00ff00;
        }}
        
        .status-led.ramping {{
            background: linear-gradient(135deg, #00ff00, #00bcd4);
            color: #00ff00;
            animation: ramp-pulse 2s ease-in-out infinite;
        }}
        
        .status-led.off {{
            background: #555;
            color: #555;
            animation: none;
        }}
        
        .status-led.pulsing {{
            background: #ffaa00;
            color: #ffaa00;
            animation: pulse 0.5s ease-in-out infinite;
        }}
        
        .status-led.completed {{
            background: #4CAF50;
            color: #4CAF50;
            animation: none;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        @keyframes ramp-pulse {{
            0%, 100% {{ opacity: 1; box-shadow: 0 0 10px #00ff00; }}
            50% {{ opacity: 0.8; box-shadow: 0 0 20px #00bcd4; }}
        }}
        
        .channels-container {{
            display: grid;
            /* Default: 2 columns for better readability */
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        /* Wider columns for single channel */
        .channels-container.cols-1 {{
            grid-template-columns: 1fr;
        }}
        
        @media (max-width: 900px) {{
            .channels-container {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .channel-section {{
            background: #f9f9f9;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .channel-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        
        .channel-header h2 {{
            font-size: 1.8em;
        }}
        
        .pattern-block {{
            background: white;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            position: relative;
        }}
        
        .pattern-block.current {{
            border-left-color: #ff6b6b;
            background: #fff5f5;
            box-shadow: 0 4px 15px rgba(255,107,107,0.3);
        }}
        
        .pattern-block.current::before {{
            content: '▶ CURRENT';
            position: absolute;
            top: -10px;
            right: 20px;
            background: #ff6b6b;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .pattern-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .pattern-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }}
        
        .pattern-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
            font-size: 0.95em;
        }}
        
        .info-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .info-label {{
            font-weight: bold;
            color: #666;
        }}
        
        .timeline {{
            background: #f5f5f5;
            border-radius: 5px;
            padding: 15px;
            margin-top: 15px;
        }}
        
        .timeline-row {{
            margin: 8px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .timeline-label {{
            width: 80px;
            font-weight: bold;
            color: #666;
        }}
        
        .timeline-bar {{
            flex: 1;
            height: 30px;
            display: flex;
            border: 2px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
            position: relative;
        }}
        
        .timeline-segment {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
            color: white;
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
            position: relative;
        }}
        
        .timeline-segment.on {{
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        }}
        
        .timeline-segment.off {{
            background: linear-gradient(135deg, #9e9e9e 0%, #757575 100%);
        }}
        
        .timeline-segment.pulsing {{
            background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
            animation: shimmer 1s ease-in-out infinite;
        }}
        
        .current-position {{
            position: absolute;
            top: -5px;
            bottom: -5px;
            width: 3px;
            background: red;
            box-shadow: 0 0 10px red;
            z-index: 10;
        }}
        
        .current-position::after {{
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 12px;
            height: 12px;
            background: red;
            border-radius: 50%;
            box-shadow: 0 0 15px red;
        }}
        
        @keyframes shimmer {{
            0%, 100% {{ filter: brightness(1); }}
            50% {{ filter: brightness(1.3); }}
        }}
        
        .legend {{
            display: flex;
            gap: 20px;
            margin-top: 10px;
            flex-wrap: wrap;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .legend-box {{
            width: 30px;
            height: 20px;
            border-radius: 3px;
        }}
        
        .summary {{
            background: #f0f0f0;
            padding: 20px;
            border-radius: 10px;
            margin-top: 30px;
        }}
        
        .summary h2 {{
            margin-bottom: 15px;
            color: #333;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        
        .summary-item {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .summary-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .summary-label {{
            color: #666;
            margin-top: 5px;
        }}
        
        .timestamp {{
            text-align: center;
            color: #666;
            margin-top: 20px;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔦 Protocol Timeline Visualization</h1>
            <div class="subtitle">Light Controller v2.3</div>
        </div>
        
        <div class="status-panel">
            <h2>🔴 LIVE STATUS - {now.strftime('%Y-%m-%d %H:%M:%S')}</h2>
"""
    
    if upload_time:
        elapsed = (now - upload_time).total_seconds()
        html += f"""
            <div style="margin-bottom: 15px;">
                <strong>Upload Time:</strong> {upload_time.strftime('%Y-%m-%d %H:%M:%S')} 
                <strong style="margin-left: 20px;">Elapsed:</strong> {format_time(elapsed * 1000)}
            </div>
"""
        
        # Show per-channel start times
        if channel_start_times:
            html += """
            <div style="margin-top: 10px; font-size: 0.9em; color: #bbb;">
                <strong>Channel Start → End Times:</strong><br>
"""
            for ch_num in sorted(channel_start_times.keys()):
                ch_start = channel_start_times[ch_num]
                # Calculate channel total duration excluding any wait pattern (pattern 0)
                ch_total_ms_excl_wait = 0
                for p in channels.get(ch_num, []):
                    if p.get('pattern', None) == 0:
                        # skip wait pattern when computing end time
                        continue
                    ch_total_ms_excl_wait += sum(p['time_ms_original']) * p['repeats']

                ch_end = ch_start + timedelta(milliseconds=ch_total_ms_excl_wait)
                html += f"""                CH{ch_num}: {ch_start.strftime('%Y-%m-%d %H:%M:%S')} → {ch_end.strftime('%Y-%m-%d %H:%M:%S')}<br>
"""
            html += """
            </div>
"""
    
    html += """
            <div class="status-grid">
"""
    
    # Generate status cards for each channel (will be updated dynamically by JavaScript)
    for ch_num in sorted(channels.keys()):
        # Calculate initial status to avoid "Loading..." flicker
        initial_status = "..."
        initial_led_class = "off"
        if upload_time:
            elapsed_ms = (now - upload_time).total_seconds() * 1000
            # Quick check if channel is in pattern 0 (waiting) - use uncalibrated/original times
            if len(channels[ch_num]) > 0 and channels[ch_num][0]['pattern'] == 0:
                pattern_0_duration = sum(channels[ch_num][0]['time_ms_original']) * channels[ch_num][0]['repeats']
                if elapsed_ms < pattern_0_duration:
                    initial_status = "⏰ WAITING"
                    initial_led_class = "off"
        
        html += f"""
                <div class="channel-status">
                    <h3>Channel {ch_num}</h3>
                    <div class="status-indicator">
                        <div class="status-led {initial_led_class}"></div>
                        <strong>{initial_status}</strong>
                    </div>
                    <div style="font-size: 0.9em; margin-top: 10px;">
                        <div>Pattern: --</div>
                        <div>Cycle: --</div>
                        <div>Elapsed: --:--:--</div>
                        <div>Left: <span id="ch{ch_num}_left">--:--:--</span></div>
                    </div>
                </div>
"""
    
    html += """
            </div>
        </div>
"""
    
    # Determine column class based on channel count
    num_channels = len(channels)
    if num_channels == 1:
        cols_class = "cols-1"
    else:
        cols_class = ""  # Default 2 columns for 2+ channels
    
    html += f"""
    <div class="channels-container {cols_class}">
"""
    
    # Generate channel timelines
    for ch_num in sorted(channels.keys()):
        html += f"""
        <div class="channel-section" id="channel-{ch_num}-section">
            <div class="channel-header">
                <h2>Channel {ch_num}</h2>
            </div>
"""
        
        current_time = 0
        current_time_orig = 0
        
        for p_idx, pattern in enumerate(channels[ch_num]):
            # Don't set current class statically - let JavaScript handle it dynamically

            # Use original (uncalibrated) times for all visualization math
            cycle_duration_orig = sum(pattern['time_ms_original']) if pattern['time_ms_original'] else 0
            
            # For RAMP patterns, cycle_duration_orig may be 0 - use total_duration instead
            if cycle_duration_orig == 0 and pattern.get('total_duration', 0) > 0:
                cycle_duration_orig = pattern['total_duration']
            
            total_duration_orig = cycle_duration_orig * pattern['repeats'] if cycle_duration_orig > 0 else 0
            
            # Check if this is a wait pattern (pattern 0)
            is_wait_pattern = (pattern['pattern'] == 0)
            
            # Determine header time display: absolute datetimes if upload_time provided,
            # otherwise keep relative duration display.
            if upload_time:
                pat_start_dt = upload_time + timedelta(milliseconds=current_time_orig)
                pat_end_dt = pat_start_dt + timedelta(milliseconds=total_duration_orig)
                start_str = pat_start_dt.strftime('%Y-%m-%d %H:%M:%S')
                end_str = pat_end_dt.strftime('%Y-%m-%d %H:%M:%S')
                time_display = f"{start_str} → {end_str}"
            else:
                time_display = f"{format_time(current_time_orig)} → {format_time(current_time_orig + total_duration_orig)}"

            html += f"""
            <div class="pattern-block">
                <div class="pattern-header">
                    <div class="pattern-title">Pattern {pattern["pattern"]}</div>
                    <div style="color: #666;">
                        {time_display}
                    </div>
                </div>
                
                <div class="pattern-info">
                    <div class="info-item">
                        <span class="info-label">Duration:</span>
                        <span>{format_time(total_duration_orig)}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">{'RAMP:' if pattern.get('is_ramp') else 'States:'}</span>
                        <span>{format_pattern_states(pattern)}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Times:</span>
                        <span>{format_pattern_times(pattern)}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Repeats:</span>
                        <span>{pattern['repeats']}x</span>
                    </div>

                    <div class="info-item">
                        <span class="info-label">Pattern Left:</span>
                        <span id="ch{ch_num}_pat{p_idx}_left">--:--:--</span>
                    </div>
"""
            
            if pattern['pulse']:
                html += """
                    <div class="info-item">
                        <span class="info-label">Pulse:</span>
                        <span>✓ Active</span>
                    </div>
"""
            
            html += """
                </div>
"""
            
            # Show cycle timeline for ALL patterns (including pattern 0)
            html += """
                <div class="timeline">
                    <div class="timeline-label">Cycle Pattern:</div>
"""
            # Show only ONE cycle with cycle counter
            html += f"""
                    <div class="timeline-row">
                        <div class="timeline-label">
                            <span id="ch{ch_num}_pat{p_idx}_cycle">Cycle 1/{pattern['repeats']}</span>
                        </div>
                        <div class="timeline-bar" id="ch{ch_num}_pat{p_idx}_timeline">
"""
            
            # Add timeline segments for all patterns (use uncalibrated/original durations)
            if pattern.get('is_ramp') and pattern.get('ramp_segments'):
                # RAMP pattern - show gradient segments
                ramp_total = pattern.get('ramp_total_duration', 0) or sum(seg.get('duration_ms', seg.get('duration', 1000)) for seg in pattern['ramp_segments'])
                for s_idx, seg in enumerate(pattern['ramp_segments']):
                    duration = seg.get('duration_ms', seg.get('duration', 1000))
                    start_pwm = seg.get('start_pwm', seg.get('start', 0))
                    end_pwm = seg.get('end_pwm', seg.get('end', 255))
                    mode = seg.get('mode', 'L')
                    
                    width_percent = (duration / ramp_total * 100) if ramp_total > 0 else 100
                    
                    # Create gradient color based on PWM values (0=dark, 255=bright green)
                    start_brightness = int(50 + (start_pwm / 255) * 150)  # 50-200
                    end_brightness = int(50 + (end_pwm / 255) * 150)
                    
                    html += f'''
                            <div class="timeline-segment" style="width: {width_percent}%; 
                                background: linear-gradient(90deg, rgb({start_brightness}, {start_brightness + 50}, {start_brightness//2}) 0%, rgb({end_brightness}, {end_brightness + 50}, {end_brightness//2}) 100%);
                                border: 1px solid #4CAF50;" title="{mode}: {start_pwm}→{end_pwm}">
                                <span style="font-size:10px; color:#fff; text-shadow: 1px 1px 1px #000;">{mode}</span>
                            </div>
'''
            else:
                for s_idx, (state, duration) in enumerate(zip(pattern['status'], pattern['time_ms_original'])):
                    # Avoid division by zero for RAMP patterns with empty time_ms_original
                    if cycle_duration_orig > 0:
                        width_percent = (duration / cycle_duration_orig) * 100
                    else:
                        width_percent = 100  # Single segment takes full width
                    
                    # Determine max value based on likely channel type (4095 for DAC, 255 for PWM)
                    # Check if any value > 255 to detect DAC mode
                    max_val = 255
                    for s in pattern['status']:
                        if isinstance(s, (int, float)) and s > 255:
                            max_val = 4095
                            break
                    
                    # Handle different value types: binary (0/1), normalized (0.0-1.0), direct PWM/DAC
                    if pattern['pulse'] and (state == 1 or state == 1.0):
                        state_class = 'pulsing'
                        state_text = '≈'
                    elif state == 1 or state == 1.0:
                        state_class = 'on'
                        state_text = f'MAX'
                    elif state == 0:
                        state_class = 'off'
                        state_text = '░'
                    elif isinstance(state, float) and 0 < state < 1:
                        # Normalized float value (0.0-1.0)
                        brightness = int(50 + state * 150)
                        pct = int(state * 100)
                        state_class = 'pwm'
                        state_text = f'{pct}%'
                        html += f'''
                            <div class="timeline-segment" style="width: {width_percent}%; 
                                background: rgb({brightness}, {brightness + 50}, {brightness//2});
                                border: 1px solid #4CAF50; color: #fff; font-size: 10px; text-shadow: 1px 1px 1px #000;" title="Normalized: {state:.2f} ({pct}%)">
                                {state_text}
                            </div>
'''
                        continue
                    else:
                        # Direct PWM (0-255) or DAC (0-4095) value
                        norm_val = state / max_val if max_val > 0 else 0
                        brightness = int(50 + norm_val * 150)
                        state_class = 'pwm'
                        state_text = str(int(state))
                        html += f'''
                            <div class="timeline-segment" style="width: {width_percent}%; 
                                background: rgb({brightness}, {brightness + 50}, {brightness//2});
                                border: 1px solid #4CAF50; color: #fff; font-size: 10px; text-shadow: 1px 1px 1px #000;" title="Value: {state}">
                                {state_text}
                            </div>
'''
                        continue
                    
                    html += f"""
                            <div class="timeline-segment {state_class}" style="width: {width_percent}%">
                                {state_text}
                            </div>
"""
            
            html += """
                        </div>
                    </div>
"""
            
            # Add legend for all patterns
            html += """
                    <div class="legend">
                        <div class="legend-item">
                            <div class="legend-box" style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);"></div>
                            <span>ON █</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-box" style="background: linear-gradient(135deg, #9e9e9e 0%, #757575 100%);"></div>
                            <span>OFF ░</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-box" style="background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);"></div>
                            <span>PULSING ≈</span>
                        </div>
                    </div>
"""
            
            # Close timeline div for both wait and normal patterns
            html += """
                </div>
            </div>
"""
            
            current_time += total_duration_orig  # keep current_time in calibrated units unused, but advance by original
            current_time_orig += total_duration_orig
        
        # Add intensity plot for ALL channels (unified visualization for all patterns)
        # Show square wave for ON/OFF, smooth ramp for RAMP, constant for PWM
        html += f"""
            <div class="intensity-plot-container" style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 10px;">
                <h3 style="margin-bottom: 10px; color: #667eea;">📈 Intensity Timeline</h3>
                <div id="intensity-plot-ch{ch_num}" style="width: 100%; height: 250px;"></div>
            </div>
"""
        
        # Close channel section
        html += """
        </div>
"""
    
    # Close channels container
    html += """
    </div>
    
    """
    
    # Total duration summary
    html += """
        <div style="text-align: right; font-size: 1.2em; font-weight: bold; color: #667eea; margin-top: 10px;">
"""
    
    # Calculate total duration for all channels (use original times for display)
    max_duration = 0
    for ch_num in channels.keys():
        ch_duration = sum(sum(p['time_ms_original']) * p['repeats'] for p in channels[ch_num])
        if ch_duration > max_duration:
            max_duration = ch_duration
    
    html += f"""
            <div style="text-align: right; font-size: 1.2em; font-weight: bold; color: #667eea; margin-top: 10px;">
                Total Duration: {format_time(max_duration)}
            </div>
        </div>
"""
    
    # Summary
    total_patterns = sum(len(patterns) for patterns in channels.values())
    
    html += f"""
        <div class="summary">
            <h2>📊 Summary</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-value">{len(channels)}</div>
                    <div class="summary-label">Total Channels</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{total_patterns}</div>
                    <div class="summary-label">Total Patterns</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{format_time(max_duration)}</div>
                    <div class="summary-label">Maximum Duration</div>
                </div>
            </div>
        </div>
        
        <div class="timestamp">
            Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
    
    <script>
        // Channel data and timing configuration
        const channelsData = {channels_json};
        const uploadTimeStr = {json.dumps(upload_time_str)};
        const uploadTime = uploadTimeStr ? new Date(uploadTimeStr) : null;
        
        // LOOP configuration per channel (0=no loop, 1=loop forever)
        const loopInfo = {loop_info_json};
        
        // Channel types from Arduino config (e.g., 'MMMM' for 4 MCP4728 channels)
        // P=PWM (0-255), D=DAC (0-4095), M=MCP4728 (0-4095), B=Binary (0-1)
        const channelTypes = {channel_types_json};
        
        // Helper function to get max value for a channel
        function getChannelMaxValue(chNum) {{
            if (!channelTypes || chNum > channelTypes.length) return 255;
            const chType = channelTypes[chNum - 1];
            if (chType === 'B') return 1;
            if (chType === 'D' || chType === 'M') return 4095;
            return 255;  // PWM or unknown
        }}
        
        // Helper function to get channel type name
        function getChannelTypeName(chNum) {{
            if (!channelTypes || chNum > channelTypes.length) return 'PWM';
            const chType = channelTypes[chNum - 1];
            const typeNames = {{ 'P': 'PWM', 'D': 'DAC', 'M': 'MCP4728', 'B': 'Binary' }};
            return typeNames[chType] || 'PWM';
        }}
        
        // Calibration factor: real_time * calib_factor = calibrated_time (timeline time)
        const calibFactor = {calib_factor};
        
        // Channel start times (upload_time + wait_time per channel) - for display only
        const channelStartTimesRaw = {channel_start_times_json};
        const channelStartTimes = {{}};
        for (const [ch, timeStr] of Object.entries(channelStartTimesRaw)) {{
            channelStartTimes[ch] = new Date(timeStr);
        }}

        // Precompute per-pattern start offsets and durations for each channel
        const channelsMeta = {{}};
        Object.keys(channelsData).forEach(chNum => {{
            const channel = channelsData[chNum];
            let offset = 0;
            const starts = [];
            const durations = [];

            channel.forEach((p, idx) => {{
                const cycle = p.time_ms_original.reduce((a, b) => a + b, 0);
                const dur = cycle * p.repeats;
                starts.push(offset);
                durations.push(dur);
                offset += dur;
            }});

            channelsMeta[chNum] = {{ starts: starts, durations: durations, total: offset }};
        }});
        
        // Format milliseconds to DD:HH:mm:ss format
        function formatTime(ms) {{
            const totalSeconds = Math.floor(ms / 1000);
            const days = Math.floor(totalSeconds / 86400);
            const hours = Math.floor((totalSeconds % 86400) / 3600);
            const minutes = Math.floor((totalSeconds % 3600) / 60);
            const seconds = totalSeconds % 60;
            
            return String(days).padStart(2, '0') + ':' + 
                   String(hours).padStart(2, '0') + ':' + 
                   String(minutes).padStart(2, '0') + ':' + 
                   String(seconds).padStart(2, '0');
        }}
        
        // Format section time dynamically based on duration
        function formatSectionTime(ms) {{
            const totalSeconds = ms / 1000.0;
            
            if (totalSeconds >= 3600) {{  // >= 1 hour
                const hours = Math.floor(totalSeconds / 3600);
                const minutes = Math.floor((totalSeconds % 3600) / 60);
                const seconds = totalSeconds % 60;
                return String(hours).padStart(2, '0') + ':' + 
                       String(minutes).padStart(2, '0') + ':' + 
                       seconds.toFixed(3).padStart(6, '0');
            }} else if (totalSeconds >= 60) {{  // >= 1 minute
                const minutes = Math.floor(totalSeconds / 60);
                const seconds = totalSeconds % 60;
                return String(minutes).padStart(2, '0') + ':' + 
                       seconds.toFixed(3).padStart(6, '0');
            }} else {{  // < 1 minute
                return totalSeconds.toFixed(3) + 's';
            }}
        }}
        
        // Parse pulse parameters from pattern
        function parsePulseParams(pulseStr) {{
            // Check if pulseStr is valid and is a string
            if (!pulseStr || typeof pulseStr !== 'string' || pulseStr === '' || pulseStr === ',') {{
                return null;
            }}
            
            // Parse pulse format: "Tperiod_pw_pulsewidth,Tperiod_pw_pulsewidth"
            // Example: "T998pw99,T0pw0" means period=998ms, pulsewidth=99ms for state1
            const parts = pulseStr.split(',');
            const result = [];
            
            for (const part of parts) {{
                if (!part || part === '') {{
                    result.push(null);
                    continue;
                }}
                
                // Match pattern like "T998pw99"
                const match = part.match(/T(\\d+)pw(\\d+)/);
                if (match) {{
                    const period = parseInt(match[1]);
                    const pulsewidth = parseInt(match[2]);
                    const frequency = period > 0 ? (1000 / period).toFixed(2) : 0;
                    const dutyCycle = period > 0 ? ((pulsewidth / period) * 100).toFixed(1) : 0;
                    
                    result.push({{
                        period: period,
                        pulsewidth: pulsewidth,
                        frequency: frequency,
                        dutyCycle: dutyCycle
                    }});
                }} else {{
                    result.push(null);
                }}
            }}
            
            return result;
        }}
        
        // Calculate current position for a channel (with LOOP support)
        function calculatePosition(channel, elapsedMs, chNum) {{
            // Check if this channel has LOOP enabled
            const hasLoop = loopInfo[chNum] === 1;
            
            // Handle negative elapsed (protocol hasn't started yet)
            if (elapsedMs < 0) {{
                return {{
                    elapsed_ms: 0,
                    current_pattern: 0,
                    current_cycle: 0,
                    current_state: 0,
                    status: channel[0].status[0],
                    is_pulsing: false,
                    pulse_info: null,
                    completed: false,
                    waiting: true,
                    position_percent: 0,
                    pattern_start_ms: 0,
                    looping: hasLoop,
                    loop_iteration: 0
                }};
            }}
            
            // Calculate total channel duration (excluding wait pattern for loop calculation)
            let channelTotalDuration = 0;
            let nonWaitDuration = 0;
            let waitDuration = 0;
            for (let p = 0; p < channel.length; p++) {{
                const pd = channel[p].time_ms_original.reduce((a, b) => a + b, 0) * channel[p].repeats;
                channelTotalDuration += pd;
                if (channel[p].pattern === 0) {{
                    waitDuration += pd;
                }} else {{
                    nonWaitDuration += pd;
                }}
            }}
            
            // For LOOP: wrap elapsed time to loop the non-wait portion
            let effectiveElapsed = elapsedMs;
            let loopIteration = 0;
            if (hasLoop && elapsedMs > waitDuration && nonWaitDuration > 0) {{
                const timeAfterWait = elapsedMs - waitDuration;
                loopIteration = Math.floor(timeAfterWait / nonWaitDuration);
                const timeInCurrentLoop = timeAfterWait % nonWaitDuration;
                effectiveElapsed = waitDuration + timeInCurrentLoop;
            }}
            
            let totalElapsed = 0;
            
            for (let pIdx = 0; pIdx < channel.length; pIdx++) {{
                const pattern = channel[pIdx];
                const cycleDuration = pattern.time_ms_original.reduce((a, b) => a + b, 0);
                const patternDuration = cycleDuration * pattern.repeats;
                
                if (totalElapsed + patternDuration > effectiveElapsed) {{
                    // Current pattern
                    const patternElapsed = effectiveElapsed - totalElapsed;
                    const currentCycle = Math.floor(patternElapsed / cycleDuration);
                    const cycleElapsed = patternElapsed % cycleDuration;
                    
                    // Find current state within cycle
                    let stateElapsed = 0;
                    let currentState = 0;
                    for (let s = 0; s < pattern.time_ms_original.length; s++) {{
                        if (stateElapsed + pattern.time_ms_original[s] > cycleElapsed) {{
                            currentState = s;
                            break;
                        }}
                        stateElapsed += pattern.time_ms_original[s];
                    }}
                    
                    const positionPercent = (effectiveElapsed / channelTotalDuration) * 100;
                    
                    // Check if this is pattern 0 (wait pattern) - treat as "waiting"
                    const isWaitingPattern = (pattern.pattern === 0);
                    
                    // Calculate ramp value if this is a RAMP pattern
                    let rampValue = null;
                    let actualStatus = pattern.status[currentState];
                    if (pattern.is_ramp && pattern.ramp_segments) {{
                        rampValue = getCurrentRampValue(pattern, cycleElapsed);
                        if (rampValue) {{
                            actualStatus = rampValue.value;
                        }}
                    }}
                    
                    return {{
                        elapsed_ms: elapsedMs,  // Actual elapsed (not wrapped)
                        effective_elapsed_ms: effectiveElapsed,  // Wrapped for loop
                        current_pattern: pIdx,
                        current_cycle: currentCycle,
                        current_state: currentState,
                        status: actualStatus,
                        is_ramp: pattern.is_ramp || false,
                        ramp_info: rampValue,
                        is_pulsing: pattern.pulse ? true : false,
                        pulse_info: pattern.pulse ? pattern : null,
                        completed: false,
                        waiting: isWaitingPattern,
                        position_percent: positionPercent,
                        pattern_start_ms: totalElapsed,
                        cycle_elapsed_ms: cycleElapsed,
                        looping: hasLoop,
                        loop_iteration: loopIteration
                    }};
                }}
                
                totalElapsed += patternDuration;
            }}
            
            // Completed (only if not looping)
            if (hasLoop) {{
                // Should not reach here if loop logic is correct, but handle gracefully
                return calculatePosition(channel, waitDuration + 1, chNum);
            }}
            
            return {{
                elapsed_ms: elapsedMs,
                effective_elapsed_ms: elapsedMs,
                current_pattern: channel.length - 1,
                current_cycle: channel[channel.length - 1].repeats - 1,
                current_state: channel[channel.length - 1].status.length - 1,
                status: 0,
                is_pulsing: false,
                pulse_info: null,
                completed: true,
                waiting: false,
                position_percent: 100,
                pattern_start_ms: totalElapsed,
                looping: false,
                loop_iteration: 0
            }};
        }}
        
        // Format status value for display (handles binary, PWM, DAC values)
        function formatStatusValue(status, isRamp = false, rampInfo = null) {{
            if (isRamp && rampInfo) {{
                // Show ramp value with direction indicator
                const direction = rampInfo.start < rampInfo.end ? '↑' : (rampInfo.start > rampInfo.end ? '↓' : '→');
                return `${{Math.round(status)}} ${{direction}} (${{rampInfo.mode}}: ${{rampInfo.start}}→${{rampInfo.end}})`;
            }}
            if (status === 0) return 'OFF (0)';
            if (status === 1) return 'ON (1→MAX)';
            if (status === 1.0) return 'ON (1.0→MAX)';
            if (typeof status === 'number' && status > 0 && status < 1) {{
                const pct = (status * 100).toFixed(1);
                return `${{pct}}% (${{status}})`;
            }}
            // Direct PWM/DAC value
            return `${{status}}`;
        }}
        
        // Calculate eased value for RAMP patterns
        function calculateRampValue(progress, startVal, endVal, mode, tStart, tEnd) {{
            // Map progress [0, 1] to t [tStart, tEnd]
            const t = tStart + progress * (tEnd - tStart);
            
            // f(t) = (1 - cos(π * t)) / 2
            const cosValue = (1 - Math.cos(Math.PI * t)) / 2;
            
            // Apply easing based on mode
            let easedProgress;
            if (mode === 'L') {{
                easedProgress = progress;  // Linear
            }} else {{
                easedProgress = cosValue;  // Eased (I, O, C, X modes)
            }}
            
            return startVal + easedProgress * (endVal - startVal);
        }}
        
        // Get current ramp value for a pattern at given cycle elapsed time
        function getCurrentRampValue(pattern, cycleElapsed) {{
            if (!pattern.is_ramp || !pattern.ramp_segments) {{
                return null;
            }}
            
            const segments = pattern.ramp_segments;
            let segmentStart = 0;
            
            for (let i = 0; i < segments.length; i++) {{
                const seg = segments[i];
                const segDuration = seg.duration_ms || seg.duration || 1000;
                
                if (segmentStart + segDuration > cycleElapsed) {{
                    // We're in this segment
                    const timeInSegment = cycleElapsed - segmentStart;
                    const progress = timeInSegment / segDuration;
                    
                    const startVal = seg.start_pwm !== undefined ? seg.start_pwm : seg.start;
                    const endVal = seg.end_pwm !== undefined ? seg.end_pwm : seg.end;
                    const mode = seg.mode || 'L';
                    const tStart = seg.t_start !== undefined ? seg.t_start : 0;
                    const tEnd = seg.t_end !== undefined ? seg.t_end : 1;
                    
                    const currentValue = calculateRampValue(progress, startVal, endVal, mode, tStart, tEnd);
                    
                    return {{
                        value: currentValue,
                        start: startVal,
                        end: endVal,
                        mode: mode,
                        progress: progress,
                        segmentIndex: i
                    }};
                }}
                
                segmentStart += segDuration;
            }}
            
            // Past all segments - return last segment's end value
            const lastSeg = segments[segments.length - 1];
            return {{
                value: lastSeg.end_pwm !== undefined ? lastSeg.end_pwm : lastSeg.end,
                start: lastSeg.start_pwm !== undefined ? lastSeg.start_pwm : lastSeg.start,
                end: lastSeg.end_pwm !== undefined ? lastSeg.end_pwm : lastSeg.end,
                mode: lastSeg.mode || 'L',
                progress: 1,
                segmentIndex: segments.length - 1
            }};
        }}
        
        // Cache DOM elements for faster updates
        let cachedElements = null;
        
        function cacheElements() {{
            const statusHeader = document.querySelector('.status-panel h2');
            const elapsedDiv = document.querySelector('.status-panel > div:first-of-type');
            
            const channels = {{}};
            const channelKeys = Object.keys(channelsData).sort((a, b) => parseInt(a) - parseInt(b));
            
            channelKeys.forEach((chNum, index) => {{
                const statusDiv = document.querySelector(`.channel-status:nth-child(${{index + 1}})`);
                const channelSection = document.getElementById('channel-' + chNum + '-section');
                
                if (statusDiv) {{
                    channels[chNum] = {{
                        statusDiv: statusDiv,
                        led: statusDiv.querySelector('.status-led'),
                        statusText: statusDiv.querySelector('.status-indicator strong'),
                        infoDiv: statusDiv.querySelector('div[style*="font-size"]'),
                        leftTime: statusDiv.querySelector('#ch' + chNum + '_left'),
                        channelSection: channelSection
                    }};
                }}
            }});
            
            cachedElements = {{
                statusHeader: statusHeader,
                elapsedDiv: elapsedDiv,
                channels: channels,
                channelKeys: channelKeys
            }};
        }}
        
        // Update the display - optimized version
        function updateDisplay() {{
            try {{
                if (!cachedElements) {{
                    cacheElements();
                }}
                
                const now = new Date();
                
                // Debug: Log update (can be removed later)
                if (window.updateCount === undefined) window.updateCount = 0;
                window.updateCount++;
                if (window.updateCount % 10 === 1) {{  // Log every 10 seconds
                    console.log('✅ Update loop running, count:', window.updateCount);
                }}
                
                // Update current time display
                const timeStr = now.toLocaleString('en-CA', {{
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false
                }}).replace(',', '');
                
                if (cachedElements.statusHeader) {{
                    cachedElements.statusHeader.textContent = '🔴 LIVE STATUS - ' + timeStr;
                }}
                
                // Update elapsed time if we have upload time
                if (uploadTime && cachedElements.elapsedDiv) {{
                    const totalElapsed = now - uploadTime;
                    const uploadTimeStr = uploadTime.toLocaleString('en-CA', {{
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: false
                    }}).replace(',', '');
                    
                    cachedElements.elapsedDiv.innerHTML = '<strong>Upload Time:</strong> ' + uploadTimeStr + 
                        ' <strong style="margin-left: 20px;">Total Elapsed:</strong> ' + formatTime(totalElapsed);
                }}
                
                // Update each channel status and position markers
                if (uploadTime) {{
                    cachedElements.channelKeys.forEach(chNum => {{
                        const channel = channelsData[chNum];
                        const cached = cachedElements.channels[chNum];
                        
                        if (!cached || !cached.led || !cached.statusText) {{
                            return;
                        }}
                        
                        // Calculate elapsed time from UPLOAD TIME
                        // Pattern 0 (wait pattern) handles the waiting period
                        const channelElapsed = now - uploadTime;
                        const pos = calculatePosition(channel, channelElapsed, chNum);
                        
                        // Check if this channel has LOOP enabled
                        const hasLoop = loopInfo[chNum] === 1;

                        // Compute total channel duration and remaining time
                        const channelTotalDuration = channel.reduce((acc, p) => {{
                            const cycle = p.time_ms_original.reduce((a, b) => a + b, 0);
                            return acc + cycle * p.repeats;
                        }}, 0);
                        
                        // For looping channels, show "∞ LOOPING" instead of countdown
                        let remainingDisplay;
                        if (hasLoop && !pos.waiting) {{
                            remainingDisplay = '∞ LOOP #' + (pos.loop_iteration + 1);
                        }} else {{
                            const remainingMs = Math.max(0, channelTotalDuration - pos.elapsed_ms);
                            remainingDisplay = formatTime(remainingMs);
                        }}
                        if (cached.leftTime) {{
                            cached.leftTime.textContent = remainingDisplay;
                        }}

                        // Update per-pattern remaining times for this channel
                        // For LOOP channels, use effective_elapsed_ms (wrapped) instead of elapsed_ms
                        const meta = channelsMeta[chNum];
                        if (meta) {{
                            const elapsedForCalc = hasLoop ? pos.effective_elapsed_ms : pos.elapsed_ms;
                            
                            for (let pi = 0; pi < meta.starts.length; pi++) {{
                                const startMs = meta.starts[pi];
                                const dur = meta.durations[pi];
                                let leftForPattern = 0;

                                if (elapsedForCalc < startMs) {{
                                    leftForPattern = dur;
                                }} else if (elapsedForCalc >= startMs + dur) {{
                                    leftForPattern = 0;
                                }} else {{
                                    leftForPattern = (startMs + dur) - elapsedForCalc;
                                }}

                                const el = document.getElementById('ch' + chNum + '_pat' + pi + '_left');
                                if (el) {{
                                    // For looping channels, show loop info with remaining time in current cycle
                                    if (hasLoop && elapsedForCalc >= startMs && elapsedForCalc < startMs + dur) {{
                                        el.textContent = formatTime(leftForPattern) + ' 🔄#' + (pos.loop_iteration + 1);
                                    }} else if (hasLoop && !pos.waiting) {{
                                        // LOOP channel but not in this pattern - show appropriate status
                                        if (elapsedForCalc < startMs) {{
                                            el.textContent = formatTime(leftForPattern) + ' 🔄#' + (pos.loop_iteration + 1);
                                        }} else {{
                                            el.textContent = '✓ 🔄#' + (pos.loop_iteration + 1);
                                        }}
                                    }} else {{
                                        el.textContent = formatTime(leftForPattern);
                                    }}
                                }}
                            }}
                        }}
                        
                        // Update LED and status text - show exact values for non-binary states
                        const statusVal = pos.status;
                        const isRamp = pos.is_ramp || false;
                        const rampInfo = pos.ramp_info || null;
                        const statusDisplay = formatStatusValue(statusVal, isRamp, rampInfo);
                        
                        // Determine LED class based on value
                        let ledClass = 'off';
                        if (statusVal === 0) {{
                            ledClass = 'off';
                        }} else if (statusVal === 1 || statusVal === 1.0) {{
                            ledClass = 'on';
                        }} else if (typeof statusVal === 'number' && statusVal > 0) {{
                            // Intermediate value - use "on" class with partial brightness indication
                            ledClass = 'on';
                        }}
                        
                        // For RAMP patterns, add special styling
                        if (isRamp && rampInfo) {{
                            ledClass = 'on';  // RAMP is always "active"
                        }}
                        
                        if (pos.waiting) {{
                            // Show actual status value even during waiting
                            if (pos.is_pulsing) {{
                                cached.led.className = 'status-led pulsing';
                                cached.statusText.textContent = '⏰ WAITING - PULSING ≈ ' + statusDisplay;
                            }} else if (statusVal === 0) {{
                                cached.led.className = 'status-led off';
                                cached.statusText.textContent = '⏰ WAITING - OFF ░';
                            }} else {{
                                cached.led.className = 'status-led ' + ledClass;
                                cached.statusText.textContent = '⏰ WAITING - ' + statusDisplay;
                            }}
                        }} else if (pos.completed) {{
                            cached.led.className = 'status-led completed';
                            cached.statusText.textContent = 'COMPLETED ✓';
                        }} else if (isRamp && rampInfo) {{
                            // RAMP pattern - show dynamic value with ramp indicator
                            cached.led.className = 'status-led ramping';
                            let loopIndicator = hasLoop ? ' 🔄' : '';
                            cached.statusText.textContent = '📈 RAMP: ' + statusDisplay + loopIndicator;
                        }} else if (pos.is_pulsing) {{
                            cached.led.className = 'status-led pulsing';
                            cached.statusText.textContent = 'PULSING ≈ ' + statusDisplay;
                        }} else if (statusVal === 0) {{
                            cached.led.className = 'status-led off';
                            cached.statusText.textContent = 'OFF ░';
                        }} else {{
                            cached.led.className = 'status-led ' + ledClass;
                            // Show exact value with loop indicator if looping
                            let loopIndicator = hasLoop ? ' 🔄' : '';
                            cached.statusText.textContent = statusDisplay + loopIndicator;
                        }}
                        
                        // Update pattern/cycle info
                        if (cached.infoDiv) {{
                            if (pos.waiting) {{
                                // Pattern 0 (waiting pattern) - show countdown to start
                                const channelStartTime = channelStartTimes[chNum] || uploadTime;
                                const timeToStart = Math.max(0, channelStartTime - now);
                                const startTimeStr = channelStartTime.toLocaleString('en-CA', {{
                                    year: 'numeric',
                                    month: '2-digit',
                                    day: '2-digit',
                                    hour: '2-digit',
                                    minute: '2-digit',
                                    second: '2-digit',
                                    hour12: false
                                }}).replace(',', '');
                                
                                const currentPattern = channel[pos.current_pattern];
                                if (!currentPattern) {{
                                    console.error('Pattern not found:', chNum, pos.current_pattern);
                                    return;
                                }}
                                
                                // Calculate protocol elapsed (time since pattern 0 ended for this channel)
                                let protocolElapsedDisplay = '--:--:--:--';
                                if (channel[0] && channel[0].pattern === 0) {{
                                    const pattern0Duration = channel[0].time_ms_original.reduce((a, b) => a + b, 0) * channel[0].repeats;
                                    if (pos.elapsed_ms >= pattern0Duration) {{
                                        const protocolElapsed = pos.elapsed_ms - pattern0Duration;
                                        protocolElapsedDisplay = formatTime(protocolElapsed);
                                    }}
                                }} else {{
                                    // No pattern 0, protocol elapsed = total elapsed
                                    protocolElapsedDisplay = formatTime(pos.elapsed_ms);
                                }}
                                
                                // Check if waiting pattern has pulse info
                                let pulseInfo = '';
                                if (currentPattern.pulse && pos.is_pulsing) {{
                                    const pulseParams = parsePulseParams(currentPattern.pulse);
                                    pulseInfo = '<div style="color: #ff9800; font-weight: bold; margin-top: 8px;">🟠 PULSING (Wait)</div>';
                                    
                                    if (pulseParams && pulseParams[pos.current_state]) {{
                                        const p = pulseParams[pos.current_state];
                                        pulseInfo += '<div style="font-size: 0.85em; color: #bbb; margin-top: 4px;">';
                                        pulseInfo += 'Freq: ' + p.frequency + ' Hz<br>';
                                        pulseInfo += 'Period: ' + p.period + ' ms<br>';
                                        pulseInfo += 'PW: ' + p.pulsewidth + ' ms<br>';
                                        pulseInfo += 'DC: ' + p.dutyCycle + ' %';
                                        pulseInfo += '</div>';
                                    }} else if (currentPattern.pulse) {{
                                        pulseInfo += '<div style="font-size: 0.85em; color: #bbb;">Raw: ' + currentPattern.pulse + '</div>';
                                    }}
                                }}
                                
                                cached.infoDiv.innerHTML = `
                                    <div>Pattern: ${{pos.current_pattern + 1}}/${{channel.length}}</div>
                                    <div>Cycle: ${{pos.current_cycle + 1}}/${{currentPattern.repeats}}</div>
                                    <div style="color: #fff;">Protocol Elapsed: ${{protocolElapsedDisplay}}</div>
                                    <div style="font-size: 1.15em; color: #fff; font-weight: bold; margin-top: 6px;">Total Left: ${{formatTime(remainingMs)}}</div>
                                    <div style="color: #bbb; margin-top: 3px;">Starts at: ${{startTimeStr}}</div>
                                    <div style="color: #ff9800; font-weight: bold; margin-top: 3px;">⏱️ Starts in: ${{formatTime(timeToStart)}}</div>
                                    ${{pulseInfo}}
                                `;
                            }} else if (pos.completed) {{
                                cached.infoDiv.innerHTML = '<div style="color: #4CAF50; font-weight: bold;">✓ Complete</div>';
                            }} else {{
                                // Active pattern
                                const currentPattern = channel[pos.current_pattern];
                                if (!currentPattern) {{
                                    console.error('Pattern not found:', chNum, pos.current_pattern);
                                    return;
                                }}
                                
                                let pulseInfo = '';
                                if (pos.is_pulsing && pos.pulse_info) {{
                                    const pattern = pos.pulse_info;
                                    const pulseParams = parsePulseParams(pattern.pulse);
                                    
                                    pulseInfo = '<div style="color: #ff9800; font-weight: bold; margin-top: 8px;">🟠 PULSING</div>';
                                    
                                    if (pulseParams && pulseParams[pos.current_state]) {{
                                        const p = pulseParams[pos.current_state];
                                        pulseInfo += '<div style="font-size: 0.85em; color: #bbb; margin-top: 4px;">';
                                        pulseInfo += 'Freq: ' + p.frequency + ' Hz<br>';
                                        pulseInfo += 'Period: ' + p.period + ' ms<br>';
                                        pulseInfo += 'PW: ' + p.pulsewidth + ' ms<br>';
                                        pulseInfo += 'DC: ' + p.dutyCycle + ' %';
                                        pulseInfo += '</div>';
                                    }} else if (pattern.pulse) {{
                                        pulseInfo += '<div style="font-size: 0.85em; color: #bbb;">Raw: ' + pattern.pulse + '</div>';
                                    }}
                                }}
                                
                                // Calculate protocol elapsed (time since pattern 0 ended for this channel)
                                // For LOOP channels, show both total elapsed and elapsed in current loop cycle
                                let protocolElapsedDisplay = '--:--:--:--';
                                let loopCycleElapsed = '--:--:--:--';
                                const elapsedToUse = hasLoop ? pos.effective_elapsed_ms : pos.elapsed_ms;
                                if (channel[0] && channel[0].pattern === 0) {{
                                    const pattern0Duration = channel[0].time_ms_original.reduce((a, b) => a + b, 0) * channel[0].repeats;
                                    if (pos.elapsed_ms >= pattern0Duration) {{
                                        // Total elapsed since protocol started (actual time)
                                        const protocolElapsed = pos.elapsed_ms - pattern0Duration;
                                        protocolElapsedDisplay = formatTime(protocolElapsed);
                                        // For LOOP: also show elapsed in current loop cycle
                                        if (hasLoop && pos.effective_elapsed_ms >= pattern0Duration) {{
                                            const cycleElapsed = pos.effective_elapsed_ms - pattern0Duration;
                                            loopCycleElapsed = formatTime(cycleElapsed);
                                        }}
                                    }}
                                }} else {{
                                    // No pattern 0, protocol elapsed = total elapsed
                                    protocolElapsedDisplay = formatTime(pos.elapsed_ms);
                                    if (hasLoop) {{
                                        loopCycleElapsed = formatTime(pos.effective_elapsed_ms);
                                    }}
                                }}
                                
                                // Show loop info if enabled
                                let loopDisplay = '';
                                // For LOOP: calculate remaining time in current loop cycle
                                const nonWaitDuration = channel.slice(1).reduce((acc, p) => {{
                                    const cycle = p.time_ms_original.reduce((a, b) => a + b, 0);
                                    return acc + cycle * p.repeats;
                                }}, 0);
                                let remainingDisplay = formatTime(Math.max(0, channelTotalDuration - pos.elapsed_ms));
                                if (hasLoop) {{
                                    // Calculate remaining time in current loop iteration
                                    const pattern0Duration = channel[0] && channel[0].pattern === 0 
                                        ? channel[0].time_ms_original.reduce((a, b) => a + b, 0) * channel[0].repeats 
                                        : 0;
                                    const timeInLoop = pos.effective_elapsed_ms - pattern0Duration;
                                    const remainingInLoop = Math.max(0, nonWaitDuration - timeInLoop);
                                    loopDisplay = '<div style="color: #00bcd4; font-weight: bold; margin-top: 4px;">🔄 LOOP #' + (pos.loop_iteration + 1) + ' (∞)</div>';
                                    loopDisplay += '<div style="color: #00bcd4; font-size: 0.9em;">Cycle Elapsed: ' + loopCycleElapsed + '</div>';
                                    remainingDisplay = formatTime(remainingInLoop) + ' (this cycle)';
                                }}
                                
                                cached.infoDiv.innerHTML = `
                                    <div>Pattern: ${{pos.current_pattern + 1}}/${{channel.length}}</div>
                                    <div>Cycle: ${{pos.current_cycle + 1}}/${{currentPattern.repeats}}</div>
                                    <div style="color: #fff;">Total Elapsed: ${{protocolElapsedDisplay}}</div>
                                    <div style="font-size: 1.15em; color: #fff; font-weight: bold; margin-top: 6px;">Time Left: ${{remainingDisplay}}</div>
                                    ${{loopDisplay}}
                                    ${{pulseInfo}}
                                `;
                            }}
                        }}
                        
                        // Update pattern block highlighting and position marker
                        if (cached.channelSection) {{
                            try {{
                                // Remove 'current' class from all pattern blocks
                                cached.channelSection.querySelectorAll('.pattern-block').forEach(block => {{
                                    block.classList.remove('current');
                                }});
                                
                                // Add 'current' class to active pattern block
                                if (!pos.completed && pos.current_pattern < channel.length) {{
                                    const patternBlocks = cached.channelSection.querySelectorAll('.pattern-block');
                                    if (patternBlocks[pos.current_pattern]) {{
                                        patternBlocks[pos.current_pattern].classList.add('current');
                                    }}
                                    
                                    // Update cycle label
                                    const cycleLabel = document.getElementById('ch' + chNum + '_pat' + pos.current_pattern + '_cycle');
                                    const currentPattern = channel[pos.current_pattern];
                                    if (cycleLabel && currentPattern) {{
                                        cycleLabel.textContent = 'Cycle ' + (pos.current_cycle + 1) + '/' + currentPattern.repeats;
                                    }}
                                    
                                    // Remove old position markers
                                    cached.channelSection.querySelectorAll('.current-position').forEach(m => m.remove());
                                    
                                    // Add new position marker
                                    const timeline = document.getElementById('ch' + chNum + '_pat' + pos.current_pattern + '_timeline');
                                    if (timeline && currentPattern) {{
                                        const cycleDuration = currentPattern.time_ms_original.reduce((a, b) => a + b, 0);
                                        // For LOOP channels, use effective_elapsed_ms which is wrapped to current loop cycle
                                        const elapsedToUse = hasLoop ? pos.effective_elapsed_ms : pos.elapsed_ms;
                                        const patternElapsed = elapsedToUse - pos.pattern_start_ms;
                                        const cycleElapsed = patternElapsed % cycleDuration;
                                        const percentInCycle = (cycleElapsed / cycleDuration) * 100;
                                        
                                        const marker = document.createElement('div');
                                        marker.className = 'current-position';
                                        marker.style.left = percentInCycle + '%';
                                        timeline.appendChild(marker);
                                    }}
                                }}
                            }} catch (blockError) {{
                                console.error('Error updating pattern block for channel', chNum, ':', blockError);
                            }}
                        }}
                    }});
                }} else {{
                    // No upload time - show static initial state
                    cachedElements.channelKeys.forEach(chNum => {{
                        const channel = channelsData[chNum];
                        const cached = cachedElements.channels[chNum];
                        const pos = calculatePosition(channel, 0, chNum);
                        const hasLoop = loopInfo[chNum] === 1;
                        
                        if (cached && cached.led && cached.statusText) {{
                            if (pos.completed) {{
                                cached.led.className = 'status-led completed';
                                cached.statusText.textContent = 'COMPLETED ✓';
                            }} else {{
                                cached.led.className = 'status-led off';
                                const loopIndicator = hasLoop ? ' 🔄' : '';
                                cached.statusText.textContent = 'Ready' + loopIndicator;
                            }}
                            
                            if (cached.infoDiv) {{
                                // Compute total duration for this channel (static display)
                                let channelTotalDuration = 0;
                                for (let pIdx = 0; pIdx < channel.length; pIdx++) {{
                                    const p = channel[pIdx];
                                    const cycle = p.time_ms_original.reduce((a, b) => a + b, 0);
                                    channelTotalDuration += cycle * p.repeats;
                                }}
                                
                                const remainingDisplay = hasLoop ? '∞ LOOP mode' : formatTime(channelTotalDuration - pos.elapsed_ms);

                                cached.infoDiv.innerHTML = `
                                    <div>Pattern: ${{pos.current_pattern + 1}}/${{channel.length}}</div>
                                    <div>Cycle: ${{pos.current_cycle + 1}}/${{channel[pos.current_pattern].repeats}}</div>
                                    <div>Elapsed: ${{formatTime(0)}}</div>
                                    <div style="font-size: 1.15em; color: #333; font-weight: bold; margin-top: 6px;">Total Left: ${{remainingDisplay}}</div>
                                    ${{hasLoop ? '<div style="color: #00bcd4; font-weight: bold; margin-top: 4px;">🔄 LOOP enabled</div>' : ''}}
                                `;
                            }}
                        }}
                    }});
                }}
            }} catch (error) {{
                console.error('❌ Error updating display:', error);
                console.error('Stack trace:', error.stack);
                // Re-throw to stop the timer so errors are visible
            }}
        }}
        
        // Initialize and start updates
        updateDisplay();
        setInterval(updateDisplay, 1000);
    </script>
    
    <script>
        // Intensity plotting functionality
        function calculateEasedValue(progress, startPwm, endPwm, easing, tStart, tEnd) {{
            // Map progress [0, 1] to t [tStart, tEnd]
            const t = tStart + progress * (tEnd - tStart);
            
            // f(t) = (1 - cos(π * t)) / 2
            const cosValue = (1 - Math.cos(Math.PI * t)) / 2;
            
            // Apply easing based on mode
            let easedProgress;
            if (easing === 'L') {{
                easedProgress = progress;
            }} else {{
                easedProgress = cosValue;
            }}
            
            return startPwm + easedProgress * (endPwm - startPwm);
        }}
        
        function generateIntensityCurve(segments) {{
            const times = [];
            const intensities = [];
            let currentTime = 0;
            
            segments.forEach((seg, segIndex) => {{
                const isConstant = (seg.start === seg.end);
                const isRamp = (seg.mode && seg.mode !== 'L' && !isConstant);
                
                if (isConstant) {{
                    // Square wave for constant ON/OFF/PWM values
                    // Add point at start (vertical transition if prev segment was different)
                    if (segIndex > 0) {{
                        const prevSeg = segments[segIndex - 1];
                        if (prevSeg.end !== seg.start) {{
                            // Add vertical transition point
                            times.push(currentTime / 1000);
                            intensities.push(seg.start);
                        }}
                    }}
                    // Start of constant segment
                    times.push(currentTime / 1000);
                    intensities.push(seg.start);
                    // End of constant segment
                    times.push((currentTime + seg.duration) / 1000);
                    intensities.push(seg.end);
                }} else {{
                    // RAMP or gradient - use smooth interpolation
                    const numPoints = Math.max(50, Math.floor(seg.duration / 10));
                    
                    for (let i = 0; i <= numPoints; i++) {{
                        const progress = i / numPoints;
                        const time = currentTime + progress * seg.duration;
                        const intensity = calculateEasedValue(
                            progress,
                            seg.start,
                            seg.end,
                            seg.mode,
                            seg.t_start,
                            seg.t_end
                        );
                        
                        times.push(time / 1000);  // Convert to seconds
                        intensities.push(intensity);
                    }}
                }}
                
                currentTime += seg.duration;
            }});
            
            return {{ times, intensities }};
        }}
        
        // Channel intensity data from Python
        const channelIntensityData = {channel_intensity_json};
        
        // Detect value range from data
        function detectValueRange(values) {{
            if (!values || values.length === 0) return {{ min: 0, max: 255, type: 'pwm' }};
            const maxVal = Math.max(...values);
            const minVal = Math.min(...values);
            
            if (maxVal <= 1) return {{ min: 0, max: 1, type: 'binary' }};
            if (maxVal <= 255) return {{ min: 0, max: 255, type: 'pwm' }};
            return {{ min: 0, max: 4095, type: 'dac' }};
        }}
        
        // Calculate dynamic Y-axis limits with padding
        function calculateDynamicYlim(values, paddingPct = 0.1) {{
            if (!values || values.length === 0) return {{ min: -5, max: 260 }};
            
            const dataMin = Math.min(...values);
            const dataMax = Math.max(...values);
            const range = detectValueRange(values);
            
            // Calculate padding
            const dataRange = dataMax - dataMin;
            const padding = Math.max(dataRange * paddingPct, range.max * 0.02);
            
            let yMin = Math.max(-range.max * 0.02, dataMin - padding);
            let yMax = Math.min(range.max * 1.05, dataMax + padding);
            
            // Ensure minimum visible range (at least 5% of full range)
            if (yMax - yMin < range.max * 0.05) {{
                yMax = yMin + range.max * 0.1;
            }}
            
            return {{ min: yMin, max: yMax, type: range.type }};
        }}
        
        // Render intensity plots for all channels
        Object.keys(channelIntensityData).forEach(chNum => {{
            const plotDiv = document.getElementById(`intensity-plot-ch${{chNum}}`);
            if (!plotDiv) return;
            
            const segments = channelIntensityData[chNum];
            if (!segments || segments.length === 0) return;
            
            const curve = generateIntensityCurve(segments);
            const hasLoop = loopInfo[chNum] === 1;
            
            // Get channel type info (use known channel type instead of auto-detecting)
            const chMax = getChannelMaxValue(parseInt(chNum));
            const chTypeName = getChannelTypeName(parseInt(chNum));
            
            // Calculate dynamic Y-axis limits using known channel max
            const ylim = calculateDynamicYlim(curve.intensities);
            ylim.max = chMax;  // Override with known channel max
            
            // Generate Y-axis label based on channel type
            const yAxisLabel = `Value (0-${{chMax}} ${{chTypeName}})`;
            
            // Add loop indicator to title
            const loopIndicator = hasLoop ? ' 🔄 LOOP' : '';
            
            const trace = {{
                x: curve.times,
                y: curve.intensities,
                type: 'scatter',
                mode: 'lines',
                fill: 'tozeroy',
                fillcolor: hasLoop ? 'rgba(0, 188, 212, 0.3)' : 'rgba(102, 126, 234, 0.3)',
                line: {{
                    color: hasLoop ? '#00bcd4' : '#667eea',
                    width: 2,
                    shape: 'hv'  // Use step/horizontal-vertical for pulse visualization
                }},
                name: `Channel ${{chNum}} Intensity`
            }};
            
            const layout = {{
                title: {{
                    text: `Intensity Over Time${{loopIndicator}}`,
                    font: {{ size: 14, color: '#333' }}
                }},
                xaxis: {{
                    title: 'Time (seconds)',
                    showgrid: true,
                    gridcolor: '#e0e0e0',
                    zeroline: true
                }},
                yaxis: {{
                    title: yAxisLabel,
                    range: [ylim.min, ylim.max],
                    showgrid: true,
                    gridcolor: '#e0e0e0',
                    zeroline: true
                }},
                margin: {{ t: 40, r: 20, b: 50, l: 60 }},
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                showlegend: false
            }};
            
            const config = {{
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'resetScale2d']
            }};
            
            Plotly.newPlot(plotDiv, [trace], layout, config);
            
            // Store plot info for "Now" indicator updates
            plotDiv._plotInfo = {{
                chNum: chNum,
                ylim: ylim,
                totalDuration: curve.times.length > 0 ? curve.times[curve.times.length - 1] : 0,
                hasLoop: hasLoop
            }};
        }});
        
        // Function to update "Now" indicator on all intensity plots
        function updateNowIndicators() {{
            if (!uploadTime) return;  // No upload time = no "now" indicator
            
            const now = new Date();
            
            Object.keys(channelIntensityData).forEach(chNum => {{
                const plotDiv = document.getElementById(`intensity-plot-ch${{chNum}}`);
                if (!plotDiv || !plotDiv._plotInfo) return;
                
                const info = plotDiv._plotInfo;
                const hasLoop = info.hasLoop;
                
                // Calculate elapsed time - reference point depends on whether timeline includes wait pattern
                // For LOOP channels: timeline skips wait pattern, so X=0 is when main pattern starts (channelStartTimes)
                // For non-LOOP channels: timeline includes wait pattern, so X=0 is uploadTime
                let elapsedMs;
                if (hasLoop) {{
                    // LOOP: timeline starts after wait, use channel-specific start time
                    const channelStart = channelStartTimes[chNum];
                    if (!channelStart) return;
                    elapsedMs = now - channelStart;
                }} else {{
                    // Non-LOOP: timeline includes wait from upload, use uploadTime
                    elapsedMs = now - uploadTime;
                }}
                
                // Timeline is in calibrated time (time_ms_original), which matches real-world time
                // No calibFactor needed here since time_ms_original already represents expected real duration
                let elapsedSec = elapsedMs / 1000;
                
                // For LOOP channels, wrap elapsed time to show current position in cycle
                let loopIteration = 0;
                if (hasLoop && elapsedSec > 0 && info.totalDuration > 0) {{
                    loopIteration = Math.floor(elapsedSec / info.totalDuration);
                    elapsedSec = elapsedSec % info.totalDuration;
                }}
                
                // Create "Now" indicator shape (vertical line)
                const shapes = [];
                const annotations = [];
                
                // Show position indicator (loops for LOOP channels)
                if (elapsedSec >= 0 && (hasLoop || elapsedSec <= info.totalDuration)) {{
                    shapes.push({{
                        type: 'line',
                        x0: elapsedSec,
                        x1: elapsedSec,
                        y0: info.ylim.min,
                        y1: info.ylim.max,
                        line: {{
                            color: hasLoop ? '#00bcd4' : '#ff4444',
                            width: 2,
                            dash: 'dot'
                        }}
                    }});
                    
                    const nowText = hasLoop ? `🔄 LOOP #${{loopIteration + 1}}` : '⏱ NOW';
                    annotations.push({{
                        x: elapsedSec,
                        y: info.ylim.max,
                        xref: 'x',
                        yref: 'y',
                        text: nowText,
                        showarrow: false,
                        font: {{
                            color: hasLoop ? '#00bcd4' : '#ff4444',
                            size: 10,
                            family: 'Arial, sans-serif'
                        }},
                        bgcolor: 'rgba(255, 255, 255, 0.8)',
                        bordercolor: hasLoop ? '#00bcd4' : '#ff4444',
                        borderwidth: 1,
                        borderpad: 2,
                        yshift: 10
                    }});
                }} else if (!hasLoop && elapsedSec > info.totalDuration) {{
                    // Protocol completed (only for non-loop channels)
                    annotations.push({{
                        x: info.totalDuration,
                        y: info.ylim.max,
                        xref: 'x',
                        yref: 'y',
                        text: '✓ DONE',
                        showarrow: false,
                        font: {{
                            color: '#28a745',
                            size: 10,
                            family: 'Arial, sans-serif'
                        }},
                        bgcolor: 'rgba(255, 255, 255, 0.8)',
                        bordercolor: '#28a745',
                        borderwidth: 1,
                        borderpad: 2,
                        yshift: 10
                    }});
                }} else {{
                    // Waiting to start (elapsedSec < 0)
                    annotations.push({{
                        x: 0,
                        y: info.ylim.max,
                        xref: 'x',
                        yref: 'y',
                        text: '⏳ WAITING',
                        showarrow: false,
                        font: {{
                            color: '#ffc107',
                            size: 10,
                            family: 'Arial, sans-serif'
                        }},
                        bgcolor: 'rgba(255, 255, 255, 0.8)',
                        bordercolor: '#ffc107',
                        borderwidth: 1,
                        borderpad: 2,
                        yshift: 10
                    }});
                }}
                
                // Update the plot with shapes/annotations
                Plotly.relayout(plotDiv, {{
                    shapes: shapes,
                    annotations: annotations
                }});
            }});
        }}
        
        // Start "Now" indicator updates (every second)
        if (uploadTime) {{
            updateNowIndicators();  // Initial update
            setInterval(updateNowIndicators, 1000);
        }}
    </script>
</body>
</html>
"""
    
    # Write using UTF-8 to avoid encoding errors on non-UTF consoles
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    safe_print(f"HTML visualization saved: {output_file}")
    safe_print(f"Open in browser: file://{os.path.abspath(output_file)}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate HTML Protocol Visualization with Real-Time Status'
    )
    parser.add_argument(
        'commands_file',
        help='Commands file (.txt)'
    )
    parser.add_argument(
        '-o', '--output',
        default=None,
        help='Output HTML file (default: commands_visualization.html)'
    )
    parser.add_argument(
        '-u', '--upload-time',
        default=None,
        help='Protocol upload time - when commands were sent to Arduino (format: "YYYY-MM-DD HH:MM:SS")'
    )
    parser.add_argument(
        '-s', '--start-time',
        default=None,
        help='(Deprecated - use --upload-time instead) Protocol start time (format: "YYYY-MM-DD HH:MM:SS")'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.commands_file):
        print(f"Error: File not found: {args.commands_file}")
        sys.exit(1)
    
    # Parse commands
    print(f"Parsing commands from: {args.commands_file}")
    channels, calib_factor, loop_info, channel_types = parse_commands(args.commands_file)
    
    if not channels:
        print("Error: No channels found in commands file")
        sys.exit(1)
    
    print(f"Found {len(channels)} channels")
    print(f"Calibration Factor: {calib_factor:.5f}")
    if channel_types:
        type_names = {'P': 'PWM', 'D': 'DAC', 'M': 'MCP4728', 'B': 'Binary'}
        ch_info = [f'CH{i+1}:{type_names.get(t, t)}' for i, t in enumerate(channel_types)]
        print(f"Channel Types: {', '.join(ch_info)}")
    if loop_info:
        print(f"LOOP enabled for channels: {[f'CH{ch}' for ch, v in loop_info.items() if v]}")
    
    # Parse upload time (or fallback to start_time for backward compatibility)
    upload_time = None
    if args.upload_time:
        try:
            upload_time = datetime.strptime(args.upload_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            print(f"Error: Invalid upload time format. Use: YYYY-MM-DD HH:MM:SS")
            sys.exit(1)
    elif args.start_time:
        # Backward compatibility: treat start_time as upload_time
        try:
            upload_time = datetime.strptime(args.start_time, '%Y-%m-%d %H:%M:%S')
            print("Note: --start-time is deprecated, use --upload-time instead")
        except ValueError:
            print(f"Error: Invalid start time format. Use: YYYY-MM-DD HH:MM:SS")
            sys.exit(1)
    
    # Calculate per-channel start times from upload_time + wait_time
    channel_start_times = {}
    if upload_time:
        for ch_num, patterns in channels.items():
            # Find pattern 0 (wait pattern) for this channel
            wait_time_ms = 0
            for pattern in patterns:
                if pattern['pattern'] == 0:
                    # Sum all time_ms in pattern 0
                    wait_time_ms = sum(pattern['time_ms_original'])
                    break
            
            # Calculate start time for this channel
            wait_time_seconds = wait_time_ms / 1000.0
            channel_start_times[ch_num] = upload_time + timedelta(seconds=wait_time_seconds)
    
    # Calculate positions
    if upload_time:
        print(f"Using upload time: {upload_time.strftime('%Y-%m-%d %H:%M:%S')}")
        positions = calculate_current_position(channels, upload_time)
    else:
        print("No upload time provided - showing structure only")
        # Create empty positions
        positions = {
            ch: {
                'elapsed_ms': 0,
                'current_pattern': -1,
                'current_cycle': 0,
                'current_state': 0,
                'state_elapsed_ms': 0,
                'status': 0,
                'is_pulsing': False,
                'completed': False
            }
            for ch in channels.keys()
        }
    
    # Generate output filename in the same directory as commands file
    commands_path = os.path.abspath(args.commands_file)
    output_dir = os.path.dirname(commands_path)
    
    if args.output:
        output_file = args.output
        if not output_file.endswith('.html'):
            output_file += '.html'
        # If relative path, put in same directory as commands file
        if not os.path.isabs(output_file):
            output_file = os.path.join(output_dir, os.path.basename(output_file))
    else:
        # Match the commands file name but change extension to .html
        base = os.path.splitext(os.path.basename(args.commands_file))[0]
        # Replace 'commands' with 'monitor' in generated filename
        base_monitor = base.replace('commands', 'monitor')
        output_file = os.path.join(output_dir, f"{base_monitor}.html")
    
    # Generate HTML
    print(f"Generating HTML visualization...")
    generate_html(channels, positions, output_file, upload_time, channel_start_times, loop_info, channel_types, calib_factor)


if __name__ == '__main__':
    main()
