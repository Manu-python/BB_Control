from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget
from core.serial_worker import SerialWorker
from core.keymap import KeyMap
from core.logger import AppLogger
from ui.control_tab import ControlTab
from ui.settings_tab import SettingsTab
from ui.styles import DARK_STYLE
from utils.port_scanner import get_available_ports


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("BB Control")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(DARK_STYLE)

        self.worker_thread = None
        self.keymap = KeyMap()

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

        # Tabs
        self.control_tab = ControlTab(self.keymap)
        self.settings_tab = SettingsTab(self.keymap)

        self.tab_widget.addTab(self.control_tab, "Control")
        self.tab_widget.addTab(self.settings_tab, "Settings")

        # Signal wiring
        self.control_tab.command_requested.connect(self.send_command)

        self.settings_tab.connect_requested.connect(self.start_connection)
        self.settings_tab.disconnect_requested.connect(self.stop_connection)
        self.settings_tab.refresh_requested.connect(self.refresh_ports)
        self.settings_tab.key_updated.connect(self.handle_key_update)

    # -------------------------------------------------
    # Serial Logic
    # -------------------------------------------------

    def start_connection(self, port, baud):
        self.worker_thread = SerialWorker(port, baud)
        self.worker_thread.data_received.connect(self.log_message)
        self.worker_thread.connection_status.connect(self.handle_connection_status)
        self.worker_thread.start()

    def stop_connection(self):
        if self.worker_thread:
            self.worker_thread.stop_serial()
            self.worker_thread.wait()
            self.worker_thread = None

    def send_command(self, command):
        if self.worker_thread:
            self.worker_thread.send_data(command)

    # -------------------------------------------------
    # Port Handling
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
        except ValueError:
            pass

    # -------------------------------------------------
    # Logging
    # -------------------------------------------------

    def log_message(self, message):
        html = AppLogger.format(message)
        self.settings_tab.log_message(html)

        if message.startswith("TX"):
            self.control_tab.log_tx(html)

    # -------------------------------------------------
    # UI Updates
    # -------------------------------------------------

    def handle_connection_status(self, connected, message):
        self.settings_tab.set_connection_state(connected)
        self.control_tab.enable_buttons(connected)
        self.log_message(message)
