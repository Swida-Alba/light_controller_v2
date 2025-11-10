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
        # Get pattern_length parameter from command line (required)
        pattern_length = 2  # Default value
        if len(sys.argv) > 1:
            try:
                pattern_length = int(sys.argv[1])
                print(f'Using pattern_length: {pattern_length}')
            except ValueError:
                print(f'Error: Invalid pattern_length "{sys.argv[1]}". Must be an integer.')
                print('Usage: python protocol_parser.py [pattern_length]')
                print('Example: python protocol_parser.py 4')
                sys.exit(1)
        else:
            print(f'Using default pattern_length: {pattern_length}')
            print('(To specify: python protocol_parser.py [pattern_length])')
        
        # Select protocol file
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
                                          verify_pattern_length=True):
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
