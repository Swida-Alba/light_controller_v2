# 📋 Quick Reference - Output at Protocol Path

## File Locations

### Before vs After

| Before (v2.2.0) | After (v2.2.1) |
|-----------------|----------------|
| `output/commands/protocol_commands_TIMESTAMP.txt` | `{protocol_dir}/protocol_commands_TIMESTAMP.txt` |
| `output/visualizations/protocol_commands_TIMESTAMP.html` | `{protocol_dir}/protocol_commands_TIMESTAMP.html` |

### Example

```bash
# You have this protocol file:
examples/my_experiment.txt

# Generated files will be:
examples/my_experiment_commands_20251108205626.txt
examples/my_experiment_commands_20251108205626.html

# Same directory, matching timestamps! 🎯
```

## Commands

### Preview Protocol (No Hardware)
```bash
python preview_protocol.py examples/protocol.txt
```
**Output:** Files in `examples/` directory  
**Visualization:** Structure only (no real-time)

### Execute Protocol (With Arduino)
```bash
python protocol_parser.py
# Select: examples/protocol.txt
```
**Output:** Files in `examples/` directory  
**Visualization:** Real-time with auto-refresh (5 sec)

### Manual Visualization
```bash
python viz_protocol_html.py examples/protocol_commands_TIMESTAMP.txt \
       --start-time "2025-11-08 21:00:00"
```
**Output:** HTML in same directory as commands file

## Real-Time Features

### When Executing
- 🟢 **Live LED indicators** (ON/OFF/PULSING)
- 🔴 **Current position marker** on timeline
- ⏰ **Auto-refresh** every 5 seconds
- 📊 **Status panel** with elapsed time
- 📈 **Progress bars** for each channel

### When Previewing
- 📊 **Timeline visualization** (structure)
- ⚙️ **Pattern details** (no real-time)
- 🎨 **Color-coded states** (static)

## File Management

### Find Matching Files
```bash
# All generated files for a protocol
ls examples/protocol_commands_*.*

# Specific run by timestamp
ls examples/*_commands_20251108205626.*
```

### Clean Up
```bash
# Remove all generated files from a directory
rm examples/*_commands_*.txt
rm examples/*_commands_*.html

# Or use find for recursive cleanup
find . -name "*_commands_*.txt" -delete
find . -name "*_commands_*.html" -delete
```

### Archive Results
```bash
# Archive complete experiment
mkdir -p archive/2025-11-08_experiment_results/
cp examples/experiment.txt archive/2025-11-08_experiment_results/
cp examples/experiment_commands_*.* archive/2025-11-08_experiment_results/
```

## Git Integration

### What's Tracked
```
✅ examples/protocol.txt          # Your protocol (tracked)
❌ examples/protocol_commands_*.txt   # Generated (ignored)
❌ examples/protocol_commands_*.html  # Generated (ignored)
```

### Force Add Specific Results
```bash
git add -f examples/important_commands_20251108120000.txt
git add -f examples/important_commands_20251108120000.html
git commit -m "Important experiment results"
```

## Troubleshooting

### Files Not in Expected Location?
```bash
# Check where protocol file is
echo "Protocol: $(pwd)/examples/protocol.txt"

# Files will be saved in same directory
ls -l examples/*_commands_*
```

### Can't Find HTML?
```bash
# HTML has same name as commands file, just .html extension
commands_file="examples/protocol_commands_20251108205626.txt"
html_file="${commands_file%.txt}.html"
open "$html_file"
```

### Visualization Not Refreshing?
```bash
# Hard refresh browser
# macOS: Cmd + Shift + R
# Windows/Linux: Ctrl + Shift + R

# Or check browser console (F12) for errors
```

## Quick Examples

### Example 1: Simple Preview
```bash
python preview_protocol.py examples/simple_blink_example.txt
# Output: examples/simple_blink_example_commands_20251108205626.txt
# Output: examples/simple_blink_example_commands_20251108205626.html
# Browser opens automatically
```

### Example 2: Protocol in Different Location
```bash
python preview_protocol.py ~/Desktop/test.txt
# Output: ~/Desktop/test_commands_20251108210000.txt
# Output: ~/Desktop/test_commands_20251108210000.html
```

### Example 3: Multiple Runs
```bash
# Run 1 at 12:00
python protocol_parser.py  # Select: experiment.txt
# → experiment_commands_20251108120000.txt/html

# Run 2 at 14:00
python protocol_parser.py  # Select: experiment.txt
# → experiment_commands_20251108140000.txt/html

# Both runs in same directory, different timestamps!
```

## Key Benefits

✅ **Organized** - Protocol and results together  
✅ **Easy Archive** - Copy folder = copy everything  
✅ **Simple Cleanup** - Delete folder = delete all  
✅ **Git Friendly** - Ignore patterns work everywhere  
✅ **Matching Files** - Same timestamp = related files  

## Documentation

| Guide | Purpose |
|-------|---------|
| `docs/OUTPUT_AT_PROTOCOL_PATH.md` | Complete user guide |
| `docs/SUCCESS_SUMMARY.md` | Implementation summary |
| `docs/UPDATE_OUTPUT_AT_PROTOCOL_PATH.md` | Technical details |

---

**Updated:** November 8, 2025  
**Version:** 2.2.1  
**Quick Tip:** Use `ls *_commands_*.txt` to find all generated command files!
