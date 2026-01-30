"""
Light Controller Protocol Parser

This is a simple wrapper that uses the LightControllerParser class
to parse and execute LED control protocols.

The new class-based approach makes the code much cleaner and more maintainable.
For details, see light_controller_parser.py

=============================================================================
CONFIGURATION OPTIONS
=============================================================================

There are TWO ways to configure this script:

1. IN-FILE SETTINGS (edit the DEFAULT_* variables below):
   - Good for repeated use with the same hardware setup
   - No need to type long command-line arguments each time
   
2. COMMAND-LINE ARGUMENTS (override in-file settings):
   - Good for one-off runs or scripting
   - Takes precedence over in-file settings

=============================================================================
USAGE EXAMPLES
=============================================================================

# Using in-file defaults (after setting DEFAULT_PORT and DEFAULT_PROTOCOL_FILE):
python protocol_parser.py

# Override with command-line arguments:
python protocol_parser.py [pattern_length] [port] [protocol_file] [--monitor]

# Examples:
python protocol_parser.py 2
python protocol_parser.py 2 /dev/cu.usbmodem1101
python protocol_parser.py 2 /dev/cu.usbmodem1101 examples/1min_test.txt
python protocol_parser.py 2 /dev/cu.usbmodem1101 examples/1min_test.txt --monitor

# --monitor flag can appear anywhere:
python protocol_parser.py --monitor 2 /dev/cu.usbmodem1101 examples/1min_test.txt

=============================================================================
FLAGS
=============================================================================

--monitor    Enable real-time monitoring of Arduino $CHMON messages after
             protocol upload. Displays live PWM values and saves to CSV/HTML.
             Overrides DEFAULT_MONITOR_MODE setting.

--no-monitor Disable monitoring even if DEFAULT_MONITOR_MODE is True.
             Useful for scripted/automated runs.

=============================================================================
"""

from light_controller_parser import LightControllerParser
import sys
import os
import subprocess
from datetime import datetime

# File dialog - use tkinter (standard library, always available)
try:
    import tkinter as tk
    from tkinter import filedialog
    USE_TKINTER = True
except ImportError:
    USE_TKINTER = False


# =============================================================================
# IN-FILE SETTINGS - Edit these for your default configuration
# =============================================================================

# Default pattern length (number of patterns per channel)
# Set to None to use default value of 2
DEFAULT_PATTERN_LENGTH = 4

# Default serial port for Arduino connection
# Examples:
#   macOS:   '/dev/cu.usbmodem1101' or '/dev/cu.usbmodem14301'
#   Windows: 'COM3' or 'COM4'
#   Linux:   '/dev/ttyACM0' or '/dev/ttyUSB0'
# Set to None to auto-detect or use file dialog
DEFAULT_PORT = None

# Default protocol file path (relative or absolute)
# Examples:
#   'examples/1min_test.txt'
#   'examples/auto_calibration/simple_blink_example.txt'
#   '/Users/username/protocols/my_protocol.txt'
# Set to None to use file dialog
DEFAULT_PROTOCOL_FILE = None

# Default monitor mode (real-time PWM visualization)
# True:  Always enable monitoring (show live PWM values after upload)
# False: Disable monitoring by default
# Can be overridden by --monitor or --no-monitor flags
DEFAULT_MONITOR_MODE = True

# Default monitor print step in milliseconds (how often Arduino sends PWM values)
# 100ms = 10 samples/second (good for capturing fast pulses)
# 1000ms = 1 sample/second (lower data rate)
# Range: 10-10000ms
DEFAULT_MONITOR_STEP_MS = 100

# =============================================================================


if __name__ == '__main__':
    print('Welcome to use the light controller!')
    
    try:
        # Parse command line arguments
        # Usage: python protocol_parser.py [pattern_length] [port] [protocol_file] [--monitor]
        # Command-line args override in-file DEFAULT_* settings
        
        pattern_length = DEFAULT_PATTERN_LENGTH or 2
        port = DEFAULT_PORT
        protocol_file = DEFAULT_PROTOCOL_FILE
        
        # Monitor mode: check flags first, then fall back to in-file setting
        # --monitor forces ON, --no-monitor forces OFF, otherwise use DEFAULT_MONITOR_MODE
        if '--monitor' in sys.argv:
            monitor_mode = True
            monitor_source = 'from --monitor flag'
        elif '--no-monitor' in sys.argv:
            monitor_mode = False
            monitor_source = 'from --no-monitor flag'
        else:
            monitor_mode = DEFAULT_MONITOR_MODE
            monitor_source = 'from in-file setting'
        
        # Remove monitor flags from argv for positional argument parsing
        args = [a for a in sys.argv if a not in ('--monitor', '--no-monitor')]
        
        if len(args) > 1:
            try:
                pattern_length = int(args[1])
                print(f'Using pattern_length: {pattern_length} (from command line)')
            except ValueError:
                print(f'Error: Invalid pattern_length "{args[1]}". Must be an integer.')
                print('Usage: python protocol_parser.py [pattern_length] [port] [protocol_file] [--monitor]')
                print('Example: python protocol_parser.py 2 /dev/cu.usbmodem1101 protocol.txt --monitor')
                sys.exit(1)
        elif DEFAULT_PATTERN_LENGTH:
            print(f'Using pattern_length: {pattern_length} (from in-file setting)')
        else:
            print(f'Using default pattern_length: {pattern_length}')
        
        # Get port from command line if provided, otherwise use in-file default
        if len(args) > 2:
            port = args[2]
            print(f'Using port: {port} (from command line)')
        elif DEFAULT_PORT:
            print(f'Using port: {port} (from in-file setting)')
        
        # Get protocol file from command line if provided, otherwise defer to after connection
        if len(args) > 3:
            protocol_file = args[3]
            if not os.path.exists(protocol_file):
                print(f'Error: Protocol file not found: {protocol_file}')
                sys.exit(1)
            print(f'Using protocol file: {protocol_file} (from command line)')
        elif DEFAULT_PROTOCOL_FILE:
            if not os.path.exists(protocol_file):
                print(f'Warning: In-file protocol file not found: {protocol_file}')
                protocol_file = None
            else:
                print(f'Using protocol file: {protocol_file} (from in-file setting)')
        
        if monitor_mode:
            print(f'Monitor mode: ENABLED ({monitor_source})')
        else:
            print(f'Monitor mode: DISABLED ({monitor_source})')
        
        # =================================================================
        # STEP 1: Connect to Arduino FIRST (before protocol selection)
        # =================================================================
        from lcfunc import SetUpSerialPort, ClearSerialBuffer, SendGreeting, SetMonitorEnabled
        
        print('\n' + '='*60)
        print('STEP 1: Connecting to Arduino...')
        print('='*60)
        
        ser = SetUpSerialPort(board_type='Arduino', baudrate=9600, port=port)
        if not ser:
            raise ValueError('Serial port is not available.')
        
        # Clear buffer and send greeting to confirm board connection
        ClearSerialBuffer(ser, print_flag=True)
        arduino_config = SendGreeting(ser)
        
        print(f'\n✓ Arduino connected successfully!')
        if arduino_config:
            print(f'  Board config: PATTERN_LENGTH={arduino_config.get("pattern_length", "?")}')
            # Show channel types if available
            channel_types = arduino_config.get('channel_types', '')
            if channel_types:
                type_names = {'P': 'PWM', 'D': 'DAC', 'M': 'MCP4728', 'B': 'Binary'}
                ch_info = [f'CH{i+1}:{type_names.get(t, t)}' for i, t in enumerate(channel_types)]
                print(f'  Channel types: {", ".join(ch_info)}')        
        # Configure monitor mode on Arduino
        print(f'\n📡 Configuring Arduino monitor...')
        SetMonitorEnabled(ser, enabled=monitor_mode)
        
        # =================================================================
        # STEP 2: Select protocol file (after board is confirmed)
        # =================================================================
        print('\n' + '='*60)
        print('STEP 2: Selecting protocol file...')
        print('='*60)
        
        # If no protocol file provided, use file dialog NOW
        if not protocol_file:
            print('\nPlease select your protocol file...')
            
            if USE_TKINTER:
                # Use tkinter file dialog (standard library)
                root = tk.Tk()
                root.withdraw()  # Hide the root window
                protocol_file = filedialog.askopenfilename(
                    title='Select the protocol file',
                    filetypes=[('Protocol files', '*.xlsx *.txt'), ('Excel files', '*.xlsx'), ('Text files', '*.txt')]
                )
                root.destroy()
            else:
                print('Error: No GUI available for file selection.')
                print('Please provide protocol file as argument.')
                protocol_file = None
        
        if not protocol_file:
            print('No file selected. Exiting.')
            ser.close()
        else:
            print(f'\nSelected protocol: {protocol_file}')
            
            # =================================================================
            # STEP 3: Parse and execute protocol
            # =================================================================
            print('\n' + '='*60)
            print('STEP 3: Parsing and executing protocol...')
            print('='*60)
            
            # Create parser instance (using context manager for automatic cleanup)
            # Pass the already-connected serial port
            with LightControllerParser(protocol_file, pattern_length=pattern_length, calibration_method='v2') as parser:
                # Use existing serial connection instead of setting up new one
                parser.ser = ser
                parser.arduino_config = arduino_config
                
                # Generate and send commands (serial already connected)
                parser.generate_pattern_commands()
                commands_file = parser.parse_and_execute()
                print(f'\nProtocol execution completed successfully!')
                print(f'Commands saved to: {commands_file}')
                
                # Automatically generate HTML visualization
                print('\n' + '='*70)
                print('🎨 Generating interactive HTML visualization...')
                print('='*70)
                
                try:
                    # Get upload time (now - when commands are uploaded)
                    upload_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Generate HTML visualization with real-time status
                    viz_script = os.path.join(os.path.dirname(__file__), 'viz_protocol_html.py')
                    
                    if os.path.exists(viz_script):
                        result = subprocess.run(
                            ['python', viz_script, commands_file, '--upload-time', upload_time],
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode == 0:
                            print(result.stdout)
                            
                            # Extract HTML filename from output
                            for line in result.stdout.split('\n'):
                                if 'HTML visualization saved:' in line:
                                    html_file = line.split(': ')[1].strip()
                                    
                                    # Try to open in browser
                                    try:
                                        if sys.platform == 'darwin':  # macOS
                                            subprocess.run(['open', html_file])
                                        elif sys.platform == 'win32':  # Windows
                                            subprocess.run(['start', html_file], shell=True)
                                        else:  # Linux
                                            subprocess.run(['xdg-open', html_file])
                                        
                                        print(f'🌐 Opening visualization in browser...')
                                    except:
                                        print(f'📝 Please manually open: {html_file}')
                        else:
                            print(f'⚠️  Visualization failed: {result.stderr}')
                    else:
                        print(f'⚠️  Visualization script not found: {viz_script}')
                        print(f'    You can manually run: python viz_protocol_html.py {commands_file}')
                        
                except Exception as viz_error:
                    print(f'⚠️  Could not generate visualization: {viz_error}')
                    print(f'    Protocol executed successfully, but visualization failed.')
                
                print('='*70)
                
                # Optional: Monitor serial output for $CHMON messages
                if monitor_mode:
                    # Set monitor print step (how often Arduino sends PWM values)
                    from lcfunc import SetMonitorStep, SayBye
                    print(f'\n📡 Configuring monitor...')
                    SetMonitorStep(parser.ser, DEFAULT_MONITOR_STEP_MS)
                    
                    # Send Bye command to start execution (but don't close connection)
                    SayBye(parser.ser)
                    
                    monitor_csv = commands_file.replace('.txt', '_monitored.csv')
                    monitor_html = commands_file.replace('.txt', '_monitored.html')
                    
                    # Get loop info for display in real-time monitor
                    loop_info = parser.loop if hasattr(parser, 'loop') else {}
                    
                    # Print loop info if any channels are looping
                    if loop_info and any(v == 1 for v in loop_info.values()):
                        looping_channels = [ch for ch, v in loop_info.items() if v == 1]
                        print(f'\n🔄 LOOP enabled for: {", ".join(looping_channels)}')
                    
                    # Try to use matplotlib real-time plot window
                    try:
                        from realtime_plot import run_realtime_plot, MATPLOTLIB_AVAILABLE
                        
                        if MATPLOTLIB_AVAILABLE:
                            print('\n📊 Launching real-time PWM visualization window...')
                            print('   (5-minute display window, data saved on close)')
                            print('   Close window or press Ctrl+C to stop\n')
                            
                            # Get channel configuration from Arduino
                            channel_types = parser.arduino_config.get('channel_types', '')
                            channel_max_values = parser.arduino_config.get('channel_max_values', [])
                            pwm_ramp_enabled = parser.arduino_config.get('pwm_ramp_mode', True)
                            
                            # Determine number of channels to monitor
                            # Prioritize Arduino config (physical channels), fallback to protocol usage, then default to 4
                            monitor_channels = len(channel_types) if channel_types else (len(parser.valid_channels) or 4)
                            
                            # run_realtime_plot is blocking - it shows the matplotlib window
                            result = run_realtime_plot(
                                serial_port=parser.ser,
                                csv_output=monitor_csv,
                                html_output=monitor_html,
                                num_channels=monitor_channels,
                                loop_info=loop_info,
                                channel_types=channel_types,
                                channel_max_values=channel_max_values,
                                pwm_ramp_enabled=pwm_ramp_enabled
                            )
                            
                            if result:
                                print(f'\n📊 Data saved to: {monitor_csv}')
                            else:
                                raise ImportError("Matplotlib not available")
                        else:
                            raise ImportError("Matplotlib not available")
                            
                    except ImportError:
                        # Fallback to text-mode monitoring
                        print('\n📊 Monitoring channel values (text mode)...')
                        print('   Install matplotlib for graphical display: pip install matplotlib')
                        print('   Press Ctrl+C to stop\n')
                        
                        csv_file = open(monitor_csv, 'w')
                        csv_file.write("timestamp,time_ms,CH1,CH2,CH3,CH4,CH5,CH6,CH7,CH8\n")
                        start_time = datetime.now()
                        last_print_time = 0
                        
                        try:
                            while True:
                                if parser.ser and parser.ser.in_waiting:
                                    line = parser.ser.readline().decode('utf-8', errors='ignore').strip()
                                    if line.startswith('$CHMON:'):
                                        # Parse: $CHMON:CH1:pwm1,CH2:pwm2,...
                                        elapsed = (datetime.now() - start_time).total_seconds()
                                        channels = {}
                                        for ch_data in line[7:].split(','):
                                            parts = ch_data.split(':')
                                            if len(parts) == 2:
                                                ch_num = int(parts[0][2:])
                                                channels[ch_num] = int(parts[1])
                                        
                                        # Write to CSV
                                        timestamp = datetime.now().isoformat()
                                        values = [channels.get(i, 0) for i in range(1, 9)]
                                        csv_file.write(f"{timestamp},{elapsed*1000:.0f},{','.join(map(str, values))}\n")
                                        csv_file.flush()
                                        
                                        # Print status every 0.5 seconds
                                        if elapsed - last_print_time >= 0.5:
                                            status = f"⏱️  {elapsed:6.1f}s | "
                                            for ch in range(1, min(5, len(channels)+1)):
                                                pwm = channels.get(ch, 0)
                                                bar_len = pwm // 25
                                                bar = '█' * bar_len + '░' * (10 - bar_len)
                                                status += f"CH{ch}: {pwm:3d} [{bar}] | "
                                            print(status)
                                            last_print_time = elapsed
                                    elif line and not line.startswith('$'):
                                        print(f"  < {line}")
                                else:
                                    import time
                                    time.sleep(0.01)
                        except KeyboardInterrupt:
                            print(f'\n\n⏹️  Monitoring stopped')
                            print(f'📊 Data saved to: {monitor_csv}')
                        finally:
                            csv_file.close()
                    
                    # Close serial and mark as closed to prevent double-Bye
                    if parser.ser:
                        parser.ser.close()
                        parser.ser = None
                
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
