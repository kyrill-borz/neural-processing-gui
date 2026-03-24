import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QGridLayout, QComboBox, QDialogButtonBox, QCheckBox, QPushButton

class ProcessingTab(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        """Create the Network page UI."""
        layout = QGridLayout(self)
        layout.addWidget(QPushButton("Glucose Comparison"),0,1)
        plot_graph_raw = pg.PlotWidget()
        plot_graph_filtered = pg.PlotWidget()
        layout.addWidget(plot_graph_raw,2,0,1,3)
        layout.addWidget(plot_graph_filtered,3,0,1,3)

        self.btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )