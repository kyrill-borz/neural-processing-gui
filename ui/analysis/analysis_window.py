from PyQt5.QtWidgets import QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel, QScrollArea, QFileDialog
from PyQt5.QtCore import Qt, QRectF
import pyqtgraph as pg
import numpy as np


class AnalysisWindow(QMainWindow):
    def __init__(self, result: dict, parent=None):
        super().__init__(parent)
        self.plotHeight = 300
        self.setWindowTitle(result.get("title", "Analysis"))
        self.resize(1000, 800)

        central = QWidget()
        layout = QVBoxLayout(central)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.result = result
        self.time_reference_plot = None

        self.COLOR_CYCLE = [
            "#1f77b4",  # blue
            "#d62728",  # red
            "#2ca02c",  # green
            "#ff7f0e",  # orange
            "#9467bd",  # purple
            "#8c564b",  # brown
            "#e377c2",  # pink
            "#7f7f7f",  # gray
        ]
        for item in result["plots"]:

            # ---------- TEXT ----------
            if item["kind"] == "text":
                label = QLabel(item["content"])
                layout.addWidget(label)
                continue

            # ---------- STANDARD PLOT ----------
            if item["kind"] == "plot":
                plot = pg.PlotWidget(title=item.get("title", ""))
                plot.setMinimumHeight(self.plotHeight)

                if item.get("time_axis", False):
                    if self.time_reference_plot is None:
                        self.time_reference_plot = plot
                    else:
                        plot.setXLink(self.time_reference_plot)

                legend = plot.addLegend()

                for i, series in enumerate(item.get("series", [])):
                    if "x" in series:
                        x = series["x"]
                    y = series["y"]
                    name = series.get("name", None)
                    colour = series.get("color", self.COLOR_CYCLE[i % len(self.COLOR_CYCLE)])
                    pen = pg.mkPen(color=colour, width=2)

                    # ---- LINE ----
                    if series["type"] == "line":
                        plot.plot(x, y, name=name, pen=pen)

                    # ---- SCATTER ----
                    elif series["type"] == "scatter":
                        scatter = plot.plot(
                            x, y,
                            pen=None,
                            symbol="o",
                            name=name
                        )

                        # ---- POINT LABELS ----
                        if "labels" in series:
                            for xi, yi, label in zip(x, y, series["labels"]):
                                text = pg.TextItem(label, anchor=(0, 1))
                                text.setPos(xi, yi)
                                plot.addItem(text)

                    # ---- HIST ----
                    elif series["type"] == "hist":
                        hist, bins = np.histogram(y, bins=series.get("bins", 50))
                        plot.plot(bins, hist, stepMode=True, fillLevel=0, name=name)

                    elif series["type"] == "bar":
                        x_width = (x[1] - x[0]) * 0.8 if len(x) > 1 else 0.8
                        
                        bg = pg.BarGraphItem(x=x, height=y, width=x_width, brush=(100, 100, 250, 150))
                        plot.addItem(bg)

                # ---- AXES ----
                if "xlabel" in item:
                    plot.setLabel("bottom", item["xlabel"])
                if "ylabel" in item:
                    plot.setLabel("left", item["ylabel"])

                if item.get("grid", False):
                    plot.showGrid(x=True, y=True)

                # ---- EQUATIONS ----
                if "equations" in item:
                    eq_text = "\n".join(item["equations"])
                    eq_item = pg.TextItem(eq_text, anchor=(1, 0))
                    eq_item.setPos(10, 1)  # temporary, will fix below
                    plot.addItem(eq_item)

                    # Place in top-right using viewbox
                    def update_eq_position():
                        vb = plot.getViewBox()
                        rect = vb.viewRect()
                        eq_item.setPos(rect.right(), rect.top())

                    plot.sigRangeChanged.connect(lambda *_: update_eq_position())
                    update_eq_position()

                layout.addWidget(plot)

                continue

            # ---------- IMAGE (HEATMAP / SPECTROGRAM / ISI) ----------
            if item["kind"] == "image":
                graphics = pg.GraphicsLayoutWidget()
                plot = graphics.addPlot(title=item.get("title", ""))
                plot.setMinimumHeight(self.plotHeight)

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
        
        self.export_button = QPushButton("Export JSON")
        self.export_button.clicked.connect(self.export_JSON)
        layout.addWidget(self.export_button)
        scroll.setWidget(central)
        self.setCentralWidget(scroll)
    
    def export_JSON(self):
        folder_path = QFileDialog.getExistingDirectory(
            caption="Select Export Folder"
        )
        if not folder_path:
            return
        json = self.result
        with open(f"{folder_path}/data.json", 'w') as f:
            json.dump(json, f)



