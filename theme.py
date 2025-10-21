"""
theme.py

Dark and light theme stylesheets for the Qt application.
"""

from PySide6.QtWidgets import QApplication


DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
}

QDockWidget {
    background-color: #252525;
    color: #e0e0e0;
    titlebar-close-icon: url(close.png);
    titlebar-normal-icon: url(float.png);
}

QDockWidget::title {
    background-color: #2d2d2d;
    padding: 6px;
}

QGroupBox {
    border: 1px solid #444444;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    color: #e0e0e0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 5px;
    color: #00b4d8;
}

QPushButton {
    background-color: #0077b6;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #0096c7;
}

QPushButton:pressed {
    background-color: #005f8a;
}

QPushButton:disabled {
    background-color: #444444;
    color: #888888;
}

QSpinBox, QDoubleSpinBox, QLineEdit {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 3px;
    padding: 4px;
    color: #e0e0e0;
}

QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
    border: 1px solid #0077b6;
}

QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 3px;
    padding: 4px;
    color: #e0e0e0;
}

QComboBox:hover {
    border: 1px solid #0077b6;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    selection-background-color: #0077b6;
    color: #e0e0e0;
}

QSlider::groove:horizontal {
    border: 1px solid #444444;
    height: 6px;
    background: #2d2d2d;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #0077b6;
    border: 1px solid #0096c7;
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #0096c7;
}

QCheckBox {
    color: #e0e0e0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #444444;
    border-radius: 3px;
    background-color: #2d2d2d;
}

QCheckBox::indicator:checked {
    background-color: #0077b6;
    border: 1px solid #0096c7;
}

QLabel {
    color: #e0e0e0;
}

QStatusBar {
    background-color: #252525;
    color: #e0e0e0;
}

QMenuBar {
    background-color: #252525;
    color: #e0e0e0;
}

QMenuBar::item:selected {
    background-color: #0077b6;
}

QMenu {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #444444;
}

QMenu::item:selected {
    background-color: #0077b6;
}

QScrollBar:vertical {
    background: #2d2d2d;
    width: 14px;
    border-radius: 7px;
}

QScrollBar::handle:vertical {
    background: #555555;
    border-radius: 7px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #666666;
}

QScrollBar:horizontal {
    background: #2d2d2d;
    height: 14px;
    border-radius: 7px;
}

QScrollBar::handle:horizontal {
    background: #555555;
    border-radius: 7px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background: #666666;
}
"""


LIGHT_THEME = """
QMainWindow, QWidget {
    background-color: #f5f5f5;
    color: #1e1e1e;
}

QDockWidget {
    background-color: #ffffff;
    color: #1e1e1e;
}

QDockWidget::title {
    background-color: #e0e0e0;
    padding: 6px;
}

QGroupBox {
    border: 1px solid #c0c0c0;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    color: #1e1e1e;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 5px;
    color: #0077b6;
}

QPushButton {
    background-color: #0077b6;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #0096c7;
}

QPushButton:pressed {
    background-color: #005f8a;
}

QPushButton:disabled {
    background-color: #c0c0c0;
    color: #888888;
}

QSpinBox, QDoubleSpinBox, QLineEdit {
    background-color: white;
    border: 1px solid #c0c0c0;
    border-radius: 3px;
    padding: 4px;
    color: #1e1e1e;
}

QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
    border: 1px solid #0077b6;
}

QComboBox {
    background-color: white;
    border: 1px solid #c0c0c0;
    border-radius: 3px;
    padding: 4px;
    color: #1e1e1e;
}

QComboBox:hover {
    border: 1px solid #0077b6;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: white;
    selection-background-color: #0077b6;
    selection-color: white;
    color: #1e1e1e;
}

QSlider::groove:horizontal {
    border: 1px solid #c0c0c0;
    height: 6px;
    background: white;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #0077b6;
    border: 1px solid #0096c7;
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #0096c7;
}

QCheckBox {
    color: #1e1e1e;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #c0c0c0;
    border-radius: 3px;
    background-color: white;
}

QCheckBox::indicator:checked {
    background-color: #0077b6;
    border: 1px solid #0096c7;
}

QLabel {
    color: #1e1e1e;
}

QStatusBar {
    background-color: #e0e0e0;
    color: #1e1e1e;
}

QMenuBar {
    background-color: #e0e0e0;
    color: #1e1e1e;
}

QMenuBar::item:selected {
    background-color: #0077b6;
    color: white;
}

QMenu {
    background-color: white;
    color: #1e1e1e;
    border: 1px solid #c0c0c0;
}

QMenu::item:selected {
    background-color: #0077b6;
    color: white;
}

QScrollBar:vertical {
    background: #f5f5f5;
    width: 14px;
    border-radius: 7px;
}

QScrollBar::handle:vertical {
    background: #c0c0c0;
    border-radius: 7px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #a0a0a0;
}

QScrollBar:horizontal {
    background: #f5f5f5;
    height: 14px;
    border-radius: 7px;
}

QScrollBar::handle:horizontal {
    background: #c0c0c0;
    border-radius: 7px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background: #a0a0a0;
}
"""


def apply_theme(app: QApplication, dark: bool = True):
    """
    Apply a theme to the application.
    
    Args:
        app: QApplication instance
        dark: If True, apply dark theme; otherwise apply light theme
    """
    if dark:
        app.setStyleSheet(DARK_THEME)
    else:
        app.setStyleSheet(LIGHT_THEME)
