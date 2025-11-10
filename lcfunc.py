# serial communication from: https://github.com/Swida-Alba/visual-behavior

import serial
import serial.tools.list_ports
import platform
import datetime
import time
import os
import numpy as np
import pandas as pd
import re
import threading
import ast
import json
import hashlib


from collections import defaultdict

# functions
def SetUpSerialPort(board_type='Arduino Uno', **kwargs):
    # modified from LoomingFunc.py
    current_os = platform.system()
    Port = ''
    port_list = list(serial.tools.list_ports.comports())
    port_names = [None]*len(port_list)
    port_num = 0
    ser = ''
    
    # Normalize board_type for generic Arduino search
    search_term = 'Arduino' if 'Arduino' in board_type else board_type
    
    print(f'\nSearching for {board_type} on {current_os}...')
    print('Available ports:')
    for port in port_list:
        print(f'  - {port.device}: {port.description} (Manufacturer: {port.manufacturer})')
    
    for i, port in enumerate(port_list):
        port_name = port.device
        port_names[i] = port_name
        found = False
        
        if current_os == 'Windows':
            # Windows 11 fix: Check both description AND manufacturer fields
            # Many Arduino clones or CH340-based boards show "USB-SERIAL CH340" in description
            # but have "Arduino" or chip manufacturer in the manufacturer field
            if port.description and port.description.find(board_type) != -1:
                found = True
            elif port.manufacturer and port.manufacturer.find(search_term) != -1:
                found = True
            # Also check for common Arduino USB chip manufacturers
            elif port.manufacturer and any(chip in port.manufacturer for chip in ['FTDI', 'CH340', 'CP210', 'wch.cn']):
                print(f'  Note: Found potential Arduino with {port.manufacturer} chipset on {port_name}')
                found = True
            
            if found:
                port_num += 1
                Port = port_name
                
        elif current_os == 'Darwin' or current_os == 'Linux':
            if board_type != 'Arduino':
                search_term = 'Arduino'
                print('Detailed Arduino board cannot be recognized on Mac or Linux. Searching for all "Arduino" boards.')
            if port.manufacturer != None and port.manufacturer.find(search_term) != -1:
                port_num += 1
                Port = port_name
                
    if port_num == 1:
        print('\n{} is found on {}'.format(board_type,Port))
        answer = input('\nDo you confirm using this port? (Y/n): ')
        if not (answer == 'Y' or answer == 'y'):
            raise ValueError('Port is not confirmed.')
        print('\nBuilding serial connection...')
        ser = serial.Serial(port=Port,**kwargs)
        # Longer wait time for all boards, especially Arduino Due Native USB
        # Native USB needs more time for enumeration
        print('Waiting for board initialization...')
        time.sleep(6)
    elif port_num > 1:
        print(f'\n\033[33mMore than one {board_type} is connected.\033[0m')
        print('Please select the correct port manually:')
        for i, port in enumerate(port_list):
            print(f'  [{i+1}] {port.device}: {port.description} (Manufacturer: {port.manufacturer})')
        
        while True:
            try:
                choice = input(f'\nEnter port number (1-{len(port_list)}) or "q" to quit: ')
                if choice.lower() == 'q':
                    raise ValueError('Port selection cancelled by user.')
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(port_list):
                    Port = port_list[choice_idx].device
                    print(f'\nSelected port: {Port}')
                    print('\nBuilding serial connection...')
                    ser = serial.Serial(port=Port,**kwargs)
                    # Longer wait time for all boards, especially Native USB
                    print('Waiting for board initialization...')
                    time.sleep(6)
                    break
                else:
                    print(f'\033[31mInvalid choice. Please enter a number between 1 and {len(port_list)}.\033[0m')
            except ValueError as e:
                if 'cancelled' in str(e):
                    raise
                print('\033[31mInvalid input. Please enter a number or "q" to quit.\033[0m')
    else:
        print('\n\033[33mNo {} detected automatically.\033[0m'.format(board_type))
        if len(port_list) > 0:
            print('Would you like to manually select a port? Available ports:')
            for i, port in enumerate(port_list):
                print(f'  [{i+1}] {port.device}: {port.description} (Manufacturer: {port.manufacturer})')
            
            while True:
                try:
                    choice = input(f'\nEnter port number (1-{len(port_list)}) or "n" to skip: ')
                    if choice.lower() == 'n':
                        print('\n\033[33mSerial communication is unavailable.\033[0m\n')
                        break
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(port_list):
                        Port = port_list[choice_idx].device
                        print(f'\nSelected port: {Port}')
                        print('\nBuilding serial connection...')
                        ser = serial.Serial(port=Port,**kwargs)
                        # Longer wait time for all boards, especially Native USB
                        print('Waiting for board initialization...')
                        time.sleep(6)
                        break
                    else:
                        print(f'\033[31mInvalid choice. Please enter a number between 1 and {len(port_list)}.\033[0m')
                except ValueError as e:
                    print('\033[31mInvalid input. Please enter a number or "n" to skip.\033[0m')
        else:
            print('\033[33mNo serial ports available. Serial communication is unavailable.\033[0m\n')
    return ser

def ClearSerialBuffer(ser, print_flag = False):
    '''check and clear the serial buffer'''
    # modified from LoomingFunc.py
    if not ser:
        return
    else:
        lineNum = 0
        while ser.inWaiting() > 0:
            fb = ser.readline().decode('utf-8').strip()
            lineNum += 1
            print(f'\033[30mCleared serial buffer -- line {lineNum}: {fb}\033[0m')
        if lineNum == 0 and print_flag:
            print('No info in serial buffer.')
        return 0

# ============================================================================
# Calibration Database Management
# ============================================================================

def get_arduino_unique_id(ser):
    """
    Get a unique identifier for the connected Arduino board.
    
    Works on Windows 10/11, macOS, and Linux.
    
    Uses a combination of (in priority order):
    1. Serial number (most reliable, works across ports)
    2. VID:PID + port (for clone boards without serial number)
    3. Port + description (fallback)
    
    Args:
        ser: Serial connection object
        
    Returns:
        str: Unique identifier string (16-char hash)
        dict: Board information (port, description, manufacturer, etc.)
        
    Note:
        - Windows: Handles COM port names (COM1, COM3, etc.)
        - macOS: Handles /dev/cu.* and /dev/tty.* ports
        - Linux: Handles /dev/ttyUSB*, /dev/ttyACM* ports
    """
    try:
        port_name = ser.port
        
        # Get detailed port information
        port_list = list(serial.tools.list_ports.comports())
        board_info = {
            'port': port_name,
            'description': 'Unknown',
            'manufacturer': 'Unknown',
            'serial_number': None,
            'vid': None,
            'pid': None,
            'location': None,
            'hwid': None
        }
        
        for port in port_list:
            # Match port device - normalize path for cross-platform compatibility
            port_device = port.device
            
            # On Windows, COM port matching is case-insensitive
            if platform.system() == 'Windows':
                if port_device.upper() == port_name.upper():
                    match_found = True
                else:
                    match_found = False
            else:
                # On Unix systems (macOS, Linux), case-sensitive matching
                if port_device == port_name:
                    match_found = True
                else:
                    match_found = False
            
            if match_found:
                board_info['description'] = port.description or 'Unknown'
                board_info['manufacturer'] = port.manufacturer or 'Unknown'
                board_info['serial_number'] = port.serial_number
                board_info['vid'] = port.vid
                board_info['pid'] = port.pid
                board_info['location'] = getattr(port, 'location', None)
                board_info['hwid'] = port.hwid if hasattr(port, 'hwid') else None
                break
        
        # Create unique ID from available information
        # Priority: serial_number > (vid, pid) > (vid, pid, port) > port
        if board_info['serial_number']:
            # Best case: Use serial number (consistent across ports and computers)
            unique_string = f"{board_info['serial_number']}"
        elif board_info['vid'] and board_info['pid'] and board_info['location']:
            # Good case: Use VID:PID + location (consistent across reboots)
            unique_string = f"{board_info['vid']}:{board_info['pid']}:{board_info['location']}"
        elif board_info['vid'] and board_info['pid']:
            # Acceptable: Use VID:PID + port (changes if port changes)
            # Normalize port name for consistency
            normalized_port = port_name.upper() if platform.system() == 'Windows' else port_name
            unique_string = f"{board_info['vid']}:{board_info['pid']}:{normalized_port}"
        else:
            # Fallback: Use port + description (least reliable)
            normalized_port = port_name.upper() if platform.system() == 'Windows' else port_name
            unique_string = f"{normalized_port}:{board_info['description']}"
        
        # Create hash for consistent ID (16 characters for readability)
        unique_id = hashlib.md5(unique_string.encode()).hexdigest()[:16]
        
        return unique_id, board_info
        
    except Exception as e:
        print(f'\033[33mWarning: Could not get Arduino unique ID: {e}\033[0m')
        import traceback
        traceback.print_exc()
        # Fallback to port name only
        try:
            normalized_port = ser.port.upper() if platform.system() == 'Windows' else ser.port
            unique_id = hashlib.md5(normalized_port.encode()).hexdigest()[:16]
            return unique_id, {'port': ser.port, 'description': 'Unknown', 'manufacturer': 'Unknown', 'serial_number': None, 'vid': None, 'pid': None}
        except:
            # Ultimate fallback
            return 'unknown_board', {'port': 'Unknown', 'description': 'Unknown', 'manufacturer': 'Unknown', 'serial_number': None, 'vid': None, 'pid': None}



def load_calibration_database(db_path='calibration_database.json'):
    """
    Load calibration database from JSON file.
    
    Args:
        db_path: Path to calibration database file
        
    Returns:
        dict: Calibration database
    """
    if os.path.exists(db_path):
        try:
            with open(db_path, 'r') as f:
                db = json.load(f)
            return db
        except Exception as e:
            print(f'\033[33mWarning: Could not load calibration database: {e}\033[0m')
            print('Creating new database...')
            return {}
    else:
        return {}


def save_calibration_database(db, db_path='calibration_database.json'):
    """
    Save calibration database to JSON file.
    
    Args:
        db: Calibration database dictionary
        db_path: Path to save database file
    """
    try:
        with open(db_path, 'w') as f:
            json.dump(db, f, indent=2)
        print(f'\n✓ Calibration database saved to: {db_path}')
    except Exception as e:
        print(f'\033[31mError: Could not save calibration database: {e}\033[0m')


def get_calibration_for_arduino(ser, db_path='calibration_database.json'):
    """
    Get stored calibration factor for the connected Arduino.
    
    Checks if calibration is older than 3 months and prompts for recalibration
    if needed due to component aging.
    
    Args:
        ser: Serial connection object
        db_path: Path to calibration database file
        
    Returns:
        dict or None: Calibration data if found and valid, None if expired or not found
    """
    unique_id, board_info = get_arduino_unique_id(ser)
    db = load_calibration_database(db_path)
    
    if unique_id in db:
        calib_data = db[unique_id]
        
        # Check calibration age (3 months = 90 days)
        try:
            calib_timestamp = datetime.datetime.strptime(calib_data["timestamp"], '%Y-%m-%d %H:%M:%S')
            now = datetime.datetime.now()
            age_days = (now - calib_timestamp).days
            age_months = age_days / 30.44  # Average days per month
            
            # Check if calibration is older than 3 months
            if age_days > 90:
                print(f'\n{"="*70}')
                print(f'⚠️  CALIBRATION EXPIRED - Recalibration Required')
                print(f'{"="*70}')
                print(f'Board ID: {unique_id}')
                print(f'Port: {board_info["port"]}')
                print(f'Description: {board_info["description"]}')
                if board_info['serial_number']:
                    print(f'Serial Number: {board_info["serial_number"]}')
                print(f'\nOld calibration factor: {calib_data["calib_factor"]:.6f}')
                print(f'Calibration date: {calib_data["timestamp"]}')
                print(f'Age: {age_days} days ({age_months:.1f} months)')
                print(f'\nWHY RECALIBRATE?')
                print(f'  • Crystal oscillators drift over time (±1-5 ppm/year)')
                print(f'  • Temperature effects accumulate')
                print(f'  • Component aging affects timing accuracy')
                print(f'  • Recommended: Recalibrate every 3 months for precision')
                print(f'\nCalibration expired. A new calibration is required.')
                print(f'{"="*70}\n')
                return None  # Force recalibration
                
        except (ValueError, KeyError) as e:
            # Timestamp format issue - treat as needing recalibration
            print(f'\nWarning: Could not parse calibration timestamp. Recalibration recommended.')
            return None
        
        # Calibration is still valid (< 3 months old)
        print(f'\n{"="*70}')
        print(f'✓ Found existing calibration for this Arduino')
        print(f'{"="*70}')
        print(f'Board ID: {unique_id}')
        print(f'Port: {board_info["port"]}')
        print(f'Description: {board_info["description"]}')
        if board_info['serial_number']:
            print(f'Serial Number: {board_info["serial_number"]}')
        print(f'\nCalibration factor: {calib_data["calib_factor"]:.6f}')
        print(f'Last calibrated: {calib_data["timestamp"]}')
        print(f'Age: {age_days} days ({age_months:.1f} months) - Valid ✓')
        print(f'Method: {calib_data.get("method", "Unknown")}')
        print(f'R-squared: {calib_data.get("r_squared", "N/A")}')
        print(f'{"="*70}\n')
        
        # All calibration methods (V1, V1.1, V2) now use the same format:
        # python_time = calib_factor × arduino_time
        # CorrectTime divides by calib_factor
        return calib_data
    else:
        print(f'\n{"="*70}')
        print(f'No existing calibration found for this Arduino')
        print(f'{"="*70}')
        print(f'Board ID: {unique_id}')
        print(f'Port: {board_info["port"]}')
        print(f'Description: {board_info["description"]}')
        if board_info['serial_number']:
            print(f'Serial Number: {board_info["serial_number"]}')
        print(f'\nA new calibration will be performed.')
        print(f'{"="*70}\n')
        return None


def save_calibration_for_arduino(ser, calib_result, method='v2', db_path='calibration_database.json'):
    """
    Save calibration result for the connected Arduino.
    
    Args:
        ser: Serial connection object
        calib_result: Dictionary with calibration results (must contain 'calib_factor')
        method: Calibration method used (v1, v1.1, v2, v2_improved)
        db_path: Path to calibration database file
    """
    unique_id, board_info = get_arduino_unique_id(ser)
    db = load_calibration_database(db_path)
    
    # Store calibration data
    db[unique_id] = {
        'calib_factor': calib_result['calib_factor'],
        'offset': calib_result.get('offset', calib_result.get('cost', 0)),
        'r_squared': calib_result.get('r_squared', None),
        'method': method,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'board_info': {
            'port': board_info['port'],
            'description': board_info['description'],
            'manufacturer': board_info['manufacturer'],
            'serial_number': board_info['serial_number']
        }
    }
    
    save_calibration_database(db, db_path)
    
    print(f'\n{"="*70}')
    print(f'✓ Calibration saved for this Arduino')
    print(f'{"="*70}')
    print(f'Board ID: {unique_id}')
    print(f'Calibration factor: {calib_result["calib_factor"]:.6f}')
    print(f'This calibration will be automatically used next time.')
    print(f'{"="*70}\n')


def list_all_calibrations(db_path='calibration_database.json'):
    """
    List all stored calibrations in the database.
    Shows calibration age and expiration status (>90 days = expired).
    
    Args:
        db_path: Path to calibration database file
    """
    db = load_calibration_database(db_path)
    
    if not db:
        print('\nNo calibrations stored in database.\n')
        return
    
    now = datetime.datetime.now()
    expired_count = 0
    valid_count = 0
    
    print(f'\n{"="*70}')
    print(f'Stored Calibrations ({len(db)} boards)')
    print(f'{"="*70}\n')
    
    for i, (board_id, data) in enumerate(db.items(), 1):
        print(f'{i}. Board ID: {board_id}')
        print(f'   Port: {data["board_info"]["port"]}')
        print(f'   Description: {data["board_info"]["description"]}')
        if data["board_info"]["serial_number"]:
            print(f'   Serial Number: {data["board_info"]["serial_number"]}')
        print(f'   Calibration factor: {data["calib_factor"]:.6f}')
        print(f'   Method: {data["method"]}')
        print(f'   Last calibrated: {data["timestamp"]}')
        
        # Calculate age and expiration status
        try:
            calib_timestamp = datetime.datetime.strptime(data["timestamp"], '%Y-%m-%d %H:%M:%S')
            age_days = (now - calib_timestamp).days
            age_months = age_days / 30.44
            
            if age_days > 90:
                print(f'   Age: {age_days} days ({age_months:.1f} months) - ⚠️  EXPIRED (recalibration needed)')
                expired_count += 1
            else:
                print(f'   Age: {age_days} days ({age_months:.1f} months) - ✓ Valid')
                valid_count += 1
        except (ValueError, KeyError):
            print(f'   Age: Unknown (timestamp parse error)')
        
        print()
    
    # Summary
    print(f'{"="*70}')
    print(f'Summary: {valid_count} valid, {expired_count} expired (>90 days)')
    if expired_count > 0:
        print(f'\n⚠️  {expired_count} board(s) need recalibration!')
        print(f'Crystal oscillators drift over time. Recalibrate every 3 months')
        print(f'for optimal timing accuracy.')
    print(f'{"="*70}\n')


def delete_calibration(board_id=None, db_path='calibration_database.json'):
    """
    Delete a calibration from the database.
    
    Args:
        board_id: Board ID to delete (if None, will prompt user)
        db_path: Path to calibration database file
    """
    db = load_calibration_database(db_path)
    
    if not db:
        print('\nNo calibrations stored in database.\n')
        return
    
    if board_id is None:
        list_all_calibrations(db_path)
        board_id = input('Enter Board ID to delete (or "cancel"): ').strip()
        if board_id.lower() == 'cancel':
            print('Deletion cancelled.')
            return
    
    if board_id in db:
        confirm = input(f'Delete calibration for {board_id}? (yes/no): ')
        if confirm.lower() == 'yes':
            del db[board_id]
            save_calibration_database(db, db_path)
            print(f'\n✓ Calibration for {board_id} deleted.\n')
        else:
            print('Deletion cancelled.')
    else:
        print(f'\n✗ Board ID {board_id} not found in database.\n')

    
def CheckEmptyDataInMiddle(protocol_df):
    # generated by GPT 4o
    columns_with_empty_in_middle = []
    
    for col in protocol_df.columns:
        data = protocol_df[col]
        
        first_non_null_idx = data.first_valid_index()
        last_non_null_idx = data.last_valid_index()
        
        # if starts with nan values but has non-nan values in the middle
        if first_non_null_idx != 0 and first_non_null_idx is not None:
            columns_with_empty_in_middle.append(col)
            continue
        
        # if nan values in the middle
        if first_non_null_idx is not None and last_non_null_idx is not None:
            if data[first_non_null_idx:last_non_null_idx].isnull().any():
                columns_with_empty_in_middle.append(col)
    
    if columns_with_empty_in_middle:
        raise ValueError(f'The following columns contain empty data in the middle: {columns_with_empty_in_middle}')

def GetChannelInfo(protocol_df):
    
    CheckEmptyDataInMiddle(protocol_df)
    
    # Normalize synonyms and time units before detection
    # This ensures we're looking for standard column names
    df_normalized = NormalizeSynonyms(protocol_df)
    
    # Detect if we have ANY pulse-related columns
    # After synonym normalization, check for: period, pulse_width, frequency, duty_cycle
    pulse_col_indicators = ['_period', '_pulse_width', '_frequency', '_duty_cycle']
    has_pulse_cols = any(indicator in col for col in df_normalized.columns for indicator in pulse_col_indicators)
    
    if has_pulse_cols:
        # New format: determine number of pulse columns per channel
        # Count distinct pulse parameter types for first channel
        ch1_pulse_cols = [col for col in df_normalized.columns if col.startswith('CH1_') and any(ind in col for ind in pulse_col_indicators)]
        num_pulse_cols = len(ch1_pulse_cols)
        
        # Each channel has: status + time + pulse parameters
        expected_cols_per_channel = 2 + num_pulse_cols
        candidates_num = (df_normalized.shape[1] - 1) / expected_cols_per_channel
    else:
        # Old format: each channel has 2 columns (status, time)
        expected_cols_per_channel = 2
        candidates_num = (df_normalized.shape[1] - 1) / expected_cols_per_channel
    
    if candidates_num % 1 != 0:
        pulse_info = f", plus {num_pulse_cols} pulse parameters" if has_pulse_cols else ""
        raise ValueError(f'The number of channel columns in the protocol file is not correct. Expected {expected_cols_per_channel} columns per channel (status, time{pulse_info}).')
    else:
        candidates_num = int(candidates_num)

    # get channel number and verify the format
    ch_num = 0
    for i in range(int(candidates_num)):
        # check if the column name ends with '_status' and the next column ends with '_time_[unit]'
        col_status_i = df_normalized.columns[i*expected_cols_per_channel+1]
        col_time_i = df_normalized.columns[i*expected_cols_per_channel+2]
        status_name_i = col_status_i.split('_')[0]
        time_name_i = col_time_i.split('_')[0]
        ch_name_i = 'CH' + str(i+1)
        
        if (not status_name_i == ch_name_i) or (not col_status_i.split('_')[-1] == 'status'):
            raise ValueError(f'Column {i*expected_cols_per_channel+1} "{col_status_i}" does not match the format of continuous channel index or status assignment, which should be "{ch_name_i}_status".')
        elif (not time_name_i == ch_name_i) or (not col_time_i.split('_')[-2] == 'time'):
            raise ValueError(f'Column {i*expected_cols_per_channel+2} "{col_time_i}" does not match the format of continuous channel index or time assignment, which should be "{ch_name_i}_time_[unit]".')
        
        # Check pulse parameter columns if present
        # After normalization, they should be: frequency, period, pulse_width, duty_cycle (any combination)
        if has_pulse_cols:
            # Verify each pulse column belongs to this channel
            for col_idx in range(2, expected_cols_per_channel):
                col_i = df_normalized.columns[i*expected_cols_per_channel + col_idx + 1]
                if not col_i.startswith(f'{ch_name_i}_'):
                    raise ValueError(f'Column {i*expected_cols_per_channel + col_idx + 1} "{col_i}" does not belong to channel {ch_name_i}.')
                
                # Verify it's a recognized pulse parameter
                pulse_param = col_i.replace(f'{ch_name_i}_', '').split('_')[0]
                if pulse_param not in ['frequency', 'period', 'pulse', 'duty']:  # 'pulse' for pulse_width
                    raise ValueError(f'Column {i*expected_cols_per_channel + col_idx + 1} "{col_i}" is not a recognized pulse parameter.')
        
        ch_num += 1
    
    # get valid length of each channel
    ch_valid_length = dict()
    valid_channels = []
    for i in range(ch_num):
        ch_name = 'CH' + str(i+1)
        ch_status = df_normalized.iloc[:, i*expected_cols_per_channel+1]
        ch_time = df_normalized.iloc[:, i*expected_cols_per_channel+2]
        
        ch_valid_length[ch_name] = ch_status.count()
        if ch_valid_length[ch_name] != ch_time.count():
            raise ValueError(f'Channel "{ch_name}" has different length of status and time columns.')
        
        # Check period and pulse_width columns if present
        if has_pulse_cols:
            ch_period = df_normalized.iloc[:, i*expected_cols_per_channel+3]
            ch_pw = df_normalized.iloc[:, i*expected_cols_per_channel+4]
            # Period and pulse_width can have NaN values, but we count non-NaN for consistency checking
            # They should be specified when status=1, but can be left empty when status=0
        
        if ch_valid_length[ch_name] == 0:
            print(f'Channel "{ch_name}" is empty.')
        else:
            valid_channels.append(ch_name)
        
    # get channel time units
    ch_units = [df_normalized.columns[i*expected_cols_per_channel+2].split('_')[-1] for i in range(ch_num)]
    for i in range(ch_num):
        if ch_units[i] in ['s', 'sec', 'second', 'seconds']:
            ch_units[i] = 'sec'
        elif ch_units[i] in ['m', 'min', 'minute', 'minutes']:
            ch_units[i] = 'min'
        elif ch_units[i] in ['h', 'hr', 'hour', 'hours']:
            ch_units[i] = 'hr'
        elif ch_units[i] in ['ms', 'msec', 'millisecond', 'milliseconds']:
            ch_units[i] = 'ms'
        else:
            raise ValueError(f'Channel time unit {ch_units[i]} is not recognized. Please use millisecond(msec, ms), second(sec, s), minute(min, m), or hour(hr, h).')
    
    return ch_units, valid_channels

def NormalizeSynonyms(protocol_df):
    """
    Normalize column name synonyms to standard format.
    
    Supported synonyms:
        - Period: period, Period, PERIOD, T, cycle_time, cycletime
        - Pulse_Width: pulse_width, pulsewidth, pulsewdith, pulse_wdith, PulseWidth, 
                      Pulse_Width, PW, pw, on_time, ontime
        - Duty_Cycle: duty_cycle, dutycycle, DutyCycle, Duty_Cycle, DC, dc, duty
        - Frequency: frequency, Frequency, FREQUENCY, freq, frq, f, hz, Hz
    
    Time unit suffixes are preserved during this step (handled separately).
    
    Args:
        protocol_df: DataFrame with potentially synonym column names
    
    Returns:
        DataFrame with normalized column names
    """
    df = protocol_df.copy()
    
    # Define synonym mappings (case-insensitive except for 'T')
    # Format: {synonym: standard_name}
    synonym_map = {
        # Period synonyms
        'period': 'period',
        'Period': 'period',
        'PERIOD': 'period',
        'T': 'period',  # Capital T only (case-sensitive)
        'cycle_time': 'period',
        'cycletime': 'period',
        
        # Pulse_width synonyms
        'pulse_width': 'pulse_width',
        'pulsewidth': 'pulse_width',
        'pulsewdith': 'pulse_width',  # Common typo
        'pulse_wdith': 'pulse_width',  # Common typo
        'PulseWidth': 'pulse_width',
        'Pulse_Width': 'pulse_width',
        'PW': 'pulse_width',
        'pw': 'pulse_width',
        'on_time': 'pulse_width',
        'ontime': 'pulse_width',
        
        # Duty_cycle synonyms
        'duty_cycle': 'duty_cycle',
        'dutycycle': 'duty_cycle',
        'DutyCycle': 'duty_cycle',
        'Duty_Cycle': 'duty_cycle',
        'DC': 'duty_cycle',
        'dc': 'duty_cycle',
        'duty': 'duty_cycle',
        
        # Frequency synonyms
        'frequency': 'frequency',
        'Frequency': 'frequency',
        'FREQUENCY': 'frequency',
        'freq': 'frequency',
        'frq': 'frequency',
        'f': 'frequency',
        'hz': 'frequency',
        'Hz': 'frequency',
    }
    
    # Process each column
    new_columns = []
    for col in df.columns:
        if col == 'Sections':
            new_columns.append(col)
            continue
        
        # Parse column name: CH#_synonym or CH#_synonym_unit
        parts = col.split('_')
        if len(parts) < 2 or not parts[0].startswith('CH'):
            new_columns.append(col)
            continue
        
        ch_prefix = parts[0]  # CH1, CH2, etc.
        
        # Detect if last part is a time unit suffix
        time_units = ['ms', 'msec', 'millisecond', 'milliseconds',
                     's', 'sec', 'second', 'seconds',
                     'm', 'min', 'minute', 'minutes',
                     'h', 'hr', 'hour', 'hours']
        
        has_unit_suffix = False
        unit_suffix = ''
        param_parts = parts[1:]  # Everything after CH#
        
        if param_parts[-1] in time_units:
            has_unit_suffix = True
            unit_suffix = param_parts[-1]
            param_parts = param_parts[:-1]  # Remove unit suffix
        
        # Reconstruct parameter name (could be multi-part like 'pulse_width')
        param_name = '_'.join(param_parts)
        
        # Special case: 'T' must be exactly 'T' (case-sensitive)
        if param_name == 'T':
            standard_name = 'period'
        elif param_name == 't':
            # Reject lowercase 't' (ambiguous with time)
            raise ValueError(
                f"Ambiguous column name '{col}':\n"
                f"  Lowercase 't' is not allowed (could mean time or period).\n"
                f"  Use capital 'T' for period, or spell out 'period':\n"
                f"    {ch_prefix}_T or {ch_prefix}_period"
            )
        else:
            # Check if it's a synonym (case-insensitive for most)
            standard_name = None
            for syn, std in synonym_map.items():
                if param_name.lower() == syn.lower() and syn != 'T':  # Case-insensitive except T
                    standard_name = std
                    break
            
            if standard_name is None:
                # Not a pulse parameter synonym, keep original
                new_columns.append(col)
                continue
        
        # Reconstruct column name
        if has_unit_suffix:
            new_col = f"{ch_prefix}_{standard_name}_{unit_suffix}"
        else:
            new_col = f"{ch_prefix}_{standard_name}"
        
        new_columns.append(new_col)
    
    df.columns = new_columns
    return df


def ConvertPulseTimeUnits(protocol_df):
    """
    Convert time unit suffixes in pulse parameter columns to milliseconds.
    
    Supported time units:
        - ms, msec, millisecond, milliseconds (×1)
        - s, sec, second, seconds (×1000)
        - m, min, minute, minutes (×60000)
        - h, hr, hour, hours (×3600000)
    
    Only applies to period and pulse_width columns (not duty_cycle or frequency).
    
    Args:
        protocol_df: DataFrame with potentially time-unit-suffixed columns
    
    Returns:
        DataFrame with time units converted to ms and suffixes removed from column names
    """
    df = protocol_df.copy()
    
    # Define time unit multipliers
    unit_multipliers = {
        'ms': 1,
        'msec': 1,
        'millisecond': 1,
        'milliseconds': 1,
        's': 1000,
        'sec': 1000,
        'second': 1000,
        'seconds': 1000,
        'm': 60000,
        'min': 60000,
        'minute': 60000,
        'minutes': 60000,
        'h': 3600000,
        'hr': 3600000,
        'hour': 3600000,
        'hours': 3600000,
    }
    
    # Parameters that support time units
    time_unit_params = ['period', 'pulse_width']
    
    # Process columns
    columns_to_rename = {}
    for col in df.columns:
        if col == 'Sections':
            continue
        
        # Parse: CH#_param_unit
        parts = col.split('_')
        if len(parts) < 3 or not parts[0].startswith('CH'):
            continue
        
        # Check if this is a time-unit parameter
        # Could be CH#_period_unit or CH#_pulse_width_unit (2 words)
        unit_suffix = parts[-1]
        if unit_suffix not in unit_multipliers:
            continue
        
        # Determine parameter name (everything between CH# and unit)
        param_parts = parts[1:-1]
        param_name = '_'.join(param_parts)
        
        if param_name not in time_unit_params:
            continue
        
        # Convert values
        multiplier = unit_multipliers[unit_suffix]
        if multiplier != 1:  # Only convert if not already in ms
            df[col] = df[col] * multiplier
        
        # Mark for renaming (remove unit suffix)
        ch_prefix = parts[0]
        new_col = f"{ch_prefix}_{param_name}"
        columns_to_rename[col] = new_col
    
    # Rename columns to remove unit suffixes
    if columns_to_rename:
        df = df.rename(columns=columns_to_rename)
    
    return df


def NormalizePulseParameters(protocol_df):
    """
    Convert various pulse parameter combinations to standard Period + pulse_width format (both in ms).
    
    PREREQUISITE: This function expects synonyms and time units to already be normalized.
    Call NormalizeSynonyms() and ConvertPulseTimeUnits() before this function.
    
    Supports 4 input combinations:
    1. frequency (Hz) + pulse_width (ms) → convert frequency to period
    2. frequency (Hz) + duty_cycle (%) → calculate both period and pulse_width
    3. period (ms) + pulse_width (ms) → already in standard format
    4. period (ms) + duty_cycle (%) → calculate pulse_width
    
    All outputs will be: period (ms) + pulse_width (ms)
    This eliminates float operations in Arduino by using only integer milliseconds.
    
    Validates:
    - pulse_width must be <= period
    - duty_cycle must be <= 100%
    - Both determinants must be present (or both absent)
    """
    df = protocol_df.copy()
    
    # Find all channels
    channel_cols = [col for col in df.columns if col.startswith('CH') and col.endswith('_status')]
    
    for ch_col in channel_cols:
        ch_num = ch_col.split('_')[0]  # e.g., 'CH1'
        
        # Check which pulse columns exist
        freq_col = f'{ch_num}_frequency'
        period_col = f'{ch_num}_period'
        pw_col = f'{ch_num}_pulse_width'
        dc_col = f'{ch_num}_duty_cycle'
        
        has_freq = freq_col in df.columns
        has_period = period_col in df.columns
        has_pw = pw_col in df.columns
        has_dc = dc_col in df.columns
        
        # Skip if no pulse parameters
        if not (has_freq or has_period or has_pw or has_dc):
            continue
        
        # Create standard columns if they don't exist (period and pulse_width)
        if not has_period:
            df[period_col] = 0
        if not has_pw:
            df[pw_col] = 0
        
        # Convert based on what's provided
        for idx in df.index:
            freq = df.loc[idx, freq_col] if has_freq else 0
            period = df.loc[idx, period_col] if has_period else 0
            pw = df.loc[idx, pw_col] if has_pw else 0
            dc = df.loc[idx, dc_col] if has_dc else 0
            
            # Handle NaN
            freq = 0 if pd.isna(freq) else freq
            period = 0 if pd.isna(period) else period
            pw = 0 if pd.isna(pw) else pw
            dc = 0 if pd.isna(dc) else dc
            
            # Handle duty cycle with % sign: "10%" or "10.5%" → 10.0 or 10.5
            if isinstance(dc, str):
                dc = dc.strip()
                if dc.endswith('%'):
                    dc = float(dc.rstrip('%'))
                else:
                    dc = float(dc) if dc else 0
            
            # Normalize duty cycle: support both decimal (0.1) and percentage (10) formats
            # If duty cycle is between 0 and 1 (exclusive), treat as decimal and convert to percentage
            if 0 < dc <= 1:
                dc = dc * 100.0  # Convert 0.1 → 10%
            
            # Validate duty cycle range
            if dc > 100:
                raise ValueError(
                    f"Invalid duty_cycle in {ch_num} row {idx+2}: {dc}%\n"
                    f"Duty cycle must be between 0% and 100% (or 0.0-1.0 in decimal format).\n"
                    f"A duty cycle > 100% means pulse width exceeds the period, which is impossible."
                )
            
            # Case 1: frequency + pulse_width → convert frequency to period
            if freq > 0 and pw > 0:
                period_calculated = int(1000.0 / freq)  # Convert Hz to ms
                # Validate pulse_width <= period
                if pw > period_calculated:
                    raise ValueError(
                        f"Invalid pulse parameters in {ch_num} row {idx+2}:\n"
                        f"  frequency={freq} Hz → period={period_calculated} ms\n"
                        f"  pulse_width={pw} ms\n"
                        f"Pulse width ({pw} ms) cannot exceed period ({period_calculated} ms).\n"
                        f"Either reduce pulse_width or reduce frequency."
                    )
                df.loc[idx, period_col] = period_calculated
                df.loc[idx, pw_col] = int(pw)
            
            # Case 2: frequency + duty_cycle → calculate both period and pulse_width
            elif freq > 0 and dc > 0:
                period_calculated = int(1000.0 / freq)  # Convert Hz to ms
                pw_calculated = int(period_calculated * dc / 100.0)
                df.loc[idx, period_col] = period_calculated
                df.loc[idx, pw_col] = pw_calculated
            
            # Case 3: period + pulse_width → already in standard format
            elif period > 0 and pw > 0:
                # Validate pulse_width <= period
                if pw > period:
                    raise ValueError(
                        f"Invalid pulse parameters in {ch_num} row {idx+2}:\n"
                        f"  period={period} ms\n"
                        f"  pulse_width={pw} ms\n"
                        f"Pulse width ({pw} ms) cannot exceed period ({period} ms).\n"
                        f"Either reduce pulse_width or increase period."
                    )
                df.loc[idx, period_col] = int(period)
                df.loc[idx, pw_col] = int(pw)
            
            # Case 4: period + duty_cycle → calculate pulse_width
            elif period > 0 and dc > 0:
                pw_calculated = int(period * dc / 100.0)
                df.loc[idx, period_col] = int(period)
                df.loc[idx, pw_col] = pw_calculated
            
            # Case 5: Partial specification - only one determinant (ERROR)
            elif (freq > 0 and dc == 0 and pw == 0) or (period > 0 and dc == 0 and pw == 0):
                raise ValueError(
                    f"Incomplete pulse parameters in {ch_num} row {idx+2}:\n"
                    f"  frequency={freq}, period={period}, pulse_width={pw}, duty_cycle={dc}\n"
                    f"You must specify BOTH determinants:\n"
                    f"  - frequency/period AND pulse_width, OR\n"
                    f"  - frequency/period AND duty_cycle\n"
                    f"To disable pulsing, set both to 0 or leave both empty."
                )
            elif (pw > 0 and freq == 0 and period == 0) or (dc > 0 and freq == 0 and period == 0):
                raise ValueError(
                    f"Incomplete pulse parameters in {ch_num} row {idx+2}:\n"
                    f"  frequency={freq}, period={period}, pulse_width={pw}, duty_cycle={dc}\n"
                    f"You must specify BOTH determinants:\n"
                    f"  - frequency/period AND pulse_width, OR\n"
                    f"  - frequency/period AND duty_cycle\n"
                    f"To disable pulsing, set both to 0 or leave both empty."
                )
            
            # Case 6: No pulse (all zeros or missing) - valid
            else:
                df.loc[idx, period_col] = 0
                df.loc[idx, pw_col] = 0
        
        # Remove auxiliary columns (frequency, duty_cycle) after conversion
        if has_freq and freq_col in df.columns:
            df = df.drop(columns=[freq_col])
        if has_dc and dc_col in df.columns:
            df = df.drop(columns=[dc_col])
    
    return df

def ConvertTimeToMillisecond(protocol_df, ch_units):
    df_ms = protocol_df.copy()
    
    # Step 1: Normalize column name synonyms (T→period, PW→pulse_width, etc.)
    df_ms = NormalizeSynonyms(df_ms)
    
    # Step 2: Convert pulse parameter time units to milliseconds
    df_ms = ConvertPulseTimeUnits(df_ms)
    
    # Step 3: Normalize pulse parameters (convert all formats to period + pulse_width in ms)
    df_ms = NormalizePulseParameters(df_ms)
    
    # Detect if we have pulse columns
    has_pulse_cols = any('_period' in col for col in df_ms.columns)
    expected_cols_per_channel = 4 if has_pulse_cols else 2
    
    col_names = df_ms.columns.tolist()
    for i in range(len(ch_units)):
        col_names[i*expected_cols_per_channel+2] = col_names[i*expected_cols_per_channel+2].split('_')[0] + '_time_ms'
    df_ms.columns = col_names
    
    for i in range(len(ch_units)):
        time_col_idx = i*expected_cols_per_channel+2
        if ch_units[i] == 'sec':
            df_ms.iloc[:, time_col_idx] = df_ms.iloc[:, time_col_idx] * 1000
        elif ch_units[i] == 'min':
            df_ms.iloc[:, time_col_idx] = df_ms.iloc[:, time_col_idx] * 60 * 1000
        elif ch_units[i] == 'hr':
            df_ms.iloc[:, time_col_idx] = df_ms.iloc[:, time_col_idx] * 60 * 60 * 1000
        elif ch_units[i] == 'ms':
            pass
        else:
            raise ValueError(f'Channel time unit {ch_units[i]} is not recognized. Please use millisecond(msec, ms), second(sec, s), minute(min, m), or hour(hr, h).')
    
    # Fill NaN values with 0 for status and time columns
    # For period and pulse_width, fill NaN with 0 (means no pulsing)
    for col in df_ms.columns:
        if col.endswith('_status') or col.endswith('_time_ms'):
            df_ms[col] = df_ms[col].fillna(0)
    
    # convert columns to appropriate types
    for col in df_ms.columns[1:]:
        if col.endswith('_status') or col.endswith('_time_ms') or col.endswith('_pulse_width') or col.endswith('_period'):
            # These should be integers (period is now in ms, no more float needed)
            df_ms[col] = df_ms[col].fillna(0).astype(int)
    
    # Check for values greater than 2^32 - 1, excluding strings and floats
    for col in df_ms.columns:
        if df_ms[col].dtype in [int, 'int64', 'int32'] and df_ms[col].max() > 2**32 - 1:
            max_val = df_ms[col].max()
            max_val_loc = df_ms[df_ms[col] == max_val].index.tolist()
            raise ValueError(f'The value {max_val} in column "{col}" is larger than the maximum value of 2^32 - 1. Please check the following rows: {max_val_loc}')
    return df_ms

def str2datetime(time_str):
    # generated by GPT 4o
    # Try time-only formats first - these need today's date
    time_only_formats = ['%H:%M', '%H:%M:%S']
    for fmt in time_only_formats:
        try:
            parsed_time = datetime.datetime.strptime(time_str, fmt)
            # Time-only formats return 1900-01-01, replace with today
            today = datetime.datetime.now().date()
            return datetime.datetime.combine(today, parsed_time.time())
        except ValueError:
            continue
    
    # Try full datetime formats - preserve the date as-is
    datetime_formats = ['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S']
    for fmt in datetime_formats:
        try:
            return datetime.datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Time data '{time_str}' does not match any of the formats: {time_only_formats + datetime_formats}")

def ReadStartTime(df_startTime):
    """
    Read start time and wait status from DataFrame.
    Supports two formats:
    
    Format 1 (Row-based, original): 
        Columns: CH1, CH2, CH3, ...
        Row 0: start_time values
        Row 1: wait_status values
    
    Format 2 (Column-based, NEW - better for many channels):
        Column 'Channels': CH1, CH2, CH3, ...
        Column 'Start_time': start_time values
        Column 'Wait_status': wait_status values
    """
    
    # Detect format by checking if 'Channels', 'Start_time', and 'Wait_status' columns exist
    columns_lower = [col.lower().replace('_', '').replace(' ', '') for col in df_startTime.columns]
    has_channels_col = any(col == 'channels' for col in columns_lower)
    has_starttime_col = any(col in ['starttime', 'start'] for col in columns_lower)
    has_waitstatus_col = any(col in ['waitstatus', 'wait'] for col in columns_lower)
    
    if has_channels_col and has_starttime_col and has_waitstatus_col:
        # Format 2: Column-based format (NEW)
        return _ReadStartTimeColumnFormat(df_startTime)
    else:
        # Format 1: Row-based format (ORIGINAL)
        return _ReadStartTimeRowFormat(df_startTime)

def _ReadStartTimeColumnFormat(df_startTime):
    """Read start time from column-based format (Channels | Start_time | Wait_status)"""
    
    # Find the correct column names (case-insensitive)
    columns_map = {}
    for col in df_startTime.columns:
        col_normalized = col.lower().replace('_', '').replace(' ', '')
        if col_normalized == 'channels':
            columns_map['channels'] = col
        elif col_normalized in ['starttime', 'start']:
            columns_map['start_time'] = col
        elif col_normalized in ['waitstatus', 'wait']:
            columns_map['wait_status'] = col
    
    if len(columns_map) != 3:
        raise ValueError(f'Column-based format requires "Channels", "Start_time", and "Wait_status" columns. Found: {df_startTime.columns.tolist()}')
    
    start_time = dict()
    wait_status = dict()
    start_time_nans = []
    wait_status_nans = []
    
    # Validate channel names
    pattern = re.compile(r'CH\d+')
    for idx, row in df_startTime.iterrows():
        ch_name = row[columns_map['channels']]
        
        # Handle NaN channel names
        if pd.isna(ch_name):
            continue
            
        ch_name = str(ch_name).strip()
        if not pattern.match(ch_name):
            raise ValueError(f'Channel name "{ch_name}" does not match the format CH + number (CH1, CH2, ..., starts from CH1).')
        
        ch_time = row[columns_map['start_time']]
        ch_status = row[columns_map['wait_status']]
        
        # Process start time
        if pd.isna(ch_time):
            start_time[ch_name] = None
            start_time_nans.append(ch_name)
        elif type(ch_time) is datetime.time:
            start_time[ch_name] = ch_time
        elif isinstance(ch_time, (int, float, np.integer, np.floating)): # in seconds
            start_time[ch_name] = ch_time
        else:
            start_time[ch_name] = str2datetime(str(ch_time))
            Warning(f'Channel "{ch_name}" start time is not in datetime format or countdown in seconds. Auto conversion may cause errors.')
        
        # Process wait status
        if pd.isna(ch_status):
            wait_status[ch_name] = None
            wait_status_nans.append(ch_name)
        else:
            wait_status[ch_name] = int(bool(ch_status))
    
    if start_time_nans != wait_status_nans:
        raise ValueError(f'Incomplete start time file. A channel should have both or neither start time and wait status')
    
    # if the start time does not have date, add the date of today
    today = datetime.datetime.now().date()
    for key in start_time.keys():
        if type(start_time[key]) is datetime.time:
            start_time[key] = datetime.datetime.combine(today, start_time[key])
    
    return start_time, wait_status

def _ReadStartTimeRowFormat(df_startTime):
    """Read start time from row-based format (Original: CH1, CH2, CH3 as columns)"""
    
    # check if the start time file has only two rows
    if df_startTime.shape[0] != 2:
        raise ValueError('The start time file (row-based format) should have two rows: one for start_time and one for the wait_status.')
    
    # check if column names match 'CH' + number (ignore non-CH columns)
    pattern = re.compile(r'CH\d+')
    valid_columns = []
    for col in df_startTime.columns:
        if pattern.match(col):
            valid_columns.append(col)
    
    if not valid_columns:
        raise ValueError(f'No valid channel columns (CH1, CH2, ...) found. Columns: {df_startTime.columns.tolist()}')
    
    # read the start time of each channel and convert to datetime
    start_time = dict()
    wait_status = dict()
    start_time_nans = []
    wait_status_nans = []
    for col in valid_columns:
        # read as string using .iloc for position-based indexing
        ch_time = df_startTime[col].iloc[0]
        ch_status = df_startTime[col].iloc[1]
        
        if pd.isna(ch_time):
            start_time[col] = None
            start_time_nans.append(col)
        elif type(ch_time) is datetime.time:
            start_time[col] = ch_time
        elif isinstance(ch_time, (int, float, np.integer, np.floating)): # in seconds
            start_time[col] = ch_time
        else:
            start_time[col] = str2datetime(str(ch_time))
            Warning(f'Channel "{col}" start time is not in datetime format or countdown in seconds. Auto conversion may cause errors.')
        if pd.isna(ch_status):
            wait_status[col] = None
            wait_status_nans.append(col)
        else:
            wait_status[col] = int(bool(ch_status))
            
    if start_time_nans != wait_status_nans:
        raise ValueError(f'Incomplete start time file. A channel should have both or neither start time and wait status')
    
    # if the start time does not have date, add the date of today
    today = datetime.datetime.now().date()
    for key in start_time.keys():
        if type(start_time[key]) is datetime.time:
            start_time[key] = datetime.datetime.combine(today, start_time[key])
    
    return start_time, wait_status

def CheckStartTimeForChannels(start_time, valid_channels):
    # check if start time is missing
    missing_start_time = []
    for ch in valid_channels:
        if ch not in start_time.keys() or start_time[ch] is None:
            missing_start_time.append(ch)
    if missing_start_time:
        raise ValueError(f'Start time is missing for the following channels: {missing_start_time}')
    
    # check if start time is earlier than current time
    earlier_start_time = []
    countdown_channels = []
    for ch in valid_channels:
        if isinstance(start_time[ch], (int, float, np.integer, np.floating)):
            Warning(f'Channel "{ch}" start time is in seconds. It will be treated as countdown.')
            countdown_channels.append(ch)
        elif type(start_time[ch]) is datetime.datetime and start_time[ch] < datetime.datetime.now():
            earlier_start_time.append(ch)
        else:
            # convert to string and then to datetime
            try:
                start_time[ch] = str2datetime(str(start_time[ch]))
                if start_time[ch] < datetime.datetime.now():
                    earlier_start_time.append(ch)
            except ValueError:
                raise ValueError(f'Start time for channel {ch} is not recognized. Please use datetime format or countdown number in seconds.')
    if earlier_start_time:
        raise ValueError(f'Start time is earlier than current time for the following channels: {earlier_start_time}')

def CountDown(start_time):
    '''return the remaining time for each channel to start in milliseconds'''
    # get remaining time for each channel to start, convert to milliseconds
    remaining_time = dict()
    for ch in start_time.keys():
        if isinstance(start_time[ch], (int, float, np.integer, np.floating)):
            remaining_time[ch] = int(start_time[ch] * 1000)
        elif type(start_time[ch]) is datetime.datetime:
            remaining_time[ch] = int((start_time[ch] - datetime.datetime.now()).total_seconds() * 1000) 
    return remaining_time

def SendCommand(ser, command, time_out=5):
    command = str(command).strip()
    cmd_t = command + '\n'
    ser.write(cmd_t.encode('utf-8'))
    t_cmd = time.time()
    while True:
        if ser.inWaiting() > 0:
            fb = ser.readline().decode('utf-8').strip()
            if fb == command.strip():
                print(f'Python: Command "{cmd_t.strip()}" is sent successfully.')
                break
            else:
                print(f'\033[31mCommand "{cmd_t.strip()}" is not received correctly. Received "{fb}".\033[0m')
                break
        if time.time() - t_cmd > time_out:
            print(f'\033[31mCommand "{cmd_t.strip()}" is not received correctly. Timeout. Please check the connection.\033[0m')
            break

def SendGreeting(ser, time_out=10, expected_pattern_length=None):
    """
    Send greeting to Arduino and parse configuration response.
    
    Args:
        ser: Serial connection object
        time_out: Timeout in seconds
        expected_pattern_length: Expected PATTERN_LENGTH value (for verification)
        
    Returns:
        dict: Arduino configuration {'pattern_length': int, 'max_pattern_num': int, 'max_channel_num': int}
    """
    # Clear any residual data in buffer before greeting (important for Arduino Due)
    ser.reset_input_buffer()
    time.sleep(0.5)
    
    greeting = 'Hello\n'
    ser.write(greeting.encode('utf-8'))
    ser.flush()  # Ensure data is sent
    t_greet = time.time()
    
    arduino_config = {}
    
    while True:
        if ser.inWaiting() > 0:
            fb = ser.readline().decode('utf-8').strip()
            
            # Parse new format: "Salve;PATTERN_LENGTH:4;MAX_PATTERN_NUM:10;MAX_CHANNEL_NUM:8"
            if fb.startswith('Salve'):
                print('Arduino: Salve!')
                
                # Parse configuration parameters
                parts = fb.split(';')
                for part in parts[1:]:  # Skip "Salve"
                    if ':' in part:
                        key, value = part.split(':', 1)
                        key = key.strip().lower()
                        try:
                            arduino_config[key] = int(value.strip())
                        except ValueError:
                            print(f'\033[33mWarning: Could not parse {key}={value}\033[0m')
                
                # Display configuration
                if arduino_config:
                    print(f'Arduino Configuration:')
                    for key, val in arduino_config.items():
                        print(f'  {key.upper()}: {val}')
                    
                    # Verify PATTERN_LENGTH if specified
                    if expected_pattern_length is not None and 'pattern_length' in arduino_config:
                        arduino_pl = arduino_config['pattern_length']
                        python_pl = expected_pattern_length
                        
                        if python_pl > arduino_pl:
                            # Python needs more than Arduino can provide - this is an ERROR
                            raise ValueError(
                                f'\n\033[31mPATTERN_LENGTH MISMATCH!\033[0m\n'
                                f'  Python requires: {python_pl}\n'
                                f'  Arduino supports: {arduino_pl}\n'
                                f'Protocol requires pattern length {python_pl} but Arduino only supports up to {arduino_pl}.\n'
                                f'Please update Arduino sketch PATTERN_LENGTH to at least {python_pl}.'
                            )
                        elif python_pl < arduino_pl:
                            # Python needs less than Arduino can provide - this is OK, just warn
                            print(f'\033[33m⚠️  PATTERN_LENGTH mismatch (safe):\033[0m')
                            print(f'\033[33m   Protocol uses: {python_pl}\033[0m')
                            print(f'\033[33m   Arduino supports: {arduino_pl}\033[0m')
                            print(f'   \033[32m✓ Compatible:\033[0m \033[33mArduino can handle smaller patterns.\033[0m')
                        else:
                            # Perfect match
                            print(f'\033[32m✓ PATTERN_LENGTH verified: {expected_pattern_length}\033[0m')
                
                return arduino_config
                
            elif fb == 'Salve':
                # Old format (backward compatible)
                print('Arduino: Salve!')
                print('\033[33mWarning: Arduino firmware does not report configuration. Consider updating firmware.\033[0m')
                return {}
                
            elif fb:  # Got some response but not the expected one
                print(f'Unexpected response: "{fb}". Retrying...')
                # Try sending greeting again
                ser.write(greeting.encode('utf-8'))
                ser.flush()
                t_greet = time.time()  # Reset timeout
            else:
                continue
                
        if time.time() - t_greet > time_out:
            raise TimeoutError(f'Greeting "{greeting.strip()}" is not received correctly. Timeout. Please check the connection.')
    
    return arduino_config

def GetArduinoMemory(ser, time_out=5):
    """
    Get Arduino memory information.
    
    Returns:
        dict: Memory information
            - free: Free SRAM in bytes
            - total: Total SRAM in bytes
            - used: Used SRAM in bytes
            - percent_used: Percentage of SRAM used
            - pulse_mode: Current pulse mode (0 or 1)
            - pulse_compile: Compile-time mode ('dynamic', 'always', 'never')
    """
    command = 'GET_MEMORY'
    ser.write((command + '\n').encode('utf-8'))
    t_cmd = time.time()
    
    while True:
        if ser.inWaiting() > 0:
            response = ser.readline().decode('utf-8').strip()
            
            # Parse: MEMORY;FREE:12345;TOTAL:98304;PULSE_MODE:1;PULSE_COMPILE:dynamic
            if response.startswith('MEMORY;'):
                parts = response.split(';')
                memory_info = {}
                
                for part in parts[1:]:  # Skip "MEMORY"
                    if ':' in part:
                        key, value = part.split(':', 1)
                        memory_info[key.lower()] = value
                
                # Convert numeric values
                free_ram = int(memory_info.get('free', 0))
                total_ram = int(memory_info.get('total', 0)) if memory_info.get('total') != 'unknown' else 0
                
                result = {
                    'free': free_ram,
                    'total': total_ram,
                    'used': total_ram - free_ram if total_ram > 0 else 0,
                    'percent_used': ((total_ram - free_ram) / total_ram * 100) if total_ram > 0 else 0,
                    'pulse_mode': int(memory_info.get('pulse_mode', 0)),
                    'pulse_compile': memory_info.get('pulse_compile', 'unknown')
                }
                
                return result
            elif response:
                print(f'Unexpected response: "{response}"')
                
        if time.time() - t_cmd > time_out:
            print(f'\033[31mGET_MEMORY timeout. Arduino may not support memory reporting.\033[0m')
            return None

def CheckPulseModeCompatibility(ser, protocol_requires_pulse, time_out=5):
    """
    Check if Arduino pulse mode is compatible with protocol requirements.
    
    Raises warning if protocol needs pulses but Arduino pulse mode is disabled
    at compile time.
    
    Args:
        ser: Serial connection object
        protocol_requires_pulse: True if protocol uses pulse parameters
        time_out: Timeout in seconds
        
    Returns:
        bool: True if compatible, False if incompatible
    """
    # Get Arduino memory info (includes pulse mode status)
    mem_info = GetArduinoMemory(ser, time_out)
    
    if mem_info is None:
        print('\033[33m⚠️  Warning: Could not check pulse mode compatibility (memory info unavailable)\033[0m')
        return True  # Assume compatible if can't check
    
    arduino_pulse_enabled = mem_info['pulse_mode'] == 1
    
    print(f'\n🔍 Pulse Mode Compatibility Check:')
    print(f'   Protocol requires pulses: {"YES" if protocol_requires_pulse else "NO"}')
    print(f'   Arduino pulse mode:       {"ENABLED" if arduino_pulse_enabled else "DISABLED"} (compile-time)')
    
    # Check for incompatibility
    if protocol_requires_pulse and not arduino_pulse_enabled:
        print(f'\n{"="*70}')
        print('❌ ERROR: Pulse Mode Incompatibility!')
        print(f'{"="*70}')
        print(f'  Protocol REQUIRES pulse modulation')
        print(f'  But Arduino pulse mode is DISABLED')
        print(f'')
        print(f'  Arduino firmware was compiled with PULSE_MODE_COMPILE = 0')
        print(f'  Pulse support is DISABLED at compile time.')
        print(f'')
        print(f'  ⚠️  Solution: Recompile Arduino firmware with PULSE_MODE_COMPILE = 1')
        print(f'     Edit light_controller_v2_2_arduino.ino, change:')
        print(f'     #define PULSE_MODE_COMPILE 0  →  #define PULSE_MODE_COMPILE 1')
        print(f'     Then recompile and upload to Arduino.')
        print(f'{"="*70}\n')
        return False
    
    elif not protocol_requires_pulse and arduino_pulse_enabled:
        # Protocol doesn't need pulses but Arduino has them enabled
        # This is OK, just not optimal for memory
        print(f'   ✓ Compatible (Arduino pulse enabled but not needed)')
        print(f'   \033[33m💡 Note: Protocol does NOT use pulse modulation\033[0m')
        print(f'   \033[33m   Arduino has pulse mode ENABLED (~2.5KB memory used)\033[0m')
        print(f'   \033[33m   Consider setting PULSE_MODE_COMPILE = 0 to save memory\033[0m')
        return True
    
    else:
        # Perfect match
        print(f'   ✓ Compatible')
        return True

def SayBye(ser, time_out=5):
    bye = 'Bye\n'
    ser.write(bye.encode('utf-8'))
    t_bye = time.time()
    while True:
        if ser.inWaiting() > 0:
            fb = ser.readline().decode('utf-8').strip()
            if fb == 'Arrivederci':
                print('Arduino: Arrivederci!')
                break
            else:
                print(f'\033[31mBye "{bye.strip()}" is not received correctly. Received "{fb}".\033[0m')
                break
        if time.time() - t_bye > time_out:
            print(f'\033[31mBye "{bye.strip()}" is not received correctly. Timeout. Please check the connection.\033[0m')
            break

def MatchTime(ser, t_send=20, time_out=0):
    t_timeout = time.time()
    if time_out <= t_send:
        time_out = t_send + 5
    t_sent = int(t_send * 1e3) # convert to milliseconds
    calibrate = f'calibrate_{t_sent}\n'
    ser.write(calibrate.encode('utf-8'))
    t1 = time.time()
    time.sleep(t_send - 2)
    while True:
        if ser.inWaiting() > 0:
            t2 = time.time()
            fb = ser.readline().decode('utf-8').strip()
            if fb.startswith('calibration'):
                # print(fb)
                t_feedback = t2 - t1
                break
            else:
                print(f'\033[31mTime is not calibrated correctly. Received "{fb}".\033[0m')
                break
        if time.time() - t_timeout > time_out:
            print(f'\033[31mTime is not calibrated correctly. Timeout. Please check the connection.\033[0m')
            break
    return t_feedback

def countdown_timer(total_time, step=1):
    """
    Countdown timer that runs for the specified total time.
    """
    for remaining in range(total_time, 0, -step):
        print(f"Time remaining: {remaining} seconds     ", end="\n")
        time.sleep(step)
    print("Time's up!                           ")

def CalibrateArduinoTime_v2(ser, duration=300, num_samples=30, use_countdown=True):
    '''
    Improved calibration using multi-timestamp method.
    
    This method is faster and more accurate than the original CalibrateArduinoTime:
    - Single calibration run instead of multiple separate measurements
    - Multiple data points for better statistical confidence
    - Removes per-message serial overhead for more accurate slope
    - Non-blocking Arduino implementation
    - Better quality diagnostics (RMSE, max error, stability detection)
    
    Args:
        ser: serial port object
        duration: Total calibration time in seconds (default: 300)
        num_samples: Number of timestamp samples to collect (default: 10)
        use_countdown: Show countdown timer (default: True)
    
    Returns:
        dict: Calibration results with quality metrics
            - calib_factor: Calibration factor (slope)
            - offset: Time offset in seconds
            - r_squared: R-squared goodness of fit
            - rmse: Root mean square error in seconds
            - max_error: Maximum absolute error in seconds
            - timing_stable: Boolean indicating if timing is stable
            - arduino_times: Array of Arduino-reported times
            - python_times: Array of Python-measured times
    '''
    print(f'Calibrating Arduino time (v2 - multi-timestamp method)...')
    print(f'Duration: {duration}s with {num_samples} samples')
    
    # Send calibration command
    command = f'calibrate_timestamps_{duration}_{num_samples}\n'
    ser.write(command.encode('utf-8'))
    
    # Wait for Arduino acknowledgment
    time.sleep(0.1)
    
    # Start countdown timer in separate thread if requested
    if use_countdown:
        timer_thread = threading.Thread(target=countdown_timer, args=(duration, 5))
        timer_thread.start()
    
    t_start_python = time.time()
    
    # Collect timestamp reports
    timestamps_arduino = []
    timestamps_python = []
    
    expected_reports = num_samples + 1  # Initial timestamp + N samples
    timeout = duration + 10  # Add 10 second buffer
    
    print(f'\nCollecting {expected_reports} timestamps...')
    
    for i in range(expected_reports):
        # Wait for data with timeout
        wait_start = time.time()
        while ser.inWaiting() == 0:
            if time.time() - wait_start > timeout:
                raise TimeoutError(f'Calibration timeout waiting for timestamp {i+1}/{expected_reports}')
            time.sleep(0.01)
        
        # Record Python time when data arrives
        t_python = time.time()
        response = ser.readline().decode('utf-8').strip()
        
        if response.startswith('calib_timestamp_'):
            # Parse Arduino timestamp
            arduino_ms = int(response.split('_')[2])
            timestamps_arduino.append(arduino_ms / 1000.0)  # Convert to seconds
            timestamps_python.append(t_python - t_start_python)
            
            if (i + 1) % 3 == 0 or i == 0:
                print(f'  Sample {i+1}/{expected_reports}: Arduino={arduino_ms}ms, Python={timestamps_python[-1]:.3f}s')
        else:
            print(f'\033[33mWarning: Unexpected response during calibration: "{response}"\033[0m')
    
    # Wait for countdown timer to finish
    if use_countdown:
        timer_thread.join()
    
    # Convert to numpy arrays for analysis
    arduino_times = np.array(timestamps_arduino)
    python_times = np.array(timestamps_python)
    
    # Linear regression: python_time = calib_factor * arduino_time + offset
    # This matches V1/V1.1 approach: fit Python (measured) time as function of Arduino time
    # The factor accounts for BOTH clock speed difference AND system overhead
    # - calib_factor > 1: System (Python) measures MORE time than Arduino reports → Arduino slow
    # - calib_factor < 1: System (Python) measures LESS time than Arduino reports → Arduino fast
    coefficients = np.polyfit(arduino_times, python_times, 1)
    calib_factor = coefficients[0]
    offset = coefficients[1]
    
    # Calculate quality metrics using the fitted relationship
    y_pred = calib_factor * arduino_times + offset
    residuals = python_times - y_pred
    
    # R-squared
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((python_times - np.mean(python_times)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
    
    # RMSE (Root Mean Square Error)
    rmse = np.sqrt(np.mean(residuals ** 2))
    
    # Maximum absolute error
    max_error = np.max(np.abs(residuals))
    
    # Timing stability check (max error should be < 500ms)
    timing_stable = max_error < 0.5
    
    # Print results
    print(f'\n{"="*70}')
    print(f'Calibration Results (v2):')
    print(f'{"="*70}')
    print(f'Calibration factor: {calib_factor:.6f}')
    
    # Interpret the calibration factor (same convention as V1/V1.1)
    # factor = python_time / arduino_time
    if calib_factor > 1:
        error_percent = (calib_factor - 1) * 100
        print(f'Arduino clock: {error_percent:.4f}% slower than real time')
    elif calib_factor < 1:
        error_percent = (1 - calib_factor) * 100
        print(f'Arduino clock: {error_percent:.4f}% faster than real time')
    else:
        print(f'Arduino clock: Perfect (no correction needed)')
    
    print(f'Time offset: {offset:.3f} seconds')
    print(f'R-squared: {r_squared:.6f}')
    print(f'RMSE: {rmse*1000:.2f} ms')
    print(f'Max error: {max_error*1000:.2f} ms')
    print(f'Timing stable: {"✓ Yes" if timing_stable else "✗ No (high jitter detected)"}')
    
    # Calculate timing drift per 12 hours
    # calib_factor = python/arduino, so (calib_factor - 1) gives drift rate
    time_drift_12h = (calib_factor - 1) * 12 * 3600
    if time_drift_12h > 0:
        print(f'Time drift: Arduino loses {time_drift_12h:.2f} seconds per 12 hours')
    elif time_drift_12h < 0:
        print(f'Time drift: Arduino gains {abs(time_drift_12h):.2f} seconds per 12 hours')
    else:
        print(f'Time drift: None (perfect clock)')
    print(f'{"="*70}')
    
    if not timing_stable:
        print(f'\033[33m⚠️  Warning: High timing jitter detected!')
        print(f'   Max error of {max_error*1000:.0f}ms exceeds 500ms threshold.')
        print(f'   Consider running calibration again or checking USB connection.\033[0m')
    
    return {
        'calib_factor': calib_factor,
        'offset': offset,
        'r_squared': r_squared,
        'rmse': rmse,
        'max_error': max_error,
        'timing_stable': timing_stable,
        'arduino_times': arduino_times,
        'python_times': python_times,
        'cost': offset  # For backward compatibility with old code
    }

def CalibrateArduinoTime(ser, t_send=None, use_v2=False):
    '''
    Calibrate the time of Arduino
    
    Args:
        ser: serial port
        t_send: list of time to send in seconds, default is [60, 80, 80, 80] (total: 300s)
        use_v2: Use improved v2 calibration method (default: False for backward compatibility)
    
    Returns:
        dict: Calibration results
            - calib_factor: Calibration factor
            - cost: Time offset
            - r_squared: R-squared goodness of fit
            - t_send: Array of sent times (v1 only)
            - t_feedback: Array of feedback times (v1 only)
    
    Note: Original implementation kept for backward compatibility.
          For new code, consider using CalibrateArduinoTime_v2() directly for better performance.
    '''
    # Use improved method if requested
    if use_v2:
        result = CalibrateArduinoTime_v2(ser, duration=300, num_samples=30)
        # Return dict compatible with old format
        return {
            'calib_factor': result['calib_factor'],
            'cost': result['offset'],
            'r_squared': result['r_squared'],
            't_send': result['arduino_times'],
            't_feedback': result['python_times']
        }
    
    # Original implementation below
    if t_send is None:
        t_send = [60, 70, 80, 90]
    elif type(t_send) is int:
        t_send = [t_send]
    
    if len(t_send) < 2:
        if t_send[0] != 40:
            t_send = [40] + t_send
    
    t_feedback = []
    t_sum = sum(t_send)
    print(f'Calibrating Arduino time.... Please wait for about {t_sum} seconds.')
    timer_thread = threading.Thread(target=countdown_timer, args=(t_sum,10,))
    timer_thread.start()
    for t in t_send:
        t_feedback_i = MatchTime(ser, t_send=t)
        t_feedback.append(t_feedback_i)
    timer_thread.join()

    # linear regression
    t_sent = np.array(t_send)
    t_feed = np.array(t_feedback)
    coefficients = np.polyfit(t_sent, t_feed, 1)
    linear_fit = np.poly1d(coefficients)
    
    # Calculate R-squared
    y_pred = linear_fit(t_send)
    ss_res = np.sum((t_feedback - y_pred) ** 2)
    ss_tot = np.sum((t_feedback - np.mean(t_feedback)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    kwargs_output = {'calib_factor': coefficients[0], 'cost': coefficients[1], 'r_squared': r_squared, 't_send': t_sent, 't_feedback': t_feed}
    
    return kwargs_output


def CalibrateArduinoTime_v11(ser, t_send=None, use_countdown=True):
    '''
    V1.1 calibration method: V1 logic with active wait instead of dead sleep
    
    This method uses the same Arduino-side logic as V1 (Arduino waits, Python measures),
    but Python actively polls for the response instead of using dead sleep.
    This provides better timing precision and more responsive response detection.
    
    Args:
        ser: Serial port connection
        t_send: List of time values to send in seconds (default: [60, 80, 80, 80] = 300s total)
        use_countdown: Show countdown timer during calibration (default: True)
    
    Returns:
        dict: Calibration results
            - calib_factor: Calibration factor (python_time / requested_time)
            - offset: Communication delay offset in seconds
            - r_squared: R-squared goodness of fit
            - measurements: List of individual measurement dicts
            - method: 'v1.1'
    
    Example:
        result = CalibrateArduinoTime_v11(ser, t_send=[60, 80, 80, 80])
        print(f"Calibration factor: {result['calib_factor']:.6f}")
    '''
    if t_send is None:
        t_send = [60, 70, 80, 90]
    elif isinstance(t_send, (int, float)):
        t_send = [t_send]
    
    if len(t_send) < 2:
        raise ValueError("At least 2 time values required for calibration")
    
    t_sum = sum(t_send)
    print(f'\n{"="*70}')
    print(f'V1.1 CALIBRATION (Active Wait Method)')
    print(f'{"="*70}')
    print(f'Test duration: {t_sum} seconds')
    print(f'Arduino waits using millis(), Python actively monitors for response')
    print(f'Linear regression accounts for communication delay')
    print(f'\n{"Requested":<12} {"Arduino":<12} {"Python":<12} {"Py-Ard":<12}')
    print(f'{"(seconds)":<12} {"(seconds)":<12} {"(seconds)":<12} {"(seconds)":<12}')
    print(f'{"-"*50}')
    
    # Start countdown timer if enabled
    if use_countdown:
        timer_thread = threading.Thread(target=countdown_timer, args=(t_sum, 10,))
        timer_thread.start()
    
    measurements = []
    requested_times = []
    python_times = []
    
    import_time = time.time()
    
    for t_requested in t_send:
        # Send V1.1 command: calibrate_v11_XXXXX (in milliseconds)
        command = f'calibrate_v11_{int(t_requested * 1000)}\n'
        ser.write(command.encode('utf-8'))
        ser.flush()
        
        # Measure real elapsed time - active wait (no dead sleep)
        t_start = time.time()
        
        # Actively wait for response
        timeout_start = time.time()
        arduino_elapsed = None
        
        while True:
            if ser.inWaiting() > 0:
                t_end = time.time()
                response = ser.readline().decode('utf-8').strip()
                # Response format: calibration_v11_XXXXX
                if response.startswith('calibration_v11_'):
                    arduino_ms = int(response.split('_')[2])
                    arduino_elapsed = arduino_ms / 1000.0
                    break
            
            if time.time() - timeout_start > t_requested + 5:
                print(f"Timeout waiting for {t_requested}s response")
                t_end = time.time()
                break
            
            time.sleep(0.001)  # Minimal sleep to prevent CPU overload
        
        python_elapsed = t_end - t_start
        
        if arduino_elapsed:
            diff_py_ard = python_elapsed - arduino_elapsed
            print(f'{t_requested:<12.1f} {arduino_elapsed:<12.6f} {python_elapsed:<12.6f} {diff_py_ard:<12.6f}')
            
            measurements.append({
                'requested': t_requested,
                'arduino': arduino_elapsed,
                'python': python_elapsed,
                'diff_py_ard': diff_py_ard
            })
            requested_times.append(t_requested)
            python_times.append(python_elapsed)
        else:
            print(f'{t_requested:<12.1f} {"N/A":<12} {python_elapsed:<12.6f} {"N/A":<12}')
        
        time.sleep(0.5)  # Small delay between tests
    
    if use_countdown:
        timer_thread.join()
    
    # Linear regression: python_time = factor × requested_time + offset
    if len(requested_times) >= 2:
        requested = np.array(requested_times)
        python = np.array(python_times)
        
        coefficients = np.polyfit(requested, python, 1)
        calib_factor = coefficients[0]
        offset = coefficients[1]
        
        # Calculate R-squared
        y_pred = calib_factor * requested + offset
        ss_res = np.sum((python - y_pred) ** 2)
        ss_tot = np.sum((python - np.mean(python)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
        
        print(f'\n{"V1.1 Analysis:":<30}')
        print(f'  {"Calibration factor:":<30} {calib_factor:.6f}')
        print(f'  {"Communication offset:":<30} {offset:.6f}s')
        print(f'  {"R-squared:":<30} {r_squared:.6f}')
        print(f'  {"Method:":<30} V1.1 (Active Wait)')
        
        return {
            'calib_factor': calib_factor,
            'offset': offset,
            'r_squared': r_squared,
            'measurements': measurements,
            'method': 'v1.1',
            'requested_times': requested,
            'python_times': python
        }
    else:
        raise ValueError("Not enough valid measurements for calibration")


def CalibrateArduinoTime_v2_improved(ser, duration=180, num_samples=9, use_countdown=True):
    '''
    V2 calibration method (improved): Multi-timestamp approach with Python vs Arduino timing
    
    This method has Arduino send periodic timestamps while Python records their arrival times.
    It fits python_time vs arduino_time to account for both Arduino clock speed AND
    communication delays. More accurate than V1 due to more data points and better
    separation of clock drift from communication delay.
    
    Args:
        ser: Serial port connection
        duration: Total calibration duration in seconds (default: 300)
        num_samples: Number of timestamp samples excluding t=0 (default: 9, giving ~33s intervals for 300s)
        use_countdown: Show countdown timer during calibration (default: True)
    
    Returns:
        dict: Calibration results
            - calib_factor: Calibration factor (python_time / arduino_time)
            - offset: Communication delay offset in seconds
            - r_squared: R-squared goodness of fit
            - arduino_times: Array of Arduino timestamps (seconds)
            - python_times: Array of Python timestamps (seconds)
            - method: 'v2_improved'
            - samples_used: Number of samples used (excludes t=0)
    
    Example:
        result = CalibrateArduinoTime_v2_improved(ser, duration=300, num_samples=9)
        print(f"Calibration factor: {result['calib_factor']:.6f}")
    '''
    print(f'\n{"="*70}')
    print(f'V2 CALIBRATION (Multi-Timestamp Method - Improved)')
    print(f'{"="*70}')
    print(f'Test duration: {duration} seconds with {num_samples+1} samples')
    print(f'V2: Arduino sends timestamps, Python records when they arrive')
    print(f'Fitting python vs arduino accounts for clock speed + communication')
    
    # Send V2 command
    command = f'calibrate_timestamps_{duration}_{num_samples}\n'
    print(f'Sending: {command.strip()}')
    
    ser.write(command.encode('utf-8'))
    time.sleep(0.1)
    
    # Start countdown timer if enabled
    if use_countdown:
        timer_thread = threading.Thread(target=countdown_timer, args=(duration, 10,))
        timer_thread.start()
    
    t_start_python = time.time()
    
    print(f'\n{"#":<5} {"Arduino Time":<15} {"Python Time":<15} {"Difference":<12}')
    print(f'{"":5} {"(seconds)":<15} {"(seconds)":<15} {"(Py - Ard)":<12}')
    print(f'{"-"*52}')
    
    results = []
    expected_samples = num_samples + 1  # Including initial timestamp at 0
    
    print(f'Collecting {expected_samples} timestamps over {duration} seconds...')
    
    for i in range(expected_samples):
        timeout_start = time.time()
        while ser.inWaiting() == 0:
            if time.time() - timeout_start > duration + 5:
                print(f"Timeout waiting for sample {i+1}/{expected_samples}")
                break
            time.sleep(0.01)
        
        if ser.inWaiting() > 0:
            t_arrival = time.time()
            response = ser.readline().decode('utf-8').strip()
            
            # Response format: calib_timestamp_XXXXX
            if response.startswith('calib_timestamp_'):
                arduino_ms = int(response.split('_')[2])
                arduino_s = arduino_ms / 1000.0
                python_s = t_arrival - t_start_python
                diff = python_s - arduino_s
                
                print(f'{i+1:<5} {arduino_s:<15.6f} {python_s:<15.6f} {diff:<12.6f}')
                
                results.append({
                    'arduino': arduino_s,
                    'python': python_s,
                    'diff': diff
                })
    
    if use_countdown:
        timer_thread.join()
    
    # Calculate calibration factor (excluding t=0)
    if len(results) >= 2:
        # Skip first data point (t=0) as it has initialization overhead
        results_for_calib = results[1:] if len(results) > 1 else results
        
        arduino = np.array([r['arduino'] for r in results_for_calib])
        python = np.array([r['python'] for r in results_for_calib])
        diffs = np.array([r['diff'] for r in results_for_calib])
        
        # Fit python vs arduino: python_time = factor × arduino_time + offset
        coefficients = np.polyfit(arduino, python, 1)
        calib_factor = coefficients[0]
        offset = coefficients[1]
        
        # Calculate R-squared
        y_pred = calib_factor * arduino + offset
        ss_res = np.sum((python - y_pred) ** 2)
        ss_tot = np.sum((python - np.mean(python)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
        
        avg_diff = np.mean(diffs)
        std_diff = np.std(diffs)
        
        print(f'\n{"V2 Analysis:":<30}')
        print(f'  {"Data points collected:":<30} {len(results)}')
        print(f'  {"Used for calibration:":<30} {len(results_for_calib)} (excluding t=0)')
        print(f'  {"Avg diff (Py-Ard):":<30} {avg_diff:.6f}s')
        print(f'  {"Std deviation:":<30} {std_diff:.6f}s')
        print(f'  {"Calibration factor:":<30} {calib_factor:.6f}')
        print(f'  {"Communication offset:":<30} {offset:.6f}s')
        print(f'  {"R-squared:":<30} {r_squared:.6f}')
        print(f'  {"Method:":<30} V2 (Multi-Timestamp, Improved)')
        print(f'  {"Note:":<30} Excludes t=0 to avoid initialization overhead')
        
        return {
            'calib_factor': calib_factor,
            'offset': offset,
            'r_squared': r_squared,
            'arduino_times': arduino,
            'python_times': python,
            'method': 'v2_improved',
            'samples_used': len(results_for_calib),
            'all_results': results
        }
    else:
        raise ValueError("Not enough valid measurements for calibration")


def auto_calibrate_arduino(ser, method='v2', force_recalibrate=False, db_path='calibration_database.json'):
    """
    Automatically manage Arduino calibration with database storage.
    
    This function:
    1. Checks if calibration exists for this Arduino
    2. Checks if calibration is expired (>90 days old)
    3. If valid and not forced, uses stored calibration
    4. If expired, not exists, or forced, performs new calibration
    5. Saves new calibration to database with timestamp
    
    Calibrations expire after 90 days (3 months) due to:
    - Crystal oscillator aging (±1-5 ppm/year)
    - Temperature-dependent drift accumulation
    - Component aging effects
    
    Args:
        ser: Serial connection object
        method: Calibration method to use ('v1', 'v1.1', 'v2', 'v2_improved')
        force_recalibrate: Force new calibration even if one exists (default: False)
        db_path: Path to calibration database file
        
    Returns:
        float: Calibration factor to use
        dict: Full calibration results
    """
    # Check for existing calibration (automatically checks expiration)
    existing_calib = None
    if not force_recalibrate:
        existing_calib = get_calibration_for_arduino(ser, db_path)
        # Note: get_calibration_for_arduino returns None if calibration is expired
    
    if existing_calib and not force_recalibrate:
        # Valid calibration found (< 90 days old)
        response = input('\nUse existing calibration? (Y/n/recalibrate): ').strip().lower()
        
        if response == 'recalibrate' or response == 'r':
            print('\nPerforming new calibration...')
            existing_calib = None
        elif response == 'n' or response == 'no':
            print('\nCalibration skipped. Using default factor 1.0')
            return 1.0, {'calib_factor': 1.0, 'method': 'default'}
        else:
            # Use existing
            print(f'\n✓ Using stored calibration factor: {existing_calib["calib_factor"]:.6f}')
            return existing_calib['calib_factor'], existing_calib
    
    # Perform new calibration (expired, doesn't exist, or force_recalibrate=True)
    print(f'\n{"="*70}')
    print(f'Performing Calibration (Method: {method.upper()})')
    print(f'{"="*70}\n')
    
    if method == 'v1':
        result = CalibrateArduinoTime(ser, use_v2=False)
    elif method == 'v1.1':
        result = CalibrateArduinoTime_v11(ser)
    elif method == 'v2':
        result = CalibrateArduinoTime_v2(ser, duration=300, num_samples=10)
    elif method == 'v2_improved':
        result = CalibrateArduinoTime_v2_improved(ser, duration=300, num_samples=9)
    else:
        raise ValueError(f'Unknown calibration method: {method}. Use v1, v1.1, v2, or v2_improved')
    
    # Save to database
    save_calibration_for_arduino(ser, result, method, db_path)
    
    return result['calib_factor'], result


def CorrectTime_df(df_ms, calib_factor):
    df_corrected = df_ms.copy()
    for col in df_corrected.columns:
        if col.endswith('_time_ms'):
            df_corrected[col] = df_corrected[col] / calib_factor
    df_corrected = df_corrected.fillna(0)
    
    # Convert columns to appropriate types (all integers now - no more floats)
    for col in df_corrected.columns[1:]:
        df_corrected[col] = df_corrected[col].astype(int)
    return df_corrected

def CorrectTime_dict(remaining_time, calib_factor):
    remaining_time_corrected = dict()
    for ch, t in remaining_time.items():
        remaining_time_corrected[ch] = int(t / calib_factor)
    return remaining_time_corrected

def CorrectTime(dataIn, calib_factor=1):
    if type(dataIn) is pd.DataFrame:
        return CorrectTime_df(dataIn, calib_factor)
    elif type(dataIn) is dict:
        return CorrectTime_dict(dataIn, calib_factor)
    else:
        raise ValueError('Input data type is not recognized. Please use pandas DataFrame or dictionary.')

def FindRepeatedPatterns(df_ms, pattern_length=2):
    """
    Find and compress repeated patterns across status, time_ms, period and pulse_width for all channels.
    
    Each channel has columns: CH[n]_status, CH[n]_time_ms, and optionally CH[n]_period and CH[n]_pulse_width.
    The status can be 0 or 1, time_ms is the time in milliseconds.
    Period is in milliseconds, pulse_width is in milliseconds.
    
    :param df_ms: pandas DataFrame containing the protocol data
    :param pattern_length: the length of the pattern to search for
    :return: a dictionary with channel names as keys and their compressed patterns as values
    """
    compressed_patterns = {}
    
    # Detect how many channels we have
    # Check for both old format (status, time_ms) and new format (status, time_ms, period, pulse_width)
    channel_cols = [col for col in df_ms.columns if col.startswith('CH') and col.endswith('_status')]
    num_channels = len(channel_cols)
    
    for n in range(1, num_channels + 1):
        status_col = f'CH{n}_status'
        time_col = f'CH{n}_time_ms'
        period_col = f'CH{n}_period'
        pw_col = f'CH{n}_pulse_width'
        
        status_data = df_ms[status_col].tolist()
        time_data = df_ms[time_col].tolist()
        
        # Check if period and pulse_width columns exist
        has_pulse_cols = period_col in df_ms.columns and pw_col in df_ms.columns
        
        if has_pulse_cols:
            period_data = df_ms[period_col].tolist()
            pw_data = df_ms[pw_col].tolist()
            
            # Validate pulse data consistency
            for idx, (period, pw) in enumerate(zip(period_data, pw_data)):
                # Convert NaN to 0 for easier checking
                period_val = 0 if pd.isna(period) else period
                pw_val = 0 if pd.isna(pw) else pw
                
                # Skip if both are 0 (valid: no pulsing)
                if period_val == 0 and pw_val == 0:
                    continue
                    
                # Check for inconsistent values (one specified, other not)
                if period_val > 0 and pw_val == 0:
                    raise ValueError(
                        f"Invalid pulse data in {period_col} row {idx+2}: "
                        f"period={period_val} ms but pulse_width is 0 or empty. "
                        f"Both period and pulse_width must be specified for pulsing, "
                        f"or both should be 0 for no pulsing."
                    )
                if period_val == 0 and pw_val > 0:
                    raise ValueError(
                        f"Invalid pulse data in {period_col} row {idx+2}: "
                        f"pulse_width={pw_val} ms but period is 0 or empty. "
                        f"Both period and pulse_width must be specified for pulsing, "
                        f"or both should be 0 for no pulsing."
                    )
            
            # Combine status, time, period, and pulse_width into tuples
            combined = list(zip(status_data, time_data, period_data, pw_data))
        else:
            # Combine status and time into tuples (old format)
            combined = list(zip(status_data, time_data))
        
        patterns = []
        i = 0
        while i < len(combined):
            # Extract the current pattern
            current_pattern = tuple(combined[i:i + pattern_length])
            count = 1
            j = i + pattern_length
            # Check for consecutive repeats of the current pattern
            while j + pattern_length <= len(combined) and tuple(combined[j:j + pattern_length]) == current_pattern:
                count += 1
                j += pattern_length
            patterns.append({'pattern': current_pattern, 'repeats': count})
            i = j
        compressed_patterns[f'CH{n}'] = patterns
    
    return compressed_patterns

def GeneratePatternCommands(compressed_patterns):
    '''
    Generate string commands from compressed patterns
    compressed_patterns: Dictionary containing compressed patterns for each channel, generated by FindRepeatedPatterns()
    '''
    commands = []
    for channel_name, patterns in compressed_patterns.items():
        # Extract channel number from the channel name (e.g., 'CH1' -> 1)
        channel_num = int(channel_name.replace('CH', ''))
        for i, pattern in enumerate(patterns):
            # Check if pattern contains pulse info (tuple of 4 elements) or old format (tuple of 2 elements)
            if len(pattern['pattern'][0]) == 4:
                # New format with pulse: (status, time, period, pw)
                status_values = [str(s) for s, t, T, pw in pattern['pattern']]
                time_values = [str(t) for s, t, T, pw in pattern['pattern']]
                period_values = [T for s, t, T, pw in pattern['pattern']]
                pw_values = [pw for s, t, T, pw in pattern['pattern']]
                
                # Check if any non-zero pulse values exist (treat None, NaN, and 0 as no pulse)
                has_pulse = any(
                    (T is not None and T != 0 and not (isinstance(T, float) and T != T)) or 
                    (pw is not None and pw != 0)
                    for T, pw in zip(period_values, pw_values)
                )
                
                # if the status_values are all 0, time_values are all 0, skip
                if all([s == '0' for s in status_values]) and all([t == '0' for t in time_values]):
                    continue
                
                # Build pulse string if needed
                pulse_str = ""
                if has_pulse:
                    pulse_parts = []
                    for period, pw in zip(period_values, pw_values):
                        # Handle None, NaN, and convert to 0
                        period_val = 0 if (period is None or (isinstance(period, float) and period != period)) else period
                        pw_val = 0 if pw is None else pw
                        pulse_parts.append(f"T{period_val}pw{pw_val}")
                    pulse_str = f";PULSE:{','.join(pulse_parts)},"
                
                # Construct the command string
                cmd_t = \
                    f"PATTERN:{i+1};CH:{channel_num};STATUS:{','.join(status_values)};" \
                    f"TIME_MS:{','.join(time_values)};REPEATS:{pattern['repeats']}{pulse_str}\n"
                commands.append(cmd_t)
            else:
                # Old format without pulse: (status, time)
                status_values = [str(s) for s, t in pattern['pattern']]
                time_values = [str(t) for s, t in pattern['pattern']]
                repeats = pattern['repeats']
                # if the status_values are all 0, time_values are all 0, skip
                if all([s == '0' for s in status_values]) and all([t == '0' for t in time_values]):
                    continue
                # Construct the command string
                cmd_t = \
                    f"PATTERN:{i+1};CH:{channel_num};STATUS:{','.join(status_values)};" \
                    f"TIME_MS:{','.join(time_values)};REPEATS:{repeats}\n"
                commands.append(cmd_t)
    return commands

def GenerateWaitCommands(wait_status, remaining_time, valid_channels, wait_pulse=None):
    '''
    Generate string commands for waiting for each channel to start.
    Now uses pattern_length=1 format (single state) instead of dummy second state.
    
    wait_status: Dictionary containing wait status for each channel
    remaining_time: Dictionary containing remaining time for each channel to start in milliseconds
    valid_channels: List of valid channel names
    wait_pulse: Optional dictionary containing pulse parameters for wait period
                Format: {channel_name: {'period': int, 'pw': int}}
                Example: {'CH1': {'period': 2000, 'pw': 100}}
    return -> List of string commands, one for each channel
    for example: ['PATTERN:0;CH:1;STATUS:1;TIME_MS:1000;REPEATS:1;PULSE:T2000pw100\n', ...]
    '''
    commands = []
    for channel_name in valid_channels:
        channel_num = int(channel_name.replace('CH', ''))
        status = wait_status[channel_name]
        if status is None:
            continue
        
        # Build command with pattern_length=1 (single state)
        cmd_t = \
            f"PATTERN:0;CH:{channel_num};STATUS:{status};" \
            f"TIME_MS:{remaining_time[channel_name]};REPEATS:1"
        
        # Add PULSE parameter if provided for this channel
        if wait_pulse and channel_name in wait_pulse:
            pulse_info = wait_pulse[channel_name]
            period = pulse_info.get('period', 0)
            pw = pulse_info.get('pw', 0)
            cmd_t += f";PULSE:T{period}pw{pw},"
        
        cmd_t += "\n"
        commands.append(cmd_t)
    return commands

def AddCommandDescriptions(commands, protocol_info=None):
    """
    Add descriptive comments after each command line.
    
    Args:
        commands: List of command strings
        protocol_info: Optional dict with metadata like:
            - 'protocol_file': Original protocol filename
            - 'parse_time': Time taken to parse protocol
            - 'total_channels': Number of channels
            - 'calib_factor': Calibration factor
            - 'start_time': Start time info
            
    Returns:
        List of command strings with comments appended
    """
    commented_commands = []
    
    for cmd in commands:
        cmd = cmd.rstrip('\n')  # Remove trailing newline
        
        # Parse command to extract information
        parts = cmd.split(';')
        comment_parts = []
        
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                
                if key == 'PATTERN':
                    if value == '0':
                        comment_parts.append('Wait pattern')
                    else:
                        comment_parts.append(f'Pattern #{value}')
                        
                elif key == 'CH':
                    comment_parts.append(f'Channel {value}')
                    
                elif key == 'STATUS':
                    statuses = value.split(',')
                    if len(statuses) == 1:
                        comment_parts.append(f'Status: {statuses[0]}')
                    else:
                        comment_parts.append(f'Status: {" → ".join(statuses)}')
                        
                elif key == 'TIME_MS':
                    times = value.split(',')
                    time_strs = []
                    for t in times:
                        t_val = int(t)
                        if t_val == 0:
                            time_strs.append('0ms')
                        elif t_val < 1000:
                            time_strs.append(f'{t_val}ms')
                        elif t_val < 60000:
                            time_strs.append(f'{t_val/1000:.1f}s')
                        elif t_val < 3600000:
                            time_strs.append(f'{t_val/60000:.1f}min')
                        else:
                            time_strs.append(f'{t_val/3600000:.1f}hr')
                    comment_parts.append(f'Time: {" → ".join(time_strs)}')
                    
                elif key == 'REPEATS':
                    if value == '1':
                        comment_parts.append('1 cycle')
                    else:
                        comment_parts.append(f'{value} cycles')
                        
                elif key == 'PULSE':
                    pulses = value.split(',')
                    pulse_strs = []
                    for pulse in pulses:
                        if 'T' in pulse and 'pw' in pulse:
                            # Parse T[period]pw[width]
                            match = re.match(r'T(\d+)pw(\d+)', pulse)
                            if match:
                                period_ms = int(match.group(1))
                                pw_ms = int(match.group(2))
                                if period_ms == 0 and pw_ms == 0:
                                    pulse_strs.append('No pulse')
                                else:
                                    freq_hz = 1000.0 / period_ms if period_ms > 0 else 0
                                    duty_pct = (pw_ms / period_ms * 100) if period_ms > 0 else 0
                                    pulse_strs.append(f'{freq_hz:.2f}Hz DC={duty_pct:.1f}%')
                    if pulse_strs:
                        comment_parts.append(f'Pulse: {" → ".join(pulse_strs)}')
        
        # Combine command with comment
        comment = ' # ' + ', '.join(comment_parts)
        commented_commands.append(cmd + comment + '\n')
    
    return commented_commands

def ReadExcelFile(file_path):
    '''
    Read the protocol file in Excel format
    file_path: path to the Excel file
    return -> pandas DataFrame
    
    Automatically detects start_time sheet format:
    - Row-based (original): Uses index_col=0 to set first column as row names
    - Column-based (new): Uses index_col=None to keep all columns including 'Channels'
    
    Empty columns in protocol sheet are automatically removed, including:
    - Completely empty columns (all NaN values)
    - Unnamed columns (Unnamed: X)
    - Columns with whitespace-only names
    - Columns with only whitespace data
    '''
    excel_file = pd.ExcelFile(file_path)
    sheet_names = excel_file.sheet_names
    if 'protocol' in sheet_names:
        df_protocol = excel_file.parse('protocol', header=0, index_col=None)
        
        # Track original column count for reporting
        initial_cols = len(df_protocol.columns)
        columns_to_drop = []
        
        for col in df_protocol.columns:
            col_str = str(col)
            
            # Check 1: Completely empty column (all NaN)
            if df_protocol[col].isna().all():
                columns_to_drop.append(col)
                continue
            
            # Check 2: Unnamed columns created by pandas (e.g., "Unnamed: 5")
            if col_str.startswith('Unnamed:'):
                columns_to_drop.append(col)
                continue
            
            # Check 3: Column name is whitespace-only or empty string
            if col_str.strip() == '':
                columns_to_drop.append(col)
                continue
            
            # Check 4: Column contains only whitespace values (no actual data)
            # Convert to string and check if all non-NaN values are whitespace
            non_nan_values = df_protocol[col].dropna()
            if len(non_nan_values) > 0:
                # Check if all non-NaN values are whitespace when converted to string
                if all(str(val).strip() == '' for val in non_nan_values):
                    columns_to_drop.append(col)
                    continue
        
        # Remove identified columns
        if columns_to_drop:
            df_protocol = df_protocol.drop(columns=columns_to_drop)
            removed_cols = len(columns_to_drop)
            print(f'Removed {removed_cols} empty/invalid column(s) from protocol sheet:')
            for col in columns_to_drop:
                col_type = 'unnamed' if str(col).startswith('Unnamed:') else 'empty'
                print(f'  - {col} ({col_type})')
        
    else:
        raise ValueError('Sheet "protocol" is not found in the Excel file.')
    if 'start_time' in sheet_names:
        # First, read without index_col to detect format
        df_startTime_test = excel_file.parse('start_time', header=0, index_col=None)
        
        # Detect format by checking column names
        columns_lower = [str(col).lower().replace('_', '').replace(' ', '') for col in df_startTime_test.columns]
        has_channels_col = any(col == 'channels' for col in columns_lower)
        has_starttime_col = any(col in ['starttime', 'start'] for col in columns_lower)
        has_waitstatus_col = any(col in ['waitstatus', 'wait'] for col in columns_lower)
        
        if has_channels_col and has_starttime_col and has_waitstatus_col:
            # Column-based format: keep all columns
            df_startTime = df_startTime_test
        else:
            # Row-based format: use first column as index
            df_startTime = excel_file.parse('start_time', header=0, index_col=0)
    else:
        raise ValueError('Sheet "start_time" is not found in the Excel file.')
    if 'calibration' in sheet_names:
        df_calibration = excel_file.parse('calibration', header=0, index_col=None)
        if df_calibration.shape[0] > 1:
            raise ValueError('The calibration sheet should have only one row.')
        elif df_calibration.shape[0] == 1:
            calib_factor = df_calibration.iloc[0, 0]
            if pd.isna(calib_factor):
                calib_factor = None
            elif calib_factor <= 0:
                raise ValueError('Calibration factor should be positive.')
        else:
            calib_factor = None
    else:
        calib_factor = None
    if calib_factor is not None:
        print(f'Read calibration factor: {calib_factor}')
    return df_protocol, df_startTime, calib_factor

def ReadTxtFile(file_path):
    '''
    Read the protocol file in TXT format
    file_path: path to the TXT file
    return -> list of pattern commands, start_time dict, wait_status dict, wait_pulse dict, calibration factor
    
    Commands can include PULSE parameter in format: PULSE:T[period]pw[width],T[period]pw[width]
    Period is in milliseconds, pulse_width is in milliseconds.
    Example: PATTERN:1;CH:1;STATUS:0,1;TIME_MS:10000,10000;REPEATS:4;PULSE:T1000pw50,T1000pw50
    
    TXT file can include:
    - PATTERN: commands with optional PULSE parameter
    - START_TIME: dictionary {channel_name: time_value or countdown_seconds}
    - WAIT_STATUS: dictionary {channel_name: 0 or 1}
    - WAIT_PULSE: dictionary {channel_name: {'period': int, 'pw': int}}
    - CALIBRATION_FACTOR: float value
    - Comments: lines starting with # are ignored
    - Empty lines are ignored
    '''
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    pattern_commands = []
    start_time = {}
    wait_status = {}
    wait_pulse = {}
    calib_factor = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines and comments (lines starting with #)
        if not line or line.startswith('#'):
            i += 1
            continue
        
        # For PATTERN lines, remove spaces and validate
        if line.startswith('PATTERN:'):
            line_no_space = line.replace(' ', '')
            # Validate PULSE format if present
            try:
                ValidatePulseFormat(line_no_space, line_num=i+1)
            except ValueError as e:
                raise ValueError(f"Error in file at line {i+1}:\n{str(e)}")
            pattern_commands.append(line_no_space + '\n')
            i += 1
        elif line.startswith('START_TIME:'):
            # Collect all lines until we have a complete dictionary
            start_time_lines = []
            start_time_lines.append(line)
            i += 1
            # Check if the dictionary is complete
            complete = line.count('{') == line.count('}')
            while i < len(lines) and not complete:
                start_time_lines.append(lines[i])
                complete = ''.join(start_time_lines).count('{') == ''.join(start_time_lines).count('}')
                i += 1
            
            # Parse the complete START_TIME
            start_time_str = ''.join(start_time_lines)
            start_time_str = start_time_str.split('START_TIME:', 1)[1].strip()
            
            try:
                start_time_dict = ast.literal_eval(start_time_str)
                for ch, time_value in start_time_dict.items():
                    if time_value is None or (isinstance(time_value, str) and not time_value):
                        start_time[ch] = None
                    elif isinstance(time_value, (int, float)):
                        # Numeric value represents countdown in seconds
                        start_time[ch] = time_value
                    else:
                        # String value, parse as datetime
                        start_time[ch] = str2datetime(time_value)
            except (ValueError, SyntaxError) as e:
                print(f"Warning: Could not parse START_TIME: {e}")
                print(f"START_TIME string: {start_time_str}")
        elif line.startswith('WAIT_STATUS:'):
            # Collect all lines until we have a complete dictionary
            wait_status_lines = []
            wait_status_lines.append(line)
            i += 1
            # Check if the dictionary is complete
            complete = line.count('{') == line.count('}')
            while i < len(lines) and not complete:
                wait_status_lines.append(lines[i])
                complete = ''.join(wait_status_lines).count('{') == ''.join(wait_status_lines).count('}')
                i += 1
            
            # Parse the complete WAIT_STATUS
            wait_status_str = ''.join(wait_status_lines)
            wait_status_str = wait_status_str.split('WAIT_STATUS:', 1)[1].strip()
            
            try:
                wait_status_dict = ast.literal_eval(wait_status_str)
                for ch, status_value in wait_status_dict.items():
                    if status_value is None:
                        wait_status[ch] = None
                    else:
                        wait_status[ch] = int(bool(status_value))
            except (ValueError, SyntaxError) as e:
                print(f"Warning: Could not parse WAIT_STATUS: {e}")
                print(f"WAIT_STATUS string: {wait_status_str}")
        elif line.startswith('WAIT_PULSE:'):
            # Collect all lines until we have a complete dictionary
            wait_pulse_lines = []
            wait_pulse_lines.append(line)
            i += 1
            # Check if the dictionary is complete
            complete = line.count('{') == line.count('}')
            while i < len(lines) and not complete:
                wait_pulse_lines.append(lines[i])
                complete = ''.join(wait_pulse_lines).count('{') == ''.join(wait_pulse_lines).count('}')
                i += 1
            
            # Parse the complete WAIT_PULSE
            wait_pulse_str = ''.join(wait_pulse_lines)
            wait_pulse_str = wait_pulse_str.split('WAIT_PULSE:', 1)[1].strip()
            
            try:
                wait_pulse_dict = ast.literal_eval(wait_pulse_str)
                for ch, pulse_info in wait_pulse_dict.items():
                    if pulse_info is None:
                        wait_pulse[ch] = None
                    elif isinstance(pulse_info, dict):
                        # Validate pulse_info has period and pw
                        if 'period' in pulse_info and 'pw' in pulse_info:
                            wait_pulse[ch] = {
                                'period': int(pulse_info['period']),
                                'pw': int(pulse_info['pw'])
                            }
                        else:
                            print(f"Warning: Invalid WAIT_PULSE format for {ch}. Expected dict with 'period' and 'pw'.")
                    else:
                        print(f"Warning: Invalid WAIT_PULSE format for {ch}. Expected dict or None.")
            except (ValueError, SyntaxError) as e:
                print(f"Warning: Could not parse WAIT_PULSE: {e}")
                print(f"WAIT_PULSE string: {wait_pulse_str}")
        elif line.startswith('CALIBRATION_FACTOR:'):
            # Remove spaces for parsing
            line_no_space = line.replace(' ', '')
            calib_str = line_no_space.split('CALIBRATION_FACTOR:', 1)[1].strip()
            # Handle empty or whitespace-only calibration factor
            if calib_str:
                try:
                    calib_factor = float(calib_str)
                    # Warn user about outdated practice of manual CALIBRATION_FACTOR
                    print("\n" + "="*80)
                    print("⚠️  OUTDATED PRACTICE DETECTED: Manual CALIBRATION_FACTOR in protocol file")
                    print("="*80)
                    print(f"Found: CALIBRATION_FACTOR: {calib_factor}")
                    print("\nThis protocol file uses the old manual calibration approach.")
                    print("While this still works (backward compatible), consider upgrading to")
                    print("automatic calibration for easier management:\n")
                    print("BENEFITS OF AUTOMATIC CALIBRATION:")
                    print("  • No manual calibration factor management")
                    print("  • Automatic board identification (serial number/VID/PID)")
                    print("  • Per-board calibration storage in database")
                    print("  • Seamless multi-board support")
                    print("  • Eliminates manual tracking errors\n")
                    print("TO UPGRADE:")
                    print("  1. Remove the CALIBRATION_FACTOR line from this protocol file")
                    print("  2. Run the protocol - you'll be prompted to calibrate once")
                    print("  3. Calibration is saved automatically for future use\n")
                    print("DOCUMENTATION:")
                    print("  • Auto-calibration: docs/AUTO_CALIBRATION_DATABASE.md")
                    print("  • Backward compatibility: docs/BACKWARD_COMPATIBILITY.md")
                    print("  • Examples: examples/auto_calibration/")
                    print("="*80 + "\n")
                except ValueError:
                    print(f"Warning: Invalid CALIBRATION_FACTOR value '{calib_str}'. Will calibrate automatically.")
                    calib_factor = None
            else:
                calib_factor = None
            i += 1
        else:
            i += 1
    
    # If wait_status was not explicitly provided, try to extract from PATTERN:0 commands
    if not wait_status:
        for cmd in pattern_commands:
            if 'PATTERN:0;' in cmd:
                # Parse channel number
                ch_match = re.search(r'CH:(\d+)', cmd)
                status_match = re.search(r'STATUS:(\d+),', cmd)
                if ch_match and status_match:
                    ch_num = int(ch_match.group(1))
                    ch_name = f'CH{ch_num}'
                    wait_status[ch_name] = int(status_match.group(1))
    
    # If wait_status is still empty, set it based on start_time with default value of 0
    if not wait_status:
        for ch in start_time.keys():
            wait_status[ch] = 0  # Default wait status
    
    return pattern_commands, start_time, wait_status, wait_pulse, calib_factor

def ValidatePulseFormat(cmd_string, line_num=None):
    '''
    Validate PULSE parameter format in a command string
    Raises ValueError if format is invalid (helps catch typos)
    Allows empty/missing PULSE parameter
    
    Format: PULSE:T[period]pw[width],T[period]pw[width]
    Where period and pulse_width are integers in milliseconds
    '''
    pulse_match = re.search(r'PULSE:([\w.,]*)', cmd_string)
    if not pulse_match:
        # No PULSE parameter - this is fine (backward compatible)
        return True
    
    pulse_str = pulse_match.group(1).strip()
    if not pulse_str:
        # Empty PULSE parameter (e.g., "PULSE:" or "PULSE:;") - this is fine
        return True
    
    # Parse individual pulse items
    pulse_items = pulse_str.split(',')
    for i, item in enumerate(pulse_items):
        item = item.strip()
        if not item:
            # Empty item (e.g., trailing comma) - this is fine
            continue
        
        # Check format: must be T[number]pw[number]
        if not re.match(r'^T[\d]+pw[\d]+$', item):
            location = f" (line {line_num})" if line_num else ""
            raise ValueError(
                f"Invalid PULSE format{location}: '{item}'\n"
                f"Expected format: T[period]pw[pulse_width]\n"
                f"Examples: T1000pw50, T500pw100, T2000pw200\n"
                f"  - period: integer in milliseconds (e.g., 1000, 500, 2000)\n"
                f"  - pulse_width: integer in milliseconds (e.g., 50, 100)\n"
                f"Full command: {cmd_string.strip()}"
            )
    
    return True

def ConvertTimeUnitsToMS(pattern_commands):
    '''
    Convert TIME_S, TIME_M, TIME_H to TIME_MS in pattern commands
    Supports float values for time
    pattern_commands: list of command strings
    return -> list of commands with TIME_MS
    '''
    converted_commands = []
    for cmd in pattern_commands:
        # Check for TIME_H (hours)
        time_h_match = re.search(r'TIME_H:([\d.,]+)', cmd)
        if time_h_match:
            time_str = time_h_match.group(1)
            time_values = [float(t) for t in time_str.split(',')]
            # Convert hours to milliseconds
            time_ms = [int(t * 3600 * 1000) for t in time_values]
            time_ms_str = ','.join(map(str, time_ms))
            new_cmd = re.sub(r'TIME_H:[\d.,]+', f'TIME_MS:{time_ms_str}', cmd)
            converted_commands.append(new_cmd)
            continue
        
        # Check for TIME_M (minutes)
        time_m_match = re.search(r'TIME_M:([\d.,]+)', cmd)
        if time_m_match:
            time_str = time_m_match.group(1)
            time_values = [float(t) for t in time_str.split(',')]
            # Convert minutes to milliseconds
            time_ms = [int(t * 60 * 1000) for t in time_values]
            time_ms_str = ','.join(map(str, time_ms))
            new_cmd = re.sub(r'TIME_M:[\d.,]+', f'TIME_MS:{time_ms_str}', cmd)
            converted_commands.append(new_cmd)
            continue
        
        # Check for TIME_S (seconds)
        time_s_match = re.search(r'TIME_S:([\d.,]+)', cmd)
        if time_s_match:
            time_str = time_s_match.group(1)
            time_values = [float(t) for t in time_str.split(',')]
            # Convert seconds to milliseconds
            time_ms = [int(t * 1000) for t in time_values]
            time_ms_str = ','.join(map(str, time_ms))
            new_cmd = re.sub(r'TIME_S:[\d.,]+', f'TIME_MS:{time_ms_str}', cmd)
            converted_commands.append(new_cmd)
            continue
        
        # Already TIME_MS or no time field
        converted_commands.append(cmd)
    
    return converted_commands

def ApplyCalibrationToTxtCommands(pattern_commands, calib_factor):
    '''
    Apply calibration factor to TIME_MS values in pattern commands
    pattern_commands: list of command strings
    calib_factor: calibration factor to apply
    return -> list of calibrated command strings
    '''
    calibrated_commands = []
    for cmd in pattern_commands:
        # Parse the command to extract TIME_MS values
        time_match = re.search(r'TIME_MS:([\d,]+)', cmd)
        if time_match:
            time_str = time_match.group(1)
            time_values = [int(t) for t in time_str.split(',')]
            # Apply calibration
            calibrated_times = [int(t / calib_factor) for t in time_values]
            # Replace TIME_MS in the command
            new_time_str = ','.join(map(str, calibrated_times))
            new_cmd = re.sub(r'TIME_MS:[\d,]+', f'TIME_MS:{new_time_str}', cmd)
            
            # Also calibrate pulse width and period if PULSE parameter exists
            pulse_match = re.search(r'PULSE:([\w.,]+)', new_cmd)
            if pulse_match:
                pulse_str = pulse_match.group(1)
                pulse_parts = pulse_str.split(',')
                calibrated_pulse_parts = []
                for part in pulse_parts:
                    # Parse T[period]pw[width] format
                    period_match = re.search(r'T([\d]+)', part)
                    pw_match = re.search(r'pw([\d]+)', part)
                    if period_match and pw_match:
                        period = float(period_match.group(1))
                        pw = float(pw_match.group(1))
                        # Apply calibration to both period and pulse width
                        calibrated_period = int(period / calib_factor)
                        calibrated_pw = int(pw / calib_factor)
                        calibrated_pulse_parts.append(f'T{calibrated_period}pw{calibrated_pw}')
                    else:
                        calibrated_pulse_parts.append(part)
                new_pulse_str = ','.join(calibrated_pulse_parts)
                new_cmd = re.sub(r'PULSE:[\w.,]+', f'PULSE:{new_pulse_str}', new_cmd)
            
            calibrated_commands.append(new_cmd)
        else:
            calibrated_commands.append(cmd)
    return calibrated_commands