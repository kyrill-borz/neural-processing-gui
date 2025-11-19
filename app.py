import sys
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QFormLayout,
    QGridLayout,
    QLineEdit,
    QDialogButtonBox,
    QComboBox,
    QPushButton
)

class Window(QWidget):
    def __init__(self):
        super().__init__()
        pg.setConfigOption('background', '#f2f2f2')
        pg.setConfigOption('foreground', '#2a2a2a')

        self.setWindowTitle("Processing GUI")
        self.resize(1200, 600)
        # Create a top-level layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        # Create the tab widget with two tabs
        tabs = QTabWidget()
        tabs.addTab(self.ImportTabUI(), "Import")
        tabs.addTab(self.NeuralTabUI(), "Neural Check")
        tabs.addTab(self.ProcessingTabUI(), "Analysis")
        tabs.setTabPosition(QTabWidget.West)
        tabs.tabBar().setStyleSheet("QTabBar::tab{ height: 124 px; width: 150px; }")
        layout.addWidget(tabs)

        with open("style.css","r") as fh:
            self.setStyleSheet(fh.read())

    def ImportTabUI(self):
        """Create the General page UI."""
        importTab = QWidget()
        layout = QVBoxLayout()
        formlayout = QFormLayout()
        formlayout.addRow("Data Path:", QLineEdit())
        formlayout.addRow("Filter:", QCheckBox())
        formlayout.addRow("See Data:", QCheckBox())
        plot_graph_raw = pg.PlotWidget()
        plot_graph_filtered = pg.PlotWidget()
        formlayout.addRow("Raw Signal:", plot_graph_raw)
        formlayout.addRow("Filtered Signal:", plot_graph_filtered)
        btnBox = QDialogButtonBox()
        btnBox.setStandardButtons(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        layout.addLayout(formlayout)
        layout.addWidget(btnBox)
        importTab.setLayout(layout)
        return importTab

    def NeuralTabUI(self):
        """Create the Network page UI."""
        NeuralTab = QWidget()
        layout = QGridLayout()
        layout.addWidget(QCheckBox("Drop Bad Channels"), 1,0)
        layout.addWidget(QCheckBox("Single Channel Analysis"),0,1)
        layout.addWidget(QCheckBox("Multiple Channel Analysis"),0,2)

        combobox = QComboBox(self)
        combobox.addItem("Select Referencing Method")
        combobox.addItem("No Referencing")
        combobox.addItem("Median")
        combobox.addItem("Laplacian")
        combobox.addItem("Bipolar")
        combobox.addItem("Tripolar")
        layout.addWidget(combobox,0,0)

        combobox2 = QComboBox(self)
        combobox2.addItem("Type of Single Channel Analysis")
        combobox2.addItem("Referencing Only")
        combobox2.addItem("Single Channel Spike Detection")
        combobox2.addItem("ISI Distribution")
        combobox2.addItem("Clustering of Spikes")
        layout.addWidget(combobox2,1,1)

        combobox3 = QComboBox(self)
        combobox3.addItem("Type of Multi-Channel Analysis")
        combobox3.addItem("Multiple Channel Spike Detection")
        combobox3.addItem("Cross Correlation of Spike Trains")
        combobox3.addItem("Directionality Analysis")
        combobox3.addItem("Propogation Coefficient")
        layout.addWidget(combobox3,1,2)

        plot_graph_raw = pg.PlotWidget()
        plot_graph_filtered = pg.PlotWidget()
        layout.addWidget(plot_graph_raw,2,0,1,3)
        layout.addWidget(plot_graph_filtered,3,0,1,3)
        btnBox = QDialogButtonBox()
        btnBox.setStandardButtons(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        layout.addWidget(btnBox,4,2)
        NeuralTab.setLayout(layout)
        return NeuralTab
    
    def ProcessingTabUI(self):
        """Create the Network page UI."""
        processingTab = QWidget()
        layout = QGridLayout()
        layout.addWidget(QCheckBox("Using Multiple Traces"), 0,0)

        layout.addWidget(QPushButton("Temporal Heatmap Correlogram"),0,1)
        layout.addWidget(QPushButton("Overlap Analysed Traces"),0,2)
        plot_graph_raw = pg.PlotWidget()
        plot_graph_filtered = pg.PlotWidget()
        layout.addWidget(plot_graph_raw,2,0,1,3)
        layout.addWidget(plot_graph_filtered,3,0,1,3)
        processingTab.setLayout(layout)
        return processingTab

if __name__ == "__main__":
    app = QApplication(sys.argv)
    

    window = Window()
    window.show()
    sys.exit(app.exec_())