#!/usr/bin/env python
"""
Calibration Method Comparison

Compares V1, V1.1, and V2 calibration methods by testing with the same Arduino
and comparing results, speed, and data quality.
"""

import sys
import os
# Add parent directory to path to import lcfunc
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lcfunc import (
    SetUpSerialPort,
    CalibrateArduinoTime,
    CalibrateArduinoTime_v11, 
    CalibrateArduinoTime_v2,
    CalibrateArduinoTime_v2_improved
)
import time
import numpy as np


def test_calibration_method(ser, method_name, **kwargs):
    """Test a single calibration method."""
    print(f"\n{'='*70}")
    print(f"{method_name.upper()} CALIBRATION TEST")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    if method_name == 'v1':
        t_send = kwargs.get('t_send', [20,40,60])
        print(f"Test times: {t_send} seconds (total: {sum(t_send)}s)")
        result = CalibrateArduinoTime(ser, t_send=t_send, use_v2=False)
    elif method_name == 'v1.1':
        t_send = kwargs.get('t_send', [20,40,60])
        print(f"Test times: {t_send} seconds (total: {sum(t_send)}s)")
        result = CalibrateArduinoTime_v11(ser, t_send=t_send)
    elif method_name == 'v2':
        duration = kwargs.get('duration', 180)
        num_samples = kwargs.get('num_samples', 18)
        print(f"Duration: {duration}s with {num_samples} samples")
        result = CalibrateArduinoTime_v2(ser, duration=duration, num_samples=num_samples)
    else:
        raise ValueError(f"Unknown method: {method_name}")
    
    elapsed_time = time.time() - start_time
    
    print(f"\n{method_name.upper()} Results:")
    print(f"  Time: {elapsed_time:.1f}s")
    print(f"  Factor: {result['calib_factor']:.6f}")
    if 'r_squared' in result:
        print(f"  R²: {result.get('r_squared', 'N/A')}")
    if 'rmse' in result:
        print(f"  RMSE: {result.get('rmse', 0)*1000:.2f} ms")
    
    return result, elapsed_time


def compare_results(results_dict):
    """Compare calibration results."""
    print(f"\n{'='*70}")
    print("COMPARISON")
    print(f"{'='*70}")
    
    methods = list(results_dict.keys())
    factors = [results_dict[m][0]['calib_factor'] for m in methods]
    times = [results_dict[m][1] for m in methods]
    
    print(f"\n{'Method':<15} {'Factor':<12} {'Time (s)':<12}")
    print("-" * 40)
    for method, factor, elapsed in zip(methods, factors, times):
        print(f"{method:<15} {factor:<12.6f} {elapsed:<12.1f}")
    
    mean_factor = np.mean(factors)
    std_factor = np.std(factors)
    
    print(f"\nFactor Statistics:")
    print(f"  Mean: {mean_factor:.6f}")
    print(f"  Std: {std_factor:.6f} ({std_factor/mean_factor*100:.4f}%)")
    print(f"  Range: {max(factors) - min(factors):.6f}")
    
    if std_factor / mean_factor < 0.001:
        print(f"\n✓ EXCELLENT: All methods agree within 0.1%")
    elif std_factor / mean_factor < 0.01:
        print(f"\n✓ GOOD: All methods agree within 1%")
    else:
        print(f"\n⚠️  WARNING: Methods show disagreement")


def main():
    print("="*70)
    print("CALIBRATION METHOD COMPARISON")
    print("="*70)
    print("\nTesting V1, V1.1, V2, V2_improved")
    print("Total time: ~20 minutes")
    
    ser = SetUpSerialPort(board_type='Arduino', baudrate=9600)
    if not ser:
        print("\nERROR: Could not connect")
        return
    
    try:
        results = {}
        
        # input("\nPress Enter to start V2...")
        results['V2'], time_v2 = test_calibration_method(
            ser, 'v2', duration=300, num_samples=30
        )
        time.sleep(2)
        
        # input("\nPress Enter to start V1...")
        results['V1'], time_v1 = test_calibration_method(
            ser, 'v1', t_send=[60, 70, 80, 90]
        )
        time.sleep(2)
        
        # input("\nPress Enter to start V1.1...")
        results['V1.1'], time_v11 = test_calibration_method(
            ser, 'v1.1', t_send=[60, 70, 80, 90]
        )
        time.sleep(2)
        
        
        results_with_times = {
            'V1': (results['V1'], time_v1),
            'V1.1': (results['V1.1'], time_v11),
            'V2': (results['V2'], time_v2),
        }
        
        compare_results(results_with_times)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if ser:
            ser.close()
            print("\nConnection closed")


if __name__ == '__main__':
    main()
