# Serial Logger Scripts

Two Python scripts for logging serial data with different database backends and features.

## Scripts Overview

### 1. Debug Serial Logger (`script.py`)

A comprehensive debugging tool for serial communication that logs to SQLite database.

### 2. Antenna Serial Logger (`script2.py`)

A specialized logging system for antenna data that stores information in MySQL with antenna identification.

## Features Comparison

| Feature              | Debug Logger         | Antenna Logger             |
| -------------------- | -------------------- | -------------------------- |
| Database             | SQLite               | MySQL                      |
| Antenna Support      | ❌                   | ✅ (1 or 2)                |
| Interactive Commands | Full command sending | Simplified antenna control |
| Debug Output         | Verbose debugging    | Antenna-focused logging    |
| Binary Data Support  | ✅                   | ✅                         |
| Auto-reconnect       | ❌                   | ✅ (MySQL)                 |

## Requirements

### Common Dependencies

In a virtual environement : 
```bash
pip install -r requirements.txt
```

## Database Setup

### Debug Logger (SQLite)

No setup required - database file is created automatically.

### Antenna Logger (MySQL)

1. Install MySQL server
2. Create database and user:

```sql
CREATE DATABASE data_logs;
CREATE USER 'example'@'localhost' IDENTIFIED BY 'pswrdexample';
GRANT ALL PRIVILEGES ON data_logs.* TO 'userexample'@'localhost';
FLUSH PRIVILEGES;
```

## Configuration

### Debug Logger

Edit these variables in the script:

```python
PORT = "/dev/ttyUSB0"      # Your serial port
BAUDRATE = 9600            # Baud rate
```

### Antenna Logger

Edit these variables in the script:

```python
PORT = "/dev/ttyUSB0"      # Your serial port
BAUDRATE = 9600            # Baud rate

MYSQL_CONFIG = {
    "host": "localhost",
    "database": "data_logs",
    "user": "userexample",
    "password": "pswdexample",
    "port": 3306,
}
```

## Usage

### Debug Logger

```bash
python script.py
```

**Interactive Commands:**

- `test` - Test connection
- `stats` - Show statistics
- `quit` - Exit
- Any other text - Send as command to serial device (refers to the component datasheet)

**Features:**

- Automatic data reception monitoring
- Verbose debugging output
- Multiple read methods (readline, single bytes)
- Raw bytes logging in hex format
- Real-time statistics

### Antenna Logger

```bash
python script2.py
```

**Interactive Commands:**

- `antenna 1` - Set antenna to 1
- `antenna 2` - Set antenna to 2
- `start` - Start monitoring with selected antenna
- `stats` - Show statistics
- `quit` - Exit

It's not really possible to use the command from the datasheet with this script but with the first one it's possible.

**Features:**

- Antenna-specific data logging
- MySQL storage with indexing
- Automatic database reconnection
- Simplified interface focused on antenna switching

## Database Schema

### Debug Logger (SQLite)

```sql
CREATE TABLE serial_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    data TEXT,
    data_type TEXT,
    raw_bytes TEXT,
    byte_count INTEGER
);
```

### Antenna Logger (MySQL)

```sql
CREATE TABLE serial_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    data TEXT,
    data_type VARCHAR(50),
    raw_bytes LONGTEXT,
    byte_count INT,
    antenna INT,
    INDEX idx_timestamp (timestamp),
    INDEX idx_data_type (data_type),
    INDEX idx_antenna (antenna)
);
```

## Data Types Logged

Both scripts log different types of data:

- `auto_received` - Normal text data received automatically
- `binary_received` - Binary data (stored as hex)
- `command_sent` - Commands sent to device (Debug Logger only)

## Serial Port Configuration

Both scripts use these serial parameters:

- **Data bits:** 8
- **Parity:** None
- **Stop bits:** 1
- **Timeout:** 0.1 seconds (non-blocking)

## Common Serial Ports

### Linux/macOS

- `/dev/ttyUSB0`, `/dev/ttyUSB1` (USB-to-serial adapters)
- `/dev/ttyACM0`, `/dev/ttyACM1` (Arduino, CDC devices)
- `/dev/ttyS0`, `/dev/ttyS1` (Built-in serial ports)

### Windows

- `COM1`, `COM2`, `COM3`, etc.

## Troubleshooting

### Permission Issues (Linux/macOS)

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER
# Log out and back in

# Or run with sudo (not recommended)
sudo python script.py
```

## File Outputs

### Debug Logger

- **Database:** `serial_debug.db` (SQLite file)

### Antenna Logger

- **Database:** MySQL `data_logs` database
- **Tables:** `serial_logs` table with antenna column

## Performance Notes

- Both scripts use threading for non-blocking serial monitoring
- Short sleep intervals (0.01s) for responsive data capture
- MySQL version includes connection pooling and auto-reconnect
- SQLite version is simpler but single-threaded for database access
