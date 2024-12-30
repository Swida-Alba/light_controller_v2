from lcfunc import *
import tkinter as tk
from tkinter import filedialog

if __name__ == '__main__':
    print('Welcom to use the light controller!')
    try:
        print('Please select your protocol file...')
        protocol_file = filedialog.askopenfilename(title='Select the protocol file', filetypes=[('Excel files', '*.xlsx')])
        # protocol_file = R'protocol.xlsx'
        
        required_board_type = 'Arduino'
        
        df_protocol, df_startTime, calib_factor = ReadExcelFile(protocol_file)
        channel_units, valid_channels = GetChannelInfo(df_protocol)
        start_time, wait_status = ReadStartTime(df_startTime)
        CheckStartTimeForChannels(start_time, valid_channels)
        df_ms = ConvertTimeToMillisecond(df_protocol, channel_units)
        for ch in valid_channels:
            print(f'{ch}: start time: {start_time[ch]}, wait status: {wait_status[ch]}.')
        
        ser = SetUpSerialPort(board_type=required_board_type, baudrate=9600)
        if not ser:
            raise ValueError('Serial port is not available.')
        
        ClearSerialBuffer(ser, print_flag=True)
        
        SendGreeting(ser)
        
        if calib_factor is None:
            calibration_parameters = CalibrateArduinoTime(ser, t_send=[40, 60, 80, 100])
            calib_factor = calibration_parameters['calib_factor']
            # if calib_factor > 1:
            #     calib_factor = (calib_factor - 1) * 0.85 + 1
        print(f'Calibration factor is {calib_factor:.5f}. Correct {(calib_factor - 1) * 12 * 3600:.2f} seconds per 12 hours.')
        
        df_corrected = CorrectTime(df_ms, calib_factor)
        
        compressed_patterns = FindRepeatedPatterns(df_corrected, pattern_length=2)
        cmd_patterns = GeneratePatternCommands(compressed_patterns)
        for cmd_t in cmd_patterns:
            SendCommand(ser, cmd_t)
        
        time_countdown = CountDown(start_time)
        remainging_time_corrected = CorrectTime(time_countdown, calib_factor)
        
        cmd_wait = GenerateWaitCommands(wait_status, remainging_time_corrected, valid_channels)
        for cmd_t in cmd_wait:
            SendCommand(ser, cmd_t)
        
        SayBye(ser)
        ser.close()
        
        # write all commands to a txt
        protocol_path = os.path.abspath(protocol_file)
        protocol_name = os.path.basename(protocol_path)
        protocol_name = os.path.splitext(protocol_name)[0]
        timestamp_str = datetime.datetime.now().strftime(f'%Y%m%d%H%M%S')
        
        start_time_str = {}
        for ch, t in start_time.items():
            start_time_str[ch] = t.strftime('%Y-%m-%d %H:%M:%S')
        
        commands_file = os.path.join(os.path.dirname(protocol_path), f'{protocol_name}_commands_{timestamp_str}.txt')
        with open(commands_file, 'w') as f:
            for cmd_t in cmd_wait:
                f.write(cmd_t)
            for cmd_t in cmd_patterns:
                f.write(cmd_t)
            # write the start time and wait status to the file
            f.write(f'START_TIME: {start_time_str}\n')
            # write calibration factor and keep 10 decimals
            f.write(f'CALIBRATION_FACTOR: {calib_factor:.5f}\n')
        print(f'Commands are written to {commands_file}.')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'\nError: {e}\n')
        print('Program is terminated.')
        if 'ser' in locals() and ser != '':
            ser.close()
    finally:
        input('\nPress <Enter> to exit:')