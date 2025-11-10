#!/usr/bin/env python
"""
Simple example demonstrating how to choose calibration method.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from light_controller_parser import LightControllerParser

# Example 1: Use V2 method (recommended, default)
print("Example 1: Using V2 calibration (fast, accurate)")
parser_v2 = LightControllerParser('examples/simple_blink_example.txt', calibration_method='v2')
print(f"Parser created with calibration method: {parser_v2.calibration_method}")

# Example 2: Use V1 method (original, for compatibility)
print("\nExample 2: Using V1 calibration (original method)")
parser_v1 = LightControllerParser('examples/simple_blink_example.txt', calibration_method='v1')
print(f"Parser created with calibration method: {parser_v1.calibration_method}")

# Example 3: Override calibration method when calling calibrate()
print("\nExample 3: Override method per calibration call")
parser = LightControllerParser('examples/simple_blink_example.txt', calibration_method='v2')
print(f"Parser default method: {parser.calibration_method}")
print("You can override with: parser.calibrate(use_v2=False)  # Forces V1")
print("Or use default with: parser.calibrate()  # Uses V2")

print("\n✓ All examples loaded successfully!")
print("\nTo run actual calibration with hardware:")
print("  1. Connect your Arduino")
print("  2. Run: python test_calibration_comparison.py")
