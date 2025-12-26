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
    """Parse commands file and extract pattern data and calibration factor."""
    channels = {}
    calib_factor = 1.0  # Default calibration factor
    
    with open(commands_file, 'r') as f:
        lines = f.readlines()
    
    # First, extract calibration factor from header
    for line in lines:
        if line.startswith('# Calibration Factor:'):
            try:
                calib_factor = float(line.split(':')[1].strip())
            except (ValueError, IndexError):
                pass
            break
    
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
        status_match = re.search(r'STATUS:([\d,]+)', line)
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
            # Standard STATUS/TIME_MS command
            status_list = [int(s) for s in status_match.group(1).split(',')]
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
    
    return channels, calib_factor


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


def generate_html(channels, positions, output_file, upload_time=None, channel_start_times=None):
    """Generate interactive HTML visualization with real-time status.
    
    All time calculations and position updates are done in JavaScript for independence.
    Python only provides the initial data structure and upload time.
    
    Args:
        channels: Dict of channel patterns
        positions: Not used anymore - kept for backwards compatibility
        output_file: Path to output HTML file
        upload_time: When commands were uploaded to Arduino
        channel_start_times: Dict of per-channel start times (for display only)
    """
    
    import json
    from datetime import datetime
    
    # Get current time for initial display only
    now = datetime.now()
    
    # Prepare data for JavaScript - only static data
    channels_json = json.dumps(channels)
    
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
    channel_intensity_data = {}
    for ch_num, patterns in channels.items():
        segments = []
        for pattern in patterns:
            repeats = pattern.get('repeats', 1)
            if pattern.get('is_ramp') and pattern.get('ramp_segments'):
                # Use RAMP segment data directly
                for _ in range(repeats):
                    for seg in pattern['ramp_segments']:
                        segments.append({
                            'start': seg.get('start_pwm', seg.get('start', 0)),
                            'end': seg.get('end_pwm', seg.get('end', 255)),
                            'duration': seg.get('duration_ms', seg.get('duration', 1000)),
                            'mode': seg.get('mode', 'L'),
                            't_start': seg.get('t_start', 0),
                            't_end': seg.get('t_end', 1)
                        })
            elif any(0 < s < 255 for s in pattern.get('status', [])):
                # Regular pattern with PWM values - create constant segments
                for _ in range(repeats):
                    for i, (status, time_ms) in enumerate(zip(pattern['status'], pattern['time_ms_original'])):
                        if isinstance(status, int) and 0 < status < 255:
                            # This is a PWM value
                            segments.append({
                                'start': status,
                                'end': status,
                                'duration': time_ms,
                                'mode': 'L',
                                't_start': 0,
                                't_end': 1
                            })
                        elif status == 1 or status == 255:
                            # ON state
                            segments.append({
                                'start': 255,
                                'end': 255,
                                'duration': time_ms,
                                'mode': 'L',
                                't_start': 0,
                                't_end': 1
                            })
                        else:
                            # OFF state
                            segments.append({
                                'start': 0,
                                'end': 0,
                                'duration': time_ms,
                                'mode': 'L',
                                't_start': 0,
                                't_end': 1
                            })
            else:
                # Regular ON/OFF patterns - include for complete timeline
                for _ in range(repeats):
                    for status, time_ms in zip(pattern.get('status', [0]), pattern.get('time_ms_original', [1000])):
                        # Handle status value: 255 or 1 = ON (full brightness), 0 = OFF
                        if status >= 1:
                            pwm = 255 if status == 1 else status  # status could be a PWM value
                        else:
                            pwm = 0
                        segments.append({
                            'start': pwm,
                            'end': pwm,
                            'duration': time_ms,
                            'mode': 'L',
                            't_start': 0,
                            't_end': 1
                        })
        
        if segments:
            channel_intensity_data[ch_num] = segments
    
    channel_intensity_json = json.dumps(channel_intensity_data)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Protocol Visualization - Light Controller v2.2</title>
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
        
        .channels-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
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
            <div class="subtitle">Light Controller v2.2</div>
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
    
    <div class="channels-container">
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
                    
                    if pattern['pulse'] and state == 1:
                        state_class = 'pulsing'
                        state_text = '≈'
                    elif state == 1 or state == 255:
                        state_class = 'on'
                        state_text = '█'
                    elif state == 0:
                        state_class = 'off'
                        state_text = '░'
                    else:
                        # PWM value between 0-255
                        brightness = int(50 + (state / 255) * 150)
                        state_class = 'pwm'
                        state_text = str(state)
                    
                    # Handle PWM states with inline style
                    if state not in [0, 1, 255]:
                        brightness = int(50 + (state / 255) * 150)
                        html += f'''
                            <div class="timeline-segment" style="width: {width_percent}%; 
                                background: rgb({brightness}, {brightness + 50}, {brightness//2});
                                border: 1px solid #4CAF50; color: #fff; font-size: 10px; text-shadow: 1px 1px 1px #000;" title="PWM: {state}">
                                {state_text}
                            </div>
'''
                    else:
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
        
        // Calculate current position for a channel
        function calculatePosition(channel, elapsedMs) {{
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
                    pattern_start_ms: 0
                }};
            }}
            
            let totalElapsed = 0;
            
            for (let pIdx = 0; pIdx < channel.length; pIdx++) {{
                const pattern = channel[pIdx];
                const cycleDuration = pattern.time_ms_original.reduce((a, b) => a + b, 0);
                const patternDuration = cycleDuration * pattern.repeats;
                
                if (totalElapsed + patternDuration > elapsedMs) {{
                    // Current pattern
                    const patternElapsed = elapsedMs - totalElapsed;
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
                    
                    // Calculate position percentage within the entire channel timeline
                    let channelTotalDuration = 0;
                    for (let p = 0; p < channel.length; p++) {{
                        const pd = channel[p].time_ms_original.reduce((a, b) => a + b, 0) * channel[p].repeats;
                        channelTotalDuration += pd;
                    }}
                    const positionPercent = (elapsedMs / channelTotalDuration) * 100;
                    
                    // Check if this is pattern 0 (wait pattern) - treat as "waiting"
                    const isWaitingPattern = (pattern.pattern === 0);
                    
                    return {{
                        elapsed_ms: elapsedMs,
                        current_pattern: pIdx,
                        current_cycle: currentCycle,
                        current_state: currentState,
                        status: pattern.status[currentState],
                        is_pulsing: pattern.pulse ? true : false,  // Show pulse even during waiting
                        pulse_info: pattern.pulse ? pattern : null,  // Include pulse info even during waiting
                        completed: false,
                        waiting: isWaitingPattern,
                        position_percent: positionPercent,
                        pattern_start_ms: totalElapsed
                    }};
                }}
                
                totalElapsed += patternDuration;
            }}
            
            // Completed
            return {{
                elapsed_ms: elapsedMs,
                current_pattern: channel.length - 1,
                current_cycle: channel[channel.length - 1].repeats - 1,
                current_state: channel[channel.length - 1].status.length - 1,
                status: 0,
                is_pulsing: false,
                pulse_info: null,
                completed: true,
                waiting: false,
                position_percent: 100,
                pattern_start_ms: totalElapsed
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
                        const pos = calculatePosition(channel, channelElapsed);

                        // Compute total channel duration and remaining time
                        const channelTotalDuration = channel.reduce((acc, p) => {{
                            const cycle = p.time_ms_original.reduce((a, b) => a + b, 0);
                            return acc + cycle * p.repeats;
                        }}, 0);
                        const remainingMs = Math.max(0, channelTotalDuration - pos.elapsed_ms);
                        if (cached.leftTime) {{
                            cached.leftTime.textContent = formatTime(remainingMs);
                        }}

                        // Update per-pattern remaining times for this channel
                        const meta = channelsMeta[chNum];
                        if (meta) {{
                            for (let pi = 0; pi < meta.starts.length; pi++) {{
                                const startMs = meta.starts[pi];
                                const dur = meta.durations[pi];
                                let leftForPattern = 0;

                                if (pos.elapsed_ms < startMs) {{
                                    leftForPattern = dur;
                                }} else if (pos.elapsed_ms >= startMs + dur) {{
                                    leftForPattern = 0;
                                }} else {{
                                    leftForPattern = (startMs + dur) - pos.elapsed_ms;
                                }}

                                const el = document.getElementById('ch' + chNum + '_pat' + pi + '_left');
                                if (el) {{
                                    el.textContent = formatTime(leftForPattern);
                                }}
                            }}
                        }}
                        
                        // Update LED and status text
                        if (pos.waiting) {{
                            // Show actual ON/OFF status even during waiting
                            if (pos.is_pulsing) {{
                                cached.led.className = 'status-led pulsing';
                                cached.statusText.textContent = '⏰ WAITING - PULSING ≈';
                            }} else if (pos.status === 1) {{
                                cached.led.className = 'status-led on';
                                cached.statusText.textContent = '⏰ WAITING - ON █';
                            }} else {{
                                cached.led.className = 'status-led off';
                                cached.statusText.textContent = '⏰ WAITING - OFF ░';
                            }}
                        }} else if (pos.completed) {{
                            cached.led.className = 'status-led completed';
                            cached.statusText.textContent = 'COMPLETED ✓';
                        }} else if (pos.is_pulsing) {{
                            cached.led.className = 'status-led pulsing';
                            cached.statusText.textContent = 'PULSING ≈';
                        }} else if (pos.status === 1) {{
                            cached.led.className = 'status-led on';
                            cached.statusText.textContent = 'ON █';
                        }} else {{
                            cached.led.className = 'status-led off';
                            cached.statusText.textContent = 'OFF ░';
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
                                
                                cached.infoDiv.innerHTML = `
                                    <div>Pattern: ${{pos.current_pattern + 1}}/${{channel.length}}</div>
                                    <div>Cycle: ${{pos.current_cycle + 1}}/${{currentPattern.repeats}}</div>
                                    <div style="color: #fff;">Protocol Elapsed: ${{protocolElapsedDisplay}}</div>
                                    <div style="font-size: 1.15em; color: #fff; font-weight: bold; margin-top: 6px;">Total Left: ${{formatTime(remainingMs)}}</div>
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
                                        const patternElapsed = pos.elapsed_ms - pos.pattern_start_ms;
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
                        const pos = calculatePosition(channel, 0);
                        
                        if (cached && cached.led && cached.statusText) {{
                            if (pos.completed) {{
                                cached.led.className = 'status-led completed';
                                cached.statusText.textContent = 'COMPLETED ✓';
                            }} else {{
                                cached.led.className = 'status-led off';
                                cached.statusText.textContent = 'Ready';
                            }}
                            
                            if (cached.infoDiv) {{
                                // Compute total duration for this channel (static display)
                                let channelTotalDuration = 0;
                                for (let pIdx = 0; pIdx < channel.length; pIdx++) {{
                                    const p = channel[pIdx];
                                    const cycle = p.time_ms_original.reduce((a, b) => a + b, 0);
                                    channelTotalDuration += cycle * p.repeats;
                                }}

                                cached.infoDiv.innerHTML = `
                                    <div>Pattern: ${{pos.current_pattern + 1}}/${{channel.length}}</div>
                                    <div>Cycle: ${{pos.current_cycle + 1}}/${{channel[pos.current_pattern].repeats}}</div>
                                    <div>Elapsed: ${{formatTime(0)}}</div>
                                    <div style="font-size: 1.15em; color: #333; font-weight: bold; margin-top: 6px;">Total Left: ${{formatTime(channelTotalDuration - pos.elapsed_ms)}}</div>
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
        
        // Render intensity plots for all channels
        Object.keys(channelIntensityData).forEach(chNum => {{
            const plotDiv = document.getElementById(`intensity-plot-ch${{chNum}}`);
            if (!plotDiv) return;
            
            const segments = channelIntensityData[chNum];
            if (!segments || segments.length === 0) return;
            
            const curve = generateIntensityCurve(segments);
            
            const trace = {{
                x: curve.times,
                y: curve.intensities,
                type: 'scatter',
                mode: 'lines',
                fill: 'tozeroy',
                fillcolor: 'rgba(102, 126, 234, 0.3)',
                line: {{
                    color: '#667eea',
                    width: 2
                }},
                name: `Channel ${{chNum}} Intensity`
            }};
            
            const layout = {{
                title: {{
                    text: `PWM Intensity Over Time`,
                    font: {{ size: 14, color: '#333' }}
                }},
                xaxis: {{
                    title: 'Time (seconds)',
                    showgrid: true,
                    gridcolor: '#e0e0e0',
                    zeroline: true
                }},
                yaxis: {{
                    title: 'PWM Value',
                    range: [0, 260],
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
        }});
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
    channels, calib_factor = parse_commands(args.commands_file)
    
    if not channels:
        print("Error: No channels found in commands file")
        sys.exit(1)
    
    print(f"Found {len(channels)} channels")
    print(f"Calibration Factor: {calib_factor:.5f}")
    
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
    generate_html(channels, positions, output_file, upload_time, channel_start_times)


if __name__ == '__main__':
    main()
