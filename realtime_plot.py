#!/usr/bin/env python3
"""
Real-Time PWM/DAC Monitoring Plot with Per-Channel Subplots

Uses Matplotlib for real-time visualization of Arduino $CHMON messages.
Each channel gets its own subplot with the appropriate Y-axis scale:
- PWM channels: 0-255 (8-bit)
- DAC channels: 0-4095 (12-bit)
- Binary channels: 0-1 (when PWM mode disabled)

Features:
- Real-time scrolling line chart for each channel
- Per-channel Y-axis scales based on channel type
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
# Extended to support up to 16 channels
CHANNEL_COLORS = [
    '#FFFF00',    # CH1: Yellow
    '#00FFFF',    # CH2: Cyan  
    '#FF00FF',    # CH3: Magenta
    '#00FF00',    # CH4: Green
    '#FF8000',    # CH5: Orange
    '#8080FF',    # CH6: Light blue
    '#FF8080',    # CH7: Pink
    '#80FF80',    # CH8: Light green
    '#FFD700',    # CH9: Gold
    '#40E0D0',    # CH10: Turquoise
    '#FF69B4',    # CH11: Hot pink
    '#32CD32',    # CH12: Lime green
    '#FF4500',    # CH13: Orange red
    '#9370DB',    # CH14: Medium purple
    '#F0E68C',    # CH15: Khaki
    '#98FB98',    # CH16: Pale green
]

# Channel type constants (matching Arduino)
OUTPUT_TYPE_PWM = 'P'       # 8-bit (0-255)
OUTPUT_TYPE_DAC = 'D'       # 12-bit native DAC (0-4095)
OUTPUT_TYPE_MCP4728 = 'M'   # 12-bit MCP4728 DAC (0-4095)
OUTPUT_TYPE_BINARY = 'B'    # Binary (0 or 1)


def get_channel_range(channel_type: str, pwm_ramp_enabled: bool = True) -> Tuple[int, int, str]:
    """
    Get the value range for a channel type.
    
    Args:
        channel_type: 'P' (PWM), 'D' (DAC), 'M' (MCP4728), 'B' (Binary)
        pwm_ramp_enabled: If False, PWM channels behave as binary (0/1)
        
    Returns:
        (min_val, max_val, label) tuple
    """
    if channel_type == OUTPUT_TYPE_BINARY:
        return (0, 1, 'Binary (0-1)')
    elif channel_type == OUTPUT_TYPE_PWM:
        if pwm_ramp_enabled:
            return (0, 255, 'PWM (0-255)')
        else:
            return (0, 1, 'Digital (0-1)')
    elif channel_type in (OUTPUT_TYPE_DAC, OUTPUT_TYPE_MCP4728):
        return (0, 4095, 'DAC (0-4095)')
    else:
        return (0, 255, 'Unknown (0-255)')


# For backwards compatibility with protocol_parser.py
PYQTGRAPH_AVAILABLE = MATPLOTLIB_AVAILABLE


class RealtimePWMPlot:
    """
    Real-time PWM/DAC value plotting with Matplotlib subplots.
    
    Each channel gets its own subplot with the appropriate Y-axis scale
    based on channel type (PWM 0-255, DAC 0-4095, or Binary 0-1).
    """
    
    def __init__(self, 
                 serial_port: Optional[object] = None,
                 port_name: Optional[str] = None,
                 baudrate: int = 9600,
                 max_points: int = 36000,  # 1 hour at 10Hz (for long protocols)
                 display_window: int = 300,  # 5-minute display window
                 csv_output: Optional[str] = None,
                 num_channels: int = 4,
                 html_output: Optional[str] = None,
                 loop_info: Optional[Dict[str, int]] = None,
                 channel_durations: Optional[Dict[str, float]] = None,
                 channel_types: Optional[str] = None,
                 channel_max_values: Optional[List[int]] = None,
                 pwm_ramp_enabled: bool = True):
        """
        Initialize the real-time plot.
        
        Args:
            serial_port: Existing serial.Serial object (if already connected)
            port_name: Serial port name to connect to (if serial_port not provided)
            baudrate: Serial baudrate (default 9600)
            max_points: Maximum points to store (default: 1 hour at 10Hz)
            display_window: Seconds to display in moving window (default: 300 = 5 min)
            csv_output: Path to save CSV data (optional)
            num_channels: Number of channels to display (1-16)
            html_output: Path to save Plotly HTML visualization (optional)
            loop_info: Dict of channel loop settings (for info display only)
            channel_durations: Dict of channel durations in ms (for info display only)
            channel_types: String of channel types from Arduino (e.g., "PPMM" or "MMPP")
            channel_max_values: List of max values per channel (e.g., [255, 255, 4095, 4095])
            pwm_ramp_enabled: If False, PWM channels display as binary (0/1)
        """
        self.serial_port = serial_port
        self.port_name = port_name
        self.baudrate = baudrate
        self.max_points = max_points
        self.display_window = display_window
        self.csv_output = csv_output
        self.html_output = html_output
        self.num_channels = min(num_channels, 16)  # Support up to 16 channels
        
        # Channel configuration
        self.channel_types = channel_types or ('P' * self.num_channels)  # Default to PWM
        self.channel_max_values = channel_max_values or [255] * self.num_channels
        self.pwm_ramp_enabled = pwm_ramp_enabled
        
        # LOOP info (for display only - Arduino handles actual looping)
        self.loop_info = loop_info or {}
        self.channel_durations = channel_durations or {}
        
        # Maximum supported channels (can be extended if needed)
        self.max_supported_channels = 16
        
        # Store ALL data for HTML export (not limited by display window)
        self.all_time_data = []
        self.all_channel_data = [[] for _ in range(self.max_supported_channels)]
        
        # Data storage
        self.time_data = deque(maxlen=max_points)
        self.channel_data = [deque(maxlen=max_points) for _ in range(self.max_supported_channels)]
        self.start_time = None
        
        # CSV file
        self.csv_file = None
        self.csv_writer = None
        
        # Status
        self.running = True
        self.last_values = [0] * self.max_supported_channels  # Raw values from Arduino
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
    
    def _get_channel_config(self, ch_idx: int) -> Tuple[int, int, str]:
        """Get min, max, and label for a channel based on its type."""
        if ch_idx < len(self.channel_types):
            ch_type = self.channel_types[ch_idx]
        else:
            ch_type = OUTPUT_TYPE_PWM
        
        return get_channel_range(ch_type, self.pwm_ramp_enabled)
    
    def _format_channel_value(self, ch_idx: int, value: int) -> str:
        """Format a channel value for display based on channel type."""
        min_val, max_val, _ = self._get_channel_config(ch_idx)
        
        if max_val == 1:
            return f"{value}"  # Binary: just 0 or 1
        elif max_val == 255:
            return f"{value:3d}"  # PWM: 3 digits
        else:
            return f"{value:4d}"  # DAC: 4 digits
    
    def _setup_plot(self):
        """Setup the Matplotlib figure with subplots for each channel."""
        plt.style.use('dark_background')
        
        # Create figure with subplots - one row per channel
        self.fig, self.axes = plt.subplots(
            nrows=self.num_channels, 
            ncols=1, 
            figsize=(14, 2.5 * self.num_channels),
            sharex=True
        )
        
        # Handle single channel case
        if self.num_channels == 1:
            self.axes = [self.axes]
        
        self.fig.canvas.manager.set_window_title('🔌 Real-Time Channel Monitor')
        
        # Configure each subplot
        self.lines = []
        for i, ax in enumerate(self.axes):
            min_val, max_val, label = self._get_channel_config(i)
            
            # Add padding to y-axis
            if max_val == 1:
                y_padding = 0.2
            elif max_val == 255:
                y_padding = 25
            else:
                y_padding = 400
            
            ax.set_xlim(0, self.display_window)
            ax.set_ylim(-y_padding, max_val + y_padding)
            ax.set_ylabel(f'CH{i+1}\n{label}', fontsize=9, rotation=0, ha='right', va='center')
            ax.yaxis.set_label_coords(-0.08, 0.5)
            ax.grid(True, alpha=0.3)
            
            # Reference lines at min and max
            ax.axhline(y=0, color='white', linestyle='-', alpha=0.3, linewidth=0.5)
            ax.axhline(y=max_val, color='white', linestyle='-', alpha=0.3, linewidth=0.5)
            if max_val > 1:
                ax.axhline(y=max_val/2, color='white', linestyle='--', alpha=0.2, linewidth=0.5)
            
            # Create line for this channel
            line, = ax.plot([], [], 
                           color=CHANNEL_COLORS[i], 
                           linewidth=1.5,
                           drawstyle='steps-post',
                           label=f'CH{i+1}')
            self.lines.append(line)
            
            # Add value text annotation on right side
            ax.value_text = ax.text(0.98, 0.85, '', 
                                    transform=ax.transAxes,
                                    fontsize=11,
                                    fontweight='bold',
                                    verticalalignment='top',
                                    horizontalalignment='right',
                                    fontfamily='monospace',
                                    color=CHANNEL_COLORS[i],
                                    bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
        
        # Only bottom subplot gets x-axis label
        self.axes[-1].set_xlabel('Time (seconds)', fontsize=11)
        
        # Add main title with status
        self.title_text = self.fig.suptitle(
            f'Real-Time Channel Monitoring ({self.display_window//60} min window)',
            fontsize=14, fontweight='bold', y=0.995
        )
        
        # Status text at top
        self.status_text = self.fig.text(
            0.02, 0.995, '', 
            fontsize=10,
            verticalalignment='top',
            fontfamily='monospace',
            color='white'
        )
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.95, hspace=0.15)
    
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
            # Header - use num_channels for displayed channels
            headers = ['timestamp', 'time_ms'] + [f'CH{i+1}' for i in range(self.num_channels)]
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
            values = [0] * self.max_supported_channels
            
            for part in parts:
                if ':' in part:
                    ch_part, val_part = part.split(':')
                    ch_num = int(ch_part.replace('CH', '')) - 1
                    if 0 <= ch_num < self.max_supported_channels:
                        values[ch_num] = int(val_part)
            
            # Calculate elapsed time
            elapsed = (datetime.now() - self.start_time).total_seconds()
            
            # Store raw data for plotting
            self.time_data.append(elapsed)
            for i, val in enumerate(values):
                self.channel_data[i].append(val)
                self.last_values[i] = val
            
            self.message_count += 1
            
            # Store ALL data for HTML export
            self.all_time_data.append(elapsed)
            for i, val in enumerate(values):
                self.all_channel_data[i].append(val)
            
            # Write to CSV (only num_channels columns)
            if self.csv_writer:
                row = [datetime.now().isoformat(), int(elapsed * 1000)] + values[:self.num_channels]
                self.csv_writer.writerow(row)
                self.csv_file.flush()
            
            return True
            
        except Exception as e:
            # Silently ignore parse errors
            return False
    
    def _update(self, frame):
        """Animation update function for subplots."""
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
            
            # Update each channel's subplot
            for i, (line, ax) in enumerate(zip(self.lines, self.axes)):
                if i < len(self.channel_data):
                    ch_values = list(self.channel_data[i])
                    line.set_data(times, ch_values)
                    
                    # Update value text on each subplot
                    value_str = self._format_channel_value(i, self.last_values[i])
                    ax.value_text.set_text(value_str)
            
            # Adjust x-axis for scrolling effect
            headroom = self.display_window * 0.1
            if times[-1] > self.display_window - headroom:
                for ax in self.axes:
                    ax.set_xlim(times[-1] - self.display_window + headroom, times[-1] + headroom)
            else:
                for ax in self.axes:
                    ax.set_xlim(0, self.display_window)
        
        # Update status text
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        # Check if any channel has LOOP enabled
        has_loop = self.loop_info and any(v == 1 for v in self.loop_info.values())
        loop_str = ' | [LOOP]' if has_loop else ''
        
        self.status_text.set_text(f'Time: {elapsed:.1f}s | Samples: {self.message_count}{loop_str}')
        
        return self.lines
    
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
            blit=False,  # Can't use blit with multiple subplots + text updates
            cache_frame_data=False
        )
        
        # Handle window close
        def on_close(event):
            self.running = False
            self._cleanup()
        
        self.fig.canvas.mpl_connect('close_event', on_close)
        
        # Show plot (blocking)
        try:
            plt.show()
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            self._cleanup()
    
    def _save_plotly_html(self):
        """Save an interactive Plotly HTML visualization with subplots for each channel."""
        if not self.all_time_data or not self.html_output:
            return
        
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            # Create figure with subplots
            fig = make_subplots(
                rows=self.num_channels, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=[f'CH{i+1}' for i in range(self.num_channels)]
            )
            
            # Add traces for each channel
            for i in range(self.num_channels):
                if len(self.all_channel_data[i]) > 0:
                    min_val, max_val, label = self._get_channel_config(i)
                    
                    fig.add_trace(
                        go.Scatter(
                            x=self.all_time_data,
                            y=self.all_channel_data[i],
                            mode='lines',
                            name=f'CH{i+1} ({label})',
                            line=dict(color=CHANNEL_COLORS[i], width=2, shape='hv')
                        ),
                        row=i+1, col=1
                    )
                    
                    # Set y-axis range for this subplot
                    y_padding = max_val * 0.1 if max_val > 1 else 0.2
                    fig.update_yaxes(
                        range=[-y_padding, max_val + y_padding],
                        title_text=label,
                        row=i+1, col=1
                    )
            
            # Calculate total duration
            total_seconds = self.all_time_data[-1] if self.all_time_data else 0
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            duration_str = f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s"
            
            # Build loop info string for title
            loop_info_str = ''
            if self.loop_info and any(v == 1 for v in self.loop_info.values()):
                looping_channels = [ch for ch, v in self.loop_info.items() if v == 1]
                loop_info_str = f' | [LOOP]: {", ".join(looping_channels)}'
            
            # Update layout
            fig.update_layout(
                title=dict(
                    text=f'Channel Monitoring Data - Duration: {duration_str} ({self.message_count} samples){loop_info_str}',
                    font=dict(size=16)
                ),
                height=200 * self.num_channels + 100,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hovermode='x unified',
                template='plotly_dark'
            )
            
            # X-axis label only on bottom subplot
            fig.update_xaxes(title_text='Time (seconds)', row=self.num_channels, col=1)
            
            # Add range slider for navigation
            fig.update_xaxes(rangeslider_visible=True, row=self.num_channels, col=1)
            
            # Save to HTML
            fig.write_html(self.html_output, include_plotlyjs=True)
            print(f'📊 Plotly visualization saved: {self.html_output}')
            
        except ImportError:
            print('Warning: plotly not installed. Cannot save HTML visualization.')
        except Exception as e:
            print(f'Warning: Could not save Plotly HTML: {e}')
    
    def _cleanup(self):
        """Cleanup resources, stop Arduino monitoring, and save HTML visualization."""
        # Stop Arduino channel monitoring
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(b'MONITOR_ENABLE:0\n')
                self.serial_port.flush()
            except Exception:
                pass  # Ignore errors if port already closed
        
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
        
        # Save Plotly HTML visualization
        if self.html_output:
            self._save_plotly_html()
    
    def close(self):
        """Close the plot and cleanup."""
        self.running = False
        self._cleanup()
        plt.close(self.fig)


def run_realtime_plot(serial_port=None,
                      port_name: Optional[str] = None,
                      csv_output: Optional[str] = None,
                      html_output: Optional[str] = None,
                      num_channels: int = 4,
                      duration: Optional[float] = None,
                      loop_info: Optional[Dict[str, int]] = None,
                      channel_durations: Optional[Dict[str, float]] = None,
                      channel_types: Optional[str] = None,
                      channel_max_values: Optional[List[int]] = None,
                      pwm_ramp_enabled: bool = True) -> Optional[Tuple]:
    """
    Launch the real-time PWM/DAC visualization with per-channel subplots.
    
    Args:
        serial_port: Existing serial connection (optional)
        port_name: Port to connect to (if serial_port not provided)
        csv_output: Path to save CSV data
        html_output: Path to save Plotly HTML visualization
        num_channels: Number of channels to display
        duration: Maximum duration in seconds
        loop_info: Dict of channel loop settings e.g. {'CH1': 1, 'CH2': 0} (1=loop forever)
        channel_durations: Dict of channel durations in ms e.g. {'CH1': 60000, 'CH2': 120000}
        channel_types: String of channel types from Arduino (e.g., "PPMM" or "MMPP")
        channel_max_values: List of max values per channel (e.g., [255, 255, 4095, 4095])
        pwm_ramp_enabled: If False, PWM channels display as binary (0/1)
    
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
            html_output=html_output,
            num_channels=num_channels,
            loop_info=loop_info,
            channel_durations=channel_durations,
            channel_types=channel_types,
            channel_max_values=channel_max_values,
            pwm_ramp_enabled=pwm_ramp_enabled
        )
        
        # Run the plot (blocking)
        plot.run(duration=duration)
        
        return (plot, None)
        
    except Exception as e:
        print(f"Error launching real-time plot: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description='Real-time PWM/DAC visualization from Arduino $CHMON messages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python realtime_plot.py --port /dev/cu.usbmodem1101
    python realtime_plot.py --port COM3 --duration 120
    python realtime_plot.py --port /dev/ttyACM0 --output data.csv --html data.html
    python realtime_plot.py --port /dev/cu.usbmodem1101 --channel-types MMPP
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
    parser.add_argument('--html', default=None,
                       help='Output Plotly HTML file path')
    parser.add_argument('--channels', '-c', type=int, default=4,
                       help='Number of channels to display (1-16, default: 4)')
    parser.add_argument('--channel-types', '-t', default=None,
                       help='Channel types string (e.g., "PPMM" for 2 PWM + 2 MCP4728)')
    parser.add_argument('--no-pwm-ramp', action='store_true',
                       help='Treat PWM channels as binary (0/1)')
    
    args = parser.parse_args()
    
    if not MATPLOTLIB_AVAILABLE:
        print("Error: matplotlib not installed.")
        print("Install with: pip install matplotlib")
        sys.exit(1)
    
    if not SERIAL_AVAILABLE:
        print("Error: pyserial not installed.")
        print("Install with: pip install pyserial")
        sys.exit(1)
    
    print(f"Starting real-time PWM/DAC monitor (5-minute display window)...")
    print(f"  Port: {args.port}")
    print(f"  Channels: {args.channels}")
    if args.channel_types:
        print(f"  Channel types: {args.channel_types}")
    if args.output:
        print(f"  CSV output: {args.output}")
    if args.html:
        print(f"  HTML output: {args.html}")
    if args.duration:
        print(f"  Duration: {args.duration}s")
    print("\nClose the window or press Ctrl+C to stop.\n")
    
    result = run_realtime_plot(
        port_name=args.port,
        csv_output=args.output,
        html_output=args.html,
        num_channels=args.channels,
        duration=args.duration,
        channel_types=args.channel_types,
        pwm_ramp_enabled=not args.no_pwm_ramp
    )
    
    if result:
        print("\nMonitoring complete.")
    else:
        print("\nMonitoring failed.")
        sys.exit(1)


if __name__ == '__main__':
    main()
