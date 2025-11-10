# TXT Protocol Syntax Highlighter

Syntax highlighting extension for Light Controller TXT protocol files.

## Features

- **Comments**: Lines starting with `#` are highlighted as comments (green/gray)
- **Keywords**: Protocol keywords highlighted in bold (PROTOCOL, TIME_UNIT, START_TIME, etc.)
- **Commands**: Channel commands (CH1-CH4, WAIT) highlighted distinctly
- **Dictionaries**: Python dictionary syntax highlighting
- **Numbers**: Numeric values highlighted

## Highlighted Elements

### Keywords (Purple/Blue)
- `PROTOCOL:`
- `TIME_UNIT:`
- `START_TIME:`
- `REPEAT:`
- `PULSE:`
- `WAIT_STATUS:`
- `WAIT_PULSE:`
- `COMMANDS:`

### Commands (Yellow/Orange)
- `CH1`, `CH2`, `CH3`, `CH4`
- `WAIT`

### Comments (Green/Gray)
- Lines starting with `#`

### Numbers (Light Blue)
- Integer and decimal numbers

## Installation

This extension is automatically available when you open this workspace in VS Code.

## Usage

1. Open any `.txt` file in the `examples/` folder
2. VS Code will automatically apply syntax highlighting
3. Comments will be clearly visible in green/gray
4. Commands will stand out in different colors

## Color Scheme

Colors depend on your VS Code theme:
- **Dark themes**: Bright, contrasting colors
- **Light themes**: Darker, readable colors

## Example

```
# This is a comment - appears in green
PROTOCOL: 1                    # keyword in purple/blue
TIME_UNIT: seconds             # keyword in purple/blue
COMMANDS:
CH1 0.5 255;                   # CH1 in yellow, numbers in light blue
WAIT 1.0;                      # WAIT in yellow
```
