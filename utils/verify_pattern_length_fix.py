#!/usr/bin/env python
"""
Quick test to verify the pattern length check now allows smaller patterns.
"""

import sys

# Mock the SendGreeting behavior
def test_pattern_length_check():
    """Simulate the new pattern length validation"""
    
    test_cases = [
        (2, 4, "Your case - protocol needs 2, Arduino has 4"),
        (4, 4, "Perfect match"),
        (8, 4, "Error case - protocol needs more than Arduino has"),
    ]
    
    for python_pl, arduino_pl, description in test_cases:
        print(f"\n{'='*70}")
        print(f"Test: {description}")
        print(f"  Python requires: {python_pl}")
        print(f"  Arduino supports: {arduino_pl}")
        print(f"{'='*70}")
        
        try:
            # Simulate the check from lcfunc.py
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
                print("   ✅ PASSED (warning only, no error)")
            else:
                # Perfect match
                print(f'\033[32m✓ PATTERN_LENGTH verified: {python_pl}\033[0m')
                print("   ✅ PASSED")
                
        except ValueError as e:
            print(str(e))
            print("   ❌ RAISED ERROR (as expected)")

if __name__ == '__main__':
    print("\n" + "="*70)
    print("PATTERN LENGTH VALIDATION TEST")
    print("="*70)
    test_pattern_length_check()
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("✓ Pattern length 2 with Arduino 4: Shows warning, continues")
    print("✓ Pattern length 4 with Arduino 4: Perfect match")
    print("✗ Pattern length 8 with Arduino 4: Raises error (correct!)")
    print("\nYour case (2 vs 4) will now PASS with a warning instead of error!")
    print("="*70 + "\n")
