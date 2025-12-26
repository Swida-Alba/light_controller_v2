# Folder Structure Reorganization Summary

## Date: November 8, 2025

## Changes Made

### 1. New Folder Structure

Created organized output structure:

```
light_controller_v2.2/
├── output/                      # Auto-generated files (git ignored)
│   ├── commands/                # Command .txt files with timestamps
│   ├── visualizations/          # HTML files matching command names
│   └── README.md                # Documentation for output folder
│
└── archive/                     # For saving important experiments
    └── experiments/             # User's archived results
```

### 2. Files Deleted

**Removed redundant/backup files:**
- `lcfunc.py.backup`
- `protocol_parser.py.backup`
- `protocol_visualizer.py` (obsolete, replaced by viz_protocol_html.py)
- `protocol_visualizer_backup.py`
- `protocol_visualizer_simple.py` (replaced by viz_protocol_html.py)
- `viz_protocol.py` (ASCII-only, replaced by viz_protocol_html.py)
- `simple_blink_commands.txt` (test file, moved to output/)

**Result:** Cleaner root directory with only active files

### 3. File Naming Convention

**Before:**
- Commands: `{protocol}_commands_{timestamp}.txt` (scattered in root/examples)
- Visualization: `{protocol}_visualization.html` (inconsistent naming)

**After:**
- Commands: `output/commands/{protocol}_commands_{timestamp}.txt`
- Visualization: `output/visualizations/{protocol}_commands_{timestamp}.html`

**Benefits:**
- ✅ Matching names with same timestamp
- ✅ Easy to find corresponding files
- ✅ Organized in separate folders
- ✅ Clean project root

### 4. Code Changes

#### `light_controller_parser.py`
**Modified:** `save_commands()` method

**Changes:**
- Default output directory changed from protocol file location to `output/commands/`
- Auto-creates output directory if missing
- Detects project root intelligently (handles examples/ subfolder)

```python
# Before
output_dir = os.path.dirname(protocol_path)

# After
project_root = # ... intelligent detection
output_dir = os.path.join(project_root, 'output', 'commands')
os.makedirs(output_dir, exist_ok=True)
```

#### `viz_protocol_html.py`
**Modified:** Output path generation

**Changes:**
- Finds project root by looking for `protocol_parser.py`
- Saves to `output/visualizations/`
- Matches command file naming (same timestamp)
- Works from any subdirectory (examples/, etc.)

```python
# Project root detection
while project_root != os.path.dirname(project_root):
    if os.path.exists(os.path.join(project_root, 'protocol_parser.py')):
        break
    project_root = os.path.dirname(project_root)

# Output to organized location
output_dir = os.path.join(project_root, 'output', 'visualizations')
```

#### `.gitignore`
**Added:** `output/` directory

**Reason:**
- Generated files shouldn't be in version control
- Users can archive important results separately
- Keeps repository clean

### 5. Documentation Updates

#### Created:
1. **`output/README.md`** - Documentation for output folder structure
2. **`docs/AUTO_VISUALIZATION_SUMMARY.md`** - Updated with new paths

#### Updated:
1. **`README.md`** - Added "Project Structure" section
2. **File output locations** - Documented in Quick Start

### 6. Archive Structure

Created `archive/experiments/` for users to save important results:

```bash
# Example usage
cp output/commands/important_protocol_*.txt archive/experiments/experiment_1/
cp output/visualizations/important_protocol_*.html archive/experiments/experiment_1/
```

**Benefits:**
- Permanent storage for important data
- Organized by experiment
- Separated from auto-generated files

## Benefits of Reorganization

### 1. Clarity
- ✅ Clear separation of code vs generated files
- ✅ Easy to find matching command and visualization files
- ✅ Clean project root directory

### 2. Organization
- ✅ All generated files in one place (`output/`)
- ✅ Consistent naming convention
- ✅ Timestamped for tracking

### 3. Maintainability
- ✅ Easy to clean up old files (`rm -rf output/`)
- ✅ Git ignores temporary files
- ✅ Archive for permanent storage

### 4. User Experience
- ✅ Files automatically organized
- ✅ No manual file management needed
- ✅ Clear documentation

## File Locations Reference

### Before Reorganization
```
light_controller_v2.2/
├── protocol_visualizer.py         # Obsolete
├── protocol_visualizer_backup.py  # Backup
├── viz_protocol.py                 # ASCII only
├── lcfunc.py.backup               # Backup
├── simple_blink_commands.txt      # Test file
├── example_visualization.html     # Scattered
└── simple_blink_example_commands_20251108204423_visualization.html
```

### After Reorganization
```
light_controller_v2.2/
├── viz_protocol_html.py           # Single visualizer
├── lcfunc.py                      # No backup
│
├── output/                        # All generated files
│   ├── commands/
│   │   └── {protocol}_commands_{timestamp}.txt
│   └── visualizations/
│       └── {protocol}_commands_{timestamp}.html
│
└── archive/                       # User's saved experiments
    └── experiments/
```

## Migration Notes

### For Existing Users

If you have old generated files in the root directory:

```bash
# Move old commands to new location
mkdir -p output/commands output/visualizations
mv *_commands_*.txt output/commands/ 2>/dev/null
mv *_visualization*.html output/visualizations/ 2>/dev/null
```

### For Git Users

Update your `.git/info/exclude` if you had custom ignores:
```bash
# Remove old patterns (now covered by output/)
# output/ is now in .gitignore
```

## Testing

### Tested Scenarios

1. **Preview from examples folder:**
   ```bash
   python preview_protocol.py examples/simple_blink_example.txt
   ```
   ✅ Commands saved to `output/commands/`
   ✅ HTML saved to `output/visualizations/`
   ✅ Names match with timestamp

2. **Visualization from examples:**
   ```bash
   python viz_protocol_html.py examples/example_commands_for_visualization.txt
   ```
   ✅ Finds project root correctly
   ✅ Saves to `output/visualizations/`

3. **Directory auto-creation:**
   ✅ Creates `output/commands/` if missing
   ✅ Creates `output/visualizations/` if missing

## Cleanup Script

Created for easy maintenance:

```bash
#!/bin/bash
# cleanup_output.sh

# Remove all generated files
echo "Cleaning output directory..."
rm -rf output/commands/*
rm -rf output/visualizations/*

# Keep the README
echo "Cleanup complete. Output directories preserved."
```

## Future Considerations

### Possible Enhancements

1. **Automatic archiving** - Move files older than N days to archive
2. **Compression** - Zip old visualization HTML files
3. **Database** - SQLite index of all runs
4. **Web interface** - Browse generated files
5. **Export** - Batch export to other formats

### Maintenance

Regular cleanup recommended:

```bash
# Weekly: Remove files older than 7 days
find output/ -type f -mtime +7 -delete

# Monthly: Archive important experiments
# (Manual process recommended)
```

## Documentation

All documentation updated to reflect new structure:
- ✅ README.md - Project structure section
- ✅ output/README.md - Output folder guide
- ✅ docs/REALTIME_VISUALIZATION.md - Updated paths
- ✅ docs/AUTO_VISUALIZATION_SUMMARY.md - Updated examples

## Summary

**Deleted:** 7 redundant/backup files
**Created:** Organized `output/` and `archive/` structure
**Updated:** 4 code files, 3 documentation files
**Result:** Clean, organized, maintainable project structure

✅ All generated files now in `output/`
✅ Matching names for commands and visualizations
✅ Git ignores temporary files
✅ Archive available for important results
✅ Comprehensive documentation

---

**Reorganization Date:** November 8, 2025  
**Version:** 2.2.0  
**Status:** ✅ Complete
