# HTML Visualization - Quick Reference Card

**Real-Time Protocol Monitoring Interface**

---

## 🎯 Quick Start

```bash
# Generate with current time
python viz_protocol_html.py examples/my_protocol.txt -u "$(date '+%Y-%m-%d %H:%M:%S')"

# Or let protocol_parser do it automatically
python protocol_parser.py  # Opens HTML in browser after upload
```

---

## 📊 Interface Layout

```
┌─────────────────────────────────────────────────────┐
│  🔴 LIVE STATUS - 2025-11-08 23:35:45              │
│  Upload Time: 2025-11-08 23:35:30                   │
│  Total Elapsed: 00:00:00:15                         │
│  Channel Start Times:                               │
│    CH1: 2025-11-08 23:36:00                        │
│    CH2: 2025-11-08 23:36:30                        │
└─────────────────────────────────────────────────────┘

┌──────────────┬──────────────┬──────────────┐
│  Channel 1   │  Channel 2   │  Channel 3   │
│  🟢 ON █     │  ⚪ OFF ░    │  🟠 PULSING ≈│
│              │              │              │
│  Pattern:2/3 │  Pattern:1/3 │  Pattern:2/4 │
│  Cycle: 5/12 │  Cycle: 1/1  │  Cycle: 3/8  │
│  Protocol:   │  Protocol:   │  Protocol:   │
│  00:00:02:15 │  --:--:--:-- │  00:00:01:30 │
└──────────────┴──────────────┴──────────────┘

[Timeline visualization with colored bars and position marker]
```

---

## 🎨 Status Indicators

### LED Colors
- 🟢 **Green (pulsing)** → ON
- ⚪ **Gray (static)** → OFF  
- 🟠 **Orange (animated)** → PULSING
- 🔵 **Blue (static)** → COMPLETED

### Status Text
- `ON █` - Currently ON
- `OFF ░` - Currently OFF
- `PULSING ≈` - Currently pulsing
- `⏰ WAITING - ON █` - Waiting, LED is ON
- `⏰ WAITING - OFF ░` - Waiting, LED is OFF
- `⏰ WAITING - PULSING ≈` - Waiting, LED pulsing
- `COMPLETED ✓` - Protocol finished

---

## ⏱️ Time Display

### Header (Global)
```
Upload Time: 2025-11-08 23:35:30  ← Fixed reference
Total Elapsed: 00:00:05:23        ← Counts from upload
```

### Per Channel
```
Protocol Elapsed: --:--:--:--  ← During wait (pattern 0)
Protocol Elapsed: 00:00:02:15  ← After wait ends
```

**Format:** `DD:HH:mm:ss` (Days:Hours:Minutes:Seconds)

---

## 🟠 Pulse Information

### During Wait
```
🟠 PULSING (Wait)
Freq: 0.5 Hz
Period: 2000 ms
PW: 100 ms
DC: 5.0 %
```

### During Active Protocol
```
🟠 PULSING
Freq: 1.0 Hz
Period: 1000 ms
PW: 100 ms
DC: 10.0 %
```

---

## 📍 Timeline Features

### Pattern Block
```
┌───────────────────────────┐
│ Pattern 2 (12x)           │ ← Yellow border = active
│ Cycle 5/12                │
│ ▓▓▓▓▒▒▒▒▓▓▓▓              │ ← Green=ON, Gray=OFF
│ │                         │
│ └─ Red marker = position  │
│ 5.0s  5.0s  5.0s          │ ← Section durations
│ Total: 15.0s              │
└───────────────────────────┘
```

### Colors
- 🟢 **Green bars** = ON sections
- ⚪ **Gray bars** = OFF sections
- 🟠 **Orange bars** = PULSING sections
- 🔴 **Red line** = Current position

---

## ⚡ Performance

| Feature | Value |
|---------|-------|
| Update frequency | 1 second |
| DOM queries | ~1 (cached) |
| Load time | <0.1 seconds |
| Memory usage | Stable |
| CPU usage | Low |

---

## 🔧 Troubleshooting

### Timer Frozen
**Symptom:** Elapsed time stops updating
**Fix:** Refresh page (F5 / Cmd+R)

### Wrong Status
**Symptom:** LED doesn't match expected
**Fix:** Check browser console (F12) for errors

### Not Opening
**Symptom:** HTML generated but doesn't open
**Fix:** Manually open file from protocol directory

### Loading Forever
**Symptom:** Page shows "Loading..." indefinitely
**Fix:** Regenerate with latest code

---

## 📱 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| F5 / Cmd+R | Refresh page |
| F12 | Open developer console |
| Cmd++ / Ctrl++ | Zoom in |
| Cmd+- / Ctrl+- | Zoom out |
| Cmd+0 / Ctrl+0 | Reset zoom |

---

## 🌐 Browser Support

✅ Chrome 90+  
✅ Firefox 88+  
✅ Safari 14+  
✅ Edge 90+  
✅ Mobile browsers

---

## 📂 File Location

```
protocol_directory/
├── my_protocol.txt
├── my_protocol_commands_20251108233530.txt   ← Command output
└── my_protocol_monitor_20251108233530.html   ← Visualization (opened in browser)
```

**Pattern:** `{protocol}_monitor_{timestamp}.html`

---

## 💡 Pro Tips

1. **Keep HTML open** while protocol runs
2. **Use dual monitors** for serial + visualization
3. **Save HTML files** for documentation
4. **Check console** if something looks wrong
5. **Refresh if stale** after regenerating

---

## 🔗 Related Commands

```bash
# Preview without upload time (structure only)
python viz_protocol_html.py examples/my_protocol.txt

# Custom upload time
python viz_protocol_html.py examples/my_protocol.txt -u "2025-11-08 23:30:00"

# Custom output location
python viz_protocol_html.py examples/my_protocol.txt -o /path/to/output.html

# Automatic (recommended)
python protocol_parser.py  # Auto-generates and opens
```

---

## 📖 Full Documentation

- **[HTML Visualization Guide](HTML_VISUALIZATION.md)** - Complete user manual
- **[HTML Visualization Updates](HTML_VISUALIZATION_UPDATES.md)** - Technical details
- **[Usage Guide](USAGE.md)** - General usage instructions
- **[Troubleshooting](TROUBLESHOOTING.md)** - Solutions for common issues

---

## 🆕 What's New in v2.2.0

✅ JavaScript-only calculations (no Python dependency)  
✅ DOM caching (60x faster)  
✅ 1-second updates (5x smoother)  
✅ Dual time tracking (total + protocol elapsed)  
✅ Smart waiting display (shows actual status)  
✅ Enhanced pulse info (during wait too)  
✅ Better colors (#bbb instead of #666)  
✅ Fixed timer freezing bug  
✅ Fixed loading delays  

---

**Version:** 2.2.0  
**Updated:** November 8, 2025  
**Status:** ✅ Production Ready

---

*For questions: Check [Troubleshooting](TROUBLESHOOTING.md)*  
*For issues: [GitHub Issues](https://github.com/Swida-Alba/light_controller_v2/issues)*
