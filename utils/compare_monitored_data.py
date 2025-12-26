#!/usr/bin/env python3
"""
Compare monitored Arduino PWM data with expected protocol values.

This script reads a monitored CSV file and compares the actual PWM values
from the Arduino against the expected values from the protocol.
"""

import sys
import math
import csv
from pathlib import Path

def cosine_ease(t, start, end, duration):
    """
    Calculate PWM value using cosine easing.
    
    Args:
        t: Current time within this segment (ms)
        start: Starting PWM value
        end: Ending PWM value
        duration: Total duration of this segment (ms)
        
    Returns:
        PWM value (0-255)
    """
    if duration == 0:
        return end
    progress = min(t / duration, 1.0)
    # Cosine easing: slow start, fast middle, slow end
    ease = (1 - math.cos(progress * math.pi)) / 2
    return int(start + (end - start) * ease)


def calculate_expected_ch1(t_ms, pattern):
    """
    Calculate expected CH1 value at time t_ms based on the RAMP pattern.
    
    Pattern: RAMP:(C:0,255,15000),(C:255,0,15000);REPEATS:2
    - Segment 1: 0→255 over 15000ms (cosine)
    - Segment 2: 255→0 over 15000ms (cosine)
    - Total cycle: 30000ms, repeated 2 times = 60000ms total
    """
    cycle_duration = 30000  # 15000 + 15000
    t_in_cycle = t_ms % cycle_duration
    
    if t_in_cycle < 15000:
        # First segment: 0 → 255
        return cosine_ease(t_in_cycle, 0, 255, 15000)
    else:
        # Second segment: 255 → 0
        return cosine_ease(t_in_cycle - 15000, 255, 0, 15000)


def calculate_expected_ch2(t_ms, pattern):
    """
    Calculate expected CH2 value at time t_ms based on the STATUS pattern.
    
    Pattern: STATUS:255,0;TIME_MS:1000,1000;REPEATS:30
    - ON (255) for 1000ms
    - OFF (0) for 1000ms
    - Total cycle: 2000ms, repeated 30 times = 60000ms total
    
    Returns: (expected_value, near_transition)
    near_transition indicates if we're within 100ms of a state change
    """
    cycle_duration = 2000  # 1000 + 1000
    t_in_cycle = t_ms % cycle_duration
    
    # Check if we're near a transition (within 100ms margin)
    near_transition = (abs(t_in_cycle - 1000) < 100 or 
                       t_in_cycle < 100 or 
                       t_in_cycle > 1900)
    
    if t_in_cycle < 1000:
        return 255, near_transition
    else:
        return 0, near_transition


def analyze_monitored_data(csv_path):
    """
    Analyze monitored data and compare with expected values.
    """
    errors_ch1 = []
    errors_ch2 = []
    max_error_ch1 = 0
    max_error_ch2 = 0
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"Analyzing {len(rows)} data points from {csv_path}")
    print("=" * 70)
    
    # Analyze each data point
    ch2_transition_samples = 0
    ch2_non_transition_errors = []
    
    for row in rows:
        t_ms = float(row['time_ms'])
        ch1_actual = int(row['CH1'])
        ch2_actual = int(row['CH2'])
        
        ch1_expected = calculate_expected_ch1(t_ms, None)
        ch2_expected, ch2_near_transition = calculate_expected_ch2(t_ms, None)
        
        error_ch1 = abs(ch1_actual - ch1_expected)
        error_ch2 = abs(ch2_actual - ch2_expected)
        
        errors_ch1.append(error_ch1)
        errors_ch2.append(error_ch2)
        
        if ch2_near_transition:
            ch2_transition_samples += 1
        else:
            ch2_non_transition_errors.append(error_ch2)
        
        if error_ch1 > max_error_ch1:
            max_error_ch1 = error_ch1
            max_error_ch1_time = t_ms
            max_error_ch1_actual = ch1_actual
            max_error_ch1_expected = ch1_expected
        
        if error_ch2 > max_error_ch2:
            max_error_ch2 = error_ch2
            max_error_ch2_time = t_ms
    
    # Calculate statistics
    avg_error_ch1 = sum(errors_ch1) / len(errors_ch1) if errors_ch1 else 0
    avg_error_ch2 = sum(errors_ch2) / len(errors_ch2) if errors_ch2 else 0
    
    print("\n📊 CHANNEL 1 (RAMP with Cosine Easing)")
    print("-" * 40)
    print(f"  Average error: {avg_error_ch1:.2f} PWM steps")
    print(f"  Maximum error: {max_error_ch1} PWM steps")
    if max_error_ch1 > 0:
        print(f"    at t={max_error_ch1_time:.0f}ms: actual={max_error_ch1_actual}, expected={max_error_ch1_expected}")
    
    print("\n📊 CHANNEL 2 (STATUS blink)")
    print("-" * 40)
    print(f"  Average error: {avg_error_ch2:.2f} PWM steps")
    print(f"  Maximum error: {max_error_ch2} PWM steps")
    print(f"  Samples near transitions: {ch2_transition_samples} ({100*ch2_transition_samples/len(rows):.1f}%)")
    if ch2_non_transition_errors:
        avg_error_ch2_stable = sum(ch2_non_transition_errors) / len(ch2_non_transition_errors)
        max_error_ch2_stable = max(ch2_non_transition_errors)
        print(f"  Average error (stable periods): {avg_error_ch2_stable:.2f} PWM steps")
        print(f"  Maximum error (stable periods): {max_error_ch2_stable} PWM steps")
    
    # Timing accuracy
    first_t = float(rows[0]['time_ms'])
    last_t = float(rows[-1]['time_ms'])
    actual_duration = last_t - first_t
    expected_duration = 60000  # 60 seconds
    timing_error = abs(actual_duration - expected_duration)
    timing_error_pct = (timing_error / expected_duration) * 100
    
    print("\n⏱️  TIMING ACCURACY")
    print("-" * 40)
    print(f"  Expected duration: {expected_duration/1000:.1f}s")
    print(f"  Actual duration:   {actual_duration/1000:.1f}s")
    print(f"  Timing error:      {timing_error/1000:.2f}s ({timing_error_pct:.3f}%)")
    
    # Overall verdict
    print("\n" + "=" * 70)
    avg_error_ch2_stable = sum(ch2_non_transition_errors) / len(ch2_non_transition_errors) if ch2_non_transition_errors else avg_error_ch2
    if avg_error_ch1 < 5 and avg_error_ch2_stable < 10 and timing_error_pct < 1:
        print("✅ PASS: Arduino PWM output matches protocol expectations!")
    else:
        print("⚠️  REVIEW: Some deviations detected (may be timing jitter)")
    print("=" * 70)
    
    return {
        'avg_error_ch1': avg_error_ch1,
        'avg_error_ch2': avg_error_ch2,
        'max_error_ch1': max_error_ch1,
        'max_error_ch2': max_error_ch2,
        'timing_error_pct': timing_error_pct
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        # Default to the most recent monitored file
        examples_dir = Path(__file__).parent.parent / 'examples'
        csv_files = sorted(examples_dir.glob('*_monitored.csv'))
        if csv_files:
            csv_path = csv_files[-1]
            print(f"Using most recent file: {csv_path}")
        else:
            print("Usage: python compare_monitored_data.py <monitored.csv>")
            sys.exit(1)
    else:
        csv_path = sys.argv[1]
    
    results = analyze_monitored_data(csv_path)
