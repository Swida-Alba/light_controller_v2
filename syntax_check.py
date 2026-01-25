#!/usr/bin/env python3
"""
Protocol Syntax Checker for Light Controller v2.3

This module provides comprehensive syntax validation for protocol files
before they are compiled and sent to Arduino. It uses fuzzy matching
to provide correction suggestions for typos without auto-correcting.

Usage:
    python syntax_check.py <protocol_file>
    python syntax_check.py examples/1min_test.txt
    python syntax_check.py protocol.xlsx

Classes:
    SyntaxError: Custom exception for syntax errors with suggestions
    PatternValidator: Validates PATTERN command syntax
    RampValidator: Validates RAMP segment syntax
    DictBlockValidator: Validates START_TIME, WAIT_STATUS, WAIT_PULSE blocks
    ProtocolSyntaxChecker: Main validator orchestrating all checks

Author: Light Controller Project
Version: 2.3.0
"""

import re
import sys
import argparse
from difflib import get_close_matches
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Set


# ==============================================================================
# VALID SYNTAX CONSTANTS
# ==============================================================================

# Valid field names in PATTERN commands
VALID_PATTERN_FIELDS = {'PATTERN', 'CH', 'STATUS', 'RAMP', 'TIME_MS', 'TIME_S', 
                        'TIME_M', 'TIME_H', 'REPEATS', 'PULSE'}

# Valid RAMP modes
VALID_RAMP_MODES = {'L', 'C', 'I', 'O', 'X', 'F'}

# Valid F mode function names (built-in)
VALID_F_MODE_FUNCTIONS = {'heartbeat', 'bounce', 'sine_wave', 'sawtooth', 
                          'triangle', 'breathing', 'flicker', 'double_sine',
                          'exp_decay', 'log_rise', 'step_50', 'myfunc'}

# Valid dict block keywords
VALID_DICT_BLOCKS = {'START_TIME', 'WAIT_STATUS', 'WAIT_PULSE', 'CALIBRATION_FACTOR', 'LOOP'}

# Common typos/misspellings to check against
COMMON_FIELD_TYPOS = {
    'PATERN': 'PATTERN',
    'PATTER': 'PATTERN',
    'PATTRN': 'PATTERN',
    'CHANEL': 'CH',
    'CHANNEL': 'CH',
    'STAUS': 'STATUS',
    'SATUS': 'STATUS',
    'STATSU': 'STATUS',
    'STAUTS': 'STATUS',
    'REPAETS': 'REPEATS',
    'REPATS': 'REPEATS',
    'REPEAST': 'REPEATS',
    'REPEAT': 'REPEATS',
    'RPEATS': 'REPEATS',
    'TIME': 'TIME_MS',
    'TIMEMS': 'TIME_MS',
    'TIMES': 'TIME_S',
    'TIME_SEC': 'TIME_S',
    'TIME_MIN': 'TIME_M',
    'TIME_HOUR': 'TIME_H',
    'PULS': 'PULSE',
    'PUSLE': 'PULSE',
    'PLUSE': 'PULSE',
    'RAMPE': 'RAMP',
    'RMAP': 'RAMP',
}

COMMON_MODE_TYPOS = {
    'LINEAR': 'L',
    'LIN': 'L',
    'COSINE': 'C',
    'COS': 'C',
    'EASEIN': 'I',
    'EASE-IN': 'I',
    'EASE_IN': 'I',
    'IN': 'I',
    'EASEOUT': 'O',
    'EASE-OUT': 'O',
    'EASE_OUT': 'O',
    'OUT': 'O',
    'CUSTOM': 'X',
    'FUNCTION': 'F',
    'FUNC': 'F',
}

# Excel column synonyms (for validation)
EXCEL_TIME_SUFFIXES = {'_ms', '_msec', '_millisecond', '_milliseconds',
                       '_s', '_sec', '_second', '_seconds',
                       '_m', '_min', '_minute', '_minutes',
                       '_h', '_hr', '_hour', '_hours'}

EXCEL_FREQUENCY_SYNONYMS = {'frequency', 'freq', 'frq', 'f', 'hz', 'Hz'}
EXCEL_PERIOD_SYNONYMS = {'period', 'T', 'cycle_time', 'cycletime'}
EXCEL_PULSE_WIDTH_SYNONYMS = {'pulse_width', 'pulsewidth', 'PW', 'pw', 'on_time', 'ontime'}
EXCEL_DUTY_CYCLE_SYNONYMS = {'duty_cycle', 'dutycycle', 'DC', 'dc', 'duty'}


# ==============================================================================
# CUSTOM EXCEPTIONS
# ==============================================================================

class SyntaxValidationError(Exception):
    """
    Custom exception for syntax validation errors with suggestions.
    
    Attributes:
        message: Error description
        line_num: Line number where error occurred (1-indexed)
        line_content: The actual line content
        suggestions: List of correction suggestions
    """
    def __init__(self, message: str, line_num: int = None, 
                 line_content: str = None, suggestions: List[str] = None):
        self.message = message
        self.line_num = line_num
        self.line_content = line_content
        self.suggestions = suggestions or []
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format error message with location and suggestions."""
        parts = []
        
        if self.line_num:
            parts.append(f"Line {self.line_num}")
        
        parts.append(self.message)
        
        if self.line_content:
            parts.append(f"\n  Content: {self.line_content.strip()}")
        
        if self.suggestions:
            suggestions_text = "\n".join(f"    • {s}" for s in self.suggestions)
            parts.append(f"\n  Did you mean:\n{suggestions_text}")
        
        return " - ".join(parts[:2]) + "".join(parts[2:])


# ==============================================================================
# FUZZY MATCHING UTILITIES
# ==============================================================================

class FuzzyMatcher:
    """Utility class for fuzzy string matching and suggestion generation."""
    
    @staticmethod
    def find_similar(word: str, valid_words: Set[str], 
                     cutoff: float = 0.6) -> List[str]:
        """
        Find similar words from a set of valid words.
        
        Args:
            word: The word to match
            valid_words: Set of valid words to match against
            cutoff: Minimum similarity ratio (0-1)
            
        Returns:
            List of similar valid words, sorted by similarity
        """
        # First check common typos
        word_upper = word.upper()
        if word_upper in COMMON_FIELD_TYPOS:
            return [COMMON_FIELD_TYPOS[word_upper]]
        if word_upper in COMMON_MODE_TYPOS:
            return [COMMON_MODE_TYPOS[word_upper]]
        
        # Use difflib for fuzzy matching
        matches = get_close_matches(word.upper(), 
                                   [w.upper() for w in valid_words], 
                                   n=3, cutoff=cutoff)
        
        # Return original case versions
        result = []
        for match in matches:
            for valid in valid_words:
                if valid.upper() == match:
                    result.append(valid)
                    break
        
        return result
    
    @staticmethod
    def suggest_correction(word: str, valid_words: Set[str]) -> Optional[str]:
        """
        Get the best suggestion for a misspelled word.
        
        Args:
            word: The misspelled word
            valid_words: Set of valid words
            
        Returns:
            Best suggestion or None
        """
        suggestions = FuzzyMatcher.find_similar(word, valid_words)
        return suggestions[0] if suggestions else None


# ==============================================================================
# PATTERN COMMAND VALIDATOR
# ==============================================================================

class PatternValidator:
    """Validates PATTERN command syntax in text protocols."""
    
    # Regex patterns for validation
    PATTERN_FIELD_REGEX = re.compile(r'^PATTERN:(\d+)$')
    CH_FIELD_REGEX = re.compile(r'^CH:(\d+)$')
    STATUS_FIELD_REGEX = re.compile(r'^STATUS:([\d.,]+)$')
    TIME_FIELD_REGEX = re.compile(r'^TIME_(MS|S|M|H):([\d.,]+)$')
    REPEATS_FIELD_REGEX = re.compile(r'^REPEATS:(\d+)$')
    PULSE_FIELD_REGEX = re.compile(r'^PULSE:([\w.,]*)$')
    RAMP_FIELD_REGEX = re.compile(r'^RAMP:(.+)$')
    
    @staticmethod
    def strip_inline_comment(value: str) -> str:
        """Strip inline comment from a value (e.g., '1 # comment' -> '1')."""
        if ' #' in value:
            return value.split(' #')[0].strip()
        return value.strip()
    
    def __init__(self):
        self.errors: List[SyntaxValidationError] = []
        self.warnings: List[str] = []
    
    def validate_command(self, command: str, line_num: int) -> bool:
        """
        Validate a single PATTERN command.
        
        Args:
            command: The command string (without comments)
            line_num: Line number in file (1-indexed)
            
        Returns:
            True if valid, False if errors found
        """
        command = command.strip()
        if not command:
            return True
        
        # Split by semicolon
        fields = [f.strip() for f in command.split(';') if f.strip()]
        
        if not fields:
            return True
        
        # Track which required fields are present
        has_pattern = False
        has_ch = False
        has_status = False
        has_ramp = False
        has_time = False
        has_repeats = False
        
        for field in fields:
            if not field:
                continue
            
            # Check if field has key:value format
            if ':' not in field:
                self.errors.append(SyntaxValidationError(
                    f"Invalid field format (missing colon)",
                    line_num, command,
                    ["Fields must be in KEY:value format", f"Found: '{field}'"]
                ))
                continue
            
            key, _, value = field.partition(':')
            key = key.strip().upper()
            value = value.strip()
            
            # Validate known fields
            if self._validate_field(key, value, field, command, line_num):
                if key == 'PATTERN':
                    has_pattern = True
                elif key == 'CH':
                    has_ch = True
                elif key == 'STATUS':
                    has_status = True
                elif key == 'RAMP':
                    has_ramp = True
                elif key.startswith('TIME_'):
                    has_time = True
                elif key == 'REPEATS':
                    has_repeats = True
        
        # Check required fields
        if not has_pattern:
            self.errors.append(SyntaxValidationError(
                "Missing PATTERN field",
                line_num, command,
                ["Add PATTERN:<n> to specify pattern number"]
            ))
        
        if not has_ch:
            self.errors.append(SyntaxValidationError(
                "Missing CH field",
                line_num, command,
                ["Add CH:<n> to specify channel number"]
            ))
        
        if not has_repeats:
            self.errors.append(SyntaxValidationError(
                "Missing REPEATS field",
                line_num, command,
                ["Add REPEATS:<n> to specify repetition count"]
            ))
        
        # Must have either STATUS+TIME or RAMP
        if has_ramp:
            if has_status or has_time:
                self.warnings.append(
                    f"Line {line_num}: RAMP command has STATUS/TIME fields "
                    "(they will be ignored when RAMP is present)"
                )
        else:
            if not has_status:
                self.errors.append(SyntaxValidationError(
                    "Missing STATUS field (required when not using RAMP)",
                    line_num, command,
                    ["Add STATUS:<values> or use RAMP:(<segments>)"]
                ))
            if not has_time:
                self.errors.append(SyntaxValidationError(
                    "Missing TIME field (required when not using RAMP)",
                    line_num, command,
                    ["Add TIME_MS:<values>, TIME_S:<values>, etc."]
                ))
        
        return len(self.errors) == 0
    
    def _validate_field(self, key: str, value: str, field: str, 
                        command: str, line_num: int) -> bool:
        """Validate a single field key:value pair."""
        # Strip inline comments from value
        value = self.strip_inline_comment(value)
        
        # Check for typos in field name
        if key not in VALID_PATTERN_FIELDS and not key.startswith('TIME_'):
            suggestions = FuzzyMatcher.find_similar(key, VALID_PATTERN_FIELDS)
            self.errors.append(SyntaxValidationError(
                f"Unknown field '{key}'",
                line_num, command,
                suggestions if suggestions else ["Valid fields: PATTERN, CH, STATUS, RAMP, TIME_MS, TIME_S, TIME_M, TIME_H, REPEATS, PULSE"]
            ))
            return False
        
        # Validate PATTERN field
        if key == 'PATTERN':
            if not self.PATTERN_FIELD_REGEX.match(field):
                self.errors.append(SyntaxValidationError(
                    f"Invalid PATTERN value '{value}'",
                    line_num, command,
                    ["PATTERN must be a positive integer (e.g., PATTERN:1, PATTERN:2)"]
                ))
                return False
        
        # Validate CH field
        elif key == 'CH':
            if not self.CH_FIELD_REGEX.match(field):
                self.errors.append(SyntaxValidationError(
                    f"Invalid CH value '{value}'",
                    line_num, command,
                    ["CH must be a positive integer (e.g., CH:1, CH:2)"]
                ))
                return False
        
        # Validate STATUS field
        elif key == 'STATUS':
            if not self._validate_status_values(value, command, line_num):
                return False
        
        # Validate TIME fields
        elif key.startswith('TIME_'):
            time_unit = key[5:]
            if time_unit not in ('MS', 'S', 'M', 'H'):
                suggestions = ['TIME_MS', 'TIME_S', 'TIME_M', 'TIME_H']
                self.errors.append(SyntaxValidationError(
                    f"Invalid time unit '{time_unit}'",
                    line_num, command,
                    suggestions
                ))
                return False
            # Extract pattern ID for TIME_MS:0 validation (allow for PATTERN:0)
            pattern_match = re.search(r'PATTERN:(\d+)', command)
            pattern_id = int(pattern_match.group(1)) if pattern_match else None
            if not self._validate_time_values(value, command, line_num, pattern_id):
                return False
        
        # Validate REPEATS field
        elif key == 'REPEATS':
            # Strip inline comment and reconstruct field for regex
            clean_value = self.strip_inline_comment(value)
            clean_field = f"REPEATS:{clean_value}"
            if not self.REPEATS_FIELD_REGEX.match(clean_field):
                self.errors.append(SyntaxValidationError(
                    f"Invalid REPEATS value '{clean_value}'",
                    line_num, command,
                    ["REPEATS must be a positive integer (e.g., REPEATS:1, REPEATS:10)"]
                ))
                return False
        
        # Validate PULSE field
        elif key == 'PULSE':
            if value:  # PULSE can be empty
                if not self._validate_pulse_format(value, command, line_num):
                    return False
        
        # Validate RAMP field
        elif key == 'RAMP':
            ramp_validator = RampValidator()
            if not ramp_validator.validate(value, line_num, command):
                self.errors.extend(ramp_validator.errors)
                return False
        
        return True
    
    def _validate_status_values(self, value: str, command: str, line_num: int) -> bool:
        """Validate STATUS values (comma-separated integers 0-4095 or floats 0-1)."""
        try:
            values = [v.strip() for v in value.split(',')]
            for v in values:
                if not v:
                    continue
                num = float(v)
                if '.' in v:
                    # Float value (0.0-1.0)
                    if not (0.0 <= num <= 1.0):
                        self.errors.append(SyntaxValidationError(
                            f"STATUS float value '{v}' out of range",
                            line_num, command,
                            ["Float values must be 0.0-1.0 (normalized intensity)"]
                        ))
                        return False
                else:
                    # Integer value (0-4095 for DAC, 0-255 for PWM, 0-1 for binary)
                    int_val = int(num)
                    if int_val < 0:
                        self.errors.append(SyntaxValidationError(
                            f"STATUS value '{v}' cannot be negative",
                            line_num, command,
                            ["Use 0-4095 for DAC, 0-255 for PWM, 0-1 for binary"]
                        ))
                        return False
                    if int_val > 4095:
                        self.warnings.append(
                            f"Line {line_num}: STATUS value {int_val} exceeds max DAC value (4095)"
                        )
            return True
        except ValueError:
            self.errors.append(SyntaxValidationError(
                f"Invalid STATUS values '{value}'",
                line_num, command,
                ["STATUS must be comma-separated numbers (e.g., STATUS:0,255 or STATUS:0.0,1.0)"]
            ))
            return False
    
    def _validate_time_values(self, value: str, command: str, line_num: int, 
                               pattern_id: int = None) -> bool:
        """Validate TIME values (comma-separated positive numbers).
        
        Note: TIME_MS:0 is allowed for PATTERN:0 (wait patterns).
        """
        try:
            values = [v.strip() for v in value.split(',')]
            for v in values:
                if not v:
                    continue
                num = float(v)
                # Allow TIME_MS:0 for wait patterns (PATTERN:0)
                if num < 0:
                    self.errors.append(SyntaxValidationError(
                        f"TIME value '{v}' cannot be negative",
                        line_num, command,
                        ["Time values must be >= 0"]
                    ))
                    return False
                if num == 0 and pattern_id != 0:
                    self.warnings.append(
                        f"Line {line_num}: TIME value of 0 (only valid for PATTERN:0 wait patterns)"
                    )
            return True
        except ValueError:
            self.errors.append(SyntaxValidationError(
                f"Invalid TIME values '{value}'",
                line_num, command,
                ["TIME must be comma-separated positive numbers"]
            ))
            return False
    
    def _validate_pulse_format(self, value: str, command: str, line_num: int) -> bool:
        """
        Validate PULSE format: T<period>pw<width>,T<period>pw<width>,...
        """
        items = value.split(',')
        pulse_pattern = re.compile(r'^T(\d+)pw(\d+)$')
        
        for i, item in enumerate(items):
            item = item.strip()
            if not item:
                continue  # Empty item allowed (trailing comma)
            
            match = pulse_pattern.match(item)
            if not match:
                self.errors.append(SyntaxValidationError(
                    f"Invalid PULSE format: '{item}'",
                    line_num, command,
                    [
                        "Format: T<period>pw<width>",
                        "Example: T1000pw50 (1000ms period, 50ms pulse width)",
                        "Use T0pw0 for no pulse"
                    ]
                ))
                return False
            
            period = int(match.group(1))
            pw = int(match.group(2))
            
            if period > 0 and pw > period:
                self.warnings.append(
                    f"Line {line_num}: Pulse width ({pw}ms) exceeds period ({period}ms)"
                )
        
        return True


# ==============================================================================
# RAMP SEGMENT VALIDATOR
# ==============================================================================

class RampValidator:
    """Validates RAMP segment syntax."""
    
    # Regex for different RAMP segment formats
    # Support both integer (0,255) and float (0.0,1.0) PWM values
    STANDARD_SEGMENT = re.compile(r'^\(([LCIO]):([\d.]+),([\d.]+),(\d+)\)$')
    X_MODE_SEGMENT = re.compile(r'^\(X:([\d.]+),([\d.]+),(\d+)\|([\d.]+),([\d.]+)\)$')
    X_MODE_SHORT = re.compile(r'^\(X:(\d+)\|([\d.]+),([\d.]+)\)$')  # (X:duration|t_start,t_end)
    F_MODE_SEGMENT = re.compile(r'^\(F:(\w+),(\d+)\)$')
    
    def __init__(self):
        self.errors: List[SyntaxValidationError] = []
        self.warnings: List[str] = []
    
    def validate(self, ramp_str: str, line_num: int, command: str = None) -> bool:
        """
        Validate a complete RAMP specification.
        
        Args:
            ramp_str: The RAMP value (everything after 'RAMP:')
            line_num: Line number in file
            command: Full command for error context
            
        Returns:
            True if valid, False if errors found
        """
        if not ramp_str:
            self.errors.append(SyntaxValidationError(
                "Empty RAMP specification",
                line_num, command,
                ["RAMP must have at least one segment: RAMP:(L:0,255,5000)"]
            ))
            return False
        
        # Parse segments - they should be comma-separated parenthesized groups
        segments = self._split_segments(ramp_str)
        
        if not segments:
            self.errors.append(SyntaxValidationError(
                "No valid RAMP segments found",
                line_num, command,
                ["Segments must be wrapped in parentheses: (MODE:params)"]
            ))
            return False
        
        for segment in segments:
            if not self._validate_segment(segment, line_num, command):
                return False
        
        return True
    
    def _split_segments(self, ramp_str: str) -> List[str]:
        """Split RAMP string into individual segments."""
        segments = []
        depth = 0
        current = ""
        
        for char in ramp_str:
            if char == '(':
                depth += 1
                current += char
            elif char == ')':
                depth -= 1
                current += char
                if depth == 0:
                    segments.append(current.strip())
                    current = ""
            elif char == ',' and depth == 0:
                # Skip commas between segments
                continue
            else:
                current += char
        
        # Filter empty segments
        return [s for s in segments if s]
    
    def _validate_segment(self, segment: str, line_num: int, command: str) -> bool:
        """Validate a single RAMP segment."""
        
        # Check basic structure
        if not segment.startswith('(') or not segment.endswith(')'):
            self.errors.append(SyntaxValidationError(
                f"RAMP segment missing parentheses: '{segment}'",
                line_num, command,
                ["Segments must be: (MODE:params)", "Example: (L:0,255,5000)"]
            ))
            return False
        
        # Extract content
        content = segment[1:-1]  # Remove parentheses
        
        if ':' not in content:
            self.errors.append(SyntaxValidationError(
                f"RAMP segment missing mode separator: '{segment}'",
                line_num, command,
                ["Format: (MODE:params)", "Modes: L, C, I, O, X, F"]
            ))
            return False
        
        mode = content.split(':')[0].upper()
        
        # Check for typos in mode
        if mode not in VALID_RAMP_MODES:
            suggestions = FuzzyMatcher.find_similar(mode, VALID_RAMP_MODES)
            if not suggestions:
                suggestions = list(VALID_RAMP_MODES)
            self.errors.append(SyntaxValidationError(
                f"Invalid RAMP mode '{mode}'",
                line_num, command,
                suggestions
            ))
            return False
        
        # Validate based on mode
        if mode == 'F':
            return self._validate_f_mode(segment, line_num, command)
        elif mode == 'X':
            return self._validate_x_mode(segment, line_num, command)
        else:
            return self._validate_standard_mode(segment, mode, line_num, command)
    
    def _validate_standard_mode(self, segment: str, mode: str, 
                                 line_num: int, command: str) -> bool:
        """Validate L, C, I, O mode segments."""
        match = self.STANDARD_SEGMENT.match(segment)
        if not match:
            self.errors.append(SyntaxValidationError(
                f"Invalid {mode} mode format: '{segment}'",
                line_num, command,
                [
                    f"Format: ({mode}:start,end,duration)",
                    f"Example: ({mode}:0,255,5000) or ({mode}:0.0,1.0,5000)",
                    "start/end: 0-4095 (int) or 0.0-1.0 (float), duration: milliseconds"
                ]
            ))
            return False
        
        start = float(match.group(2))
        end = float(match.group(3))
        duration = int(match.group(4))
        
        # Validate ranges - support both integer (0-4095) and float (0.0-1.0)
        if start < 0:
            self.warnings.append(f"Line {line_num}: Start PWM {start} cannot be negative")
        elif start > 1.0 and start > 4095:
            self.warnings.append(f"Line {line_num}: Start PWM {start} may be out of range (0-4095 or 0.0-1.0)")
        if end < 0:
            self.warnings.append(f"Line {line_num}: End PWM {end} cannot be negative")
        elif end > 1.0 and end > 4095:
            self.warnings.append(f"Line {line_num}: End PWM {end} may be out of range (0-4095 or 0.0-1.0)")
        if duration <= 0:
            self.errors.append(SyntaxValidationError(
                f"Duration must be positive: {duration}ms",
                line_num, command,
                ["Duration must be > 0 milliseconds"]
            ))
            return False
        
        return True
    
    def _validate_x_mode(self, segment: str, line_num: int, command: str) -> bool:
        """Validate X mode segment with custom t-range."""
        # Try full format first
        match = self.X_MODE_SEGMENT.match(segment)
        if match:
            t_start = float(match.group(4))
            t_end = float(match.group(5))
        else:
            # Try short format
            match = self.X_MODE_SHORT.match(segment)
            if match:
                t_start = float(match.group(2))
                t_end = float(match.group(3))
            else:
                self.errors.append(SyntaxValidationError(
                    f"Invalid X mode format: '{segment}'",
                    line_num, command,
                    [
                        "Format: (X:start,end,duration|t_start,t_end)",
                        "Or: (X:duration|t_start,t_end)",
                        "Example: (X:0,255,5000|0,2)",
                        "t_start/t_end: 0.0-2.0 (cosine curve position)"
                    ]
                ))
                return False
        
        # Validate t-range
        if not (0.0 <= t_start <= 2.0):
            self.errors.append(SyntaxValidationError(
                f"t_start {t_start} out of range",
                line_num, command,
                ["t_start must be 0.0-2.0"]
            ))
            return False
        if not (0.0 <= t_end <= 2.0):
            self.errors.append(SyntaxValidationError(
                f"t_end {t_end} out of range",
                line_num, command,
                ["t_end must be 0.0-2.0"]
            ))
            return False
        
        return True
    
    def _validate_f_mode(self, segment: str, line_num: int, command: str) -> bool:
        """Validate F mode segment with custom function."""
        match = self.F_MODE_SEGMENT.match(segment)
        if not match:
            self.errors.append(SyntaxValidationError(
                f"Invalid F mode format: '{segment}'",
                line_num, command,
                [
                    "Format: (F:function_name,duration)",
                    "Example: (F:heartbeat,2000)",
                    f"Built-in functions: {', '.join(sorted(VALID_F_MODE_FUNCTIONS))}"
                ]
            ))
            return False
        
        func_name = match.group(1)
        duration = int(match.group(2))
        
        # Check if function is known
        if func_name.lower() not in VALID_F_MODE_FUNCTIONS:
            suggestions = FuzzyMatcher.find_similar(func_name.lower(), VALID_F_MODE_FUNCTIONS)
            if suggestions:
                self.warnings.append(
                    f"Line {line_num}: Unknown function '{func_name}'. "
                    f"Did you mean: {', '.join(suggestions)}? "
                    "(Custom functions must be defined in Arduino code)"
                )
            else:
                self.warnings.append(
                    f"Line {line_num}: Unknown function '{func_name}'. "
                    "Make sure it's defined in custom_easing.h on Arduino."
                )
        
        if duration <= 0:
            self.errors.append(SyntaxValidationError(
                f"Duration must be positive: {duration}ms",
                line_num, command,
                ["Duration must be > 0 milliseconds"]
            ))
            return False
        
        return True


# ==============================================================================
# DICTIONARY BLOCK VALIDATOR
# ==============================================================================

class DictBlockValidator:
    """Validates START_TIME, WAIT_STATUS, WAIT_PULSE, CALIBRATION_FACTOR blocks."""
    
    def __init__(self):
        self.errors: List[SyntaxValidationError] = []
        self.warnings: List[str] = []
    
    def validate_start_time(self, block_lines: List[Tuple[int, str]]) -> bool:
        """Validate START_TIME block."""
        return self._validate_dict_block(block_lines, 'START_TIME', 
                                         self._validate_start_time_value)
    
    def validate_wait_status(self, block_lines: List[Tuple[int, str]]) -> bool:
        """Validate WAIT_STATUS block."""
        return self._validate_dict_block(block_lines, 'WAIT_STATUS',
                                         self._validate_wait_status_value)
    
    def validate_wait_pulse(self, block_lines: List[Tuple[int, str]]) -> bool:
        """Validate WAIT_PULSE block."""
        return self._validate_dict_block(block_lines, 'WAIT_PULSE',
                                         self._validate_wait_pulse_value)
    
    def validate_loop(self, block_lines: List[Tuple[int, str]]) -> bool:
        """Validate LOOP block."""
        return self._validate_dict_block(block_lines, 'LOOP',
                                         self._validate_loop_value)
    
    def validate_calibration_factor(self, line: str, line_num: int) -> bool:
        """Validate CALIBRATION_FACTOR line."""
        match = re.match(r'^\s*CALIBRATION_FACTOR\s*:\s*([\d.]+)\s*$', line)
        if not match:
            self.errors.append(SyntaxValidationError(
                "Invalid CALIBRATION_FACTOR format",
                line_num, line,
                ["Format: CALIBRATION_FACTOR: <float>", "Example: CALIBRATION_FACTOR: 1.00131"]
            ))
            return False
        
        try:
            factor = float(match.group(1))
            if factor <= 0:
                self.errors.append(SyntaxValidationError(
                    f"CALIBRATION_FACTOR must be positive: {factor}",
                    line_num, line,
                    ["Typical values: 0.99 - 1.01"]
                ))
                return False
            if factor < 0.9 or factor > 1.1:
                self.warnings.append(
                    f"Line {line_num}: CALIBRATION_FACTOR {factor} is unusual. "
                    "Typical range is 0.99-1.01"
                )
        except ValueError:
            self.errors.append(SyntaxValidationError(
                f"Invalid CALIBRATION_FACTOR value",
                line_num, line,
                ["Must be a decimal number (e.g., 1.00131)"]
            ))
            return False
        
        return True
    
    def _validate_dict_block(self, block_lines: List[Tuple[int, str]], 
                             block_name: str, value_validator) -> bool:
        """Generic dictionary block validator."""
        if not block_lines:
            return True
        
        # Join lines and try to parse as Python dict
        full_text = ""
        first_line_num = block_lines[0][0]
        
        for line_num, line in block_lines:
            # Extract content after block name
            if block_name + ':' in line:
                _, _, content = line.partition(block_name + ':')
                full_text += content.strip()
            else:
                full_text += line.strip()
        
        # Try to parse as dict
        try:
            # Replace single quotes for eval safety check
            if '{' not in full_text or '}' not in full_text:
                self.errors.append(SyntaxValidationError(
                    f"{block_name} must be a dictionary",
                    first_line_num, block_lines[0][1],
                    [f"Format: {block_name}: {{'CH1': value, 'CH2': value}}"]
                ))
                return False
            
            # Basic validation - check for common issues
            self._check_dict_syntax(full_text, block_name, first_line_num, block_lines[0][1])
            
            # Try to eval (with safety measures)
            import ast
            parsed = ast.literal_eval(full_text)
            
            if not isinstance(parsed, dict):
                self.errors.append(SyntaxValidationError(
                    f"{block_name} must be a dictionary",
                    first_line_num, block_lines[0][1],
                    [f"Format: {block_name}: {{'CH1': value}}"]
                ))
                return False
            
            # Validate each entry
            for key, value in parsed.items():
                # Check channel name format
                if not re.match(r'^CH\d+$', key):
                    self.warnings.append(
                        f"Line {first_line_num}: Unusual channel name '{key}'. "
                        "Expected format: CH1, CH2, etc."
                    )
                
                # Validate value
                if not value_validator(key, value, first_line_num, full_text):
                    return False
            
            return True
            
        except (SyntaxError, ValueError) as e:
            self.errors.append(SyntaxValidationError(
                f"Invalid {block_name} syntax: {e}",
                first_line_num, full_text,
                [
                    "Check for missing quotes around channel names",
                    "Check for missing commas between entries",
                    "Check for matching braces {}"
                ]
            ))
            return False
    
    def _check_dict_syntax(self, text: str, block_name: str, 
                           line_num: int, line_content: str):
        """Check for common dictionary syntax issues."""
        # Check for double quotes (should be single)
        if '"CH' in text:
            self.warnings.append(
                f"Line {line_num}: Use single quotes for channel names: 'CH1' not \"CH1\""
            )
        
        # Check for missing quotes
        if re.search(r'[{,]\s*CH\d+\s*:', text):
            self.errors.append(SyntaxValidationError(
                "Channel names must be quoted",
                line_num, line_content,
                ["Use 'CH1': value, not CH1: value"]
            ))
    
    def _validate_start_time_value(self, key: str, value: Any, 
                                   line_num: int, context: str) -> bool:
        """Validate a single START_TIME value."""
        if isinstance(value, (int, float)):
            # Countdown in seconds
            if value < 0:
                self.errors.append(SyntaxValidationError(
                    f"START_TIME countdown cannot be negative: {value}",
                    line_num, context,
                    ["Use positive seconds for countdown, or time string like '21:00'"]
                ))
                return False
        elif isinstance(value, str):
            # Time string
            time_patterns = [
                r'^\d{1,2}:\d{2}$',          # HH:MM
                r'^\d{1,2}:\d{2}:\d{2}$',    # HH:MM:SS
                r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'  # YYYY-MM-DD HH:MM:SS
            ]
            if not any(re.match(p, value) for p in time_patterns):
                self.errors.append(SyntaxValidationError(
                    f"Invalid START_TIME format: '{value}'",
                    line_num, context,
                    [
                        "Valid formats: '21:00', '21:00:30', '2025-01-15 21:00:00'",
                        "Or use countdown in seconds: 120"
                    ]
                ))
                return False
        else:
            self.errors.append(SyntaxValidationError(
                f"Invalid START_TIME value type for {key}",
                line_num, context,
                ["Must be string (time) or number (countdown seconds)"]
            ))
            return False
        return True
    
    def _validate_wait_status_value(self, key: str, value: Any,
                                    line_num: int, context: str) -> bool:
        """Validate a single WAIT_STATUS value."""
        if isinstance(value, (int, float)):
            if value not in (0, 1, 0.0, 1.0):
                # Allow float values for PWM wait status
                if not (0.0 <= float(value) <= 1.0):
                    self.errors.append(SyntaxValidationError(
                        f"WAIT_STATUS value must be 0, 1, or 0.0-1.0: {value}",
                        line_num, context,
                        ["0 = OFF during wait, 1 = ON during wait, 0.0-1.0 = PWM intensity"]
                    ))
                    return False
        else:
            self.errors.append(SyntaxValidationError(
                f"WAIT_STATUS value must be a number: {value}",
                line_num, context,
                ["Use 0 or 1 (or 0.0-1.0 for PWM intensity)"]
            ))
            return False
        return True
    
    def _validate_loop_value(self, key: str, value: Any,
                             line_num: int, context: str) -> bool:
        """Validate a single LOOP value."""
        if isinstance(value, (int, float)):
            if value not in (0, 1, 0.0, 1.0):
                self.errors.append(SyntaxValidationError(
                    f"LOOP value must be 0 or 1: {value}",
                    line_num, context,
                    ["0 = stop after all patterns, 1 = loop forever"]
                ))
                return False
        else:
            self.errors.append(SyntaxValidationError(
                f"LOOP value must be a number: {value}",
                line_num, context,
                ["Use 0 (stop) or 1 (loop forever)"]
            ))
            return False
        return True
    
    def _validate_wait_pulse_value(self, key: str, value: Any,
                                   line_num: int, context: str) -> bool:
        """Validate a single WAIT_PULSE value.
        
        Supports two formats:
        1. {'period': 2000, 'pw': 100} - period in ms, pulse width in ms
        2. {'frequency': 0.5, 'pulse_width': 100} - frequency in Hz, pulse width in ms
        """
        if not isinstance(value, dict):
            self.errors.append(SyntaxValidationError(
                f"WAIT_PULSE value must be a dict: {value}",
                line_num, context,
                ["Format: {'period': 2000, 'pw': 100}",
                 "Or: {'frequency': 0.5, 'pulse_width': 100}"]
            ))
            return False
        
        # Support both formats: period/pw OR frequency/pulse_width
        has_period_format = 'period' in value and 'pw' in value
        has_frequency_format = 'frequency' in value and 'pulse_width' in value
        
        if not has_period_format and not has_frequency_format:
            self.errors.append(SyntaxValidationError(
                f"WAIT_PULSE missing required keys",
                line_num, context,
                ["Must have 'period' and 'pw' keys",
                 "Or 'frequency' and 'pulse_width' keys",
                 "Format 1: {'period': 2000, 'pw': 100}",
                 "Format 2: {'frequency': 0.5, 'pulse_width': 100}"]
            ))
            return False
        
        # Get values based on format
        if has_frequency_format:
            freq = value.get('frequency', 0)
            pw = value.get('pulse_width', 0)
            if not isinstance(freq, (int, float)) or freq <= 0:
                self.errors.append(SyntaxValidationError(
                    f"WAIT_PULSE frequency must be positive: {freq}",
                    line_num, context,
                    ["Frequency is in Hz (e.g., 0.5 = 2 second period)"]
                ))
                return False
            period = 1000.0 / freq  # Convert to period for pw check
        else:
            period = value.get('period', 0)
            pw = value.get('pw', 0)
        
        if not isinstance(period, (int, float)) or period <= 0:
            self.errors.append(SyntaxValidationError(
                f"WAIT_PULSE period must be positive: {period}",
                line_num, context,
                ["Period is milliseconds (e.g., 2000 = 2 seconds)"]
            ))
            return False
        
        if not isinstance(pw, (int, float)) or pw < 0:
            self.errors.append(SyntaxValidationError(
                f"WAIT_PULSE pw must be non-negative: {pw}",
                line_num, context,
                ["Pulse width in milliseconds"]
            ))
            return False
        
        if pw > period:
            self.warnings.append(
                f"Line {line_num}: WAIT_PULSE pw ({pw}) exceeds period ({period})"
            )
        
        return True


# ==============================================================================
# MAIN PROTOCOL SYNTAX CHECKER
# ==============================================================================

class ProtocolSyntaxChecker:
    """
    Main syntax checker that orchestrates all validation.
    
    Usage:
        checker = ProtocolSyntaxChecker()
        is_valid, errors, warnings = checker.check_file('protocol.txt')
        
        if not is_valid:
            for error in errors:
                print(error)
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize the syntax checker.
        
        Args:
            strict_mode: If True, treat warnings as errors
        """
        self.strict_mode = strict_mode
        self.errors: List[SyntaxValidationError] = []
        self.warnings: List[str] = []
        self._reset()
    
    def _reset(self):
        """Reset state for new validation."""
        self.errors = []
        self.warnings = []
        self.channels_seen: Set[str] = set()
        self.patterns_seen: Dict[str, Set[int]] = {}  # CH -> set of pattern IDs
        self.has_start_time = False
        self.is_generated_file = False  # Track if file is generated output
    
    def check_file(self, filepath: str) -> Tuple[bool, List[str], List[str]]:
        """
        Check a protocol file for syntax errors.
        
        Args:
            filepath: Path to the protocol file (.txt or .xlsx)
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self._reset()
        path = Path(filepath)
        
        if not path.exists():
            self.errors.append(SyntaxValidationError(
                f"File not found: {filepath}"
            ))
            return False, [str(e) for e in self.errors], self.warnings
        
        # Detect generated command files (not meant for validation)
        filename = path.name
        if '_commands_' in filename or filename.endswith('_monitored.csv'):
            self.is_generated_file = True
            self.warnings.append(
                f"Skipping validation: '{filename}' appears to be a generated output file"
            )
            return True, [], self.warnings
        
        if path.suffix.lower() == '.xlsx':
            return self._check_excel_file(filepath)
        elif path.suffix.lower() == '.txt':
            return self._check_text_file(filepath)
        else:
            self.errors.append(SyntaxValidationError(
                f"Unsupported file format: {path.suffix}",
                suggestions=["Use .txt or .xlsx files"]
            ))
            return False, [str(e) for e in self.errors], self.warnings
    
    def check_string(self, content: str) -> Tuple[bool, List[str], List[str]]:
        """
        Check protocol content from a string (text format).
        
        Args:
            content: Protocol content as string
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self._reset()
        lines = content.split('\n')
        return self._check_text_lines(lines)
    
    def _check_text_file(self, filepath: str) -> Tuple[bool, List[str], List[str]]:
        """Check a text protocol file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return self._check_text_lines(lines)
        except Exception as e:
            self.errors.append(SyntaxValidationError(
                f"Error reading file: {e}"
            ))
            return False, [str(e) for e in self.errors], self.warnings
    
    def _check_text_lines(self, lines: List[str]) -> Tuple[bool, List[str], List[str]]:
        """Check text protocol lines."""
        pattern_validator = PatternValidator()
        dict_validator = DictBlockValidator()
        
        i = 0
        while i < len(lines):
            line_num = i + 1
            line = lines[i]
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                i += 1
                continue
            
            # Check for PATTERN commands
            if stripped.startswith('PATTERN:'):
                pattern_validator.validate_command(stripped, line_num)
                # Track channels
                ch_match = re.search(r'CH:(\d+)', stripped)
                if ch_match:
                    ch = f"CH{ch_match.group(1)}"
                    self.channels_seen.add(ch)
                i += 1
                continue
            
            # Check for dictionary blocks
            if any(stripped.startswith(f'{block}:') for block in VALID_DICT_BLOCKS):
                block_name = stripped.split(':')[0].strip()
                
                # Check for typos in block name
                if block_name.upper() not in VALID_DICT_BLOCKS:
                    suggestions = FuzzyMatcher.find_similar(
                        block_name, VALID_DICT_BLOCKS
                    )
                    self.errors.append(SyntaxValidationError(
                        f"Unknown block type '{block_name}'",
                        line_num, line,
                        suggestions if suggestions else list(VALID_DICT_BLOCKS)
                    ))
                    i += 1
                    continue
                
                if block_name.upper() == 'CALIBRATION_FACTOR':
                    dict_validator.validate_calibration_factor(stripped, line_num)
                    i += 1
                    continue
                
                # Collect multi-line dict block
                block_lines = [(line_num, stripped)]
                brace_count = stripped.count('{') - stripped.count('}')
                
                while brace_count > 0 and i + 1 < len(lines):
                    i += 1
                    next_line = lines[i]
                    block_lines.append((i + 1, next_line))
                    brace_count += next_line.count('{') - next_line.count('}')
                
                # Validate the block
                if block_name.upper() == 'START_TIME':
                    dict_validator.validate_start_time(block_lines)
                    self.has_start_time = True
                elif block_name.upper() == 'WAIT_STATUS':
                    dict_validator.validate_wait_status(block_lines)
                elif block_name.upper() == 'WAIT_PULSE':
                    dict_validator.validate_wait_pulse(block_lines)
                elif block_name.upper() == 'LOOP':
                    dict_validator.validate_loop(block_lines)
                
                i += 1
                continue
            
            # Unknown line - check for typos
            first_word = stripped.split(':')[0].split(';')[0].strip().upper()
            all_valid = VALID_PATTERN_FIELDS | VALID_DICT_BLOCKS
            suggestions = FuzzyMatcher.find_similar(first_word, all_valid)
            
            if suggestions:
                self.errors.append(SyntaxValidationError(
                    f"Unknown command or block",
                    line_num, line,
                    suggestions
                ))
            else:
                self.errors.append(SyntaxValidationError(
                    f"Unrecognized line",
                    line_num, line,
                    ["Lines must be PATTERN commands, dict blocks, or comments (#)"]
                ))
            
            i += 1
        
        # Collect all errors
        self.errors.extend(pattern_validator.errors)
        self.warnings.extend(pattern_validator.warnings)
        self.errors.extend(dict_validator.errors)
        self.warnings.extend(dict_validator.warnings)
        
        # Check for required elements
        if not self.has_start_time and self.channels_seen:
            self.errors.append(SyntaxValidationError(
                "Missing START_TIME block",
                suggestions=["Add START_TIME: {'CH1': 0} or similar"]
            ))
        
        is_valid = len(self.errors) == 0
        if self.strict_mode and self.warnings:
            is_valid = False
        
        return is_valid, [str(e) for e in self.errors], self.warnings
    
    def _check_excel_file(self, filepath: str) -> Tuple[bool, List[str], List[str]]:
        """Check an Excel protocol file."""
        try:
            import pandas as pd
        except ImportError:
            self.errors.append(SyntaxValidationError(
                "pandas required for Excel validation",
                suggestions=["pip install pandas openpyxl"]
            ))
            return False, [str(e) for e in self.errors], self.warnings
        
        try:
            xl = pd.ExcelFile(filepath)
            sheet_names = [s.lower() for s in xl.sheet_names]
            
            # Check required sheets
            if 'protocol' not in sheet_names:
                self.errors.append(SyntaxValidationError(
                    "Missing 'protocol' sheet",
                    suggestions=["Sheet name must be lowercase: 'protocol'"]
                ))
            
            if 'start_time' not in sheet_names:
                self.errors.append(SyntaxValidationError(
                    "Missing 'start_time' sheet",
                    suggestions=["Sheet name must be lowercase: 'start_time'"]
                ))
            
            # Validate protocol sheet if exists
            if 'protocol' in sheet_names:
                self._validate_excel_protocol_sheet(xl, filepath)
            
            # Validate start_time sheet if exists
            if 'start_time' in sheet_names:
                self._validate_excel_start_time_sheet(xl, filepath)
            
            # Validate calibration sheet if exists
            if 'calibration' in sheet_names:
                self._validate_excel_calibration_sheet(xl, filepath)
            
            is_valid = len(self.errors) == 0
            if self.strict_mode and self.warnings:
                is_valid = False
            
            return is_valid, [str(e) for e in self.errors], self.warnings
            
        except Exception as e:
            self.errors.append(SyntaxValidationError(
                f"Error reading Excel file: {e}"
            ))
            return False, [str(e) for e in self.errors], self.warnings
    
    def _validate_excel_protocol_sheet(self, xl, filepath: str):
        """Validate the protocol sheet in Excel file."""
        import pandas as pd
        
        # Find exact sheet name (case-insensitive)
        protocol_sheet = None
        for name in xl.sheet_names:
            if name.lower() == 'protocol':
                protocol_sheet = name
                break
        
        if protocol_sheet != 'protocol':
            self.warnings.append(
                f"Sheet name '{protocol_sheet}' should be lowercase 'protocol'"
            )
        
        df = pd.read_excel(filepath, sheet_name=protocol_sheet)
        columns = df.columns.tolist()
        
        # Check for channel columns
        channel_cols = {}
        for col in columns:
            col_upper = str(col).upper()
            match = re.match(r'^CH(\d+)_', col_upper)
            if match:
                ch_num = int(match.group(1))
                if ch_num not in channel_cols:
                    channel_cols[ch_num] = []
                channel_cols[ch_num].append(col)
        
        # Check channel numbering
        if channel_cols:
            ch_nums = sorted(channel_cols.keys())
            if ch_nums[0] != 1:
                self.errors.append(SyntaxValidationError(
                    "Channel numbers must start at 1",
                    suggestions=[f"Found: CH{ch_nums[0]}. Use CH1, CH2, etc."]
                ))
            
            for i, ch in enumerate(ch_nums):
                if i > 0 and ch != ch_nums[i-1] + 1:
                    self.errors.append(SyntaxValidationError(
                        f"Channel numbers must be continuous",
                        suggestions=[f"Gap between CH{ch_nums[i-1]} and CH{ch}"]
                    ))
        
        # Check for RAMP columns (not supported in Excel)
        for col in columns:
            if 'ramp' in str(col).lower():
                self.warnings.append(
                    f"Excel format does not support RAMP mode. "
                    f"Column '{col}' will be ignored. Use .txt format for RAMP."
                )
    
    def _validate_excel_start_time_sheet(self, xl, filepath: str):
        """Validate the start_time sheet in Excel file."""
        import pandas as pd
        
        # Find exact sheet name
        start_time_sheet = None
        for name in xl.sheet_names:
            if name.lower() == 'start_time':
                start_time_sheet = name
                break
        
        if start_time_sheet != 'start_time':
            self.warnings.append(
                f"Sheet name '{start_time_sheet}' should be lowercase 'start_time'"
            )
        
        df = pd.read_excel(filepath, sheet_name=start_time_sheet)
        
        # Basic structure validation
        if df.empty:
            self.errors.append(SyntaxValidationError(
                "start_time sheet is empty"
            ))
    
    def _validate_excel_calibration_sheet(self, xl, filepath: str):
        """Validate the calibration sheet in Excel file."""
        import pandas as pd
        
        # Find exact sheet name
        calib_sheet = None
        for name in xl.sheet_names:
            if name.lower() == 'calibration':
                calib_sheet = name
                break
        
        if calib_sheet != 'calibration':
            self.warnings.append(
                f"Sheet name '{calib_sheet}' should be lowercase 'calibration'"
            )


# ==============================================================================
# COMMAND LINE INTERFACE
# ==============================================================================

def print_results(is_valid: bool, errors: List[str], warnings: List[str], 
                  verbose: bool = False):
    """Print validation results in a formatted way."""
    
    # Header
    print("\n" + "=" * 70)
    print("PROTOCOL SYNTAX CHECK RESULTS")
    print("=" * 70)
    
    # Status
    if is_valid:
        print("\n✅ VALID - No syntax errors found")
    else:
        print(f"\n❌ INVALID - {len(errors)} error(s) found")
    
    # Errors
    if errors:
        print("\n" + "-" * 70)
        print("ERRORS:")
        print("-" * 70)
        for i, error in enumerate(errors, 1):
            print(f"\n{i}. {error}")
    
    # Warnings
    if warnings:
        print("\n" + "-" * 70)
        print("WARNINGS:")
        print("-" * 70)
        for i, warning in enumerate(warnings, 1):
            print(f"\n{i}. {warning}")
    
    print("\n" + "=" * 70)
    
    # Summary
    if is_valid and not warnings:
        print("Protocol is ready for compilation.")
    elif is_valid and warnings:
        print("Protocol is valid but has warnings. Review before running.")
    else:
        print("Fix errors before compiling the protocol.")
    
    print("=" * 70 + "\n")


def main():
    """Command line entry point."""
    parser = argparse.ArgumentParser(
        description='Validate Light Controller protocol syntax',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python syntax_check.py examples/1min_test.txt
    python syntax_check.py protocol.xlsx --strict
    python syntax_check.py *.txt --verbose
        """
    )
    
    parser.add_argument(
        'files', nargs='+',
        help='Protocol file(s) to check (.txt or .xlsx)'
    )
    parser.add_argument(
        '--strict', '-s', action='store_true',
        help='Treat warnings as errors'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Show detailed output'
    )
    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help='Only show errors, no summary'
    )
    
    args = parser.parse_args()
    
    # Process each file
    all_valid = True
    checker = ProtocolSyntaxChecker(strict_mode=args.strict)
    
    for filepath in args.files:
        if not args.quiet:
            print(f"\nChecking: {filepath}")
        
        is_valid, errors, warnings = checker.check_file(filepath)
        
        if not args.quiet:
            print_results(is_valid, errors, warnings, args.verbose)
        elif errors or (args.verbose and warnings):
            for error in errors:
                print(f"ERROR: {error}")
            if args.verbose:
                for warning in warnings:
                    print(f"WARNING: {warning}")
        
        if not is_valid:
            all_valid = False
    
    # Exit code
    sys.exit(0 if all_valid else 1)


# ==============================================================================
# MODULE INTERFACE
# ==============================================================================

def check_protocol(filepath: str, strict: bool = False) -> Tuple[bool, List[str], List[str]]:
    """
    Convenience function for checking a protocol file.
    
    Args:
        filepath: Path to protocol file
        strict: Treat warnings as errors
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    checker = ProtocolSyntaxChecker(strict_mode=strict)
    return checker.check_file(filepath)


def check_protocol_string(content: str, strict: bool = False) -> Tuple[bool, List[str], List[str]]:
    """
    Convenience function for checking protocol content from string.
    
    Args:
        content: Protocol content as string
        strict: Treat warnings as errors
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    checker = ProtocolSyntaxChecker(strict_mode=strict)
    return checker.check_string(content)


if __name__ == '__main__':
    main()
