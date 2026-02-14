from PyQt5.QtCore import QThread, pyqtSignal
import serial
import time


class SerialWorker(QThread):
    """
    Worker thread responsible for handling serial communication.
    Runs independently from the GUI to prevent UI blocking.
    """

    # Signals emitted by the worker thread
    data_received = pyqtSignal(str)           # Emitted when data is read from device
    connection_status = pyqtSignal(bool, str)  # Emitted on connection/disconnection

    def __init__(self, port: str, baud_rate: int):
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.running = True
        self.send_queue = []

    def run(self):
        """
        Main loop of the worker thread.
        Handles connection, reading, and writing.
        """
        try:
            # --- CONNECT ---
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=0.1  # Non-blocking read
            )

            # Allow Bluetooth to stabilize
            time.sleep(5)

            if self.ser and self.ser.isOpen():
                self.send_data("INIT_CHECK")
                self.connection_status.emit(
                    True,
                    f"Connected to {self.port} at {self.baud_rate} baud. Sent INIT_CHECK to confirm link."
                )

            # --- I/O LOOP ---
            while self.ser and self.running and self.ser.isOpen():

                # --- READ ---
                if self.ser.in_waiting > 0:
                    try:
                        raw_data = self.ser.readline()

                        try:
                            data = raw_data.decode("utf-8").strip()
                            if data:
                                self.data_received.emit(f"RX: {data}")
                        except UnicodeDecodeError:
                            self.data_received.emit(
                                f"WARNING: Corrupt data received and discarded ({len(raw_data)} bytes)."
                            )

                    except serial.SerialException as e:
                        self.connection_status.emit(False, f"Read Error: {e}")
                        break
                    except Exception as e:
                        self.connection_status.emit(False, f"Unexpected Read Error: {e}")
                        break

                # --- WRITE ---
                if self.send_queue:
                    data_to_send = self.send_queue.pop(0)
                    try:
                        self.ser.write(data_to_send)
                        self.data_received.emit(
                            f"TX: {data_to_send.decode().strip()}"
                        )
                    except serial.SerialException as e:
                        self.connection_status.emit(False, f"Write Error: {e}")
                        break

                time.sleep(0.01)

        except serial.SerialException as e:
            self.connection_status.emit(False, f"Connection Failed: {e}")

        finally:
            self.stop_serial()
            self.connection_status.emit(False, "Disconnected.")

    def send_data(self, data: str):
        """
        Adds outgoing command to send queue.
        """
        command = data.encode("utf-8") + b"\n"
        self.send_queue.append(command)

    def stop_serial(self):
        """
        Stops worker loop and safely closes serial connection.
        """
        if not self.running:
            return

        self.running = False


        if self.ser:
            try:
                self.ser.close()
            except OSError as e:
                if "Bad file descriptor" in str(e):
                    print(f"Ignored OSError during serial close: {e}")
                else:
                    raise e
            except Exception as e:
                print(f"Error during serial close: {e}")
            finally:
                self.ser = None
