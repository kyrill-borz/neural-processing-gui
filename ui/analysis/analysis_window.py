from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt, QRectF
import pyqtgraph as pg
import numpy as np


class AnalysisWindow(QMainWindow):
    def __init__(self, result: dict, parent=None):
        super().__init__(parent)

        self.setWindowTitle(result.get("title", "Analysis"))
        self.resize(1000, 800)

        central = QWidget()
        layout = QVBoxLayout(central)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        for item in result["plots"]:

            # ---------- TEXT ----------
            if item["kind"] == "text":
                label = QLabel(item["content"])
                layout.addWidget(label)
                continue

            # ---------- STANDARD PLOT ----------
            if item["kind"] in ["line", "scatter", "hist"]:
                plot = pg.PlotWidget(title=item.get("title", ""))

                # ---- LINE ----
                if item["kind"] == "line":
                    plot.plot(item["x"], item["y"])

                # ---- SCATTER ----
                elif item["kind"] == "scatter":
                    plot.plot(
                        item["x"],
                        item["y"],
                        pen=None,
                        symbol="o"
                    )

                # ---- HISTOGRAM ----
                elif item["kind"] == "hist":
                    y = item["y"]
                    hist, bins = np.histogram(y, bins=item.get("bins", 50))

                    # bins has length N+1, hist has length N
                    plot.plot(
                        bins,
                        hist,
                        stepMode=True,
                        fillLevel=0
                    )

                # ---- Axis Labels (NEW) ----
                if "xlabel" in item:
                    plot.setLabel("bottom", item["xlabel"])

                if "ylabel" in item:
                    plot.setLabel("left", item["ylabel"])

                # Optional grid
                if item.get("grid", False):
                    plot.showGrid(x=True, y=True)

                layout.addWidget(plot)
                continue

            # ---------- IMAGE (HEATMAP / SPECTROGRAM / ISI) ----------
            if item["kind"] == "image":
                graphics = pg.GraphicsLayoutWidget()
                plot = graphics.addPlot(title=item.get("title", ""))

                img = pg.ImageItem(item["z"])
                plot.addItem(img)

                # Axis scaling (optional)
                if "x" in item and "y" in item:
                    x = item["x"]
                    y = item["y"]

                    if len(x) > 1 and len(y) > 1:
                        img.setRect(
                            QRectF(
                                x[0],
                                y[0],
                                x[-1] - x[0],
                                y[-1] - y[0],
                            )
                        )

                plot.setLabel("left", item.get("ylabel", ""))
                plot.setLabel("bottom", item.get("xlabel", ""))

                layout.addWidget(graphics)
                continue
        scroll.setWidget(central)
        self.setCentralWidget(scroll)