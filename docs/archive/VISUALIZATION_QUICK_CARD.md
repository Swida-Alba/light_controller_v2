# 🔴 Real-Time Visualization - Quick Reference

## Automatic Generation

### Preview Protocol
```bash
python preview_protocol.py protocol.txt
```
**Result:** HTML opens showing protocol structure (no timing)

### Execute Protocol
```bash
python protocol_parser.py
```
**Result:** HTML opens with real-time status tracking

---

## Visual Indicators

### Status Panel LEDs
- 🟢 **Green pulsing** → Currently ON
- ⬜ **Gray static** → Currently OFF
- 🟡 **Orange pulsing** → PWM PULSING
- 🟢 **Green static** → COMPLETED

### Timeline Colors
- 🟢 **Green bars** → LED ON (solid)
- ⬜ **Gray bars** → LED OFF
- 🟡 **Orange bars** → LED PULSING (PWM)

### Position Marker
- 🔴 **Red vertical line** → Current position in timeline
- Updates every 5 seconds

---

## What the Visualization Shows

### Live Status Panel
```
🔴 LIVE STATUS - 2025-11-08 20:35:42
Started: 2025-11-08 20:30:00    Elapsed: 5.70min

┌─────────────────┐  ┌─────────────────┐
│  Channel 1      │  │  Channel 2      │
│  ● ON █        │  │  ● PULSING ≈   │
│  Pattern: 2     │  │  Pattern: 1     │
│  Cycle: 3       │  │  Cycle: 5       │
└─────────────────┘  └─────────────────┘
```

### Timeline View
```
Pattern 1                           ▶ CURRENT
────────────────────────────────────────────
Time: 0ms → 10.00s
Duration: 10.00s
Repeats: 5x

Visual:
Cycle 1: |██████████████░░░░░░░░░░|
              ↑ Red marker
Cycle 2: |██████████████░░░░░░░░░░|
```

---

## Manual Generation

### With Start Time (tracking)
```bash
python viz_protocol_html.py commands.txt \
  --start-time "2025-11-08 20:30:00"
```

### Without Start Time (structure only)
```bash
python viz_protocol_html.py commands.txt
```

### Custom Output Name
```bash
python viz_protocol_html.py commands.txt -o my_protocol
```

---

## Key Features

✅ **Auto-generates** - No manual steps
✅ **Auto-opens** - Browser opens automatically
✅ **Auto-refreshes** - Updates every 5 seconds
✅ **Real-time status** - Live LED indicators
✅ **Position tracking** - Red marker shows progress
✅ **Beautiful design** - Gradient backgrounds, animations

---

## Common Use Cases

### 1. Monitor Running Protocol
```bash
python protocol_parser.py
# Leave browser window open
# Watch progress in real-time
```

### 2. Preview Before Running
```bash
python preview_protocol.py protocol.txt
# Check structure and timing
# Verify patterns look correct
```

### 3. Document Experiment
```bash
# HTML file is saved automatically
# Share: protocol_commands_TIMESTAMP_visualization.html
```

---

## Troubleshooting

**Browser doesn't open?**
→ Manually open `*_visualization.html` from project folder

**Old data showing?**
→ Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

**Status not updating?**
→ Wait 5 seconds (auto-refresh interval)

**Wrong time displayed?**
→ Regenerate with correct start time

---

## Technical Details

**Update Interval:** 5 seconds (auto-refresh)
**File Format:** Standalone HTML (no dependencies)
**Browser:** Any modern browser (Chrome, Firefox, Safari, Edge)
**Position:** Calculated from start time + elapsed time

---

## Pro Tips

💡 **Multiple monitors** - Put visualization on second screen

💡 **Screenshot docs** - Capture key moments for records

💡 **Archive files** - Save HTML with descriptive names

💡 **Disable refresh** - Comment out JavaScript if needed

💡 **Share results** - HTML works standalone (email/cloud)

---

## Documentation

📖 **Full Guide:** [docs/REALTIME_VISUALIZATION.md](REALTIME_VISUALIZATION.md)
📖 **Quick Start:** [docs/VISUALIZATION_QUICKSTART.md](VISUALIZATION_QUICKSTART.md)
📖 **Summary:** [docs/AUTO_VISUALIZATION_SUMMARY.md](AUTO_VISUALIZATION_SUMMARY.md)

---

**Version:** 2.2.0 | **Updated:** November 8, 2025 | **Status:** ✅ Production Ready
