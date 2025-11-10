# 📁 Output at Protocol Path

## Overview

All generated files (commands and visualizations) are now saved **at the same location as your protocol file** with matching timestamps for easy pairing.

## File Naming Convention

```
{protocol_name}_commands_{timestamp}.txt
{protocol_name}_commands_{timestamp}.html
```

### Example

If your protocol file is:
```
examples/my_experiment.txt
```

Generated files will be:
```
examples/my_experiment_commands_20251108205626.txt   # Commands
examples/my_experiment_commands_20251108205626.html  # Visualization
```

**Same timestamp** = Files that belong together! 🎯

## Location Benefits

### ✅ Advantages

1. **Organized by Experiment**
   - All related files in one place
   - Protocol + Commands + Visualization together

2. **Easy to Archive**
   - Just copy the folder
   - Everything you need in one location

3. **Simple Cleanup**
   - Delete old experiments easily
   - No scattered files

4. **Version Control Friendly**
   - Keep protocol files in git
   - Add `*_commands_*.txt` and `*_commands_*.html` to `.gitignore`

### Example Directory Structure

```
my_project/
├── protocols/
│   ├── experiment1.txt
│   ├── experiment1_commands_20251108120000.txt
│   ├── experiment1_commands_20251108120000.html
│   ├── experiment2.txt
│   ├── experiment2_commands_20251108130000.txt
│   └── experiment2_commands_20251108130000.html
│
└── archive/
    └── 2025-11-08_important_results/
        ├── experiment1.txt
        ├── experiment1_commands_20251108120000.txt
        └── experiment1_commands_20251108120000.html
```

## Real-Time Visualization

### Auto-Refresh Feature ⚡

The HTML visualization automatically refreshes **every 5 seconds** when a protocol is running with a start time.

#### How It Works

1. **When executing protocol** (`protocol_parser.py`):
   ```python
   start_time = datetime.now()  # Capture when protocol starts
   # HTML shows current position on timeline
   # Auto-refreshes every 5 seconds
   ```

2. **When previewing protocol** (`preview_protocol.py`):
   ```python
   # No start time set
   # HTML shows structure only (no real-time tracking)
   # Still auto-refreshes (for consistency)
   ```

### Visual Indicators

The HTML visualization shows:

- 🟢 **Green LED** = Channel currently ON
- ⚫ **Gray LED** = Channel currently OFF  
- 🟠 **Orange LED (pulsing)** = Channel pulsing
- 🔴 **Red line** = Current position marker on timeline

### Current Status Panel

Located at the top of the visualization:

```
┌─────────────────────────────────────────┐
│ 🔴 LIVE STATUS                          │
│ Current Time: 2025-11-08 20:56:30       │
│                                         │
│ 🟢 CH1: ON   (Pattern 2, Cycle 5/10)   │
│ ⚫ CH2: OFF  (Pattern 1, Cycle 3/8)    │
│ 🟠 CH3: PULSING (10Hz, DC=50%)         │
│ ✓  CH4: Completed                       │
└─────────────────────────────────────────┘
```

## Usage Examples

### 1. Preview Protocol (No Hardware)

```bash
python preview_protocol.py protocols/my_experiment.txt
```

**Generated:**
- `protocols/my_experiment_commands_20251108205626.txt`
- `protocols/my_experiment_commands_20251108205626.html`

**Visualization shows:**
- Protocol structure
- Timeline visualization
- No real-time tracking (no start time)

### 2. Execute Protocol (With Arduino)

```bash
python protocol_parser.py
# Select: protocols/my_experiment.txt
```

**Generated:**
- `protocols/my_experiment_commands_20251108210530.txt`
- `protocols/my_experiment_commands_20251108210530.html`

**Visualization shows:**
- Protocol structure
- Timeline visualization
- **Real-time current position** (red marker)
- **Live status panel** (updates every 5 seconds)
- Current channel states (ON/OFF/PULSING)

### 3. Manual Visualization with Start Time

```bash
python viz_protocol_html.py protocols/my_experiment_commands_20251108210530.txt \
       --start-time "2025-11-08 21:05:30"
```

**Use case:** Regenerate visualization with custom start time for analysis

## File Management

### Clean Up Old Files

```bash
# Remove all generated files from a directory
find protocols/ -name "*_commands_*.txt" -delete
find protocols/ -name "*_commands_*.html" -delete

# Or with specific date pattern
rm protocols/*_commands_20251108*.txt
rm protocols/*_commands_20251108*.html
```

### Archive Important Results

```bash
# Create dated archive folder
mkdir -p archive/2025-11-08_important_experiment/

# Copy all related files
cp protocols/important_experiment.txt archive/2025-11-08_important_experiment/
cp protocols/important_experiment_commands_*.txt archive/2025-11-08_important_experiment/
cp protocols/important_experiment_commands_*.html archive/2025-11-08_important_experiment/
```

### Find Recent Files

```bash
# Files modified in last 24 hours
find protocols/ -name "*_commands_*.txt" -mtime -1

# Files from specific date
ls protocols/*_commands_20251108*.txt

# Matching pairs (same timestamp)
ls protocols/*_commands_20251108205626.*
# Result:
#   protocols/experiment_commands_20251108205626.txt
#   protocols/experiment_commands_20251108205626.html
```

## Git Integration

### Recommended .gitignore

Add to your `.gitignore`:

```gitignore
# Generated command files
*_commands_*.txt
*_commands_*.html

# Keep protocol files
!*.txt
!examples/*.txt
!protocols/*.txt
```

This way:
- ✅ Protocol files are tracked
- ❌ Generated commands/HTML are ignored
- ✅ Example protocols are tracked

### Alternative: Track Everything

If you want to track results in git:

```bash
# Commit protocol and results together
git add protocols/experiment1.txt
git add protocols/experiment1_commands_20251108120000.txt
git add protocols/experiment1_commands_20251108120000.html
git commit -m "Experiment 1 results - successful protocol"
```

## Troubleshooting

### Files Not in Expected Location?

**Check 1:** Make sure you're using the latest code
```bash
cd /Users/apple/Documents/GitHub/light_controller_v2.2
git pull
```

**Check 2:** Verify the protocol path
```python
# Files save to same directory as protocol_file
protocol_file = "/path/to/my_protocol.txt"
# Output will be: /path/to/my_protocol_commands_TIMESTAMP.txt
```

### Can't Find Matching Files?

**Solution:** Use the timestamp to match files
```bash
# If you have the commands file
commands_file="experiment_commands_20251108205626.txt"

# Find matching HTML
html_file="${commands_file%.txt}.html"
echo $html_file
# Output: experiment_commands_20251108205626.html
```

### Visualization Not Refreshing?

**Check 1:** Browser cache - Hard refresh (Cmd+Shift+R on macOS, Ctrl+Shift+R on Windows)

**Check 2:** Check the console for JavaScript errors (F12 → Console)

**Check 3:** Verify start time is set (for real-time tracking):
```bash
# Look in the HTML for:
# const startTime = new Date("2025-11-08 21:05:30");
# If null, no real-time tracking
```

## Code Changes Summary

### Modified Files

1. **`light_controller_parser.py`**
   - `save_commands()` now defaults to protocol directory
   - Changed from: `output/commands/`
   - Changed to: Same directory as protocol file

2. **`viz_protocol_html.py`**
   - Output saves to same directory as commands file
   - Changed from: `output/visualizations/`
   - Changed to: Same directory as commands file

3. **`preview_protocol.py`**
   - No changes needed (already uses protocol directory)

4. **`protocol_parser.py`**
   - No changes needed (calls `save_commands()` without override)

### Key Code Changes

**Before:**
```python
# Old: Complex project root detection
project_root = find_project_root(protocol_path)
output_dir = os.path.join(project_root, 'output', 'commands')
```

**After:**
```python
# New: Simple - same directory as protocol
output_dir = os.path.dirname(protocol_path)
```

## Migration from Old Structure

If you were using the old `output/` structure:

### Option 1: Move Files to Protocol Directories

```bash
# Move commands back to protocol directories
for f in output/commands/*_commands_*.txt; do
    # Extract protocol name (before _commands_)
    protocol=$(basename "$f" | sed 's/_commands_.*//')
    
    # Find original protocol file
    protocol_file=$(find . -name "${protocol}.txt" -o -name "${protocol}.xlsx")
    
    if [ -n "$protocol_file" ]; then
        # Move to protocol directory
        mv "$f" "$(dirname "$protocol_file")/"
        
        # Also move matching HTML
        html="${f%.txt}.html"
        if [ -f "$html" ]; then
            mv "$html" "$(dirname "$protocol_file")/"
        fi
    fi
done
```

### Option 2: Keep Old Structure

If you prefer the old `output/` structure, you can override:

```python
# In your code
parser = LightControllerParser('protocol.txt')
commands_file = parser.save_commands(output_dir='output/commands')
```

---

**Updated:** November 8, 2025  
**Version:** 2.2.1  
**Status:** ✅ Active
