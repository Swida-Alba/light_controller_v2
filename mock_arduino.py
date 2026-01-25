#!/usr/bin/env python3
"""
Mock Arduino Simulator for Light Controller v2.2

Simulates Arduino behavior for testing protocols without hardware.
- Parses protocol files with validation/scrutinization
- Simulates PWM transitions with correct easing
- Supports custom easing functions via header files
- Outputs channel monitor data ($CHMON: format)
- Generates CSV logs and visualizations

Usage:
    python mock_arduino.py protocol.txt --output simulation.csv --plot
    python mock_arduino.py protocol.txt --realtime --speed 10
    python mock_arduino.py protocol.txt --validate  # Check protocol only
"""

import argparse
import time
import math
import csv
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass, field
import re
import warnings

# Try to import optional dependencies
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


# =============================================================================
# PWM UTILITIES
# =============================================================================

# Channel output type constants
OUTPUT_TYPE_PWM = 'P'       # 8-bit PWM (0-255)
OUTPUT_TYPE_DAC = 'D'       # 12-bit Native DAC (0-4095)
OUTPUT_TYPE_MCP4728 = 'M'   # 12-bit MCP4728 DAC (0-4095)
OUTPUT_TYPE_BINARY = 'B'    # Binary (0 or 1)

# Resolution constants
RESOLUTION_BINARY = 1
RESOLUTION_8BIT = 255
RESOLUTION_12BIT = 4095

# Virtual pin constants (matching Arduino)
NATIVE_DAC_PIN_BASE = 100   # 100=DAC0, 101=DAC1
MCP4728_PIN_BASE = 201      # 201-204 = MCP4728 channels A-D


def detect_pin_type(pin: int) -> str:
    """
    Auto-detect channel type from virtual pin number.
    Matches Arduino behavior:
      - 0-99: PWM ('P')
      - 100-101: Native DAC ('D')
      - 201-204: MCP4728 ('M')
    """
    if MCP4728_PIN_BASE <= pin <= MCP4728_PIN_BASE + 3:
        return OUTPUT_TYPE_MCP4728
    if NATIVE_DAC_PIN_BASE <= pin <= NATIVE_DAC_PIN_BASE + 1:
        return OUTPUT_TYPE_DAC
    return OUTPUT_TYPE_PWM


def get_channel_types_from_pins(pins: list) -> str:
    """
    Get channel types string from a list of virtual pin numbers.
    
    Args:
        pins: List of virtual pin numbers (e.g., [11, 12, 201, 202])
        
    Returns:
        String of channel types (e.g., "PPMM")
    """
    return ''.join(detect_pin_type(p) for p in pins)


def get_max_value_for_type(channel_type: str) -> int:
    """Get maximum value for a channel type"""
    return {
        OUTPUT_TYPE_BINARY: RESOLUTION_BINARY,
        OUTPUT_TYPE_PWM: RESOLUTION_8BIT,
        OUTPUT_TYPE_DAC: RESOLUTION_12BIT,
        OUTPUT_TYPE_MCP4728: RESOLUTION_12BIT,
    }.get(channel_type, RESOLUTION_8BIT)


def clip_value(value: float, max_val: int = 255) -> int:
    """Clip value to valid range [0, max_val]"""
    if value < 0:
        return 0
    elif value > max_val:
        return max_val
    return int(round(value))


def clip_pwm(value: float) -> int:
    """Clip PWM value to valid range [0, 255] (backward compatible)"""
    return clip_value(value, 255)


# =============================================================================
# EASING FUNCTIONS (Match Arduino implementation)
# =============================================================================

def f(t: float) -> float:
    """Core easing function: f(t) = (1 - cos(π*t)) / 2"""
    return (1 - math.cos(math.pi * t)) / 2


def calculate_eased_pwm(progress: float, start_pwm: int, end_pwm: int, 
                         t_start: float, t_end: float) -> int:
    """
    Calculate PWM value with easing (for L, C, I, O modes).
    Normalizes f(t) to map [f(t_start), f(t_end)] → [0, 1].
    
    Args:
        progress: 0 to 1 (elapsed time proportion)
        start_pwm: Starting PWM (0-255)
        end_pwm: Ending PWM (0-255)
        t_start: Start of t range (0-2)
        t_end: End of t range (0-2)
        
    Returns:
        PWM value clipped to [0, 255]
    """
    # Map progress to t range
    t = t_start + progress * (t_end - t_start)
    
    # Calculate f(t) at endpoints and current
    f_start = f(t_start)
    f_end = f(t_end)
    f_current = f(t)
    
    # Normalize to [0, 1]
    if abs(f_end - f_start) < 0.0001:
        eased_progress = progress
    else:
        eased_progress = (f_current - f_start) / (f_end - f_start)
    
    # Calculate PWM and clip to valid range
    pwm = start_pwm + eased_progress * (end_pwm - start_pwm)
    return clip_pwm(pwm)


def calculate_x_mode_pwm(progress: float, t_start: float, t_end: float) -> int:
    """
    Calculate PWM for X mode (custom t range) - NO SCALING.
    
    X mode directly uses 255 * f(t) without normalization.
    This means:
      - t: 0→0.5   → PWM: 0→127.5 (ascending, ease-in shape)
      - t: 0.5→1   → PWM: 127.5→255 (ascending, ease-out shape)
      - t: 1→1.5   → PWM: 255→127.5 (DESCENDING, ease-in shape)
      - t: 1.5→2   → PWM: 127.5→0 (DESCENDING, ease-out shape)
      - t: 0→2     → PWM: 0→255→0 (full breathing cycle)
    
    Args:
        progress: 0 to 1 (elapsed time proportion)
        t_start: Start of t range (0-2)
        t_end: End of t range (0-2)
        
    Returns:
        PWM value clipped to [0, 255]
    """
    # Map progress to t range
    t = t_start + progress * (t_end - t_start)
    
    # Direct f(t) * 255 - no normalization
    pwm = 255 * f(t)
    return clip_pwm(pwm)


# =============================================================================
# CUSTOM FUNCTION SUPPORT
# =============================================================================

class CustomFunctionLoader:
    """
    Load custom easing functions from header files.
    
    Custom functions are defined in .h files with a specific format:
    
    // custom_easing.h
    // CUSTOM_FUNC: my_function
    // Returns PWM value (0-255) for given progress (0.0-1.0)
    // Note: Values outside [0,255] will be clipped automatically
    
    float my_function(float progress) {
        return 255.0 * sin(progress * PI);  // Example: sine wave
    }
    """
    
    def __init__(self):
        self.functions: Dict[str, Callable[[float], float]] = {}
        self._load_builtin_functions()
    
    def _load_builtin_functions(self):
        """Load built-in custom functions"""
        # Sine wave (non-monotonic)
        self.functions['sine'] = lambda p: 255 * math.sin(p * math.pi)
        
        # Triangle wave
        self.functions['triangle'] = lambda p: 255 * (2 * abs(p - 0.5))
        
        # Square wave (with soft edges)
        self.functions['square'] = lambda p: 255 if p >= 0.5 else 0
        
        # Exponential
        self.functions['exponential'] = lambda p: 255 * (math.exp(p) - 1) / (math.e - 1)
        
        # Logarithmic
        self.functions['logarithmic'] = lambda p: 255 * math.log(1 + p * (math.e - 1)) / math.log(math.e)
        
        # Bounce
        self.functions['bounce'] = lambda p: 255 * abs(math.sin(p * math.pi * 3) * (1 - p))
    
    def load_from_header(self, filepath: str) -> bool:
        """
        Load custom functions from a C/C++ header file.
        
        Format expected:
        // CUSTOM_FUNC: function_name
        // PYTHON_EQUIV: lambda p: expression
        """
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Find function definitions
            pattern = r'//\s*CUSTOM_FUNC:\s*(\w+)\s*\n\s*//\s*PYTHON_EQUIV:\s*(.+)'
            matches = re.findall(pattern, content)
            
            for name, expr in matches:
                try:
                    # Safely evaluate the lambda expression
                    func = eval(expr, {'math': math, 'sin': math.sin, 'cos': math.cos, 
                                       'exp': math.exp, 'log': math.log, 'sqrt': math.sqrt,
                                       'pi': math.pi, 'PI': math.pi})
                    self.functions[name] = func
                    print(f"  Loaded custom function: {name}")
                except Exception as e:
                    warnings.warn(f"Failed to load function {name}: {e}")
            
            return len(matches) > 0
        except FileNotFoundError:
            return False
    
    def get_function(self, name: str) -> Optional[Callable[[float], float]]:
        """Get a custom function by name"""
        return self.functions.get(name)
    
    def list_functions(self) -> List[str]:
        """List available custom functions"""
        return list(self.functions.keys())


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class RampSegment:
    """Single ramp segment"""
    start_pwm: int
    end_pwm: int
    duration_ms: int
    mode: str  # L, C, I, O, X, F
    t_start: float = 0.0
    t_end: float = 1.0
    func_name: str = None  # For F mode (custom function)


@dataclass
class PatternSection:
    """Single section within a pattern"""
    pwm: int
    duration_ms: int
    is_ramp: bool = False
    ramp_segments: List[RampSegment] = None


@dataclass
class Pattern:
    """Complete pattern definition"""
    pattern_id: int
    channel: int
    sections: List[PatternSection]
    repeats: int = 1


# =============================================================================
# PROTOCOL PARSER
# =============================================================================

class ProtocolParser:
    """Parse protocol files into executable patterns with validation"""
    
    # Default t ranges for each mode (ASCENDING: end_pwm > start_pwm)
    MODE_T_RANGES = {
        'L': (0, 1),      # Linear (doesn't use cosine)
        'C': (0, 1),      # Cosine (full S-curve)
        'I': (0, 0.5),    # Ease-in (slow start, accelerating)
        'O': (0.5, 1),    # Ease-out (fast start, decelerating)
        'X': (0, 1),      # Custom (user-specified)
        'F': (0, 1),      # Custom Function (uses raw values, no scaling)
    }
    
    # Alternate ranges for DESCENDING (end_pwm < start_pwm)
    MODE_T_RANGES_DESC = {
        'L': (0, 1),
        'C': (1, 2),
        'I': (1, 1.5),    # Ease-in descending (slow start going down)
        'O': (1.5, 2),    # Ease-out descending (slow end going down)
        'X': (0, 1),
        'F': (0, 1),
    }
    
    def __init__(self, verbose: bool = True):
        self.patterns: List[Pattern] = []
        self.start_times: Dict[int, int] = {}  # Channel -> start time offset
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.verbose = verbose
        self.custom_functions = CustomFunctionLoader()
        
    def parse_file(self, filepath: str) -> List[Pattern]:
        """Parse a protocol file"""
        with open(filepath, 'r') as f:
            content = f.read()
        return self.parse_content(content)
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate all parsed patterns.
        
        Returns:
            (is_valid, warnings, errors)
        """
        return len(self.errors) == 0, self.warnings, self.errors
    
    def _add_warning(self, msg: str):
        """Add a warning message"""
        self.warnings.append(msg)
        if self.verbose:
            print(f"⚠️  Warning: {msg}")
    
    def _add_error(self, msg: str):
        """Add an error message"""
        self.errors.append(msg)
        if self.verbose:
            print(f"❌ Error: {msg}")
    
    def parse_content(self, content: str) -> List[Pattern]:
        """Parse protocol content string with validation"""
        self.patterns = []
        self.warnings = []
        self.errors = []
        line_num = 0
        
        for line in content.split('\n'):
            line_num += 1
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
                
            # Parse START_TIME
            if line.startswith('START_TIME:'):
                self._parse_start_time(line)
                continue
                
            # Parse pattern line
            if 'PATTERN:' in line:
                pattern = self._parse_pattern_line(line, line_num)
                if pattern:
                    self.patterns.append(pattern)
        
        # Print validation summary
        if self.verbose and (self.warnings or self.errors):
            print(f"\n📋 Validation Summary: {len(self.errors)} errors, {len(self.warnings)} warnings")
        
        return self.patterns
    
    def _parse_start_time(self, line: str):
        """Parse START_TIME: {'CH1': 30, ...}"""
        match = re.search(r"START_TIME:\s*(\{.*\})", line)
        if match:
            try:
                # Simple parsing for {'CH1': 30} format
                times_str = match.group(1)
                for ch_match in re.finditer(r"'CH(\d+)':\s*(\d+)", times_str):
                    ch = int(ch_match.group(1))
                    time_sec = int(ch_match.group(2))
                    self.start_times[ch] = time_sec * 1000  # Convert to ms
            except:
                pass
    
    def _parse_pattern_line(self, line: str, line_num: int = 0) -> Optional[Pattern]:
        """Parse a single pattern line with validation"""
        # Extract components
        pattern_id = self._extract_value(line, 'PATTERN', int)
        channel = self._extract_value(line, 'CH', int)
        repeats = self._extract_value(line, 'REPEATS', int) or 1
        
        if pattern_id is None or channel is None:
            self._add_error(f"Line {line_num}: Missing PATTERN or CH specification")
            return None
        
        # Check for HYBRID protocol (both RAMP and STATUS/TIME_MS in same line)
        has_ramp = 'RAMP:' in line
        has_status = 'STATUS:' in line and 'TIME_MS:' in line
        
        if has_ramp and has_status:
            self._add_error(
                f"Line {line_num}: HYBRID protocols mixing RAMP and STATUS/TIME_MS are INVALID. "
                f"For constant sections within a RAMP, use L mode: (L:pwm,pwm,duration)"
            )
            return None
        
        sections = []
        
        # Parse RAMP commands
        ramp_matches = re.finditer(r'RAMP:([^;]+)', line)
        for match in ramp_matches:
            ramp_str = match.group(1)
            ramp_sections = self._parse_ramp(ramp_str, line_num, channel)
            sections.extend(ramp_sections)
        
        # Parse STATUS/TIME_MS pairs (only if no RAMP)
        if not has_ramp:
            status_match = re.search(r'STATUS:([^;]+)', line)
            time_match = re.search(r'TIME_MS:([^;]+)', line)
            
            if status_match and time_match:
                status_strs = [x.strip() for x in status_match.group(1).split(',')]
                times = [int(x.strip()) for x in time_match.group(1).split(',')]
                
                # Parse status values (can be int or normalized float)
                statuses = []
                for s in status_strs:
                    if '.' in s:
                        val = float(s)
                        if 0 <= val <= 1.0:
                            statuses.append(int(val * 255))
                        else:
                            statuses.append(int(val))
                    else:
                        val = int(s)
                        # Scale 12-bit to 8-bit for simulation
                        if val > 255:
                            statuses.append(int((val / 4095) * 255))
                        else:
                            statuses.append(val)
                
                for pwm, duration in zip(statuses, times):
                    sections.append(PatternSection(pwm=clip_pwm(pwm), duration_ms=duration))
        
        if not sections:
            self._add_warning(f"Line {line_num}: Pattern {pattern_id} CH{channel} has no sections")
            return None
            
        return Pattern(
            pattern_id=pattern_id,
            channel=channel,
            sections=sections,
            repeats=repeats
        )
    
    def _scrutinize_ramp(self, mode: str, start_pwm: int, end_pwm: int, 
                         t_start: float, t_end: float, line_num: int) -> Tuple[float, float]:
        """
        Scrutinize ramp parameters and auto-correct t range if needed.
        
        Handles:
        1. PWM values outside [0, 255] → warning
        2. t range outside [0, 2] → warning
        3. Direction mismatch (ascending PWM with descending t range) → warning
        4. Non-monotonic t ranges that cross t=1 peak → warning
        
        Returns corrected (t_start, t_end)
        """
        is_ascending = end_pwm > start_pwm
        is_descending = end_pwm < start_pwm
        
        # Check PWM values
        if start_pwm < 0 or start_pwm > 255:
            self._add_warning(f"Line {line_num}: start_pwm={start_pwm} outside [0,255], will be clipped")
        if end_pwm < 0 or end_pwm > 255:
            self._add_warning(f"Line {line_num}: end_pwm={end_pwm} outside [0,255], will be clipped")
        
        # Validate t range
        if t_start < 0 or t_start > 2 or t_end < 0 or t_end > 2:
            self._add_warning(f"Line {line_num}: t range [{t_start},{t_end}] outside [0,2]")
        
        # Check for NON-MONOTONIC t ranges (crossing t=1 peak)
        # f(t) peaks at t=1 with f(1)=1
        # If t range includes t=1, the curve is non-monotonic
        crosses_peak = (t_start < 1 < t_end) or (t_end < 1 < t_start)
        
        if crosses_peak:
            # Determine f values
            f_start = f(t_start)
            f_peak = 1.0  # f(1) = 1
            f_end = f(t_end)
            
            self._add_warning(
                f"Line {line_num}: Non-monotonic t range [{t_start},{t_end}] crosses peak at t=1. "
                f"f(t) goes {f_start:.3f}→1.000→{f_end:.3f}. "
                f"PWM will NOT be a smooth transition - consider splitting into two segments."
            )
            
            # Explain the PWM scaling behavior for non-monotonic ranges
            if self.verbose:
                print(f"   ℹ️  For non-monotonic t ranges, PWM is scaled by normalizing f(t):")
                print(f"       eased_progress = (f(t) - f({t_start})) / (f({t_end}) - f({t_start}))")
                print(f"       This maps f(t) from [{f_start:.3f}, {f_end:.3f}] to [0, 1]")
                print(f"       Result: PWM overshoots then returns (creates a bump/dip)")
        
        # Check for direction mismatch (only for monotonic ranges)
        if not crosses_peak and mode in ['I', 'O'] and not (t_start == t_end):
            expected_asc = self.MODE_T_RANGES[mode]
            expected_desc = self.MODE_T_RANGES_DESC[mode]
            
            if is_ascending and (t_start, t_end) == expected_desc:
                self._add_warning(
                    f"Line {line_num}: Mode '{mode}' with ascending PWM ({start_pwm}→{end_pwm}) "
                    f"uses descending t range [{t_start},{t_end}]. "
                    f"Consider using [{expected_asc[0]},{expected_asc[1]}] for proper easing."
                )
            elif is_descending and (t_start, t_end) == expected_asc:
                self._add_warning(
                    f"Line {line_num}: Mode '{mode}' with descending PWM ({start_pwm}→{end_pwm}) "
                    f"uses ascending t range [{t_start},{t_end}]. "
                    f"Consider using [{expected_desc[0]},{expected_desc[1]}] for proper easing."
                )
        
        return t_start, t_end
    
    def _parse_ramp(self, ramp_str: str, line_num: int = 0, channel: int = 0) -> List[PatternSection]:
        """Parse RAMP command into sections with validation"""
        sections = []
        
        # New format for L, C, I, O modes: (MODE:start,end,duration)
        # Values can be integers (0-255, 0-4095) or floats (0.0-1.0 normalized)
        # X mode format: (X:duration|t_start,t_end) - NO PWM values!
        # F mode format: (F:func_name,duration)
        
        # Pattern for L, C, I, O modes: (MODE:start,end,duration) - supports int and float values
        lciox_format = re.findall(r'\(([LCIO]):([0-9.]+),([0-9.]+),(\d+)\)', ramp_str)
        
        # Pattern for X mode: (X:duration|t_start,t_end)
        x_format = re.findall(r'\(X:(\d+)\|([0-9.]+),([0-9.]+)\)', ramp_str)
        
        # Pattern for F mode: (F:func_name,duration)
        func_format = re.findall(r'\(F:(\w+),(\d+)\)', ramp_str)
        
        if lciox_format:
            for match in lciox_format:
                mode = match[0]
                start_str = match[1]
                end_str = match[2]
                duration = int(match[3])
                
                # Parse values - could be normalized (0.0-1.0) or integer
                # For now, assume 255 max for PWM simulation (will be scaled at output)
                if '.' in start_str:
                    start_val = float(start_str)
                    if 0 <= start_val <= 1.0:
                        start_pwm = int(start_val * 255)
                    else:
                        start_pwm = int(start_val)
                else:
                    start_val = int(start_str)
                    # If value > 255, scale down for simulation (12-bit -> 8-bit)
                    if start_val > 255:
                        start_pwm = int((start_val / 4095) * 255)
                    else:
                        start_pwm = start_val
                
                if '.' in end_str:
                    end_val = float(end_str)
                    if 0 <= end_val <= 1.0:
                        end_pwm = int(end_val * 255)
                    else:
                        end_pwm = int(end_val)
                else:
                    end_val = int(end_str)
                    # If value > 255, scale down for simulation (12-bit -> 8-bit)
                    if end_val > 255:
                        end_pwm = int((end_val / 4095) * 255)
                    else:
                        end_pwm = end_val
                
                # Determine t range based on direction
                is_descending = end_pwm < start_pwm
                
                if is_descending:
                    t_start, t_end = self.MODE_T_RANGES_DESC[mode]
                else:
                    t_start, t_end = self.MODE_T_RANGES[mode]
                
                # Scrutinize the ramp parameters (skip for valid 12-bit or normalized values)
                if not ('.' in start_str or start_val <= 255) or not ('.' in end_str or end_val <= 255):
                    pass  # 12-bit values - don't warn
                else:
                    t_start, t_end = self._scrutinize_ramp(mode, start_pwm, end_pwm, t_start, t_end, line_num)
                
                segment = RampSegment(
                    start_pwm=clip_pwm(start_pwm),
                    end_pwm=clip_pwm(end_pwm),
                    duration_ms=duration,
                    mode=mode,
                    t_start=t_start,
                    t_end=t_end
                )
                
                sections.append(PatternSection(
                    pwm=clip_pwm(start_pwm),
                    duration_ms=duration,
                    is_ramp=True,
                    ramp_segments=[segment]
                ))
        
        if x_format:
            for match in x_format:
                duration = int(match[0])
                t_start = float(match[1])
                t_end = float(match[2])
                
                # Validate t range
                if t_start < 0 or t_start > 2 or t_end < 0 or t_end > 2:
                    self._add_warning(f"Line {line_num}: X mode t range [{t_start},{t_end}] outside [0,2]")
                
                segment = RampSegment(
                    start_pwm=0,  # Ignored for X mode
                    end_pwm=255,  # Ignored for X mode
                    duration_ms=duration,
                    mode='X',
                    t_start=t_start,
                    t_end=t_end
                )
                
                sections.append(PatternSection(
                    pwm=0,
                    duration_ms=duration,
                    is_ramp=True,
                    ramp_segments=[segment]
                ))
        
        if func_format:
            for match in func_format:
                func_name = match[0]
                duration = int(match[1])
                
                if not self.custom_functions.get_function(func_name):
                    self._add_error(f"Line {line_num}: Custom function '{func_name}' not found. "
                                   f"Available: {', '.join(self.custom_functions.list_functions())}")
                    continue
                
                segment = RampSegment(
                    start_pwm=0,
                    end_pwm=255,
                    duration_ms=duration,
                    mode='F',
                    t_start=0,
                    t_end=1,
                    func_name=func_name
                )
                
                sections.append(PatternSection(
                    pwm=0,
                    duration_ms=duration,
                    is_ramp=True,
                    ramp_segments=[segment]
                ))
        
        if not lciox_format and not x_format and not func_format:
            # Legacy format: start,end,duration,steps,mode
            legacy = re.findall(r'(\d+),(\d+),(\d+),(\d+),([LCIOX])', ramp_str)
            for match in legacy:
                start_pwm = int(match[0])
                end_pwm = int(match[1])
                duration = int(match[2])
                mode = match[4]
                
                is_descending = end_pwm < start_pwm
                if is_descending:
                    t_start, t_end = self.MODE_T_RANGES_DESC[mode]
                else:
                    t_start, t_end = self.MODE_T_RANGES[mode]
                
                segment = RampSegment(
                    start_pwm=start_pwm,
                    end_pwm=end_pwm,
                    duration_ms=duration,
                    mode=mode,
                    t_start=t_start,
                    t_end=t_end
                )
                
                sections.append(PatternSection(
                    pwm=start_pwm,
                    duration_ms=duration,
                    is_ramp=True,
                    ramp_segments=[segment]
                ))
        
        return sections
    
    def _extract_value(self, line: str, key: str, cast_type):
        """Extract a value from a pattern line"""
        match = re.search(rf'{key}:(\d+)', line)
        if match:
            return cast_type(match.group(1))
        return None


# =============================================================================
# MOCK ARDUINO SIMULATOR
# =============================================================================

class MockArduino:
    """Simulates Arduino PWM/DAC control and channel monitoring"""
    
    def __init__(self, time_step_ms: int = 10, max_channels: int = 8, 
                 custom_functions: Optional[CustomFunctionLoader] = None,
                 channel_types: str = None,
                 channel_pins: list = None):
        """
        Initialize mock Arduino simulator.
        
        Args:
            time_step_ms: Simulation time step in milliseconds
            max_channels: Maximum number of channels
            custom_functions: Custom easing function loader
            channel_types: String of channel types (e.g., "PPMM" for 2 PWM + 2 MCP4728)
                          If None and channel_pins provided, auto-detects from pins.
                          If both None, defaults to all PWM ('P' * max_channels)
            channel_pins: List of virtual pin numbers (e.g., [11, 12, 201, 202])
                         If provided, channel_types is auto-detected from pins.
        """
        self.time_step_ms = time_step_ms
        self.max_channels = max_channels
        self.custom_functions = custom_functions or CustomFunctionLoader()
        
        # Store channel pins (default to sequential PWM pins)
        if channel_pins:
            self.channel_pins = list(channel_pins)[:max_channels]
            while len(self.channel_pins) < max_channels:
                self.channel_pins.append(len(self.channel_pins))
        else:
            self.channel_pins = list(range(max_channels))
        
        # Set up channel types - prefer auto-detection from pins
        if channel_pins:
            # Auto-detect from virtual pins
            self.channel_types = get_channel_types_from_pins(self.channel_pins)
        elif channel_types:
            self.channel_types = channel_types[:max_channels].ljust(max_channels, 'P')
        else:
            self.channel_types = 'P' * max_channels
        
        # Calculate max values per channel
        self.channel_max_values = [
            get_max_value_for_type(t) for t in self.channel_types
        ]
        
        # Initialize state
        self.current_values = [0] * self.max_channels  # Current output value per channel
        self.simulation_time_ms = 0
        self.data_log: List[Tuple[int, List[int]]] = []  # (time_ms, [ch1, ch2, ...])
        
        # Print configuration if verbose
        print(f"MockArduino initialized:")
        print(f"  Pins: {self.channel_pins}")
        print(f"  Types: {self.channel_types} ({self._describe_types()})")
        print(f"  Max values: {self.channel_max_values}")
    
    def _describe_types(self) -> str:
        """Return human-readable channel type description"""
        type_names = {
            'P': 'PWM(8bit)',
            'D': 'DAC(12bit)',
            'M': 'MCP4728(12bit)',
            'B': 'Binary'
        }
        return ', '.join(type_names.get(t, '?') for t in self.channel_types)
        
    def reset(self):
        """Reset simulator state"""
        self.current_values = [0] * self.max_channels
        self.simulation_time_ms = 0
        self.data_log = []
    
    def get_channel_type(self, channel: int) -> str:
        """Get the type of a channel (1-indexed)"""
        idx = channel - 1
        if 0 <= idx < len(self.channel_types):
            return self.channel_types[idx]
        return 'P'  # Default to PWM
    
    def get_channel_max(self, channel: int) -> int:
        """Get the maximum value for a channel (1-indexed)"""
        idx = channel - 1
        if 0 <= idx < len(self.channel_max_values):
            return self.channel_max_values[idx]
        return 255  # Default to 8-bit
    
    def set_channel_value(self, channel: int, value: int):
        """Set a channel's output value, clipping to valid range"""
        idx = channel - 1
        if 0 <= idx < self.max_channels:
            max_val = self.channel_max_values[idx]
            self.current_values[idx] = clip_value(value, max_val)
    
    # Backward compatible property
    @property
    def current_pwm(self):
        return self.current_values
    
    @current_pwm.setter
    def current_pwm(self, value):
        self.current_values = value
    
    def simulate_patterns(self, patterns: List[Pattern], 
                          realtime: bool = False, 
                          speed_factor: float = 1.0,
                          print_interval_ms: int = 100) -> List[Tuple[int, List[int]]]:
        """
        Simulate pattern execution.
        
        Args:
            patterns: List of patterns to execute
            realtime: If True, simulate in real-time (with optional speed factor)
            speed_factor: Speed multiplier for realtime mode (10 = 10x faster)
            print_interval_ms: Interval for $CHMON: output
            
        Returns:
            List of (time_ms, [pwm values]) tuples
        """
        self.reset()
        
        # Group patterns by channel
        channel_patterns: Dict[int, List[Pattern]] = {}
        for p in patterns:
            if p.channel not in channel_patterns:
                channel_patterns[p.channel] = []
            channel_patterns[p.channel].append(p)
        
        # Calculate total duration
        total_duration_ms = 0
        for ch, pats in channel_patterns.items():
            ch_duration = sum(
                sum(s.duration_ms for s in p.sections) * p.repeats 
                for p in pats
            )
            total_duration_ms = max(total_duration_ms, ch_duration)
        
        # Initialize channel states
        channel_states: Dict[int, dict] = {}
        for ch in channel_patterns.keys():
            channel_states[ch] = {
                'pattern_idx': 0,
                'section_idx': 0,
                'repeat_idx': 0,
                'section_time': 0,
                'done': False
            }
        
        last_print_time = 0
        
        # Main simulation loop
        while self.simulation_time_ms <= total_duration_ms:
            # Update each channel
            for ch, patterns_list in channel_patterns.items():
                if channel_states[ch]['done']:
                    continue
                    
                state = channel_states[ch]
                
                # Get current pattern and section
                if state['pattern_idx'] >= len(patterns_list):
                    state['done'] = True
                    continue
                    
                pattern = patterns_list[state['pattern_idx']]
                
                if state['section_idx'] >= len(pattern.sections):
                    # Move to next repeat or pattern
                    state['repeat_idx'] += 1
                    if state['repeat_idx'] >= pattern.repeats:
                        state['pattern_idx'] += 1
                        state['repeat_idx'] = 0
                    state['section_idx'] = 0
                    state['section_time'] = 0
                    continue
                
                section = pattern.sections[state['section_idx']]
                
                # Calculate PWM value
                if section.is_ramp and section.ramp_segments:
                    seg = section.ramp_segments[0]
                    progress = min(1.0, state['section_time'] / section.duration_ms)
                    
                    if seg.mode == 'L':
                        # Linear interpolation
                        pwm = seg.start_pwm + progress * (seg.end_pwm - seg.start_pwm)
                    elif seg.mode == 'X':
                        # X mode: raw f(t) * 255 without scaling
                        pwm = calculate_x_mode_pwm(progress, seg.t_start, seg.t_end)
                    elif seg.mode == 'F':
                        # Custom function mode
                        func = self.custom_functions.get_function(seg.func_name) if hasattr(seg, 'func_name') else None
                        if func:
                            pwm = clip_pwm(func(progress))
                        else:
                            pwm = seg.start_pwm + progress * (seg.end_pwm - seg.start_pwm)
                    else:
                        # C, I, O modes: scaled easing
                        pwm = calculate_eased_pwm(
                            progress, 
                            seg.start_pwm, 
                            seg.end_pwm, 
                            seg.t_start, 
                            seg.t_end
                        )
                    
                    self.current_pwm[ch - 1] = int(round(pwm))
                else:
                    self.current_pwm[ch - 1] = section.pwm
                
                # Advance time within section
                state['section_time'] += self.time_step_ms
                
                if state['section_time'] >= section.duration_ms:
                    state['section_idx'] += 1
                    state['section_time'] = 0
            
            # Log data
            self.data_log.append((
                self.simulation_time_ms,
                self.current_pwm.copy()
            ))
            
            # Print channel monitor output
            if self.simulation_time_ms - last_print_time >= print_interval_ms:
                self._print_channel_monitor()
                last_print_time = self.simulation_time_ms
            
            # Real-time simulation
            if realtime:
                time.sleep((self.time_step_ms / 1000.0) / speed_factor)
            
            self.simulation_time_ms += self.time_step_ms
        
        return self.data_log
    
    def _print_channel_monitor(self):
        """Print $CHMON: format output"""
        parts = [f"CH{i+1}:{self.current_pwm[i]}" for i in range(self.max_channels)]
        print(f"$CHMON:{','.join(parts)}")
    
    def save_csv(self, filepath: str):
        """Save simulation data to CSV"""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            headers = ['time_ms'] + [f'CH{i+1}' for i in range(self.max_channels)]
            writer.writerow(headers)
            for time_ms, pwms in self.data_log:
                writer.writerow([time_ms] + pwms)
        print(f"Saved simulation data to {filepath}")
    
    def plot(self, title: str = "Mock Arduino Simulation", 
             show: bool = True, save_html: str = None):
        """Generate Plotly visualization"""
        if not HAS_PLOTLY:
            print("Error: plotly not installed. Run: pip install plotly")
            return None
        
        times = [d[0] / 1000.0 for d in self.data_log]  # Convert to seconds
        
        fig = make_subplots(rows=1, cols=1)
        
        colors = ['#667eea', '#f56565', '#48bb78', '#ed8936', '#9f7aea', '#38b2ac', '#fc8181', '#f6ad55']
        
        for ch in range(self.max_channels):
            pwms = [d[1][ch] for d in self.data_log]
            if any(p > 0 for p in pwms):  # Only plot channels with activity
                fig.add_trace(go.Scatter(
                    x=times,
                    y=pwms,
                    mode='lines',
                    name=f'CH{ch + 1}',
                    line=dict(color=colors[ch], width=2)
                ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Time (seconds)',
            yaxis_title='PWM Value (0-255)',
            yaxis=dict(range=[0, 260]),
            template='plotly_white',
            hovermode='x unified',
            legend=dict(x=1.02, y=1)
        )
        
        if save_html:
            fig.write_html(save_html)
            print(f"Saved plot to {save_html}")
        
        if show:
            fig.show()
        
        return fig


# =============================================================================
# MAIN CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Mock Arduino Simulator for Light Controller',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python mock_arduino.py protocol.txt
  python mock_arduino.py protocol.txt --output data.csv --plot
  python mock_arduino.py protocol.txt --realtime --speed 10
  python mock_arduino.py protocol.txt --save-plot simulation.html
  python mock_arduino.py protocol.txt --custom-funcs custom_easing.h
  python mock_arduino.py protocol.txt --pins 201,202,203,13  # MCP4728 + PWM
        '''
    )
    
    parser.add_argument('protocol', help='Protocol file to simulate')
    parser.add_argument('--output', '-o', help='Output CSV file for data logging')
    parser.add_argument('--plot', action='store_true', help='Show interactive plot')
    parser.add_argument('--save-plot', help='Save plot to HTML file')
    parser.add_argument('--realtime', action='store_true', help='Simulate in real-time')
    parser.add_argument('--speed', type=float, default=1.0, 
                        help='Speed factor for realtime mode (default: 1.0)')
    parser.add_argument('--step', type=int, default=10,
                        help='Simulation time step in ms (default: 10)')
    parser.add_argument('--print-interval', type=int, default=100,
                        help='$CHMON print interval in ms (default: 100)')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress $CHMON output')
    parser.add_argument('--custom-funcs', metavar='HEADER',
                        help='Load custom functions from Arduino header file (e.g., custom_easing.h)')
    parser.add_argument('--pins', metavar='PIN_LIST',
                        help='Comma-separated virtual pin numbers (e.g., 201,202,203,13). '
                             'Auto-detects channel types: 0-99=PWM, 100-101=DAC, 201-204=MCP4728')
    
    args = parser.parse_args()
    
    # Parse protocol
    print(f"Parsing protocol: {args.protocol}")
    parser_obj = ProtocolParser()
    
    # Load custom functions from header if specified
    if args.custom_funcs:
        before_count = len(parser_obj.custom_functions.list_functions())
        loaded = parser_obj.custom_functions.load_from_header(args.custom_funcs)
        after_count = len(parser_obj.custom_functions.list_functions())
        loaded_count = after_count - before_count
        if loaded:
            print(f"Loaded {loaded_count} custom function(s) from {args.custom_funcs}")
        else:
            print(f"Warning: No custom functions found in {args.custom_funcs}")
    
    patterns = parser_obj.parse_file(args.protocol)
    
    if not patterns:
        print("Error: No patterns found in protocol file")
        sys.exit(1)
    
    print(f"Found {len(patterns)} pattern(s)")
    for p in patterns:
        print(f"  Pattern {p.pattern_id}: CH{p.channel}, {len(p.sections)} sections, {p.repeats} repeats")
    
    # Create simulator with custom functions from parser
    # Parse channel pins if provided
    channel_pins = None
    if args.pins:
        try:
            channel_pins = [int(p.strip()) for p in args.pins.split(',')]
            print(f"Using virtual pins: {channel_pins}")
        except ValueError:
            print(f"Error: Invalid pin format '{args.pins}'. Use comma-separated integers.")
            sys.exit(1)
    
    arduino = MockArduino(
        time_step_ms=args.step, 
        custom_functions=parser_obj.custom_functions,
        channel_pins=channel_pins
    )
    
    # Run simulation
    print("\nStarting simulation...")
    if args.quiet:
        # Redirect stdout temporarily
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
    
    arduino.simulate_patterns(
        patterns,
        realtime=args.realtime,
        speed_factor=args.speed,
        print_interval_ms=args.print_interval
    )
    
    if args.quiet:
        sys.stdout = old_stdout
    
    print(f"\nSimulation complete: {arduino.simulation_time_ms / 1000:.1f} seconds simulated")
    print(f"Data points collected: {len(arduino.data_log)}")
    
    # Save CSV if requested
    if args.output:
        arduino.save_csv(args.output)
    
    # Plot if requested
    if args.plot or args.save_plot:
        arduino.plot(
            title=f"Simulation: {Path(args.protocol).stem}",
            show=args.plot,
            save_html=args.save_plot
        )


if __name__ == '__main__':
    main()
