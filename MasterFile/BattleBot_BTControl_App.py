import sys
import serial
import serial.tools.list_ports
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QComboBox, QLineEdit, 
    QTextEdit, QLabel, QGroupBox, QTabWidget, QGridLayout,
    QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt

# --- 1. SERIAL WORKER THREAD ---
class SerialWorker(QThread):
    # Signals emitted by the worker thread
    data_received = pyqtSignal(str) # Emitted when data is read from the device
    connection_status = pyqtSignal(bool, str) # Emitted on connection/disconnection
    
    def __init__(self, port, baud_rate):
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.running = True
        self.send_queue = [] # Queue for data to be sent

    def run(self):
        """Main loop for the thread: attempts to connect and then handles I/O."""
        
        try:
            # 1. Connect
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=0.1  # Low timeout for non-blocking read
            )
            # Increased wait time for Bluetooth stabilization on connection (5 seconds)
            time.sleep(5) 
            
            if self.ser and self.ser.isOpen():
                # Send an initial command to confirm the link is active.
                self.send_data("INIT_CHECK")
                self.connection_status.emit(True, f"Connected to {self.port} at {self.baud_rate} baud. Sent INIT_CHECK to confirm link.")
            
            # 2. I/O Loop
            while self.ser and self.running and self.ser.isOpen():
                # Read incoming data
                if self.ser.in_waiting > 0:
                    try:
                        # Read until newline
                        raw_data = self.ser.readline()
                        
                        # --- FIX: Safe Data Decoding to Prevent Crash (UnicodeDecodeError) ---
                        try:
                            # Decode the raw bytes and strip whitespace
                            data = raw_data.decode('utf-8').strip()
                            if data:
                                self.data_received.emit(f"RX: {data}")
                        except UnicodeDecodeError:
                            # If decoding fails (corrupt data), log a warning and discard
                            self.data_received.emit(f"WARNING: Corrupt data received and discarded ({len(raw_data)} bytes).")

                    except serial.SerialException as e:
                        self.connection_status.emit(False, f"Read Error: {e}")
                        break
                    except Exception as e:
                        # Catch any other unexpected read errors that might occur
                        self.connection_status.emit(False, f"Unexpected Read Error: {e}")
                        break
                
                # Write outgoing data from queue
                if self.send_queue:
                    data_to_send = self.send_queue.pop(0)
                    try:
                        self.ser.write(data_to_send)
                        # Echo sent data to log, excluding the newline
                        self.data_received.emit(f"TX: {data_to_send.decode().strip()}")
                    except serial.SerialException as e:
                        self.connection_status.emit(False, f"Write Error: {e}")
                        break
                
                # Short delay to prevent 100% CPU usage
                time.sleep(0.01) 

        except serial.SerialException as e:
            self.connection_status.emit(False, f"Connection Failed: {e}")
            
        finally:
            self.stop_serial()
            self.connection_status.emit(False, "Disconnected.")

    def send_data(self, data):
        """Adds data to the queue to be sent by the run loop."""
        # Convert string command to bytes and append the required newline character ('\n')
        command = data.encode('utf-8') + b'\n'
        self.send_queue.append(command)

    def stop_serial(self):
        """Stops the worker loop and closes the serial port."""
        self.running = False
        if self.ser:
            try:
                # Attempt to close the serial port
                self.ser.close()
            except OSError as e:
                # Catch the 'Bad file descriptor' error (Errno 9)
                if 'Bad file descriptor' in str(e):
                    print(f"Warning: Ignored OSError during serial close: {e}")
                else:
                    raise e
            except Exception as e:
                print(f"Error during serial close: {e}")
            finally:
                self.ser = None


# --- 2. MAIN APPLICATION WINDOW ---
class ESP32ControllerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESP32 Bluetooth Serial Controller (Dark Mode)") 
        self.setGeometry(100, 100, 750, 600)
        self.worker_thread = None
        self.baud_rate = 115200 

        # NEW: Default keyboard key mappings
        self.key_map = {
            "A1": "W", # Forward
            "A2": "X", # Backward
            "A0": "S", # Stop
            "A3": "D", # Right
            "A4": "A", # Left
            "A5": "Q", # Top Left
            "A6": "E", # Top Right
            "A7": "Z", # Bottom Left
            "A8": "C",  # Bottom Right
            "A9": "F", # Turn Right
            "A10": "R", # Turn Left
            "A11": "G", # Open Gripper
            "A12": "T", # Close Gripper
            "A13": "Y" # Move Arm
        }

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Initialize the logs before init_ui for logging in find_ports
        self.full_log_area = QTextEdit()
        self.control_log_area = QTextEdit()

        # Apply global dark theme stylesheet
        self.setStyleSheet(
            """
            QMainWindow, QWidget, QTabWidget, QTabWidget::pane { 
                background-color: #2B2B2B; 
                color: #FFFFFF; 
            }
            QTabWidget::tab-bar {
                left: 5px; /* move bar to the right */
            }
            QTabBar::tab {
                background: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #505050;
                border-bottom-color: #2B2B2B; /* match background */
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 15px;
            }
            QTabBar::tab:selected {
                background: #1E1E1E; /* Darker background for active tab */
                border-color: #505050;
                border-bottom-color: #1E1E1E; /* make it look connected */
                font-weight: bold;
            }
            QGroupBox { 
                border: 1px solid #505050; 
                margin-top: 10px; 
                padding-top: 10px; 
                font-weight: bold; 
                color: #FFFFFF;
                border-radius: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                color: #AAAAAA;
            }
            QLabel { color: #FFFFFF; }
            QComboBox, QLineEdit {
                background-color: #3C3C3C;
                border: 1px solid #505050;
                padding: 5px;
                color: #FFFFFF;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #505050;
                border: 1px solid #666666;
                color: #FFFFFF;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            """
        )

        # Initialize the keep-alive timer
        self.keep_alive_timer = QTimer(self)
        self.keep_alive_timer.setInterval(500) # Ping every 0.5 seconds (500 ms)
        self.keep_alive_timer.timeout.connect(lambda: self.send_command("PING")) # PING command
        
        # Set focus policy to capture key presses across the main window
        self.setFocusPolicy(Qt.StrongFocus) 
        
        # Helper dictionary for mapping command to button object
        self.button_map = {} 
        
        # FIX: Call the new init_ui method to set up the tabs
        self.init_ui()
        self.find_ports()

    def init_ui(self):
        """Initializes the main user interface layout using QTabWidget."""
        
        # 1. Create the Tab Widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # 2. Create individual tab contents
        control_tab = self.init_control_tab()
        settings_tab = self.init_settings_tab()

        # 3. Add tabs to the main widget
        self.tab_widget.addTab(control_tab, "Control Console")
        self.tab_widget.addTab(settings_tab, "Settings & Log")
        
    # Helper function to get the current key from the map
    def get_key(self, command):
        return self.key_map.get(command, "?")

    def init_control_tab(self):
        """
        Initializes the Control Tab with directional buttons (Forward, Backward, Stop).
        """
        control_widget = QWidget()
        main_h_layout = QHBoxLayout(control_widget)

        # Left Column: Buttons
        left_column = QWidget()
        left_v_layout = QVBoxLayout(left_column)
        left_v_layout.setContentsMargins(0, 0, 0, 0)

        # --- Directional Control Group ---
        command_group = QGroupBox("Control Console (Keyboard Enabled)")
        control_section = QVBoxLayout()
        command_group.setLayout(control_section)
        control_grid = QGridLayout()
        turn_grid = QGridLayout()
        # control_grid.setSpacing(10)  # May add this line later for spacing
        
        base_style = "color: white; padding: 15px; font-weight: bold;"
        
        # Helper to create and style a button
        def create_button(command, default_color):
            btn = QPushButton(f"{command} ({self.get_key(command)})")
            btn.setEnabled(False) 
            btn.clicked.connect(lambda: self.send_command(command)) 
            btn.setStyleSheet(f"background-color: {default_color}; {base_style}")
            self.button_map[command] = btn
            return btn

        # A1: Forward 
        self.forward_button = create_button("A1", "#418DF1")
        control_grid.addWidget(self.forward_button, 0, 1)

        # A0: Stop 
        self.stop_button = create_button("A0", "#E62626")
        control_grid.addWidget(self.stop_button, 1, 1)

        # A2: Backward 
        self.backward_button = create_button("A2", "#418DF1")
        control_grid.addWidget(self.backward_button, 2, 1)

        # A3: Right 
        self.right_button = create_button("A3", "#418DF1")
        control_grid.addWidget(self.right_button, 1, 2)

        # A4: Left 
        self.left_button = create_button("A4", "#418DF1")
        control_grid.addWidget(self.left_button, 1, 0)

        # A5: Top Left 
        self.topLeft_button = create_button("A5", "#418DF1")
        control_grid.addWidget(self.topLeft_button, 0, 0)

        # A6: Top Right 
        self.topRight_button = create_button("A6", "#418DF1")
        control_grid.addWidget(self.topRight_button, 0, 2)

        # A7: Bottom Left 
        self.botLeft_button = create_button("A7", "#418DF1")
        control_grid.addWidget(self.botLeft_button, 2, 0)

        # A8: Bottom Right 
        self.botRight_button = create_button("A8", "#418DF1")
        control_grid.addWidget(self.botRight_button, 2, 2)

        # A9: Left Turn
        self.turnLeft_button = create_button("A9", "#418DF1")
        turn_grid.addWidget(self.turnLeft_button, 0, 0)

        # A10: Right Turn
        self.turnRight_button = create_button("A10", "#418DF1")
        turn_grid.addWidget(self.turnRight_button, 0, 1)

        # A11: Open Gripper
        self.openGripper_button = create_button("A11", "#418DF1")
        turn_grid.addWidget(self.openGripper_button, 1, 0)

        # A12: Close Gripper
        self.closeGripper_button = create_button("A12", "#418DF1")
        turn_grid.addWidget(self.closeGripper_button, 1, 1)

        # A13: Move Arm
        self.moveArm_button = create_button("A13", "#418DF1")
        turn_grid.addWidget(self.moveArm_button, 2, 0, 1, 2) # Span two columns

        control_section.addLayout(control_grid)
        control_section.addLayout(turn_grid)
        command_group.setLayout(control_section)
        left_v_layout.addWidget(command_group)
        left_v_layout.addStretch(1)
        main_h_layout.addWidget(left_column, 1) # Left column takes 1/3 of the width

        # Right Column Log Area
        right_column = QWidget()
        right_v_layout = QVBoxLayout(right_column)
        right_v_layout.setContentsMargins(0, 0, 0, 0) 

        # --- Log Area (TX Only) ---
        log_label = QLabel("Outgoing Commands (TX Log):")
        right_v_layout.addWidget(log_label)
        
        self.control_log_area.setReadOnly(True)
        self.control_log_area.setStyleSheet("background-color: #1E1E1E; border: 1px solid #505050; font-family: monospace; color: #E0E0E0;")
        right_v_layout.addWidget(self.control_log_area)

        # Right column takes 2/3 of the width
        main_h_layout.addWidget(right_column, 0.5) 

        return control_widget

    def init_settings_tab(self):
        """Initializes the Settings Tab (Connection Settings, Key Mapping, and Full Log)."""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)

        # --- 1. Connection Group ---
        connection_group = QGroupBox("Connection Settings")
        conn_layout = QHBoxLayout()

        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(250)
        
        self.baud_line = QLineEdit(str(self.baud_rate)) 
        self.baud_line.setMaximumWidth(100)
        baud_label = QLabel("Baud Rate:")

        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet("background-color: #38761D; color: white; border-radius: 4px; padding: 8px 15px;")
        self.connect_button.clicked.connect(self.toggle_connection)
        
        self.refresh_button = QPushButton("Refresh Ports")
        self.refresh_button.clicked.connect(self.find_ports)

        conn_layout.addWidget(self.port_combo)
        conn_layout.addWidget(self.refresh_button)
        conn_layout.addWidget(baud_label)
        conn_layout.addWidget(self.baud_line)
        conn_layout.addWidget(self.connect_button)
        
        connection_group.setLayout(conn_layout)
        layout.addWidget(connection_group)
        
        # --- 2. Key Mapping Group (NEW FEATURE) ---
        key_map_group = QGroupBox("Keyboard Key Mapping")
        key_grid = QGridLayout()
        
        # List of command names and their corresponding commands
        key_commands = [
            ("Forward (A1)", "A1"), ("Backward (A2)", "A2"), ("Stop (A0)", "A0"), 
            ("Left (A4)", "A4"), ("Right (A3)", "A3"), 
            ("Top Left (A5)", "A5"), ("Top Right (A6)", "A6"), 
            ("Bottom Left (A7)", "A7"), ("Bottom Right (A8)", "A8"),
            ("Turn Left (A10)", "A10"), ("Turn Right (A9)", "A9"), 
            ("Open Gripper (A11)", "A11"), ("Close Gripper (A12)", "A12"), 
            ("Move Arm (A13)", "A13")
        ]
        
        # Create LineEdits and labels for each command
        self.key_line_edits = {}
        row = 0
        col = 0
        for label_text, command in key_commands:
            label = QLabel(label_text + ":")
            
            line_edit = QLineEdit(self.get_key(command))
            line_edit.setMaxLength(1) # Only allow a single character
            line_edit.setMaximumWidth(50)
            # Store the QLineEdit reference for validation and dynamic updates
            self.key_line_edits[command] = line_edit
            # Connect editingFinished signal to validation/update function
            line_edit.editingFinished.connect(lambda cmd=command, le=line_edit: self.update_key_map(cmd, le))

            key_grid.addWidget(label, row, col)
            key_grid.addWidget(line_edit, row, col + 1)
            
            # Simple grid layout (3 rows, 6 columns)
            col += 2
            if col >= 6:
                col = 0
                row += 1

        key_map_group.setLayout(key_grid)
        layout.addWidget(key_map_group)

        # --- 3. Full Log/Status Area ---
        log_label = QLabel("Full Communication Log (TX, RX, Status):")
        layout.addWidget(log_label)
        
        self.full_log_area.setReadOnly(True)
        self.full_log_area.setStyleSheet("background-color: #1E1E1E; border: 1px solid #505050; font-family: monospace; color: #E0E0E0;")
        layout.addWidget(self.full_log_area)

        return settings_widget
    
    def update_key_map(self, command, line_edit):
        """
        Validates the new key input and updates the key map and button labels.
        """
        new_key = line_edit.text().upper().strip()

        # 1. Validation: Must be a single, non-empty, alphanumeric character
        if not new_key or len(new_key) != 1 or not new_key.isalnum():
            # If invalid, revert the text box to the current key and show a message
            QMessageBox.critical(self, "Invalid Key", "Key must be a single, non-empty letter or number.")
            line_edit.setText(self.key_map.get(command, "?"))
            return

        # 2. Check for Duplicate Key Mapping
        for cmd, key in self.key_map.items():
            if key == new_key and cmd != command:
                # If duplicate, revert and show a message
                QMessageBox.critical(self, "Duplicate Key", f"The key '{new_key}' is already assigned to command {cmd}.")
                line_edit.setText(self.key_map.get(command, "?"))
                return

        # 3. Update the map and UI
        self.key_map[command] = new_key
        
        # Update the corresponding button text in the Motor Control tab
        if command in self.button_map:
            current_text = self.button_map[command].text().split('(')[0].strip()
            self.button_map[command].setText(f"{current_text} ({new_key})")
            
        self.log_message(f"Key map updated: '{command}' is now controlled by key '{new_key}'.", "info")


    def find_ports(self):
        """Populates the port selection dropdown."""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            self.log_message("No serial ports found. Is your ESP32 paired/connected?", "error") 
            return

        for port, desc, hwid in sorted(ports):
            # Prioritize ports that look like Bluetooth or Arduino
            display_text = f"{port} ({desc})"
            self.port_combo.addItem(display_text, port)
            if "ESP32" in desc or "Bluetooth" in desc or "USB Serial" in desc:
                 # Move potential ports to the top
                 current_text = self.port_combo.itemText(0)
                 self.port_combo.setItemText(0, display_text)
                 self.port_combo.setItemText(self.port_combo.count() - 1, current_text)

        self.log_message(f"Found {len(ports)} ports. Select your ESP32 serial or Bluetooth port.")


    def toggle_connection(self):
        """Starts or stops the serial connection thread."""
        if self.worker_thread and self.worker_thread.isRunning():
            # Disconnect sequence
            self.worker_thread.stop_serial()
            self.worker_thread.wait() # Wait for the thread to finish cleanly
        else:
            # Connect sequence
            selected_port = self.port_combo.currentData()
            if not selected_port:
                self.log_message("Please select a valid port.", "error")
                return

            try:
                new_baud = int(self.baud_line.text())
                self.baud_rate = new_baud
            except ValueError:
                self.log_message("Baud Rate must be a number.", "error")
                return
            
            self.log_message(f"Attempting to connect to {selected_port} at {self.baud_rate}...")
            
            # Create and start the worker thread
            self.worker_thread = SerialWorker(selected_port, self.baud_rate)
            self.worker_thread.data_received.connect(self.log_message)
            self.worker_thread.connection_status.connect(self.update_ui_on_status)
            self.worker_thread.start()

    def update_ui_on_status(self, is_connected, message):
        """Updates UI elements based on connection status from the worker thread."""
        self.log_message(message, "success" if is_connected else "error")
        
        # Get all directional buttons
        buttons = [
            self.forward_button, self.stop_button, self.backward_button,
            self.right_button, self.left_button, self.topLeft_button,
            self.topRight_button, self.botLeft_button, self.botRight_button,
            self.turnRight_button, self.turnLeft_button, self.openGripper_button, 
            self.closeGripper_button, self.moveArm_button
        ]

        if is_connected:
            self.connect_button.setText("Disconnect")
            self.connect_button.setStyleSheet("background-color: #CC0000; color: white; border-radius: 4px; padding: 8px 15px;")
            self.port_combo.setEnabled(False)
            self.baud_line.setEnabled(False)
            self.refresh_button.setEnabled(False)
            
            # Enable all directional buttons
            for button in buttons:
                button.setEnabled(True)
            
            # Disable key map line edits while connected to prevent accidental changes
            for le in self.key_line_edits.values():
                 le.setEnabled(False)

            self.keep_alive_timer.start() 
        else:
            self.connect_button.setText("Connect")
            self.connect_button.setStyleSheet("background-color: #38761D; color: white; border-radius: 4px; padding: 8px 15px;")
            self.port_combo.setEnabled(True)
            self.baud_line.setEnabled(True)
            self.refresh_button.setEnabled(True)
            
            # Disable all directional buttons
            for button in buttons:
                button.setEnabled(False)
                
            # Re-enable key map line edits
            for le in self.key_line_edits.values():
                 le.setEnabled(True)

            self.keep_alive_timer.stop()
            if self.worker_thread:
                 self.worker_thread.stop_serial()
                 self.worker_thread.wait()
                 self.worker_thread = None

    def send_command(self, command_str):
        """
        Sends a specific command string (like 'A1', 'A2', or 'A0') via the worker thread.
        """
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.send_data(command_str)
        else:
            self.log_message(f"Cannot send '{command_str}'. Not connected.", "error")

    def set_button_style(self, command, is_pressed):
        """
        Applies or resets the visual style for a control button to show a press effect.
        """
        button = self.button_map.get(command)
        
        # Define the colors used in init_control_tab
        base_style = "color: white; padding: 15px; font-weight: bold;"
        
        # --- Define Colors ---
        # Blue for movement commands, Red for Stop
        original_color = "#E62626" if command == "A0" else "#418DF1"
        pressed_color = "#C3552D" if command == "A0" else "#0E4AAA"
        
        if button and button.isEnabled():
            if is_pressed:
                # Apply pressed style (darker color, white border to highlight)
                style = f"background-color: {pressed_color}; {base_style} border: 3px solid white;"
            else:
                # Reset to original style 
                style = f"background-color: {original_color}; {base_style}"
            
            button.setStyleSheet(style)
            
    def is_line_edit_focused(self):
        """Returns True if any QLineEdit (including key mapping fields) is currently focused."""
        focus_widget = QApplication.focusWidget()
        return isinstance(focus_widget, QLineEdit)


    def keyPressEvent(self, event):
        """
        Captures keyboard events to send control commands using dynamic key map.
        """
        # 1. Block control commands if a text input field is focused
        if self.is_line_edit_focused():
            super().keyPressEvent(event)
            return
            
        # 2. Process control command if connected
        if self.worker_thread and self.worker_thread.isRunning():
            
            # Get the character pressed, convert to uppercase
            # Use event.text() for standard alphanumeric keys
            key_char = event.text().upper()
            command = None
            
            # Reverse lookup: map the key character back to the command (A0-A8)
            # Create the reverse map dynamically for robustness
            reverse_key_map = {v: k for k, v in self.key_map.items()}
            
            command = reverse_key_map.get(key_char)
            
            if command:
                self.send_command(command)
                # Set the visual "pressed" state
                self.set_button_style(command, True)
        
        super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event):
        """
        Captures keyboard events to reset button graphics when the key is released.
        """
        # 1. Block key release events if a text input field is focused
        if self.is_line_edit_focused():
            super().keyReleaseEvent(event)
            return
            
        # Only reset style if the key is NOT auto-repeating (i.e., the user physically released it)
        if not event.isAutoRepeat():
            
            key_char = event.text().upper()
            command = None
            
            reverse_key_map = {v: k for k, v in self.key_map.items()}
            command = reverse_key_map.get(key_char)
            
            if command:
                # Reset the visual style
                self.set_button_style(command, False) 

        super().keyReleaseEvent(event)


    def log_message(self, message, message_type="info"):
        """Displays a message in the log area with color coding."""
        timestamp = time.strftime("[%H:%M:%S]")
        
        # Adjusted colors for better visibility on a dark background
        if message_type == "success":
            color = "#7FFF00" # Bright Green
        elif message_type == "error":
            color = "#FF4500" # Red-Orange
        elif message_type == "warning":
            color = "#FFFF00" # Yellow
        elif message_type.startswith("RX"):
            color = "#4CAF50" # Standard Green
        elif message_type.startswith("TX"):
            color = "#9932CC" # Purple/Orchid
        else:
            color = "#E0E0E0" # Light Grey (info/default)

        # Timestamp color is white (#FFFFFF)
        html_message = f'<span style="color: #FFFFFF;"><b>{timestamp}</b></span> <span style="color: {color};">{message}</span>'
        
        # LOGIC: TX messages go to both logs, everything else only goes to the full log.
        if message_type.startswith("TX"):
            # Outgoing messages go to the Control (TX only) log
            self.control_log_area.append(html_message)
            # And also to the Full log
            self.full_log_area.append(html_message)
        else:
            # All other messages (RX, status, error, info) go ONLY to the full log
            self.full_log_area.append(html_message)


    def closeEvent(self, event):
        """Ensure the serial connection is closed when the app is closed."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop_serial()
            self.worker_thread.wait()
        self.keep_alive_timer.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ESP32ControllerApp()
    window.show()
    sys.exit(app.exec_())
