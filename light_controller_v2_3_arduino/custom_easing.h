/**
 * Custom Easing Functions for Light Controller v2.2
 * ================================================
 * 
 * This file provides custom PWM easing functions that go beyond the
 * built-in L, C, I, O, X modes. Use these for non-monotonic effects
 * like heartbeat, bounce, or complex waveforms.
 * 
 * F MODE FORMAT:
 * --------------
 *   RAMP:(F:function_name,duration_ms);
 * 
 *   - function_name: Name of the custom function (e.g., heartbeat)
 *   - duration_ms: How long the function runs (scales time to progress)
 * 
 * PROGRESS PARAMETER:
 * -------------------
 * All functions receive `progress` as a value between [0, 1]:
 *   - progress = elapsed_time / duration_ms
 *   - Time-to-progress conversion is done OUTSIDE the function
 *   - Your function only needs to return PWM value for given progress
 * 
 * USAGE IN ARDUINO:
 * -----------------
 * 1. This file is automatically included in the Arduino sketch
 * 2. Functions take progress (0.0 to 1.0) and return PWM (0.0 to 255.0)
 * 3. The Arduino's clipPWM() is called AFTER these functions
 * 
 * ⚠️ IMPORTANT: Adding a new function here does NOT automatically make
 * it available in Arduino protocols! You must ALSO:
 *   1. Add a case for your function name in the firmware's F mode dispatcher
 *   2. Recompile and upload the modified firmware
 * 
 * USAGE IN PYTHON SIMULATOR:
 * --------------------------
 * The PYTHON_EQUIV comments allow mock_arduino.py to load these functions:
 *   python mock_arduino.py protocol.txt --custom-funcs custom_easing.h
 * 
 * ✓ New functions ARE immediately available in the Python simulator!
 * 
 * ADDING NEW FUNCTIONS:
 * ---------------------
 * 1. Add a comment block with:
 *    // CUSTOM_FUNC: your_function_name
 *    // PYTHON_EQUIV: lambda p: your_python_expression
 * 2. Define the C function below the comments
 * 3. Progress (p) is always 0.0 to 1.0
 * 4. Return value should be 0.0 to 255.0 (clipping is done externally)
 * 
 * PROTOCOL USAGE:
 * ---------------
 * Use F mode in RAMP commands:
 *   PATTERN:1;CH:1;RAMP:(F:sine_wave,5000);REPEATS:3
 *   PATTERN:1;CH:2;RAMP:(F:heartbeat,2000);REPEATS:10
 */

#ifndef CUSTOM_EASING_H
#define CUSTOM_EASING_H

#include <math.h>

// =============================================================================
// SINE WAVE - Half cycle 0→255→0
// =============================================================================
// CUSTOM_FUNC: sine_wave
// PYTHON_EQUIV: lambda p: 255 * math.sin(p * math.pi)

float sine_wave(float progress) {
    // progress: 0.0 to 1.0
    // output: 0 → 255 → 0 (half sine wave)
    return 255.0 * sin(progress * 3.14159265);
}

// =============================================================================
// DOUBLE SINE - Two complete bumps in one cycle
// =============================================================================
// CUSTOM_FUNC: double_sine
// PYTHON_EQUIV: lambda p: 127.5 * (1 + math.sin(2 * math.pi * p * 2 - math.pi/2))

float double_sine(float progress) {
    return 127.5 * (1.0 + sin(2.0 * 3.14159265 * progress * 2.0 - 3.14159265 / 2.0));
}

// =============================================================================
// BOUNCE - Damped oscillation (ball bounce effect)
// =============================================================================
// CUSTOM_FUNC: bounce
// PYTHON_EQUIV: lambda p: 255 * abs(math.sin(p * math.pi * 3) * (1 - p))

float bounce(float progress) {
    return 255.0 * fabs(sin(progress * 3.14159265 * 3.0) * (1.0 - progress));
}

// =============================================================================
// HEARTBEAT - Two quick pulses (lub-dub pattern)
// =============================================================================
// CUSTOM_FUNC: heartbeat
// PYTHON_EQUIV: lambda p: min(255, 255 * (math.exp(-20*(p-0.2)**2) + 0.6*math.exp(-20*(p-0.4)**2)))

float heartbeat(float progress) {
    float pulse1 = exp(-20.0 * pow(progress - 0.2, 2));
    float pulse2 = 0.6 * exp(-20.0 * pow(progress - 0.4, 2));
    return 255.0 * (pulse1 + pulse2);  // May exceed 255, clipPWM handles it
}

// =============================================================================
// EXPONENTIAL DECAY - Sharp start, gradual decay  
// =============================================================================
// CUSTOM_FUNC: exp_decay
// PYTHON_EQUIV: lambda p: 255 * math.exp(-3 * p)

float exp_decay(float progress) {
    return 255.0 * exp(-3.0 * progress);
}

// =============================================================================
// LOGARITHMIC RISE - Slow start, accelerating finish
// =============================================================================
// CUSTOM_FUNC: log_rise
// PYTHON_EQUIV: lambda p: 255 * math.log(1 + p * (math.e - 1)) / math.log(math.e)

float log_rise(float progress) {
    return 255.0 * log(1.0 + progress * (2.71828 - 1.0));
}

// =============================================================================
// STEP FUNCTION - Jump at 50%
// =============================================================================
// CUSTOM_FUNC: step_50
// PYTHON_EQUIV: lambda p: 255 if p >= 0.5 else 0

float step_50(float progress) {
    return progress >= 0.5 ? 255.0 : 0.0;
}

// =============================================================================
// SAWTOOTH - Linear rise, instant drop (3 cycles)
// =============================================================================
// CUSTOM_FUNC: sawtooth
// PYTHON_EQUIV: lambda p: 255 * ((p * 3) % 1)

float sawtooth(float progress) {
    float phase = fmod(progress * 3.0, 1.0);
    return 255.0 * phase;
}

// =============================================================================
// BREATHING - Smooth in-out cycle using cosine
// =============================================================================
// CUSTOM_FUNC: breathing
// PYTHON_EQUIV: lambda p: 127.5 * (1 - math.cos(2 * math.pi * p))

float breathing(float progress) {
    return 127.5 * (1.0 - cos(2.0 * 3.14159265 * progress));
}

// =============================================================================
// FLICKER - Random-like flickering effect
// =============================================================================
// CUSTOM_FUNC: flicker  
// PYTHON_EQUIV: lambda p: 127.5 + 127.5 * math.sin(p * math.pi * 20) * math.sin(p * math.pi * 7)

float flicker(float progress) {
    return 127.5 + 127.5 * sin(progress * 3.14159265 * 20.0) * sin(progress * 3.14159265 * 7.0);
}

// =============================================================================
// MYFUNC - User-customizable placeholder function
// =============================================================================
// This is YOUR function! Modify the formula below to create your own effect.
// No need to modify any Arduino dispatcher code - just edit this formula.
//
// CUSTOM_FUNC: myfunc
// PYTHON_EQUIV: lambda p: 255 * p

float myfunc(float progress) {
    // =============================================
    // CUSTOMIZE YOUR FUNCTION HERE!
    // =============================================
    // progress goes from 0.0 (start) to 1.0 (end)
    // Return a PWM value from 0.0 to 255.0
    //
    // Examples you can try:
    //   return 255.0 * progress;                        // Linear ramp
    //   return 255.0 * progress * progress;             // Quadratic ease-in
    //   return 255.0 * (1.0 - progress);                // Reverse ramp
    //   return 255.0 * sin(progress * 3.14159265);      // Half sine wave
    //   return 127.5 + 127.5 * sin(progress * 6.28);    // Full sine oscillation
    //
    // Current: simple linear ramp (same as L mode)
    return 255.0 * progress;
}

#endif // CUSTOM_EASING_H
