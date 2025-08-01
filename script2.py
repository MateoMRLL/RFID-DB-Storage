import serial
import mysql.connector
from mysql.connector import Error
import threading
import time
from datetime import datetime
import sys


class AntennaSerialLogger:
    def __init__(self, port, baudrate=9600, mysql_config=None):
        self.port = port
        self.baudrate = baudrate
        self.mysql_config = mysql_config or {
            "host": "localhost",
            "database": "data_logs",
            "user": "mateo",
            "password": "password123",
            "port": 3306,
        }
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
        """Initialize MySQL database with antenna column"""
        try:
            # Connect to MySQL server
            self.db_conn = mysql.connector.connect(**self.mysql_config)

            if self.db_conn.is_connected():
                cursor = self.db_conn.cursor()

                # Create database if it doesn't exist
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS {self.mysql_config['database']}"
                )
                cursor.execute(f"USE {self.mysql_config['database']}")

                # Create table with antenna column
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS serial_logs (
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
                    )
                """
                )

                self.db_conn.commit()
                print(
                    f"MySQL database ready: {self.mysql_config['host']}:{self.mysql_config['port']}/{self.mysql_config['database']}"
                )

        except Error as e:
            print(f"MySQL connection error: {e}")
            print("Please check your MySQL configuration:")
            print(f"  Host: {self.mysql_config['host']}")
            print(f"  Port: {self.mysql_config['port']}")
            print(f"  Database: {self.mysql_config['database']}")
            print(f"  User: {self.mysql_config['user']}")
            sys.exit(1)

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

    def log_data(self, data, raw_bytes, antenna, data_type="auto_received"):
        """Log data with antenna info to MySQL"""
        try:
            if self.db_conn and self.db_conn.is_connected():
                cursor = self.db_conn.cursor()

                # Convert raw_bytes to hex string for storage
                raw_bytes_hex = (
                    raw_bytes.hex() if isinstance(raw_bytes, bytes) else str(raw_bytes)
                )

                query = """
                    INSERT INTO serial_logs (data, data_type, raw_bytes, byte_count, antenna)
                    VALUES (%s, %s, %s, %s, %s)
                """
                values = (data, data_type, raw_bytes_hex, len(raw_bytes), antenna)

                cursor.execute(query, values)
                self.db_conn.commit()
                cursor.close()

        except Error as e:
            print(f"MySQL logging error: {e}")
            # Try to reconnect if connection was lost
            self.reconnect_db()
        except Exception as e:
            print(f"Logging error: {e}")

    def reconnect_db(self):
        """Attempt to reconnect to MySQL database"""
        try:
            if self.db_conn:
                self.db_conn.close()

            print("Attempting to reconnect to MySQL...")
            self.db_conn = mysql.connector.connect(**self.mysql_config)

            if self.db_conn.is_connected():
                cursor = self.db_conn.cursor()
                cursor.execute(f"USE {self.mysql_config['database']}")
                cursor.close()
                print("MySQL reconnection successful")
                return True

        except Error as e:
            print(f"MySQL reconnection failed: {e}")
            return False

    def set_antenna(self, antenna_number):
        """Set the antenna to use (1 or 2)"""
        if antenna_number not in [1, 2]:
            print("Error: Antenna must be 1 or 2")
            return False

        self.current_antenna = antenna_number
        print(f"Antenna set to: {antenna_number}")
        return True

    def start_monitoring(self, antenna=1):
        """Start monitoring with specified antenna"""
        if self.running:
            print("Monitoring already active")
            return

        if antenna not in [1, 2]:
            print("Error: Antenna must be 1 or 2")
            return

        self.current_antenna = antenna
        self.running = True
        self.log_thread = threading.Thread(target=self._monitor_loop)
        self.log_thread.daemon = True
        self.log_thread.start()

        print("MONITORING STARTED")
        print(f"Using antenna: {self.current_antenna}")
        print("Listening for data on serial port...")
        print("-" * 50)

    def _monitor_loop(self):
        """Enhanced monitoring loop with antenna logging"""
        while self.running:
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    # Try to read a line
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
                                    f"[{timestamp}] ANTENNA {self.current_antenna}: '{decoded_data}' (bytes: {len(raw_data)})"
                                )
                                self.log_data(
                                    decoded_data,
                                    raw_data,
                                    self.current_antenna,
                                    "auto_received",
                                )
                            except UnicodeDecodeError:
                                # Handle binary data
                                hex_data = raw_data.hex()
                                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                print(
                                    f"[{timestamp}] ANTENNA {self.current_antenna} BINARY: {hex_data} (bytes: {len(raw_data)})"
                                )
                                self.log_data(
                                    hex_data,
                                    raw_data,
                                    self.current_antenna,
                                    "binary_received",
                                )

                    except Exception as read_error:
                        print(f"Read error: {read_error}")

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
        print(f"   Current antenna: {getattr(self, 'current_antenna', 'Not set')}")

    def stop(self):
        """Stop monitoring and close connections"""
        print("\nStopping monitor...")
        self.running = False

        if self.log_thread and self.log_thread.is_alive():
            self.log_thread.join(timeout=2)

        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

        if self.db_conn and self.db_conn.is_connected():
            self.db_conn.close()

        print("Monitor stopped")
        self.show_stats()


# Main script
if __name__ == "__main__":
    # Configuration
    PORT = "/dev/ttyUSB0"  # Change this to your port
    BAUDRATE = 9600

    # MySQL configuration
    MYSQL_CONFIG = {
        "host": "localhost",
        "database": "data_logs",
        "user": "mateo",
        "password": "password123",
        "port": 3306,
        "autocommit": True,
        "charset": "utf8mb4",
    }

    print("ANTENNA SERIAL LOGGER")
    print("=" * 50)
    print(f"Port: {PORT}")
    print(f"Baudrate: {BAUDRATE}")
    print(f"MySQL Host: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}")
    print(f"Database: {MYSQL_CONFIG['database']}")
    print("=" * 50)

    logger = AntennaSerialLogger(PORT, BAUDRATE, MYSQL_CONFIG)

    try:
        # Connect
        if logger.connect():
            print("\nCOMMANDS:")
            print("  - 'antenna 1' : Set antenna to 1")
            print("  - 'antenna 2' : Set antenna to 2")
            print("  - 'start' : Start monitoring")
            print("  - 'stats' : Show statistics")
            print("  - 'quit' : Exit")

            # Interactive loop - simplified to only antenna commands
            while True:
                try:
                    user_input = input("\n> ").strip().lower()

                    if user_input == "quit":
                        break
                    elif user_input == "antenna 1":
                        logger.set_antenna(1)
                    elif user_input == "antenna 2":
                        logger.set_antenna(2)
                    elif user_input == "start":
                        antenna = getattr(logger, "current_antenna", 1)
                        logger.start_monitoring(antenna)
                        print(
                            f"Monitoring started with antenna {antenna}. Press Ctrl+C to stop monitoring."
                        )
                        try:
                            while logger.running:
                                time.sleep(1)
                        except KeyboardInterrupt:
                            logger.running = False
                            print("\nMonitoring stopped.")
                    elif user_input == "stats":
                        logger.show_stats()
                    else:
                        print(
                            "Invalid command. Use 'antenna 1', 'antenna 2', 'start', 'stats', or 'quit'"
                        )

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
