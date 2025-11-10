# HTML Visualization Guide

**Real-Time Protocol Monitoring with Interactive Browser Interface**

---

## Overview

The HTML visualization system provides a real-time, browser-based monitoring interface for your light controller protocols. It automatically opens after protocol execution starts and updates live as your protocol runs.

**Key Features:**
- 🔴 **Real-time monitoring** - Updates every second
- 💡 **Visual LED indicators** - Animated status display
- 📊 **Timeline visualization** - Color-coded protocol progress
- ⏱️ **Dual time tracking** - Total and protocol-specific elapsed times
- 🟢 **Smart status display** - Shows actual state even during waiting
- ⚡ **Performance optimized** - No loading delays or freezing

---

## Automatic Generation

The HTML visualization is **automatically generated** in two scenarios:

### 1. Preview Mode
```bash
python preview_protocol.py examples/my_protocol.txt
```
- Generates static visualization showing protocol structure
- No upload time (displays structure only)
- Useful for reviewing protocol before execution

### 2. Execution Mode
```bash
python protocol_parser.py
# Select your protocol file
```
- Generates live visualization with upload time
- Opens automatically in your default browser
- Updates in real-time as protocol executes

**Generated File Location:**
```
{protocol_directory}/{protocol}_commands_{timestamp}.html
```

Example:
```
examples/my_protocol.txt
examples/my_protocol_commands_20251108233530.html  ← Auto-generated
```

---

## Interface Components

### Header: Status Panel

**Location:** Top of page with purple background

**Displays:**
- 🔴 **LIVE STATUS** - Current date/time (updates every second)
- **Upload Time** - When protocol was uploaded to Arduino
- **Total Elapsed** - Time since upload (DD:HH:mm:ss format)

**Channel Start Times** (below upload time in light gray):
- Shows when each channel will start (after wait period)
- Format: `CH1: 2025-11-08 23:35:30`

### Channel Monitors

**Each channel has its own monitor card with:**

#### 1. Channel Header
- Channel number and name
- Background color indicates channel

#### 2. LED Status Indicator
Animated circle showing current state:
- 🟢 **Green (pulsing)** - ON
- ⚪ **Gray** - OFF
- 🟠 **Orange (pulsing)** - PULSING
- 🔵 **Blue (completed)** - COMPLETED

#### 3. Status Text
Shows current state with emoji indicator:
- `⏰ WAITING - ON █` - Waiting period, LED ON
- `⏰ WAITING - OFF ░` - Waiting period, LED OFF
- `⏰ WAITING - PULSING ≈` - Waiting period, LED pulsing
- `ON █` - Active, LED ON
- `OFF ░` - Active, LED OFF
- `PULSING ≈` - Active, LED pulsing
- `COMPLETED ✓` - Protocol finished

#### 4. Pattern/Cycle Info
- **Pattern**: Current/Total (e.g., `Pattern: 2/3`)
- **Cycle**: Current/Total (e.g., `Cycle: 5/12`)
- **Protocol Elapsed**: Time since this channel started
  - Shows `--:--:--:--` during wait period
  - Starts counting from `00:00:00:00` after pattern 1 begins

#### 5. Wait Period Info (if applicable)
During waiting:
- **Starts at**: Scheduled start time
- **⏱️ Starts in**: Countdown to start (orange, bold)

#### 6. Pulse Information (if pulsing)
Shows pulse parameters in light gray:
```
🟠 PULSING
Freq: 1.0 Hz
Period: 1000 ms
PW: 100 ms
DC: 10.0 %
```

Or during waiting:
```
🟠 PULSING (Wait)
Freq: 0.5 Hz
Period: 2000 ms
PW: 100 ms
DC: 5.0 %
```

### Timeline Visualization

**Below each channel monitor:**

#### Pattern Blocks
Each pattern is shown as a block containing:
- **Pattern number** and repeat count
- **Cycle progress** (e.g., `Cycle 5/12`)
- **Timeline bar** with colored segments:
  - 🟢 **Green** - LED ON
  - ⚪ **Gray** - LED OFF
  - 🟠 **Orange** - PULSING
- **Section times** - Duration of each state
- **Total duration** - Full pattern duration

#### Current Position Marker
- **Red vertical line** on active pattern timeline
- Shows exact position within current cycle
- Moves smoothly as protocol progresses

#### Active Pattern Highlighting
- Currently executing pattern has **yellow border**
- Makes it easy to see which pattern is running

---

## Time Tracking System

### Three Time References

#### 1. Upload Time (Fixed)
**Location:** Header, next to "Upload Time:"

**What it is:**
- Timestamp when protocol was uploaded to Arduino
- Never changes after upload
- Reference point for all other times

**Format:** `2025-11-08 23:35:30`

#### 2. Total Elapsed (Global)
**Location:** Header, next to "Total Elapsed:"

**What it is:**
- Time since upload
- Includes wait periods for all channels
- Same for all channels (counts from upload)

**Format:** `DD:HH:mm:ss` (e.g., `00:00:05:23`)

**Use case:** Track overall protocol runtime including all waits

#### 3. Protocol Elapsed (Per-Channel)
**Location:** Each channel monitor, "Protocol Elapsed:"

**What it is:**
- Time since THIS channel finished waiting and started actual protocol
- Different for each channel (depends on individual wait times)
- Shows `--:--:--:--` during pattern 0 (wait period)
- Starts from `00:00:00:00` when pattern 1 begins

**Format:** `DD:HH:mm:ss` or `--:--:--:--` (waiting)

**Use case:** Track actual protocol progress for each channel independently

### Example Scenario

```
Upload Time: 23:30:00

Channel 1: 30 second wait
- Total Elapsed: 00:00:00:15
- Protocol Elapsed: --:--:--:-- (still waiting)

Channel 2: 60 second wait
- Total Elapsed: 00:00:00:15
- Protocol Elapsed: --:--:--:-- (still waiting)

After 35 seconds:
Channel 1: Now in pattern 1
- Total Elapsed: 00:00:00:35
- Protocol Elapsed: 00:00:00:05 (5 sec since starting)

Channel 2: Still waiting
- Total Elapsed: 00:00:00:35
- Protocol Elapsed: --:--:--:-- (still waiting)

After 65 seconds:
Channel 1:
- Total Elapsed: 00:00:01:05
- Protocol Elapsed: 00:00:00:35 (35 sec of protocol)

Channel 2: Now in pattern 1
- Total Elapsed: 00:00:01:05
- Protocol Elapsed: 00:00:00:05 (5 sec since starting)
```

---

## Status Display Logic

### During Wait Period (Pattern 0)

**Status shows actual LED state:**
- `⏰ WAITING - ON █` - LED is ON during wait
- `⏰ WAITING - OFF ░` - LED is OFF during wait
- `⏰ WAITING - PULSING ≈` - LED is pulsing during wait

**LED color matches state:**
- Green (pulsing) when ON
- Gray when OFF
- Orange (animated) when PULSING

**Pulse info displayed:**
```
🟠 PULSING (Wait)
Freq: 0.5 Hz
Period: 2000 ms
PW: 100 ms
DC: 5.0 %
```

### During Active Protocol

**Status based on current state:**
- `ON █` - LED is ON
- `OFF ░` - LED is OFF
- `PULSING ≈` - LED is pulsing

**LED animations:**
- **ON**: Green circle with pulsing animation
- **OFF**: Gray circle (static)
- **PULSING**: Orange circle with stronger pulsing

**Pulse info (when pulsing):**
```
🟠 PULSING
Freq: 1.0 Hz
Period: 1000 ms
PW: 100 ms
DC: 10.0 %
```

### After Completion

**Status:** `COMPLETED ✓`
**LED:** Blue circle (static)
**Timeline:** No position marker
**Info:** `✓ Complete` in green

---

## Performance Optimizations

### DOM Caching System

**Problem:** Repeated DOM queries slow down updates
**Solution:** Cache all elements once, reuse 60 times/minute

```javascript
// Cached once on first update:
- Status header
- Elapsed time div
- All channel LED indicators
- All status text elements
- All info divs
- All timeline sections
```

**Result:** Eliminates 60+ DOM queries per second

### Update Frequency

**Timer:** `setInterval(updateDisplay, 1000)`
- Updates every 1 second (not 5 seconds)
- Smooth, responsive interface
- No perceptible lag

### JavaScript-Only Calculations

**All dynamic calculations in browser:**
- Current position calculation
- Elapsed time formatting
- Pattern/cycle tracking
- Status determination

**Benefits:**
- No server/Python dependency after generation
- Works offline
- Instant updates
- Can refresh/reopen without regenerating

---

## Troubleshooting

### Visualization Not Opening

**Symptom:** HTML file generated but doesn't open automatically

**Solutions:**
1. **Manual open:** Navigate to the file and double-click
2. **Check browser:** Ensure default browser is set
3. **File location:** Check same directory as protocol file

### Timer Frozen/Stopped

**Symptom:** Elapsed time stops updating

**Solutions:**
1. **Refresh page:** Press F5 or Cmd+R
2. **Check console:** Press F12, look for JavaScript errors
3. **Browser compatibility:** Use Chrome, Firefox, Safari, or Edge

### Incorrect Times

**Symptom:** Times don't match expected values

**Possible causes:**
1. **Upload time mismatch:** Check if HTML was generated before upload
2. **Time zone issues:** Times display in local browser time
3. **Stale page:** Refresh or regenerate visualization

### Loading Delays

**Symptom:** Page shows "Loading..." for long time

**Fixed in v2.2!** This was caused by:
- DOM query overhead (fixed with caching)
- Python calculation dependencies (moved to JavaScript)
- Synchronous blocking operations (now asynchronous)

**If still occurring:**
1. Regenerate HTML with latest code
2. Clear browser cache
3. Check console for errors

### Channel Shows Wrong Status

**Symptom:** LED color doesn't match expected state

**Check:**
1. **Wait vs Active:** Different display during pattern 0
2. **Pulse configuration:** Verify pulse parameters in protocol
3. **Timing:** Ensure protocol elapsed time is correct
4. **Browser console:** Check for calculation errors

---

## Advanced Usage

### Manual Time Specification

Generate visualization with specific upload time:

```bash
python viz_protocol_html.py examples/my_protocol.txt -u "2025-11-08 23:30:00"
```

**Use cases:**
- Retrospective analysis of past runs
- Testing specific scenarios
- Documentation/screenshots at specific times

### Static Visualization (No Upload Time)

Generate structure-only visualization:

```bash
python viz_protocol_html.py examples/my_protocol.txt
```

**Shows:**
- Protocol structure and timelines
- Pattern blocks and durations
- No live status updates
- No elapsed time tracking

**Use cases:**
- Protocol documentation
- Planning and review
- Sharing protocol design

### Custom Output Location

```bash
python viz_protocol_html.py examples/my_protocol.txt -o /path/to/output.html
```

### Integration with Monitoring Systems

**The HTML file is self-contained:**
- No external dependencies
- Can be served by web server
- Embeddable in dashboards
- Works on mobile devices

**Example:** Deploy to web server for remote monitoring
```bash
cp protocol_commands_20251108233530.html /var/www/html/monitor.html
```

Access from anywhere: `http://your-server/monitor.html`

---

## Color Reference

### LED Indicators
- 🟢 **Green (#4CAF50)** - ON state
- ⚪ **Gray (#cccccc)** - OFF state
- 🟠 **Orange (#ff9800)** - PULSING state
- 🔵 **Blue (#2196F3)** - COMPLETED state

### Timeline Colors
- 🟢 **Green** - ON sections
- ⚪ **Light gray** - OFF sections
- 🟠 **Orange** - PULSING sections
- 🔴 **Red line** - Current position marker

### Text Colors
- **White (#fff)** - Protocol elapsed time, main info
- **Light gray (#bbb)** - Pulse parameters, start times
- **Orange (#ff9800)** - Countdown timers, pulsing labels
- **Green (#4CAF50)** - Completion status
- **Dark (#333)** - Main text

### Background Colors
- **Purple gradient** - Status panel header
- **Dark (#1a1a1a)** - Page background
- **Gray (#2d2d2d)** - Channel cards
- **Darker gray (#252525)** - Pattern blocks
- **Yellow border** - Active pattern highlight

---

## Technical Details

### File Structure

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        /* CSS styles for layout and animations */
    </style>
</head>
<body>
    <div class="status-panel">
        <!-- Header with time tracking -->
    </div>
    
    <div class="status-grid">
        <!-- Channel monitors -->
    </div>
    
    <!-- Channel sections with timelines -->
    
    <script>
        // JavaScript for real-time updates
        const channelsData = {...};  // Protocol structure
        const uploadTime = new Date("2025-11-08 23:35:30");
        
        function updateDisplay() {
            // Update all channels every second
        }
        
        setInterval(updateDisplay, 1000);
    </script>
</body>
</html>
```

### Data Flow

1. **Python generates:**
   - Channel structure (patterns, times, pulse info)
   - Upload time (if provided)
   - Channel start times
   - Static HTML template with embedded data

2. **JavaScript calculates:**
   - Current time
   - Elapsed times (total and per-channel)
   - Current pattern/cycle/state
   - Position in timeline
   - Status (ON/OFF/PULSING/WAITING/COMPLETED)

3. **Browser renders:**
   - Updated LED states
   - Moving position markers
   - Counting timers
   - Animated effects

### Browser Compatibility

**Tested and working:**
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

**Required features:**
- ES6 JavaScript (arrow functions, template literals)
- CSS animations
- `Date` object with locale formatting
- `setInterval` for timers

**Mobile support:**
- ✅ iOS Safari
- ✅ Chrome Mobile
- ✅ Firefox Mobile

---

## Examples

### Basic Protocol
```bash
python viz_protocol_html.py examples/basic_protocol.txt -u "2025-11-08 23:30:00"
```

**Shows:**
- 3 channels with different start times
- Simple ON/OFF patterns
- Protocol elapsed tracking per channel

### Wait + Pulse Protocol
```bash
python viz_protocol_html.py examples/wait_pulse_protocol.txt -u "2025-11-08 23:30:00"
```

**Shows:**
- Waiting periods with pulse display
- Pulse parameter details
- Pulsing LED indicators during wait
- Smooth transition to active protocol

### Complex Multi-Channel
```bash
python viz_protocol_html.py examples/pattern_length_4_example.txt -u "2025-11-08 23:30:00"
```

**Shows:**
- 4-element patterns
- Multiple cycles
- Pattern highlighting
- Timeline position tracking

---

## Best Practices

### For Monitoring
1. **Keep HTML file open** while protocol runs
2. **Check browser console** if issues occur
3. **Refresh if stale** (press F5)
4. **Use dual monitors** for Arduino serial + HTML view

### For Documentation
1. **Generate with specific time** for consistent screenshots
2. **Save HTML files** with protocol versions
3. **Include in reports** for visual representation
4. **Share with team** for protocol review

### For Debugging
1. **Compare expected vs actual** status
2. **Verify timing** with elapsed counters
3. **Check pulse parameters** against protocol
4. **Use position marker** to identify issues

---

## Future Enhancements

**Planned features:**
- Historical data logging
- Graph views for analog values
- Export to CSV/PDF
- Multi-protocol comparison
- Remote control integration
- Custom themes/colors
- Alert notifications

---

## Related Documentation

- **[Output at Protocol Path](OUTPUT_AT_PROTOCOL_PATH.md)** - File organization and location
- **[Real-time Visualization](REALTIME_VISUALIZATION.md)** - Overview of visualization features
- **[Usage Guide](USAGE.md)** - General usage instructions
- **[Protocol Formats](PROTOCOL_FORMATS.md)** - Protocol file syntax

---

**Last Updated:** November 8, 2025  
**Version:** 2.2.0  
**Status:** ✅ Production Ready
