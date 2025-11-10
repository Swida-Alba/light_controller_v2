"""
Protocol Preview Tool

Preview what commands will be generated from a protocol file without
connecting to hardware. Useful for:
- Validating protocol files
- Testing new protocols
- Debugging command generation
- Educational purposes

Usage:
    python preview_protocol.py                    # Interactive file selection
    python preview_protocol.py protocol.xlsx      # Preview specific file
    python preview_protocol.py protocol.txt -n 5  # Show first 5 commands only
    python preview_protocol.py protocol.xlsx -c 1.00131  # Custom calibration
"""

import sys
import os
import argparse
import tkinter as tk
from tkinter import filedialog
from light_controller_parser import LightControllerParser
import subprocess


def preview_protocol(protocol_file, calib_factor=1.0, max_commands=None, save_output=False):
    """
    Preview protocol commands without hardware.
    
    Args:
        protocol_file (str): Path to protocol file
        calib_factor (float): Calibration factor to use
        max_commands (int): Max commands to display per type (None = all)
        save_output (bool): Save commands to file
        
    Returns:
        dict: Preview data with commands_file key if saved
    """
    try:
        print(f'\n🔍 Previewing protocol: {os.path.basename(protocol_file)}')
        print('-' * 70)
        
        # Create parser
        parser = LightControllerParser(protocol_file)
        
        # Preview without hardware
        preview_data = parser.preview_only(
            calib_factor=calib_factor,
            show_wait=True,
            show_patterns=True,
            max_commands=max_commands
        )
        
        # Always save to file for visualization (even if not explicitly requested)
        commands_file = parser.save_commands()
        preview_data['commands_file'] = commands_file
        
        if save_output:
            print(f'\n💾 Commands saved to: {commands_file}')
        
        return preview_data
        
    except Exception as e:
        print(f'\n❌ Error previewing protocol: {e}')
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main entry point for preview tool."""
    parser = argparse.ArgumentParser(
        description='Preview LED control protocol commands without hardware',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python preview_protocol.py                          # Interactive file picker
  python preview_protocol.py examples/basic_protocol.xlsx
  python preview_protocol.py protocol.txt -n 10       # Show first 10 commands
  python preview_protocol.py protocol.xlsx -c 1.00131 # Custom calibration
  python preview_protocol.py protocol.txt -s          # Save commands to file
        """
    )
    
    parser.add_argument(
        'protocol_file',
        nargs='?',
        help='Path to protocol file (.xlsx or .txt)'
    )
    
    parser.add_argument(
        '-c', '--calib',
        type=float,
        default=1.0,
        help='Calibration factor (default: 1.0)'
    )
    
    parser.add_argument(
        '-n', '--max-commands',
        type=int,
        default=None,
        help='Maximum commands to show per type (default: all)'
    )
    
    parser.add_argument(
        '-s', '--save',
        action='store_true',
        help='Save commands to timestamped file'
    )
    
    args = parser.parse_args()
    
    # Get protocol file
    protocol_file = args.protocol_file
    
    if not protocol_file:
        print('📂 Please select your protocol file...')
        root = tk.Tk()
        root.withdraw()
        protocol_file = filedialog.askopenfilename(
            title='Select protocol file to preview',
            filetypes=[
                ('Protocol files', '*.xlsx *.txt'),
                ('Excel files', '*.xlsx'),
                ('Text files', '*.txt'),
                ('All files', '*.*')
            ]
        )
        
        if not protocol_file:
            print('No file selected. Exiting.')
            return
    
    # Validate file exists
    if not os.path.exists(protocol_file):
        print(f'❌ Error: File not found: {protocol_file}')
        return
    
    # Preview protocol
    preview_data = preview_protocol(
        protocol_file,
        calib_factor=args.calib,
        max_commands=args.max_commands,
        save_output=args.save
    )
    
    if preview_data:
        print('\n✅ Preview completed successfully!')
        print(f'\nQuick Stats:')
        print(f'  • Channels: {len(preview_data["channels"])}')
        print(f'  • Wait commands: {preview_data["total_wait"]}')
        print(f'  • Pattern commands: {preview_data["total_patterns"]}')
        print(f'  • Total commands: {preview_data["total_wait"] + preview_data["total_patterns"]}')
        print(f'  • Calibration: {preview_data["calib_factor"]:.5f}')
        
        # Automatically generate HTML visualization
        if preview_data.get('commands_file'):
            print('\n' + '='*70)
            print('🎨 Generating interactive HTML visualization...')
            print('='*70)
            
            try:
                viz_script = os.path.join(os.path.dirname(__file__), 'viz_protocol_html.py')
                
                if os.path.exists(viz_script):
                    # Get current time as start time for real-time tracking
                    from datetime import datetime
                    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    result = subprocess.run(
                        ['python', viz_script, preview_data['commands_file'], '--start-time', start_time],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        print(result.stdout)
                        
                        # Extract HTML filename and open in browser
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
                        print(f'⚠️  Visualization generation had issues.')
                else:
                    print(f'ℹ️  To generate visualization, run:')
                    print(f'   python viz_protocol_html.py {preview_data["commands_file"]}')
                    
            except Exception as viz_error:
                print(f'⚠️  Could not generate visualization: {viz_error}')
            
            print('='*70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\n⚠️  Preview cancelled by user.')
    except Exception as e:
        print(f'\n❌ Unexpected error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        # Don't auto-close on Windows for debugging
        if sys.platform == 'win32':
            input('\nPress Enter to exit...')
