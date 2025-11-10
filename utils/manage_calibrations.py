#!/usr/bin/env python3
"""
Calibration Database Manager

This utility allows you to view, manage, and test Arduino calibrations stored
in the calibration database.

Usage:
    python manage_calibrations.py [command]
    
Commands:
    list        - List all stored calibrations
    delete      - Delete a calibration
    test        - Test connection and show Arduino ID
    export      - Export database to readable text file
    help        - Show this help message
"""

import sys
import os

# Add parent directory to path to import lcfunc
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lcfunc import (
    list_all_calibrations, 
    delete_calibration,
    get_arduino_unique_id,
    load_calibration_database,
    SetUpSerialPort
)
import json


def test_arduino_connection():
    """Test connection and show Arduino information."""
    print("\n" + "="*70)
    print("Arduino Connection Test")
    print("="*70 + "\n")
    
    try:
        # Setup serial connection
        print("Connecting to Arduino...")
        ser = SetUpSerialPort(board_type='Arduino', baudrate=115200, timeout=5)
        
        if not ser:
            print("\n✗ Failed to connect to Arduino")
            return
        
        print("\n✓ Connection successful!\n")
        
        # Get Arduino information
        unique_id, board_info = get_arduino_unique_id(ser)
        
        print("Arduino Information:")
        print("-" * 70)
        print(f"Board ID (Hash):    {unique_id}")
        print(f"Port:               {board_info['port']}")
        print(f"Description:        {board_info['description']}")
        print(f"Manufacturer:       {board_info['manufacturer']}")
        if board_info['serial_number']:
            print(f"Serial Number:      {board_info['serial_number']}")
        if board_info['vid']:
            print(f"Vendor ID (VID):    0x{board_info['vid']:04x}")
        if board_info['pid']:
            print(f"Product ID (PID):   0x{board_info['pid']:04x}")
        print("-" * 70)
        
        # Check if calibration exists
        db = load_calibration_database()
        if unique_id in db:
            calib_data = db[unique_id]
            print(f"\n✓ Calibration found in database:")
            print(f"  Factor:          {calib_data['calib_factor']:.6f}")
            print(f"  Method:          {calib_data['method']}")
            print(f"  Last calibrated: {calib_data['timestamp']}")
        else:
            print(f"\n✗ No calibration found for this Arduino")
            print(f"  Run calibration to add it to database")
        
        ser.close()
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}\n")


def export_database(output_file='calibration_database.txt'):
    """Export database to readable text file."""
    db = load_calibration_database()
    
    if not db:
        print("\nNo calibrations stored in database.\n")
        return
    
    try:
        with open(output_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("Arduino Calibration Database Export\n")
            f.write("="*70 + "\n\n")
            f.write(f"Total boards: {len(db)}\n\n")
            
            for i, (board_id, data) in enumerate(db.items(), 1):
                f.write(f"\n{'='*70}\n")
                f.write(f"Board {i}: {board_id}\n")
                f.write(f"{'='*70}\n")
                f.write(f"Port:               {data['board_info']['port']}\n")
                f.write(f"Description:        {data['board_info']['description']}\n")
                f.write(f"Manufacturer:       {data['board_info']['manufacturer']}\n")
                if data['board_info']['serial_number']:
                    f.write(f"Serial Number:      {data['board_info']['serial_number']}\n")
                f.write(f"\nCalibration factor: {data['calib_factor']:.6f}\n")
                f.write(f"Offset:             {data['offset']:.6f} seconds\n")
                f.write(f"R-squared:          {data.get('r_squared', 'N/A')}\n")
                f.write(f"Method:             {data['method']}\n")
                f.write(f"Last calibrated:    {data['timestamp']}\n")
                
                # Calculate timing correction
                correction_12h = (data['calib_factor'] - 1) * 12 * 3600
                f.write(f"Correction/12h:     {correction_12h:.2f} seconds\n")
        
        print(f"\n✓ Database exported to: {output_file}\n")
        
    except Exception as e:
        print(f"\n✗ Error exporting database: {e}\n")


def show_help():
    """Show help message."""
    print(__doc__)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        command = 'list'
    else:
        command = sys.argv[1].lower()
    
    if command == 'list':
        list_all_calibrations()
        
    elif command == 'delete':
        delete_calibration()
        
    elif command == 'test':
        test_arduino_connection()
        
    elif command == 'export':
        if len(sys.argv) > 2:
            export_database(sys.argv[2])
        else:
            export_database()
            
    elif command == 'help' or command == '-h' or command == '--help':
        show_help()
        
    else:
        print(f"\n✗ Unknown command: {command}\n")
        show_help()


if __name__ == "__main__":
    main()
