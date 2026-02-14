from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox,
    QGridLayout, QTextEdit
)
from PyQt5.QtCore import pyqtSignal


class ControlTab(QWidget):
    """
    Control tab containing all movement buttons
    and TX log display.
    """

    command_requested = pyqtSignal(str)

    def __init__(self, keymap):
        super().__init__()
        self.keymap = keymap
        self.button_map = {}
        self.control_log_area = QTextEdit()
        self.setup_ui()

    def get_key(self, command):
        return self.keymap.get_key(command)

    def setup_ui(self):
        main_h_layout = QHBoxLayout(self)

        left_column = QWidget()
        left_v_layout = QVBoxLayout(left_column)
        left_v_layout.setContentsMargins(0, 0, 0, 0)

        command_group = QGroupBox("Control Console (Keyboard Enabled)")
        control_section = QVBoxLayout()
        command_group.setLayout(control_section)

        control_grid = QGridLayout()
        turn_grid = QGridLayout()

        base_style = "color: white; padding: 15px; font-weight: bold;"

        def create_button(command, default_color):
            btn = QPushButton(f"{command} ({self.get_key(command)})")
            btn.setEnabled(False)
            btn.clicked.connect(lambda: self.command_requested.emit(command))
            btn.setStyleSheet(f"background-color: {default_color}; {base_style}")
            self.button_map[command] = btn
            return btn

        # Movement Buttons
        control_grid.addWidget(create_button("A5", "#418DF1"), 0, 0)
        control_grid.addWidget(create_button("A1", "#418DF1"), 0, 1)
        control_grid.addWidget(create_button("A6", "#418DF1"), 0, 2)

        control_grid.addWidget(create_button("A4", "#418DF1"), 1, 0)
        control_grid.addWidget(create_button("A0", "#E62626"), 1, 1)
        control_grid.addWidget(create_button("A3", "#418DF1"), 1, 2)

        control_grid.addWidget(create_button("A7", "#418DF1"), 2, 0)
        control_grid.addWidget(create_button("A2", "#418DF1"), 2, 1)
        control_grid.addWidget(create_button("A8", "#418DF1"), 2, 2)

        turn_grid.addWidget(create_button("A9", "#418DF1"), 0, 0)
        turn_grid.addWidget(create_button("A10", "#418DF1"), 0, 1)

        turn_grid.addWidget(create_button("A11", "#418DF1"), 1, 0)
        turn_grid.addWidget(create_button("A12", "#418DF1"), 1, 1)

        turn_grid.addWidget(create_button("A13", "#418DF1"), 2, 0, 1, 2)

        control_section.addLayout(control_grid)
        control_section.addLayout(turn_grid)
        left_v_layout.addWidget(command_group)
        left_v_layout.addStretch(1)

        main_h_layout.addWidget(left_column, 1)

        # Right Column TX Log
        right_column = QWidget()
        right_v_layout = QVBoxLayout(right_column)
        right_v_layout.setContentsMargins(0, 0, 0, 0)

        log_label = QLabel("Outgoing Commands (TX Log):")
        right_v_layout.addWidget(log_label)

        self.control_log_area.setReadOnly(True)
        self.control_log_area.setStyleSheet(
            "background-color: #1E1E1E; border: 1px solid #505050; font-family: monospace; color: #E0E0E0;"
        )
        right_v_layout.addWidget(self.control_log_area)

        main_h_layout.addWidget(right_column, 0.5)

    def enable_buttons(self, enabled: bool):
        for button in self.button_map.values():
            button.setEnabled(enabled)

    def log_tx(self, html_message: str):
        self.control_log_area.append(html_message)
