import serial
import sqlite3
import threading
import time
from datetime import datetime
import sys


class DebugSerialLogger:
    def __init__(self, port, baudrate=9600, db_name="serial_debug.db"):
        self.port = port
        self.baudrate = baudrate
        self.db_name = db_name
        self.serial_conn = None
        self.db_conn = None
        self.running = False
        self.log_thread = None
        self.stats = {
            "bytes_received": 0,
            "messages_received": 0,
            "last_data_time": None,
        }

        self.setup_database()

    def setup_database(self):
        """Initialize database with debug info"""
        self.db_conn = sqlite3.connect(self.db_name, check_same_thread=False)
        cursor = self.db_conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS serial_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                data TEXT,
                data_type TEXT,
                raw_bytes TEXT,
                byte_count INTEGER
            )
        """
        )

        self.db_conn.commit()
        print(f"Database ready: {self.db_name}")

    def connect(self):
        """Connect with detailed error reporting"""
        try:
            print(f"Attempting to connect to {self.port} at {self.baudrate} baud...")

            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1,  # Short timeout for non-blocking reads
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )

            print(f"Connection successful!")
            print(f"   Port: {self.serial_conn.port}")
            print(f"   Baudrate: {self.serial_conn.baudrate}")
            print(f"   Timeout: {self.serial_conn.timeout}")
            print(f"   Is open: {self.serial_conn.is_open}")

            return True

        except Exception as e:
            print(f"Connection failed: {e}")
            print(f"   Make sure {self.port} exists and is not in use")
            return False

    def log_data(self, data, raw_bytes, data_type="auto_received"):
        """Log data with raw bytes info"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute(
                """
                INSERT INTO serial_logs (data, data_type, raw_bytes, byte_count)
                VALUES (?, ?, ?, ?)
            """,
                (data, data_type, str(raw_bytes), len(raw_bytes)),
            )
            self.db_conn.commit()

        except Exception as e:
            print(f"Logging error: {e}")

    def start_monitoring(self):
        """Start monitoring with verbose debug info"""
        if self.running:
            print("Monitoring already active")
            return

        self.running = True
        self.log_thread = threading.Thread(target=self._monitor_loop)
        self.log_thread.daemon = True
        self.log_thread.start()

        print("MONITORING STARTED")
        print("Listening for ANY data on serial port...")
        print("Will show activity every 5 seconds")
        print("-" * 50)

    def _monitor_loop(self):
        """Enhanced monitoring loop with multiple read methods"""
        last_activity_report = time.time()

        while self.running:
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    # Method 1: Check bytes waiting
                    bytes_waiting = self.serial_conn.in_waiting
                    if bytes_waiting > 0:
                        print(f"{bytes_waiting} bytes waiting in buffer")

                    # Method 2: Try to read a line
                    try:
                        raw_data = self.serial_conn.readline()
                        if raw_data:
                            self.stats["bytes_received"] += len(raw_data)
                            self.stats["messages_received"] += 1
                            self.stats["last_data_time"] = datetime.now()

                            # Try to decode
                            try:
                                decoded_data = raw_data.decode("utf-8").strip()
                                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                print(
                                    f"[{timestamp}] RECEIVED: '{decoded_data}' (bytes: {len(raw_data)})"
                                )
                                self.log_data(decoded_data, raw_data, "auto_received")
                            except UnicodeDecodeError:
                                # Handle binary data
                                hex_data = raw_data.hex()
                                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                print(
                                    f"[{timestamp}] BINARY: {hex_data} (bytes: {len(raw_data)})"
                                )
                                self.log_data(hex_data, raw_data, "binary_received")

                    except Exception as read_error:
                        print(f"Read error: {read_error}")

                    # Method 3: Try reading single bytes (for devices that don't send newlines)
                    try:
                        if self.serial_conn.in_waiting > 0:
                            single_byte = self.serial_conn.read(1)
                            if single_byte:
                                print(
                                    f"Single byte: {single_byte.hex()} ('{chr(single_byte[0]) if 32 <= single_byte[0] <= 126 else '?'}')"
                                )
                    except:
                        pass

                # Progress report every 5 seconds
                if time.time() - last_activity_report > 5:
                    self.show_stats()
                    last_activity_report = time.time()

                time.sleep(0.01)  # Very short sleep

            except Exception as e:
                print(f"Monitor loop error: {e}")
                time.sleep(1)

    def show_stats(self):
        """Show monitoring statistics"""
        print(
            f"STATS: {self.stats['messages_received']} messages, {self.stats['bytes_received']} bytes total"
        )
        if self.stats["last_data_time"]:
            print(f"   Last data: {self.stats['last_data_time'].strftime('%H:%M:%S')}")
        else:
            print("   No data received yet")

    def send_command(self, command):
        """Send command with debug info"""
        if not self.serial_conn or not self.serial_conn.is_open:
            print("Serial connection not available")
            return None

        try:
            # Send command
            cmd_bytes = f"{command}\n".encode()
            bytes_sent = self.serial_conn.write(cmd_bytes)
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] SENT: '{command}' ({bytes_sent} bytes)")

            # Log the sent command
            self.log_data(command, cmd_bytes, "command_sent")

            # Wait a bit for response
            time.sleep(0.1)

            return True

        except Exception as e:
            print(f"Send error: {e}")
            return None

    def test_connection(self):
        """Test if the connection is working"""
        if not self.serial_conn or not self.serial_conn.is_open:
            print("No connection to test")
            return False

        print("Testing connection...")
        print(f"   Port open: {self.serial_conn.is_open}")
        print(f"   Bytes waiting: {self.serial_conn.in_waiting}")

        # Try to read any available data
        try:
            available_data = self.serial_conn.read(self.serial_conn.in_waiting)
            if available_data:
                print(f"   Available data: {available_data.hex()}")
            else:
                print("   No data available")
        except Exception as e:
            print(f"   Read test error: {e}")

        return True

    def stop(self):
        """Stop monitoring and close connections"""
        print("\nStopping monitor...")
        self.running = False

        if self.log_thread and self.log_thread.is_alive():
            self.log_thread.join(timeout=2)

        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

        if self.db_conn:
            self.db_conn.close()

        print("Monitor stopped")
        self.show_stats()


# Main script with enhanced debugging
if __name__ == "__main__":
    # Configuration
    PORT = "/dev/ttyUSB0"  # Change this to your port
    BAUDRATE = 9600

    print("SERIAL DEBUG LOGGER")
    print("=" * 50)
    print(f"Port: {PORT}")
    print(f"Baudrate: {BAUDRATE}")
    print("=" * 50)

    logger = DebugSerialLogger(PORT, BAUDRATE)

    try:
        # Connect
        if logger.connect():
            # Test connection
            logger.test_connection()

            # Start monitoring
            logger.start_monitoring()

            print("\nCOMMANDS:")
            print("  - Just wait to see if data arrives automatically")
            print("  - Type any command to send it")
            print("  - 'test' : Test connection")
            print("  - 'stats' : Show statistics")
            print("  - 'quit' : Exit")
            print("\nWaiting for data...")

            # Interactive loop
            while True:
                try:
                    user_input = input("\n> ").strip()

                    if user_input.lower() == "quit":
                        break
                    elif user_input.lower() == "test":
                        logger.test_connection()
                    elif user_input.lower() == "stats":
                        logger.show_stats()
                    elif user_input:
                        logger.send_command(user_input)

                except KeyboardInterrupt:
                    print("\nKeyboard interrupt")
                    break
                except EOFError:
                    print("\nInput closed")
                    break

    except Exception as e:
        print(f"Error: {e}")

    finally:
        logger.stop()
