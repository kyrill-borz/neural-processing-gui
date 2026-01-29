from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout
import pyqtgraph as pg
import numpy as np


class AnalysisWindow(QMainWindow):
    def __init__(self, result: dict, parent=None):
        super().__init__(parent)

        self.setWindowTitle(result.get("title", "Analysis"))
        self.resize(1000, 800)

        central = QWidget()
        layout = QVBoxLayout(central)

        for plot_def in result["plots"]:
            plot = pg.PlotWidget(title=plot_def["title"])

            if plot_def["kind"] == "line":
                plot.plot(plot_def["x"], plot_def["y"])
            elif plot_def["kind"] == "scatter":
                plot.plot(plot_def["x"], plot_def["y"], pen=None, symbol="o")
            elif plot_def["kind"] == "hist":
                y = plot_def["y"]
                hist, bins = np.histogram(y, bins=50)
                plot.plot(bins[:-1], hist, stepMode=True)

            layout.addWidget(plot)

        self.setCentralWidget(central)