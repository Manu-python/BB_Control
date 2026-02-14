DARK_STYLE = """
QMainWindow, QWidget, QTabWidget, QTabWidget::pane {
    background-color: #2B2B2B;
    color: #FFFFFF;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #505050;
    top: -1px;
}

QTabBar::tab {
    background: #3C3C3C;
    color: #FFFFFF;
    padding: 8px 20px;
    border: 1px solid #505050;
    border-bottom-color: #2B2B2B;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background: #1E1E1E;
    border-bottom-color: #1E1E1E;
    font-weight: bold;
}

/* Groups */
QGroupBox {
    border: 1px solid #505050;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
    border-radius: 6px;
}

/* Buttons */
QPushButton {
    background-color: #505050;
    border: 1px solid #666666;
    padding: 8px 15px;
    border-radius: 4px;
    color: white;
}

QPushButton:hover {
    background-color: #666666;
}

/* Inputs */
QLineEdit, QComboBox {
    background-color: #3C3C3C;
    border: 1px solid #505050;
    padding: 5px;
    border-radius: 4px;
    color: white;
}

QTextEdit {
    background-color: #1E1E1E;
    border: 1px solid #505050;
    font-family: monospace;
    color: #E0E0E0;
}
"""
