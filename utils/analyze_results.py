#!/usr/bin/env python
"""
Quick analysis of the calibration results to understand the relationship
"""

import numpy as np

print("="*70)
print("ANALYZING YOUR CALIBRATION RESULTS")
print("="*70)

# V1 Data
print("\nV1 DATA:")
print("Requested: [30, 40, 50, 60] seconds (what we asked Arduino to wait)")
print("Python measured: [30.033, 40.032, 50.027, 60.032] seconds")
print("\nObservation: Python measures ~0.03s MORE than requested")
print("Interpretation: When Arduino thinks it waited 30s, real time = 30.033s")
print("               → Arduino clock is SLOW (counts slower than real time)")
print("\nBUT V1 regression: python = 0.999925 × requested")
print("This gives factor < 1, suggesting Arduino is FAST??")

# V2 Data  
print("\n" + "="*70)
print("V2 DATA (selected points):")
arduino_times = np.array([0, 6, 12, 18, 24, 30, 60, 90, 120])
python_times = np.array([0, 5.929, 11.937, 17.939, 23.938, 29.930, 59.938, 89.933, 119.939])

print(f"{'Arduino':<12} {'Python':<12} {'Difference':<12}")
print(f"{'(seconds)':<12} {'(seconds)':<12} {'(Py-Ard)':<12}")
print("-"*40)
for a, p in zip(arduino_times, python_times):
    print(f"{a:<12.1f} {p:<12.3f} {p-a:<12.3f}")

print("\nObservation: Python time < Arduino time (difference is negative)")
print("Interpretation: When Arduino reports 60s, Python measured only 59.938s")
print("               → Arduino clock is FAST (reports more time)")
print("\nV2 regression: arduino = 1.000095 × python")
print("This gives factor > 1, suggesting Arduino is SLOW??")

print("\n" + "="*70)
print("THE CONTRADICTION:")
print("="*70)
print("\nV1 shows: Python > Requested → Arduino SLOW → factor 0.999925 (< 1)")
print("V2 shows: Arduino > Python → Arduino FAST → factor 1.000095 (> 1)")
print("\nThese are OPPOSITE directions!")

print("\n" + "="*70)
print("RESOLUTION:")
print("="*70)

print("\nLet's check: Are V1 and V2 factors reciprocals?")
v1_factor = 0.999925
v2_factor = 1.000095
reciprocal = 1 / v1_factor
print(f"V1 factor: {v1_factor:.6f}")
print(f"V2 factor: {v2_factor:.6f}")
print(f"1/V1:      {reciprocal:.6f}")
print(f"Difference between V2 and 1/V1: {abs(v2_factor - reciprocal):.6f}")

print("\n✓ YES! They are reciprocals!")
print("\nThis means:")
print("  V1: python_time = 0.999925 × arduino_time")
print("  V2: arduino_time = 1.000095 × python_time")
print("\nBoth are describing the SAME clock relationship!")

print("\n" + "="*70)
print("WHICH CLOCK IS ACTUALLY FASTER?")
print("="*70)

print("\nLet's look at the RAW DATA (not regression):")
print("\nV1: Python measures MORE time than Arduino's requested wait")
print("    30s request → 30.033s real → Arduino clock is SLOW")
print("\nV2: Arduino reports MORE time than Python measures")
print("    Python 59.938s → Arduino 60s → Arduino clock is FAST")

print("\n⚠️  THESE ARE CONTRADICTORY!")
print("\nThe issue: V1 'requested' is NOT from Arduino's clock!")
print("V1 'requested' is a number WE gave (30, 40, 50, 60)")
print("Arduino uses ITS clock to wait that long")
print("Python measures the real time")

print("\nCorrect interpretation:")
print("V1: We send '30' (a number), Arduino waits using millis(), Python measures real time")
print("    If Python > 30 → real time > expected → Arduino clock is SLOW")
print("\nV2: Arduino reports millis() values, Python records real arrival times")
print("    If Arduino > Python → Arduino counting faster → Arduino clock is FAST")

print("\n⚠️  V1 and V2 STILL DISAGREE on which clock is faster!")
print("\nPossible reasons:")
print("1. V1's 'requested time' is not a pure Arduino clock measurement")
print("2. Communication delays affect them differently")
print("3. Different measurement intervals (30-60s vs 0-120s)")
