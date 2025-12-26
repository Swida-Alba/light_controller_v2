/**
 * Function Dispatcher for Light Controller v2.2 F Mode
 * ====================================================
 * 
 * This header file contains the dispatcher for custom easing functions.
 * It maps function names (strings) to their actual function implementations.
 * 
 * WHY SEPARATE FILE?
 * ------------------
 * This file is separate from custom_easing.h so you can:
 * 1. Easily locate and modify the dispatcher
 * 2. Add new function mappings without touching the main Arduino code
 * 3. Keep function definitions (custom_easing.h) separate from dispatch logic
 * 
 * HOW TO ADD A NEW FUNCTION:
 * --------------------------
 * 1. Define your function in custom_easing.h:
 *    float my_awesome_func(float progress) { return ...; }
 * 
 * 2. Add the dispatch entry in FUNCTION_REGISTRY below:
 *    {"my_awesome_func", my_awesome_func},
 * 
 * 3. That's it! Recompile and upload.
 * 
 * ALTERNATIVE: Use 'myfunc'
 * -------------------------
 * If you just want to experiment, edit the myfunc() function in custom_easing.h
 * - No need to modify this file at all!
 * - Just change the formula in myfunc() and recompile
 */

#ifndef FUNCTION_DISPATCHER_H
#define FUNCTION_DISPATCHER_H

#include <Arduino.h>    // For byte type and Serial
#include <string.h>     // For strcmp
#include "custom_easing.h"

// =============================================================================
// FUNCTION REGISTRY
// =============================================================================
// Each entry maps a function name (string) to its function pointer.
// Add your custom functions here!
//
// Format: {"function_name", function_pointer}
// 
// The function must have signature: float func(float progress)

typedef float (*EasingFunction)(float);

struct FunctionEntry {
    const char* name;
    EasingFunction func;
};

// Registry of all available custom functions
// ADD YOUR NEW FUNCTIONS TO THIS LIST!
const FunctionEntry FUNCTION_REGISTRY[] = {
    // Built-in functions from custom_easing.h
    {"sine_wave",   sine_wave},
    {"double_sine", double_sine},
    {"bounce",      bounce},
    {"heartbeat",   heartbeat},
    {"exp_decay",   exp_decay},
    {"log_rise",    log_rise},
    {"step_50",     step_50},
    {"sawtooth",    sawtooth},
    {"breathing",   breathing},
    {"flicker",     flicker},
    
    // User-customizable placeholder (edit myfunc in custom_easing.h)
    {"myfunc",      myfunc},
    
    // =========================================
    // ADD YOUR CUSTOM FUNCTIONS BELOW:
    // =========================================
    // {"my_awesome_func", my_awesome_func},
    // {"cool_effect",     cool_effect},
    // =========================================
};

const int FUNCTION_REGISTRY_SIZE = sizeof(FUNCTION_REGISTRY) / sizeof(FUNCTION_REGISTRY[0]);

// =============================================================================
// DISPATCHER FUNCTION
// =============================================================================
// This function looks up the function name in the registry and calls it.
// Returns: PWM value (0-255), clipped to valid range

byte dispatchCustomFunction(const char* funcName, float progress) {
    // Search the registry for the function
    for (int i = 0; i < FUNCTION_REGISTRY_SIZE; i++) {
        if (strcmp(funcName, FUNCTION_REGISTRY[i].name) == 0) {
            float result = FUNCTION_REGISTRY[i].func(progress);
            // Clip to valid PWM range
            if (result < 0) result = 0;
            if (result > 255) result = 255;
            return (byte)result;
        }
    }
    
    // Function not found - print warning and use linear fallback
    Serial.print("Warning: Unknown function '");
    Serial.print(funcName);
    Serial.println("', using linear fallback");
    return (byte)(255.0 * progress);
}

#endif // FUNCTION_DISPATCHER_H
