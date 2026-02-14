from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox,
    QGridLayout, QTextEdit
)
from PyQt5.QtCore import pyqtSignal


class ControlTab(QWidget):
    """
    Single responsibility:
    Render control UI from layout + registry.
    Emits command_requested; does not know serial.
    """

    command_requested = pyqtSignal(str)

    def __init__(self, keymap, command_registry, ui_layout: dict):
        super().__init__()
        self.keymap = keymap
        self.registry = command_registry
        self.layout_cfg = ui_layout

        self.button_map = {}
        self.control_log_area = QTextEdit()
        self.setup_ui()

    def setup_ui(self):
        main_h_layout = QHBoxLayout(self)

        left_column = QWidget()
        left_v_layout = QVBoxLayout(left_column)
        left_v_layout.setContentsMargins(0, 0, 0, 0)

        command_group = QGroupBox("Control Console (Keyboard Enabled)")
        control_section = QVBoxLayout(command_group)

        base_style = "color: white; padding: 15px; font-weight: bold;"

        def create_button(command_code: str):
            cmd = self.registry.get(command_code)
            label = cmd.label if cmd else command_code
            color = cmd.color if cmd else "#505050"

            key = self.keymap.get_key(command_code)
            btn = QPushButton(f"{label} [{command_code}] ({key})")
            btn.setEnabled(False)
            btn.clicked.connect(lambda: self.command_requested.emit(command_code))
            btn.setStyleSheet(f"background-color: {color}; {base_style}")
            self.button_map[command_code] = btn
            return btn

        # Control grid from config
        control_grid = QGridLayout()
        for r, row in enumerate(self.layout_cfg.get("control_grid", [])):
            for c, code in enumerate(row):
                if not code:
                    continue
                control_grid.addWidget(create_button(code), r, c)

        # Aux grid from config (supports ragged rows)
        aux_grid = QGridLayout()
        for r, row in enumerate(self.layout_cfg.get("aux_grid", [])):
            for c, code in enumerate(row):
                if not code:
                    continue
                # If single item row, span 2 columns for nicer look
                if len(row) == 1:
                    aux_grid.addWidget(create_button(code), r, 0, 1, 2)
                else:
                    aux_grid.addWidget(create_button(code), r, c)

        control_section.addLayout(control_grid)
        control_section.addLayout(aux_grid)

        left_v_layout.addWidget(command_group)
        left_v_layout.addStretch(1)
        main_h_layout.addWidget(left_column, 1)

        # Right Column TX Log
        right_column = QWidget()
        right_v_layout = QVBoxLayout(right_column)
        right_v_layout.setContentsMargins(0, 0, 0, 0)

        right_v_layout.addWidget(QLabel("Outgoing Commands (TX Log):"))
        self.control_log_area.setReadOnly(True)
        right_v_layout.addWidget(self.control_log_area)

        main_h_layout.addWidget(right_column, 0.5)

    def enable_buttons(self, enabled: bool):
        for button in self.button_map.values():
            button.setEnabled(enabled)

    def log_tx(self, html_message: str):
        self.control_log_area.append(html_message)

    def refresh_button_labels(self):
        """Call after keymap changes to update the (key) shown on buttons."""
        for code, btn in self.button_map.items():
            cmd = self.registry.get(code)
            label = cmd.label if cmd else code
            key = self.keymap.get_key(code)
            btn.setText(f"{label} [{code}] ({key})")
