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

# Value range constants for different output types
VALUE_RANGE_BINARY = (0, 1)      # Binary: 0 or 1
VALUE_RANGE_PWM = (0, 255)       # PWM: 8-bit
VALUE_RANGE_DAC = (0, 4095)      # DAC: 12-bit (MCP4728, native DAC)

def detect_value_range(values):
    """
    Detect the value range type from observed values.
    Returns (min_val, max_val, range_type) where range_type is 'binary', 'pwm', or 'dac'.
    """
    if not values:
        return 0, 255, 'pwm'  # Default to PWM range
    
    max_val = max(values)
    min_val = min(values)
    
    if max_val <= 1:
        return 0, 1, 'binary'
    elif max_val <= 255:
        return 0, 255, 'pwm'
    else:
        return 0, 4095, 'dac'

def calculate_dynamic_ylim(values, padding_pct=0.1):
    """
    Calculate dynamic Y-axis limits based on actual data values.
    Adds padding for visual clarity and handles sub-range values.
    
    Args:
        values: List of values
        padding_pct: Padding percentage (default 10%)
    
    Returns:
        (y_min, y_max) tuple for matplotlib ylim
    """
    if not values:
        return -5, 280  # Default PWM range with padding
    
    data_min = min(values)
    data_max = max(values)
    
    # Detect range type
    _, range_max, range_type = detect_value_range(values)
    
    # For narrow ranges, center the view with padding
    data_range = data_max - data_min
    if data_range == 0:
        data_range = max(1, data_max * 0.1)  # Prevent zero range
    
    padding = max(data_range * padding_pct, range_max * 0.02)  # At least 2% of full range
    
    y_min = max(-range_max * 0.02, data_min - padding)  # Small negative for visual clarity
    y_max = min(range_max * 1.05, data_max + padding)  # Cap at 105% of max range
    
    # Ensure minimum visible range (at least 5% of full range)
    if y_max - y_min < range_max * 0.05:
        y_max = y_min + range_max * 0.1
    
    return y_min, y_max

# For backwards compatibility with protocol_parser.py
PYQTGRAPH_AVAILABLE = MATPLOTLIB_AVAILABLE


class RealtimePWMPlot:
    """
    Real-time PWM/DAC value plotting with Matplotlib.
    
    Displays streaming values from Arduino $CHMON messages in a 
    scrolling line chart format. Supports:
    - Binary (0-1): Digital on/off
    - PWM (0-255): 8-bit PWM values, normalized to 0-1
    - DAC (0-4095): 12-bit DAC values (MCP4728, native DAC), normalized to 0-1
    
    All values are normalized to 0-1 range for consistent visualization.
    Y-axis is fixed at [-0.2, 1.2] to show all channel types uniformly.
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
                 channel_durations: Optional[Dict[str, float]] = None):
        """
        Initialize the real-time plot.
        
        Args:
            serial_port: Existing serial.Serial object (if already connected)
            port_name: Serial port name to connect to (if serial_port not provided)
            baudrate: Serial baudrate (default 9600)
            max_points: Maximum points to store (default: 1 hour at 10Hz)
            display_window: Seconds to display in moving window (default: 300 = 5 min)
            csv_output: Path to save CSV data (optional)
            num_channels: Number of channels to display (1-8)
            html_output: Path to save Plotly HTML visualization (optional)
            loop_info: Dict of channel loop settings (for info display only)
            channel_durations: Dict of channel durations in ms (for info display only)
        """
        self.serial_port = serial_port
        self.port_name = port_name
        self.baudrate = baudrate
        self.max_points = max_points
        self.display_window = display_window
        self.csv_output = csv_output
        self.html_output = html_output
        self.num_channels = min(num_channels, 8)
        
        # LOOP info (for display only - Arduino handles actual looping)
        self.loop_info = loop_info or {}  # {'CH1': 1, 'CH2': 0, ...}
        self.channel_durations = channel_durations or {}  # {'CH1': 60000, ...} in ms
        
        # Store ALL data for HTML export (not limited by display window)
        self.all_time_data = []
        self.all_channel_data = [[] for _ in range(8)]
        
        # Data storage
        self.time_data = deque(maxlen=max_points)
        self.channel_data = [deque(maxlen=max_points) for _ in range(8)]
        self.start_time = None
        
        # CSV file
        self.csv_file = None
        self.csv_writer = None
        
        # Status
        self.running = True
        self.last_values = [0] * 8  # Raw values from Arduino
        self.last_values_normalized = [0.0] * 8  # Normalized 0-1 values
        self.message_count = 0
        
        # Detected value range (for normalization)
        self._max_range = 255  # Will be updated based on incoming data (255 for PWM, 4095 for DAC)
        
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
        """Setup the Matplotlib figure and axes with normalized 0-1 Y-axis."""
        # Create figure with dark background for better visibility
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.fig.canvas.manager.set_window_title('🔌 Real-Time Channel Monitor')
        
        # Configure axes - 5 minute (300 second) display window
        # Y-axis fixed at normalized range [-0.2, 1.2] for all value types
        self.ax.set_xlim(0, self.display_window)
        self.ax.set_ylim(-0.2, 1.2)  # Fixed normalized range with padding
        self.ax.set_xlabel('Time (seconds)', fontsize=12)
        self.ax.set_ylabel('Normalized Value (0-1)', fontsize=12)
        self.ax.set_title(f'Real-Time Channel Monitoring ({self.display_window//60} min window)', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        
        # Fixed reference lines for normalized display
        self.ref_lines = []
        self._detected_range = 'pwm'  # Track detected range type for status text
        self._setup_normalized_reference_lines()
        
        # Create line objects for each channel
        # Use 'steps-post' drawstyle for proper square wave visualization of pulses
        self.lines = []
        for i in range(self.num_channels):
            line, = self.ax.plot([], [], 
                               color=CHANNEL_COLORS[i], 
                               linewidth=1.5,
                               drawstyle='steps-post',
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
    
    def _setup_normalized_reference_lines(self):
        """Setup fixed reference lines for normalized 0-1 display."""
        # Remove old reference lines if any
        for line in self.ref_lines:
            line.remove()
        self.ref_lines = []
        
        # Add reference lines at key normalized values
        self.ref_lines.append(self.ax.axhline(y=0, color='white', linestyle='-', alpha=0.4, linewidth=0.8))
        self.ref_lines.append(self.ax.axhline(y=0.5, color='white', linestyle='--', alpha=0.3, linewidth=0.5))
        self.ref_lines.append(self.ax.axhline(y=1.0, color='white', linestyle='-', alpha=0.4, linewidth=0.8))
        
        # Add subtle gridlines at 0.25 and 0.75
        self.ref_lines.append(self.ax.axhline(y=0.25, color='white', linestyle=':', alpha=0.15, linewidth=0.5))
        self.ref_lines.append(self.ax.axhline(y=0.75, color='white', linestyle=':', alpha=0.15, linewidth=0.5))
    
    def _normalize_value(self, raw_value):
        """Normalize a raw value to 0-1 range using the detected global range.
        
        Uses self._max_range (255 for PWM, 4095 for DAC) which is updated
        based on the maximum value seen across ALL channels.
        This ensures consistent normalization even when values temporarily
        fall within a smaller range (e.g., a DAC channel outputting 100).
        """
        if self._max_range <= 1:
            return float(raw_value)  # Binary range
        return raw_value / float(self._max_range)

    def _update_reference_lines(self, range_max, y_min=None, y_max=None, force=False):
        """Update reference lines based on detected value range and visible limits.
        
        Args:
            range_max: Maximum value for the detected range type (1, 255, or 4095)
            y_min: Current visible Y-axis minimum (for dynamic reference lines)
            y_max: Current visible Y-axis maximum (for dynamic reference lines)
            force: Force update even if values haven't changed significantly
        """
        # Use visible range if provided, otherwise use full range
        vis_min = y_min if y_min is not None else 0
        vis_max = y_max if y_max is not None else range_max
        
        # Only update if range changed significantly (>5% change) to avoid flicker
        if not force and self._last_y_min is not None and self._last_y_max is not None:
            range_size = max(1, self._last_y_max - self._last_y_min)
            min_change = abs(vis_min - self._last_y_min) / range_size
            max_change = abs(vis_max - self._last_y_max) / range_size
            if min_change < 0.05 and max_change < 0.05:
                return  # Skip update, range hasn't changed enough
        
        # Store current range
        self._last_y_min = vis_min
        self._last_y_max = vis_max
        
        vis_mid = (vis_min + vis_max) / 2
        
        # Remove old reference lines
        for line in self.ref_lines:
            line.remove()
        self.ref_lines = []
        
        # Add new reference lines based on VISIBLE range (not full range)
        self.ref_lines.append(self.ax.axhline(y=vis_min, color='white', linestyle='-', alpha=0.3, linewidth=0.5))
        self.ref_lines.append(self.ax.axhline(y=vis_mid, color='white', linestyle='--', alpha=0.2, linewidth=0.5))
        self.ref_lines.append(self.ax.axhline(y=vis_max, color='white', linestyle='-', alpha=0.3, linewidth=0.5))
        
        # Update Y-axis label with range type AND actual visible range
        if range_max <= 1:
            self.ax.set_ylabel(f'Value (Binary: {vis_min:.0f}-{vis_max:.0f})', fontsize=12)
            self._detected_range = 'binary'
        elif range_max <= 255:
            self.ax.set_ylabel(f'Value (PWM: {vis_min:.0f}-{vis_max:.0f})', fontsize=12)
            self._detected_range = 'pwm'
        else:
            self.ax.set_ylabel(f'Value (DAC: {vis_min:.0f}-{vis_max:.0f})', fontsize=12)
            self._detected_range = 'dac'
    
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
            
            # Update detected range based on incoming values
            max_incoming = max(values)
            if max_incoming > 255:
                self._max_range = 4095
                self._detected_range = 'dac'
            elif max_incoming > 1 and self._max_range < 4095:
                self._max_range = 255
                self._detected_range = 'pwm'
            
            # Calculate elapsed time
            elapsed = (datetime.now() - self.start_time).total_seconds()
            
            # Normalize values and store
            normalized_values = [self._normalize_value(v) for v in values]
            
            # Store NORMALIZED data for plotting
            self.time_data.append(elapsed)
            for i, norm_val in enumerate(normalized_values):
                self.channel_data[i].append(norm_val)
                self.last_values[i] = values[i]  # Keep raw for status display
                self.last_values_normalized[i] = norm_val
            
            self.message_count += 1
            
            # Store ALL data for HTML export (raw values)
            self.all_time_data.append(elapsed)
            for i, val in enumerate(values):
                self.all_channel_data[i].append(val)
            
            # Write to CSV (raw values)
            if self.csv_writer:
                row = [datetime.now().isoformat(), int(elapsed * 1000)] + values
                self.csv_writer.writerow(row)
                self.csv_file.flush()
            
            return True
            
        except Exception as e:
            # Silently ignore parse errors
            return False
    
    def _update(self, frame):
        """Animation update function with dynamic Y-axis scaling."""
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
            
        # Update plot data (already normalized)
        if len(self.time_data) > 0:
            times = list(self.time_data)
            
            # Update line data with normalized values
            for i, line in enumerate(self.lines):
                if i < len(self.channel_data):
                    ch_values = list(self.channel_data[i])
                    line.set_data(times, ch_values)
            
            # Y-axis is fixed at [-0.2, 1.2] - no dynamic adjustment needed
            
            # Adjust x-axis for scrolling effect (5-minute window)
            # Add 10% headroom on right side so latest data isn't at edge
            headroom = self.display_window * 0.1  # 10% = 30 seconds for 5-min window
            if times[-1] > self.display_window - headroom:
                self.ax.set_xlim(times[-1] - self.display_window + headroom, times[-1] + headroom)
            else:
                self.ax.set_xlim(0, self.display_window)
        
        # Update status text with RAW values (not normalized) for clarity
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        max_val = max(self.last_values[:self.num_channels]) if self.last_values else 0
        
        # Check if any channel has LOOP enabled (for info display)
        has_loop = self.loop_info and any(v == 1 for v in self.loop_info.values())
        
        # Determine range type label
        if self._detected_range == 'dac':
            range_label = 'DAC 0-4095'
        elif max_val > 1:
            range_label = 'PWM 0-255'
        else:
            range_label = 'Binary 0-1'
        
        # Format values based on range
        if max_val > 255:
            values_str = ', '.join([f'CH{i+1}:{self.last_values[i]:4d}' for i in range(self.num_channels)])
        else:
            values_str = ', '.join([f'CH{i+1}:{self.last_values[i]:3d}' for i in range(self.num_channels)])
        
        # Add loop indicator if any channel is looping
        status_line1 = f'Time: {elapsed:.1f}s | {range_label} | Msgs: {self.message_count}'
        if has_loop:
            status_line1 += ' | [LOOP]'
        
        self.status_text.set_text(f'{status_line1}\\n{values_str}')
        
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
        """Save an interactive Plotly HTML visualization of all captured data with dynamic Y-axis."""
        if not self.all_time_data or not self.html_output:
            return
        
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            # Create figure
            fig = go.Figure()
            
            # Collect all values for range detection
            all_values = []
            
            # Add traces for each channel
            for i in range(self.num_channels):
                if len(self.all_channel_data[i]) > 0:
                    all_values.extend(self.all_channel_data[i])
                    fig.add_trace(go.Scatter(
                        x=self.all_time_data,
                        y=self.all_channel_data[i],
                        mode='lines',
                        name=f'CH{i+1}',
                        line=dict(color=CHANNEL_COLORS[i], width=2)
                    ))
            
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
            
            # Detect value range and calculate Y-axis limits
            y_min, y_max = calculate_dynamic_ylim(all_values) if all_values else (-5, 260)
            _, range_max, range_type = detect_value_range(all_values) if all_values else (0, 255, 'pwm')
            
            # Determine Y-axis title based on range type
            range_labels = {
                'binary': 'Value (0-1 Binary)',
                'pwm': 'Value (0-255 PWM)',
                'dac': 'Value (0-4095 DAC)'
            }
            y_title = range_labels.get(range_type, 'Value')
            
            # Update layout with dynamic Y-axis
            fig.update_layout(
                title=dict(
                    text=f'Channel Monitoring Data - Duration: {duration_str} ({self.message_count} samples){loop_info_str}',
                    font=dict(size=18)
                ),
                xaxis_title='Time (seconds)',
                yaxis_title=y_title,
                yaxis=dict(range=[y_min, y_max]),
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
            
            # Add range slider for navigation
            fig.update_xaxes(rangeslider_visible=True)
            
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
                      channel_durations: Optional[Dict[str, float]] = None) -> Optional[Tuple]:
    """
    Launch the real-time PWM visualization.
    
    Args:
        serial_port: Existing serial connection (optional)
        port_name: Port to connect to (if serial_port not provided)
        csv_output: Path to save CSV data
        html_output: Path to save Plotly HTML visualization
        num_channels: Number of channels to display
        duration: Maximum duration in seconds
        loop_info: Dict of channel loop settings e.g. {'CH1': 1, 'CH2': 0} (1=loop forever)
        channel_durations: Dict of channel durations in ms e.g. {'CH1': 60000, 'CH2': 120000}
    
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
            channel_durations=channel_durations
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
    python realtime_plot.py --port /dev/ttyACM0 --output data.csv --html data.html
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
    
    print(f"Starting real-time PWM monitor (5-minute display window)...")
    print(f"  Port: {args.port}")
    print(f"  Channels: {args.channels}")
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
        duration=args.duration
    )
    
    if result:
        print("\nMonitoring complete.")
    else:
        print("\nMonitoring failed.")
        sys.exit(1)


if __name__ == '__main__':
    main()
