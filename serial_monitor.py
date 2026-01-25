#!/usr/bin/env python3
"""
Serial Monitor for Light Controller v2.2
Real-time channel value monitoring and visualization

Monitors Arduino serial output for channel PWM values and displays them
with REAL-TIME live plotting using Dash/Plotly or fallback to console bars.

Usage:
    python serial_monitor.py [--port PORT] [--baud BAUD] [--output FILE.csv]
    python serial_monitor.py --live-plot  # Real-time web dashboard
    
Examples:
    python serial_monitor.py --port /dev/cu.usbmodem14301
    python serial_monitor.py --port COM3 --baud 115200 --output channel_log.csv
    python serial_monitor.py --live-plot --port /dev/cu.usbmodem14301
"""

import sys
import argparse
import serial
import time
from datetime import datetime
from collections import deque
import threading
import json

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Warning: Plotly not available. Install with: pip install plotly")

# Try to import Dash for real-time plotting
try:
    from dash import Dash, dcc, html
    from dash.dependencies import Input, Output
    import plotly.graph_objects as go
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False


# Value range constants for different output types
VALUE_RANGE_BINARY = (0, 1)      # Binary: 0 or 1
VALUE_RANGE_PWM = (0, 255)       # PWM: 8-bit
VALUE_RANGE_DAC = (0, 4095)      # DAC: 12-bit

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
    Adds padding for visual clarity.
    
    Args:
        values: List of values
        padding_pct: Padding percentage (default 10%)
    
    Returns:
        (y_min, y_max) tuple
    """
    if not values:
        return -5, 260  # Default PWM range
    
    data_min = min(values)
    data_max = max(values)
    
    # Detect range type
    _, range_max, range_type = detect_value_range(values)
    
    # For narrow ranges, center the view with padding
    data_range = data_max - data_min
    if data_range == 0:
        data_range = max(1, data_max * 0.1)  # Prevent zero range
    
    padding = max(data_range * padding_pct, range_max * 0.02)  # At least 2% of full range
    
    y_min = max(0, data_min - padding)
    y_max = min(range_max * 1.05, data_max + padding)  # Cap at 105% of max range
    
    # Ensure minimum visible range
    if y_max - y_min < range_max * 0.05:
        y_max = y_min + range_max * 0.1
    
    return y_min, y_max


class SerialMonitor:
    """Monitor and plot Arduino channel values in real-time
    
    Supports multiple value ranges:
    - Binary: 0-1 (digital on/off)
    - PWM: 0-255 (8-bit)
    - DAC: 0-4095 (12-bit, e.g., MCP4728)
    
    Y-axis automatically adjusts to fit actual data values.
    """
    
    def __init__(self, port=None, baud=9600, max_points=300, output_file=None):
        """
        Initialize serial monitor
        
        Args:
            port: Serial port (auto-detect if None)
            baud: Baud rate (default 9600)
            max_points: Maximum points to keep in memory (for performance)
            output_file: Optional CSV file to log data
        """
        self.port = port
        self.baud = baud
        self.serial = None
        self.max_points = max_points
        self.output_file = output_file
        self.running = False
        
        # Data storage: {channel_num: {'times': [], 'values': []}}
        self.channel_data = {}
        # Track detected value range per channel: {channel_num: 'binary'|'pwm'|'dac'}
        self.channel_ranges = {}
        self.start_time = time.time()
        self.last_update_time = self.start_time
        
        # Statistics
        self.data_points_received = 0
        self.data_points_lost = 0
        self.last_print_time = 0
        
        # Output file
        self.csv_file = None
        if output_file:
            self.csv_file = open(output_file, 'w')
            self.csv_file.write("timestamp,time_ms,CH1,CH2,CH3,CH4\n")
    
    def find_serial_port(self):
        """Auto-detect Arduino serial port"""
        import serial.tools.list_ports
        
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            print("❌ No serial ports found!")
            return None
        
        print("📡 Available serial ports:")
        for i, (port, desc, hwid) in enumerate(ports, 1):
            print(f"  {i}. {port}: {desc} ({hwid})")
        
        # Try common Arduino port patterns
        for port, desc, hwid in ports:
            if any(x in desc.lower() for x in ['arduino', 'usb', 'ch340']):
                print(f"✓ Selected: {port}")
                return port
        
        # Fallback to first port
        return ports[0][0]
    
    def connect(self):
        """Connect to serial port"""
        try:
            if not self.port:
                self.port = self.find_serial_port()
            
            if not self.port:
                return False
            
            self.serial = serial.Serial(self.port, self.baud, timeout=1)
            print(f"✓ Connected to {self.port} at {self.baud} baud")
            
            # Give Arduino time to reset
            time.sleep(2)
            
            return True
        
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def parse_channel_data(self, line):
        """
        Parse channel monitor message from Arduino
        Format: $CHMON:CH1:pwm1,CH2:pwm2,CH3:pwm3,CH4:pwm4
        
        Returns: dict {channel_num: pwm_value} or None if parse fails
        """
        if not line.startswith('$CHMON:'):
            return None
        
        try:
            data_str = line[7:]  # Remove '$CHMON:' prefix
            channels = {}
            
            for ch_data in data_str.split(','):
                parts = ch_data.split(':')
                if len(parts) == 2:
                    ch_name = parts[0]  # 'CH1', 'CH2', etc.
                    pwm_value = int(parts[1])
                    ch_num = int(ch_name[2:])  # Extract channel number
                    channels[ch_num] = pwm_value
            
            return channels if channels else None
        
        except Exception as e:
            return None
    
    def update_data(self, channels):
        """Update stored channel data"""
        elapsed_ms = (time.time() - self.start_time) * 1000
        
        for ch_num, pwm_value in channels.items():
            if ch_num not in self.channel_data:
                self.channel_data[ch_num] = {'times': [], 'values': []}
            
            data = self.channel_data[ch_num]
            data['times'].append(elapsed_ms / 1000)  # Convert to seconds
            data['values'].append(pwm_value)
            
            # Keep only max_points to avoid memory issues
            if len(data['times']) > self.max_points:
                data['times'].pop(0)
                data['values'].pop(0)
        
        self.data_points_received += 1
        
        # Log to CSV if enabled
        if self.csv_file:
            timestamp = datetime.now().isoformat()
            values = [channels.get(i, 0) for i in range(1, 5)]
            self.csv_file.write(f"{timestamp},{elapsed_ms:.0f},{','.join(map(str, values))}\n")
            self.csv_file.flush()
    
    def print_values(self, channels):
        """Print current channel values to console with adaptive bar display.
        
        Automatically detects value range (binary/PWM/DAC) and scales bar accordingly.
        """
        current_time = time.time()
        if current_time - self.last_print_time < 0.5:  # Print max 2x per second
            return
        
        elapsed_s = current_time - self.start_time
        
        status = f"⏱️  {elapsed_s:6.1f}s | "
        for ch in range(1, 5):
            value = channels.get(ch, 0)
            
            # Detect and track range type for this channel
            if ch not in self.channel_ranges:
                if value > 255:
                    self.channel_ranges[ch] = 'dac'
                elif value > 1:
                    self.channel_ranges[ch] = 'pwm'
                else:
                    self.channel_ranges[ch] = 'binary'
            elif value > 255 and self.channel_ranges[ch] != 'dac':
                self.channel_ranges[ch] = 'dac'
            elif value > 1 and self.channel_ranges[ch] == 'binary':
                self.channel_ranges[ch] = 'pwm'
            
            # Calculate bar based on detected range
            range_type = self.channel_ranges.get(ch, 'pwm')
            if range_type == 'dac':
                max_val = 4095
                bar_length = int((value / max_val) * 10)
                value_str = f"{value:4d}"
            elif range_type == 'binary':
                max_val = 1
                bar_length = 10 if value else 0
                value_str = f"{value:1d}   "
            else:  # pwm
                max_val = 255
                bar_length = int((value / max_val) * 10)
                value_str = f"{value:3d} "
            
            bar = '█' * bar_length + '░' * (10 - bar_length)
            status += f"CH{ch}: {value_str}[{bar}] | "
        
        print(status)
        self.last_print_time = current_time
    
    def run(self):
        """Main monitoring loop"""
        if not self.connect():
            return False
        
        self.running = True
        print("\n📊 Monitoring channel values (Ctrl+C to stop)...\n")
        
        try:
            while self.running:
                if self.serial and self.serial.in_waiting:
                    try:
                        line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                        
                        if not line:
                            continue
                        
                        # Try to parse as channel data
                        channels = self.parse_channel_data(line)
                        if channels:
                            self.update_data(channels)
                            self.print_values(channels)
                        else:
                            # Print other messages for debugging
                            if not line.startswith('$'):
                                print(f"  < {line}")
                    
                    except Exception as e:
                        self.data_points_lost += 1
                
                time.sleep(0.01)  # Small delay to prevent CPU spinning
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped")
        
        finally:
            self.close()
            return True
    
    def close(self):
        """Close serial connection and output file"""
        self.running = False
        
        if self.serial:
            self.serial.close()
            print("✓ Serial connection closed")
        
        if self.csv_file:
            self.csv_file.close()
            print(f"✓ Data logged to {self.output_file}")
        
        # Print summary
        print(f"\n📊 Summary:")
        print(f"  Data points received: {self.data_points_received}")
        print(f"  Data points lost: {self.data_points_lost}")
        print(f"  Total duration: {time.time() - self.start_time:.1f}s")
        print(f"  Channels monitored: {len(self.channel_data)}")
    
    def run_with_live_plot(self, update_interval_ms=100, max_points=500):
        """
        Run serial monitor with REAL-TIME live plotting using Dash web dashboard.
        
        Opens a web browser with live updating charts that refresh every update_interval_ms.
        
        Args:
            update_interval_ms: How often to refresh charts (default 100ms = 10Hz)
            max_points: Maximum data points to show on chart (for performance)
        """
        if not DASH_AVAILABLE:
            print("❌ Dash not available for real-time plotting.")
            print("   Install with: pip install dash plotly")
            print("   Falling back to console-only mode...")
            return self.run()
        
        if not self.connect():
            return False
        
        print("\n🚀 Starting REAL-TIME Live Plot Dashboard...")
        print(f"   Open your browser to: http://127.0.0.1:8050")
        print("   Press Ctrl+C to stop\n")
        
        # Shared data for threading
        self.live_data_lock = threading.Lock()
        self.live_running = True
        self.max_live_points = max_points
        
        # Start serial reading in background thread
        serial_thread = threading.Thread(target=self._live_serial_reader, daemon=True)
        serial_thread.start()
        
        # Create Dash app
        app = Dash(__name__)
        
        app.layout = html.Div([
            html.H1("🌈 Light Controller - Real-Time Monitor", 
                    style={'textAlign': 'center', 'color': '#667eea'}),
            html.Div(id='status-bar', style={
                'textAlign': 'center', 
                'padding': '10px',
                'backgroundColor': '#f0f0f0',
                'marginBottom': '20px'
            }),
            dcc.Graph(id='live-graph', style={'height': '70vh'}),
            dcc.Interval(
                id='interval-component',
                interval=update_interval_ms,  # milliseconds
                n_intervals=0
            )
        ], style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'})
        
        @app.callback(
            [Output('live-graph', 'figure'),
             Output('status-bar', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_graph(n):
            with self.live_data_lock:
                data_copy = {ch: {'times': list(d['times']), 'values': list(d['values'])} 
                            for ch, d in self.channel_data.items()}
                points = self.data_points_received
            
            num_channels = len(data_copy) if data_copy else 4
            fig = make_subplots(
                rows=num_channels, cols=1,
                subplot_titles=[f"Channel {i+1}" for i in range(num_channels)],
                shared_xaxes=True,
                vertical_spacing=0.08
            )
            
            colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe']
            
            # Calculate dynamic X-axis range (show sliding window of time)
            x_max = 0
            x_min = 0
            if data_copy:
                for idx, ch in enumerate(sorted(data_copy.keys()), 1):
                    d = data_copy[ch]
                    # Limit points for performance
                    times = d['times'][-self.max_live_points:]
                    values = d['values'][-self.max_live_points:]
                    
                    # Track x-axis range across all channels
                    if times:
                        x_max = max(x_max, max(times))
                        x_min = min(x_min, min(times)) if x_min == 0 else min(x_min, min(times))
                    
                    fig.add_trace(
                        go.Scatter(
                            x=times,
                            y=values,
                            name=f'Ch {ch}',
                            mode='lines',
                            fill='tozeroy',
                            line=dict(color=colors[(ch-1) % len(colors)], width=2)
                        ),
                        row=idx, col=1
                    )
                    
                    # Dynamic Y-axis based on actual data values
                    y_min, y_max = calculate_dynamic_ylim(values)
                    _, _, range_type = detect_value_range(values)
                    
                    # Add range indicator to Y-axis title
                    range_labels = {'binary': '0-1', 'pwm': '0-255', 'dac': '0-4095'}
                    fig.update_yaxes(
                        range=[y_min, y_max],
                        title_text=f"Value ({range_labels.get(range_type, '0-255')})",
                        row=idx, col=1
                    )
                
                # Update X-axis range to show sliding window with padding
                x_padding = max(5, (x_max - x_min) * 0.02)  # At least 5s or 2% padding
                fig.update_xaxes(range=[x_min - x_padding, x_max + x_padding])
            else:
                # No data yet - show empty placeholder with default PWM range
                for idx in range(1, 5):
                    fig.add_trace(go.Scatter(x=[], y=[], name=f'Ch {idx}'), row=idx, col=1)
                    fig.update_yaxes(range=[0, 260], title_text="Value (0-255)", row=idx, col=1)
                fig.update_xaxes(range=[0, 60])  # Default 60s window when no data
            
            fig.update_layout(
                hovermode='x unified',
                showlegend=False,
                margin=dict(l=60, r=30, t=40, b=40),
                paper_bgcolor='white',
                plot_bgcolor='#fafafa'
            )
            fig.update_xaxes(title_text="Time (seconds)", row=num_channels, col=1)
            
            elapsed = time.time() - self.start_time if self.start_time else 0
            status = f"⏱️ Running for {elapsed:.1f}s | 📊 {points} data points | 🔄 Refresh: {update_interval_ms}ms"
            
            return fig, status
        
        try:
            app.run(debug=False, use_reloader=False)
        except KeyboardInterrupt:
            print("\n⏹️  Stopping live monitor...")
        finally:
            self.live_running = False
            self.close()
        
        return True
    
    def _live_serial_reader(self):
        """Background thread for reading serial data during live plotting."""
        self.start_time = time.time()
        
        while self.live_running:
            try:
                if self.serial and self.serial.in_waiting > 0:
                    line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                    
                    if not line:
                        continue
                    
                    channel_values = self.parse_channel_data(line)
                    
                    if channel_values:
                        with self.live_data_lock:
                            self.update_data(channel_values)
                    else:
                        # Print non-channel messages for debugging
                        if not line.startswith('$') and line:
                            print(f"  < {line}")
                else:
                    time.sleep(0.01)  # Small sleep to prevent busy-waiting
            except Exception as e:
                if self.live_running:  # Only log if we're supposed to be running
                    print(f"⚠️  Serial read error: {e}")
                time.sleep(0.1)
    
    def plot_data(self, show=True, save_html=None):
        """
        Generate interactive Plotly visualization of channel data
        
        Args:
            show: Display plot in browser (default True)
            save_html: Optional file path to save HTML plot
        """
        if not PLOTLY_AVAILABLE:
            print("❌ Plotly not available. Install with: pip install plotly")
            return
        
        if not self.channel_data:
            print("❌ No data to plot")
            return
        
        # Create subplots
        num_channels = len(self.channel_data)
        fig = make_subplots(
            rows=num_channels, cols=1,
            subplot_titles=[f"Channel {ch}" for ch in sorted(self.channel_data.keys())],
            shared_xaxes=True
        )
        
        colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe']
        
        for idx, ch in enumerate(sorted(self.channel_data.keys()), 1):
            data = self.channel_data[ch]
            
            fig.add_trace(
                go.Scatter(
                    x=data['times'],
                    y=data['values'],
                    name=f'Channel {ch}',
                    mode='lines',
                    fill='tozeroy',
                    fillcolor=f'rgba({colors[ch-1]}, 0.3)',
                    line=dict(color=colors[ch-1], width=2)
                ),
                row=idx, col=1
            )
        
        # Update layout
        fig.update_yaxes(range=[0, 260], title_text="PWM Value")
        fig.update_xaxes(title_text="Time (seconds)")
        
        fig.update_layout(
            title="Light Controller - Real-time Channel Monitor",
            height=300 * num_channels,
            hovermode='x unified',
            showlegend=False
        )
        
        # Save if requested
        if save_html:
            fig.write_html(save_html)
            print(f"✓ Plot saved to {save_html}")
        
        # Show plot
        if show:
            fig.show()


def main():
    parser = argparse.ArgumentParser(
        description='Monitor and visualize Light Controller channel values in real-time'
    )
    parser.add_argument(
        '--port', '-p',
        help='Serial port (auto-detect if not specified)'
    )
    parser.add_argument(
        '--baud', '-b',
        type=int, default=9600,
        help='Baud rate (default: 9600)'
    )
    parser.add_argument(
        '--output', '-o',
        help='CSV output file for logging'
    )
    parser.add_argument(
        '--plot',
        action='store_true',
        help='Generate static plot after monitoring (requires Plotly)'
    )
    parser.add_argument(
        '--save-plot',
        help='Save plot to HTML file'
    )
    parser.add_argument(
        '--live-plot',
        action='store_true',
        help='🔴 REAL-TIME live plotting dashboard (requires Dash)'
    )
    parser.add_argument(
        '--refresh-rate',
        type=int, default=100,
        help='Live plot refresh rate in ms (default: 100ms = 10Hz)'
    )
    
    args = parser.parse_args()
    
    monitor = SerialMonitor(
        port=args.port,
        baud=args.baud,
        output_file=args.output
    )
    
    # Choose run mode
    if args.live_plot:
        success = monitor.run_with_live_plot(update_interval_ms=args.refresh_rate)
    else:
        success = monitor.run()
        
        if success and (args.plot or args.save_plot):
            monitor.plot_data(show=args.plot, save_html=args.save_plot)


if __name__ == '__main__':
    main()
