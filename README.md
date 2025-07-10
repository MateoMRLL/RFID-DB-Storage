# Serial Debug Logger

A comprehensive Python tool for debugging serial communication with detailed logging and real-time monitoring.

## Features

- **Real-time monitoring** - Continuously listens for incoming data
- **Multiple read methods** - Handles line-based and byte-based communication
- **SQLite logging** - Stores all data with timestamps for analysis
- **Binary data support** - Handles both text and binary data
- **Interactive commands** - Send commands and see responses
- **Detailed statistics** - Track bytes received, message counts, and timing

## Quick Start

I recommend to launch the program on Linux system because on Windows driver is required.

```bash
# Create .venv (on Windows)
& "c:/Program Files/Python313/python.exe" -m venv .venv
# Create .venv (on Linux)
pyhton -m venv .venv

# Launch it (on Windows)
.venv\Scripts\activate

# Launch it (on Linux)
source .venv/bin/activate


# Install dependencies
pip install -r requirements.txt

# Run the logger
python script.py
```

## Configuration

Edit these variables in the script:

```python
PORT = "/dev/ttyUSB0"    # Your serial port (Windows: "COM3", etc.)
BAUDRATE = 9600          # Match your device's baud rate
```

## Usage

1. **Connect** - Script automatically connects to the specified port
2. **Monitor** - Listens for incoming data and displays it in real-time
3. **Send commands** - Type any command and press Enter to send
4. **View stats** - Type `stats` to see connection statistics

## Interactive Commands

- `test` - Test the connection status
- `stats` - Show reception statistics
- `quit` - Exit the program
- Any other text - Send as command to the device

## Output

The logger shows:

- **Timestamp** for each message
- **Raw data** received from the device
- **Byte counts** for debugging
- **Connection status** and statistics

## Database

All data is automatically logged to `serial_debug.db` with:

- Timestamps
- Raw data content
- Data type (text/binary)
- Byte counts

## Troubleshooting

- **Permission denied**: Add user to dialout group or run with sudo
- **Port not found**: Check port name with `ls /dev/tty*`
- **No data received**: Verify baud rate and device connection
- **Garbled data**: Check baud rate matches device settings

## Requirements

- Python 3.6+
- pyserial library
- SQLite3 (built-in with Python)
