# Quick Setup: Syntax Highlighting

## ⚡ 3-Step Setup

### 1️⃣ Reload VS Code
Press: `Cmd+Shift+P` → Type: `Reload Window` → Press Enter

### 2️⃣ Open a Protocol File
Open: `examples/example_protocol.txt`

### 3️⃣ Done! 🎉
Comments and commands are now highlighted!

---

## What You'll See

```
# This comment is now GREEN and italic ✨
PROTOCOL: 1                    ← PURPLE and bold
TIME_UNIT: seconds             ← PURPLE and bold
COMMANDS:
CH1 0.5 255;                   ← CH1 is YELLOW, numbers are LIGHT GREEN
WAIT 1.0;                      ← WAIT is YELLOW
```

---

## 🎨 Color Key

- 🟢 **Comments** (`#`) - Green, italic
- 🟣 **Keywords** (`PROTOCOL:`, `COMMANDS:`, etc.) - Purple, bold
- 🟡 **Commands** (`CH1`, `WAIT`) - Yellow
- 🔵 **Numbers** (`0.5`, `255`) - Light green/blue

---

## 🔧 Not Working?

Try clicking the language indicator in the bottom-right corner of VS Code:
1. Click where it says "Plain Text"
2. Type: `TXT Protocol`
3. Select it

---

## 📖 Full Guide

See **[SYNTAX_HIGHLIGHTING_GUIDE.md](SYNTAX_HIGHLIGHTING_GUIDE.md)** for:
- Customizing colors
- Troubleshooting
- Advanced configuration
