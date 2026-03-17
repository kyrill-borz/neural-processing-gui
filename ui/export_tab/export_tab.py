import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QGridLayout, QComboBox, QDialogButtonBox, QCheckBox, QPushButton

class ExportTab(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        """Create the Network page UI."""
        layout = QGridLayout(self)
        layout.addWidget(QPushButton("Export data"), 0,0)

    