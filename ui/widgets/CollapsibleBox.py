from PyQt5.QtWidgets import (
    QWidget, QToolButton, QVBoxLayout, QSizePolicy
)
from PyQt5.QtCore import Qt

class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)

        self.toggle_button = QToolButton(
            text=title, checkable=True, checked=True
        )
        self.toggle_button.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(Qt.DownArrow)
        self.toggle_button.clicked.connect(self.on_toggle)

        self.content = QWidget()
        self.content.setMaximumHeight(self.content.sizeHint().height())
        self.content.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content)

    def setContentLayout(self, layout):
        self.content.setLayout(layout)

    def on_toggle(self, checked):
        self.toggle_button.setArrowType(
            Qt.DownArrow if checked else Qt.RightArrow
        )
        self.content.setMaximumHeight(
            self.content.sizeHint().height() if checked else 0
        )