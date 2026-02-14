from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLineEdit,
    QLabel, QGroupBox, QGridLayout,
    QTextEdit
)
from PyQt5.QtCore import pyqtSignal


class SettingsTab(QWidget):
    """
    Settings tab handles:
    - Serial connection UI
    - Key mapping UI
    - Full communication log
    Emits signals for logic handling.
    """

    # Signals to MainWindow
    connect_requested = pyqtSignal(str, int)
    disconnect_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    key_updated = pyqtSignal(str, str)

    def __init__(self, keymap):
        super().__init__()
        self.keymap = keymap
        self.connected = False
        self.key_line_edits = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # -----------------------------
        # 1️⃣ Connection Group
        # -----------------------------
        connection_group = QGroupBox("Connection Settings")
        conn_layout = QHBoxLayout()

        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(250)

        self.baud_line = QLineEdit("115200")
        self.baud_line.setMaximumWidth(100)

        self.connect_button = QPushButton("Connect")
        self.refresh_button = QPushButton("Refresh Ports")

        conn_layout.addWidget(self.port_combo)
        conn_layout.addWidget(self.refresh_button)
        conn_layout.addWidget(QLabel("Baud Rate:"))
        conn_layout.addWidget(self.baud_line)
        conn_layout.addWidget(self.connect_button)

        connection_group.setLayout(conn_layout)
        layout.addWidget(connection_group)

        # -----------------------------
        # 2️⃣ Key Mapping Group
        # -----------------------------
        key_group = QGroupBox("Keyboard Key Mapping")
        key_layout = QGridLayout()

        row = 0
        col = 0

        for command, key in self.keymap.get_all().items():
            label = QLabel(f"{command}:")
            line_edit = QLineEdit(key)
            line_edit.setMaxLength(1)
            line_edit.setMaximumWidth(50)

            # connect editing event
            line_edit.editingFinished.connect(
                lambda cmd=command, le=line_edit: self.emit_key_update(cmd, le)
            )

            self.key_line_edits[command] = line_edit

            key_layout.addWidget(label, row, col)
            key_layout.addWidget(line_edit, row, col + 1)

            col += 2
            if col >= 6:
                col = 0
                row += 1

        key_group.setLayout(key_layout)
        layout.addWidget(key_group)

        # -----------------------------
        # 3️⃣ Full Log
        # -----------------------------
        layout.addWidget(QLabel("Full Communication Log:"))

        self.full_log_area = QTextEdit()
        self.full_log_area.setReadOnly(True)
        layout.addWidget(self.full_log_area)

        # -----------------------------
        # Connect Button Behavior
        # -----------------------------
        self.connect_button.clicked.connect(self.handle_connect_button)
        self.refresh_button.clicked.connect(
            lambda: self.refresh_requested.emit()
        )

    # -------------------------------------------------
    # Signal Emitters
    # -------------------------------------------------

    def handle_connect_button(self):
        if not self.connected:
            port = self.port_combo.currentData()
            if not port:
                return

            try:
                baud = int(self.baud_line.text())
            except ValueError:
                return

            self.connect_requested.emit(port, baud)
        else:
            self.disconnect_requested.emit()

    def emit_key_update(self, command, line_edit):
        new_key = line_edit.text().upper().strip()
        self.key_updated.emit(command, new_key)

    # -------------------------------------------------
    # Methods called by MainWindow
    # -------------------------------------------------

    def set_ports(self, ports):
        self.port_combo.clear()
        for port, desc, hwid in ports:
            self.port_combo.addItem(f"{port} ({desc})", port)

    def set_connection_state(self, connected: bool):
        self.connected = connected

        if connected:
            self.connect_button.setText("Disconnect")
            self.connect_button.setStyleSheet("background-color: #CC0000; color: white;")
            self.port_combo.setEnabled(False)
            self.baud_line.setEnabled(False)
            self.refresh_button.setEnabled(False)
        else:
            self.connect_button.setText("Connect")
            self.connect_button.setStyleSheet("background-color: #38761D; color: white;")
            self.port_combo.setEnabled(True)
            self.baud_line.setEnabled(True)
            self.refresh_button.setEnabled(True)

        for le in self.key_line_edits.values():
            le.setEnabled(not connected)

    def log_message(self, html_message):
        self.full_log_area.append(html_message)
