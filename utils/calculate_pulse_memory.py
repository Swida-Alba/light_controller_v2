"""
Arduino Memory Calculator for Pulse Arrays

Calculate memory usage and savings based on configuration.
"""

def calculate_pulse_memory(max_channels=8, max_patterns=10, pattern_length=4):
    """
    Calculate pulse array memory usage.
    
    Args:
        max_channels: Number of channels (MAX_CHANNEL_NUM)
        max_patterns: Maximum patterns per channel (MAX_PATTERN_NUM)
        pattern_length: Elements per pattern (PATTERN_LENGTH)
        
    Returns:
        dict with memory breakdown
    """
    # Size of unsigned long in bytes
    ULONG_SIZE = 4
    # Size of bool in bytes
    BOOL_SIZE = 1
    
    # Pulse arrays per channel
    period_per_channel = max_patterns * pattern_length * ULONG_SIZE
    pw_per_channel = max_patterns * pattern_length * ULONG_SIZE
    total_per_channel = period_per_channel + pw_per_channel
    
    # Total for all channels
    period_total = period_per_channel * max_channels
    pw_total = pw_per_channel * max_channels
    arrays_total = total_per_channel * max_channels
    
    # State variables
    pulse_state_size = max_channels * BOOL_SIZE
    next_pulse_time_size = max_channels * ULONG_SIZE
    state_vars_total = pulse_state_size + next_pulse_time_size
    
    # Grand total
    grand_total = arrays_total + state_vars_total
    
    return {
        'config': {
            'max_channels': max_channels,
            'max_patterns': max_patterns,
            'pattern_length': pattern_length
        },
        'per_channel': {
            'period_array': period_per_channel,
            'pulse_width_array': pw_per_channel,
            'total': total_per_channel
        },
        'all_channels': {
            'period_arrays': period_total,
            'pulse_width_arrays': pw_total,
            'arrays_total': arrays_total
        },
        'state_variables': {
            'pulse_state': pulse_state_size,
            'next_pulse_time': next_pulse_time_size,
            'total': state_vars_total
        },
        'grand_total_bytes': grand_total,
        'grand_total_kb': grand_total / 1024.0
    }

def print_memory_report(config):
    """Print formatted memory report."""
    print("="*70)
    print("Arduino Pulse Memory Calculator")
    print("="*70)
    
    cfg = config['config']
    print(f"\nConfiguration:")
    print(f"  MAX_CHANNEL_NUM:  {cfg['max_channels']}")
    print(f"  MAX_PATTERN_NUM:  {cfg['max_patterns']}")
    print(f"  PATTERN_LENGTH:   {cfg['pattern_length']}")
    
    per_ch = config['per_channel']
    print(f"\nMemory Per Channel:")
    print(f"  period[{cfg['max_patterns']}][{cfg['pattern_length']}]:      {per_ch['period_array']:>6} bytes")
    print(f"  pulse_width[{cfg['max_patterns']}][{cfg['pattern_length']}]: {per_ch['pulse_width_array']:>6} bytes")
    print(f"  {'─' * 40}")
    print(f"  Total per channel:     {per_ch['total']:>6} bytes")
    
    all_ch = config['all_channels']
    print(f"\nMemory for All {cfg['max_channels']} Channels:")
    print(f"  period arrays:         {all_ch['period_arrays']:>6} bytes")
    print(f"  pulse_width arrays:    {all_ch['pulse_width_arrays']:>6} bytes")
    print(f"  {'─' * 40}")
    print(f"  Arrays total:          {all_ch['arrays_total']:>6} bytes")
    
    state = config['state_variables']
    print(f"\nState Variables:")
    print(f"  pulseState[{cfg['max_channels']}]:        {state['pulse_state']:>6} bytes")
    print(f"  nextPulseTime[{cfg['max_channels']}]:     {state['next_pulse_time']:>6} bytes")
    print(f"  {'─' * 40}")
    print(f"  State vars total:      {state['total']:>6} bytes")
    
    print(f"\n{'='*70}")
    print(f"TOTAL PULSE MEMORY:    {config['grand_total_bytes']:>6} bytes ({config['grand_total_kb']:.2f} KB)")
    print(f"{'='*70}")
    
    print(f"\nMemory Savings with PULSE_MODE_COMPILE = 0:")
    print(f"  ✅ Saves {config['grand_total_bytes']} bytes (~{config['grand_total_kb']:.1f} KB)")
    
    # Arduino Due context
    if cfg['max_channels'] <= 16:  # Reasonable Arduino Due config
        print(f"\nArduino Due (96 KB SRAM):")
        pattern_with_pulse = estimate_total_pattern_memory(cfg, with_pulse=True)
        pattern_no_pulse = estimate_total_pattern_memory(cfg, with_pulse=False)
        system_overhead = 5 * 1024  # ~5KB for system
        
        available_with = 96 * 1024 - system_overhead - pattern_with_pulse
        available_without = 96 * 1024 - system_overhead - pattern_no_pulse
        
        print(f"  With pulse arrays:    {available_with/1024:.1f} KB available for user")
        print(f"  Without pulse arrays: {available_without/1024:.1f} KB available for user")
        print(f"  Gain:                 {(available_without-available_with)/1024:.1f} KB more")

def estimate_total_pattern_memory(cfg, with_pulse=True):
    """Estimate total pattern structure memory."""
    ch = cfg['max_channels']
    pat = cfg['max_patterns']
    pl = cfg['pattern_length']
    
    # Base arrays (always present)
    status = ch * pat * pl * 1       # byte
    time_ms = ch * pat * pl * 4      # unsigned long
    repeats = ch * pat * 4           # int
    pattern_length = ch * pat * 4    # int
    pattern_num = ch * 4             # int
    
    base_total = status + time_ms + repeats + pattern_length + pattern_num
    
    if with_pulse:
        period = ch * pat * pl * 4       # unsigned long
        pulse_width = ch * pat * pl * 4  # unsigned long
        pulse_state = ch * 1             # bool
        next_pulse_time = ch * 4         # unsigned long
        pulse_total = period + pulse_width + pulse_state + next_pulse_time
        return base_total + pulse_total
    else:
        return base_total

def compare_configurations():
    """Compare different configurations."""
    configs = [
        ("Default (8 ch, 10 pat, 4 len)", 8, 10, 4),
        ("Large (16 ch, 20 pat, 8 len)", 16, 20, 8),
        ("Small (4 ch, 5 pat, 4 len)", 4, 5, 4),
        ("Huge (32 ch, 10 pat, 4 len)", 32, 10, 4),
    ]
    
    print("\n" + "="*70)
    print("Configuration Comparison")
    print("="*70)
    print(f"{'Configuration':<35} {'Pulse Memory':<15} {'Savings':<15}")
    print("─"*70)
    
    for name, ch, pat, pl in configs:
        mem = calculate_pulse_memory(ch, pat, pl)
        print(f"{name:<35} {mem['grand_total_bytes']:>6} bytes    {mem['grand_total_kb']:>6.2f} KB")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) == 4:
        # Custom configuration
        try:
            ch = int(sys.argv[1])
            pat = int(sys.argv[2])
            pl = int(sys.argv[3])
            print(f"\nCustom Configuration: CH={ch}, PAT={pat}, LEN={pl}\n")
            mem = calculate_pulse_memory(ch, pat, pl)
            print_memory_report(mem)
        except ValueError:
            print("Usage: python calculate_pulse_memory.py <channels> <patterns> <length>")
            print("Example: python calculate_pulse_memory.py 8 10 4")
            sys.exit(1)
    else:
        # Default configuration
        print("\nDefault Configuration Analysis\n")
        mem = calculate_pulse_memory()
        print_memory_report(mem)
        
        # Show comparisons
        compare_configurations()
        
        print("\n" + "="*70)
        print("Usage for custom config:")
        print("  python calculate_pulse_memory.py <channels> <patterns> <length>")
        print("Example:")
        print("  python calculate_pulse_memory.py 16 20 8")
        print("="*70)
