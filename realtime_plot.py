#!/usr/bin/env python3
"""
Real-Time PWM Monitoring Plot

Uses Matplotlib for real-time visualization of Arduino $CHMON messages.
This module provides a standalone plotting window that can be launched from
protocol_parser.py or used independently.

Matplotlib is used for portability - it works on all platforms without
Qt plugin configuration issues.

Features:
- Real-time scrolling line chart for PWM values
- Color-coded channels (matching oscilloscope colors)
- CSV data logging
- Cross-platform (Windows, macOS, Linux)

Installation:
    pip install matplotlib pyserial

Usage:
    # From command line (standalone):
    python realtime_plot.py --port /dev/cu.usbmodem1101 --duration 60
    
    # From protocol_parser.py (with --monitor flag):
    python protocol_parser.py 2 /dev/cu.usbmodem1101 protocol.txt --monitor
"""

import sys
import os
import time
import csv
import argparse
from datetime import datetime
from collections import deque
from typing import Optional, Dict, List, Tuple

try:
    import matplotlib
    matplotlib.use('TkAgg')  # Use TkAgg backend for cross-platform compatibility
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


# Channel colors (matching common oscilloscope colors)
# RGB tuples normalized to 0-1 for matplotlib
CHANNEL_COLORS = [
    '#FFFF00',    # CH1: Yellow
    '#00FFFF',    # CH2: Cyan  
    '#FF00FF',    # CH3: Magenta
    '#00FF00',    # CH4: Green
    '#FF8000',    # CH5: Orange
    '#8080FF',    # CH6: Light blue
    '#FF8080',    # CH7: Pink
    '#80FF80',    # CH8: Light green
]

# For backwards compatibility with protocol_parser.py
PYQTGRAPH_AVAILABLE = MATPLOTLIB_AVAILABLE


class RealtimePWMPlot:
    """
    Real-time PWM value plotting with Matplotlib.
    
    Displays streaming PWM values from Arduino $CHMON messages in a 
    scrolling line chart format.
    """
    
    def __init__(self, 
                 serial_port: Optional[object] = None,
                 port_name: Optional[str] = None,
                 baudrate: int = 9600,
                 max_points: int = 600,  # 60 seconds at 10Hz
                 csv_output: Optional[str] = None,
                 num_channels: int = 4):
        """
        Initialize the real-time plot.
        
        Args:
            serial_port: Existing serial.Serial object (if already connected)
            port_name: Serial port name to connect to (if serial_port not provided)
            baudrate: Serial baudrate (default 9600)
            max_points: Maximum points to display (rolling window)
            csv_output: Path to save CSV data (optional)
            num_channels: Number of channels to display (1-8)
        """
        self.serial_port = serial_port
        self.port_name = port_name
        self.baudrate = baudrate
        self.max_points = max_points
        self.csv_output = csv_output
        self.num_channels = min(num_channels, 8)
        
        # Data storage
        self.time_data = deque(maxlen=max_points)
        self.channel_data = [deque(maxlen=max_points) for _ in range(8)]
        self.start_time = None
        
        # CSV file
        self.csv_file = None
        self.csv_writer = None
        
        # Status
        self.running = True
        self.last_values = [0] * 8
        self.message_count = 0
        
        # Setup plot
        self._setup_plot()
        
        # Connect to serial if port name provided
        if serial_port is None and port_name:
            self._connect_serial()
        
        # Setup CSV output
        if csv_output:
            self._setup_csv()
        
        self.start_time = datetime.now()
    
    def _setup_plot(self):
        """Setup the Matplotlib figure and axes."""
        # Create figure with dark background for better visibility
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.fig.canvas.manager.set_window_title('🔌 Real-Time PWM Monitor')
        
        # Configure axes
        self.ax.set_xlim(0, 60)  # 60 seconds window
        self.ax.set_ylim(-5, 260)
        self.ax.set_xlabel('Time (seconds)', fontsize=12)
        self.ax.set_ylabel('PWM Value (0-255)', fontsize=12)
        self.ax.set_title('Real-Time PWM Monitoring', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        
        # Add horizontal reference lines
        self.ax.axhline(y=0, color='white', linestyle='-', alpha=0.3, linewidth=0.5)
        self.ax.axhline(y=128, color='white', linestyle='--', alpha=0.2, linewidth=0.5)
        self.ax.axhline(y=255, color='white', linestyle='-', alpha=0.3, linewidth=0.5)
        
        # Create line objects for each channel
        self.lines = []
        for i in range(self.num_channels):
            line, = self.ax.plot([], [], 
                               color=CHANNEL_COLORS[i], 
                               linewidth=2,
                               label=f'CH{i+1}')
            self.lines.append(line)
        
        # Add legend
        self.ax.legend(loc='upper right', fontsize=10, framealpha=0.7)
        
        # Status text
        self.status_text = self.ax.text(0.02, 0.98, '', 
                                        transform=self.ax.transAxes,
                                        fontsize=10,
                                        verticalalignment='top',
                                        fontfamily='monospace',
                                        color='white',
                                        bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
        
        plt.tight_layout()
    
    def _connect_serial(self):
        """Connect to serial port."""
        if not SERIAL_AVAILABLE:
            print("Warning: pyserial not installed. Cannot connect to serial port.")
            return
        
        try:
            self.serial_port = serial.Serial(self.port_name, self.baudrate, timeout=0.1)
            print(f"Connected to {self.port_name}")
        except serial.SerialException as e:
            print(f"Error connecting to {self.port_name}: {e}")
            self.serial_port = None
    
    def _setup_csv(self):
        """Setup CSV output file."""
        try:
            self.csv_file = open(self.csv_output, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            # Header
            headers = ['timestamp', 'time_ms'] + [f'CH{i+1}' for i in range(8)]
            self.csv_writer.writerow(headers)
        except Exception as e:
            print(f"Error setting up CSV: {e}")
            self.csv_file = None
            self.csv_writer = None
    
    def _process_line(self, line: str) -> bool:
        """
        Process a line from serial, looking for $CHMON messages.
        
        Format: $CHMON:CH1:value,CH2:value,...
        
        Returns True if a $CHMON message was processed.
        """
        if not line.startswith('$CHMON:'):
            return False
        
        try:
            # Parse $CHMON:CH1:255,CH2:128,...
            parts = line[7:].split(',')  # Skip "$CHMON:"
            values = [0] * 8
            
            for part in parts:
                if ':' in part:
                    ch_part, val_part = part.split(':')
                    ch_num = int(ch_part.replace('CH', '')) - 1
                    if 0 <= ch_num < 8:
                        values[ch_num] = int(val_part)
            
            # Calculate elapsed time
            elapsed = (datetime.now() - self.start_time).total_seconds()
            
            # Store data
            self.time_data.append(elapsed)
            for i, val in enumerate(values):
                self.channel_data[i].append(val)
                self.last_values[i] = val
            
            self.message_count += 1
            
            # Write to CSV
            if self.csv_writer:
                row = [datetime.now().isoformat(), int(elapsed * 1000)] + values
                self.csv_writer.writerow(row)
                self.csv_file.flush()
            
            return True
            
        except Exception as e:
            # Silently ignore parse errors
            return False
    
    def _update(self, frame):
        """Animation update function."""
        if not self.running:
            return self.lines
        
        # Read from serial
        if self.serial_port:
            try:
                while self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self._process_line(line)
            except Exception:
                pass
        
        # Update plot data
        if len(self.time_data) > 0:
            times = list(self.time_data)
            
            for i, line in enumerate(self.lines):
                if i < len(self.channel_data):
                    line.set_data(times, list(self.channel_data[i]))
            
            # Adjust x-axis for scrolling effect
            if times[-1] > 60:
                self.ax.set_xlim(times[-1] - 60, times[-1])
            else:
                self.ax.set_xlim(0, max(60, times[-1] + 5))
        
        # Update status text
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        values_str = ', '.join([f'CH{i+1}:{self.last_values[i]:3d}' for i in range(self.num_channels)])
        self.status_text.set_text(f'Time: {elapsed:.1f}s | Messages: {self.message_count}\n{values_str}')
        
        return self.lines + [self.status_text]
    
    def run(self, duration: Optional[float] = None):
        """
        Run the real-time plot.
        
        Args:
            duration: Maximum duration in seconds (None for infinite)
        """
        # Create animation
        self.ani = FuncAnimation(
            self.fig,
            self._update,
            interval=100,  # 10 Hz update
            blit=True,
            cache_frame_data=False
        )
        
        # Handle window close
        def on_close(event):
            self.running = False
            if self.csv_file:
                self.csv_file.close()
        
        self.fig.canvas.mpl_connect('close_event', on_close)
        
        # Show plot (blocking)
        try:
            plt.show()
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            if self.csv_file:
                self.csv_file.close()
    
    def close(self):
        """Close the plot and cleanup."""
        self.running = False
        if self.csv_file:
            self.csv_file.close()
        plt.close(self.fig)


def run_realtime_plot(serial_port=None,
                      port_name: Optional[str] = None,
                      csv_output: Optional[str] = None,
                      num_channels: int = 4,
                      duration: Optional[float] = None) -> Optional[Tuple]:
    """
    Launch the real-time PWM visualization.
    
    Args:
        serial_port: Existing serial connection (optional)
        port_name: Port to connect to (if serial_port not provided)
        csv_output: Path to save CSV data
        num_channels: Number of channels to display
        duration: Maximum duration in seconds
    
    Returns:
        Tuple of (plot_object, None) for compatibility, or None if failed
    """
    if not MATPLOTLIB_AVAILABLE:
        print("Error: matplotlib not available. Install with: pip install matplotlib")
        return None
    
    try:
        plot = RealtimePWMPlot(
            serial_port=serial_port,
            port_name=port_name,
            csv_output=csv_output,
            num_channels=num_channels
        )
        
        # Run the plot (blocking)
        plot.run(duration=duration)
        
        return (plot, None)
        
    except Exception as e:
        print(f"Error launching real-time plot: {e}")
        return None


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description='Real-time PWM visualization from Arduino $CHMON messages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python realtime_plot.py --port /dev/cu.usbmodem1101
    python realtime_plot.py --port COM3 --duration 120
    python realtime_plot.py --port /dev/ttyACM0 --output data.csv
        """
    )
    parser.add_argument('--port', '-p', required=True,
                       help='Serial port (e.g., /dev/cu.usbmodem1101, COM3)')
    parser.add_argument('--baudrate', '-b', type=int, default=9600,
                       help='Serial baudrate (default: 9600)')
    parser.add_argument('--duration', '-d', type=float, default=None,
                       help='Duration in seconds (default: unlimited)')
    parser.add_argument('--output', '-o', default=None,
                       help='Output CSV file path')
    parser.add_argument('--channels', '-c', type=int, default=4,
                       help='Number of channels to display (1-8, default: 4)')
    
    args = parser.parse_args()
    
    if not MATPLOTLIB_AVAILABLE:
        print("Error: matplotlib not installed.")
        print("Install with: pip install matplotlib")
        sys.exit(1)
    
    if not SERIAL_AVAILABLE:
        print("Error: pyserial not installed.")
        print("Install with: pip install pyserial")
        sys.exit(1)
    
    print(f"Starting real-time PWM monitor...")
    print(f"  Port: {args.port}")
    print(f"  Channels: {args.channels}")
    if args.output:
        print(f"  CSV output: {args.output}")
    if args.duration:
        print(f"  Duration: {args.duration}s")
    print("\nClose the window or press Ctrl+C to stop.\n")
    
    result = run_realtime_plot(
        port_name=args.port,
        csv_output=args.output,
        num_channels=args.channels,
        duration=args.duration
    )
    
    if result:
        print("\nMonitoring complete.")
    else:
        print("\nMonitoring failed.")
        sys.exit(1)


if __name__ == '__main__':
    main()
