from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLineEdit,
    QLabel, QGroupBox, QGridLayout,
    QTextEdit, QMessageBox
)
from PyQt5.QtCore import pyqtSignal


class SettingsTab(QWidget):
    """
    Single responsibility:
    Settings UI (ports/baud, key mapping editor, full log).
    Emits signals; does not manage threads.
    """

    connect_requested = pyqtSignal(str, int)
    disconnect_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    key_updated = pyqtSignal(str, str)

    def __init__(self, keymap, command_registry):
        super().__init__()
        self.keymap = keymap
        self.registry = command_registry
        self.connected = False
        self.key_line_edits = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Connection
        connection_group = QGroupBox("Connection Settings")
        conn_layout = QHBoxLayout(connection_group)

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

        layout.addWidget(connection_group)

        # Key mapping editor
        key_group = QGroupBox("Keyboard Key Mapping")
        key_grid = QGridLayout(key_group)

        # Only show non-hidden commands (students can hide in commands.json)
        commands = self.registry.all(include_hidden=False)

        row = 0
        col = 0
        for cmd in commands:
            # Some commands may not have keybinds; still allow editing if present in keymap
            label = QLabel(f"{cmd.label} [{cmd.code}]:")
            line_edit = QLineEdit(self.keymap.get_key(cmd.code))
            line_edit.setMaxLength(1)
            line_edit.setMaximumWidth(50)

            line_edit.editingFinished.connect(
                lambda code=cmd.code, le=line_edit: self._emit_key_update(code, le)
            )

            self.key_line_edits[cmd.code] = line_edit
            key_grid.addWidget(label, row, col)
            key_grid.addWidget(line_edit, row, col + 1)

            col += 2
            if col >= 6:
                col = 0
                row += 1

        layout.addWidget(key_group)

        # Full Log
        layout.addWidget(QLabel("Full Communication Log:"))
        self.full_log_area = QTextEdit()
        self.full_log_area.setReadOnly(True)
        layout.addWidget(self.full_log_area)

        # Wiring
        self.connect_button.clicked.connect(self._handle_connect_button)
        self.refresh_button.clicked.connect(lambda: self.refresh_requested.emit())

        # initial style
        self.connect_button.setStyleSheet("background-color: #38761D; color: white;")

    def _handle_connect_button(self):
        if not self.connected:
            port = self.port_combo.currentData()
            if not port:
                QMessageBox.critical(self, "No Port", "Please select a valid serial/Bluetooth port.")
                return
            try:
                baud = int(self.baud_line.text())
            except ValueError:
                QMessageBox.critical(self, "Invalid Baud", "Baud rate must be a number.")
                return
            self.connect_requested.emit(port, baud)
        else:
            self.disconnect_requested.emit()

    def _emit_key_update(self, command, line_edit):
        new_key = line_edit.text().upper().strip()
        self.key_updated.emit(command, new_key)

    # Called by MainWindow
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

    def set_key_text(self, command: str, key: str):
        if command in self.key_line_edits:
            self.key_line_edits[command].setText(key)
