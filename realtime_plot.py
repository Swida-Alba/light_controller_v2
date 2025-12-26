#!/usr/bin/env python3
"""
Real-Time PWM Monitoring Plot

Uses PyQtGraph for fast, real-time visualization of Arduino $CHMON messages.
This module provides a standalone plotting window that can be launched from
protocol_parser.py or used independently.

PyQtGraph is recommended for real-time plotting because:
- Very fast rendering (uses OpenGL)
- Designed for scientific/engineering applications
- Handles streaming data efficiently
- Cross-platform (Windows, macOS, Linux)

Installation:
    pip install pyqtgraph PyQt6

Usage:
    # From command line (standalone):
    python realtime_plot.py --port /dev/cu.usbmodem1101 --duration 60
    
    # From protocol_parser.py (with --monitor flag):
    python protocol_parser.py 2 /dev/cu.usbmodem1101 protocol.txt --monitor
"""

import sys
import time
import csv
import argparse
from datetime import datetime
from collections import deque
from typing import Optional, Dict, List

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
    from PyQt6.QtCore import QTimer, Qt
    from PyQt6.QtGui import QFont
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


# Channel colors (matching common oscilloscope colors)
CHANNEL_COLORS = [
    (255, 255, 0),    # CH1: Yellow
    (0, 255, 255),    # CH2: Cyan
    (255, 0, 255),    # CH3: Magenta
    (0, 255, 0),      # CH4: Green
    (255, 128, 0),    # CH5: Orange
    (128, 128, 255),  # CH6: Light blue
    (255, 128, 128),  # CH7: Pink
    (128, 255, 128),  # CH8: Light green
]


class RealtimePWMPlot(QMainWindow):
    """
    Real-time PWM value plotting window.
    
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
        Initialize the real-time plot window.
        
        Args:
            serial_port: Existing serial.Serial object (if already connected)
            port_name: Serial port name to connect to (if serial_port not provided)
            baudrate: Serial baudrate (default 9600)
            max_points: Maximum points to display (rolling window)
            csv_output: Path to save CSV data (optional)
            num_channels: Number of channels to display (1-8)
        """
        super().__init__()
        
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
        
        # Setup UI
        self._setup_ui()
        
        # Connect to serial if port name provided
        if serial_port is None and port_name:
            self._connect_serial()
        
        # Setup CSV output
        if csv_output:
            self._setup_csv()
        
        # Start update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(10)  # 100 Hz update rate
        
        self.start_time = datetime.now()
    
    def _setup_ui(self):
        """Setup the PyQtGraph UI."""
        self.setWindowTitle('🔌 Real-Time PWM Monitor')
        self.setGeometry(100, 100, 1200, 600)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Header with status
        header = QHBoxLayout()
        
        self.status_label = QLabel('⏳ Waiting for data...')
        self.status_label.setFont(QFont('Monaco', 14))
        header.addWidget(self.status_label)
        
        self.time_label = QLabel('Time: 0.0s')
        self.time_label.setFont(QFont('Monaco', 14))
        header.addWidget(self.time_label)
        
        header.addStretch()
        layout.addLayout(header)
        
        # PyQtGraph plot widget
        pg.setConfigOptions(antialias=True)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('k')  # Black background
        self.plot_widget.setTitle('PWM Intensity Over Time', color='w', size='14pt')
        self.plot_widget.setLabel('left', 'PWM Value', units='', color='w')
        self.plot_widget.setLabel('bottom', 'Time', units='s', color='w')
        self.plot_widget.setYRange(0, 255)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()
        
        layout.addWidget(self.plot_widget)
        
        # Create plot lines for each channel
        self.curves = []
        for i in range(self.num_channels):
            pen = pg.mkPen(color=CHANNEL_COLORS[i], width=2)
            curve = self.plot_widget.plot([], [], pen=pen, name=f'CH{i+1}')
            self.curves.append(curve)
        
        # Channel value labels
        values_layout = QHBoxLayout()
        self.value_labels = []
        for i in range(self.num_channels):
            label = QLabel(f'CH{i+1}: ---')
            label.setFont(QFont('Monaco', 16, QFont.Weight.Bold))
            label.setStyleSheet(f'color: rgb{CHANNEL_COLORS[i]}; background-color: #222; padding: 5px; border-radius: 3px;')
            self.value_labels.append(label)
            values_layout.addWidget(label)
        
        values_layout.addStretch()
        layout.addLayout(values_layout)
    
    def _connect_serial(self):
        """Connect to serial port."""
        if not SERIAL_AVAILABLE:
            print("Error: pyserial not installed. Run: pip install pyserial")
            return
        
        try:
            self.serial_port = serial.Serial(self.port_name, self.baudrate, timeout=0.1)
            print(f"Connected to {self.port_name}")
        except Exception as e:
            print(f"Failed to connect to {self.port_name}: {e}")
            self.serial_port = None
    
    def _setup_csv(self):
        """Setup CSV output file."""
        self.csv_file = open(self.csv_output, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['timestamp', 'time_ms'] + [f'CH{i+1}' for i in range(8)])
    
    def _update(self):
        """Update plot with new serial data."""
        if self.serial_port is None:
            return
        
        try:
            # Read all available lines
            while self.serial_port.in_waiting:
                line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                
                if line.startswith('$CHMON:'):
                    self._process_chmon(line)
        except Exception as e:
            self.status_label.setText(f'⚠️ Error: {e}')
    
    def _process_chmon(self, line: str):
        """Process a $CHMON message."""
        # Parse: $CHMON:CH1:pwm1,CH2:pwm2,...
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        channels = {}
        for ch_data in line[7:].split(','):
            parts = ch_data.split(':')
            if len(parts) == 2:
                try:
                    ch_num = int(parts[0][2:])
                    channels[ch_num] = int(parts[1])
                except ValueError:
                    continue
        
        # Update data
        self.time_data.append(elapsed)
        for i in range(8):
            self.channel_data[i].append(channels.get(i + 1, 0))
        
        # Update plots
        time_list = list(self.time_data)
        for i, curve in enumerate(self.curves):
            curve.setData(time_list, list(self.channel_data[i]))
        
        # Update labels
        self.time_label.setText(f'Time: {elapsed:.1f}s')
        self.status_label.setText('📊 Receiving data...')
        
        for i in range(self.num_channels):
            pwm = channels.get(i + 1, 0)
            bar_len = pwm // 25
            bar = '█' * bar_len + '░' * (10 - bar_len)
            self.value_labels[i].setText(f'CH{i+1}: {pwm:3d} [{bar}]')
        
        # Auto-scroll X axis
        if elapsed > 10:
            self.plot_widget.setXRange(elapsed - 10, elapsed)
        
        # Write to CSV
        if self.csv_writer:
            values = [channels.get(i + 1, 0) for i in range(8)]
            self.csv_writer.writerow([datetime.now().isoformat(), f'{elapsed*1000:.0f}'] + values)
            self.csv_file.flush()
    
    def set_serial(self, serial_port: object):
        """Set serial port (for external connection)."""
        self.serial_port = serial_port
        self.start_time = datetime.now()
    
    def closeEvent(self, event):
        """Cleanup on window close."""
        self.timer.stop()
        if self.csv_file:
            self.csv_file.close()
        event.accept()


def run_realtime_plot(serial_port=None, 
                      port_name: str = None, 
                      csv_output: str = None,
                      num_channels: int = 4) -> Optional[QApplication]:
    """
    Launch the real-time plot window.
    
    Args:
        serial_port: Existing serial connection (optional)
        port_name: Serial port to connect to (if serial_port not provided)
        csv_output: Path to save CSV data
        num_channels: Number of channels to display
        
    Returns:
        QApplication instance (call app.exec() to run event loop)
    """
    if not PYQTGRAPH_AVAILABLE:
        print("=" * 60)
        print("⚠️  PyQtGraph not available for real-time plotting")
        print("=" * 60)
        print("\nTo enable real-time visualization, install:")
        print("  pip install pyqtgraph PyQt6")
        print("=" * 60)
        return None
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    window = RealtimePWMPlot(
        serial_port=serial_port,
        port_name=port_name,
        csv_output=csv_output,
        num_channels=num_channels
    )
    window.show()
    
    return app, window


def main():
    """Standalone mode: connect to serial and plot."""
    parser = argparse.ArgumentParser(
        description='Real-time PWM monitoring plot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python realtime_plot.py --port /dev/cu.usbmodem1101
  python realtime_plot.py --port COM3 --output data.csv
  python realtime_plot.py --port /dev/ttyACM0 --channels 2
        """
    )
    parser.add_argument('--port', '-p', required=True, help='Serial port name')
    parser.add_argument('--baudrate', '-b', type=int, default=9600, help='Baudrate (default: 9600)')
    parser.add_argument('--output', '-o', help='CSV output file')
    parser.add_argument('--channels', '-c', type=int, default=4, help='Number of channels (default: 4)')
    
    args = parser.parse_args()
    
    result = run_realtime_plot(
        port_name=args.port,
        csv_output=args.output,
        num_channels=args.channels
    )
    
    if result:
        app, window = result
        sys.exit(app.exec())
    else:
        print("\nFalling back to text-mode monitoring...")
        # Fallback to simple text output
        if SERIAL_AVAILABLE:
            ser = serial.Serial(args.port, args.baudrate)
            print(f"Connected to {args.port}")
            print("Press Ctrl+C to stop\n")
            
            try:
                start = datetime.now()
                while True:
                    if ser.in_waiting:
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        if line.startswith('$CHMON:'):
                            elapsed = (datetime.now() - start).total_seconds()
                            print(f"[{elapsed:6.1f}s] {line}")
            except KeyboardInterrupt:
                print("\nStopped")
            finally:
                ser.close()


if __name__ == '__main__':
    main()
