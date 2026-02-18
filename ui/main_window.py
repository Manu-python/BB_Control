from pathlib import Path

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QApplication
from PyQt5.QtCore import QTimer, Qt

from core.serial_worker import SerialWorker
from core.logger import AppLogger
from core.config_store import ConfigStore
from core.command_registry import CommandRegistry
from core.keymap import KeyMap

from ui.control_tab import ControlTab
from ui.settings_tab import SettingsTab
from ui.styles import DARK_STYLE
from utils.port_scanner import get_available_ports


class MainWindow(QMainWindow):
    """
    Application orchestrator.
    Handles config loading, UI wiring, thread lifecycle,
    and routing between UI and backend.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("BB Control")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(DARK_STYLE)
        self.setFocusPolicy(Qt.StrongFocus)

        # -------------------------------------------------
        # Config loading
        # -------------------------------------------------
        self.base_dir = Path(__file__).resolve().parents[1]
        self.store = ConfigStore(self.base_dir)

        commands_dict = self.store.read_json("commands.json", default={})
        layout_dict = self.store.read_json("ui_layout.json", default={})
        keymap_dict = self.store.read_json("keymap.json", default={})

        self.registry = CommandRegistry(commands_dict)
        self.keymap = KeyMap(keymap_dict)
        self.layout_cfg = layout_dict

        # -------------------------------------------------
        # Thread + timers
        # -------------------------------------------------
        self.worker_thread = None

        self.keep_alive_timer = QTimer(self)
        self.keep_alive_timer.setInterval(500)
        self.keep_alive_timer.timeout.connect(lambda: self.send_command("PING"))

        # -------------------------------------------------
        # UI
        # -------------------------------------------------
        self.init_ui()
        self.refresh_ports()

    # -------------------------------------------------
    # UI Setup
    # -------------------------------------------------

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self.control_tab = ControlTab(self.keymap, self.registry, self.layout_cfg)
        self.settings_tab = SettingsTab(self.keymap, self.registry)

        self.tab_widget.addTab(self.control_tab, "Control")
        self.tab_widget.addTab(self.settings_tab, "Settings")

        # -------------------------------------------------
        # SIGNAL WIRING (CRITICAL)
        # -------------------------------------------------

        # Commands
        self.control_tab.command_requested.connect(self.send_command)

        # Connection signals
        self.settings_tab.connect_requested.connect(self.start_connection)
        self.settings_tab.disconnect_requested.connect(self.stop_connection)
        self.settings_tab.refresh_requested.connect(self.refresh_ports)

        # Key updates
        self.settings_tab.key_updated.connect(self.handle_key_update)

    # -------------------------------------------------
    # Serial Lifecycle
    # -------------------------------------------------

    def start_connection(self, port, baud):
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.log_message(f"Connecting to {port} at {baud}...", "info")

        self.worker_thread = SerialWorker(port, baud)
        self.worker_thread.data_received.connect(self.log_message)
        self.worker_thread.connection_status.connect(self.handle_connection_status)

        self.worker_thread.start()

    def stop_connection(self):
        print("STOP CONNECTION CALLED")

        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop_serial()
            self.worker_thread.wait()

        self.worker_thread = None
        self.keep_alive_timer.stop()

        # Update UI immediately
        self.settings_tab.set_connection_state(False)
        self.control_tab.enable_buttons(False)

        self.log_message("Disconnected.", "warning")

    def handle_connection_status(self, connected, message):
        self.settings_tab.set_connection_state(connected)
        self.control_tab.enable_buttons(connected)

        if connected:
            self.keep_alive_timer.start()
        else:
            self.keep_alive_timer.stop()
            self.worker_thread = None

        self.log_message(message, "success" if connected else "error")

    # -------------------------------------------------
    # Command Sending
    # -------------------------------------------------

    def send_command(self, command_code):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.send_data(command_code)
        else:
            self.log_message(f"Cannot send '{command_code}'. Not connected.", "error")

    # -------------------------------------------------
    # Ports
    # -------------------------------------------------

    def refresh_ports(self):
        ports = get_available_ports()
        self.settings_tab.set_ports(ports)

    # -------------------------------------------------
    # Key Mapping
    # -------------------------------------------------

    def handle_key_update(self, command, new_key):
        try:
            self.keymap.update_key(command, new_key)
        except ValueError as e:
            self.settings_tab.set_key_text(command, self.keymap.get_key(command))
            self.log_message(str(e), "error")
            return

        # Save config
        self.store.write_json("keymap.json", self.keymap.get_all())

        # Update UI labels
        self.control_tab.refresh_button_labels()

        self.log_message(f"Key updated: {command} → {new_key}", "success")

    # -------------------------------------------------
    # Logging
    # -------------------------------------------------

    def log_message(self, message, message_type="info"):
        html = AppLogger.format(message, message_type)

        self.settings_tab.log_message(html)

        if str(message).startswith("TX"):
            self.control_tab.log_tx(html)

    # -------------------------------------------------
    # Keyboard Control
    # -------------------------------------------------

    def keyPressEvent(self, event):
        from PyQt5.QtWidgets import QLineEdit

        focus_widget = QApplication.focusWidget()
        if isinstance(focus_widget, QLineEdit):
            super().keyPressEvent(event)
            return

        if self.worker_thread and self.worker_thread.isRunning():
            key_char = event.text().upper()
            command = self.keymap.get_command_from_key(key_char)

            if command:
                self.send_command(command)

        super().keyPressEvent(event)

    # -------------------------------------------------
    # Cleanup
    # -------------------------------------------------

    def closeEvent(self, event):
        self.stop_connection()
        event.accept()
