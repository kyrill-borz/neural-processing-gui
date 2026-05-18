from PyQt5.QtWidgets import QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

class InfoHoverButton(QPushButton):
    """
    A simple info icon button that displays a tooltip on hover.
    
    Usage:
        info = InfoHoverButton("This is helpful information about the feature")
        layout.addWidget(info)
    """
    def __init__(self, tooltip_text: str, parent=None):
        super().__init__("ℹ", parent)  # Info icon using Unicode
        self.setMaximumWidth(25)
        self.setMaximumHeight(25)
        self.setToolTip(tooltip_text)
        self.setStyleSheet("""
            QPushButton {
                border-radius: 12px;
                background-color: #e0e0e0;
                border: 1px solid #999;
                font-weight: bold;
                color: #333;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)