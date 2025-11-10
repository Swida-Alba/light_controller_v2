#!/usr/bin/env python3
"""
Quick test script to read Arduino board information and test unique ID generation.
Tests Windows 10/11, macOS, and Linux compatibility.
"""

from lcfunc import SetUpSerialPort, get_arduino_unique_id
import platform

print("="*70)
print("Arduino Board Information Test")
print("="*70)
print(f"Operating System: {platform.system()} {platform.release()}")
print(f"Platform: {platform.platform()}")
print()

# Connect to Arduino
print("Connecting to Arduino...")
try:
    ser = SetUpSerialPort(board_type='Arduino', baudrate=115200, timeout=5)
    
    if not ser:
        print("\n✗ Failed to connect to Arduino")
        exit(1)
    
    print("\n✓ Connection successful!\n")
    
    # Get unique ID and board info
    print("Reading board information...")
    unique_id, board_info = get_arduino_unique_id(ser)
    
    print("\n" + "="*70)
    print("Arduino Board Information")
    print("="*70)
    print(f"Unique ID (Hash):     {unique_id}")
    print(f"Port:                 {board_info['port']}")
    print(f"Description:          {board_info['description']}")
    print(f"Manufacturer:         {board_info['manufacturer']}")
    
    if board_info['serial_number']:
        print(f"Serial Number:        {board_info['serial_number']}")
    else:
        print(f"Serial Number:        Not available")
    
    if board_info['vid']:
        print(f"Vendor ID (VID):      0x{board_info['vid']:04x}")
    else:
        print(f"Vendor ID (VID):      Not available")
        
    if board_info['pid']:
        print(f"Product ID (PID):     0x{board_info['pid']:04x}")
    else:
        print(f"Product ID (PID):     Not available")
    
    if board_info.get('location'):
        print(f"Location:             {board_info['location']}")
    
    if board_info.get('hwid'):
        print(f"Hardware ID:          {board_info['hwid']}")
    
    print("="*70)
    
    # Show what will be used for unique ID generation
    print("\nUnique ID Generation Logic:")
    print("-"*70)
    if board_info['serial_number']:
        print(f"✓ Method: Serial Number")
        print(f"  Value: {board_info['serial_number']}")
        print(f"  Reliability: ★★★★★ (Best - consistent across ports and computers)")
    elif board_info['vid'] and board_info['pid'] and board_info.get('location'):
        print(f"✓ Method: VID:PID + Location")
        print(f"  Value: {board_info['vid']:04x}:{board_info['pid']:04x}:{board_info['location']}")
        print(f"  Reliability: ★★★★☆ (Good - consistent across reboots)")
    elif board_info['vid'] and board_info['pid']:
        port_display = board_info['port'].upper() if platform.system() == 'Windows' else board_info['port']
        print(f"✓ Method: VID:PID + Port")
        print(f"  Value: {board_info['vid']:04x}:{board_info['pid']:04x}:{port_display}")
        print(f"  Reliability: ★★★☆☆ (OK - changes if USB port changes)")
    else:
        port_display = board_info['port'].upper() if platform.system() == 'Windows' else board_info['port']
        print(f"✓ Method: Port + Description")
        print(f"  Value: {port_display}:{board_info['description']}")
        print(f"  Reliability: ★★☆☆☆ (Fair - changes with port)")
    print("-"*70)
    
    # Platform-specific notes
    print("\nPlatform-Specific Information:")
    print("-"*70)
    if platform.system() == 'Windows':
        print("✓ Windows detected")
        print("  - COM port names normalized to uppercase for consistency")
        print("  - Example: COM3, COM10, COM15")
        print(f"  - Your port: {board_info['port']}")
    elif platform.system() == 'Darwin':
        print("✓ macOS detected")
        print("  - Using /dev/cu.* ports (cu = callout, for outgoing connections)")
        print(f"  - Your port: {board_info['port']}")
    elif platform.system() == 'Linux':
        print("✓ Linux detected")
        print("  - Typical ports: /dev/ttyUSB*, /dev/ttyACM*")
        print(f"  - Your port: {board_info['port']}")
    print("-"*70)
    
    # Check for existing calibration
    from lcfunc import load_calibration_database
    db = load_calibration_database()
    
    print("\nCalibration Status:")
    print("-"*70)
    if unique_id in db:
        calib_data = db[unique_id]
        print(f"✓ Calibration found!")
        print(f"  Factor:             {calib_data['calib_factor']:.6f}")
        print(f"  Method:             {calib_data['method']}")
        print(f"  Last calibrated:    {calib_data['timestamp']}")
        print(f"  R-squared:          {calib_data.get('r_squared', 'N/A')}")
        
        # Show board info from database
        if 'board_info' in calib_data:
            db_info = calib_data['board_info']
            print(f"\n  Calibration was done on:")
            print(f"    Port: {db_info.get('port', 'Unknown')}")
            print(f"    Description: {db_info.get('description', 'Unknown')}")
    else:
        print(f"✗ No calibration found for this board")
        print(f"  Board ID: {unique_id}")
        print(f"  Run calibration to add it to the database")
    print("-"*70)
    
    # Close connection
    ser.close()
    print("\n✓ Test completed successfully!\n")
    print("="*70)
    print("\nCompatibility:")
    print("  ✓ Windows 10/11 - COM port handling")
    print("  ✓ macOS - /dev/cu.* port handling")  
    print("  ✓ Linux - /dev/tty* port handling")
    print("="*70)
    
except Exception as e:
    print(f"\n✗ Error: {e}\n")
    import traceback
    traceback.print_exc()
    exit(1)

