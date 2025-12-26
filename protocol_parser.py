"""
Light Controller Protocol Parser

This is a simple wrapper that uses the LightControllerParser class
to parse and execute LED control protocols.

The new class-based approach makes the code much cleaner and more maintainable.
For details, see light_controller_parser.py
"""

from light_controller_parser import LightControllerParser
import tkinter as tk
from tkinter import filedialog
import sys
import os
import subprocess
from datetime import datetime


if __name__ == '__main__':
    print('Welcome to use the light controller!')
    
    try:
        # Parse command line arguments
        # Usage: python protocol_parser.py [pattern_length] [port] [protocol_file] [--monitor]
        pattern_length = 2  # Default value
        port = None
        protocol_file = None
        monitor_mode = '--monitor' in sys.argv
        
        # Remove --monitor from argv for positional argument parsing
        args = [a for a in sys.argv if a != '--monitor']
        
        if len(args) > 1:
            try:
                pattern_length = int(args[1])
                print(f'Using pattern_length: {pattern_length}')
            except ValueError:
                print(f'Error: Invalid pattern_length "{args[1]}". Must be an integer.')
                print('Usage: python protocol_parser.py [pattern_length] [port] [protocol_file] [--monitor]')
                print('Example: python protocol_parser.py 2 /dev/cu.usbmodem1101 protocol.txt --monitor')
                sys.exit(1)
        else:
            print(f'Using default pattern_length: {pattern_length}')
        
        # Get port from command line if provided
        if len(args) > 2:
            port = args[2]
            print(f'Using port: {port}')
        
        # Get protocol file from command line if provided
        if len(args) > 3:
            protocol_file = args[3]
            if not os.path.exists(protocol_file):
                print(f'Error: Protocol file not found: {protocol_file}')
                sys.exit(1)
            print(f'Using protocol file: {protocol_file}')
        
        if monitor_mode:
            print('Monitor mode: ENABLED (will capture $CHMON data after execution)')
        
        # If no protocol file provided, use file dialog
        if not protocol_file:
            print('\nPlease select your protocol file...')
            protocol_file = filedialog.askopenfilename(
                title='Select the protocol file',
                filetypes=[('Protocol files', '*.xlsx *.txt'), ('Excel files', '*.xlsx'), ('Text files', '*.txt')]
            )
        
        if not protocol_file:
            print('No file selected. Exiting.')
        else:
            print(f'\nSelected protocol: {protocol_file}')
            
            # Create parser instance (using context manager for automatic cleanup)
            with LightControllerParser(protocol_file, pattern_length=pattern_length, calibration_method='v2') as parser:
                # Setup serial connection with pattern length verification
                if not parser.setup_serial(board_type='Arduino', baudrate=9600, 
                                          verify_pattern_length=True, port=port):
                    raise ValueError('Serial port is not available.')
                
                # Parse and execute
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
                    # Send Bye command to start execution (but don't close connection)
                    from lcfunc import SayBye
                    SayBye(parser.ser)
                    print('\n📊 Monitoring channel values (Ctrl+C to stop)...\n')
                    
                    monitor_csv = commands_file.replace('.txt', '_monitored.csv')
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
